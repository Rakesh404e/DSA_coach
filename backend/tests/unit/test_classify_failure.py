"""Unit tests for classify_failure_node and related graph nodes."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Ensure backend/src is on sys.path
backend_src = Path(__file__).resolve().parents[2] / "src"
if str(backend_src) not in sys.path:
    sys.path.insert(0, str(backend_src))

from triage_coach.graph.nodes import (
    classify_failure_node,
    escalate_check_node,
    generate_hint_node,
    run_tests_node,
)
from triage_coach.problems.sample_problems import BINARY_SEARCH_PROBLEM, TWO_SUM_PROBLEM


def test_classify_failure_index_error_off_by_one_pattern():
    """IndexError should be classified as off_by_one without needing LLM."""
    mock_llm = MagicMock()
    state = {
        "session_id": "test_session",
        "problem_id": "binary_search",
        "code": "def binary_search(nums, target): return nums[len(nums)]",
        "test_results": [
            {
                "test_case": {"input": ([1, 2, 3], 2), "expected_output": 1},
                "passed": False,
                "actual_output": None,
                "error": "IndexError: list index out of range",
            }
        ],
        "failure_type": None,
        "hint_tier": 0,
        "attempt_count": 1,
        "hint_text": None,
        "resolved": False,
    }

    result = classify_failure_node(state, llm_invoke=mock_llm)
    assert result["failure_type"] == "off_by_one"
    mock_llm.assert_not_called()


def test_classify_failure_off_by_one_with_mocked_llm():
    """Off-by-one logical error (wrong loop boundary) classifies via mocked LLM."""
    mock_llm = MagicMock(return_value="off_by_one")
    state = {
        "session_id": "test_session",
        "problem_id": "binary_search",
        "code": BINARY_SEARCH_PROBLEM["buggy_variants"]["off_by_one"],
        "test_results": [
            {
                "test_case": {"input": ([1, 2, 3, 4, 5], 5), "expected_output": 4},
                "passed": False,
                "actual_output": -1,
                "error": None,
            }
        ],
        "failure_type": None,
        "hint_tier": 0,
        "attempt_count": 1,
        "hint_text": None,
        "resolved": False,
    }

    result = classify_failure_node(state, llm_invoke=mock_llm)
    assert result["failure_type"] == "off_by_one"
    mock_llm.assert_called_once()


def test_classify_failure_wrong_data_structure_fixture():
    """Wrong data structure bug fixture triggers mocked LLM classification."""
    mock_llm = MagicMock(return_value="wrong_data_structure")
    state = {
        "session_id": "test_session",
        "problem_id": "two_sum",
        "code": TWO_SUM_PROBLEM["buggy_variants"]["wrong_data_structure"],
        "test_results": [
            {
                "test_case": {"input": ([2, 7, 11, 15], 9), "expected_output": [0, 1]},
                "passed": False,
                "actual_output": [7, 2],
                "error": None,
            }
        ],
        "failure_type": None,
        "hint_tier": 0,
        "attempt_count": 1,
        "hint_text": None,
        "resolved": False,
    }

    result = classify_failure_node(state, llm_invoke=mock_llm)
    assert result["failure_type"] == "wrong_data_structure"
    mock_llm.assert_called_once()


def test_classify_failure_passed_fixture():
    """All tests passed should return failure_type 'passed' without calling LLM."""
    mock_llm = MagicMock()
    state = {
        "session_id": "test_session",
        "problem_id": "binary_search",
        "code": BINARY_SEARCH_PROBLEM["canonical_solution"],
        "test_results": [
            {
                "test_case": {"input": ([1, 2, 3], 2), "expected_output": 1},
                "passed": True,
                "actual_output": 1,
                "error": None,
            }
        ],
        "failure_type": None,
        "hint_tier": 0,
        "attempt_count": 1,
        "hint_text": None,
        "resolved": True,
    }

    result = classify_failure_node(state, llm_invoke=mock_llm)
    assert result["failure_type"] == "passed"
    mock_llm.assert_not_called()


def test_run_tests_node_executes_sandbox():
    """run_tests_node should invoke sandbox and populate test_results."""
    state = {
        "session_id": "test_session",
        "problem_id": "binary_search",
        "code": BINARY_SEARCH_PROBLEM["canonical_solution"],
        "test_results": [],
        "failure_type": None,
        "hint_tier": 0,
        "attempt_count": 0,
        "hint_text": None,
        "resolved": False,
    }

    res = run_tests_node(state)
    assert res["resolved"] is True
    assert len(res["test_results"]) == len(BINARY_SEARCH_PROBLEM["test_cases"])
    assert all(r["passed"] for r in res["test_results"])


def test_generate_hint_node_tier_enforcement():
    """Test hint generation respects tier restrictions and never provides tier 2 patch if tier < 2."""
    state_tier0 = {
        "session_id": "test_session",
        "problem_id": "binary_search",
        "code": "def binary_search(): pass",
        "test_results": [],
        "failure_type": "off_by_one",
        "hint_tier": 0,
        "attempt_count": 1,
        "hint_text": None,
        "resolved": False,
    }

    # Mock that tries to leak code at Tier 0
    leaky_mock = MagicMock(return_value="```python\ndef binary_search(): return 42\n```")
    res_tier0 = generate_hint_node(state_tier0, llm_invoke=leaky_mock)
    # Patch must be scrubbed / replaced with conceptual fallback
    assert "```" not in res_tier0["hint_text"]
    assert "def " not in res_tier0["hint_text"]

    # Tier 2 is allowed to provide code patch
    state_tier2 = dict(state_tier0, hint_tier=2)
    clean_mock = MagicMock(return_value="Here is the fix:\n```python\n# fix\n```")
    res_tier2 = generate_hint_node(state_tier2, llm_invoke=clean_mock)
    assert "```python" in res_tier2["hint_text"]


def test_escalate_check_node_increments_tier():
    """escalate_check_node should increment hint_tier and attempt_count."""
    state = {
        "session_id": "test_session",
        "problem_id": "two_sum",
        "code": "",
        "test_results": [],
        "failure_type": "wrong_data_structure",
        "hint_tier": 0,
        "attempt_count": 1,
        "hint_text": None,
        "resolved": False,
    }

    update = escalate_check_node(state)
    assert update["hint_tier"] == 1
    assert update["attempt_count"] == 2


# ==========================================
# Phase 6: AWS Clients & Config Unit Tests
# ==========================================
import io
import json
import os
import pytest
import boto3
from moto import mock_aws

from triage_coach import config
from triage_coach.clients import bedrock_client, dynamo_client


def test_config_reads_env_vars():
    """config should read MODEL_ID, AWS_REGION, and TABLE_NAME from env vars."""
    with patch.dict(os.environ, {
        "AWS_REGION": "us-west-2",
        "MODEL_ID": "test-model-id",
        "TABLE_NAME": "test_triage_table",
    }):
        assert config.AWS_REGION == "us-west-2"
        assert config.MODEL_ID == "test-model-id"
        assert config.TABLE_NAME == "test_triage_table"
        assert config.get_table_name() == "test_triage_table"


def test_config_missing_table_name_raises():
    """Accessing TABLE_NAME without setting it in env must raise ValueError (no fallback)."""
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match="TABLE_NAME"):
            _ = config.get_table_name()
        with pytest.raises(ValueError, match="TABLE_NAME"):
            _ = config.TABLE_NAME


def test_bedrock_client_invoke_mocked():
    """bedrock_client.invoke wraps invoke_model without making real AWS calls."""
    mock_body = io.BytesIO(
        json.dumps({
            "content": [{"text": "off_by_one"}]
        }).encode("utf-8")
    )
    mock_boto_client = MagicMock()
    mock_boto_client.invoke_model.return_value = {"body": mock_body}

    with patch("triage_coach.clients.bedrock_client.get_bedrock_client", return_value=mock_boto_client):
        result = bedrock_client.invoke("Analyze this error")
        assert result == "off_by_one"
        mock_boto_client.invoke_model.assert_called_once()


def test_dynamo_client_get_and_put_session_with_moto():
    """dynamo_client get_session and put_session tested with moto mock DynamoDB."""
    with patch.dict(os.environ, {
        "AWS_REGION": "us-east-1",
        "TABLE_NAME": "test_sessions_table",
        "AWS_ACCESS_KEY_ID": "testing",
        "AWS_SECRET_ACCESS_KEY": "testing",
    }):
        with mock_aws():
            dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
            dynamodb.create_table(
                TableName="test_sessions_table",
                KeySchema=[{"AttributeName": "session_id", "KeyType": "HASH"}],
                AttributeDefinitions=[{"AttributeName": "session_id", "AttributeType": "S"}],
                BillingMode="PAY_PER_REQUEST",
            )

            # Assert get on non-existent session returns None
            assert dynamo_client.get_session("non_existent") is None

            # Put session
            sample_state = {
                "problem_id": "two_sum",
                "code": "def two_sum(): pass",
                "test_results": [],
                "failure_type": "wrong_data_structure",
                "hint_tier": 1,
                "attempt_count": 2,
                "hint_text": "Sample hint",
                "resolved": False,
            }
            dynamo_client.put_session("sess_100", sample_state)

            # Get session
            saved = dynamo_client.get_session("sess_100")
            assert saved is not None
            assert saved["session_id"] == "sess_100"
            assert saved["problem_id"] == "two_sum"
            assert saved["hint_tier"] == 1
            assert saved["attempt_count"] == 2


# ==========================================
# Phase 7: Lambda Handler Unit Tests
# ==========================================
from triage_coach.handler import lambda_handler


def test_lambda_handler_options_preflight():
    event = {"httpMethod": "OPTIONS"}
    response = lambda_handler(event)
    assert response["statusCode"] == 200
    assert response["headers"]["Access-Control-Allow-Origin"] == "*"


def test_lambda_handler_missing_session_id():
    event = {
        "httpMethod": "POST",
        "body": json.dumps({"code": "pass", "problem_id": "binary_search"}),
    }
    response = lambda_handler(event)
    assert response["statusCode"] == 400
    assert "session_id" in response["body"]


def test_lambda_handler_invalid_json():
    event = {
        "httpMethod": "POST",
        "body": "invalid-json-content{",
    }
    response = lambda_handler(event)
    assert response["statusCode"] == 400
    assert "Invalid JSON" in response["body"]


def test_lambda_handler_fresh_submission():
    event = {
        "httpMethod": "POST",
        "body": json.dumps({
            "session_id": "test_h_1",
            "problem_id": "binary_search",
            "code": BINARY_SEARCH_PROBLEM["canonical_solution"],
            "user_still_stuck": False,
        }),
    }
    with patch("triage_coach.clients.dynamo_client.get_session", return_value=None):
        with patch("triage_coach.clients.dynamo_client.put_session") as mock_put:
            response = lambda_handler(event)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["resolved"] is True
    assert body["hint_text"] is None
    mock_put.assert_called_once()


def test_lambda_handler_escalation_request():
    existing_session = {
        "session_id": "test_h_2",
        "problem_id": "two_sum",
        "code": TWO_SUM_PROBLEM["buggy_variants"]["wrong_data_structure"],
        "test_results": [],
        "failure_type": "wrong_data_structure",
        "hint_tier": 0,
        "attempt_count": 1,
        "hint_text": "Tier 0 nudge",
        "resolved": False,
    }
    event = {
        "httpMethod": "POST",
        "body": json.dumps({
            "session_id": "test_h_2",
            "problem_id": "two_sum",
            "user_still_stuck": True,
        }),
    }
    with patch("triage_coach.clients.dynamo_client.get_session", return_value=existing_session):
        with patch("triage_coach.clients.dynamo_client.put_session") as mock_put:
            with patch("triage_coach.clients.bedrock_client.invoke", return_value="Focus on using a dictionary"):
                response = lambda_handler(event)

    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["hint_tier"] == 1
    assert body["attempt_count"] == 2
    mock_put.assert_called_once()


