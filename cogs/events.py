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
        self.history = {}
        self.data_file = "activity_data.json"
        # Структура даних: ключ – id користувача (рядок), значення – словник з активністю
        self.activity_data = {}
        # Для відстеження часу приєднання до голосових каналів
        self.voice_start = {}
        # Для збереження щоденної активності (не зберігається у файл, лише в оперативці)
        self.daily_activity = {}
        self.load_data()

        # Запуск задач: скидання даних та періодичне збереження
        self.reset_daily.start()
        self.reset_monthly.start()
        self.save_data_loop.start()

    def load_data(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, "r", encoding="utf-8") as f:
                self.activity_data = json.load(f)
        else:
            self.activity_data = {}

    def save_data(self):
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.activity_data, f, indent=4)

    @tasks.loop(minutes=1)
    async def save_data_loop(self):
        self.save_data()

    def cog_unload(self):
        self.reset_daily.cancel()
        self.reset_monthly.cancel()
        self.save_data_loop.cancel()
        self.save_data()

    @tasks.loop(hours=24)
    async def reset_daily(self):
        for key, data in self.activity_data.items():
            data['today'] = 0

    @tasks.loop(hours=24)
    async def reset_monthly(self):
        now = datetime.utcnow()
        if now.day == 1:
            for key, data in self.activity_data.items():
                data['month'] = 0

    @reset_daily.before_loop
    async def before_reset_daily(self):
        now = datetime.utcnow()
        target = datetime.combine(now.date(), time(0, 0)) + timedelta(days=1)
        sleep_time = (target - now).total_seconds()
        await asyncio.sleep(sleep_time)

    @reset_monthly.before_loop
    async def before_reset_monthly(self):
        now = datetime.utcnow()
        if now.month == 12:
            target = datetime(now.year + 1, 1, 1)
        else:
            target = datetime(now.year, now.month + 1, 1)
        sleep_time = (target - now).total_seconds()
        await asyncio.sleep(sleep_time)



    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # Специфічна обробка для певного користувача
        if member.id == 366581917522591744:
            if not before.mute and after.mute:
                print(f"{member.display_name} був зам'ючений")
                await member.edit(mute=False)
            if not before.deaf and after.deaf:
                print(f"{member.display_name} був заглушений")
                await member.edit(deafen=False)

        now = datetime.utcnow()
        # Відстеження зміни голосових каналів
        if before.channel != after.channel:
            # Якщо користувач виходить з каналу – рахуємо тривалість сесії
            if before.channel is not None:
                join_time = self.voice_start.pop(member.id, None)
                if join_time:
                    duration = (now - join_time).total_seconds() / 3600.0  # години
                    user_key = str(member.id)
                    data = self.activity_data.setdefault(user_key, {'today': 0, 'month': 0, 'total': 0, 'messages': 0})
                    data['today'] += duration
                    data['month'] += duration
                    data['total'] += duration

                    # Оновлення щоденної активності
                    today_str = now.date().strftime("%Y-%m-%d")
                    if user_key not in self.daily_activity:
                        self.daily_activity[user_key] = {}
                    self.daily_activity[user_key][today_str] = self.daily_activity[user_key].get(today_str, 0) + duration

            # Якщо користувач приєднується до каналу – зберігаємо час входу
            if after.channel is not None:
                self.voice_start[member.id] = now

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.system_channel
        message = f'Ласкаво просимо, {member.mention}!\n'
        no_bot_message = 'Тобі потрібно вибрати свою групу в <#1174023100392808478>'
        message = message + no_bot_message if not member.bot else message
        if channel:
            await channel.send(message)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        channel = member.guild.system_channel
        if channel:
            await channel.send(f'{member.mention} покинув нас. Сумуватимемо!')

    @commands.Cog.listener()
    async def on_message(self, message):
        # Рахування повідомлень (ігноруючи ботів)
        if not message.author.bot:
            user_key = str(message.author.id)
            data = self.activity_data.setdefault(user_key, {'today': 0, 'month': 0, 'total': 0, 'messages': 0})
            data['messages'] += 1

        connect_to_voice = True

        await knight_say(
            message=message,
            history=self.history,
            say='иди нахуй',
            path_to_file='media/извинись.ogg',
            bot=self.bot,
            connect_to_voice=connect_to_voice
        )

        await knight_say(
            message=message,
            history=self.history,
            say='женщина',
            path_to_file='media/женщина.ogg',
            bot=self.bot,
            connect_to_voice=connect_to_voice
        )

        await knight_say(
            message=message,
            history=self.history,
            say='нет',
            path_to_file='media/нет.ogg',
            bot=self.bot,
            connect_to_voice=connect_to_voice
        )

    def create_graph(self, member: disnake.Member, data: dict) -> io.BytesIO:
        """Генерує графік голосової активності та повертає зображення у вигляді BytesIO."""
        labels = ["Today", "Month", "Total"]
        values = [data.get("today", 0), data.get("month", 0), data.get("total", 0)]

        fig, ax = plt.subplots(figsize=(6, 4))
        bars = ax.bar(labels, values, color="#7289DA")  # використання кольору, що нагадує Discord
        ax.set_ylabel("Годин")
        ax.set_title(f"Голосова активність для {member.display_name}")

        # Додаємо підпис значення над кожним стовпчиком
        for bar in bars:
            height = bar.get_height()
            ax.annotate(f"{height:.2f}",
                        xy=(bar.get_x() + bar.get_width() / 2, height),
                        xytext=(0, 3),
                        textcoords="offset points",
                        ha='center', va='bottom')

        fig.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format="png")
        buf.seek(0)
        plt.close(fig)
        return buf

    @commands.user_command(name="Статистика")
    async def user_stats(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member = None):
        member = member or inter.author
        user_key = str(member.id)
        data = self.activity_data.get(user_key)
        if not data:
            await inter.response.send_message(f"Немає даних про активність для {member.display_name}.", ephemeral=True)
            return

        # Створення футуристичного графіка голосової активності
        graph_buffer = self.create_futuristic_graph(member, data)
        file = disnake.File(fp=graph_buffer, filename="graph.png")

        # Отримання кольору ролі користувача
        member_color = member.color if member.color != disnake.Color.default() else disnake.Color(0x5865F2)

        # Підготовка даних
        today_hours = data.get('today', 0)
        month_hours = data.get('month', 0)
        total_hours = data.get('total', 0)

        # Форматування часу в годинах і хвилинах
        def format_time(hours):
            hours_int = int(hours)
            minutes = int((hours - hours_int) * 60)
            return f"{hours_int} годин {minutes} хвилин"

        # Отримання рейтингу активності
        activity_rank = self.get_activity_rank(member.id)
        rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
        rank_emoji = rank_emojis.get(activity_rank, "🏆") if activity_rank <= 10 else "👤"

        embed = disnake.Embed(
            title=f"{rank_emoji} Статистика активності | {member.display_name}",
            color=member_color
        )

        # Додавання аватару користувача
        embed.set_thumbnail(url=member.display_avatar.url)

        # Голосова активність без прогрес-барів
        embed.add_field(
            name="⌛ Час в голосових каналах",
            value=(
                f"**Сьогодні:** `{format_time(today_hours)}`\n"
                f"**За місяць:** `{format_time(month_hours)}`\n"
                f"**Всього:** `{format_time(total_hours)}`\n"
            ),
            inline=False
        )

        # Текстова активність
        messages_count = data.get('messages', 0)
        embed.add_field(
            name="💬 Повідомлення",
            value=f"**Всього надіслано:** `{messages_count}` повідомлень",
            inline=False
        )

        # Інші статистичні дані (якщо є)
        if data.get('reactions', 0) > 0 or data.get('files', 0) > 0:
            embed.add_field(
                name="🔍 Додаткова статистика",
                value=(
                    f"**Реакції:** `{data.get('reactions', 0)}`\n" if data.get('reactions', 0) > 0 else ""
                                                                                                        f"**Файли:** `{data.get('files', 0)}`" if data.get(
                        'files', 0) > 0 else ""
                ),
                inline=False
            )

        embed.set_image(url="attachment://graph.png")
        embed.set_footer(text=f"ID: {member.id} • Статистика оновлюється щохвилини")

        await inter.response.send_message(embed=embed, file=file)

    @commands.slash_command(name="activity", description="Переглянути активність користувача з графіками")
    async def activity(self, inter: disnake.ApplicationCommandInteraction, member: disnake.Member = None):
        member = member or inter.author
        user_key = str(member.id)
        data = self.activity_data.get(user_key)
        if not data:
            await inter.response.send_message(f"Немає даних про активність для {member.display_name}.", ephemeral=True)
            return

        # Створення футуристичного графіка голосової активності
        graph_buffer = self.create_futuristic_graph(member, data)
        file = disnake.File(fp=graph_buffer, filename="graph.png")

        # Отримання кольору ролі користувача
        member_color = member.color if member.color != disnake.Color.default() else disnake.Color(0x5865F2)

        # Підготовка даних
        today_hours = data.get('today', 0)
        month_hours = data.get('month', 0)
        total_hours = data.get('total', 0)

        # Форматування часу в годинах і хвилинах
        def format_time(hours):
            hours_int = int(hours)
            minutes = int((hours - hours_int) * 60)
            return f"{hours_int} годин {minutes} хвилин"

        # Отримання рейтингу активності
        activity_rank = self.get_activity_rank(member.id)
        rank_emojis = {1: "🥇", 2: "🥈", 3: "🥉"}
        rank_emoji = rank_emojis.get(activity_rank, "🏆") if activity_rank <= 10 else "👤"

        embed = disnake.Embed(
            title=f"{rank_emoji} Статистика активності | {member.display_name}",
            color=member_color
        )

        # Додавання аватару користувача
        embed.set_thumbnail(url=member.display_avatar.url)

        # Голосова активність без прогрес-барів
        embed.add_field(
            name="⌛ Час в голосових каналах",
            value=(
                f"**Сьогодні:** `{format_time(today_hours)}`\n"
                f"**За місяць:** `{format_time(month_hours)}`\n"
                f"**Всього:** `{format_time(total_hours)}`\n"
            ),
            inline=False
        )

        # Текстова активність
        messages_count = data.get('messages', 0)
        embed.add_field(
            name="💬 Повідомлення",
            value=f"**Всього надіслано:** `{messages_count}` повідомлень",
            inline=False
        )

        # Інші статистичні дані (якщо є)
        if data.get('reactions', 0) > 0 or data.get('files', 0) > 0:
            embed.add_field(
                name="🔍 Додаткова статистика",
                value=(
                    f"**Реакції:** `{data.get('reactions', 0)}`\n" if data.get('reactions', 0) > 0 else ""
                    f"**Файли:** `{data.get('files', 0)}`" if data.get('files', 0) > 0 else ""
                ),
                inline=False
            )

        embed.set_image(url="attachment://graph.png")
        embed.set_footer(text=f"ID: {member.id} • Статистика оновлюється щохвилини")

        await inter.response.send_message(embed=embed, file=file)

    def create_futuristic_graph(self, member, data):
        """Створює покращений футуристичний графік активності користувача з реальними даними"""
        import io
        import matplotlib.pyplot as plt
        import matplotlib.patheffects as path_effects
        from matplotlib.dates import DateFormatter
        import matplotlib.dates as mdates
        from datetime import datetime, timedelta
        import numpy as np
        from matplotlib.colors import LinearSegmentedColormap
        from matplotlib.collections import LineCollection

        # Отримуємо останні 7 днів
        end_date = datetime.utcnow().date()
        dates = [end_date - timedelta(days=i) for i in range(6, -1, -1)]
        date_strs = [d.strftime("%Y-%m-%d") for d in dates]

        user_key = str(member.id)
        if user_key not in self.daily_activity:
            self.daily_activity[user_key] = {}

        # Оновлюємо дані за сьогодні: беремо максимум між накопиченим у daily_activity та даними з activity_data
        today_str = end_date.strftime("%Y-%m-%d")
        current_day_activity = data.get('today', 0)
        self.daily_activity[user_key][today_str] = max(self.daily_activity[user_key].get(today_str, 0), current_day_activity)

        # Формуємо значення для графіка по кожному дню
        values = [self.daily_activity[user_key].get(date_str, 0) for date_str in date_strs]

        # Якщо всі значення рівні нулю, задаємо мінімальне значення для візуалізації
        if all(v == 0 for v in values):
            values = [0.0001] * 7

        plt.style.use('dark_background')
        fig = plt.figure(figsize=(12, 8), dpi=150)
        ax = fig.add_subplot(111)

        # Визначення кольору користувача
        r, g, b = member.color.r / 255, member.color.g / 255, member.color.b / 255
        if member.color == disnake.Color.default():
            primary_color = (0.4, 0.2, 0.8)  # Фіолетовий для дефолтного кольору
        else:
            primary_color = (r, g, b)

        # Створюємо неоновий градієнт
        neon_cmap = LinearSegmentedColormap.from_list(
            'neon',
            [(0, (0.1, 0.1, 0.3)),
             (0.5, primary_color),
             (1, (1.0, 1.0, 1.0))]
        )

        fig.patch.set_facecolor('#000000')
        ax.set_facecolor('#070714')
        ax.grid(True, linestyle='-', alpha=0.2, color='#ffffff')
        for y in ax.get_yticks():
            ax.axhline(y=y, color='#3030a0', alpha=0.25, linestyle='-', linewidth=1)

        # Конвертуємо рядки дат у datetime для побудови графіка
        plot_dates = [datetime.strptime(date_str, "%Y-%m-%d") for date_str in date_strs]
        numeric_dates = mdates.date2num(plot_dates)
        points = np.array([numeric_dates, values]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        norm = plt.Normalize(0, len(segments) - 1)

        # Побудова основної кривої з перемінною шириною
        lc = LineCollection(segments, cmap=neon_cmap, norm=norm, linewidth=6, alpha=0.9)
        lc.set_array(np.arange(len(segments)))
        ax.add_collection(lc)

        glow_line, = ax.plot(plot_dates, values, color=primary_color, linewidth=2, alpha=0.7)
        glow_line.set_path_effects([
            path_effects.SimpleLineShadow(offset=(0, 0), shadow_color=primary_color, alpha=0.8, rho=8),
            path_effects.SimpleLineShadow(offset=(0, 0), shadow_color='white', alpha=0.4, rho=12),
            path_effects.Normal()
        ])

        scatter = ax.scatter(plot_dates, values, s=150, color='white', alpha=1.0, zorder=5,
                             edgecolor=primary_color, linewidth=2.5)
        scatter.set_path_effects([
            path_effects.SimpleLineShadow(offset=(0, 0), shadow_color=primary_color, alpha=0.8, rho=8),
            path_effects.Normal()
        ])

        ax.fill_between(plot_dates, values, color=primary_color, alpha=0.3)
        ax.xaxis.set_major_formatter(plt.NullFormatter())
        ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))

        def hours_formatter(x, pos):
            hours_int = int(x)
            minutes = int((x - hours_int) * 60)
            if hours_int == 0:
                return f'{minutes} хв'
            return f'{hours_int} год {minutes} хв'

        ax.yaxis.set_major_formatter(plt.FuncFormatter(hours_formatter))
        ax.tick_params(axis='y', labelsize=14, colors='white', pad=10)

        y_max = max(max(values) * 1.3, 0.2)
        y_min = 0
        ax.set_ylim(y_min, y_max)

        def neon_text(text, x, y, **kwargs):
            text_obj = ax.text(x, y, text, **kwargs)
            text_obj.set_path_effects([
                path_effects.Stroke(linewidth=4, foreground=primary_color, alpha=0.7),
                path_effects.Normal()
            ])
            return text_obj

        neon_text(f'Активність {member.display_name}', 0.5, 1.05,
                  fontsize=22, fontweight='bold', color='white', alpha=0.95,
                  transform=ax.transAxes, ha='center')

        for spine in ax.spines.values():
            spine.set_visible(False)

        for i, (d, v) in enumerate(zip(plot_dates, values)):
            hours = int(v)
            minutes = int((v - hours) * 60)
            time_str = f'{hours} год {minutes} хв' if hours > 0 else f'{minutes} хв'
            text = ax.annotate(time_str, (d, v), textcoords="offset points",
                               xytext=(0, 25), ha='center', fontweight='bold', fontsize=14,
                               color='white', alpha=0.95)
            text.set_path_effects([
                path_effects.Stroke(linewidth=3, foreground=primary_color, alpha=0.7),
                path_effects.Normal()
            ])

        bottom_line = ax.axhline(y=y_min, color=primary_color, alpha=0.7, linewidth=2.5)
        bottom_line.set_path_effects([
            path_effects.SimpleLineShadow(offset=(0, 0), shadow_color=primary_color, alpha=0.7, rho=8),
            path_effects.Normal()
        ])

        weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Нд']
        for i, d in enumerate(plot_dates):
            weekday = weekdays[d.weekday()]
            ax.text(d, -y_max * 0.05, weekday,
                    ha='center', fontsize=16, color='white', alpha=1.0,
                    fontweight='bold')

        plt.subplots_adjust(bottom=0.15)
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=150, facecolor='#000000', edgecolor='none', bbox_inches='tight')
        buffer.seek(0)
        plt.close()
        return buffer

    def get_activity_rank(self, user_id):
        """Повертає рейтинг користувача серед усіх користувачів за активністю"""
        all_users = []
        for uid, data in self.activity_data.items():
            all_users.append((uid, data.get('total', 0)))
        all_users.sort(key=lambda x: x[1], reverse=True)
        for i, (uid, _) in enumerate(all_users):
            if uid == str(user_id):
                return i + 1
        return len(all_users) + 1


def setup(bot):
    bot.add_cog(EventsCog(bot))
