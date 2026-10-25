#!/usr/bin/env python3
"""seeded-server: an MCP server with PLANTED defects for agentic-maker's MCP audit (the planted defects and what finds them are tabulated in docs/evidence/06-audit-mcp.md)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _mini import main  # noqa: E402

LONG = ("Retrieves a single user record from the directory service. " * 12).strip()   # ~700 characters


def tool(name, description, props=None, required=None, annotations=None, schema=None):
    t = {"name": name}
    if description is not None:
        t["description"] = description
    t["inputSchema"] = schema or {"type": "object", "properties": props or {}, "required": required or []}
    if annotations:
        t["annotations"] = annotations
    return t


TOOLS = [
    tool("get_user", "Get a user by id.", {"id": {"type": "string", "description": "user id"}}, ["id"]),
    tool("fetch_user", "Get a user by id.", {"id": {"type": "string", "description": "user id"}}, ["id"]),          # D: near-duplicate of get_user
    tool("Get-User Info", LONG, {"id": {"type": "string"}}, ["id"]),                                              # D: unsafe name, 700-char description
    tool("ping_thing", None, {}),                                                                                 # D: no description
    tool("delete_account", "Delete an account permanently.", {"id": {"type": "string", "description": "account id"}}, ["id"]),  # D: destructive, no annotations
    tool("export_all", "Export every record.", {}),                                                               # D: 50 KB response
    tool("create_ticket", "Create a support ticket.", {                                                          # D: 9 params, nested 3 deep
        "title": {"type": "string"}, "body": {"type": "string"}, "priority": {"type": "string"}, "assignee": {"type": "string"},
        "labels": {"type": "array", "items": {"type": "string"}}, "due": {"type": "string"}, "project": {"type": "string"},
        "reporter": {"type": "object", "properties": {"contact": {"type": "object", "properties": {"phone": {"type": "object", "properties": {"number": {"type": "string"}}}}}}},
        "notify": {"type": "boolean"}},
        ["title", "body", "priority", "assignee", "labels", "due", "project", "reporter"]),
    tool("search", "Search records.", schema={"type": "object", "oneOf": [{"properties": {"q": {"type": "string"}}}, {"properties": {"id": {"type": "string"}}}]}),  # D: top-level oneOf
    tool("set_region", "Set the region.", {"region": {"type": "string", "enum": ["r%d" % i for i in range(14)], "description": "region"}}, ["region"]),  # D: 14-value enum
] + [tool("list_report_%d" % i, "List report %d rows." % i, {"limit": {"type": "integer", "description": "max rows"}}, [], {"readOnlyHint": True}) for i in range(1, 16)]   # 24 tools in all


def get_user(a):
    if a.get("id") in ("1", "2"):
        return {"content": [{"type": "text", "text": '{"id": "%s"}' % a["id"]}], "isError": False}
    return {"content": [{"type": "text", "text": "Error: user not found"}], "isError": False}      # D: failure reported as success


SPEC = {"name": "seeded-server", "banner": "Seeded server starting...", "tools": TOOLS,            # D: banner on stdout
        "handlers": {"get_user": get_user,
                     "export_all": lambda a: {"content": [{"type": "text", "text": "row," * 12500}], "isError": False}}}

if __name__ == "__main__":
    main(SPEC)
