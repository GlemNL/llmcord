import pytest
import asyncio
from unittest.mock import MagicMock

from app.models import MsgNode, ConversationWarnings


class TestMsgNode:

    def test_init_defaults(self):
        # Setup & Execute
        node = MsgNode()

        # Verify default values
        assert node.text is None
        assert node.images == []
        assert node.role == "assistant"
        assert node.user_id is None
        assert node.has_bad_attachments is False
        assert node.fetch_parent_failed is False
        assert node.parent_msg is None
        assert isinstance(node.lock, asyncio.Lock)

    def test_init_with_values(self):
        # Setup
        mock_parent = MagicMock()

        # Execute
        node = MsgNode(
            text="Test message",
            images=[{"type": "image_url", "image_url": {"url": "test_url"}}],
            role="user",
            user_id=12345,
            has_bad_attachments=True,
            fetch_parent_failed=True,
            parent_msg=mock_parent,
        )

        # Verify
        assert node.text == "Test message"
        assert len(node.images) == 1
        assert node.images[0]["type"] == "image_url"
        assert node.role == "user"
        assert node.user_id == 12345
        assert node.has_bad_attachments is True
        assert node.fetch_parent_failed is True
        assert node.parent_msg is mock_parent
        assert isinstance(node.lock, asyncio.Lock)

    @pytest.mark.asyncio
    async def test_lock(self):
        # Setup
        node = MsgNode()

        # Execute & Verify
        # Lock should not be held initially
        assert not node.lock.locked()

        # Acquire the lock
        async with node.lock:
            # Lock should be held
            assert node.lock.locked()

        # Lock should be released automatically
        assert not node.lock.locked()


class TestConversationWarnings:

    def test_init(self):
        # Setup & Execute
        warnings = ConversationWarnings()

        # Verify
        assert isinstance(warnings.warnings, set)
        assert len(warnings.warnings) == 0

    def test_add(self):
        # Setup
        warnings = ConversationWarnings()

        # Execute
        warnings.add("Warning 1")
        warnings.add("Warning 2")
        warnings.add("Warning 1")  # Duplicate should be ignored

        # Verify
        assert len(warnings.warnings) == 2
        assert "Warning 1" in warnings.warnings
        assert "Warning 2" in warnings.warnings

    def test_get_sorted(self):
        # Setup
        warnings = ConversationWarnings()
        warnings.add("C - Warning")
        warnings.add("A - Warning")
        warnings.add("B - Warning")

        # Execute
        sorted_warnings = warnings.get_sorted()

        # Verify
        assert sorted_warnings == ["A - Warning", "B - Warning", "C - Warning"]
