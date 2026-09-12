"""Application configuration loaded from environment variables."""

import os

DEFAULT_AWS_REGION = "us-east-1"
DEFAULT_MODEL_ID = "anthropic.claude-3-haiku-20240307-v1:0"


def get_aws_region() -> str:
    """Return AWS_REGION from environment, defaulting to us-east-1."""
    return os.getenv("AWS_REGION", DEFAULT_AWS_REGION)


def get_model_id() -> str:
    """Return MODEL_ID from environment, defaulting to Claude 3 Haiku."""
    return os.getenv("MODEL_ID", DEFAULT_MODEL_ID)


def get_table_name() -> str:
    """Return TABLE_NAME from environment variables.

    Raises ValueError if TABLE_NAME is not explicitly set (no fallback allowed).
    """
    table_name = os.getenv("TABLE_NAME")
    if not table_name:
        raise ValueError("TABLE_NAME environment variable is required and must be set explicitly.")
    return table_name


def __getattr__(name: str):
    if name == "TABLE_NAME":
        return get_table_name()
    if name == "AWS_REGION":
        return get_aws_region()
    if name == "MODEL_ID":
        return get_model_id()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

