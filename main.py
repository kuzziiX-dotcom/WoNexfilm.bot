import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# --- CONFIGURATION ---
API_ID = int(os.environ.get("API_ID", ""))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
BIN_CHANNEL = int(os.environ.get("BIN_CHANNEL", ""))
URL = os.environ.get("URL", "") # Render App URL

bot = Client("wonex_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# භාෂා සැකසුම් (Sinhala & English)
strings = {
    "en": {
        "start": "👋 Welcome! Send me any video or file to get a direct link.",
        "gen": "✅ **Link Generated!**\n\n🎬 **File:** `{}`\n🔗 **Link:** `{}`",
        "btn_video": "🎬 Send Video",
        "btn_lang": "සිංහල භාෂාව"
    },
    "si": {
        "start": "👋 සාදරයෙන් පිළිගනිමු! ඕනෑම වීඩියෝවක් මට එවන්න.",
        "gen": "✅ **ලින්ක් එක සූදානම්!**\n\n🎬 **ගොනුව:** `{}`\n🔗 **ලින්ක් එක:** `{}`",
        "btn_video": "🎬 වීඩියෝව එවන්න",
        "btn_lang": "English Language"
    }
}

user_lang = {}

@bot.on_message(filters.command("start"))
async def start(client, message):
    uid = message.from_user.id
    lang = user_lang.get(uid, "en")
    btn = InlineKeyboardMarkup([[
        InlineKeyboardButton(strings[lang]["btn_lang"], callback_data="set_lang")
    ]])
    await message.reply_text(strings[lang]["start"], reply_markup=btn)

@bot.on_callback_query(filters.regex("set_lang"))
async def change_lang(client, query):
    uid = query.from_user.id
    user_lang[uid] = "si" if user_lang.get(uid, "en") == "en" else "en"
    lang = user_lang[uid]
    await query.message.edit_text(strings[lang]["start"], 
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(strings[lang]["btn_lang"], callback_data="set_lang")]]))

@bot.on_message(filters.video | filters.document)
async def handle_file(client, message):
    lang = user_lang.get(message.from_user.id, "en")
    msg = await message.reply_text("⌛ Processing..." if lang == "en" else "⌛ සැකසෙමින් පවතියි...")
    
    # Forward to Bin Channel
    log_msg = await message.copy(BIN_CHANNEL)
    file_name = message.video.file_name if message.video else "File"
    
    # Generate Link (Render URL based)
    stream_link = f"{URL}/{log_msg.id}"
    
    await msg.edit_text(
        strings[lang]["gen"].format(file_name, stream_link),
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🎬 Watch / Download", url=stream_link),
            InlineKeyboardButton("📁 Get File", callback_data=f"get_{log_msg.id}")
        ]])
    )

@bot.on_callback_query(filters.regex(r"get_"))
async def get_file(client, query):
    msg_id = int(query.data.split("_")[1])
    await client.copy_message(query.from_user.id, BIN_CHANNEL, msg_id)

# Simple Web Server for Render
async def handle(request):
    return web.Response(text="WON EX STREAM BOT IS ALIVE!")

async def run_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", 8080)
    await site.start()

async def main():
    await bot.start()
    await run_server()
    print("Bot is running...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
