import os
import sys
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient
from langchain_core.messages import HumanMessage

import agents
import api
from state import FinalizerResult


class FakeFinalizer:
    def __init__(self, content=None, error=None):
        self.content = content
        self.error = error

    def invoke(self, *_):
        if self.error:
            raise self.error
        return SimpleNamespace(content=self.content)


def _state():
    return {"messages": [HumanMessage(content="approved material")], "finalizer_result": None}


def test_finalizer_success_exception_and_empty_contract():
    with patch.object(agents, "finalizer_llm", FakeFinalizer("真实报告")):
        cmd = agents.finalizer_node(_state())
    assert cmd.update["finalizer_result"].model_dump() == {
        "status": "success", "report": "真实报告", "error_type": None
    }

    with patch.object(agents, "finalizer_llm", FakeFinalizer(error=RuntimeError("Connection error"))):
        cmd = agents.finalizer_node(_state())
    result = cmd.update["finalizer_result"]
    assert result.status == "error" and result.report is None
    assert result.error_type == "finalizer_llm_error"
    assert "Connection error" not in cmd.update["messages"][0][1]

    for content in (None, ""):
        with patch.object(agents, "finalizer_llm", FakeFinalizer(content)):
            cmd = agents.finalizer_node(_state())
        result = cmd.update["finalizer_result"]
        assert result.status == "error"
        assert result.error_type == "empty_finalizer_response"


class FakeApp:
    def __init__(self, result):
        self.result = result

    def stream(self, initial_state, config=None):
        yield {"finalizer_node": {
            "messages": [("ai", self.result.get("report") or "最终报告生成失败。")],
            "finalizer_result": self.result,
        }}


def _post(path, result):
    api.forestry_app = FakeApp(result)
    client = TestClient(api.app)
    with open("tests/test.jpg", "rb") as image:
        return client.post(path, files={"image": ("test.jpg", image, "image/jpeg")})


def test_api_success_and_error_terminal_contract():
    success = {"status": "success", "report": "真实报告", "error_type": None}
    response = _post("/api/analyze", success)
    assert response.status_code == 200 and response.json()["success"] is True
    response = _post("/api/analyze-stream", success)
    assert 'event: final_report' in response.text and '"success": true' in response.text

    error = {"status": "error", "report": None, "error_type": "finalizer_llm_error"}
    response = _post("/api/analyze", error)
    assert response.status_code == 500 and response.json()["success"] is False
    response = _post("/api/analyze-stream", error)
    assert 'event: final_report' not in response.text
    assert '最终报告生成失败，请稍后重试。' in response.text
    assert '"success": false' in response.text
    assert "Connection error" not in response.text


def test_api_rejects_invalid_finalizer_result():
    invalid = {"status": "banana", "report": "伪报告", "error_type": None}
    response = _post("/api/analyze", invalid)
    assert response.status_code == 500 and response.json()["success"] is False
    response = _post("/api/analyze-stream", invalid)
    assert 'event: final_report' not in response.text
    assert '"success": false' in response.text
