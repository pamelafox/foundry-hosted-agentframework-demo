"""
Workflow demo: Multi-agent workflow using Agent Framework's WorkflowBuilder.

Three agents in a chain:
    writer → legal_reviewer → formatter

The writer creates a slogan, the legal reviewer checks it, and the formatter
styles it for terminal output. Each agent only sees the output of the
previous agent (context_mode="last_agent").

Based on the hosted-agents-vnext sample:
    samples/python/hosted-agents/agent-framework/responses/05-workflows/

Prerequisites:
    Same as Stage 1 (Azure OpenAI / Foundry model deployment).

Run locally:
    python workflow.py

Deploy (replaces main.py as the entrypoint):
    Update Dockerfile CMD and agent.yaml, then azd deploy.
"""

import os

from agent_framework import Agent, AgentExecutor, WorkflowBuilder
from agent_framework.foundry import FoundryChatClient
from agent_framework.observability import enable_instrumentation
from agent_framework_foundry_hosting import ResponsesHostServer
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=True)

PROJECT_ENDPOINT = os.environ["FOUNDRY_PROJECT_ENDPOINT"]
MODEL_DEPLOYMENT_NAME = os.environ["AZURE_AI_MODEL_DEPLOYMENT_NAME"]


def main():
    credential = DefaultAzureCredential()

    client = FoundryChatClient(
        project_endpoint=PROJECT_ENDPOINT,
        model=MODEL_DEPLOYMENT_NAME,
        credential=credential,
    )

    writer_agent = Agent(
        client=client,
        name="writer",
        instructions="You are an excellent slogan writer. You create new slogans based on the given topic.",
    )

    legal_agent = Agent(
        client=client,
        name="legal_reviewer",
        instructions=(
            "You are an excellent legal reviewer. "
            "Make necessary corrections to the slogan so that it is legally compliant."
        ),
    )

    format_agent = Agent(
        client=client,
        name="formatter",
        instructions=(
            "You are an excellent content formatter. "
            "You take the slogan and format it in a cool retro style when printing to a terminal."
        ),
    )

    writer_executor = AgentExecutor(writer_agent, context_mode="last_agent")
    legal_executor = AgentExecutor(legal_agent, context_mode="last_agent")
    format_executor = AgentExecutor(format_agent, context_mode="last_agent")

    workflow_agent = (
        WorkflowBuilder(
            start_executor=writer_executor,
            output_executors=[format_executor],
        )
        .add_edge(writer_executor, legal_executor)
        .add_edge(legal_executor, format_executor)
        .build()
        .as_agent()
    )

    server = ResponsesHostServer(workflow_agent)
    server.run()


if __name__ == "__main__":
    enable_instrumentation(enable_sensitive_data=True)
    main()
