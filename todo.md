# TODO

## Upgrade MCPStreamableHTTPTool to use `header_provider`

**When:** `azure-ai-agentserver-agentframework` releases a version compatible with `agent-framework-core>=1.0.0`

**PR:** <https://github.com/microsoft/agent-framework/pull/4849>

**What to change in `main.py`:**

Replace the `kb_mcp_endpoint` branch's httpx auth plumbing:

```python
# BEFORE (current): manual httpx client with event_hooks for auth
async def _add_auth(request: httpx.Request) -> None:
    token = await credential.get_token("https://search.azure.com/.default")
    request.headers["Authorization"] = f"Bearer {token.token}"

async with httpx.AsyncClient(event_hooks={"request": [_add_auth]}) as http_client:
    async with MCPStreamableHTTPTool(
        name="knowledge-base",
        url=mcp_url,
        http_client=http_client,
        allowed_tools=["knowledge_base_retrieve"],
    ) as kb_mcp_tool:
        ...
```

With the simpler `header_provider` parameter:

```python
# AFTER: use header_provider (requires agent-framework-core>=1.0.0)
async def _get_auth_headers() -> dict[str, str]:
    token = await credential.get_token("https://search.azure.com/.default")
    return {"Authorization": f"Bearer {token.token}"}

async with MCPStreamableHTTPTool(
    name="knowledge-base",
    url=mcp_url,
    header_provider=_get_auth_headers,
    allowed_tools=["knowledge_base_retrieve"],
) as kb_mcp_tool:
    ...
```

This also removes the `import httpx` dependency.

## Verify Search-to-OpenAI role assignment after fresh deploy

**When:** Next `azd up` / `azd provision`

**What to verify:**

The `searchToAIServicesRoleAssignment` in `infra/core/search/azure_ai_search.bicep` was updated to `scope: aiAccount`. After a fresh deploy:

1. Run `az role assignment list --assignee <search-service-principal-id> --query "[?contains(roleDefinitionName, 'OpenAI')]"` to confirm the role exists
2. Test the KB MCP endpoint tool — invoke the agent and check logs for 401 errors on OpenAI calls
3. If still failing, may need to scope the role assignment differently (e.g., to the specific AI Services resource ID)


## Open questions

Why don't we need to use uvicorn in the Dockerfile?