# Python: form-mode and URL-mode elicitation

> Read when: you are implementing `elicitation/create` for a missing argument or a URL-mode flow for OAuth or secrets in a Python MCP server.

Core rules: `../../mcp/protocol-elicitation.md`. Gating and fallbacks: `advanced-protocol.md`.

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 4: Use Elicitation To Clarify Missing Arguments, Not To Fish For Secrets -->
## Form mode with a flat model

```python
from mcp.server.fastmcp import Context, FastMCP
from pydantic import BaseModel, Field

mcp = FastMCP("booking")

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
        if result.action == "accept" and result.data and result.data.checkAlternative:
            return f"[SUCCESS] Booked for {result.data.alternativeDate}"
        return "[CANCELLED] Booking cancelled"
    return f"[SUCCESS] Booked for {date} at {time}"
```

<!-- src: audit-agentic-mcp/references/patterns/advanced-protocol.md#Pattern 5: URL-Mode Elicitation For OAuth, Secrets, And Payments -->
## URL mode with identity-bound state

```python
# FastMCP-style; raw SDKs use raise UrlElicitationRequiredError. ctx.elicit_url and ctx.user_sub are
# illustrative: confirm the method names against your SDK version
import asyncio
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
    # The call above returns when the user answers the prompt; the backend finishes out-of-band, so poll
    for _ in range(30):
        if state_store.get(eid, {}).get("status") == "granted":
            return "Stripe connected."
        await asyncio.sleep(2)
    return "Connection not completed."
```
