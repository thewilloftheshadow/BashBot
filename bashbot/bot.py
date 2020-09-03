import discord
from discord import Message, Reaction, User
from discord.abc import PrivateChannel
from discord.ext.commands import Bot, Context
from discord.utils import oauth_url

from bashbot.command.about import AboutCommand
from bashbot.command.close import CloseCommand
from bashbot.command.controls import ControlsCommand
from bashbot.command.freeze import FreezeCommand
from bashbot.command.here import HereCommand
from bashbot.command.macro import MacroCommand
from bashbot.command.open import OpenCommand
from bashbot.command.rename import RenameCommand
from bashbot.command.repeat import RepeatCommand
from bashbot.exceptions import SessionDontExistException, ArgumentFormatException
from bashbot.settings import settings
from bashbot.terminal.control import TerminalControl
from bashbot.terminal.sessions import sessions
from bashbot.terminal.terminal import TerminalState
from bashbot.utils import get_logger, parse_template, has_prefix


class BashBot(Bot):
    logger = get_logger('BashBot')
    cmd_logger = get_logger('Command')

    def __init__(self, command_prefix, **options):
        super().__init__(command_prefix, **options)
        self.add_cog(OpenCommand())
        self.add_cog(CloseCommand())
        self.add_cog(HereCommand())
        self.add_cog(FreezeCommand())
        self.add_cog(RenameCommand())
        self.add_cog(ControlsCommand())
        self.add_cog(AboutCommand())
        self.add_cog(RepeatCommand())
        self.add_cog(MacroCommand())

    async def on_ready(self):
        self.logger.info(f'Logged in as {self.user.name} ({self.user.id})')
        self.logger.info(f'You can add bot to your server via {oauth_url(self.user.id)}')

        presence = parse_template(
            settings().get("discord.presence"),
            prefix=self.command_prefix
        )
        await self.change_presence(
            status=discord.Status.online,
            activity=discord.Game(presence)
        )

    async def on_message(self, message: Message):
        if message.author.bot:
            return

        terminal = sessions().get_by_channel(message.channel)

        if self.is_invoke(message):
            await self.process_commands(message)
        elif terminal and terminal.state == TerminalState.OPEN:
            terminal.input(message.content + '\n')

            # Log message
            guild_name = message.channel.guild.name
            channel_name = message.channel.name
            author_name = message.author.name
            content = message.content

            self.cmd_logger.info(f"[{guild_name}/#{channel_name}/{terminal.name}] {author_name} typed: {content}")

    async def on_command(self, ctx: Context):
        guild_name = ctx.message.channel.guild.name
        channel_name = ctx.message.channel.name
        author_name = ctx.message.author.name
        content = ctx.message.content

        self.cmd_logger.info(f"[{guild_name}/#{channel_name}] {author_name} invoked command: {content}")

    async def on_reaction_add(self, reaction: Reaction, user: User):
        if user.bot:
            return

        terminal = sessions().get_by_message(reaction.message)
        if reaction.emoji not in terminal.controls:
            return

        control: TerminalControl = terminal.controls[reaction.emoji]
        terminal.input(control.text)

    async def on_reaction_remove(self, reaction: Reaction, user: User):
        await self.on_reaction_add(reaction, user)

    def is_invoke(self, message: Message):
        if isinstance(message.channel, PrivateChannel):
            return True

        has_mention = self.user in message.mentions
        return has_prefix(message.content) or has_mention

    async def on_command_error(self, ctx: Context, error):
        if isinstance(error, ArgumentFormatException):
            await ctx.send(error.message)

        if isinstance(error, SessionDontExistException):
            await ctx.send("You need to have open terminal to use this command")
