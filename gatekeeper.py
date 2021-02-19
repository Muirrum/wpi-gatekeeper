import discord
import collections
from discord.ext import commands

import config

intents = discord.Intents.default()
client = discord.Client(intents=intents)


# Mapping of guild IDs to guild log channels

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")


@client.event
async def on_message(msg):
    # If it's a bot or outside of the pre-ban list or not an admin of the server
    print(msg.author.guild_permissions.administrator)
    if msg.author.bot or str(msg.channel.id) != "811585504214646804" or not msg.author.guild_permissions.administrator:
        return

    content = msg.content
    parsed_content = content.split(":")

    try:
        ban_id = int(parsed_content[0])
    except ValueError:
        await msg.channel.send("Invalid format. Must be `<USERID>:<REASON>` without brackets")
        return

    try:
        user = await client.fetch_user(ban_id)
    except discord.NotFound:
        await msg.channel.send(f"Did not find a user with the ID {ban_id}")
        return

    errors = ""
    for guild in client.guilds:
        try:
            # Ban the user and purge messages up to 7 days ago
            await guild.ban(user, delete_message_days=7, reason=parsed_content[1], )
            result = f"Banned {user.mention} from {guild.name}"
        except discord.Forbidden:
            result = f"Missing permissions to ban {user.mention} from {guild.name}\n"
            errors += result
        finally:
            if str(guild.id) in config.guild_log_channels:
                log_channel = guild.get_channel(config.guild_log_channels[str(guild.id)])
                try:
                    await log_channel.send(result)
                except discord.Forbidden:
                    errors += "Missing permissions to send logging message in " + guild.name + "\n"

    if len(errors) > 0:
        await msg.channel.send(f"Completed pre-ban of {user.mention} from {len(client.guilds)} guilds\n\n__Errors__\n" + errors)
    else:
        await msg.channel.send(f"Completed pre-ban of {user.mention} from {len(client.guilds)} guilds")


client.run(config.discord_token)
