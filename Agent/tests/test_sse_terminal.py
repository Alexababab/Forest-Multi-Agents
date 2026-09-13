import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi.testclient import TestClient

import api


class FakeApp:
    def __init__(self, events=None, error=None):
        self.events = events or []
        self.error = error

    def stream(self, initial_state, config=None):
        for event in self.events:
            yield event
        if self.error:
            raise self.error


def _post(fake_app):
    api.forestry_app = fake_app
    client = TestClient(api.app)
    return client.post(
        "/api/analyze-stream",
        files={"image": ("test.jpg", b"fake image", "image/jpeg")},
        data={"prompt": "test"},
    )


def _event_lines(text, name):
    return [line for line in text.splitlines() if line == f"event: {name}"]


def test_success_requires_final_report():
    response = _post(FakeApp([
        {"planner_node": {"plan_loop_count": 1}},
        {"finalizer_node": {
            "messages": [("ai", "final report")],
            "finalizer_result": {"status": "success", "report": "final report", "error_type": None},
        }},
    ]))
    assert response.status_code == 200
    assert '"success": true' in response.text
    assert len(_event_lines(response.text, "run_completed")) == 1
    assert len(_event_lines(response.text, "error")) == 0


def test_normal_end_without_report_is_failure():
    response = _post(FakeApp([{"planner_node": {"plan_loop_count": 1}}]))
    assert '"message": "分析未能完成，未生成最终报告。"' in response.text
    assert '"success": false' in response.text
    assert len(_event_lines(response.text, "run_completed")) == 1


def test_generator_exception_is_failure():
    response = _post(FakeApp(error=RuntimeError("secret backend detail")))
    assert '"message": "分析未能完成，请稍后重试。"' in response.text
    assert "secret backend detail" not in response.text
    assert '"success": false' in response.text
    assert len(_event_lines(response.text, "error")) == 1
    assert len(_event_lines(response.text, "run_completed")) == 1


def test_finalizer_completed_without_extractable_report_is_failure():
    response = _post(FakeApp([{"finalizer_node": {"messages": []}}]))
    assert '"success": false' in response.text
    assert len(_event_lines(response.text, "run_completed")) == 1
