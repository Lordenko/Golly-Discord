import disnake
from disnake.ext import commands
import random

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="ping", description="pong")
    async def hello(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message('pong!', ephemeral=True)

    @commands.slash_command(name="send")
    @commands.has_permissions(administrator=True)
    async def hello(self,
                    inter: disnake.ApplicationCommandInteraction,
                    message: str = commands.Param(description="Enter a message to send")):

        await inter.response.send_message(message)
        await inter.delete_original_response()

    @commands.slash_command(name='reload_cogs', description='Перезапустити всі slashcommands та events')
    @commands.has_permissions(administrator=True)
    async def reload_cogs(self, inter: disnake.ApplicationCommandInteraction):
        reloaded = []
        for ext in list(self.bot.extensions.keys()):
            try:
                self.bot.reload_extension(ext)
                reloaded.append(ext)
            except Exception as e:
                await inter.response.send_message(f"❌ Помилка в `{ext}`: `{e}`", ephemeral=True)
                return

        await inter.response.send_message(f"✅ Перезавантажено коги: {', '.join(reloaded)}", ephemeral=True)

def setup(bot):
    bot.add_cog(CommandsCog(bot))
