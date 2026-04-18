"""Tests for watsonx project_id handling in llm_config.

This test verifies that watsonx configuration properly passes project_id
to the LiteLLM model, which is required by watsonx.ai API.
"""

import os
from typing import Any
from unittest.mock import MagicMock, patch

from pptx_agent.agents.llm_config import create_model
from pptx_agent.config import Config


class TestWatsonxProjectId:
    """Test watsonx project_id is properly passed to LiteLLM."""

    def test_watsonx_uses_litellm_with_project_id(self):
        """Test that watsonx provider uses LiteLLMModel with scoped project_id.

        Verifies that:
        1. watsonx uses LiteLLMModel (not AsyncOpenAI + OpenAIChatModel)
        2. project_id is set via environment variable during model creation
        3. Correct model name, API key, and base URL are passed
        4. Environment variable is properly restored after model creation
        """
        import os

        # Arrange
        config = Config.model_validate(
            {
                "llm_provider": "watsonx",
                "llm_model": "meta-llama/llama-3-1-70b-instruct",
                "watsonx_url": "https://us-south.ml.cloud.ibm.com",
                "watsonx_apikey": "test-watsonx-key-1234567890",
                "watsonx_project_id": "test-project-id-12345",
                "environment": "production",
            },
            context={"allow_test_keys": True},
        )

        # Save original environment state
        original_project_id = os.environ.get("WATSONX_PROJECT_ID")
        env_during_creation = None

        # Act & Assert
        with patch("pptx_agent.agents.llm_config.LiteLLMModel") as mock_litellm_model:

            def capture_env(*args: Any, **kwargs: Any) -> MagicMock:
                nonlocal env_during_creation
                env_during_creation = os.environ.get("WATSONX_PROJECT_ID")
                return MagicMock()

            mock_litellm_model.side_effect = capture_env

            create_model(config)

            # Verify LiteLLMModel was called (not AsyncOpenAI)
            assert mock_litellm_model.called, "LiteLLMModel should be used for watsonx provider"

            # Verify correct model name format
            call_args = mock_litellm_model.call_args.args
            assert len(call_args) > 0, "Model name should be passed as first argument"
            assert call_args[0] == "watsonx/meta-llama/llama-3-1-70b-instruct", (
                f"Expected 'watsonx/meta-llama/llama-3-1-70b-instruct', got {call_args[0]}"
            )

            # Verify API key and base URL are passed
            call_kwargs = mock_litellm_model.call_args.kwargs
            assert "api_key" in call_kwargs, "api_key should be passed to LiteLLMModel"
            assert call_kwargs["api_key"] == "test-watsonx-key-1234567890"
            assert "api_base" in call_kwargs, "api_base should be passed to LiteLLMModel"

            # Verify project_id was set in environment during model creation
            assert env_during_creation == "test-project-id-12345", (
                f"Expected WATSONX_PROJECT_ID to be 'test-project-id-12345' during creation, "
                f"got {env_during_creation}"
            )

            # Verify environment variable is restored after creation
            assert os.environ.get("WATSONX_PROJECT_ID") == original_project_id, (
                "WATSONX_PROJECT_ID should be restored to original state after model creation"
            )

    def test_watsonx_environment_restoration(self):
        """Test that watsonx provider properly restores environment after model creation.

        This test verifies the scoped context manager behavior:
        1. Environment variable is set during model creation
        2. Environment variable is restored to original state after creation
        3. No permanent environment mutation occurs
        """

        # Arrange
        config = Config.model_validate(
            {
                "llm_provider": "watsonx",
                "llm_model": "meta-llama/llama-3-1-70b-instruct",
                "watsonx_url": "https://us-south.ml.cloud.ibm.com",
                "watsonx_apikey": "test-watsonx-key-1234567890",
                "watsonx_project_id": "test-project-id-12345",
                "environment": "production",
            },
            context={"allow_test_keys": True},
        )

        # Save original environment state
        original_project_id = os.environ.get("WATSONX_PROJECT_ID")

        # Act
        with patch("pptx_agent.agents.llm_config.LiteLLMModel") as mock_litellm_model:
            mock_litellm_model.return_value = MagicMock()

            create_model(config)

            # Assert - environment should be restored to original state
            assert os.environ.get("WATSONX_PROJECT_ID") == original_project_id, (
                f"WATSONX_PROJECT_ID should be restored to {original_project_id}, "
                f"got {os.environ.get('WATSONX_PROJECT_ID')}"
            )

    def test_watsonx_concurrent_different_project_ids(self):
        """Test that concurrent create_model calls with different project_ids are thread-safe.

        This test verifies that when multiple threads create models with different
        project_ids simultaneously, each gets the correct project_id without interference.
        This proves that the refactoring eliminated the global state race condition.
        """
        import concurrent.futures
        import threading

        # Track which project_id each thread received
        results = {}
        results_lock = threading.Lock()

        def create_model_with_project_id(project_id: str) -> None:
            """Create a model and verify it gets the correct project_id."""
            config = Config.model_validate(
                {
                    "llm_provider": "watsonx",
                    "llm_model": "meta-llama/llama-3-1-70b-instruct",
                    "watsonx_url": "https://us-south.ml.cloud.ibm.com",
                    "watsonx_apikey": "test-watsonx-key-1234567890",
                    "watsonx_project_id": project_id,
                    "environment": "production",
                },
                context={"allow_test_keys": True},
            )

            # Track environment state during model creation
            env_during_creation = None

            def capture_env(*args: Any, **kwargs: Any) -> MagicMock:
                nonlocal env_during_creation
                env_during_creation = os.environ.get("WATSONX_PROJECT_ID")
                return MagicMock()

            with patch("pptx_agent.agents.llm_config.LiteLLMModel") as mock_litellm:
                mock_litellm.side_effect = capture_env
                create_model(config)

                # Verify the project_id was correctly set during creation
                actual_project_id = env_during_creation

                with results_lock:
                    results[project_id] = actual_project_id

        # Create multiple threads with different project_ids
        project_ids = [
            "project-id-thread-1",
            "project-id-thread-2",
            "project-id-thread-3",
            "project-id-thread-4",
            "project-id-thread-5",
        ]

        # Execute concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(create_model_with_project_id, pid) for pid in project_ids]
            # Wait for all to complete
            concurrent.futures.wait(futures)

        # Verify each thread got the correct project_id
        for expected_project_id in project_ids:
            assert expected_project_id in results, (
                f"Thread for {expected_project_id} did not complete"
            )
            assert results[expected_project_id] == expected_project_id, (
                f"Thread-safety violation: expected {expected_project_id}, "
                f"got {results[expected_project_id]}"
            )
