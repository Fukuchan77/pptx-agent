"""Tests for agent utility functions."""

from typing import TypeVar
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel
from pydantic_ai import Agent, AgentRunResult

from pptx_agent.agents.utils import run_agent_with_fallback
from pptx_agent.config import Config


class TestOutputType(BaseModel):
    """Test output type for agent."""

    result: str


T = TypeVar("T", bound=BaseModel)


@pytest.mark.asyncio
async def test_run_agent_with_fallback_type_signature():
    """Test that run_agent_with_fallback has proper generic type signature.

    RED PHASE: This test will fail until we add proper TypeVar support.
    The function should return AgentRunResult[T] where T is the agent's output type.
    """
    # Create a test agent
    test_agent: Agent[None, TestOutputType] = Agent(output_type=TestOutputType)

    # Create mock config
    mock_config = MagicMock(spec=Config)
    mock_config.llm_provider = "openai"
    mock_config.llm_model = "test-model"
    mock_config.enable_fallback = False

    # Mock the agent.run to return proper result
    expected_output = TestOutputType(result="test result")
    mock_result = AgentRunResult(output=expected_output)

    with (
        patch("pptx_agent.agents.utils.create_model") as mock_create_model,
        patch.object(test_agent, "run", new_callable=AsyncMock) as mock_run,
    ):
        mock_create_model.return_value = "mock-model"
        mock_run.return_value = mock_result

        # Act
        result = await run_agent_with_fallback(test_agent, "test prompt", mock_config)

        # Assert - result should be AgentRunResult with proper type
        assert isinstance(result, AgentRunResult)
        assert result.output == expected_output
        assert result.output.result == "test result"


@pytest.mark.asyncio
async def test_run_agent_with_fallback_primary_success():
    """Test successful execution with primary provider."""
    test_agent: Agent[None, TestOutputType] = Agent(output_type=TestOutputType)
    mock_config = MagicMock(spec=Config)

    expected_output = TestOutputType(result="primary success")
    mock_result = AgentRunResult(output=expected_output)

    with (
        patch("pptx_agent.agents.utils.create_model") as mock_create_model,
        patch.object(test_agent, "run", new_callable=AsyncMock) as mock_run,
    ):
        mock_create_model.return_value = "primary-model"
        mock_run.return_value = mock_result

        # Act
        result = await run_agent_with_fallback(test_agent, "test", mock_config)

        # Assert
        assert result.output.result == "primary success"
        mock_run.assert_called_once()


@pytest.mark.asyncio
async def test_run_agent_with_fallback_uses_fallback_on_failure():
    """Test that fallback is used when primary fails."""
    test_agent: Agent[None, TestOutputType] = Agent(output_type=TestOutputType)
    mock_config = MagicMock(spec=Config)

    fallback_output = TestOutputType(result="fallback success")
    fallback_result = AgentRunResult(output=fallback_output)

    with (
        patch("pptx_agent.agents.utils.create_model") as mock_create_model,
        patch("pptx_agent.agents.utils.create_fallback_model") as mock_create_fallback,
        patch.object(test_agent, "run", new_callable=AsyncMock) as mock_run,
    ):
        mock_create_model.return_value = "primary-model"
        mock_create_fallback.return_value = "fallback-model"

        # First call fails, second succeeds
        mock_run.side_effect = [Exception("Primary failed"), fallback_result]

        # Act
        result = await run_agent_with_fallback(test_agent, "test", mock_config)

        # Assert
        assert result.output.result == "fallback success"
        assert mock_run.call_count == 2


@pytest.mark.asyncio
async def test_run_agent_with_fallback_raises_when_both_fail():
    """Test that RuntimeError is raised when both providers fail."""
    test_agent: Agent[None, TestOutputType] = Agent(output_type=TestOutputType)
    mock_config = MagicMock(spec=Config)

    with (
        patch("pptx_agent.agents.utils.create_model") as mock_create_model,
        patch("pptx_agent.agents.utils.create_fallback_model") as mock_create_fallback,
        patch.object(test_agent, "run", new_callable=AsyncMock) as mock_run,
    ):
        mock_create_model.return_value = "primary-model"
        mock_create_fallback.return_value = "fallback-model"

        # Both calls fail
        mock_run.side_effect = [Exception("Primary failed"), Exception("Fallback failed")]

        # Act & Assert
        with pytest.raises(RuntimeError, match="All LLM providers failed"):
            await run_agent_with_fallback(test_agent, "test", mock_config)
