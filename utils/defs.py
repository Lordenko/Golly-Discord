import asyncio
import disnake
from datetime import datetime, timedelta
from disnake import FFmpegPCMAudio

def load_cogs(bot, *initial_extensions):
    for extension in initial_extensions:
        bot.load_extension(extension)

async def vc_disconnect(vc):
    await asyncio.sleep(3)
    await vc.disconnect()


async def knight_say(message, history, say, path_to_file, bot, connect_to_voice = False):
    COOLDOWN = 5 # minutes

    if message.author.bot:
        return

    voice = disnake.File(path_to_file)

    if say in message.content.lower():
        if connect_to_voice:
            now = datetime.now()

            if message.author.id in history and now - history[message.author.id] < timedelta(minutes=COOLDOWN):
                await message.reply(f'Спробуй через декілька хвилин :)')
            else:
                if connect_to_voice and message.author.voice and message.author.voice.channel:
                    vc = await message.author.voice.channel.connect()
                    media = FFmpegPCMAudio(path_to_file)
                    vc.play(media, after=lambda _: bot.loop.create_task(vc_disconnect(vc)))
                else:
                    await message.reply(file=voice)

                history[message.author.id] = now
        
