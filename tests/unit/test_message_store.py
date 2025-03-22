from unittest.mock import MagicMock

import pytest

from app.message_store import MessageStore
from app.models import ConversationWarnings, MsgNode


class TestMessageStore:

    def test_init(self, test_config):
        # Setup & Execute
        store = MessageStore(test_config)

        # Verify
        assert store.config == test_config
        assert isinstance(store.nodes, dict)
        assert len(store.nodes) == 0

    def test_get_creates_node_if_not_exists(self, message_store):
        # Setup
        msg_id = 12345

        # Execute
        node = message_store.get(msg_id)

        # Verify
        assert msg_id in message_store.nodes
        assert isinstance(node, MsgNode)
        assert node is message_store.nodes[msg_id]

    def test_get_returns_existing_node(self, message_store):
        # Setup
        msg_id = 12345
        existing_node = MsgNode(text="Existing node")
        message_store.nodes[msg_id] = existing_node

        # Execute
        node = message_store.get(msg_id)

        # Verify
        assert node is existing_node

    def test_set(self, message_store):
        # Setup
        msg_id = 12345
        node = MsgNode(text="Test node")

        # Execute
        message_store.set(msg_id, node)

        # Verify
        assert msg_id in message_store.nodes
        assert message_store.nodes[msg_id] is node

    def test_cleanup_removes_oldest_nodes(self, test_config):
        # Setup
        # Set MAX_MESSAGE_NODES to a smaller value for testing
        test_config.MAX_MESSAGE_NODES = 5
        store = MessageStore(test_config)

        # Add more nodes than the limit
        for i in range(10):
            store.nodes[i] = MsgNode()

        # Execute
        store.cleanup()

        # Verify
        assert len(store.nodes) == 5
        # Verify that only the newest nodes (5-9) remain
        for i in range(5, 10):
            assert i in store.nodes
        # Verify that oldest nodes (0-4) are removed
        for i in range(5):
            assert i not in store.nodes

    @pytest.mark.asyncio
    async def test_build_conversation_chain(self, message_store, mock_discord_message):
        # This test will be incomplete since build_conversation_chain depends on discord_client.py
        # which needs more complex mocking. This is a placeholder implementation.

        # Setup
        mock_parent = MagicMock()
        mock_parent.id = 98765
        mock_discord_message.reference = MagicMock()
        mock_discord_message.reference.message_id = mock_parent.id

        # Create a parent node
        parent_node = MsgNode(text="Parent message")
        message_store.set(mock_parent.id, parent_node)

        # Create current node with parent reference
        curr_node = MsgNode(parent_msg=mock_parent)
        message_store.set(mock_discord_message.id, curr_node)

        # This test would need more complex setup and mocking to fully test the method
        # For now, we'll just test that it returns the expected types
        messages, warnings = await message_store.build_conversation_chain(
            mock_discord_message, 10
        )

        # Verify just the types for now
        assert isinstance(messages, list)
        assert isinstance(warnings, ConversationWarnings)
