"""Utility functions for LLM agents."""

import logging
from typing import Any, TypeVar

from pydantic import BaseModel
from pydantic_ai import Agent, AgentRunResult

from pptx_agent.agents.llm_config import create_fallback_model, create_model
from pptx_agent.config import Config

logger = logging.getLogger(__name__)

# TypeVar for generic agent output types
OutputT = TypeVar("OutputT", bound=BaseModel)


async def run_agent_with_fallback[OutputT: BaseModel](
    agent: Agent[None, OutputT], prompt: Any, config: Config
) -> AgentRunResult[OutputT]:
    """Run agent with automatic fallback to secondary provider.

    Args:
        agent: Pydantic AI agent with specified output type
        prompt: Input prompt for the agent
        config: Application configuration

    Returns:
        AgentRunResult with the agent's output

    Raises:
        RuntimeError: If both primary and fallback providers fail
    """
    try:
        model = create_model(config)
        return await agent.run(prompt, model=model)
    except Exception as e:
        # If primary fails, log and try fallback
        logger.warning("Primary LLM provider failed: %s, trying fallback", e)
        try:
            fallback_model = create_fallback_model(config)
            if fallback_model:
                result = await agent.run(prompt, model=fallback_model)
                logger.info("Fallback LLM provider succeeded")
                return result
            # Raise original exception if no fallback model generated
            raise
        except Exception as fallback_error:
            # If fallback also fails, log both and raise RuntimeError
            error_msg = f"All LLM providers failed. Primary: {e}, Fallback: {fallback_error}"
            logger.exception("Fallback LLM provider also failed")
            raise RuntimeError(error_msg) from fallback_error
