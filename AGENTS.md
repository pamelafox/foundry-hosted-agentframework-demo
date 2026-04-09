# Instructions for Coding Agents

This repository follows Azure Developer CLI (`azd ai`) environment variable naming conventions.

Always use these names in code, scripts, and docs:

- `AZURE_AI_PROJECT_ENDPOINT`
- `AZURE_AI_MODEL_DEPLOYMENT_NAME`
- `AZURE_AI_SEARCH_SERVICE_ENDPOINT`
- `AZURE_AI_SEARCH_CONNECTION_NAME`

Do not introduce custom aliases unless there is a temporary backward-compatibility need.

Reference:
- https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/extensions/azure-ai-foundry-extension#manage-environment-variables

## Filing bugs

This is where to search and file bugs for the technologies used in this repository:

* Agent framework: github.com/microsoft/agent-framework
* azd: github.com/Azure/azure-dev
* Agentserver wrapper SDK (part of Azure Python SDK): github.com/azure/azure-sdk-for-python

## Relevant documentation:

MAF Observability
https://learn.microsoft.com/en-us/agent-framework/agents/observability?pivots=programming-language-python#spans-and-metrics

Set up tracing in Foundry
https://learn.microsoft.com/en-us/azure/foundry/observability/how-to/trace-agent-setup

