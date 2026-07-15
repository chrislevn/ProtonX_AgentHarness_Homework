"""
Tool Registry - 6-step pipeline:
1. Validate Schema
2. Check Authentication
3. Check Scopes
4. Check Rate Limit
5. Audit Log
6. Execute Tool
"""

import time
import json
from datetime import datetime
from typing import Any
from .models import ToolDefinition


# ============================================================
# Step 1: VALIDATE SCHEMA
# ============================================================

def validate_schema(tool: ToolDefinition, arguments: dict) -> dict:
    """Validate tool arguments against the tool's input_schema."""
    schema = tool.input_schema
    properties = schema.get("properties", {})

    for field in schema.get("required", []):
        if field not in arguments:
            raise ValueError(f"[SCHEMA] Missing required field: '{field}'")

    type_map = {"string": str, "integer": int, "number": (int, float), "boolean": bool}
    for key, value in arguments.items():
        prop = properties.get(key)
        if not prop:
            continue

        expected = prop.get("type")
        if expected in type_map:
            # bool is a subclass of int, so reject it explicitly for numeric fields
            wrong_type = not isinstance(value, type_map[expected])
            if wrong_type or (expected in ("integer", "number") and isinstance(value, bool)):
                raise ValueError(
                    f"[SCHEMA] Field '{key}' expected {expected}, got {type(value).__name__}"
                )

        enum_values = prop.get("enum")
        if enum_values and value not in enum_values:
            raise ValueError(
                f"[SCHEMA] Field '{key}' must be one of {enum_values}, got '{value}'"
            )

    return arguments


# ============================================================
# Step 2: CHECK AUTHENTICATION
# ============================================================

USER_DB: dict[str, dict] = {
    "sk-admin-001": {
        "user_id": "user_admin",
        "role": "admin",
        "scopes": [
            "drive:read",
            "memory:read", "memory:write",
        ],
    },
    "sk-user-002": {
        "user_id": "user_standard",
        "role": "user",
        "scopes": [
            "drive:read",
            "memory:read",
        ],
    },
}


def check_authentication(api_key: str) -> dict:
    """Authenticate user by API key."""
    if not api_key:
        raise PermissionError("[AUTH] No API key provided")

    user = USER_DB.get(api_key)
    if not user:
        raise PermissionError(f"[AUTH] Invalid API key: '{api_key[:8]}...'")

    print(f"  [Step 2] Auth OK - user={user['user_id']}, role={user['role']}")
    return user


# ============================================================
# Step 3: CHECK SCOPES
# ============================================================

def check_scopes(user: dict, tool: ToolDefinition) -> bool:
    """Check if user has required scopes for the tool."""
    user_scopes = set(user.get("scopes", []))
    required = set(tool.required_scopes)
    missing = required - user_scopes

    if missing:
        raise PermissionError(
            f"[SCOPES] User '{user['user_id']}' missing scopes: {missing}. "
            f"Has: {user_scopes}"
        )

    print(f"  [Step 3] Scopes OK - required={required}")
    return True


# ============================================================
# Step 4: RATE LIMIT
# ============================================================

class RateLimiter:
    def __init__(self, max_calls: int = 10, window_seconds: int = 60):
        self.max_calls = max_calls
        self.window_seconds = window_seconds
        self._buckets: dict[str, list[float]] = {}

    def check(self, user_id: str) -> bool:
        """Check if user is within rate limit."""
        now = time.time()
        bucket = self._buckets.setdefault(user_id, [])

        # Drop timestamps that fell out of the window
        bucket[:] = [t for t in bucket if now - t < self.window_seconds]

        if len(bucket) >= self.max_calls:
            retry_in = self.window_seconds - (now - bucket[0])
            raise RuntimeError(
                f"[RATE LIMIT] User '{user_id}' exceeded {self.max_calls} calls "
                f"per {self.window_seconds}s. Retry in {retry_in:.0f}s"
            )

        bucket.append(now)
        print(f"  [Step 4] Rate Limit OK - {self.max_calls - len(bucket)}/{self.max_calls} calls remaining")
        return True


rate_limiter = RateLimiter(max_calls=20, window_seconds=60)


# ============================================================
# Step 5: AUDIT LOG
# ============================================================

AUDIT_LOG: list[dict] = []


def audit_log(user: dict, tool_name: str, arguments: dict, result: Any = None,
              error: str = None, latency_ms: float = None):
    """Record tool call in the audit log."""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "user_id": user["user_id"],
        "role": user["role"],
        "tool": tool_name,
        "arguments": arguments,
        "result": str(result)[:200] if result is not None else None,
        "latency_ms": round(latency_ms, 1) if latency_ms is not None else None,
        "error": error,
        "status": "success" if not error else "failed",
    }
    AUDIT_LOG.append(entry)
    print(f"  [Step 5] Audit Log - {'OK' if not error else f'FAILED: {error}'}")
    return entry


# ============================================================
# Step 6: EXECUTE TOOL
# ============================================================

def execute_tool(tool: ToolDefinition, arguments: dict) -> Any:
    """Execute the tool handler with validated arguments."""
    result = tool.handler(**arguments)
    print(f"  [Step 6] Execute OK - result: {json.dumps(result, ensure_ascii=False, default=str)[:100]}")
    return result


# ============================================================
# TOOL REGISTRY
# ============================================================

class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool: ToolDefinition):
        self._tools[tool.name] = tool
        print(f"[Registry] Registered tool: '{tool.name}'")

    def get_tool(self, name: str) -> ToolDefinition:
        tool = self._tools.get(name)
        if not tool:
            raise KeyError(f"[Registry] Tool '{name}' not found. Available: {list(self._tools.keys())}")
        return tool

    def list_tools(self) -> list[dict]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
            }
            for t in self._tools.values()
        ]

    def call(self, tool_name: str, arguments: dict, api_key: str) -> dict:
        """
        Run the 6-step pipeline: Schema → Auth → Scopes → Rate Limit → Execute → Audit.
        """
        print(f"\n{'='*60}")
        print(f"  TOOL CALL: {tool_name}")
        print(f"  Arguments: {json.dumps(arguments, ensure_ascii=False)}")
        print(f"{'='*60}")

        user = None
        started = time.time()
        try:
            # Step 1: Validate Schema
            tool = self.get_tool(tool_name)
            validated_args = validate_schema(tool, arguments)
            print(f"  [Step 1] Schema Valid OK")

            # Step 2: Check Authentication
            user = check_authentication(api_key)

            # Step 3: Check Scopes
            check_scopes(user, tool)

            # Step 4: Check Rate Limit
            rate_limiter.check(user["user_id"])

            # Step 5 + 6: Execute & Audit
            result = execute_tool(tool, validated_args)
            latency_ms = (time.time() - started) * 1000
            audit_log(user, tool_name, arguments, result=result, latency_ms=latency_ms)

            print(f"{'='*60}\n")
            return {"result": result}

        except Exception as e:
            error_msg = str(e)
            if user:
                latency_ms = (time.time() - started) * 1000
                audit_log(user, tool_name, arguments, error=error_msg, latency_ms=latency_ms)
            print(f"  [ERROR] {error_msg}")
            print(f"{'='*60}\n")
            return {"error": error_msg}

    def get_audit_log(self) -> list[dict]:
        return AUDIT_LOG
