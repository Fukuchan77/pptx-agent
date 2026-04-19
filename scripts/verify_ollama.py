#!/usr/bin/env python3
"""Verification script to test Ollama connectivity with granite4:latest.

This script:
1. Loads configuration from .env.ollama.test
2. Creates an LLM model instance
3. Makes a simple test request
4. Reports the results
"""

import asyncio
import logging
import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic_ai import Agent

# Add src to path to import pptx_agent modules
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pptx_agent.agents.llm_config import create_model
from pptx_agent.config import Config

try:
    import httpx
except ImportError:
    httpx = None  # type: ignore[assignment]

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Constants for configuration
MAX_RESPONSE_DISPLAY_LENGTH = 200
HTTP_OK = 200


async def test_ollama_connection() -> bool:
    """Test Ollama connection with a simple prompt.

    Returns:
        True if connection test succeeded, False otherwise.
    """
    try:
        # Load configuration from .env.ollama.test
        logger.info("Loading configuration from .env.ollama.test...")
        load_dotenv(".env.ollama.test", override=True)

        # Load config with ollama settings
        config = Config.model_validate({}, context={"allow_test_keys": True})

        logger.info("Provider: %s", config.llm_provider)
        logger.info("Model: %s", config.llm_model)
        logger.info("API Base: %s", config.llm_api_base)

        # Create model
        logger.info("Creating LLM model instance...")
        model = create_model(config)

        # Test with a simple prompt
        logger.info("Testing connection with a simple prompt...")
        test_prompt = "こんにちは。あなたの名前は何ですか？"  # noqa: RUF001

        # Use pydantic-ai's Agent for testing
        agent = Agent(model)
        result = await agent.run(test_prompt)

        logger.info("✅ SUCCESS! Ollama connection verified.")
        # AgentRunResult stores the output in the result itself, not in .data
        response_text = str(result)
        if len(response_text) > MAX_RESPONSE_DISPLAY_LENGTH:
            logger.info("Response: %s...", response_text[:MAX_RESPONSE_DISPLAY_LENGTH])
        else:
            logger.info("Response: %s", response_text)

    except Exception:
        logger.exception("❌ FAILED: Connection test failed")
        return False
    else:
        return True


async def check_ollama_availability() -> bool:
    """Check if Ollama server is running.

    Returns:
        True if Ollama server is available with granite4 model, False otherwise.
    """
    if httpx is None:
        logger.error("httpx library not available")
        return False

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:11434/api/tags")
            if response.status_code == HTTP_OK:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                logger.info("Ollama server is running. Available models: %s", models)

                if "granite4:latest" in models or any("granite4" in m for m in models):
                    logger.info("✅ granite4 model is available")
                    return True
                logger.warning("⚠️  granite4:latest not found. Available models:")
                for model in models:
                    logger.warning("  - %s", model)
                logger.warning("Please run: ollama pull granite4:latest")
                return False
            logger.error("Ollama server returned status code: %d", response.status_code)
            return False
    except Exception:
        logger.exception("❌ Ollama server not reachable")
        logger.exception("Please ensure Ollama is running: ollama serve")
        return False


async def main() -> bool:
    """Main entry point.

    Returns:
        True if verification succeeded, False otherwise.
    """
    separator = "=" * 60
    logger.info(separator)
    logger.info("Ollama Connectivity Verification")
    logger.info("Testing granite4:latest model")
    logger.info(separator)
    logger.info("")

    # Step 1: Check if Ollama is available
    logger.info("Step 1: Checking Ollama server availability...")
    ollama_available = await check_ollama_availability()
    logger.info("")

    if not ollama_available:
        logger.error("Cannot proceed with testing. Please ensure:")
        logger.error("1. Ollama is running: ollama serve")
        logger.error("2. granite4 model is pulled: ollama pull granite4:latest")
        return False

    # Step 2: Test connection
    logger.info("Step 2: Testing LLM connection...")
    success = await test_ollama_connection()
    logger.info("")

    logger.info(separator)
    if success:
        logger.info("✅ VERIFICATION SUCCESSFUL")
        logger.info("The existing code can successfully call Ollama's granite4:latest")
    else:
        logger.error("❌ VERIFICATION FAILED")
        logger.error("Please check the error messages above")
    logger.info(separator)

    return success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
