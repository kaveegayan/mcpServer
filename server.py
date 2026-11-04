import os
import httpx
from mcp.server.fastmcp import FastMCP

API_BASE = os.environ.get("API_BASE", "http://host.docker.internal:8000")

mcp = FastMCP("users-api", host="0.0.0.0", port=8001)

@mcp.tool()
def get_user(user_id: int) -> dict:
    """Get a user's name, email and role using numeric user ID."""
    try:
        r = httpx.get(f"{API_BASE}/users/{user_id}", timeout=10)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPStatusError as e:
        return {"status": "error", "message": f"API returned {e.response.status_code}"}
    except httpx.RequestError as e:
        return {"status": "error", "message": f"Could not reach API: {type(e).__name__}"}

if __name__ == "__main__":
    mcp.run(transport="streamable-http")