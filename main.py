import os
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

client =  discord.Client(intents=discord.Intents.all())
tree = discord.app_commands.CommandTree(client)

totp_generate = pyotp.TOTP(TOTP_TOKEN)

@client.event
async def on_ready():
    await tree.sync()
    print('TOTP Ready!')

@tree.command(name="totp",description="6桁のワンタイムパスワードを取得します")
async def totp(interaction:discord.Interaction):
    print(totp_generate)
    one_time_password = totp_generate.now()
    time_remaining = totp_generate.interval - datetime.datetime.now().timestamp() % totp_generate.interval
    await interaction.response.send_message("One-Time Password : ```{}```\n有効時間 : {}s".format(one_time_password,time_remaining),ephemeral=True)
    session.add(TOTPlog(user_id=interaction.user.id,generated_totp=one_time_password))


client.run(BOT_TOKEN)
