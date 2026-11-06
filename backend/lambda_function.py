import base64
import json
import logging
import os
import uuid
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

TABLE_NAME = os.getenv("TASKS_TABLE_NAME", "tasks")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)

ALLOWED_STATUSES = {"pending", "in_progress", "done"}

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
}


def build_response(status_code, body=None):
    """Create an API Gateway proxy response with JSON body."""
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", **CORS_HEADERS},
        "body": json.dumps(body, default=str) if body is not None else "",
    }


def parse_event(event):
    """Support both REST API and HTTP API event formats."""
    method = event.get("httpMethod")
    if not method:
        request_context = event.get("requestContext", {})
        http_context = request_context.get("http", {})
        method = http_context.get("method")

    path = event.get("path") or event.get("rawPath") or ""
    path_parameters = event.get("pathParameters") or {}

    body = event.get("body")
    if body and event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    data = {}
    if body:
        try:
            data = json.loads(body)
            if not isinstance(data, dict):
                raise ValueError("Request body must be a JSON object")
        except (json.JSONDecodeError, ValueError) as exc:
            raise ValueError(str(exc)) from exc

    return (method or "").upper(), path, path_parameters, data


def get_task_id(path_parameters, path):
    """Extract the task id from path parameters or the request path."""
    if path_parameters.get("id"):
        return path_parameters["id"]

    segments = [segment for segment in path.strip("/").split("/") if segment]
    if len(segments) >= 2 and segments[-2] == "tasks":
        return segments[-1]
    return None


def scan_all_tasks():
    """Scan DynamoDB and handle pagination."""
    items = []
    scan_kwargs = {}
    while True:
        result = table.scan(**scan_kwargs)
        items.extend(result.get("Items", []))
        last_key = result.get("LastEvaluatedKey")
        if not last_key:
            break
        scan_kwargs["ExclusiveStartKey"] = last_key
    items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    return items


def handle_get_tasks():
    tasks = scan_all_tasks()
    return build_response(200, {"tasks": tasks, "count": len(tasks)})


def handle_create_task(data):
    title = str(data.get("title", "")).strip()
    description = str(data.get("description", "")).strip()

    if not title:
        return build_response(400, {"error": "title is required"})
    if len(title) > 200:
        return build_response(400, {"error": "title must be 200 characters or fewer"})
    if len(description) > 1000:
        return build_response(400, {"error": "description must be 1000 characters or fewer"})

    item = {
        "id": str(uuid.uuid4()),
        "title": title,
        "description": description,
        "status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    table.put_item(Item=item)
    logger.info("Created task %s", item["id"])
    return build_response(201, item)
def handle_update_task(task_id, data):
    if not task_id:
        return build_response(400, {"error": "task id is required"})

    existing = table.get_item(Key={"id": task_id}).get("Item")
    if not existing:
        return build_response(404, {"error": "task not found"})

    updates = {}
    if "title" in data:
        title = str(data["title"]).strip()
        if not title:
            return build_response(400, {"error": "title cannot be empty"})
        if len(title) > 200:
            return build_response(400, {"error": "title must be 200 characters or fewer"})
        updates["title"] = title

    if "description" in data:
        description = str(data["description"]).strip()
        if len(description) > 1000:
            return build_response(400, {"error": "description must be 1000 characters or fewer"})
        updates["description"] = description

    if "status" in data:
        status = str(data["status"]).strip()
        if status not in ALLOWED_STATUSES:
            return build_response(
                400,
                {"error": "status must be one of: " + ", ".join(sorted(ALLOWED_STATUSES))},
            )
        updates["status"] = status

    if not updates:
        return build_response(400, {"error": "no valid fields to update"})

    expression = "SET " + ", ".join(f"#{key} = :{key}" for key in updates)
    expression_names = {f"#{key}": key for key in updates}
    expression_values = {f":{key}": value for key, value in updates.items()}

    try:
        table.update_item(
            Key={"id": task_id},
            UpdateExpression=expression,
            ExpressionAttributeNames=expression_names,
            ExpressionAttributeValues=expression_values,
            ConditionExpression="attribute_exists(id)",
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return build_response(404, {"error": "task not found"})
        raise

    updated = table.get_item(Key={"id": task_id}).get("Item", {})
    logger.info("Updated task %s", task_id)
    return build_response(200, updated)


def handle_delete_task(task_id):
    if not task_id:
        return build_response(400, {"error": "task id is required"})

    try:
        table.delete_item(
            Key={"id": task_id},
            ConditionExpression="attribute_exists(id)",
        )
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return build_response(404, {"error": "task not found"})
        raise

    logger.info("Deleted task %s", task_id)
    return build_response(200, {"message": "Task deleted", "id": task_id})


def lambda_handler(event, context):
    """AWS Lambda entry point."""
    try:
        method, path, path_parameters, data = parse_event(event)
        logger.info("Request: %s %s", method, path)

        if method == "OPTIONS":
            return build_response(204)

        task_id = get_task_id(path_parameters, path)
        normalized_path = path.rstrip("/")

        if normalized_path.endswith("/tasks"):
            if method == "GET":
                return handle_get_tasks()
            if method == "POST":
                return handle_create_task(data)
            return build_response(405, {"error": f"Method {method} not allowed for /tasks"})

        if task_id:
            if method == "PUT":
                return handle_update_task(task_id, data)
            if method == "DELETE":
                return handle_delete_task(task_id)
            if method == "GET":
                item = table.get_item(Key={"id": task_id}).get("Item")
                if not item:
                    return build_response(404, {"error": "task not found"})
                return build_response(200, item)
            return build_response(405, {"error": f"Method {method} not allowed for /tasks/{{id}}"})

        return build_response(404, {"error": "route not found"})

    except ValueError as exc:
        logger.warning("Bad request: %s", exc)
        return build_response(400, {"error": str(exc)})
    except ClientError as exc:
        logger.exception("DynamoDB error: %s", exc)
        return build_response(500, {"error": "database error"})
    except Exception as exc:  # pragma: no cover - safety net for Lambda
        logger.exception("Unexpected error: %s", exc)
        return build_response(500, {"error": "internal server error"})

