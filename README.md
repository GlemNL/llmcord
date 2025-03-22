# LLMCord

![Discord Bot Status](https://img.shields.io/badge/discord-bot-blue)
![License](https://img.shields.io/badge/license-MIT-green)

**LLMCord** is a powerful, customizable Discord bot that connects your server to various Large Language Models (LLMs). This project is forked from [jakobdylanc/llmcord](https://github.com/jakobdylanc/llmcord).

## Features

- 🌈 **Multi-Provider Support**: Connect to OpenAI, Mistral, Groq, X-AI, OpenRouter, Ollama, LM Studio, VLLM, Oobabooga, and Jan AI.
- 🧠 **Conversation Memory**: Maintains context across messages for natural conversations.
- 📊 **Conversation Statistics**: Track usage with built-in `/stats` command.
- 🔄 **Memory Reset**: Start fresh with `/reset` command.
- 🖼️ **Vision Models**: Support for image understanding with compatible models.
- 🔒 **Granular Permissions**: Control access by user, role, and channel.
- 📝 **Custom System Prompts**: Define your bot's personality and behavior.
- 🔧 **Highly Configurable**: Adjust many parameters to suit your needs.
- 🚀 **Docker Ready**: Easy deployment with Docker support.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- A Discord bot token - [Create one here](https://discord.com/developers/applications)
- API keys for your chosen LLM providers

### Installation

#### Using Docker (Recommended)

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/llmcord.git
   cd llmcord
   ```

2. Create a configuration file:
   ```
   cp config/config-example.yaml config/config.yaml
   ```

3. Edit your configuration file:
   ```
   nano config/config.yaml
   ```

4. Run with Docker Compose:
   ```
   docker-compose up -d
   ```

#### Manual Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/llmcord.git
   cd llmcord
   ```

2. Install dependencies using Poetry:
   ```
   pip install poetry
   poetry install
   ```

3. Create and edit your configuration:
   ```
   cp config/config-example.yaml config/config.yaml
   ```

4. Run the bot:
   ```
   python main.py
   ```

## Configuration

The `config/config.yaml` file contains all settings for your bot. Key sections include:

### Discord Settings

```yaml
bot_token: YOUR_BOT_TOKEN
client_id: YOUR_CLIENT_ID
status_message: Custom status message for your bot

max_text: 100000
max_images: 5
max_messages: 25

use_plain_responses: false
allow_dms: true

permissions:
  users:
    allowed_ids: []
    blocked_ids: []
  roles:
    allowed_ids: []
    blocked_ids: []
  channels:
    allowed_ids: []
    blocked_ids: []
```

### LLM Settings

```yaml
providers:
  openai:
    base_url: https://api.openai.com/v1
    api_key: YOUR_API_KEY
  # Configure other providers as needed

model: openai/gpt-4o  # Format: provider/model

extra_api_parameters:
  max_tokens: 4096
  temperature: 1.0

system_prompt: >
  Your custom system prompt goes here.
```

## Usage

Once your bot is running and invited to your server, you can:

1. **Start a conversation**: Mention the bot or send a direct message
2. **Continue conversations**: Reply to previous messages to maintain context
3. **View stats**: Use `/stats` to see your usage statistics
4. **Reset memory**: Use `/reset` to start a fresh conversation

## Bot Responses

The bot supports two response modes:

- **Embedded responses**: Fancy Discord embeds with real-time streaming (default)
- **Plain text responses**: Set `use_plain_responses: true` in config

## Permissions System

Control who can use the bot with:

- **Allowed/blocked users**: Specific Discord user IDs
- **Allowed/blocked roles**: Role-based permissions
- **Allowed/blocked channels**: Limit where the bot can be used

Empty lists with no blocked entries means everyone can use the bot.

## Development

### Project Structure

- `app/`: Core application code
- `config/`: Configuration files and handler
- `tests/`: Test suite
- `main.py`: Entry point

### Running Tests

```
pytest tests/ -v
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Original project by [jakobdylanc](https://github.com/jakobdylanc/llmcord)
- Built with [discord.py](https://github.com/Rapptz/discord.py) and [OpenAI's Python client](https://github.com/openai/openai-python)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request