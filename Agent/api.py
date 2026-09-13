"""
林草综合防护多智能体系统 - 最小 HTTP Adapter (FastAPI)

职责：
    把一次来自 Web 的「图片 + 可选文字」请求，
    转换为对 Agent/graph.py 中 forestry_app 的同步调用，
    并返回可 JSON 序列化的最终分析报告。

本阶段明确不负责：SSE / token streaming / checkpoint / memory / 用户系统。
"""

import os
import sys
import json
import traceback
import tempfile

# Windows 控制台默认 GBK 编码，Agent 的 emoji print 会触发 UnicodeEncodeError。
# 在导入 graph 之前把标准输出重配为 UTF-8，保证 import 期间的 print 不崩溃（不修改 Agent 核心代码）。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8")
        except Exception:
            pass

from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from langchain_core.messages import HumanMessage

# 复用现有编译好的图（不做任何算法改动，不重写 Agent）
from graph import forestry_app, GRAPH_RECURSION_LIMIT

app = FastAPI(title="林草综合防护多智能体系统 API", version="0.1.0")

# 开发环境 CORS：仅放行 qingqiong 本地静态站点的来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DEFAULT_PROMPT = "请分析这张林区现场照片，给出林草异常诊断结论，并生成应急处置报告。"

# vision_expert_tool 目前仅识别这 5 种扩展名，其余回退为 .jpg
ALLOWED_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


@app.get("/")
def root():
    return {"status": "ok", "service": "forestry-agent-api"}


@app.post("/api/analyze")
async def analyze(
    image: UploadFile = File(...),
    prompt: str = Form(""),
):
    tmp_path = ""
    try:
        raw = await image.read()
        if not raw:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "上传图片内容为空"},
            )

        # 1. 保留扩展名写入临时文件（vision_expert_tool 依赖本地路径）
        ext = os.path.splitext(image.filename or "")[1].lower()
        if ext not in ALLOWED_EXT:
            ext = ".jpg"
        fd, tmp_path = tempfile.mkstemp(suffix=ext)
        with os.fdopen(fd, "wb") as f:
            f.write(raw)

        # 2. 复用 app.py 的图片路径注入方式，构造 initial_state（字段与现有 Agent 完全一致）
        user_text = prompt.strip() if prompt and prompt.strip() else DEFAULT_PROMPT
        content_str = f"{user_text}\n【系统提示：现场图片路径为 {tmp_path}】"

        initial_state = {
            "messages": [HumanMessage(content=content_str)],
            "plan_loop_count": 0,
            "execution_step_count": 0,
            "completed_tasks": ["__RESET__"],
            "task_results": {"__RESET__": "__RESET__"},
            "reflections": ["__RESET__"],
            "evidences": [],
            "evidence_seq": 0,
            "critic_verdict": None,
            "finalizer_result": None,
        }

        # 3. 同步调用现有图，收集节点信息并提取 finalizer 最终输出
        final_report = ""
        finalizer_result = None
        steps = []
        for event in forestry_app.stream(initial_state, config={"recursion_limit": GRAPH_RECURSION_LIMIT}):
            for node_name, node_state in event.items():
                if node_state is None:
                    continue
                if node_name not in steps:
                    steps.append(node_name)
                if node_name == "finalizer_node":
                    finalizer_result = _extract_finalizer_result(node_state)
                    if finalizer_result and finalizer_result.get("status") == "success":
                        final_report = finalizer_result["report"]

        if not finalizer_result or finalizer_result.get("status") != "success" or not final_report.strip():
            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": "分析未能生成最终报告。",
                    "steps": steps,
                },
            )

        return {"success": True, "report": final_report, "steps": steps}

    except Exception as e:  # 兜底：不把 traceback / 密钥暴露给前端
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": f"分析过程中发生异常: {str(e)[:300]}",
            },
        )
    finally:
        # 4. 无论成功或异常，都必须清理临时文件
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


# ==========================================
# SSE V1：实时 Agent Timeline 流式接口
# ==========================================

def _sse(event_name: str, data: dict) -> str:
    """构造一条符合 SSE 规范的帧：event: xxx\ndata: {json}\n\n（单行合法 JSON，不泄露密钥）。"""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event_name}\ndata: {payload}\n\n"


def _short_preview(text, limit: int = 160) -> str:
    """Evidence 内容短预览（V1 不把完整 content 推给浏览器）。"""
    if not text:
        return ""
    t = str(text).replace("\n", " ").replace("\r", " ").strip()
    return t[:limit] + ("…" if len(t) > limit else "")


def _extract_report_text(node_state) -> str:
    """复用 /api/analyze 已验证的消息提取逻辑（兼容 Message / tuple / str）。"""
    messages = node_state.get("messages") or []
    if not messages:
        return ""
    last = messages[-1]
    if hasattr(last, "content"):
        return last.content if isinstance(last.content, str) else str(last.content)
    if isinstance(last, (tuple, list)) and len(last) > 1:
        return str(last[1])
    return str(last)


def _extract_finalizer_result(node_state):
    """Extract the structured Finalizer result; messages are not a status source."""
    result = node_state.get("finalizer_result") if node_state else None
    if hasattr(result, "model_dump"):
        result = result.model_dump()
    if not isinstance(result, dict):
        return None
    status = result.get("status")
    report = result.get("report")
    if status not in {"success", "error"}:
        return None
    if status == "success" and (not isinstance(report, str) or not report.strip()):
        return None
    return result


@app.post("/api/analyze-stream")
async def analyze_stream(
    image: UploadFile = File(...),
    prompt: str = Form(""),
):
    """SSE 流式接口：真实 LangGraph 执行过程逐条推送给浏览器。与 /api/analyze 共享同一套 state schema。"""
    tmp_path = ""
    try:
        raw = await image.read()
        if not raw:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "上传图片内容为空"},
            )

        ext = os.path.splitext(image.filename or "")[1].lower()
        if ext not in ALLOWED_EXT:
            ext = ".jpg"
        fd, tmp_path = tempfile.mkstemp(suffix=ext)
        with os.fdopen(fd, "wb") as f:
            f.write(raw)
    except Exception as e:
        if tmp_path and os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"分析过程中发生异常: {str(e)[:300]}"},
        )

    user_text = prompt.strip() if prompt and prompt.strip() else DEFAULT_PROMPT
    content_str = f"{user_text}\n【系统提示：现场图片路径为 {tmp_path}】"
    initial_state = {
        "messages": [HumanMessage(content=content_str)],
        "plan_loop_count": 0,
        "execution_step_count": 0,
        "completed_tasks": ["__RESET__"],
        "task_results": {"__RESET__": "__RESET__"},
        "reflections": ["__RESET__"],
        "evidences": [],
        "evidence_seq": 0,
        "critic_verdict": None,
        "finalizer_result": None,
    }

    def sse_generator():
        task_map = {}
        current_loop = 0
        final_report_seen = False
        stream_error_seen = False
        stream_error_message = None
        try:
            yield _sse("run_started", {"message": "分析任务已开始"})
            for event in forestry_app.stream(initial_state, config={"recursion_limit": GRAPH_RECURSION_LIMIT}):
                for node_name, node_state in event.items():
                    if not node_state:
                        continue

                    if node_name == "planner_node":
                        plan = node_state.get("plan")
                        if plan is not None and hasattr(plan, "steps"):
                            current_loop = node_state.get("plan_loop_count", current_loop)
                            steps = []
                            for s in plan.steps:
                                steps.append({
                                    "task_id": s.task_id,
                                    "task_name": s.task_name,
                                    "tool_required": s.tool_required,
                                })
                                task_map[s.task_id] = {"task_name": s.task_name, "tool": s.tool_required}
                            yield _sse("planner_completed", {"plan_loop": current_loop, "steps": steps})
                        # JSON 重试路径无 plan：V1 静默跳过，不伪造 planner_completed

                    elif node_name == "executor_node":
                        completed = node_state.get("completed_tasks") or []
                        real_tasks = [t for t in completed if t != "__RESET__"]
                        if real_tasks:
                            task_id = real_tasks[-1]
                            info = task_map.get(task_id, {})
                            yield _sse("executor_completed", {
                                "task_id": task_id,
                                "task_name": info.get("task_name"),
                                "tool": info.get("tool"),
                                "plan_loop": current_loop,
                            })

                        for er in (node_state.get("evidences") or []):
                            d = er.model_dump() if hasattr(er, "model_dump") else dict(er)
                            meta = d.get("metadata") or {}
                            yield _sse("evidence_created", {
                                "evidence_id": d.get("evidence_id"),
                                "type": d.get("type"),
                                "tool_name": d.get("tool_name"),
                                "source": d.get("source"),
                                "rank": meta.get("rank"),
                                "plan_loop": d.get("plan_loop"),
                                "task_id": d.get("task_id"),
                                "preview": _short_preview(d.get("content")),
                            })

                    elif node_name == "critic_node":
                        verdict = node_state.get("critic_verdict")
                        if verdict is not None:
                            v = verdict.model_dump() if hasattr(verdict, "model_dump") else dict(verdict)
                            status = v.get("status")
                            # 兼容旧前端：action 语义保留（replan / finalize）
                            action = "finalize" if status in ("passed", "soft_landing", "deadlock") else "replan"
                            yield _sse("critic_result", {
                                "action": action,
                                "status": status,
                                "is_compliant": v.get("is_compliant"),
                                "plan_loop": v.get("plan_loop", current_loop),
                            })
                        else:
                            # 向后兼容：无结构化 verdict 时回退到旧 action 语义
                            if "reflections" in node_state:
                                yield _sse("critic_result", {"action": "replan", "plan_loop": current_loop})
                            elif "messages" in node_state:
                                yield _sse("critic_result", {"action": "finalize", "plan_loop": current_loop})

                    elif node_name == "finalizer_node":
                        yield _sse("finalizer_completed", {})
                        result = _extract_finalizer_result(node_state)
                        if result and result.get("status") == "success":
                            report = result["report"]
                            final_report_seen = True
                            yield _sse("final_report", {"report": report})
                        elif result and result.get("status") == "error":
                            # Keep the terminal error controlled; do not expose tool/LLM details.
                            stream_error_message = "最终报告生成失败，请稍后重试。"
                        else:
                            stream_error_message = "最终报告生成失败，请稍后重试。"

            if final_report_seen:
                yield _sse("run_completed", {"success": True})
            else:
                if not stream_error_seen:
                    stream_error_seen = True
                    yield _sse("error", {"message": stream_error_message or "分析未能完成，未生成最终报告。"})
                yield _sse("run_completed", {"success": False})

        except Exception as e:
            # 不把 traceback / 密钥暴露给浏览器，服务端仍打印真实异常用于调试
            print(f"[SSE] 流式分析异常: {e}")
            traceback.print_exc()
            if not stream_error_seen:
                stream_error_seen = True
                yield _sse("error", {"message": "分析未能完成，请稍后重试。"})
            yield _sse("run_completed", {"success": False})

        finally:
            # 临时图片在 streaming 全生命周期（含异常 / 客户端断开）之后统一清理，幂等安全
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
