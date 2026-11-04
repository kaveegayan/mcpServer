# mcp-server

A small MCP server that lets Claude read user details from my own API. It runs in Docker on my Ubuntu server.

I built it to learn how MCP works and to see Claude use a real tool on my own data.

## How it works

My API already reads from MySQL. The MCP server sits in front of it and passes Claude's requests on.

```
Claude -> Cloudflare tunnel -> MCP container (8001) -> FastAPI (8000) -> MySQL
```

The API is not changed. The MCP server only calls it over HTTP.

## Tool

| Tool | What it does |
|---|---|
| `get_user(user_id)` | Returns the name, email and role for one user ID |

The server only reads data. There is no tool that writes to the database or runs SQL.

## Requirements

- Ubuntu with Docker
- The FastAPI and MySQL API running on port 8000, listening on `0.0.0.0`
- `cloudflared` for the public HTTPS link
- A Claude account (the free plan allows one custom connector)

## Files

- `server.py`: the MCP server
- `Dockerfile`: builds the image

## Setup

Build the image:

```bash
docker build -t mcp-server .
```

Run the container:

```bash
docker run -d --name mcp-server --restart unless-stopped \
  --add-host=host.docker.internal:host-gateway \
  -e API_BASE=http://host.docker.internal:8000 \
  -p 127.0.0.1:8001:8001 \
  mcp-server
```

Check the logs:

```bash
docker logs mcp-server
```

You should see `Uvicorn running on http://0.0.0.0:8001`.

### What the options do

- `--add-host=host.docker.internal:host-gateway` lets the container reach the API on the host. Linux needs this set by hand.
- `API_BASE` is the address of the API. Change it if your API is somewhere else.
- `127.0.0.1:8001:8001` keeps the port open to the server only. The tunnel runs on the same machine, so it does not need more.

## Test it

Opening `/mcp` in a browser gives a `406 Not Acceptable` error. That is normal. The endpoint expects an MCP client.

Check it with curl:

```bash
curl -i http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"curl","version":"0"}}}'
```

A `200 OK` with an `mcp-session-id` header means the server is working.

To call the tool by hand, use the MCP Inspector:

```bash
apt install npm 
npx @modelcontextprotocol/inspector
```

Choose Streamable HTTP, enter `http://localhost:8001/mcp`, open Tools and run `get_user` with `1`.(this will run only in browser same host)

## Connect it to Claude

Claude calls the server from Anthropic's cloud, so `localhost` will not work. It needs a public HTTPS link.

1. Start a tunnel:

   ```bash
   cloudflared tunnel --url http://localhost:8001
   ```

2. Copy the `https://....trycloudflare.com` address it prints.
3. In claude.ai go to Customize, then Connectors, then Add custom connector.
4. Use the tunnel address with `/mcp` on the end (Ex: https://....trycloudflare.com/mcp)
5. Start a new chat and ask: "Use the users-api tool to get user 1."

Keep the tunnel running. The address changes each time you restart it, so the connector needs updating.

## Security

- The quick tunnel link is public and has no login. I use it for testing only.
- Keep the tool read-only.
- Stop the tunnel when I am not using it.
- For anything permanent, use a named tunnel with my own domain and add OAuth.

## Troubleshooting

| Problem | What to check |
|---|---|
| Container keeps restarting | Run `docker logs mcp-server` and read the error |
| Tool says it could not reach the API | Check the API listens on `0.0.0.0:8000`. Check `API_BASE`. If UFW is on, allow the Docker network to port 8000 |
| Claude times out | Check the tunnel is running and the URL ends in `/mcp` |
| `421 Invalid Host header` | The MCP library is rejecting the tunnel host name. Check the SDK version and its transport security settings |

## What I learned

- The newest `mcp` package (2.x) renamed `FastMCP` to `MCPServer`, so my first build kept crashing. I pinned `mcp[cli]<2` in the Dockerfile and it ran straight away. Pin versions in the Dockerfile.
- A `406` in the browser does not mean the server is broken. Test with an MCP client or curl.
- Publishing a port on `127.0.0.1` or `0.0.0.0` changes who can reach it. The tunnel only needs localhost.
- Claude's connector calls the server from the cloud, not from my PC. That is why the tunnel is needed.

## Next steps

- Add more read-only tools for the other API endpoints
- Move to a named tunnel with authentication
- Try the 2.x version of the SDK
