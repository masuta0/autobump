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
import random

# ========== 環境変数から設定を取得 ==========
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD_ID = os.getenv('GUILD_ID')
CHANNEL_ID = os.getenv('CHANNEL_ID')
INTERVAL = int(os.getenv('INTERVAL', '7201'))  # デフォルト: 2時間1秒

# BotのアプリケーションID
DISBOARD_ID = 302050872383242240  # Disboard (/bump)
DISSOKU_ID = 761562078095867916   # ディス速 (/up)
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
    print(f'対応Bot: Disboard (/bump), ディス速 (/up)')
    print(f'========================================\n')

    await command_loop()

async def send_slash_command_v2(channel, command_name, application_id):
    """スラッシュコマンドを実行（簡易版）"""
    try:
        # Nonce生成（DiscordのメッセージID形式）
        nonce = str((int(datetime.now().timestamp() * 1000) - 1420070400000) << 22)

        # スラッシュコマンドのペイロード
        payload = {
            'type': 2,  # APPLICATION_COMMAND
            'application_id': str(application_id),
            'guild_id': str(channel.guild.id),
            'channel_id': str(channel.id),
            'session_id': getattr(client._connection, 'session_id', 'undefined'),
            'data': {
                'version': '1237313708783759441',  # 汎用バージョンID
                'id': str(application_id),
                'name': command_name,
                'type': 1,
                'options': [],
                'application_command': {
                    'id': str(application_id),
                    'application_id': str(application_id),
                    'version': '1237313708783759441',
                    'type': 1,
                    'name': command_name,
                    'description': 'Bump this server',
                    'dm_permission': True,
                    'contexts': None,
                    'integration_types': [0],
                    'options': []
                },
                'attachments': []
            },
            'nonce': nonce
        }

        # リクエスト送信
        response = await client.http.request(
            discord.http.Route('POST', '/interactions'),
            json=payload
        )

        return True

    except discord.errors.HTTPException as e:
        if e.status == 404:
            print(f'⚠️  {command_name} コマンドがこのサーバーで利用できません')
        elif e.status == 403:
            print(f'⚠️  {command_name} コマンドの実行権限がありません')
        else:
            print(f'❌ HTTPエラー ({e.status}): {e.text}')
        return False

    except Exception as e:
        print(f'❌ {command_name} 実行エラー: {e}')
        return False

async def send_slash_command_simple(channel, command_name):
    """通常のメッセージとしてスラッシュコマンドを送信（フォールバック）"""
    try:
        await channel.send(f'/{command_name}')
        await asyncio.sleep(1)
        return True
    except Exception as e:
        print(f'❌ メッセージ送信エラー: {e}')
        return False

async def execute_commands(channel):
    """ディス速とDisboardのコマンドを実行"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'\n=== [{current_time}] コマンド実行開始 ===')

    success_count = 0

    # ディス速の /up を実行
    print('🔄 ディス速 /up を実行中...')
    if await send_slash_command_v2(channel, 'up', DISSOKU_ID):
        print('✅ ディス速 /up を実行しました')
        success_count += 1
    else:
        print('⚠️  方法1失敗、方法2を試行中...')
        if await send_slash_command_simple(channel, 'up'):
            print('✅ ディス速 /up を送信しました（テキスト形式）')
            success_count += 1

    # 少し待機
    await asyncio.sleep(4)

    # Disboardの /bump を実行
    print('🔄 Disboard /bump を実行中...')
    if await send_slash_command_v2(channel, 'bump', DISBOARD_ID):
        print('✅ Disboard /bump を実行しました')
        success_count += 1
    else:
        print('⚠️  方法1失敗、方法2を試行中...')
        if await send_slash_command_simple(channel, 'bump'):
            print('✅ Disboard /bump を送信しました（テキスト形式）')
            success_count += 1

    print(f'=== 実行完了: {success_count}/2 成功 ===\n')
    return success_count

async def command_loop():
    """指定間隔でコマンドを実行するループ"""
    # 初回実行前に少し待機
    await asyncio.sleep(5)

    while True:
        try:
            channel = client.get_channel(CHANNEL_ID)

            if channel is None:
                print(f'❌ エラー: チャンネルID {CHANNEL_ID} が見つかりません')
                print('チャンネルIDを確認してください')
                await asyncio.sleep(300)
                continue

            # チャンネルがギルド（サーバー）に属しているか確認
            if not hasattr(channel, 'guild') or channel.guild is None:
                print(f'❌ エラー: チャンネルがサーバーに属していません（DMチャンネルは非対応）')
                await asyncio.sleep(300)
                continue

            # コマンドを実行
            success = await execute_commands(channel)

            if success == 0:
                print('⚠️  すべてのコマンドが失敗しました')
                print('   次の点を確認してください:')
                print('   - Disboard, ディス速がサーバーにいるか')
                print('   - チャンネルでコマンドが使えるか')
                print('   - 手動で /bump と /up が実行できるか')

            # 次回実行時刻を計算
            next_time = datetime.fromtimestamp(
                datetime.now().timestamp() + INTERVAL
            ).strftime('%Y-%m-%d %H:%M:%S')

            print(f'⏰ 次回実行予定: {next_time}')
            print(f'💤 {INTERVAL}秒 ({INTERVAL//3600}時間{(INTERVAL%3600)//60}分) 待機中...')

            await asyncio.sleep(INTERVAL)

        except discord.errors.HTTPException as e:
            print(f'❌ Discord APIエラー: {e}')
            if 'rate limit' in str(e).lower() or e.status == 429:
                wait_time = 300
                print(f'レート制限が発生しました。{wait_time}秒待機します...')
                await asyncio.sleep(wait_time)
            else:
                print('60秒待機して再試行します...')
                await asyncio.sleep(60)

        except Exception as e:
            print(f'❌ 予期しないエラー: {e}')
            import traceback
            traceback.print_exc()
            print('60秒待機して再試行します...')
            await asyncio.sleep(60)

@client.event
async def on_error(event, *args, **kwargs):
    """エラーハンドリング"""
    import traceback
    print(f'❌ イベントエラー ({event}):')
    traceback.print_exc()

# Botを起動
try:
    print('='*50)
    print('Discord Selfbot - ディス速・Disboard自動実行')
    print('='*50)
    print('⚠️  警告: Selfbotの使用はDiscord利用規約違反です')
    print('⚠️  アカウントBANのリスクがあります')
    print('='*50)
    print('\nBotを起動しています...')
    client.run(TOKEN)
except discord.errors.LoginFailure:
    print('❌ ログイン失敗: トークンが無効です')
    print('DISCORD_TOKENを確認してください')
except KeyboardInterrupt:
    print('\n\n👋 Botを終了します...')
except Exception as e:
    print(f'❌ 起動エラー: {e}')
    import traceback
    traceback.print_exc()