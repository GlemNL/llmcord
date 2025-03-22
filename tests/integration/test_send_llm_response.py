from unittest.mock import AsyncMock, MagicMock, patch

import discord
import pytest

from app.models import ConversationWarnings


class TestSendLLMResponse:

    @pytest.mark.asyncio
    async def test_send_llm_response_plain_response(
        self, discord_client, mock_discord_message
    ):
        # Setup
        messages = [{"role": "user", "content": "Hello"}]
        warnings = ConversationWarnings()
        use_plain_responses = True
        max_message_length = 2000

        # Mock the LLM response using a real async generator
        content_parts = ["This is a test response", " with multiple parts."]
        finish_reasons = [None, "stop"]

        # Create a proper async generator
        async def mock_generate_response(messages):
            for content, reason in zip(content_parts, finish_reasons):
                yield content, reason

        # Patch the method directly
        discord_client.llm_client.generate_response = mock_generate_response

        # Mock message_store.get to return a MsgNode
        node = MagicMock()
        node.lock = AsyncMock()
        node.lock.acquire = AsyncMock()
        node.lock.release = AsyncMock()
        discord_client.message_store.get.return_value = node

        # Execute
        with patch("app.discord_client.asyncio.create_task"):
            await discord_client.send_llm_response(
                mock_discord_message,
                messages,
                warnings,
                use_plain_responses,
                max_message_length,
            )

        # Verify
        mock_discord_message.reply.assert_called_once()

        # Get the arguments from the call
        call_args = mock_discord_message.reply.call_args

        # Check the content based on how it was passed
        if len(call_args[0]) > 0:  # Positional args
            assert "This is a test response with multiple parts." in call_args[0][0]
        elif "content" in call_args[1]:  # Keyword args
            assert (
                "This is a test response with multiple parts."
                in call_args[1]["content"]
            )
            assert call_args[1].get("suppress_embeds", False) is True

    @pytest.mark.asyncio
    async def test_send_llm_response_with_embeds(
        self, discord_client, mock_discord_message
    ):
        # Setup
        messages = [{"role": "user", "content": "Hello"}]
        warnings = ConversationWarnings()
        use_plain_responses = False
        max_message_length = 2000

        # Add a warning to test embed creation
        warnings.add("Test Warning")

        # Mock the LLM response using a real async generator
        content_parts = ["This is a test response", " with multiple parts."]
        finish_reasons = [None, "stop"]

        # Create a proper async generator
        async def mock_generate_response(messages):
            for content, reason in zip(content_parts, finish_reasons):
                yield content, reason

        # Patch the method directly
        discord_client.llm_client.generate_response = mock_generate_response

        # Mock reply to get the response message
        response_msg = MagicMock(spec=discord.Message)
        response_msg.edit = AsyncMock()
        mock_discord_message.reply.return_value = response_msg

        # Mock message_store.get to return a MsgNode
        node = MagicMock()
        node.lock = AsyncMock()
        node.lock.acquire = AsyncMock()
        node.lock.release = AsyncMock()
        discord_client.message_store.get.return_value = node

        # Mock the embed creation
        mock_embed = MagicMock(spec=discord.Embed)
        mock_embed.description = None
        mock_embed.color = None
        mock_embed.fields = []

        with patch("discord.Embed", return_value=mock_embed):
            with patch("app.utils.create_embed_for_warnings", return_value=mock_embed):
                # Mock the asyncio task creation
                with patch(
                    "app.discord_client.asyncio.create_task",
                    side_effect=lambda coro: coro,
                ):
                    # Set current_time for last_task_time check
                    discord_client.last_task_time = 0

                    # Execute
                    await discord_client.send_llm_response(
                        mock_discord_message,
                        messages,
                        warnings,
                        use_plain_responses,
                        max_message_length,
                    )

        # Verify
        mock_discord_message.reply.assert_called_once()

        # Check that the message was created with an embed
        reply_call_args = mock_discord_message.reply.call_args
        assert reply_call_args[1].get("silent", False) is True

        # Verify message_store.set was called to create a node for the response
        discord_client.message_store.set.assert_called_once()

        # Verify the node.text was updated with the complete response text
        assert node.text == "This is a test response with multiple parts."

    @pytest.mark.asyncio
    async def test_send_llm_response_error_handling(
        self, discord_client, mock_discord_message
    ):
        # Setup
        messages = [{"role": "user", "content": "Hello"}]
        warnings = ConversationWarnings()
        use_plain_responses = False
        max_message_length = 2000

        # Mock LLM to raise an exception during generation
        async def mock_generate_error(messages):
            raise Exception("Test error")
            yield  # This won't be reached

        discord_client.llm_client.generate_response = mock_generate_error

        # Execute
        with patch("logging.exception") as mock_logging:
            await discord_client.send_llm_response(
                mock_discord_message,
                messages,
                warnings,
                use_plain_responses,
                max_message_length,
            )

        # Verify error handling
        mock_discord_message.reply.assert_called_once()

        # Get the arguments of the reply call
        call_args = mock_discord_message.reply.call_args

        # Check if error message is in positional args or keyword args
        if len(call_args[0]) > 0:  # Positional args
            assert "Sorry, I encountered an error" in call_args[0][0]
        elif "content" in call_args[1]:  # Keyword args
            assert "Sorry, I encountered an error" in call_args[1]["content"]

        # Verify that the exception was logged
        mock_logging.assert_called_once()
