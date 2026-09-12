"""AWS Lambda entrypoint handler for API Gateway triage requests."""

import json
import sys
from pathlib import Path
from typing import Any

# Ensure parent directory is on sys.path for Lambda runtime
pkg_parent = Path(__file__).resolve().parent.parent
if str(pkg_parent) not in sys.path:
    sys.path.insert(0, str(pkg_parent))

from langgraph.types import Command

from triage_coach.clients import dynamo_client
from triage_coach.graph.build_graph import graph


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
        "body": json.dumps(body),
    }


def lambda_handler(event: dict[str, Any], context: Any = None) -> dict[str, Any]:
    """Parse API Gateway event, evaluate via LangGraph, persist state, and return response."""
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

    session_id = payload.get("session_id")
    code = payload.get("code", "")
    problem_id = payload.get("problem_id", "")
    user_still_stuck = bool(payload.get("user_still_stuck", False))

    if not session_id:
        return _response(400, {"error": "Missing required field: 'session_id'"})

    # Load or initialize session state from DynamoDB
    session_state = dynamo_client.get_session(session_id)
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
        return _response(500, {"error": f"State persistence failure: {db_err}"})

    return _response(200, final_state)
