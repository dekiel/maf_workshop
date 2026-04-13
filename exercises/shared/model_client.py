
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

def create_chat_client(model_name: str) -> BaseChatClient:
    """Create a chat client for Azure OpenAI or GitHub Models."""

    if (not model_name) or model_name.strip() == "":
        logger.error("Model name is missing. Set COMPLETION_DEPLOYMENT_NAME in your .env file.")
        raise Exception(
            "Model name is not set. Please set COMPLETION_DEPLOYMENT_NAME in your .env file."
        )

    github_token = os.environ.get("GITHUB_TOKEN", "").strip() or os.environ.get("GITHUB_PAT", "").strip()
    azure_api_key = os.environ.get("AZURE_OPENAI_API_KEY", "").strip()
    azure_endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT", "").strip()

    # --- Azure OpenAI ---
    if azure_endpoint:
        logger.info("AZURE_OPENAI_ENDPOINT found: %s", azure_endpoint)

        if azure_api_key:
            logger.info("Using Azure OpenAI API key authentication.")
            return OpenAIChatCompletionClient(
                model=model_name,
                api_key=azure_api_key,
                azure_endpoint=azure_endpoint,
            )

        else:
            logger.info("Using Azure OpenAI AAD authentication.")
            token_provider = get_bearer_token_provider(
                DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default"
            )
            return OpenAIChatCompletionClient(
                model=model_name,
                credential=token_provider,
                azure_endpoint=azure_endpoint,
            )

    # --- GitHub Models ---
    if github_token:
        logger.info("Using GitHub Models endpoint with token authentication.")
        return OpenAIChatCompletionClient(
            model=model_name,
            api_key=github_token,
            base_url="https://models.github.ai/inference",
        )
    