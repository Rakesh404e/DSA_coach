"""Amazon DynamoDB client wrapper for session state persistence."""

from typing import Any

import boto3

from triage_coach import config


def get_table(table_name: str | None = None) -> Any:
    """Return boto3 DynamoDB Table resource."""
    name = table_name or config.TABLE_NAME
    dynamodb = boto3.resource("dynamodb", region_name=config.AWS_REGION)
    return dynamodb.Table(name)


def get_session(session_id: str, table: Any = None) -> dict[str, Any] | None:
    """Retrieve session state dict by session_id from DynamoDB Table, or None if not found."""
    tbl = table if table is not None else get_table()
    response = tbl.get_item(Key={"session_id": session_id})
    item = response.get("Item")
    if not item:
        return None
    return dict(item)


def put_session(session_id: str, state: dict[str, Any], table: Any = None) -> None:
    """Save session state dict to DynamoDB Table keyed by session_id."""
    tbl = table if table is not None else get_table()
    item = dict(state)
    item["session_id"] = session_id
    tbl.put_item(Item=item)
