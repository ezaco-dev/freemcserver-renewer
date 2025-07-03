import os
import asyncio
from flask import Flask
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from pyppeteer import launch
from pyppeteer_stealth import stealth

load_dotenv()
app = Flask(__name__)
scheduler = BackgroundScheduler()

# Fungsi: Renew satu akun (bisa beberapa server)
async def renew_account(username, password, server_ids):
    browser = await launch(headless=True, args=['--no-sandbox', '--disable-dev-shm-usage'])
    page = await browser.newPage()
    await stealth(page)

    print(f"🔐 Login: {username}")
    await page.goto('https://freemcserver.net/login', {'waitUntil': 'networkidle2'})
    await page.type('#username', username)
    await page.type('#password', password)
    await page.click('button[type="submit"]')
    await page.waitForNavigation({'waitUntil': 'networkidle2'})

    for server_id in server_ids:
        server_id = server_id.strip()
        print(f"🔄 Mencoba renew server {server_id}...")
        await page.goto(f'https://freemcserver.net/server/{server_id}', {'waitUntil': 'networkidle2'})
        try:
            await page.waitForSelector('#renewButton', timeout=8000)
            await page.click('#renewButton')
            print(f"✅ Server {server_id} berhasil di-renew!")
        except:
            print(f"⚠️ Server {server_id} tidak perlu diperpanjang atau gagal.")

    await browser.close()


# Fungsi: Renew semua akun
async def renew_all_accounts():
    idx = 1
    while True:
        user = os.getenv(f"USER_{idx}")
        pw = os.getenv(f"PASS_{idx}")
        ids = os.getenv(f"SERVER_IDS_{idx}")
        if not user or not pw or not ids:
            break
        server_list = ids.split(',')
        await renew_account(user, pw, server_list)
        idx += 1


# Flask route
@app.route('/')
def home():
    return '✅ Auto-renew aktif!'

@app.route('/renew')
def manual_renew():
    asyncio.get_event_loop().create_task(renew_all_accounts())
    return '🔁 Manual renew semua akun dipanggil.'

# Jadwal tiap 3 jam + langsung saat startup
scheduler.add_job(lambda: asyncio.get_event_loop().run_until_complete(renew_all_accounts()), 'interval', hours=3)
scheduler.start()
asyncio.get_event_loop().run_until_complete(renew_all_accounts())

if __name__ == '__main__':
    app.run()
