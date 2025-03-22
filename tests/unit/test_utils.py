import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import discord
import httpx
import base64

from app.utils import (
    extract_message_content,
    find_parent_message,
    check_permissions,
    create_embed_for_warnings,
    truncate_messages
)
from app.models import MsgNode, ConversationWarnings


class TestExtractMessageContent:
    
    @pytest.mark.asyncio
    async def test_extract_text_only(self, mock_discord_message, mock_client, test_config):
        # Setup
        mock_discord_message.content = "Hello, bot!"
        mock_discord_message.attachments = []
        mock_node = MsgNode()
        
        # Execute
        text, images, has_bad_attachments = await extract_message_content(
            mock_discord_message, mock_node, mock_client, test_config
        )
        
        # Verify
        assert text == "Hello, bot!"
        assert images == []
        assert has_bad_attachments is False
    
    @pytest.mark.asyncio
    async def test_extract_with_bot_mention(self, mock_discord_message, mock_client, test_config):
        # Setup
        bot_id = 999
        mock_discord_message.content = f"<@{bot_id}> Hello!"
        mock_discord_message.guild.me.id = bot_id
        mock_discord_message.mentions = [MagicMock(spec=discord.Member)]
        mock_discord_message.mentions[0].id = bot_id
        mock_node = MsgNode()
        
        # Execute
        text, images, has_bad_attachments = await extract_message_content(
            mock_discord_message, mock_node, mock_client, test_config
        )
        
        # Verify
        assert text == "Hello!"
        assert images == []
        assert has_bad_attachments is False
    
    @pytest.mark.asyncio
    async def test_extract_with_embeds(self, mock_discord_message, mock_client, test_config):
        # Setup
        mock_embed = MagicMock(spec=discord.Embed)
        mock_embed.description = "Embed description"
        mock_discord_message.content = "Message content"
        mock_discord_message.embeds = [mock_embed]
        mock_node = MsgNode()
        
        # Execute
        text, images, has_bad_attachments = await extract_message_content(
            mock_discord_message, mock_node, mock_client, test_config
        )
        
        # Verify
        assert "Message content" in text
        assert "Embed description" in text
        assert images == []
        assert has_bad_attachments is False
    
    @pytest.mark.asyncio
    async def test_extract_with_text_attachment(self, mock_discord_message, mock_client, test_config):
        # Setup
        mock_attachment = MagicMock(spec=discord.Attachment)
        mock_attachment.content_type = "text/plain"
        mock_attachment.url = "http://example.com/file.txt"
        mock_discord_message.attachments = [mock_attachment]
        
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = "Text file content"
        mock_client.get.return_value = mock_response
        
        mock_node = MsgNode()
        
        # Execute
        text, images, has_bad_attachments = await extract_message_content(
            mock_discord_message, mock_node, mock_client, test_config
        )
        
        # Verify
        assert "Hello, bot!" in text  # The original content
        assert "Text file content" in text  # The attached file content
        assert images == []
        assert has_bad_attachments is False
        mock_client.get.assert_called_once_with(mock_attachment.url)
    
    @pytest.mark.asyncio
    async def test_extract_with_image_attachment(self, mock_discord_message, mock_client, test_config):
        # Setup
        mock_attachment = MagicMock(spec=discord.Attachment)
        mock_attachment.content_type = "image/jpeg"
        mock_attachment.url = "http://example.com/image.jpg"
        mock_discord_message.attachments = [mock_attachment]
        
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b"fake_image_data"
        mock_client.get.return_value = mock_response
        
        mock_node = MsgNode()
        
        # Execute
        text, images, has_bad_attachments = await extract_message_content(
            mock_discord_message, mock_node, mock_client, test_config
        )
        
        # Verify
        assert text == "Hello, bot!"  # The original content
        assert len(images) == 1
        assert images[0]["type"] == "image_url"
        assert "data:image/jpeg;base64," in images[0]["image_url"]["url"]
        assert has_bad_attachments is False
        mock_client.get.assert_called_once_with(mock_attachment.url)
    
    @pytest.mark.asyncio
    async def test_extract_with_unsupported_attachment(self, mock_discord_message, mock_client, test_config):
        # Setup
        mock_attachment = MagicMock(spec=discord.Attachment)
        mock_attachment.content_type = "application/pdf"  # Unsupported type
        mock_attachment.url = "http://example.com/doc.pdf"
        mock_discord_message.attachments = [mock_attachment]
        
        mock_node = MsgNode()
        
        # Execute
        text, images, has_bad_attachments = await extract_message_content(
            mock_discord_message, mock_node, mock_client, test_config
        )
        
        # Verify
        assert text == "Hello, bot!"
        assert images == []
        assert has_bad_attachments is True
        mock_client.get.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_extract_with_failed_attachment_fetch(self, mock_discord_message, mock_client, test_config):
        # Setup
        mock_attachment = MagicMock(spec=discord.Attachment)
        mock_attachment.content_type = "image/jpeg"
        mock_attachment.url = "http://example.com/image.jpg"
        mock_discord_message.attachments = [mock_attachment]
        
        # Mock client to raise an exception
        mock_client.get.side_effect = Exception("Connection error")
        
        mock_node = MsgNode()
        
        # Execute
        text, images, has_bad_attachments = await extract_message_content(
            mock_discord_message, mock_node, mock_client, test_config
        )
        
        # Verify
        assert text == "Hello, bot!"
        assert images == []
        assert has_bad_attachments is False  # Not marked as bad, just failed to fetch
        mock_client.get.assert_called_once_with(mock_attachment.url)


class TestFindParentMessage:
    
    @pytest.mark.asyncio
    async def test_find_parent_direct_reply(self):
        # Setup - Direct reply
        mock_msg = MagicMock(spec=discord.Message)
        mock_parent = MagicMock(spec=discord.Message)
        
        mock_msg.reference = MagicMock()
        mock_msg.reference.message_id = 12345
        mock_msg.reference.cached_message = mock_parent
        
        # Execute
        result = await find_parent_message(mock_msg)
        
        # Verify
        assert result is mock_parent
    
    @pytest.mark.asyncio
    async def test_find_parent_direct_reply_fetch(self):
        # Setup - Direct reply, but not cached
        mock_msg = MagicMock(spec=discord.Message)
        mock_parent = MagicMock(spec=discord.Message)
        
        mock_msg.reference = MagicMock()
        mock_msg.reference.message_id = 12345
        mock_msg.reference.cached_message = None
        
        mock_msg.channel.fetch_message = AsyncMock(return_value=mock_parent)
        
        # Execute
        result = await find_parent_message(mock_msg)
        
        # Verify
        assert result is mock_parent
        mock_msg.channel.fetch_message.assert_called_once_with(12345)
    
    @pytest.mark.asyncio
    async def test_find_parent_thread_starter(self):
        # Setup - Thread starter message
        mock_msg = MagicMock(spec=discord.Message)
        mock_parent = MagicMock(spec=discord.Message)
        
        mock_msg.reference = None
        mock_msg.channel.type = discord.ChannelType.public_thread
        mock_msg.channel.starter_message = mock_parent
        
        # Execute
        result = await find_parent_message(mock_msg)
        
        # Verify
        assert result is mock_parent
    
    @pytest.mark.asyncio
    async def test_find_parent_thread_starter_fetch(self):
        # Setup - Thread starter message, but need to fetch
        mock_msg = MagicMock(spec=discord.Message)
        mock_parent = MagicMock(spec=discord.Message)
        
        mock_msg.reference = None
        mock_msg.channel.type = discord.ChannelType.public_thread
        mock_msg.channel.starter_message = None
        mock_msg.channel.id = 12345
        mock_msg.channel.parent.fetch_message = AsyncMock(return_value=mock_parent)
        
        # Execute
        result = await find_parent_message(mock_msg)
        
        # Verify
        assert result is mock_parent
        mock_msg.channel.parent.fetch_message.assert_called_once_with(12345)
    
    @pytest.mark.asyncio
    async def test_find_parent_dm_previous_message(self):
        # Setup - DM channel, previous message from bot
        mock_msg = MagicMock(spec=discord.Message)
        mock_prev_msg = MagicMock(spec=discord.Message)
        
        mock_msg.reference = None
        mock_msg.channel.type = discord.ChannelType.private
        mock_msg.author.bot = False
        
        mock_prev_msg.author.bot = True
        mock_prev_msg.type = discord.MessageType.default
        
        # Mock channel history to return the previous message
        mock_msg.channel.history.return_value.__aiter__.return_value = [mock_prev_msg]
        
        # Execute
        result = await find_parent_message(mock_msg)
        
        # Verify
        assert result is mock_prev_msg
    
    @pytest.mark.asyncio
    async def test_find_parent_same_author_previous_message(self):
        # Setup - Regular channel, previous message from same author
        mock_msg = MagicMock(spec=discord.Message)
        mock_prev_msg = MagicMock(spec=discord.Message)
        
        mock_msg.reference = None
        mock_msg.channel.type = discord.ChannelType.text
        mock_msg.guild.me = MagicMock()
        mock_msg.content = "Hello"  # No bot mention
        
        mock_prev_msg.author = mock_msg.author  # Same author
        mock_prev_msg.type = discord.MessageType.default
        
        # Mock channel history to return the previous message
        mock_msg.channel.history.return_value.__aiter__.return_value = [mock_prev_msg]
        
        # Execute
        result = await find_parent_message(mock_msg)
        
        # Verify
        assert result is mock_prev_msg
    
    @pytest.mark.asyncio
    async def test_find_parent_with_bot_mention(self):
        # Setup - Message with bot mention should start a new conversation
        mock_msg = MagicMock(spec=discord.Message)
        mock_msg.reference = None
        mock_msg.guild.me.id = 999
        mock_msg.content = f"<@999> Hello!"  # Bot mention
        
        # Execute
        result = await find_parent_message(mock_msg)
        
        # Verify
        assert result is None  # Should not find a parent
    
    @pytest.mark.asyncio
    async def test_find_parent_error_handling(self):
        # Setup - Discord API error
        mock_msg = MagicMock(spec=discord.Message)
        mock_msg.reference = MagicMock()
        mock_msg.reference.message_id = 12345
        mock_msg.reference.cached_message = None
        
        # Simulate a Discord API error
        mock_msg.channel.fetch_message = AsyncMock(side_effect=discord.NotFound(response=MagicMock(), message="Message not found"))
        
        # Execute
        result = await find_parent_message(mock_msg)
        
        # Verify
        assert result is None  # Should handle the error and return None


class TestCheckPermissions:
    
    def test_check_dm_allowed(self, test_config, mock_discord_message):
        # Setup
        mock_discord_message.channel.type = discord.ChannelType.private
        test_config.allow_dms = True
        
        # Execute
        result = check_permissions(mock_discord_message, test_config)
        
        # Verify
        assert result is True
    
    def test_check_dm_not_allowed(self, test_config, mock_discord_message):
        # Setup
        mock_discord_message.channel.type = discord.ChannelType.private
        test_config.allow_dms = False
        
        # Execute
        result = check_permissions(mock_discord_message, test_config)
        
        # Verify
        assert result is False
    
    def test_check_user_explicitly_allowed(self, test_config, mock_discord_message):
        # Setup
        user_id = 111  # From the mock_discord_message fixture
        
        # Ensure user ID is in allowed list
        test_config.permissions["users"]["allowed_ids"] = [user_id]
        
        # Execute
        result = check_permissions(mock_discord_message, test_config)
        
        # Verify
        assert result is True
    
    def test_check_user_explicitly_blocked(self, test_config, mock_discord_message):
        # Setup
        user_id = 111  # From the mock_discord_message fixture
        
        # Ensure user ID is in blocked list
        test_config.permissions["users"]["blocked_ids"] = [user_id]
        
        # Execute
        result = check_permissions(mock_discord_message, test_config)
        
        # Verify
        assert result is False
    
    def test_check_role_allowed(self, test_config, mock_discord_message):
        # Setup
        # Create roles with IDs
        role1 = MagicMock(spec=discord.Role)
        role1.id = 444  # This is in allowed_ids in the test_config fixture
        
        role2 = MagicMock(spec=discord.Role)
        role2.id = 999  # This is not in allowed_ids
        
        # Assign roles to the author
        mock_discord_message.author.roles = [role1, role2]
        
        # Execute
        result = check_permissions(mock_discord_message, test_config)
        
        # Verify
        assert result is True
    
    def test_check_role_blocked(self, test_config, mock_discord_message):
        # Setup
        # Create roles with IDs
        role1 = MagicMock(spec=discord.Role)
        role1.id = 666  # This is in blocked_ids in the test_config fixture
        
        role2 = MagicMock(spec=discord.Role)
        role2.id = 999  # This is not in blocked_ids
        
        # Assign roles to the author
        mock_discord_message.author.roles = [role1, role2]
        
        # Execute
        result = check_permissions(mock_discord_message, test_config)
        
        # Verify
        assert result is False
    
    def test_check_channel_allowed(self, test_config, mock_discord_message):
        # Setup
        channel_id = 777  # From the mock_discord_message fixture
        
        # Ensure channel ID is in allowed list
        test_config.permissions["channels"]["allowed_ids"] = [channel_id]
        
        # Execute
        result = check_permissions(mock_discord_message, test_config)
        
        # Verify
        assert result is True
    
    def test_check_channel_blocked(self, test_config, mock_discord_message):
        # Setup
        channel_id = 777  # From the mock_discord_message fixture
        
        # Ensure channel ID is in blocked list
        test_config.permissions["channels"]["blocked_ids"] = [channel_id]
        
        # Execute
        result = check_permissions(mock_discord_message, test_config)
        
        # Verify
        assert result is False
    
    def test_check_parent_channel_allowed(self, test_config, mock_discord_message):
        # Setup - Thread channel with parent
        mock_discord_message.channel.parent_id = 888  # This is in allowed_ids
        
        # Ensure parent channel ID is in allowed list
        test_config.permissions["channels"]["allowed_ids"] = [888]
        
        # Execute
        result = check_permissions(mock_discord_message, test_config)
        
        # Verify
        assert result is True
    
    def test_check_category_channel_allowed(self, test_config, mock_discord_message):
        # Setup - Channel with category
        mock_discord_message.channel.category_id = 888  # This is in allowed_ids
        
        # Ensure category ID is in allowed list
        test_config.permissions["channels"]["allowed_ids"] = [888]
        
        # Execute
        result = check_permissions(mock_discord_message, test_config)
        
        # Verify
        assert result is True


class TestCreateEmbedForWarnings:
    
    def test_create_embed_empty_warnings(self):
        # Setup
        warnings = ConversationWarnings()
        
        # Execute
        embed = create_embed_for_warnings(warnings)
        
        # Verify
        assert isinstance(embed, discord.Embed)
        assert len(embed.fields) == 0
    
    def test_create_embed_with_warnings(self):
        # Setup
        warnings = ConversationWarnings()
        warnings.add("Warning 1")
        warnings.add("Warning 2")
        
        # Execute
        embed = create_embed_for_warnings(warnings)
        
        # Verify
        assert isinstance(embed, discord.Embed)
        assert len(embed.fields) == 2
        assert embed.fields[0].name == "Warning 1"
        assert embed.fields[0].value == ""
        assert embed.fields[1].name == "Warning 2"
        assert embed.fields[1].value == ""


class TestTruncateMessages:
    
    def test_truncate_messages_empty(self):
        # Setup
        messages = []
        
        # Execute
        result = truncate_messages(messages, 1000)
        
        # Verify
        assert result == []
    
    def test_truncate_messages_single_short(self):
        # Setup
        messages = [{"content": "Short message"}]
        
        # Execute
        result = truncate_messages(messages, 1000)
        
        # Verify
        assert len(result) == 1
        assert result[0] == "Short message"
    
    def test_truncate_messages_single_long(self):
        # Setup
        long_message = "a" * 1500
        messages = [{"content": long_message}]
        
        # Execute
        result = truncate_messages(messages, 1000)
        
        # Verify
        assert len(result) == 2
        assert result[0] == "a" * 1000
        assert result[1] == "a" * 500
    
    def test_truncate_messages_multiple(self):
        # Setup
        messages = [
            {"content": "First message"},
            {"content": "Second message"}
        ]
        
        # Execute
        result = truncate_messages(messages, 1000)
        
        # Verify
        assert len(result) == 1
        assert result[0] == "First messageSecond message"
    
    def test_truncate_messages_multiple_long(self):
        # Setup
        messages = [
            {"content": "a" * 900},
            {"content": "b" * 300}
        ]
        
        # Execute
        result = truncate_messages(messages, 1000)
        
        # Verify
        assert len(result) == 2
        assert result[0] == "a" * 900
        assert result[1] == "b" * 300
    
    def test_truncate_messages_non_string_content(self):
        # Setup
        messages = [
            {"content": 123},  # Non-string content
            # {"role": "user"}  # Missing content
        ]
        
        # Execute
        result = truncate_messages(messages, 1000)
        
        # Verify - should handle gracefully
        assert len(result) == 1
        assert result[0] == ""  # Empty string for non-string content