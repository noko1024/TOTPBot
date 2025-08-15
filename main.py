import os
import asyncio
from os.path import join, dirname
from dotenv import load_dotenv
import datetime
import pyotp

from typing import Final

import discord
from discord.ext import commands

from db.db import get_db
from models import *


load_dotenv(verbose=True)
dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

BOT_TOKEN: Final = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN is not set in environment variables")

OWNER_ID_STR = os.environ.get("OWNER_ID")
if not OWNER_ID_STR:
    raise ValueError("OWNER_ID is not set in environment variables")
try:
    OWNER_ID: Final = int(OWNER_ID_STR)
except ValueError:
    raise ValueError("OWNER_ID must be a valid integer")

client = discord.Client(intents=discord.Intents.all())
tree = discord.app_commands.CommandTree(client)


def totp_generate(guild_id: str) -> pyotp.TOTP:
    with get_db() as session:
        token_record = session.query(TOTPToken).filter(TOTPToken.guild_id == guild_id).first()
        if not token_record:
            raise ValueError("指定されたサーバーのTOTPトークンが設定されていません。")
        return pyotp.TOTP(token_record.totp_token)


def auth_owner(interaction: discord.Interaction) -> bool:
    if interaction.user.id != OWNER_ID:
        return False
    return True

def auth_guild_admin_role(interaction: discord.Interaction) -> bool:
    # 管理者権限を持つかチェック
    return interaction.user.guild_permissions.administrator

def auth_role(interaction: discord.Interaction, guild_id: str) -> bool:
    with get_db() as session:
        auth_roles = session.query(Role).filter(Role.guild_id == guild_id).all()
        current_role = interaction.user.roles
        
        if not auth_roles:
            return True
        elif not any(role.id in [r.role_id for r in auth_roles] for role in current_role):
            return False
        return True

def check_admin_permission(interaction: discord.Interaction, target_guild_id: str = None) -> tuple[bool, str]:
    """
    管理者権限をチェックし、結果とエラーメッセージを返す
    
    Returns:
        tuple[bool, str]: (権限があるか, エラーメッセージ)
    """
    current_guild_id = str(interaction.guild.id)
    
    # target_guild_idが指定されていない場合は現在のサーバーを使用
    if not target_guild_id:
        target_guild_id = current_guild_id
    
    # 他のサーバーを指定している場合はOWNER_IDのみ許可
    if target_guild_id != current_guild_id:
        if interaction.user.id != OWNER_ID:
            return False, "このコマンドを実行する権限がありません"
        return True, ""
    
    # 自分のサーバーの場合はOWNER_IDまたは管理者権限
    if interaction.user.id == OWNER_ID or auth_guild_admin_role(interaction):
        return True, ""
    
    return False, "この操作は許可されていません"

@client.event
async def on_ready():
    await tree.sync()
    print('TOTP Ready!')


@tree.command(name="totp", description="6桁のワンタイムパスワードを取得します")
async def totp(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    guild_id = str(interaction.guild.id)

    if not auth_role(interaction, guild_id): 
        return await interaction.followup.send("このコマンドを実行する権限がありません", ephemeral=True)

    try:
        totp_obj = totp_generate(guild_id)
    except ValueError as e:
        await interaction.followup.send(str(e), ephemeral=True)
        return None
    
    one_time_password = totp_obj.now()
    time_remaining = totp_obj.interval - datetime.datetime.now().timestamp() % totp_obj.interval
    if time_remaining <= 5:
        await asyncio.sleep(time_remaining)
        one_time_password = totp_obj.now()
        time_remaining = totp_obj.interval - datetime.datetime.now().timestamp() % totp_obj.interval
    
    await interaction.followup.send(
        "One-Time Password : ```{}```\n有効時間 : {}s".format(one_time_password, int(time_remaining)), ephemeral=True)
    
    with get_db() as session:
        try:
            session.add(TOTPlog(user_id=str(interaction.user.id), user_name=interaction.user.name, generated_totp=one_time_password, guild_id=guild_id))
            session.commit()
        except Exception as e:
            session.rollback()
            print(f"Error logging TOTP generation: {e}")
    
    return None


@tree.command(name="show", description="ワンタイムパスワードを取得した履歴を表示します")
async def show(interaction: discord.Interaction, log_limit: int = 10):
    await interaction.response.defer()

    guild_id = str(interaction.guild.id)
    
    with get_db() as session:
        logs = session.query(TOTPlog.id,TOTPlog.user_id,TOTPlog.user_name,TOTPlog.generated_totp,TOTPlog.created_at).filter(TOTPlog.guild_id == guild_id).order_by(TOTPlog.created_at.desc()).limit(log_limit).all()

    if not logs:
        await interaction.followup.send("履歴はありませんでした")
    else:
        export_data = ""
        for log in logs:
            export_data += "`No.{} {} {}({}) {}`\n".format(log.id,log.created_at.strftime("%Y/%m/%d %H:%M:%S"),log.user_name,log.user_id,log.generated_totp)

        await interaction.followup.send(export_data)

@tree.command(name="set_token", description="TOTPトークンを設定します")
async def set_token(interaction: discord.Interaction, token: str, guild_id: str = None):
    await interaction.response.defer(ephemeral=True)

    # 権限チェック
    has_permission, error_message = check_admin_permission(interaction, guild_id)
    if not has_permission:
        return await interaction.followup.send(error_message, ephemeral=True)
    
    if not guild_id:
        guild_id = str(interaction.guild.id)

    if not auth_role(interaction, guild_id): 
        return await interaction.followup.send("このコマンドを実行する権限がありません", ephemeral=True)

    try:
        totp_obj = pyotp.TOTP(token)
        totp_obj.now()  # トークンが有効か確認
    except Exception as e:
        await interaction.followup.send(f"無効なトークンです: {e}", ephemeral=True)
        return None

    with get_db() as session:
        try:
            existing_guild = session.query(Guild).filter(Guild.guild_id == guild_id).first()
            if not existing_guild:
                guild_name = interaction.guild.name if interaction.guild else f"Guild {guild_id}"
                new_guild = Guild(name=guild_name, guild_id=guild_id, totp_token=token)
                session.add(new_guild)
                session.flush()
            else:
                # 既存のGuildレコードも更新
                existing_guild.totp_token = token

            # TOTPTokenレコードを作成または更新
            existing_token = session.query(TOTPToken).filter(TOTPToken.guild_id == guild_id).first()
            if existing_token:
                existing_token.totp_token = token
            else:
                new_token = TOTPToken(totp_token=token, guild_id=guild_id)
                session.add(new_token)

            session.commit()
            await interaction.followup.send("TOTPトークンが設定されました", ephemeral=True)
        except Exception as e:
            session.rollback()
            await interaction.followup.send(f"トークンの設定中にエラーが発生しました: {e}", ephemeral=True)
            return None
    
    return None


@tree.command(name="delete_token", description="TOTPトークンを削除します")
async def delete_token(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)

    # 権限チェック
    has_permission, error_message = check_admin_permission(interaction)
    if not has_permission:
        return await interaction.followup.send(error_message, ephemeral=True)

    guild_id = str(interaction.guild.id)

    with get_db() as session:
        try:
            existing_token = session.query(TOTPToken).filter(TOTPToken.guild_id == guild_id).first()
            if existing_token:
                session.delete(existing_token)
                session.commit()
                await interaction.followup.send("TOTPトークンが削除されました", ephemeral=True)
            else:
                await interaction.followup.send("指定されたサーバーのTOTPトークンは存在しません", ephemeral=True)
        except Exception as e:
            session.rollback()
            await interaction.followup.send(f"トークンの削除中にエラーが発生しました: {e}", ephemeral=True)

    return None


@tree.command(name="set_role", description="認証ロールを設定します")
async def set_role(interaction: discord.Interaction, role: discord.Role):
    await interaction.response.defer(ephemeral=True)

    # 権限チェック
    has_permission, error_message = check_admin_permission(interaction)
    if not has_permission:
        return await interaction.followup.send(error_message, ephemeral=True)

    guild_id = str(interaction.guild.id)

    if not interaction.guild.get_role(role.id):
        await interaction.followup.send("指定されたロールは存在しません", ephemeral=True)
        return None

    with get_db() as session:
        try:
            existing_role = session.query(Role).filter(Role.role_id == role.id, Role.guild_id == guild_id).first()
            if existing_role:
                await interaction.followup.send("指定されたロールは既に存在します", ephemeral=True)
                return None

            new_role = Role(role_id=role.id, guild_id=guild_id)
            session.add(new_role)
            session.commit()

            await interaction.followup.send("ロールが設定されました", ephemeral=True)
        except Exception as e:
            session.rollback()
            await interaction.followup.send(f"ロールの設定中にエラーが発生しました: {e}", ephemeral=True)
    
    return None


@tree.command(name="delete_role", description="認証ロールを削除します")
async def delete_role(interaction: discord.Interaction, role: discord.Role, guild_id: str = None):
    await interaction.response.defer(ephemeral=True)

    # 権限チェック
    has_permission, error_message = check_admin_permission(interaction, guild_id)
    if not has_permission:
        return await interaction.followup.send(error_message, ephemeral=True)
    
    if not guild_id:
        guild_id = str(interaction.guild.id)

    with get_db() as session:
        try:
            existing_role = session.query(Role).filter(Role.role_id == role.id, Role.guild_id == guild_id).first()
            if not existing_role: 
                return await interaction.followup.send("指定されたロールは存在しません", ephemeral=True)

            session.delete(existing_role)
            session.commit()
            await interaction.followup.send("ロールが削除されました", ephemeral=True)
        except Exception as e:
            session.rollback()
            await interaction.followup.send(f"ロールの削除中にエラーが発生しました: {e}", ephemeral=True)
    
    return None


@tree.command(name="shutdown", description="DiscordBotをシャットダウンします")
async def shutdown(interaction: discord.Interaction):
    if interaction.user.id == OWNER_ID:
        await interaction.response.send_message("shutdown now!", ephemeral=True)
        await client.close()
    else:
        await interaction.response.send_message("この操作は許可されていません", ephemeral=True)


client.run(BOT_TOKEN)