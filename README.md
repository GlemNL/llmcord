# 🤖 LLMcord

> **Transform Discord into a collaborative AI playground**

LLMcord enables seamless interactions with Large Language Models directly in your Discord server. Compatible with virtually any LLM, whether cloud-based or self-hosted.

![LLMcord Banner](https://github.com/jakobdylanc/llmcord/assets/38699060/789d49fe-ef5c-470e-b60e-48ac03057443)

## ✨ Key Capabilities

### Dynamic Conversation System
Interact naturally with AI models through Discord:
- Mention the bot to initiate a conversation
- Continue by replying to messages
- Type `@bot reset` to start fresh
- Check your usage with `@bot stats`

### Flexible Conversation Flow
- Create multiple conversation branches
- Join and continue conversations started by others
- Include any message in context by mentioning the bot while replying

### Additional Interaction Options
- In DMs: Conversations flow automatically without replies
- Thread support: Start a thread from any message and mention the bot to continue there
- Message chaining: Sequential messages from the same user are automatically grouped

### LLM Provider Flexibility

**Cloud-based options:**
- OpenAI API
- xAI API
- Mistral API
- Groq API
- OpenRouter API

**Self-hosted options:**
- Ollama
- LM Studio
- vLLM

Or any OpenAI-compatible API server of your choice.

### Advanced Features
- Persistent conversation storage in SQLite
- Image attachment support with vision-capable models
- Text file attachment handling
- Customizable AI personality
- User identity recognition (OpenAI and xAI APIs)
- Real-time response streaming
- Runtime configuration updates
- Smart warning system
- Efficient message caching
- Fully asynchronous operation

## 📁 Repository Structure

```
llmcord/
├── app/                    # Core application code
├── config/                 # Configuration files
├── data/                   # Data storage
├── scripts/                # Utility scripts
├── docker-compose.yaml
├── Dockerfile
├── main.py                 # Entry point
└── requirements.txt
```

## 🚀 Setup Guide

1. Get the code:
   ```bash
   git clone https://github.com/GlemNL/llmcord
   ```

2. Create your configuration file:
   - Copy "config-example.yaml" to "config.yaml"
   - Configure the following sections:

### Discord Configuration

| Parameter | Details |
| --- | --- |
| **bot_token** | Generate at [discord.com/developers/applications](https://discord.com/developers/applications) (enable "MESSAGE CONTENT INTENT") |
| **client_id** | Found in "OAuth2" tab |
| **status_message** | Custom bot status (max 128 characters) |
| **max_text** | Maximum text length per message (default: 100,000) |
| **max_images** | Maximum images per message (default: 5) |
| **max_messages** | Maximum messages per conversation (default: 25) |
| **use_plain_responses** | Use plaintext instead of embeds (default: false) |
| **allow_dms** | Enable/disable direct messages (default: true) |
| **permissions** | Control access for users, roles, and channels |

### LLM Configuration

| Parameter | Details |
| --- | --- |
| **providers** | API endpoints and keys for LLM providers |
| **model** | Format: `<provider>/<model>` (e.g., `openai/gpt-4o`, `ollama/llama3.3`) |
| **extra_api_parameters** | Additional LLM parameters (default: max_tokens=4096, temperature=1.0) |
| **system_prompt** | Customize bot behavior (leave empty for default) |

3. Launch the bot:

   **Standard method:**
   ```bash
   python -m pip install -U -r requirements.txt
   python main.py
   ```

   **Docker method:**
   ```bash
   # Create persistent storage
   mkdir -p data
   
   # Start with Docker Compose
   docker compose up
   ```

## 🔧 Bot Commands

- `@bot reset` - Clear conversation history
- `@bot stats` - View usage statistics
- `@bot help` - Display command information

## 📝 Additional Notes

- Troubleshooting available in the [issues section](https://github.com/GlemNL/llmcord/issues)
- Only OpenAI and xAI APIs currently support user identity awareness
- Contributions welcome!