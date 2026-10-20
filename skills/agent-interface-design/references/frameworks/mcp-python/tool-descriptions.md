# Python MCP tool description and enum examples

> Read when: you are writing Python tool descriptions or enum-constrained parameters for an MCP server.

Explanation and rules: ../../mcp/descriptions-structure-and-length.md and ../../mcp/descriptions-names-and-routing.md

## Pattern 2: Description that briefs a new hire

```python
@tool(
    name="search_contacts",
    description="""Search the CRM for contacts matching criteria.

    Returns contact records with name, email, and company.
    Use this when the user asks to find, look up, or search for people.
    Do NOT use this for updating contacts - use update_contact instead.

    Example: search_contacts(query="Jane at Acme") returns matching contacts.
    Supports partial name matching and company name filtering."""
)
```

## Pattern 5: Strict input schemas with enums and constraints

```python
from enum import Enum

class SortOrder(str, Enum):
    ASC = "ascending"
    DESC = "descending"

class DateRange(str, Enum):
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    ALL_TIME = "all_time"

@tool
def search_activity(
    space_id: str,
    sort: SortOrder = SortOrder.DESC,
    date_range: DateRange = DateRange.LAST_30_DAYS,
    limit: int = 25  # constrained via Field(ge=1, le=100)
) -> dict:
    """Search member activity in a space."""
```

What this gives you: models see the enum values in the schema and pick from them; invalid values are caught before execution with clear validation errors; defaults reduce the parameters the model must decide on; type hints auto-generate JSON Schema in frameworks such as FastMCP.
