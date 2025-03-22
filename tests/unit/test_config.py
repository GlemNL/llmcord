import os
import yaml
import pytest
from unittest.mock import patch, mock_open

from config.config import Config


@pytest.fixture
def test_config_data():
    return {
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
            "channels": {"allowed_ids": [777, 888], "blocked_ids": [999]}
        },
        "system_prompt": "Test system prompt",
        "providers": {
            "openai": {
                "base_url": "https://api.openai.com/v1",
                "api_key": "test_api_key"
            }
        },
        "model": "openai/gpt-4o",
        "extra_api_parameters": {
            "max_tokens": 2048,
            "temperature": 0.7
        }
    }


class TestConfig:
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_init_and_reload(self, mock_yaml_load, mock_file, test_config_data):
        # Setup
        mock_yaml_load.return_value = test_config_data
        
        # Execute
        config = Config("test_config.yaml")
        
        # Verify
        mock_file.assert_called_once_with("test_config.yaml", "r")
        mock_yaml_load.assert_called_once()
        assert config.data == test_config_data
        
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_reload_error_handling(self, mock_yaml_load, mock_file):
        # Setup
        mock_yaml_load.side_effect = Exception("Test exception")
        
        # Execute
        config = Config("test_config.yaml")
        
        # Verify
        assert config.data == {}
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_get_method(self, mock_yaml_load, mock_file, test_config_data):
        # Setup
        mock_yaml_load.return_value = test_config_data
        config = Config("test_config.yaml")
        
        # Execute & Verify
        assert config.get("bot_token") == "test_token"
        assert config.get("nonexistent_key") is None
        assert config.get("nonexistent_key", "default") == "default"
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_getitem_method(self, mock_yaml_load, mock_file, test_config_data):
        # Setup
        mock_yaml_load.return_value = test_config_data
        config = Config("test_config.yaml")
        
        # Execute & Verify
        assert config["bot_token"] == "test_token"
        
        # Should raise KeyError for nonexistent key
        with pytest.raises(KeyError):
            config["nonexistent_key"]
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_properties(self, mock_yaml_load, mock_file, test_config_data):
        # Setup
        mock_yaml_load.return_value = test_config_data
        config = Config("test_config.yaml")
        
        # Execute & Verify
        assert config.bot_token == "test_token"
        assert config.client_id == "123456789"
        assert config.status_message == "Testing bot"
        assert config.max_text == 10000
        assert config.max_images == 3
        assert config.max_messages == 10
        assert config.use_plain_responses is False
        assert config.allow_dms is True
        assert config.permissions == test_config_data["permissions"]
        assert config.system_prompt == "Test system prompt"
        assert config.providers == test_config_data["providers"]
        assert config.model == "openai/gpt-4o"
        assert config.extra_api_parameters == test_config_data["extra_api_parameters"]
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_constant_values(self, mock_yaml_load, mock_file, test_config_data):
        # Setup
        mock_yaml_load.return_value = test_config_data
        config = Config("test_config.yaml")
        
        # Execute & Verify
        assert "gpt-4" in config.VISION_MODEL_TAGS
        assert "claude-3" in config.VISION_MODEL_TAGS
        assert "openai" in config.PROVIDERS_SUPPORTING_USERNAMES
        assert "image" in config.ALLOWED_FILE_TYPES
        assert "text" in config.ALLOWED_FILE_TYPES
        assert config.EMBED_COLOR_COMPLETE == 0x006400
        assert config.EMBED_COLOR_INCOMPLETE == 0xFFA500
        assert config.STREAMING_INDICATOR == " ⚪"
        assert config.EDIT_DELAY_SECONDS == 1
        assert config.MAX_MESSAGE_NODES == 100
    
    @patch("builtins.open", new_callable=mock_open)
    @patch("yaml.safe_load")
    def test_default_properties(self, mock_yaml_load, mock_file):
        # Setup - empty config
        mock_yaml_load.return_value = {}
        config = Config("test_config.yaml")
        
        # Execute & Verify - should return defaults
        assert config.bot_token == ""
        assert config.client_id == ""
        assert config.status_message == "github.com/jakobdylanc/llmcord"
        assert config.max_text == 100000
        assert config.max_images == 5
        assert config.max_messages == 25
        assert config.use_plain_responses is False
        assert config.allow_dms is True
        assert config.permissions == {
            "users": {"allowed_ids": [], "blocked_ids": []},
            "roles": {"allowed_ids": [], "blocked_ids": []},
            "channels": {"allowed_ids": [], "blocked_ids": []}
        }
        assert config.system_prompt == ""
        assert config.providers == {}
        assert config.model == ""
        assert config.extra_api_parameters == {}