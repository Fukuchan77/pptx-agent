"""Tests for watsonx project_id handling in llm_config.

This test verifies that watsonx configuration properly passes project_id
to the LiteLLM model, which is required by watsonx.ai API.
"""

from unittest.mock import MagicMock, patch

from pptx_agent.agents.llm_config import create_model
from pptx_agent.config import Config


class TestWatsonxProjectId:
    """Test watsonx project_id is properly passed to LiteLLM."""

    def test_watsonx_uses_litellm_with_project_id(self):
        """Test that watsonx provider uses LiteLLMModel and sets project_id env var.

        Verifies that:
        1. watsonx uses LiteLLMModel (not AsyncOpenAI + OpenAIChatModel)
        2. WATSONX_PROJECT_ID environment variable is set for LiteLLM to use
        3. Correct model name, API key, and base URL are passed
        """
        # Arrange
        config = Config(
            llm_provider="watsonx",
            llm_model="meta-llama/llama-3-1-70b-instruct",
            watsonx_url="https://us-south.ml.cloud.ibm.com",
            watsonx_apikey="test-watsonx-key-1234567890",
            watsonx_project_id="test-project-id-12345",
            environment="production",
            allow_test_keys=True,  # Phase 3: Allow test keys in test mode
        )

        # Act & Assert
        # Mock LiteLLMModel and os.environ to verify correct behavior
        with (
            patch("pptx_agent.agents.llm_config.LiteLLMModel") as mock_litellm_model,
            patch("pptx_agent.agents.llm_config.os.environ", {}) as mock_env,
        ):
            mock_litellm_model.return_value = MagicMock()

            create_model(config)

            # Verify LiteLLMModel was called (not AsyncOpenAI)
            assert mock_litellm_model.called, "LiteLLMModel should be used for watsonx provider"

            # Verify WATSONX_PROJECT_ID environment variable was set
            assert "WATSONX_PROJECT_ID" in mock_env, (
                "WATSONX_PROJECT_ID should be set as environment variable"
            )
            assert mock_env["WATSONX_PROJECT_ID"] == "test-project-id-12345", (
                f"Expected project_id 'test-project-id-12345', got {mock_env.get('WATSONX_PROJECT_ID')}"
            )

            # Verify correct model name format
            call_args = mock_litellm_model.call_args.args
            assert len(call_args) > 0, "Model name should be passed as first argument"
            assert call_args[0] == "watsonx/meta-llama/llama-3-1-70b-instruct", (
                f"Expected 'watsonx/meta-llama/llama-3-1-70b-instruct', got {call_args[0]}"
            )

            # Verify API key and base URL are passed (but NOT project_id)
            call_kwargs = mock_litellm_model.call_args.kwargs
            assert "api_key" in call_kwargs, "api_key should be passed to LiteLLMModel"
            assert call_kwargs["api_key"] == "test-watsonx-key-1234567890"
            assert "api_base" in call_kwargs, "api_base should be passed to LiteLLMModel"
            assert "project_id" not in call_kwargs, (
                "project_id should NOT be passed to constructor (it's set as env var instead)"
            )
