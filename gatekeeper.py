from discord.ext import commands

import traceback
import discord
import json
import sys

# Creating a bot with the prefix g! and default intents
client = commands.Bot(
    command_prefix="g!",
    case_insensitive=True,
    intents=discord.Intents.default()
)

# Load the settings
with open("settings.json", "r+") as settings_file:
    settings = json.loads(settings_file.read())


def set_default_settings(guild: discord.Guild):
    """
    Sets the default settings for a guild

    :param guild: Guild to set default settings for
    """
    global settings

    settings["guilds"][str(guild.id)] = {
        "opt": 0,  # Opt in level: 0 = Only alerts to logging, 1 = Bans from trusted users, 2 = Bans from all users
        "trusted": [],  # Users trusted to ban for your server
        "logging": None  # Logging channel for bans
    }

    save_settings()


def save_settings():
    """
    Saves the current settings to the json file
    """
    global settings

    with open("settings.json", "r+") as settings_file:
        settings_file.truncate(0)
        settings_file.seek(0)
        json.dump(settings, settings_file, indent=4)


def administrator_perms(ctx):
    """
    Checks for administrator permissions in a server

    :param ctx: Context object
    :return: True / False if check passes
    """
    return ctx.message.author.guild_permissions.administrator


def ban_channel(ctx):
    """
    Checks if a command was used in the ban channel for the moderator server

    :param ctx: Context object
    :return: True / False if check passes
    """
    return ctx.channel.id == 811585504214646804


@client.event
async def on_ready():
    global settings

    print(f"Logged in as {client.user}")  # Login confirmation

    # Add default settings for new guilds
    for guild in client.guilds:
        if str(guild.id) not in settings["guilds"]:
            set_default_settings(guild)


@client.event
async def on_guild_join(guild):
    """
    Creates default settings for new guilds

    :param guild: Guild that the bot joined
    """
    global settings

    # If guild doesn't already have settings, add them
    if str(guild.id) not in settings:
        set_default_settings(guild)


@client.command(name="ban")
@commands.check(ban_channel)
@commands.guild_only()
async def ban(ctx, user: discord.User, *, reason: str):
    """
    Bans a user in the connected servers that have opted in

    :param ctx: Context object
    :param user: User to ban
    :param reason: String reason for the ban
    """
    global settings

    message = f"{ctx.author.name}#{ctx.author.discriminator} has banned {user.name}#{user.discriminator} ({user.id}) for {reason}."
    errors = ""

    for guild in client.guilds:
        logging_channel = guild.get_channel(settings["guilds"][str(guild.id)]["logging"])

        # If the guild has not opted in
        if settings["guilds"][str(guild.id)]["opt"] == 0:
            if logging_channel is not None:
                try:
                    await logging_channel.send(
                        message + " **This user has not been banned here since you have not opted into bans.**"
                    )
                except discord.Forbidden:
                    errors += f"Missing permissions to send logging message in {guild.name}\n"

        # If the guild has opted in for trusted users
        elif settings["guilds"][str(guild.id)]["opt"] == 1:
            # If the user is trusted - ban
            if ctx.author.id in settings["guilds"][str(guild.id)]["trusted"]:
                try:
                    await guild.ban(user, delete_message_days=7, reason=reason)
                except discord.Forbidden:
                    errors += f"Missing ban permissions in {guild.name}\n"
                    continue

                trusted = f" **This user was banned here since " \
                          f"{ctx.author.name}#{ctx.author.discriminator} is trusted"
            else:
                trusted = f" **This user was not banned here since " \
                          f"{ctx.author.name}#{ctx.author.discriminator} is not trusted"

            if logging_channel is not None:
                try:
                    await logging_channel.send(
                        message + trusted
                    )
                except discord.Forbidden:
                    errors += f"Missing permissions to send logging message in {guild.name}\n"

        # If the guild has opted in for all bans
        else:
            try:
                await guild.ban(user, delete_message_days=7, reason=reason)
            except discord.Forbidden:
                errors += f"Missing ban permissions in {guild.name}\n"
                continue

            if logging_channel is not None:
                try:
                    await logging_channel.send(
                        message + " **This user has been banned here**"
                    )
                except discord.Forbidden:
                    errors += f"Missing permissions to send logging message in {guild.name}\n"

    await ctx.message.add_reaction("👍")

    if len(errors) > 0:  # If there are permission errors, send them in the channel
        await ctx.send(errors)


@client.command(name="pardon")
@commands.check(ban_channel)
@commands.guild_only()
async def pardon(ctx, user: discord.User, *, reason: str):
    """
    Pardons a user in the connected servers that have opted in

    :param ctx: Context object
    :param user: User to pardon
    :param reason: String reason to pardon
    """
    global settings

    message = f"{ctx.author.name}#{ctx.author.discriminator} has pardoned {user.name}#{user.discriminator} ({user.id}) for {reason}."
    errors = ""

    for guild in client.guilds:
        logging_channel = guild.get_channel(settings["guilds"][str(guild.id)]["logging"])

        # If the guild has not opted in
        if settings["guilds"][str(guild.id)]["opt"] == 0:
            if logging_channel is not None:
                try:
                    await logging_channel.send(
                        message + " **This user has not been pardoned here since you have not opted into bans.**"
                    )
                except discord.Forbidden:
                    errors += f"Missing permissions to send logging message in {guild.name}\n"

        # If the guild has opted in for trusted users
        elif settings["guilds"][str(guild.id)]["opt"] == 1:
            # If the user is trusted - pardon
            if ctx.author.id in settings["guilds"][str(guild.id)]["trusted"]:
                try:
                    await guild.unban(user, reason=reason)
                except discord.Forbidden:
                    errors += f"Missing pardon permissions in {guild.name}\n"
                    continue

                trusted = f" **This user was pardoned here since " \
                          f"{ctx.author.name}#{ctx.author.discriminator} is trusted"
            else:
                trusted = f" **This user was not pardoned here since " \
                          f"{ctx.author.name}#{ctx.author.discriminator} is not trusted"

            if logging_channel is not None:
                try:
                    await logging_channel.send(
                        message + trusted
                    )
                except discord.Forbidden:
                    errors += f"Missing permissions to send logging message in {guild.name}\n"

        # If the guild has opted in for all pardons
        else:
            try:
                await guild.unban(user, reason=reason)
            except discord.Forbidden:
                errors += f"Missing pardon permissions in {guild.name}\n"
                continue

            if logging_channel is not None:
                try:
                    await logging_channel.send(
                        message + " **This user has been pardoned here**"
                    )
                except discord.Forbidden:
                    errors += f"Missing permissions to send logging message in {guild.name}\n"

    await ctx.message.add_reaction("👍")

    if len(errors) > 0:  # If there are permission errors - send them in the channel
        await ctx.send(errors)


@client.command(name="logging")
@commands.check(administrator_perms)
@commands.guild_only()
async def set_logging(ctx, channel: discord.TextChannel):
    """
    Sets the logging channel for a server

    :param ctx: Context object
    :param channel: Channel to send logging messages
    """
    global settings

    settings["guilds"][str(ctx.guild.id)]["logging"] = channel.id
    save_settings()
    await ctx.send(f"Successfully set logging channel to {channel}")


@client.command(name="opt")
@commands.check(administrator_perms)
@commands.guild_only()
async def set_opt_in_level(ctx, level: int):
    """
    Sets the opt in level for a server

    :param ctx: Context object
    :param level: Integer 1-3
        - 1 = Only logging - no bans
        - 2 = Bans from trusted users only
        - 3 = Bans from all users in the moderator server
    """
    global settings

    # If the opt in level is out of range
    if not 0 < level < 4:
        await ctx.send(
            "Not a valid opt in level. Levels are:\n"
            "```\n"
            "1. Only logging - no bans\n"
            "2. Bans from trusted users only\n"
            "3. Bans from all users in the moderator server\n"
            "```"
        )
        return

    settings["guilds"][str(ctx.guild.id)]["opt"] = level - 1

    save_settings()
    await ctx.send(f"Successfully set opt in level to {level}")


@client.command(name="trust")
@commands.check(administrator_perms)
@commands.guild_only()
async def set_trusted(ctx, *users: discord.User):
    """
    Adds users to the trusted list

    :param ctx: Context object
    :param users: Users to add
    """
    global settings

    added_users = ""
    for user in users:
        if user.id not in settings["guilds"][str(ctx.guild.id)]["trusted"]:
            settings["guilds"][str(ctx.guild.id)]["trusted"].append(user.id)
            added_users += f"{user.name}#{user.discriminator}, "

    if added_users == "":
        await ctx.send("No one new to trust. Have you already marked these people as trusted?")
    else:
        save_settings()
        await ctx.send(f"Added {added_users[:-2]} to trusted users")


@client.command(name="untrust")
@commands.check(administrator_perms)
@commands.guild_only()
async def remove_trusted(ctx, *users: discord.User):
    """
    Removes a user from the trusted list

    :param ctx: Context object
    :param users: Users to remove
    """
    global settings

    removed_users = ""
    invalid_users = ""

    for user in users:
        if user.id in settings["guilds"][str(ctx.guild.id)]["trusted"]:
            settings["guilds"][str(ctx.guild.id)]["trusted"].remove(user.id)
            removed_users += f"{user.name}#{user.discriminator}, "
        else:
            invalid_users += f"{user.name}#{user.discriminator}, "

    message = f"Removed {removed_users[:-2]} from trusted users"
    if len(invalid_users) > 0:
        message += f"\n{invalid_users[:-2]} were not trusted users"

    save_settings()
    await ctx.send(message)


@client.command()
@commands.check(administrator_perms)
@commands.guild_only()
async def status(ctx):
    """
    Checks to see if the bot has permissions to ban and send logging messages in the server and sends current opt in
    and trusted status

    :param ctx: Context object
    """
    global settings

    message = ""

    # Check ban perms
    if not ctx.guild.me.guild_permissions.ban_members:
        message += ":warning: I do not have permissions to ban members\n"

    # Check logging channel perms
    if settings["guilds"][str(ctx.guild.id)]["logging"] is not None:
        logging_channel = ctx.guild.get_channel(settings["guilds"][str(ctx.guild.id)]["logging"])

        if logging_channel is None:
            message += ":warning: Could not get the logging channel\n"
        elif not logging_channel.permissions_for(ctx.guild.me).send_messages:
            message += f":warning: I do not have permissions to send messages in <#{logging_channel.id}>\n"
        else:
            message += f"- Logging channel is <#{logging_channel.id}>\n"
    else:
        message += ":warning: You do not have a logging channel setup.\n"

    opt_level = settings["guilds"][str(ctx.guild.id)]["opt"]
    if opt_level == 0:
        message += "- Opt in level 1, users in the moderator server cannot ban here"
    elif opt_level == 1:
        message += "- Opt in level 2, trusted users in the moderator server can ban here\n\n__Trusted Users__\n"
        for user_id in settings["guilds"][str(ctx.guild.id)]["trusted"]:
            user = await client.fetch_user(user_id)

            message += f"{user.name}#{user.discriminator}\n"

    elif opt_level == 2:
        message += "- Opt in level 3, all users in the moderator server can ban here"

    await ctx.send(message)


@client.event
async def on_command_error(ctx, error):
    """
    Default error handling for the bot

    :param ctx: Context object
    :param error: Error
    """
    if isinstance(error, commands.CheckFailure) or isinstance(error, commands.MissingPermissions):
        print(f"!ERROR! ({ctx.author.id}) did not have permissions for {ctx.command.name} command")
    elif isinstance(error, commands.BadArgument):
        argument = list(ctx.command.clean_params)[len(ctx.args[2:] if ctx.command.cog else ctx.args[1:])]
        await ctx.send(f"Did not recognize the {argument} argument")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"{ctx.command.name} is missing arguments")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send("Bot is missing permissions.")
    else:
        print('Ignoring exception in command {}:'.format(ctx.command), file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)

# Run the bot
client.run(settings["discord_token"])
