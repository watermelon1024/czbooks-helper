"""
Discord-related utilities functions for the bot.
"""

import discord
from discord.ext import commands


def get_user_name(user: discord.User) -> str:
    """
    Get the name of a user.

    :param user: The user to get the name of.
    :type user: discord.User

    :return: The name of the user.
    :rtype: str
    """
    if user.discriminator == "0":
        return f"@{user.name}"
    return f"{user.name}#{user.discriminator}"


async def get_or_fetch_message_from_reference(
    message: discord.Message | discord.MessageReference,
) -> discord.Message:
    """
    Get the message from a referenced message.

    :param message: The message referenced to get the message from.
    :type message: Union[discord.Message, discord.MessageReference]

    :return: The message.
    :rtype: discord.Message
    """
    return message.reference.cached_message or await message.channel.fetch_message(
        message.reference.message_id
    )


def context_info(ctx: discord.ApplicationContext | discord.Interaction | commands.Context) -> str:
    """
    Get the context info of a context.

    :param ctx: The context to get the context info of.
    :type ctx: discord.ApplicationContext | discord.Interaction | commands.Context

    :return: The context info.
    :rtype: str
    """
    usr = ctx.user if isinstance(ctx, discord.Interaction) else ctx.author
    return f"[{ctx.guild.name} #{ctx.channel.name}] {get_user_name(usr)}"
