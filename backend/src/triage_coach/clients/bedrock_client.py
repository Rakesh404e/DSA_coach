"""Bedrock runtime client module for model invocations."""


def invoke(prompt: str) -> str:
    """Invoke the Bedrock model with the given prompt.

    Actual boto3 bedrock-runtime integration is configured in Phase 6.
    """
    raise NotImplementedError("Bedrock client invoke is implemented in Phase 6.")
