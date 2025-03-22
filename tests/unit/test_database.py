import os
import sqlite3
import pytest
from datetime import datetime
from unittest.mock import patch

from app.database import Database


class TestDatabase:

    def test_init_creates_tables(self, temp_db_path):
        # Setup & Execute
        db = Database(temp_db_path)

        # Verify tables were created
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()

        # Check conversations table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='conversations'"
        )
        assert cursor.fetchone() is not None

        # Check messages table
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='messages'"
        )
        assert cursor.fetchone() is not None

        conn.close()

    def test_create_conversation(self, db):
        # Setup
        user_id = 12345
        guild_id = 67890
        channel_id = 54321

        # Execute
        conversation_id = db.create_conversation(user_id, guild_id, channel_id)

        # Verify
        assert conversation_id > 0

        # Check if conversation was created in DB
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM conversations WHERE conversation_id = ?", (conversation_id,)
        )
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[1] == user_id  # user_id
        assert row[2] == guild_id  # guild_id
        assert row[3] == channel_id  # channel_id
        assert row[6] == 1  # is_active

    def test_add_message(self, db):
        # Setup
        conversation_id = db.create_conversation(12345, 67890, 54321)
        role = "user"
        content = "Test message"
        discord_message_id = 98765
        has_images = False

        # Execute
        result = db.add_message(
            conversation_id, role, content, discord_message_id, has_images
        )

        # Verify
        assert result is True

        # Check if message was added to DB
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM messages WHERE conversation_id = ?", (conversation_id,)
        )
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row[1] == conversation_id  # conversation_id
        assert row[2] == discord_message_id  # discord_message_id
        assert row[3] == role  # role
        assert row[4] == content  # content
        assert row[6] == has_images  # has_images

    def test_get_active_conversation(self, db):
        # Setup
        user_id = 12345
        conversation_id1 = db.create_conversation(user_id, 67890, 54321)
        # Create a second conversation for the same user (should mark the first as inactive)
        conversation_id2 = db.create_conversation(user_id, 67890, 54321)

        # Execute
        active_conversation_id = db.get_active_conversation(user_id)

        # Verify
        assert active_conversation_id == conversation_id2

        # First conversation should be inactive
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT is_active FROM conversations WHERE conversation_id = ?",
            (conversation_id1,),
        )
        is_active = cursor.fetchone()[0]
        conn.close()

        assert is_active == 0

    def test_get_conversation_messages(self, db):
        # Setup
        conversation_id = db.create_conversation(12345, 67890, 54321)

        # Add multiple messages
        db.add_message(conversation_id, "user", "Message 1")
        db.add_message(conversation_id, "assistant", "Message 2")
        db.add_message(conversation_id, "user", "Message 3")

        # Execute
        messages = db.get_conversation_messages(conversation_id)

        # Verify
        assert len(messages) == 3
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Message 1"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Message 2"
        assert messages[2]["role"] == "user"
        assert messages[2]["content"] == "Message 3"

    def test_reset_user_history(self, db):
        # Setup
        user_id = 12345
        conversation_id = db.create_conversation(user_id, 67890, 54321)

        # Execute
        result = db.reset_user_history(user_id)

        # Verify
        assert result is True

        # Check if conversation was marked as inactive
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT is_active FROM conversations WHERE user_id = ?", (user_id,)
        )
        is_active = cursor.fetchone()[0]
        conn.close()

        assert is_active == 0

    def test_get_user_stats(self, db):
        # Setup
        user_id = 12345
        conversation_id = db.create_conversation(user_id, 67890, 54321)

        # Add multiple messages
        db.add_message(conversation_id, "user", "Message 1")
        db.add_message(conversation_id, "assistant", "Message 2")
        db.add_message(conversation_id, "user", "Message 3")

        # Execute
        stats = db.get_user_stats(user_id)

        # Verify
        assert stats["total_messages"] == 3
        assert stats["total_conversations"] == 1
        assert stats["first_conversation"] is not None

    def test_conversation_limit(self, db):
        # Test that the get_conversation_messages respects the limit parameter

        # Setup
        conversation_id = db.create_conversation(12345, 67890, 54321)

        # Add 10 messages
        for i in range(10):
            db.add_message(
                conversation_id, "user" if i % 2 == 0 else "assistant", f"Message {i}"
            )

        # Execute with limit=5
        messages = db.get_conversation_messages(conversation_id, limit=5)

        # Verify
        assert len(messages) == 5
        for i in range(5):
            assert messages[i]["content"] == f"Message {i}"
