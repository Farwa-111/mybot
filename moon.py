import discord
from discord.ext import commands

# التوكن حقك جاهز هنا يا يوسف
TOKEN = "MTQ5MzMwNDIyMjQxMjcwNTkwMg.GxM45q.Rye_g-drO3Jkx6fuv3Z890TGwO0FlqVB9Tidw8"

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f'MOON is Online: {bot.user.name}')

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
        await ctx.send(f'تم الإرسال إلى {count} عضو.')

bot.run(TOKEN)
