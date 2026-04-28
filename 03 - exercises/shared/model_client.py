
import os
import logging

from agent_framework import BaseChatClient
from agent_framework.openai import OpenAIChatCompletionClient

from azure.identity import DefaultAzureCredential, get_bearer_token_provider
from dotenv import load_dotenv

# Configure logging for this sample module
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

load_dotenv()

def create_chat_client() -> BaseChatClient:
    """Create a chat client for Azure OpenAI or GitHub Models."""

    github_token = os.environ.get("GITHUB_PAT", "").strip()
    model_name_git = os.environ.get("GITHUB_MODEL", "").strip()
    azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()
    model_name_azure = os.environ.get("FOUNDRY_MODEL", "").strip()

    if not model_name_azure and not model_name_git:
        logger.error("Model name is missing. Set COMPLETION_DEPLOYMENT_NAME in your .env file.")
        raise Exception(
            "Model name is not set. Please set COMPLETION_DEPLOYMENT_NAME in your .env file."
        )

    # --- Azure AI Foundry ---
    foundry_endpoint = os.environ.get("FOUNDRY_PROJECT_ENDPOINT", "").strip()
    if foundry_endpoint:
        from agent_framework.foundry import FoundryChatClient
        from azure.identity import AzureCliCredential
        logger.info("FOUNDRY_PROJECT_ENDPOINT found: %s", foundry_endpoint)
        return FoundryChatClient(
            project_endpoint=foundry_endpoint,
            model=model_name_azure,
            credential=AzureCliCredential(),
        )

    # --- Azure OpenAI ---
    if azure_endpoint:
        logger.info("AZURE_OPENAI_ENDPOINT found: %s", azure_endpoint)

        if azure_api_key:
            logger.info("Using Azure OpenAI API key authentication.")
            return OpenAIChatCompletionClient(
                model=model_name_azure,
                api_key=azure_api_key,
                azure_endpoint=azure_endpoint,
            )

        else:
            logger.info("Using Azure OpenAI AAD authentication.")
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
            )
            return OpenAIChatCompletionClient(
                model=model_name_azure,
                credential=token_provider,
                azure_endpoint=azure_endpoint,
            )

    # --- GitHub Models ---
    if github_token:
        logger.info("Using GitHub Models endpoint with token authentication.")
        return OpenAIChatCompletionClient(
            model=model_name_git,
            api_key=github_token,
            base_url="https://models.github.ai/inference",
        )