"""Amazon Bedrock runtime client wrapper."""

import json
from typing import Any

import boto3

from triage_coach import config


def get_bedrock_client() -> Any:
    """Instantiate a boto3 bedrock-runtime client."""
    return boto3.client("bedrock-runtime", region_name=config.AWS_REGION)


def invoke(prompt: str, client: Any = None) -> str:
    """Invoke the Bedrock model with prompt and return the model's text response.

    Wraps boto3.client("bedrock-runtime").invoke_model.
    """
    bedrock = client if client is not None else get_bedrock_client()
    model_id = config.MODEL_ID

    body = json.dumps({
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 1024,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    })

    response = bedrock.invoke_model(
        modelId=model_id,
        body=body,
        contentType="application/json",
        accept="application/json",
    )

    raw_body = response.get("body")
    if hasattr(raw_body, "read"):
        content_str = raw_body.read()
        if isinstance(content_str, bytes):
            content_str = content_str.decode("utf-8")
        parsed = json.loads(content_str)
    elif isinstance(raw_body, str):
        parsed = json.loads(raw_body)
    elif isinstance(raw_body, dict):
        parsed = raw_body
    else:
        parsed = {}

    # Extract text from Claude messages format
    if "content" in parsed and isinstance(parsed["content"], list) and parsed["content"]:
        return parsed["content"][0].get("text", "")
    elif "generation" in parsed:
        return parsed["generation"]
    elif "completion" in parsed:
        return parsed["completion"]
    elif "outputs" in parsed and parsed["outputs"]:
        return parsed["outputs"][0].get("text", "")

    return str(parsed)
