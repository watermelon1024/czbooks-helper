"""
Cog module for the command logger.
"""

from typing import Union

import discord
from discord.ext import commands

from bot import BaseCog, Bot
from utils.discord import get_user_name


class CmdLogger(BaseCog):
    """
    The cog class for the command logger.
    """

    async def _log_command(
        self,
        ctx: Union[commands.Context, discord.ApplicationContext],
        command_type: str,
        command_args: str,
    ) -> None:
        """
        Log a command usage.
        This is an internal function and should not be called directly.

        :param ctx: The context of the command.
        :type ctx: commands.Context | discord.ApplicationContext
        :param command_type: The type of the command.
        :type command_type: str
        :param command_args: The arguments of the command.
        :type command_args: str
        """
        command_name = (
            f"{ctx.command.full_parent_name} {ctx.command.name}"
            if ctx.command.full_parent_name
            else ctx.command.name
        )
        command_args = f" - {command_args}" if command_args else ""
        msg = (
            f"[{ctx.guild.name} #{ctx.channel.name}] {get_user_name(ctx.author)}: "
            f"({command_type}-command) {command_name}{command_args}"
        )
        self.bot.logger.info(msg)


    @discord.Cog.listener()
    async def on_command(self, ctx: commands.Context) -> None:
        """
        The event that is triggered when a message command is used.
        """
        await self._log_command(ctx, "text", ", ".join(f"{k}: {v}" for k, v in ctx.kwargs))

    @discord.Cog.listener()
    async def on_application_command(self, ctx: discord.ApplicationContext) -> None:
        """
        The event that is triggered when an application command is used.
        """
        command_type = "application"
        args = ""
        match ctx.command.type:
            case 1:
                command_type = "slash"
                if (options := ctx.interaction.data.get("options")) is not None:
                    args = ", ".join(f"{option['name']}: {option['value']}" for option in options)
            case 2:
                command_type = "user"
                args = f"user: {ctx.interaction.data['target_id']}"
            case 3:
                command_type = "message"
                args = f"message: {ctx.interaction.data['target_id']}"
        await self._log_command(ctx, command_type, args)

    @discord.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError) -> None:
        """
        The event that is triggered when a message command error occurs.
        """
        if isinstance(error, (commands.CommandNotFound, commands.NotOwner)):
            return
        self.logger.exception(type(error).__name__, exc_info=error)

    @discord.Cog.listener()
    async def on_application_command_error(
        self,
        ctx: discord.ApplicationContext,
        error: discord.DiscordException,
    ) -> None:
        """
        The event that is triggered when an application command error occurs.
        """
        self.logger.exception(type(error).__name__, exc_info=error)


def setup(bot: Bot) -> None:
    """
    The setup function of the cog.
    """
    bot.add_cog(CmdLogger(bot))
