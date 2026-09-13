import json
import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

# Ensure parent directory is on sys.path for Lambda runtime
pkg_parent = Path(__file__).resolve().parent.parent
if str(pkg_parent) not in sys.path:
    sys.path.insert(0, str(pkg_parent))

from langgraph.types import Command

from triage_coach.clients import dynamo_client
from triage_coach.graph.build_graph import graph
from triage_coach.graph.nodes import synthesize_problem_from_prompt


class DecimalEncoder(json.JSONEncoder):
    """Serialize DynamoDB Decimal numbers to native Python int or float."""
    def default(self, obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return int(obj) if obj % 1 == 0 else float(obj)
        return super().default(obj)


def _response(status_code: int, body: Any) -> dict[str, Any]:
    """Helper to format API Gateway JSON response with CORS headers."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type,Authorization",
            "Access-Control-Allow-Methods": "OPTIONS,POST",
        },
        "body": json.dumps(body, cls=DecimalEncoder),
    }


def lambda_handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """Parse API Gateway event, evaluate via LangGraph, persist state, and return response."""
    try:
        # Handle CORS preflight OPTIONS requests
        if event.get("httpMethod") == "OPTIONS":
            return _response(200, {"message": "OK"})

        raw_body = event.get("body", {})
        if isinstance(raw_body, str):
            try:
                payload = json.loads(raw_body)
            except json.JSONDecodeError:
                return _response(400, {"error": "Invalid JSON in request body"})
        elif isinstance(raw_body, dict):
            payload = raw_body
        else:
            payload = {}

        # Check for problem synthesis action
        action = payload.get("action")
        if action == "synthesize_problem":
            prompt_text = payload.get("prompt", "")
            if not prompt_text:
                return _response(400, {"error": "Missing 'prompt' for problem synthesis"})
            try:
                synthesized = synthesize_problem_from_prompt(prompt_text)
                return _response(200, synthesized)
            except Exception as synth_err:
                return _response(500, {"error": f"Synthesis error: {synth_err}"})

        session_id = payload.get("session_id")
        code = payload.get("code", "")
        problem_id = payload.get("problem_id", "")
        custom_problem = payload.get("custom_problem")
        user_still_stuck = bool(payload.get("user_still_stuck", False))

        if not session_id:
            return _response(400, {"error": "Missing required field: 'session_id'"})

        # Load or initialize session state from DynamoDB
        try:
            session_state = dynamo_client.get_session(session_id)
        except Exception:
            session_state = None

        if not session_state:
            session_state = {
                "session_id": session_id,
                "problem_id": problem_id,
                "code": code,
                "test_results": [],
                "failure_type": None,
                "hint_tier": 0,
                "attempt_count": 0,
                "hint_text": None,
                "resolved": False,
            }
        else:
            if code:
                session_state["code"] = code
            if problem_id:
                session_state["problem_id"] = problem_id

        if custom_problem:
            session_state["custom_problem"] = custom_problem

        # Run compiled graph starting from appropriate entrypoint
        try:
            if user_still_stuck:
                # Escalation request: resume from escalate_check
                final_state = graph.invoke(
                    Command(goto="escalate_check", update=session_state)
                )
            else:
                # Fresh code submission: run full test and triage pipeline
                final_state = graph.invoke(session_state)
        except Exception as err:
            return _response(500, {"error": f"Graph execution failure: {err}"})

        # Persist updated session state back to DynamoDB
        try:
            dynamo_client.put_session(session_id, final_state)
        except Exception as db_err:
            # Non-fatal: even if DynamoDB fails, return the triage results to the user
            final_state["db_warning"] = str(db_err)

        return _response(200, final_state)

    except Exception as fatal_err:
        return _response(500, {"error": f"Internal server error: {fatal_err}"})
