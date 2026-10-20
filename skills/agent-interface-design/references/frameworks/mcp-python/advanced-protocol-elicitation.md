# Python: form-mode and URL-mode elicitation

> Read when: you are implementing `elicitation/create` for a missing argument or a URL-mode flow for OAuth or secrets in a Python MCP server.

Core rules: `../../mcp/protocol-elicitation.md`. Gating and fallbacks: `advanced-protocol.md`.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 4: Use Elicitation To Clarify Missing Arguments, Not To Fish For Secrets -->
## Form mode with a flat model

```python
from pydantic import BaseModel, Field

class BookingPreferences(BaseModel):
    checkAlternative: bool = Field(description="Would you like to check another date?")
    alternativeDate: str = Field(default="2024-12-26", description="Alternative date (YYYY-MM-DD)")

@mcp.tool()
async def book_table(date: str, time: str, party_size: int, ctx: Context) -> str:
    if date == "2024-12-25":
        result = await ctx.elicit(
            message=f"No tables for {party_size} on {date}. Another date?",
            schema=BookingPreferences,
        )
        if result.action == "accept" and result.data:
            return f"[SUCCESS] Booked for {result.data.alternativeDate}"
        return "[CANCELLED] Booking cancelled"
    return f"[SUCCESS] Booked for {date} at {time}"
```

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 5: URL-Mode Elicitation For OAuth, Secrets, And Payments -->
## URL mode with identity-bound state

```python
# FastMCP-style; raw SDKs use raise UrlElicitationRequiredError
import uuid

@mcp.tool()
async def connect_stripe(ctx: Context) -> str:
    eid = str(uuid.uuid4())
    state_store.put(eid, {"user": ctx.user_sub, "status": "pending"})
    result = await ctx.elicit_url(
        message="Connect your Stripe account to continue.",
        url=f"https://auth.example.com/stripe/start?state={eid}",
        elicitation_id=eid,
    )
    # Backend completes out-of-band; poll or wait
    if state_store.get(eid)["status"] == "granted":
        return "Stripe connected."
    return "Connection not completed."
```
