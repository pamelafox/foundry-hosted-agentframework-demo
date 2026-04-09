# Seattle Hotel Agent

A sample AI agent built with [Microsoft Agent Framework](https://learn.microsoft.com/agent-framework/) that helps users find hotels in Seattle. This project is designed as an `azd` starter template for deploying hosted AI agents to [Microsoft Foundry](https://learn.microsoft.com/azure/foundry/).

> **Blog post:** [Azure Developer CLI (azd): Debug hosted AI agents from your terminal](https://devblogs.microsoft.com/azure-sdk/azd-ai-agent-logs-status/)

## What it does

The agent uses a simulated hotel database and a tool-calling pattern to:

- Accept natural-language requests about Seattle hotels
- Ask clarifying questions about dates and budget
- Call the `get_available_hotels` tool to find matching options
- Present results in a conversational format

## Prerequisites

- [Python 3.12+](https://www.python.org/downloads/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- [Azure Developer CLI (azd) 1.23.7+](https://learn.microsoft.com/azure/developer/azure-developer-cli/install-azd)
- An [Azure subscription](https://azure.microsoft.com/free/)
- A [Microsoft Foundry](https://ai.azure.com/) project with a deployed model (e.g., `gpt-5.2`)

## Quick start

### Deploy to Azure

```bash
azd init -t puicchan/seattle-hotel-agent
azd ai agent init
azd up
```

During `azd ai agent init`, you'll be prompted to choose a model. You can:

- **Deploy a new model** — select `gpt-5.2` (or another supported model)
- **Connect to an existing model** — make sure the deployment name matches `AZURE_AI_MODEL_DEPLOYMENT_NAME` in your `.env`
- **Skip model setup** — configure it manually later

> **Note:** If you use a model deployment name other than `gpt-5.2`, update `AZURE_AI_MODEL_DEPLOYMENT_NAME` in your `.env` to match.

### Run locally

1. Copy `.env.sample` to `.env`, then set both required variables:
    - `AZURE_AI_PROJECT_ENDPOINT`
    - `AZURE_AI_MODEL_DEPLOYMENT_NAME`

    ```bash
    cp .env.sample .env
    ```

2. Start the local hosted-agent server:

    ```bash
    azd ai agent run
    ```

    This starts the local server on `http://localhost:8088`.

3. Invoke the agent from another terminal:

    ```bash
    azd ai agent invoke --local "hi agent"
    ```

4. Or test it with any HTTP client:

    ```http
    POST http://localhost:8088/responses
    Content-Type: application/json

    {"input": "Find me a hotel near Pike Place Market for this weekend"}
    ```

## Debug with `azd`

After deploying, use these commands to inspect and troubleshoot your hosted agent:

```bash
# View container status, health, and error details
azd ai agent show

# Fetch recent logs
azd ai agent monitor

# Stream logs in real time
azd ai agent monitor -f

# View system-level logs
azd ai agent monitor --type system
```

See the [blog post](https://devblogs.microsoft.com/azure-sdk/azd-ai-agent-logs-status/) for more details.

## Foundry IQ (Azure AI Search) integration

Relevant integration pieces from your `python-foundryagent-demos` repo are now included:

- Post-provision hooks: `infra/hooks/postprovision.sh` and `infra/hooks/postprovision.ps1`
- Indexing script: `infra/create-search-indexes.py`
- Sample index data and schema: `data/index-data/`
- Runtime AI Search context provider wiring in hosted app: `main.py` (optional, env-driven)

What happens on `azd up`:

1. The post-provision hook runs `infra/create-search-indexes.py` with keyless Microsoft Entra auth (`DefaultAzureCredential`).
2. It creates/updates `hrdocs` and `healthdocs` indexes.
3. It uploads the JSONL documents from `data/index-data/`.

If you need to rerun indexing manually:

```bash
SEARCH_ENDPOINT="https://${AZURE_AI_SEARCH_SERVICE_NAME}.search.windows.net"

uv run python infra/create-search-indexes.py \
    --endpoint "$SEARCH_ENDPOINT" \
    --openai-endpoint "$AZURE_OPENAI_ENDPOINT" \
    --data-dir data/index-data
```

If needed, you can still use API-key auth by adding `--admin-key <search-admin-key>`.

To enable AI Search knowledge retrieval in this hosted app (`main.py`), set:

- `AZURE_AI_SEARCH_SERVICE_ENDPOINT`
- `AZURE_AI_SEARCH_KNOWLEDGE_BASE_NAME`

When both are present, the app adds an `AzureAISearchContextProvider`
(`mode="agentic"`) and provides retrieved KB context directly to the model.

Environment variable naming notes for the `azd ai` extension are documented at:
https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/extensions/azure-ai-foundry-extension#manage-environment-variables