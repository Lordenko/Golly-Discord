import disnake
from disnake.ext import commands
import random

class CommandsCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="ping")
    async def hello(self, inter: disnake.ApplicationCommandInteraction):
        await inter.response.send_message('pong!', ephemeral=True)

    @commands.slash_command(name="compliment")
    async def compliment(self, inter: disnake.ApplicationCommandInteraction):
        compliments = [
            "Ти випромінюєш неймовірну енергію! ⚡",
            "Твоя усмішка робить цей світ яскравішим! 😊",
            "Ти розумний(а) і талановитий(а)! 🧠✨",
            "Твоя доброта надихає! 💖",
            "Ти – справжній майстер своєї справи! 🔥",
            "У тебе прекрасне почуття гумору! 😆",
            "Твоя підтримка безцінна! 🙌",
            "Ти робиш світ кращим! 🌍💫",
            "Твоя харизма захоплює! ✨",
            "З тобою завжди цікаво говорити! 🗣️",
            "Ти приносиш радість людям навколо! 😍",
            "Твоя впевненість – це справжня суперсила! 💪",
            "Ти маєш чудову уяву! 🎨",
            "Ти неймовірно стильний(а)! 😎",
            "Твій ентузіазм заразний! 🤩",
            "Ти завжди знаходиш правильні слова! 📝",
            "З тобою легко і приємно спілкуватися! 🫶",
            "Твоя доброзичливість – це дар! 🎁",
            "Ти приносиш світло в життя інших! 🌞",
            "Ти справжній(я) лідер(ка)! 👑",
            "Ти наповнюєш цей світ гармонією! 🎶",
            "Твої ідеї – просто геніальні! 💡",
            "Ти завжди знаходиш вихід із ситуації! 🚀",
            "Ти приклад для наслідування! 🌟",
            "Твоє серце сповнене тепла! ❤️",
            "Ти – справжній професіонал(ка)! 🎯",
            "Ти маєш неймовірну силу волі! 🏋️",
            "Твоя чуйність робить цей світ кращим! 🤗",
            "Ти унікальний(а) і особливий(а)! 💎",
            "Просто знай: ти – супер! 🦸‍♂️"
        ]

        await inter.response.send_message(random.choice(compliments))

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
