import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import discord
import asyncio

from app.discord_client import LLMCordClient
from app.message_store import MessageStore
from app.models import MsgNode, ConversationWarnings


class TestLLMCordClient:
    
    @pytest.fixture
    def discord_client(self, test_config):
        """Fixture that provides a test Discord client instance."""
        # Patch discord.Client.__init__ to prevent actual initialization
        with patch('discord.Client.__init__', return_value=None):
            client = LLMCordClient(test_config)
            
            # Create a mock for _connection
            client._connection = MagicMock()
            
            # Instead of trying to set the user property directly, we'll
            # create a mock user and patch the user property to return it
            mock_user = MagicMock(spec=discord.ClientUser)
            mock_user.id = 999
            mock_user.mention = "<@999>"
            
            # Use property() to mock the user property
            type(client).user = property(lambda self: mock_user)
            
            # Mock http_client, llm_client, message_store, and db
            client.http_client = AsyncMock()
            client.llm_client = AsyncMock()
            client.message_store = MagicMock(spec=MessageStore)
            client.db = AsyncMock()
            
            return client
    
    @pytest.mark.asyncio
    async def test_on_ready(self, discord_client):
        # Setup
        mock_user = MagicMock()
        mock_user.id = 12345
        
        # Override the user property to return our mock
        type(discord_client).user = property(lambda self: mock_user)
        discord_client.config.client_id = "67890"
        
        # Execute
        with patch('logging.info') as mock_log:
            await discord_client.on_ready()
        
        # Verify - use partial matching since MagicMock has a dynamic string representation
        # Check that some call contained both "Logged in as" and "(ID: 12345)"
        login_call_found = False
        for call_args in mock_log.call_args_list:
            arg = call_args[0][0]
            if isinstance(arg, str) and "Logged in as" in arg and "(ID: 12345)" in arg:
                login_call_found = True
                break
        
        assert login_call_found, "No login message found with correct user ID"
        
        # Still check the exact URL message
        mock_log.assert_any_call(
            '\n\nBOT INVITE URL:\n'
            f'https://discord.com/api/oauth2/authorize?client_id=67890'
            f'&permissions=412317273088&scope=bot\n'
        )
    
    @pytest.mark.asyncio
    async def test_on_message_bot_message(self, discord_client, mock_discord_message):
        # Setup - Bot message should be ignored
        mock_discord_message.author.bot = True
        
        # Mock process_message_chain to track if it gets called
        with patch.object(discord_client, 'process_message_chain', new_callable=AsyncMock) as mock_process:
            # Execute
            await discord_client.on_message(mock_discord_message)
        
            # Verify - No further processing should occur
            mock_process.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_on_message_no_mention_no_dm(self, discord_client, mock_discord_message):
        # Setup - Message without mention in a regular channel
        mock_discord_message.author.bot = False
        mock_discord_message.channel.type = discord.ChannelType.text
        # Message doesn't mention the bot
        mock_discord_message.mentions = []
        
        # Mock process_message_chain to track if it gets called
        with patch.object(discord_client, 'process_message_chain', new_callable=AsyncMock) as mock_process:
            # Execute
            await discord_client.on_message(mock_discord_message)
            
            # Verify - No processing should occur
            mock_process.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_on_message_with_mention(self, discord_client, mock_discord_message):
        # Setup - Message with bot mention
        mock_discord_message.author.bot = False
        mock_discord_message.channel.type = discord.ChannelType.text
        
        # Message mentions the bot
        # First, we need to configure our mock correctly to ensure it is detected as a mention
        # Let's fix how the user property and mentions are set up
        bot_user = MagicMock(spec=discord.ClientUser)
        bot_user.id = 999
        
        # Set up user property on discord_client to return our bot_user
        type(discord_client).user = property(lambda self: bot_user)
        
        # Set up mentions in the message to include the bot user
        mock_discord_message.mentions = [bot_user]
        
        # Make sure the user.mentioned_in method works
        bot_user.mentioned_in = MagicMock(return_value=True)
        
        # Mock check_permissions to return True
        with patch('app.discord_client.check_permissions', return_value=True):
            with patch.object(discord_client, 'process_message_chain', new_callable=AsyncMock) as mock_process:
                # Execute
                await discord_client.on_message(mock_discord_message)
                
                # Verify
                mock_process.assert_called_once_with(mock_discord_message)
    
    @pytest.mark.asyncio
    async def test_on_message_in_dm(self, discord_client, mock_discord_message):
        # Setup - DM message
        mock_discord_message.author.bot = False
        mock_discord_message.channel.type = discord.ChannelType.private
        mock_discord_message.mentions = []  # No mentions needed in DMs
        
        # Mock check_permissions to return True and process_message_chain
        with patch('app.discord_client.check_permissions', return_value=True):
            with patch.object(discord_client, 'process_message_chain', new_callable=AsyncMock) as mock_process:
                # Execute
                await discord_client.on_message(mock_discord_message)
                
                # Verify
                mock_process.assert_called_once_with(mock_discord_message)
    
    @pytest.mark.asyncio
    async def test_on_message_insufficient_permissions(self, discord_client, mock_discord_message):
        # Setup - User doesn't have permission
        mock_discord_message.author.bot = False
        mock_discord_message.channel.type = discord.ChannelType.text
        mock_discord_message.mentions = [discord_client.user]
        
        # Mock check_permissions to return False
        with patch('app.discord_client.check_permissions', return_value=False):
            with patch.object(discord_client, 'process_message_chain', new_callable=AsyncMock) as mock_process:
                # Execute
                await discord_client.on_message(mock_discord_message)
                
                # Verify - No processing should occur
                mock_process.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_on_message_reset_command(self, discord_client, mock_discord_message):
        # Setup - Reset command
        mock_discord_message.author.bot = False
        mock_discord_message.channel.type = discord.ChannelType.text
        mock_discord_message.mentions = [discord_client.user]
        mock_discord_message.content = "$reset"
        
        # Mock check_permissions to return True
        with patch('app.discord_client.check_permissions', return_value=True):
            # Mock db.reset_user_history to return True
            discord_client.db.reset_user_history = AsyncMock(return_value=True)
            
            with patch.object(discord_client, 'process_message_chain', new_callable=AsyncMock) as mock_process:
                # Execute
                await discord_client.on_message(mock_discord_message)
                
                # Verify
                discord_client.db.reset_user_history.assert_called_once_with(mock_discord_message.author.id)
                mock_discord_message.reply.assert_called_once_with("Your conversation history has been reset. Starting fresh!")
                mock_process.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_on_message_stats_command(self, discord_client, mock_discord_message):
        # Setup - Stats command
        mock_discord_message.author.bot = False
        mock_discord_message.channel.type = discord.ChannelType.text
        mock_discord_message.mentions = [discord_client.user]
        mock_discord_message.content = "$stats"
        
        # Mock check_permissions to return True
        with patch('app.discord_client.check_permissions', return_value=True):
            # Mock db.get_user_stats
            discord_client.db.get_user_stats = AsyncMock(return_value={
                "total_messages": 10,
                "total_conversations": 2,
                "first_conversation": "2023-01-01"
            })
            
            with patch.object(discord_client, 'process_message_chain', new_callable=AsyncMock) as mock_process:
                # Execute
                await discord_client.on_message(mock_discord_message)
                
                # Verify
                discord_client.db.get_user_stats.assert_called_once_with(mock_discord_message.author.id)
                mock_discord_message.reply.assert_called_once()
                mock_process.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_process_message_node(self, discord_client, mock_discord_message):
        # Setup
        node = MsgNode()
        
        # Mock extract_message_content
        with patch('app.discord_client.extract_message_content', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = ("Hello", [], False)
            
            # Mock find_parent_message
            with patch('app.discord_client.find_parent_message', new_callable=AsyncMock) as mock_find_parent:
                parent_msg = MagicMock(spec=discord.Message)
                mock_find_parent.return_value = parent_msg
                
                # Execute
                await discord_client.process_message_node(mock_discord_message, node)
                
                # Verify
                mock_extract.assert_called_once_with(
                    mock_discord_message, node, discord_client.http_client, discord_client.config
                )
                
                assert node.text == "Hello"
                assert node.images == []
                assert node.has_bad_attachments is False
                assert node.role == "user"  # Since message is from a user, not the bot
                assert node.user_id == mock_discord_message.author.id
                assert node.parent_msg is parent_msg
    
    @pytest.mark.asyncio
    async def test_process_message_node_bot_message(self, discord_client, mock_discord_message):
        # Setup - Bot message
        node = MsgNode()
        # Make the message appear to be from the bot
        mock_discord_message.author = discord_client.user
        
        # Mock extract_message_content
        with patch('app.discord_client.extract_message_content', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = ("Bot response", [], False)
            
            # Execute
            await discord_client.process_message_node(mock_discord_message, node)
            
            # Verify
            assert node.role == "assistant"  # Since message is from the bot
            assert node.user_id is None  # Bot doesn't have a user_id
    
    @pytest.mark.asyncio
    async def test_process_message_node_with_parent_reference(self, discord_client, mock_discord_message):
        # Setup - Message with reference
        node = MsgNode()
        mock_discord_message.reference = MagicMock()
        mock_discord_message.reference.message_id = 12345
        
        # Mock extract_message_content
        with patch('app.discord_client.extract_message_content', new_callable=AsyncMock) as mock_extract:
            mock_extract.return_value = ("Hello", [], False)
            
            # Mock find_parent_message - parent fetch fails
            with patch('app.discord_client.find_parent_message', new_callable=AsyncMock) as mock_find_parent:
                mock_find_parent.return_value = None
                
                # Execute
                await discord_client.process_message_node(mock_discord_message, node)
                
                # Verify
                assert node.parent_msg is None
                assert node.fetch_parent_failed is True
    
    @pytest.mark.asyncio
    async def test_build_message_chain(self, discord_client, mock_discord_message):
        # This test is more complex and would require extensive mocking
        # Here's a partial implementation focusing on key functionality
        
        # Setup
        # Create a simple message chain
        current_node = MsgNode(text="User message", role="user", user_id=111)
        parent_node = MsgNode(text="Bot response", role="assistant")
        grandparent_node = MsgNode(text="Earlier user message", role="user", user_id=111)
        
        # Mock parent relationships
        parent_msg = MagicMock(spec=discord.Message)
        parent_msg.id = 12345
        grandparent_msg = MagicMock(spec=discord.Message)
        grandparent_msg.id = 67890
        
        current_node.parent_msg = parent_msg
        parent_node.parent_msg = grandparent_msg
        
        # Set up message store to return our nodes
        def mock_get(msg_id):
            if msg_id == mock_discord_message.id:
                return current_node
            elif msg_id == parent_msg.id:
                return parent_node
            elif msg_id == grandparent_msg.id:
                return grandparent_node
            return MsgNode()
        
        discord_client.message_store.get.side_effect = mock_get
        
        # Mock process_message_node
        discord_client.process_message_node = AsyncMock()
        
        # Mock db functions
        discord_client.db.get_active_conversation = AsyncMock(return_value=None)
        discord_client.db.create_conversation = AsyncMock(return_value=1)
        discord_client.db.add_message = AsyncMock(return_value=True)
        
        # Configure LLM client capabilities
        discord_client.llm_client.model_supports_images.return_value = True
        discord_client.llm_client.provider_supports_usernames.return_value = True
        
        # Execute
        messages, warnings = await discord_client.build_message_chain(mock_discord_message)
        
        # Verify
        # Check that process_message_node was called for each message
        assert discord_client.process_message_node.call_count >= 1
        
        # Verify message format
        assert isinstance(messages, list)
        assert isinstance(warnings, ConversationWarnings)