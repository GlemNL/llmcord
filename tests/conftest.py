import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import discord
import httpx
import pytest

from app.database import Database
from app.discord_client import LLMCordClient
from app.llm_client import LLMClient
from app.message_store import MessageStore
from config.config import Config


@pytest.fixture
def temp_db_path(tmp_path):
    """Fixture that provides a temporary database path."""
    db_path = tmp_path / "test_db.db"
    return str(db_path)


@pytest.fixture
def test_config():
    """Fixture that provides a test configuration."""
    config_dict = {
        "bot_token": "test_token",
        "client_id": "123456789",
        "status_message": "Testing bot",
        "max_text": 10000,
        "max_images": 3,
        "max_messages": 10,
        "use_plain_responses": False,
        "allow_dms": True,
        "permissions": {
            "users": {"allowed_ids": [111, 222], "blocked_ids": [333]},
            "roles": {"allowed_ids": [444, 555], "blocked_ids": [666]},
            "channels": {"allowed_ids": [777, 888], "blocked_ids": [999]},
        },
        "system_prompt": "Test system prompt",
        "providers": {
            "openai": {
                "base_url": "https://api.openai.com/v1",
                "api_key": "test_api_key",
            },
            "ollama": {"base_url": "http://localhost:11434/v1"},
        },
        "model": "openai/gpt-4o",
        "extra_api_parameters": {"max_tokens": 2048, "temperature": 0.7},
    }

    # Create a mock Config object
    mock_config = MagicMock(spec=Config)

    # Set attributes on the mock
    for key, value in config_dict.items():
        setattr(mock_config, key, value)

    # Set properties that the code accesses via properties
    mock_config.bot_token = config_dict["bot_token"]
    mock_config.client_id = config_dict["client_id"]
    mock_config.status_message = config_dict["status_message"]
    mock_config.max_text = config_dict["max_text"]
    mock_config.max_images = config_dict["max_images"]
    mock_config.max_messages = config_dict["max_messages"]
    mock_config.use_plain_responses = config_dict["use_plain_responses"]
    mock_config.allow_dms = config_dict["allow_dms"]
    mock_config.permissions = config_dict["permissions"]
    mock_config.system_prompt = config_dict["system_prompt"]
    mock_config.providers = config_dict["providers"]
    mock_config.model = config_dict["model"]
    mock_config.extra_api_parameters = config_dict["extra_api_parameters"]

    # Constants
    mock_config.VISION_MODEL_TAGS = (
        "gpt-4",
        "claude-3",
        "gemini",
        "gemma",
        "pixtral",
        "mistral-small",
        "llava",
        "vision",
        "vl",
    )
    mock_config.PROVIDERS_SUPPORTING_USERNAMES = ("openai", "x-ai")
    mock_config.ALLOWED_FILE_TYPES = ("image", "text")
    mock_config.EMBED_COLOR_COMPLETE = 0x006400  # dark_green
    mock_config.EMBED_COLOR_INCOMPLETE = 0xFFA500  # orange
    mock_config.STREAMING_INDICATOR = " ⚪"
    mock_config.EDIT_DELAY_SECONDS = 1
    mock_config.MAX_MESSAGE_NODES = 100

    # Add the reload method
    mock_config.reload.return_value = config_dict

    # Add the get method
    mock_config.get.side_effect = lambda key, default=None: config_dict.get(
        key, default
    )

    # Add dict-like access
    mock_config.__getitem__.side_effect = lambda key: config_dict[key]

    return mock_config


@pytest.fixture
def db(temp_db_path):
    """Fixture that provides a test database instance."""
    return Database(temp_db_path)


@pytest.fixture
def message_store(test_config):
    """Fixture that provides a test message store instance."""
    return MessageStore(test_config)


@pytest.fixture
def llm_client(test_config):
    """Fixture that provides a test LLM client instance."""
    return LLMClient(test_config)


@pytest.fixture
def mock_discord_message():
    """Fixture that provides a mock Discord message."""
    mock_msg = MagicMock(spec=discord.Message)
    mock_msg.id = 123456789
    mock_msg.content = "Hello, bot!"
    mock_msg.attachments = []
    mock_msg.embeds = []
    mock_msg.author = MagicMock(spec=discord.Member)
    mock_msg.author.id = 111
    mock_msg.author.bot = False
    mock_msg.author.name = "TestUser"
    mock_msg.channel = MagicMock(spec=discord.TextChannel)
    mock_msg.channel.id = 777
    mock_msg.channel.type = discord.ChannelType.text
    mock_msg.guild = MagicMock(spec=discord.Guild)
    mock_msg.guild.id = 888
    mock_msg.guild.me = MagicMock(spec=discord.Member)
    mock_msg.guild.me.id = 999
    mock_msg.reference = None
    mock_msg.reply = AsyncMock()

    return mock_msg


@pytest.fixture
def mock_client():
    """Fixture that provides a mock httpx client."""
    mock = AsyncMock(spec=httpx.AsyncClient)
    return mock


@pytest.fixture(scope="session")
def event_loop_policy():
    """Return an event loop policy for all tests."""
    return asyncio.DefaultEventLoopPolicy()


@pytest.fixture
def discord_client(test_config):
    """Fixture that provides a test Discord client instance."""
    # Patch discord.Client.__init__ to prevent actual initialization
    with patch("discord.Client.__init__", return_value=None):
        client = LLMCordClient(test_config)

        # Create mocks for client properties
        client._connection = MagicMock()
        client.http = MagicMock()  # Add this for app_commands.CommandTree

        # Set up a mock tree - this is now set in setup_hook
        client.tree = MagicMock()

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

        # Mock setup_hook to prevent it from being called during tests
        client.setup_hook = AsyncMock()

        return client
