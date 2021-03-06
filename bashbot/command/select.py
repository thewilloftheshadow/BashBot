from discord.ext import commands

from bashbot.command import has_permission
from bashbot.core.exceptions import TerminalNotFoundException
from bashbot.terminal.sessions import sessions


class SelectCommand(commands.Cog):
    @commands.command(
        name='.select',
        aliases=['.s'],
        description='Sets terminal as selected',
        usage='[name]'
    )
    @has_permission('session.select')
    async def select(self, ctx, name):
        terminal = sessions().by_name(name)
        if not terminal:
            raise TerminalNotFoundException()

        sessions().select(ctx.message.channel, terminal)
        await ctx.send(f"`Selected terminal #{name}`")
