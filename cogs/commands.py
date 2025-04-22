from datetime import datetime

import requests
from dateutil.relativedelta import relativedelta

import disnake
from disnake.ext import commands


class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.admin_token = "BCdmIJaeaDli36UQLordenko"
        self.add_token_ip = "http://46.219.25.253:1488/add_token"
        self.get_token_time_ip = "http://46.219.25.253:1488/get_token_time"

    @commands.slash_command(name="ping", description="pong")
    async def hello(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message('pong!', ephemeral=True)

    @commands.slash_command(name="send")
    @commands.has_permissions(administrator=True)
    async def hello(self,
                    inter: disnake.ApplicationCommandInteraction,
                    message: str = commands.Param(description="Enter a message to send")):

        channel = self.bot.get_channel(inter.channel_id)
        await channel.send(message)
        await inter.response.send_message('eblan', ephemeral=True)
        await inter.delete_original_response()

    async def get_token_time(self, nickname: str, token: str):
        data = {
            "username": nickname,
            "token": token
        }

        response = requests.post(self.get_token_time_ip, json=data)

        if response.status_code == 200:
            return response.json()['expires_at']
        else:
            return None



    @commands.slash_command(name="create_token")
    @commands.has_permissions(administrator=True)
    async def create_token(self,
                           inter: disnake.ApplicationCommandInteraction,
                           nickname: str = commands.Param(description="Enter a nickname from minecraft"),
                           expires_at: int = commands.Param(description="Enter a expires time number (1 - mounth, 2 - 3 mounth, 3 - inf")):

        if expires_at == 1:
            expires_at = datetime.now() + relativedelta(months=1)
        elif expires_at == 2:
            expires_at = datetime.now() + relativedelta(months=3)
        elif expires_at == 3:
            expires_at = datetime.now() + relativedelta(years=10)
        else:
            await inter.response.send_message("Error expires_at", ephemeral=True)
            return

        data = {
            "admin_token": self.admin_token,
            "username": nickname,
            "expires_at": expires_at.replace(microsecond=0).isoformat()
        }

        response = requests.post(self.add_token_ip, json=data)

        answer = ''

        if response.status_code == 200:
            json = response.json()
            username = json['username']
            token = json['token']
            time = await self.get_token_time(username, token)

            answer = (f"Minecraft Login - `{username}`\n"
                      f"Token - `{token}`\n"
                      f"Expires at - <t:{time}:R>")
        else:
            answer = f"Error: {response.status_code}"

        await inter.response.send_message(answer, ephemeral=True)

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
