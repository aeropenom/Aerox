import asyncio
import random
import ssl
import json
import time
import uuid
import requests
import shutil
from loguru import logger
from websockets_proxy import Proxy, proxy_connect
from fake_useragent import UserAgent
import requests
import time

# Konfigurasi
PROXY_API_URL = "http://your-proxy-provider.com/api/getProxy"  # API untuk mendapatkan proxy baru
REFRESH_INTERVAL = 300  # Waktu refresh dalam detik (5 menit)
TEST_URL = "https://httpbin.org/ip"  # URL untuk mengetes proxy

def get_new_proxy():
    """
    Mendapatkan proxy baru dari penyedia.
    """
    try:
        response = requests.get(PROXY_API_URL)
        if response.status_code == 200:
            proxy = response.text.strip()
            print(f"🔄 Proxy baru didapatkan: {proxy}")
            return {"http": proxy, "https": proxy}
        else:
            print(f"❌ Gagal mendapatkan proxy. Status: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ Error saat mendapatkan proxy: {e}")
        return None

def test_proxy(proxy):
    """
    Mengecek apakah proxy berfungsi.
    """
    try:
        response = requests.get(TEST_URL, proxies=proxy, timeout=10)
        if response.status_code == 200:
            print(f"✅ Proxy berfungsi. IP: {response.json()['origin']}")
            return True
        else:
            print(f"❌ Proxy gagal. Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Proxy gagal: {e}")
    return False

def main():
    """
    Main loop untuk memperbarui proxy secara otomatis.
    """
    while True:
        print("\n=== Memulai proses refresh proxy ===")
        proxy = get_new_proxy()
        
        if proxy and test_proxy(proxy):
            print("🚀 Proxy aktif dan siap digunakan.")
        else:
            print("⚠️ Proxy tidak valid. Mencoba lagi dalam 10 detik...")
            time.sleep(10)
            continue
        
        print(f"🕒 Menunggu {REFRESH_INTERVAL} detik sebelum refresh berikutnya...")
        time.sleep(REFRESH_INTERVAL)

if __name__ == "__main__":
    main()

async def connect_to_wss(socks5_proxy, user_id):
    user_agent = UserAgent(os=['windows', 'macos', 'linux'], browsers='chrome')
    random_user_agent = user_agent.random
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
    logger.info(device_id)
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": random_user_agent,
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            urilist = ["wss://proxy2.wynd.network:4444/","wss://proxy2.wynd.network:4650/"]
            uri = random.choice(urilist)
            server_hostname = "proxy2.wynd.network"
            proxy = Proxy.from_url(socks5_proxy)
            async with proxy_connect(uri, proxy=proxy, ssl=ssl_context, server_hostname=server_hostname,
                                     extra_headers=custom_headers) as websocket:
                async def send_ping():
                    while True:
                        send_message = json.dumps(
                            {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}})
                        logger.debug(send_message)
                        await websocket.send(send_message)
                        await asyncio.sleep(5)

                await asyncio.sleep(1)
                asyncio.create_task(send_ping())

                while True:
                    response = await websocket.recv()
                    message = json.loads(response)
                    logger.info(message)
                    if message.get("action") == "AUTH":
                        auth_response = {
                            "id": message["id"],
                            "origin_action": "AUTH",
                            "result": {
                                "browser_id": device_id,
                                "user_id": user_id,
                                "user_agent": custom_headers['User-Agent'],
                                "timestamp": int(time.time()),
                                "device_type": "desktop",
                                "version": "4.29.0",
                            }
                        }
                        logger.debug(auth_response)
                        await websocket.send(json.dumps(auth_response))

                    elif message.get("action") == "PONG":
                        pong_response = {"id": message["id"], "origin_action": "PONG"}
                        logger.debug(pong_response)
                        await websocket.send(json.dumps(pong_response))
        except Exception as e:
            logger.error(e)
            logger.error(socks5_proxy)


async def main():
    #find user_id on the site in conlose localStorage.getItem('userId') (if you can't get it, write allow pasting)
    _user_id = input('Please Enter your user ID: ')
    with open('local_proxies.txt', 'r') as file:
            local_proxies = file.read().splitlines()
    tasks = [asyncio.ensure_future(connect_to_wss(i, _user_id)) for i in local_proxies]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    #letsgo
    asyncio.run(main())
