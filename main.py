import subprocess
import sys
import os

# discord.py-selfを自動インストール
try:
    import discord
except ImportError:
    print("discord.py-selfをインストール中...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "discord.py-self"])
    print("インストール完了！")

import discord
import asyncio
from datetime import datetime

# ========== 環境変数から設定を取得 ==========
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')
CHANNEL_ID = os.getenv('CHANNEL_ID')
INTERVAL = int(os.getenv('INTERVAL', '7201'))  # デフォルト: 2時間1秒

# コマンドのアプリケーションID（Botごとに異なる）
DISBOARD_APP_ID = 302050872383242240  # Disboard
DISSOKU_APP_ID = 761562078095867916   # DissokuのID（例）
# =========================================

# 必須環境変数のチェック
if not TOKEN:
    print('❌ エラー: DISCORD_TOKEN が設定されていません')
    sys.exit(1)

if not CHANNEL_ID:
    print('❌ エラー: CHANNEL_ID が設定されていません')
    sys.exit(1)

# IDを整数に変換
try:
    CHANNEL_ID = int(CHANNEL_ID)
    if GUILD_ID:
        GUILD_ID = int(GUILD_ID)
except ValueError:
    print('❌ エラー: GUILD_IDまたはCHANNEL_IDが無効です（数値である必要があります）')
    sys.exit(1)

client = discord.Client()

@client.event
async def on_ready():
    print(f'========================================')
    print(f'ログイン成功: {client.user}')
    if GUILD_ID:
        print(f'サーバーID: {GUILD_ID}')
    print(f'チャンネルID: {CHANNEL_ID}')
    print(f'実行間隔: {INTERVAL}秒 (約{INTERVAL//3600}時間{(INTERVAL%3600)//60}分)')
    print(f'========================================\n')

    await command_loop()

async def send_slash_command(channel, command_name, bot_id):
    """スラッシュコマンドを送信"""
    try:
        # スラッシュコマンドとして送信
        await channel.send(f'</{command_name}:{bot_id}>')
        return True
    except Exception as e:
        print(f'❌ スラッシュコマンド送信エラー: {e}')

        # フォールバック: 通常のメッセージとして送信
        try:
            await channel.send(f'/{command_name}')
            return True
        except Exception as e2:
            print(f'❌ 通常メッセージ送信エラー: {e2}')
            return False

async def execute_commands(channel):
    """利用可能なすべてのコマンドを実行"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    success_count = 0

    # /bump コマンド（Disboard）を試行
    print(f'[{current_time}] /bump を実行中...')
    if await send_slash_command(channel, 'bump', DISBOARD_APP_ID):
        print(f'✅ /bump を実行しました')
        success_count += 1

    await asyncio.sleep(3)

    # /up コマンドを試行
    print(f'[{current_time}] /up を実行中...')
    try:
        await channel.send('/up')
        print(f'✅ /up を実行しました')
        success_count += 1
    except Exception as e:
        print(f'❌ /up の実行エラー: {e}')

    return success_count

async def command_loop():
    """指定間隔でコマンドを実行"""
    while True:
        try:
            channel = client.get_channel(CHANNEL_ID)

            if channel is None:
                print(f'❌ エラー: チャンネルID {CHANNEL_ID} が見つかりません')
                print('チャンネルIDを確認してください')
                await asyncio.sleep(300)
                continue

            # コマンドを実行
            success = await execute_commands(channel)

            if success > 0:
                print(f'✅ {success}個のコマンドを実行しました')
            else:
                print(f'⚠️  コマンドの実行に失敗しました')

            # 次回実行時刻を計算
            next_time = datetime.fromtimestamp(
                datetime.now().timestamp() + INTERVAL
            ).strftime('%Y-%m-%d %H:%M:%S')

            print(f'⏰ 次回実行: {next_time}')
            print(f'💤 {INTERVAL}秒待機中...\n')

            await asyncio.sleep(INTERVAL)

        except discord.errors.HTTPException as e:
            print(f'❌ Discord APIエラー: {e}')
            print('レート制限の可能性があります。60秒待機します...')
            await asyncio.sleep(60)

        except Exception as e:
            print(f'❌ 予期しないエラー: {e}')
            print('60秒待機して再試行します...')
            await asyncio.sleep(60)

# Botを起動
try:
    print('Botを起動しています...')
    client.run(TOKEN)
except discord.errors.LoginFailure:
    print('❌ ログイン失敗: トークンが無効です')
    print('DISCORD_TOKENを確認してください')
except Exception as e:
    print(f'❌ 起動エラー: {e}')