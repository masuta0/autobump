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

async def command_loop():
    """指定間隔で/upと/bumpを実行"""
    while True:
        try:
            channel = client.get_channel(CHANNEL_ID)

            if channel is None:
                print(f'❌ エラー: チャンネルID {CHANNEL_ID} が見つかりません')
                print('チャンネルIDを確認してください')
                await asyncio.sleep(300)
                continue

            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # /upコマンド実行
            try:
                await channel.send('/up')
                print(f'✅ [{current_time}] /up を実行しました')
            except Exception as e:
                print(f'❌ /up の実行中にエラー: {e}')

            await asyncio.sleep(3)

            # /bumpコマンド実行
            try:
                await channel.send('/bump')
                print(f'✅ [{current_time}] /bump を実行しました')
            except Exception as e:
                print(f'❌ /bump の実行中にエラー: {e}')

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