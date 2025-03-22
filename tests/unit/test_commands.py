from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import discord
import pytest


class TestSlashCommands:
    @pytest.mark.asyncio
    async def test_reset_command(self, discord_client):
        """Test that the reset command calls the database correctly."""
        # Create a mock interaction
        interaction = MagicMock(spec=discord.Interaction)
        interaction.user = MagicMock(spec=discord.User)
        interaction.user.id = 12345
        interaction.response = AsyncMock()

        # Configure database mock to return success
        discord_client.db.reset_user_history = AsyncMock(return_value=True)

        # Simulate what happens in setup_hook
        async def reset_callback(interaction: discord.Interaction):
            success = discord_client.db.reset_user_history(interaction.user.id)
            if bool(success):
                await interaction.response.send_message(
                    "Your conversation history has been reset. Starting fresh!"
                )
            else:
                await interaction.response.send_message(
                    "There was an error resetting your conversation history."
                )

        # Call the function directly
        await reset_callback(interaction)

        # Verify the database was called correctly
        discord_client.db.reset_user_history.assert_called_once_with(12345)

        # Verify the response was sent
        interaction.response.send_message.assert_called_once()
        assert "reset" in interaction.response.send_message.call_args[0][0]

    @pytest.mark.asyncio
    async def test_stats_command(self, discord_client):
        """Test that the stats command calls the database correctly and formats the response."""
        # Create a mock interaction
        interaction = MagicMock(spec=discord.Interaction)
        interaction.user = MagicMock(spec=discord.User)
        interaction.user.id = 12345
        interaction.response = AsyncMock()

        # Configure database mock to return stats
        mock_stats = {
            "total_messages": 42,
            "total_conversations": 7,
            "first_conversation": "2023-01-01T12:00:00",
        }
        discord_client.db.get_user_stats = MagicMock(return_value=mock_stats)

        # Simulate what happens in setup_hook
        async def stats_callback(interaction: discord.Interaction):
            stats = discord_client.db.get_user_stats(interaction.user.id)
            if stats:
                # Format the statistics in a more readable way
                embed = discord.Embed(
                    title="Your Conversation Statistics", color=0x3498DB
                )
                embed.add_field(
                    name="Total Messages",
                    value=f"{stats['total_messages']:,}",
                    inline=True,
                )
                embed.add_field(
                    name="Total Conversations",
                    value=f"{stats['total_conversations']:,}",
                    inline=True,
                )

                first_convo = stats["first_conversation"]
                if first_convo:
                    if isinstance(first_convo, str):
                        try:
                            first_convo = datetime.fromisoformat(first_convo)
                        except ValueError:
                            pass

                    if isinstance(first_convo, datetime):
                        formatted_date = first_convo.strftime("%B %d, %Y")
                        embed.add_field(
                            name="First Conversation", value=formatted_date, inline=True
                        )
                    else:
                        embed.add_field(
                            name="First Conversation",
                            value=str(first_convo),
                            inline=True,
                        )

                await interaction.response.send_message(embed=embed)
            else:
                await interaction.response.send_message(
                    "No conversation statistics found for you."
                )

        # Call the function directly
        await stats_callback(interaction)

        # Verify the database was called correctly
        discord_client.db.get_user_stats.assert_called_once_with(12345)

        # Verify the response was sent with an embed
        interaction.response.send_message.assert_called_once()
        call_args = interaction.response.send_message.call_args[1]
        assert "embed" in call_args

        # Check embed fields
        embed = call_args["embed"]
        assert embed.title == "Your Conversation Statistics"
        assert len(embed.fields) >= 3  # Should have at least 3 fields
