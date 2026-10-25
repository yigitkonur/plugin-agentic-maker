#!/usr/bin/env python3
"""clean-server: the same service done right. The audit must report no High or Critical finding here."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _mini import main  # noqa: E402

RO = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}


def tool(name, description, props, required, annotations):
    return {"name": name, "description": description, "annotations": annotations,
            "inputSchema": {"type": "object", "properties": props, "required": required}}


TOOLS = [
    tool("get_user", "Get one user by id. Use list_users first if you only have a name.", {"id": {"type": "string", "description": "User id, e.g. 42"}}, ["id"], RO),
    tool("list_users", "List users, newest first. Returns at most 20 per page; pass the returned cursor for more.",
         {"cursor": {"type": "string", "description": "Cursor from the previous page"}, "limit": {"type": "integer", "description": "1-20, default 20"}}, [], RO),
    tool("delete_user", "Delete one user permanently. Ask the user to confirm first.", {"id": {"type": "string", "description": "User id"}}, ["id"],
         {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": False}),
]


def get_user(a):
    if a.get("id") in ("1", "2"):
        return {"content": [{"type": "text", "text": '{"id": "%s", "name": "user %s"}' % (a["id"], a["id"])}], "isError": False}
    return {"content": [{"type": "text", "text": "No user with id '%s'. Call list_users to find valid ids." % a.get("id")}], "isError": True}


SPEC = {"name": "clean-server", "instructions": "Look users up with list_users, then get_user.", "tools": TOOLS, "handlers": {"get_user": get_user}}

if __name__ == "__main__":
    main(SPEC)
