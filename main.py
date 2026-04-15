from flask import Flask
from threading import Thread

app = Flask('')

@app.route('/api/alive')
def alive():
    return "I am alive!"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# تشغيل سيرفر الإنعاش
keep_alive() 

Discord Broadcast Bot
---------------------
Command usage:
  !sendall <message>
      Sends a message to all members in the server via DM.

  !test <message>
      Sends a test DM to the command author.

  !dm <User_ID> <message>
      (Owner only) Sends a private message to a specific user by ID.

Required environment variable:
  DISCORD_TOKEN  — Your Discord bot token from the Developer Portal.

Required bot permissions:
  - Send Messages
  - Embed Links
  - Read Message History
  - Manage Messages (to delete spam/duplicate messages)

Required Privileged Intent (Discord Developer Portal → Bot):
  - Message Content Intent
"""

import os
import time
import asyncio
import logging
import discord
from discord.ext import commands
from keep_alive import keep_alive

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("broadcast-bot")

TOKEN = os.environ.get("DISCORD_TOKEN")
PREFIX = "!"

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# ─────────────────────────────────────────────
# Anti-Spam: cooldown بين الرسائل (5 ثوانٍ)
# المفتاح: (guild_id, channel_id, user_id)
# ─────────────────────────────────────────────
_last_msg_time: dict[tuple, float] = {}
COOLDOWN_SECONDS = 5

# ─────────────────────────────────────────────
# Duplicate Protection: آخر نص لكل مستخدم في كل قناة
# المفتاح: (guild_id, channel_id, user_id)
# ─────────────────────────────────────────────
_last_msg_content: dict[tuple, str] = {}

# ─────────────────────────────────────────────
# Global Command Cooldown: 5 ثوانٍ بين كل أمر وأمر للمستخدم نفسه
# ─────────────────────────────────────────────
_cmd_cooldown = commands.CooldownMapping.from_cooldown(
    1, 5, commands.BucketType.user
)


@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        await bot.process_commands(message)
        return

    key = (
        message.guild.id if message.guild else 0,
        message.channel.id,
        message.author.id,
    )
    now = time.monotonic()

    # 1) فحص التكرار (نفس النص)
    last_content = _last_msg_content.get(key, "")
    if message.content and message.content.strip() == last_content:
        try:
            await message.delete()
        except discord.Forbidden:
            pass
        return  # تجاهل صامت بدون رد

    # 2) فحص الـ cooldown (5 ثوانٍ بين الرسائل)
    last_time = _last_msg_time.get(key, 0)
    if now - last_time < COOLDOWN_SECONDS:
        remaining = COOLDOWN_SECONDS - (now - last_time)
        try:
            await message.delete()
            await message.channel.send(
                f"⏳ {message.author.mention} انتظر {remaining:.1f} ثانية قبل الإرسال مجدداً.",
                delete_after=3,
            )
        except discord.Forbidden:
            pass
        return

    # تحديث الـ state
    _last_msg_content[key] = message.content.strip() if message.content else ""
    _last_msg_time[key] = now

    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    # تجاهل صامت لأخطاء الـ cooldown على الأوامر
    if isinstance(error, commands.CommandOnCooldown):
        return
    # تجاهل الأوامر غير الموجودة
    if isinstance(error, commands.CommandNotFound):
        return
    raise error


@bot.before_invoke
async def global_command_cooldown(ctx):
    """يمنع تكرار نفس الأمر بسرعة من نفس المستخدم"""
    bucket = _cmd_cooldown.get_bucket(ctx.message)
    retry_after = bucket.update_rate_limit()
    if retry_after:
        raise commands.CommandOnCooldown(bucket, retry_after, commands.BucketType.user)


# ─────────────────────────────────────────────
# أوامر السلاش
# ─────────────────────────────────────────────
@bot.tree.command(name="hello", description="Say hello from Moon Store!")
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message("Hello from Moon Store! Your bot is active.")


@bot.event
async def on_ready():
    try:
        synced = await bot.tree.sync()
        log.info(f"Synced {len(synced)} slash command(s)")
    except Exception as e:
        log.error(f"Failed to sync commands: {e}")

    log.info(f"Logged in as {bot.user} (ID: {bot.user.id})")


# ─────────────────────────────────────────────
# أمر البث لكل الأعضاء
# ─────────────────────────────────────────────
@bot.command(name="sendall")
async def sendall(ctx, *, message: str):
    count = 0
    await ctx.send("⏳ جاري النشر...")

    for member in ctx.guild.members:
        if member.bot:
            continue
        try:
            await member.send(f"{member.mention}\n\n{message}")
            count += 1
            await asyncio.sleep(1.5)
        except Exception:
            continue

    await ctx.send(f"✅ تم النشر لـ {count} عضو!")


# ─────────────────────────────────────────────
# أمر التجربة
# ─────────────────────────────────────────────
@bot.command(name="test")
async def test(ctx, *, message: str):
    await ctx.send("🧪 جاري إرسال تجربة...")
    try:
        await ctx.author.send(f"**[تجربة]**\n\n{message}")
        await ctx.send("✅ شيك الخاص!")
    except Exception:
        pass


# ─────────────────────────────────────────────
# أمر الرسالة الخاصة — للمالك فقط
# ─────────────────────────────────────────────
@bot.command(name="dm")
@commands.is_owner()
async def dm_user(ctx, user_id: int, *, message: str):
    try:
        user = await bot.fetch_user(user_id)
        await user.send(message)
        await ctx.send(f"✅ تم إرسال الرسالة لـ **{user}** بنجاح.")
    except discord.NotFound:
        await ctx.send("❌ المستخدم غير موجود، تحقق من الـ ID.")
    except discord.Forbidden:
        await ctx.send("❌ لا أستطيع إرسال رسالة لهذا المستخدم (ربما أغلق رسائله الخاصة).")
    except Exception as e:
        await ctx.send(f"❌ حدث خطأ: {e}")


@dm_user.error
async def dm_user_error(ctx, error):
    if isinstance(error, commands.NotOwner):
        await ctx.send("⛔ هذا الأمر للمالك فقط.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("❌ الصيغة الصحيحة: `!dm [User_ID] [Message]`")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("❌ الـ ID يجب أن يكون رقماً صحيحاً.")
    elif isinstance(error, commands.CommandOnCooldown):
        return  # تجاهل صامت
@bot.command()
@commands.is_owner()
async def leave(ctx, guild_id: int):
    guild = bot.get_guild(guild_id)
    if guild:
        await guild.leave()
        await ctx.send(f"✅ تم الخروج من سيرفر: {guild.name}")
    else:
        await ctx.send("❌ لم أجد هذا السيرفر.")


if __name__ == "__main__":
    if not TOKEN:
        print("❌ Error: DISCORD_TOKEN not found!")
    else:
        keep_alive()
        bot.run(TOKEN)
