import asyncio
import json
import os
import io
import matplotlib.pyplot as plt
from datetime import datetime, timedelta, time

import disnake
from disnake.ext import commands, tasks
from disnake import FFmpegPCMAudio
from utils.defs import knight_say


class EventsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        guild = member.guild
        role = guild.get_role(1355333551880409200)
        await member.add_roles(role)


def setup(bot):
    bot.add_cog(EventsCog(bot))
