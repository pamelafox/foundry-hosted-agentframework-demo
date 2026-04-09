"""
Internal HR Helper - A simple agent with a tool to answer health insurance questions.
Uses Microsoft Agent Framework with Azure AI Foundry.
Ready for deployment to Foundry Hosted Agent service.

Run using:
azd ai agent run
"""

import asyncio
import logging
import os
from datetime import date

import httpx
from agent_framework import Agent, MCPStreamableHTTPTool
from agent_framework.azure import AzureAIAgentClient, AzureAISearchContextProvider
from agent_framework.observability import enable_instrumentation
from azure.ai.agentserver.agentframework import FoundryToolsContextProvider, from_agent_framework
from azure.ai.agentserver.agentframework.persistence import InMemoryAgentSessionRepository
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=True)


logger = logging.getLogger("hr-agent")


# Configure these for your Foundry project via environment variables (see .env.sample)
PROJECT_ENDPOINT = os.environ["AZURE_AI_PROJECT_ENDPOINT"]
MODEL_DEPLOYMENT_NAME = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]
SEARCH_SERVICE_ENDPOINT = os.environ["AZURE_AI_SEARCH_SERVICE_ENDPOINT"]
KNOWLEDGE_BASE_NAME = os.environ["AZURE_AI_SEARCH_KNOWLEDGE_BASE_NAME"]
# "context_provider" = AzureAISearchContextProvider injects KB results into context
# "kb_mcp_endpoint" = MCPStreamableHTTPTool lets the model call the KB MCP endpoint as a tool
FOUNDRY_IQ_CONTEXT_MODE = os.environ.get("FOUNDRY_IQ_CONTEXT_MODE", "kb_mcp_endpoint")


def get_current_date() -> str:
    """
    Return the current date in ISO format.
    """
    logger.info("Fetching current date")
    return date.today().isoformat()

def get_enrollment_deadline_info() -> str:
    """
    Return enrollment timeline details for health insurance plans.
    """
    logger.info("Fetching enrollment deadline information")
    return {
        "benefits_enrollment_opens": "2026-11-11",
        "benefits_enrollment_closes": "2026-11-30"
    }

async def start_server(credential, tools, context_providers):
    """Create the agent and start the server."""
    agent = Agent(
        client=AzureAIAgentClient(
            project_endpoint=PROJECT_ENDPOINT,
            model_deployment_name=MODEL_DEPLOYMENT_NAME,
            credential=credential,
        ),
        name="InternalHRHelper",
        instructions="""You are an internal HR helper focused on employee benefits and company information.
        Use the knowledge available to answer questions and ground all answers in provided context.
        You can use web search to look up current information when the knowledge base does not have the answer.
        You can use these tools if the user needs information on benefits deadlines: get_enrollment_deadline_info, get_current_date.
        If you cannot answer a question, explain that you do not have available information to fully answer the question.""",
        tools=tools,
        context_providers=context_providers,
    )
    logger.info("Internal HR Helper Server running on http://localhost:8088")
    logger.info('Try: azd ai agent invoke --local "What benefits are there, and when do I need to enroll by?"')
    server = from_agent_framework(agent, session_repository=InMemoryAgentSessionRepository())
    await server.run_async()

async def main():
    """Main function to run the agent as a web server."""
    logger.info("Starting Internal HR Helper setup (FOUNDRY_IQ_CONTEXT_MODE=%s)", FOUNDRY_IQ_CONTEXT_MODE)
    function_tools = [get_enrollment_deadline_info, get_current_date]
    foundry_tools_context_provider = FoundryToolsContextProvider(
        tools=[{"type": "web_search_preview"}, {"type": "code_interpreter"}],
    )

    async with DefaultAzureCredential() as credential:

        if FOUNDRY_IQ_CONTEXT_MODE == "kb_mcp_endpoint":
            # The model decides when to call the KB MCP endpoint as a tool
            mcp_url = (
                f"{SEARCH_SERVICE_ENDPOINT}/knowledgebases/{KNOWLEDGE_BASE_NAME}"
                f"/mcp?api-version=2025-11-01-Preview"
            )
            logger.info("Using KB MCP tool at %s", mcp_url)

            async def _add_auth(request: httpx.Request) -> None:
                token = await credential.get_token("https://search.azure.com/.default")
                request.headers["Authorization"] = f"Bearer {token.token}"

            async with httpx.AsyncClient(
                event_hooks={"request": [_add_auth]},
                timeout=httpx.Timeout(30.0, read=300.0),
            ) as http_client:
                async with MCPStreamableHTTPTool(
                    name="zava-company-knowledge-base",
                    description="Zava company documents - benefits, insurance, policies, job roles.",
                    url=mcp_url,
                    http_client=http_client,
                    allowed_tools=["knowledge_base_retrieve"],
                    load_prompts=False,
                ) as kb_mcp_tool:
                    await start_server(
                        credential,
                        [kb_mcp_tool] + function_tools,
                        [foundry_tools_context_provider],
                    )
        else:
            # KB results are injected into context automatically before each turn
            logger.info("Using AI Search context provider for knowledge base '%s'", KNOWLEDGE_BASE_NAME)
            search_context_provider = AzureAISearchContextProvider(
                endpoint=SEARCH_SERVICE_ENDPOINT,
                credential=credential,
                knowledge_base_name=KNOWLEDGE_BASE_NAME,
                mode="agentic",
            )
            await start_server(
                credential,
                function_tools,
                [search_context_provider, foundry_tools_context_provider],
            )

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    logger.setLevel(logging.INFO)
    # Silence noisy HTTP/telemetry loggers
    for name in ("azure.core.pipeline", "azure.monitor.opentelemetry", "urllib3", "azure.identity"):
        logging.getLogger(name).setLevel(logging.WARNING)

    enable_instrumentation(enable_sensitive_data=True)

    asyncio.run(main())