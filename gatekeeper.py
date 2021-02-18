import discord
import collections
from discord.ext import commands

from . import config

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(msg):
    # If it's a bot or outside of the pre-ban list
    if msg.author.bot or str(msg.channel.id) != "811585504214646804":
        return

    content = msg.content
    parsed_content = content.split(":")

    try:
        ban_id = int(parsed_content[0])
    except ValueError:
        msg.channel.send("Invalid format. Must be `<USERID>:<REASON>` without brackets")
        return
    
    guilds = await client.guilds()

    for guild in guilds:
        ctx = get_context(guild)
        converter = commands.UserConverter()
        user = converter.convert(str(ban_id))
        try:
            await guild.ban(user, reason=parsed_content[1])
        except:
            print(f"Could not ban from {guild.name}")

    await msg.add_reaction("👍")
    

async def gen_context(guild):
    """
    Generates a fake context for the converter
    """
    ctx = collections.namedtuple('Context', 'bot _state', module=commands.Context)
    ctx.bot = client
    ctx._state = await guild.text_channels[0].fetch_message(guild.text_channels[0].last_message_id)

    return ctx

client.run(config.discord_token)
