from unittest.mock import AsyncMock, patch

import pytest
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletionChunk
from openai.types.chat.chat_completion_chunk import Choice, ChoiceDelta

from app.llm_client import LLMClient


class TestLLMClient:

    def test_init(self, test_config):
        # Setup & Execute
        client = LLMClient(test_config)

        # Verify
        assert client.config == test_config

    def test_get_client(self, llm_client):
        # Setup & Execute
        openai_client = llm_client.get_client("openai")
        ollama_client = llm_client.get_client("ollama")

        # Verify
        assert isinstance(openai_client, AsyncOpenAI)
        assert isinstance(ollama_client, AsyncOpenAI)
        assert openai_client.base_url == "https://api.openai.com/v1/"
        assert ollama_client.base_url == "http://localhost:11434/v1/"

    def test_model_supports_images(self, llm_client):
        # Setup & Execute & Verify
        # Models with vision capabilities
        assert llm_client.model_supports_images("gpt-4-vision") is True
        assert llm_client.model_supports_images("claude-3-sonnet") is True
        assert llm_client.model_supports_images("gemini-pro") is True
        assert llm_client.model_supports_images("llava-13b") is True
        assert llm_client.model_supports_images("mistral-small-vision") is True

        # Models without vision capabilities
        assert llm_client.model_supports_images("gpt-3.5-turbo") is False
        assert llm_client.model_supports_images("mistral-medium") is False
        assert llm_client.model_supports_images("llama2-70b") is False

    def test_provider_supports_usernames(self, llm_client):
        # Setup & Execute & Verify
        # Providers supporting usernames
        assert llm_client.provider_supports_usernames("openai") is True
        assert llm_client.provider_supports_usernames("x-ai") is True

        # Providers not supporting usernames
        assert llm_client.provider_supports_usernames("mistral") is False
        assert llm_client.provider_supports_usernames("ollama") is False
        assert llm_client.provider_supports_usernames("groq") is False

    def test_prepare_system_message(self, llm_client):
        # Setup & Execute
        system_msg_openai = llm_client.prepare_system_message("gpt-4o", "openai")
        system_msg_mistral = llm_client.prepare_system_message(
            "mistral-medium", "mistral"
        )

        # Verify
        assert system_msg_openai["role"] == "system"
        assert "Test system prompt" in system_msg_openai["content"]
        assert "Today's date:" in system_msg_openai["content"]
        assert (
            "Discord IDs" in system_msg_openai["content"]
        )  # OpenAI supports usernames

        assert system_msg_mistral["role"] == "system"
        assert "Test system prompt" in system_msg_mistral["content"]
        assert "Today's date:" in system_msg_mistral["content"]
        assert (
            "Discord IDs" not in system_msg_mistral["content"]
        )  # Mistral doesn't support usernames

    def test_prepare_system_message_empty(self, test_config, llm_client):
        # Setup
        test_config.system_prompt = ""

        # Execute
        system_msg = llm_client.prepare_system_message("gpt-4o", "openai")

        # Verify
        assert system_msg == {}  # Should return empty dict when no system prompt is set

    @pytest.mark.asyncio
    async def test_generate_response(self, llm_client):
        # Setup
        messages = [{"role": "user", "content": "Hello, bot!"}]

        # Create mock chunks
        mock_chunks = []

        # First chunk
        delta1 = ChoiceDelta(
            content="Hello", role=None, function_call=None, tool_calls=None
        )
        choice1 = Choice(delta=delta1, finish_reason=None, index=0)
        chunk1 = ChatCompletionChunk(
            id="1",
            choices=[choice1],
            created=1,
            model="openai/gpt-4o",
            object="chat.completion.chunk",
        )
        mock_chunks.append(chunk1)

        # Second chunk
        delta2 = ChoiceDelta(
            content=", world!", role=None, function_call=None, tool_calls=None
        )
        choice2 = Choice(delta=delta2, finish_reason="stop", index=0)
        chunk2 = ChatCompletionChunk(
            id="2",
            choices=[choice2],
            created=2,
            model="openai/gpt-4o",
            object="chat.completion.chunk",
        )
        mock_chunks.append(chunk2)

        # Create a mock AsyncOpenAI client with proper nested structure
        mock_openai_client = AsyncMock()
        mock_openai_client.chat = AsyncMock()
        mock_openai_client.chat.completions = AsyncMock()

        # Configure the mock to return an async generator that yields the mock chunks
        async def mock_generator():
            for chunk in mock_chunks:
                yield chunk

        mock_openai_client.chat.completions.create = AsyncMock(
            return_value=mock_generator()
        )

        # Mock the get_client method to return our mock client
        with patch.object(llm_client, "get_client", return_value=mock_openai_client):
            # Execute
            results = []
            async for content, finish_reason in llm_client.generate_response(messages):
                results.append((content, finish_reason))

        # Verify
        assert len(results) == 2
        assert results[0] == ("Hello", None)
        assert results[1] == (", world!", "stop")

        # Verify the client was called with the correct parameters
        mock_openai_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o"
        assert len(call_kwargs["messages"]) > 0
        assert call_kwargs["stream"] is True
        assert call_kwargs["extra_body"] == {"max_tokens": 2048, "temperature": 0.7}

    @pytest.mark.asyncio
    async def test_generate_response_error(self, llm_client):
        # Setup
        messages = [{"role": "user", "content": "Hello, bot!"}]

        # Create a mock AsyncOpenAI client that raises an exception
        mock_openai_client = AsyncMock()
        mock_openai_client.chat.completions.create = AsyncMock(
            side_effect=Exception("API error")
        )

        # Mock the get_client method to return our mock client
        with patch.object(llm_client, "get_client", return_value=mock_openai_client):
            # Execute
            results = []
            async for content, finish_reason in llm_client.generate_response(messages):
                results.append((content, finish_reason))

        # Verify
        assert len(results) == 1
        assert "Error generating response" in results[0][0]
        assert results[0][1] == "error"
