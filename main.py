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
import json

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

# コマンド情報のキャッシュ
command_cache = {}

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

async def search_commands_in_channel(channel):
    """チャンネル内でスラッシュコマンドを検索"""
    try:
        # スラッシュコマンドの候補を取得
        url = f'https://discord.com/api/v9/channels/{channel.id}/application-commands/search'
        params = {
            'type': 1,  # CHAT_INPUT
            'include_applications': 'true'
        }

        headers = {
            'Authorization': client.http.token,
            'Content-Type': 'application/json'
        }

        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, headers=headers) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get('application_commands', [])
                else:
                    print(f'⚠️  コマンド検索失敗: {resp.status}')
                    return []
    except Exception as e:
        print(f'❌ コマンド検索エラー: {e}')
        return []

async def execute_slash_command(channel, command_info):
    """スラッシュコマンドを実行"""
    try:
        url = 'https://discord.com/api/v9/interactions'

        payload = {
            'type': 2,
            'application_id': command_info['application_id'],
            'guild_id': str(channel.guild.id),
            'channel_id': str(channel.id),
            'session_id': client._connection.session_id,
            'data': {
                'version': command_info['version'],
                'id': command_info['id'],
                'name': command_info['name'],
                'type': command_info['type'],
                'options': [],
                'application_command': command_info,
                'attachments': []
            }
        }

        headers = {
            'Authorization': client.http.token,
            'Content-Type': 'application/json'
        }

        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status in [200, 204]:
                    return True
                else:
                    error_text = await resp.text()
                    print(f'⚠️  実行失敗 ({resp.status}): {error_text}')
                    return False

    except Exception as e:
        print(f'❌ コマンド実行エラー: {e}')
        return False

async def send_text_command(channel, command_name):
    """テキストとしてコマンドを送信（フォールバック）"""
    try:
        await channel.send(f'/{command_name}')
        return True
    except Exception as e:
        print(f'❌ テキスト送信エラー: {e}')
        return False

async def execute_commands(channel):
    """ディス速とDisboardのコマンドを実行"""
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'\n=== [{current_time}] コマンド実行開始 ===')

    success_count = 0

    # キャッシュがない場合はコマンドを検索
    if not command_cache:
        print('🔍 利用可能なコマンドを検索中...')
        commands = await search_commands_in_channel(channel)

        for cmd in commands:
            command_cache[cmd['name']] = cmd
            print(f'   見つかったコマンド: /{cmd["name"]} (App: {cmd.get("application_id", "unknown")})')

        if not command_cache:
            print('⚠️  スラッシュコマンドが見つかりませんでした')
            print('   テキスト形式で送信を試みます')

    # /up を実行
    print('🔄 ディス速 /up を実行中...')
    if 'up' in command_cache:
        if await execute_slash_command(channel, command_cache['up']):
            print('✅ ディス速 /up を実行しました（スラッシュコマンド）')
            success_count += 1
        else:
            print('⚠️  スラッシュコマンド失敗、テキスト形式を試行...')
            if await send_text_command(channel, 'up'):
                print('✅ /up を送信しました（テキスト形式）')
                success_count += 1
    else:
        if await send_text_command(channel, 'up'):
            print('✅ /up を送信しました（テキスト形式）')
            success_count += 1

    await asyncio.sleep(4)

    # /bump を実行
    print('🔄 Disboard /bump を実行中...')
    if 'bump' in command_cache:
        if await execute_slash_command(channel, command_cache['bump']):
            print('✅ Disboard /bump を実行しました（スラッシュコマンド）')
            success_count += 1
        else:
            print('⚠️  スラッシュコマンド失敗、テキスト形式を試行...')
            if await send_text_command(channel, 'bump'):
                print('✅ /bump を送信しました（テキスト形式）')
                success_count += 1
    else:
        if await send_text_command(channel, 'bump'):
            print('✅ /bump を送信しました（テキスト形式）')
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
                await asyncio.sleep(300)
                continue

            if not hasattr(channel, 'guild') or channel.guild is None:
                print(f'❌ エラー: チャンネルがサーバーに属していません')
                await asyncio.sleep(300)
                continue

            # コマンドを実行
            success = await execute_commands(channel)

            if success == 0:
                print('⚠️  すべてのコマンドが失敗しました')

            # 次回実行時刻を計算
            next_time = datetime.fromtimestamp(
                datetime.now().timestamp() + INTERVAL
            ).strftime('%Y-%m-%d %H:%M:%S')

            print(f'⏰ 次回実行予定: {next_time}')
            print(f'💤 {INTERVAL}秒待機中...')

            await asyncio.sleep(INTERVAL)

        except Exception as e:
            print(f'❌ エラー: {e}')
            import traceback
            traceback.print_exc()
            await asyncio.sleep(60)

# Botを起動
try:
    print('='*50)
    print('Discord Selfbot - ディス速・Disboard自動実行')
    print('='*50)
    print('⚠️  警告: Selfbotの使用はDiscord利用規約違反です')
    print('='*50)
    print('\nBotを起動しています...')
    client.run(TOKEN)
except Exception as e:
    print(f'❌ 起動エラー: {e}')
    import traceback
    traceback.print_exc()