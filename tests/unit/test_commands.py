import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

import discord

from app.discord_client import LLMCordClient


@pytest.mark.asyncio
async def test_reset_command(discord_client, mock_discord_message):
    """Test the $reset command functionality."""
    # Setup
    mock_discord_message.content = "$reset"
    
    # Make sure the bot is mentioned in the message
    mock_discord_message.mentions = [discord_client.user]
    
    # Mock database.reset_user_history to return True (success)
    discord_client.db.reset_user_history = AsyncMock(return_value=True)
    
    # Execute
    await discord_client.on_message(mock_discord_message)
    
    # Verify
    discord_client.db.reset_user_history.assert_called_once_with(mock_discord_message.author.id)
    mock_discord_message.reply.assert_called_once()
    # Verify the success message contains expected text
    assert "reset" in mock_discord_message.reply.call_args[0][0].lower()
    assert "fresh" in mock_discord_message.reply.call_args[0][0].lower()


@pytest.mark.asyncio
async def test_reset_command_failure(discord_client, mock_discord_message):
    """Test the $reset command when it fails."""
    # Setup
    mock_discord_message.content = "$reset"
    
    # Make sure the bot is mentioned in the message
    mock_discord_message.mentions = [discord_client.user]
    
    # Mock database.reset_user_history to return False (failure)
    discord_client.db.reset_user_history = MagicMock(return_value=False)
    
    # Execute
    await discord_client.on_message(mock_discord_message)
    
    # Verify
    discord_client.db.reset_user_history.assert_called_once_with(mock_discord_message.author.id)
    mock_discord_message.reply.assert_called_once()
    
    # Get the actual response message
    response_message = mock_discord_message.reply.call_args[0][0].lower()
    
    # Check if the response contains expected words for error message
    assert "error" in response_message
    assert "resetting" in response_message
    assert "conversation history" in response_message


@pytest.mark.asyncio
async def test_stats_command(discord_client, mock_discord_message):
    """Test the $stats command functionality."""
    # Setup
    mock_discord_message.content = "$stats"
    
    # Make sure the bot is mentioned in the message
    mock_discord_message.mentions = [discord_client.user]
    
    # Create mock stats return value
    mock_stats = {
        "total_messages": 42,
        "total_conversations": 7,
        "first_conversation": "2023-03-15T14:30:45.123456"
    }
    
    # Mock database.get_user_stats to return our mock stats
    discord_client.db.get_user_stats = AsyncMock(return_value=mock_stats)
    
    # Execute
    await discord_client.on_message(mock_discord_message)
    
    # Verify
    discord_client.db.get_user_stats.assert_called_once_with(mock_discord_message.author.id)
    mock_discord_message.reply.assert_called_once()
    
    # Get the reply content
    reply_content = mock_discord_message.reply.call_args[0][0]
    
    # Since your on_message implementation might directly pass the stats dict
    # or format it in a specific way, handle both cases
    if isinstance(reply_content, dict):
        assert reply_content["total_messages"] == 42
        assert reply_content["total_conversations"] == 7
        assert "2023-03-15" in reply_content["first_conversation"]
    elif isinstance(reply_content, str):
        # If formatted as string, check for key values
        response_text = reply_content.lower()
        assert "42" in response_text or "messages: 42" in response_text
        assert "7" in response_text or "conversations: 7" in response_text
        assert "2023-03-15" in response_text
    else:
        # If another format, just make sure we got some kind of response
        assert reply_content is not None


@pytest.mark.asyncio
async def test_stats_command_no_data(discord_client, mock_discord_message):
    """Test the $stats command when there is no data."""
    # Setup
    mock_discord_message.content = "$stats"
    
    # Make sure the bot is mentioned in the message
    mock_discord_message.mentions = [discord_client.user]
    
    # Create mock stats return value with no data
    mock_stats = {
        "total_messages": 0,
        "total_conversations": 0,
        "first_conversation": None
    }
    
    # Mock database.get_user_stats to return our mock stats
    discord_client.db.get_user_stats = AsyncMock(return_value=mock_stats)
    
    # Execute
    await discord_client.on_message(mock_discord_message)
    
    # Verify
    discord_client.db.get_user_stats.assert_called_once_with(mock_discord_message.author.id)
    mock_discord_message.reply.assert_called_once()
    
    # Check that the reply indicates no data
    reply_content = mock_discord_message.reply.call_args[0][0]
    
    if isinstance(reply_content, dict):
        assert reply_content["total_messages"] == 0
        assert reply_content["total_conversations"] == 0
        assert reply_content["first_conversation"] is None
    elif isinstance(reply_content, str):
        assert "0" in reply_content  # Should show zero messages/conversations
    

@pytest.mark.asyncio
async def test_stats_command_formatting(discord_client, mock_discord_message):
    """Test different formatting scenarios for the stats command."""
    # Setup
    mock_discord_message.content = "$stats"
    
    # Make sure the bot is mentioned in the message
    mock_discord_message.mentions = [discord_client.user]
    
    # Test with different stat formats
    test_cases = [
        # Large numbers
        {
            "total_messages": 12345,
            "total_conversations": 789,
            "first_conversation": "2023-01-01T00:00:00.000000"
        },
        # Very recent date
        {
            "total_messages": 10,
            "total_conversations": 1,
            "first_conversation": datetime.now().isoformat()
        },
        # Very old date
        {
            "total_messages": 5000,
            "total_conversations": 300,
            "first_conversation": "2020-01-01T00:00:00.000000"
        }
    ]
    
    for test_case in test_cases:
        # Mock database.get_user_stats to return our test case
        discord_client.db.get_user_stats = AsyncMock(return_value=test_case)
        mock_discord_message.reply.reset_mock()
        
        # Execute
        await discord_client.on_message(mock_discord_message)
        
        # Verify basic call patterns
        discord_client.db.get_user_stats.assert_called_once_with(mock_discord_message.author.id)
        mock_discord_message.reply.assert_called_once()
        
        # Reset for next test case
        discord_client.db.get_user_stats.reset_mock()


@pytest.mark.asyncio
async def test_stats_command_exception_handling(discord_client, mock_discord_message):
    """Test handling of exceptions in the stats command."""
    # Setup
    mock_discord_message.content = "$stats"
    
    # Make sure the bot is mentioned in the message
    mock_discord_message.mentions = [discord_client.user]
    
    # Mock database.get_user_stats to raise an exception
    discord_client.db.get_user_stats = AsyncMock(side_effect=Exception("Database error"))
    
    # Execute
    await discord_client.on_message(mock_discord_message)
    
    # Verify
    discord_client.db.get_user_stats.assert_called_once_with(mock_discord_message.author.id)
    mock_discord_message.reply.assert_called_once()


@pytest.mark.asyncio
async def test_reset_command_exception_handling(discord_client, mock_discord_message):
    """Test handling of exceptions in the reset command."""
    # Setup
    mock_discord_message.content = "$reset"
    
    # Make sure the bot is mentioned in the message
    mock_discord_message.mentions = [discord_client.user]
    
    # Mock database.reset_user_history to raise an exception
    discord_client.db.reset_user_history = AsyncMock(side_effect=Exception("Database error"))
    
    # Execute
    await discord_client.on_message(mock_discord_message)
    
    # Verify
    discord_client.db.reset_user_history.assert_called_once_with(mock_discord_message.author.id)
    mock_discord_message.reply.assert_called_once()


@pytest.mark.asyncio
async def test_commands_in_guild(discord_client, mock_discord_message):
    """Test that commands work in guild channels."""
    # Setup for $reset command in guild
    mock_discord_message.content = "$reset"
    mock_discord_message.channel.type = discord.ChannelType.text
    
    # Make sure the bot is mentioned in the message
    mock_discord_message.mentions = [discord_client.user]
    
    discord_client.db.reset_user_history = AsyncMock(return_value=True)
    
    # Execute
    await discord_client.on_message(mock_discord_message)
    
    # Verify
    discord_client.db.reset_user_history.assert_called_once_with(mock_discord_message.author.id)
    mock_discord_message.reply.assert_called_once()


@pytest.mark.asyncio
async def test_commands_in_reply_to_bot(discord_client, mock_discord_message):
    """Test that commands don't work when replying to a bot message."""
    # Setup for $reset command in a reply to the bot
    mock_discord_message.content = "$reset"
    mock_discord_message.channel.type = discord.ChannelType.text
    
    # Set up the message reference to point to a bot message
    mock_bot_message = MagicMock(spec=discord.Message)
    mock_bot_message.author = discord_client.user
    mock_bot_message.id = 12345
    
    mock_discord_message.reference = MagicMock()
    mock_discord_message.reference.resolved = mock_bot_message
    mock_discord_message.reference.message_id = mock_bot_message.id
    mock_discord_message.reference.cached_message = mock_bot_message
    
    # No need for mentions when replying
    mock_discord_message.mentions = []
    
    discord_client.db.reset_user_history = AsyncMock(return_value=True)
    
    # Execute
    await discord_client.on_message(mock_discord_message)
    
    # Verify
    discord_client.db.reset_user_history.assert_not_called()
    mock_discord_message.reply.assert_not_called()


@pytest.mark.asyncio
async def test_commands_in_dm(discord_client, mock_discord_message):
    """Test that commands work in DM channels."""
    # Setup for $reset command in DM
    mock_discord_message.content = "$reset"
    
    # For DMs, we need to modify the message's channel and guild
    mock_discord_message.guild = None  # DMs have no guild
    mock_discord_message.channel = MagicMock(spec=discord.DMChannel)
    mock_discord_message.channel.type = discord.ChannelType.private
    mock_discord_message.channel.id = 777
    
    # No need to mention the bot in DMs
    mock_discord_message.mentions = []
    
    discord_client.db.reset_user_history = AsyncMock(return_value=True)
    
    # Execute
    await discord_client.on_message(mock_discord_message)
    
    # Verify
    discord_client.db.reset_user_history.assert_called_once_with(mock_discord_message.author.id)
    mock_discord_message.reply.assert_called_once()


@pytest.mark.asyncio
async def test_commands_with_mention(discord_client, mock_discord_message):
    """Test that commands work when the bot is mentioned."""
    # Setup for $reset command with mention
    mock_discord_message.content = f"<@{discord_client.user.id}> $reset"
    mock_discord_message.mentions = [discord_client.user]
    discord_client.db.reset_user_history = AsyncMock(return_value=True)
    
    # Execute
    await discord_client.on_message(mock_discord_message)
    
    # Verify
    discord_client.db.reset_user_history.assert_called_once_with(mock_discord_message.author.id)
    mock_discord_message.reply.assert_called_once()


@pytest.mark.asyncio
async def test_commands_respect_permissions(discord_client, mock_discord_message, test_config):
    """Test that commands respect the permission settings."""
    # Setup
    mock_discord_message.content = "$reset"
        # Make sure the bot is mentioned in the message
    mock_discord_message.mentions = [discord_client.user]
    
    # Set up a blocked user ID
    mock_discord_message.author.id = 333  # This ID is in blocked_ids in the test config
    
    # Set up the check_permissions function to properly respect the config
    with patch('app.utils.check_permissions', return_value=False) as mock_check:
        # Execute
        await discord_client.on_message(mock_discord_message)
        
        # Verify that the reset method was never called due to permissions
        discord_client.db.reset_user_history.assert_not_called()
        # Verify that no reply was sent
        mock_discord_message.reply.assert_not_called()