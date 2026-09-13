"""Structured Tool success/error contract tests (no external API or vector DB)."""

import os
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import agents
import tools


def _call(tool, tool_id, args):
    return tool.invoke({"type": "tool_call", "id": tool_id, "name": tool.name, "args": args})


def _fake_completion(content):
    return SimpleNamespace(
        chat=SimpleNamespace(
            completions=SimpleNamespace(
                create=lambda **kwargs: SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
                )
            )
        )
    )


def test_vision_success_and_empty_response():
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as image:
        image.write(b"fake image")
        image_path = image.name
    try:
        with patch.object(tools, "OpenAI", return_value=_fake_completion("visible tree")):
            result = _call(tools.vision_expert_tool, "v1", {"image_path": image_path})
        assert result.artifact["status"] == "success"
        records, error = agents._evidence_records_from_artifact(
            "vision_expert_tool", "task", 1, {"image_path": image_path}, result.content,
            result.artifact, "v1", 0,
        )
        assert error is None and len(records) == 1

        with patch.object(tools, "OpenAI", return_value=_fake_completion("")):
            result = _call(tools.vision_expert_tool, "v2", {"image_path": image_path})
        assert result.artifact == {"status": "error", "error_type": "empty_vision_response"}
        records, error = agents._evidence_records_from_artifact(
            "vision_expert_tool", "task", 1, {"image_path": image_path}, result.content,
            result.artifact, "v2", 0,
        )
        assert error is None and records == []
    finally:
        os.remove(image_path)


def test_vision_missing_image_and_api_error():
    result = _call(tools.vision_expert_tool, "v1", {"image_path": "does-not-exist.jpg"})
    assert result.artifact["status"] == "error"
    assert result.artifact["error_type"] == "image_not_found"

    with patch.object(tools, "OpenAI", side_effect=RuntimeError("backend unavailable")):
        fd, image_path = tempfile.mkstemp(suffix=".jpg")
        os.close(fd)
        try:
            result = _call(tools.vision_expert_tool, "v2", {"image_path": image_path})
        finally:
            os.remove(image_path)
    assert result.artifact == {"status": "error", "error_type": "vision_api_error"}


def test_knowledge_success_empty_and_error():
    docs = [{"content": "policy text", "source": "a.pdf", "metadata": {}, "rank": 1,
             "raw_score": 0.1, "score_semantics": "distance"}]
    with patch.object(tools, "retrieve_knowledge", return_value=docs):
        result = _call(tools.knowledge_expert_tool, "k1", {"query": "policy"})
    assert result.artifact["status"] == "success"
    records, error = agents._evidence_records_from_artifact(
        "knowledge_expert_tool", "task", 1, {"query": "policy"}, result.content,
        result.artifact, "k1", 0,
    )
    assert error is None and len(records) == 1

    with patch.object(tools, "retrieve_knowledge", return_value=[]):
        empty = _call(tools.knowledge_expert_tool, "k2", {"query": "none"})
    assert empty.artifact == {"status": "empty", "documents": []}
    records, error = agents._evidence_records_from_artifact(
        "knowledge_expert_tool", "task", 1, {"query": "none"}, "没有找到匹配资料。",
        empty.artifact, "k2", 0,
    )
    assert error is None and records == []

    with patch.object(tools, "retrieve_knowledge", side_effect=RuntimeError("db down")):
        failed = _call(tools.knowledge_expert_tool, "k3", {"query": "policy"})
    assert failed.artifact == {"status": "error", "error_type": "retrieval_error"}
    records, error = agents._evidence_records_from_artifact(
        "knowledge_expert_tool", "task", 1, {"query": "policy"}, "RAG backend unavailable",
        failed.artifact, "k3", 0,
    )
    assert error is None and records == []


def test_contract_validation_and_text_agnostic_gate():
    common = {"image_path": "x.jpg"}
    for artifact in (None, {}, {"status": "banana"}, {"status": "success", "documents": []}):
        records, error = agents._evidence_records_from_artifact(
            "knowledge_expert_tool", "task", 1, {"query": "q"}, "arbitrary text",
            artifact, "k", 0,
        )
        assert records == [] and error is not None

    error_artifact = {"status": "error", "error_type": "retrieval_error"}
    records, error = agents._evidence_records_from_artifact(
        "knowledge_expert_tool", "task", 1, {"query": "q"}, "完全不同的错误文案",
        error_artifact, "k", 0,
    )
    assert records == [] and error is None

    empty_artifact = {"status": "empty", "documents": []}
    records, error = agents._evidence_records_from_artifact(
        "knowledge_expert_tool", "task", 1, {"query": "q"}, "没有找到匹配资料。",
        empty_artifact, "k", 0,
    )
    assert records == [] and error is None
