import os
import asyncio
from typing import Final
from os.path import join, dirname
from dotenv import load_dotenv

import discord
from discord.ext import commands

from database import session, TOTPlog
import datetime
import pyotp

load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

BOT_TOKEN: Final = os.environ.get("BOT_TOKEN")
TOTP_TOKEN: Final = os.environ.get("TOTP_TOKEN")
OWNER_ID: Final = int(os.environ.get("OWNER_ID"))

client = discord.Client(intents=discord.Intents.all())
tree = discord.app_commands.CommandTree(client)

totp_generate = pyotp.TOTP(TOTP_TOKEN)


@client.event
async def on_ready():
    await tree.sync()
    print('TOTP Ready!')


@tree.command(name="totp", description="6桁のワンタイムパスワードを取得します")
async def totp(interaction: discord.Interaction):
    await interaction.response.defer()
    one_time_password = totp_generate.now()
    time_remaining = totp_generate.interval - datetime.datetime.now().timestamp() % totp_generate.interval
    if time_remaining <= 5:
        await asyncio.sleep(time_remaining)
        one_time_password = totp_generate.now()
        time_remaining = totp_generate.interval - datetime.datetime.now().timestamp() % totp_generate.interval
    await interaction.followup.send(
        "One-Time Password : ```{}```\n有効時間 : {}s".format(one_time_password, time_remaining), ephemeral=True)
    session.add(TOTPlog(user_id=interaction.user.id, user_name=interaction.user.name, generated_totp=one_time_password))
    session.commit()


@tree.command(name="show", description="ワンタイムパスワードを取得した履歴を表示します")
async def logShow(interaction: discord.Interaction, log_limit: int = 10):
    await interaction.response.defer()
    logs = session.query(TOTPlog.id,TOTPlog.user_id,TOTPlog.user_name,TOTPlog.generated_totp,TOTPlog.created_at).limit(log_limit).all()
    if not logs:
        await interaction.followup.send("履歴はありませんでした")
    else:
        export_data = ""
        for log in logs:
            export_data += "`No.{} {} {}({}) {}`\n".format(log.id,log.created_at.strftime("%Y/%m/%d %H:%M:%S"),log.user_name,log.user_id,log.generated_totp)

        await interaction.followup.send(export_data)


@tree.command(name="shutdown", description="DiscordBotをシャットダウンします")
async def sh(interaction: discord.Interaction):
    if interaction.user.id == OWNER_ID:
        await interaction.response.send_message("shutdown now!", ephemeral=True)
        await client.close()
    else:
        await interaction.response.send_message("この操作は許可されていません", ephemeral=True)


client.run(BOT_TOKEN)
