import discord
from discord.ext import commands
import os

# إعدادات البوت
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.command()
async def sendall(ctx, *, message):
    if ctx.author.guild_permissions.administrator:
        count = 0
        for member in ctx.guild.members:
            if not member.bot:
                try:
                    await member.send(message)
                    count += 1
                except:
                    pass
        await ctx.send(f'تم إرسال الرسالة إلى {count} عضو.')
    else:
        await ctx.send('هذا الأمر للمشرفين فقط.')

token = os.environ.get('DISCORD_TOKEN')
bot.run(token)
