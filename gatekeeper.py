import discord

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
    if msg.author.bot or str(msg.channel.id) != "811585504214646804" or not msg.author.guild_permissions.administrator:
        return

    content = msg.content
    parsed_content = content.split(":")

    try:
        ban_id = int(parsed_content[1])
    except ValueError:
        await msg.channel.send("Invalid format. Must be `<ACTION>:<USERID>:<REASON>` without brackets")
        return

    try:
        user = await client.fetch_user(ban_id)
    except discord.NotFound:
        await msg.channel.send(f"Did not find a user with the ID {ban_id}")
        return

    errors = ""
    if parsed_content[0].lower() == "ban":
        ban = True
    elif parsed_content[0].lower() == "pardon":
        ban = False
    else:
        await msg.channel.send("Invalid action, must either be `ban` or `pardon`")
        return

    for guild in client.guilds:
        try:
            if ban:
                # Ban the user and purge messages up to 7 days ago
                await guild.ban(user, delete_message_days=7, reason=parsed_content[2])
                result = f"Banned {user.name}#{user.discriminator} ({user.id}) from {guild.name}"
            else:
                await guild.unban(user, reason=parsed_content[2])
                result = f"Pardoned {user.name}#{user.discriminator} ({user.id}) from {guild.name}"

        except discord.Forbidden:
            result = f"Missing permissions to {parsed_content[0].lower()} {user.name}#{user.discriminator} ({user.id}) from {guild.name}\n"
            errors += result
        finally:
            if str(guild.id) in config.guild_log_channels:
                log_channel = guild.get_channel(config.guild_log_channels[str(guild.id)])
                try:
                    await log_channel.send(result)
                except discord.Forbidden:
                    errors += "Missing permissions to send logging message in " + guild.name + "\n"

    if len(errors) > 0:
        await msg.channel.send(f"Completed {parsed_content[0].lower()} of {user.name}#{user.discriminator} ({user.id}) from {len(client.guilds)} guilds\n\n__Errors__\n" + errors)
    else:
        await msg.channel.send(f"Completed {parsed_content[0].lower()} of {user.name}#{user.discriminator} ({user.id}) from {len(client.guilds)} guilds")


client.run(config.discord_token)
