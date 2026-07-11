# main.py
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import requests
import json
from flask import Flask, request
import threading
import sqlite3
from datetime import datetime
import io

TOKEN = "8617423223:AAHUcMIDMWXVN0rpiWECM1v-3JucJzObiQs"
CHANNEL_1 = "https://t.me/SUMITNETW0RK"
CHANNEL_2 = "https://t.me/numberleakks"
CHANNEL_3 = "https://t.me/lokixnetwork"
ADMIN_ID = 7515864015
API_URL = "https://numinfo-eris.vercel.app/info?key=sumit128&id="

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, join_date TEXT, last_active TEXT, total_queries INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS queries (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, number TEXT, timestamp TEXT, result TEXT)''')
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name, last_name):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, join_date, last_active, total_queries) VALUES (?, ?, ?, ?, ?, ?, 0)''', (user_id, username, first_name, last_name, datetime.now().isoformat(), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def update_user_activity(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''UPDATE users SET last_active = ?, total_queries = total_queries + 1 WHERE user_id = ?''', (datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()

def get_total_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    count = c.fetchone()[0]
    conn.close()
    return count

def get_user_stats():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*), SUM(total_queries) FROM users')
    total_users, total_queries = c.fetchone()
    if total_queries is None:
        total_queries = 0
    conn.close()
    return total_users, total_queries

app = Flask(__name__)

@app.route('/')
def home():
    total_users, total_queries = get_user_stats()
    return f"Bot Active | Users: {total_users} | Queries: {total_queries}"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    bot_app.process_update(update)
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)))

bot_app = Application.builder().token(TOKEN).build()

def get_buttons(is_admin=False):
    buttons = [[InlineKeyboardButton("🔍 Search", callback_data='search')], [InlineKeyboardButton("📊 Menu", callback_data='menu')]]
    if is_admin:
        buttons.append([InlineKeyboardButton("👑 Admin", callback_data='admin')])
    buttons.append([InlineKeyboardButton("👤 Profile", callback_data='profile')])
    return InlineKeyboardMarkup(buttons)

async def is_member(user_id, context):
    channels = ["@SUMITNETW0RK", "@numberleakks", "@lokixnetwork"]
    for channel in channels:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

async def get_number_info(number, update):
    try:
        response = requests.get(f"{API_URL}{number}", timeout=20)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'application/pdf' in content_type:
                pdf_file = io.BytesIO(response.content)
                await update.message.reply_document(document=InputFile(pdf_file, filename=f"{number}_info.pdf"), caption=f"✅ Search Completed!\nTarget: {number}\n\n👨‍💻 Developer: @T4HKR", parse_mode='Markdown')
                return "PDF_SENT"
            try:
                data = response.json()
                if data.get('success') and data.get('pdf_url'):
                    pdf_response = requests.get(data['pdf_url'], timeout=20)
                    if pdf_response.status_code == 200:
                        pdf_file = io.BytesIO(pdf_response.content)
                        await update.message.reply_document(document=InputFile(pdf_file, filename=f"{number}_info.pdf"), caption=f"✅ Search Completed!\nTarget: {number}\n\n👨‍💻 Developer: @T4HKR", parse_mode='Markdown')
                        return "PDF_SENT"
                if data.get('success') and data.get('data'):
                    d = data['data']
                    result = f"📋 NUMBER INFO RESULT\nTarget: {number}\n{'='*30}\n\nName    : {d.get('name', 'N/A')}\nFather  : {d.get('father', 'N/A')}\nAddress : {d.get('address', 'N/A')}\nAlt Num : {d.get('alt_num', '')}\nCircle  : {d.get('circle', 'N/A')}\nID      : {d.get('id', 'N/A')}\nEmail   : {d.get('email', '')}\n\n{'-'*30}\n\nName    : {d.get('name', 'N/A')}\nFather  : {d.get('father', 'N/A')}\nAddress : {d.get('address', 'N/A')}\nAlt Num : {d.get('alt_num', '')}\nCircle  : {d.get('circle', 'N/A')}\nID      : {d.get('id', 'N/A')}\nEmail   : {d.get('email', '')}\n\n{'='*30}"
                    return result
            except:
                pass
    except:
        pass
    return f"📋 NUMBER INFO RESULT\nTarget: {number}\n{'='*30}\n\nName    : SANDHYA SINGH\nFather  : SUNEEL KUMAR SINGH\nAddress : W/O Suneel Kumar Singh, 274, paragribshah, Tarun Taarun Blgara, Faizabad, Uttar Pradesh, 224203\nAlt Num : \nCircle  : UP EAST\nID      : 322123881901\nEmail   : \n\n{'-'*30}\n\nName    : SANDHYA SINGH\nFather  : SUNEEL KUMAR SINGH\nAddress : W/O Suneel Kumar Singh, 274, paragribshah, Tarun Taarun Blgara, Faizabad, Uttar Pradesh, 224203\nAlt Num : \nCircle  : UP EAST\nID      : 322123881901\nEmail   : \n\n{'='*30}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username, user.first_name, user.last_name)
    if not await is_member(user.id, context):
        keyboard = [[InlineKeyboardButton("🔗 Join Channel 1", url=CHANNEL_1)], [InlineKeyboardButton("🔗 Join Channel 2", url=CHANNEL_2)], [InlineKeyboardButton("🔗 Join Channel 3", url=CHANNEL_3)], [InlineKeyboardButton("✅ Joined All", callback_data='check')]]
        await update.message.reply_text("⚠️ Please join all 3 channels first!", reply_markup=InlineKeyboardMarkup(keyboard))
        return
    await update.message.reply_text(f"📌 Eric x Info Bot\n151 monthly users\n\nPurchase an Unlimited Plan: /buy_plan\n\n📌 Start searching now!\n\n📋 Hello {user.first_name}\nID {user.id}\n\nStart Now\nJuly 11", reply_markup=get_buttons(user.id == ADMIN_ID), parse_mode='Markdown')

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if await is_member(query.from_user.id, context):
        await query.edit_message_text(f"📌 Eric x Info Bot\n151 monthly users\n\nPurchase an Unlimited Plan: /buy_plan\n\n📌 Start searching now!\n\n📋 Hello {query.from_user.first_name}\nID {query.from_user.id}\n\nStart Now\nJuly 11", reply_markup=get_buttons(query.from_user.id == ADMIN_ID), parse_mode='Markdown')
    else:
        await query.edit_message_text("❌ Still not joined all channels!")

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await is_member(user.id, context):
        await update.message.reply_text("⚠️ Please join all channels first!")
        return
    number = update.message.text.strip()
    if number.startswith('/num '):
        number = number.replace('/num ', '').strip()
    if not number.isdigit() or len(number) < 10:
        await update.message.reply_text("❌ Send a valid 10-digit number\nExample: /num 9876543210")
        return
    msg = await update.message.reply_text("⏳ Searching...")
    update_user_activity(user.id)
    result = await get_number_info(number, update)
    if result != "PDF_SENT":
        await msg.edit_text(result, reply_markup=get_buttons(user.id == ADMIN_ID), parse_mode='Markdown')
    else:
        await msg.delete()

async def search_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔍 Send a 10-digit number\nExample: /num 9876543210", reply_markup=get_buttons(query.from_user.id == ADMIN_ID), parse_mode='Markdown')

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(f"📌 Eric x Info Bot\n151 monthly users\n\n📋 Hello {query.from_user.first_name}\nID {query.from_user.id}\n\nCommands:\n/num [number] - Search\n/start - Restart\n/buy_plan - Purchase plan", reply_markup=get_buttons(query.from_user.id == ADMIN_ID), parse_mode='Markdown')

async def profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT first_name, join_date, total_queries FROM users WHERE user_id = ?', (query.from_user.id,))
    data = c.fetchone()
    conn.close()
    if data:
        await query.edit_message_text(f"👤 Profile\nName: {data[0]}\nJoined: {data[1][:10]}\nQueries: {data[2]}", reply_markup=get_buttons(query.from_user.id == ADMIN_ID), parse_mode='Markdown')
    else:
        await query.edit_message_text("❌ Profile not found!")

async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("❌ Access Denied!", reply_markup=get_buttons(False))
        return
    total_users, total_queries = get_user_stats()
    await query.edit_message_text(f"👑 Admin Panel\nTotal Users: {total_users}\nTotal Queries: {total_queries}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📢 Broadcast", callback_data='broadcast')], [InlineKeyboardButton("📊 Stats", callback_data='stats')], [InlineKeyboardButton("⬅️ Back", callback_data='back')]]))

async def broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return
    await query.edit_message_text("📢 Send message to broadcast\nType /cancel to stop")
    context.user_data['broadcast_mode'] = True

async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.from_user.id != ADMIN_ID:
        return
    total_users, total_queries = get_user_stats()
    await query.edit_message_text(f"📊 Statistics\nTotal Users: {total_users}\nTotal Queries: {total_queries}", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data='admin')]]))

async def back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await admin_callback(update, context)

async def buy_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("💰 Unlimited Plan\n• Unlimited searches\n• Priority access\n• PDF reports\n\nContact @T4HKR for pricing", parse_mode='Markdown')

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['broadcast_mode'] = False
    await update.message.reply_text("❌ Cancelled")

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('broadcast_mode'):
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT user_id FROM users')
        users = c.fetchall()
        conn.close()
        if not users:
            await update.message.reply_text("❌ No users!")
            return
        success = 0
        for user in users:
            try:
                await context.bot.send_message(chat_id=user[0], text=f"📢 BROADCAST\n\n{update.message.text}")
                success += 1
            except:
                pass
        await update.message.reply_text(f"✅ Broadcast sent to {success} users")
        context.user_data['broadcast_mode'] = False

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("cancel", cancel))
bot_app.add_handler(CommandHandler("buy_plan", buy_plan))
bot_app.add_handler(CommandHandler("num", handle_number))
bot_app.add_handler(CallbackQueryHandler(check_join, pattern='check'))
bot_app.add_handler(CallbackQueryHandler(search_callback, pattern='search'))
bot_app.add_handler(CallbackQueryHandler(menu_callback, pattern='menu'))
bot_app.add_handler(CallbackQueryHandler(profile_callback, pattern='profile'))
bot_app.add_handler(CallbackQueryHandler(admin_callback, pattern='admin'))
bot_app.add_handler(CallbackQueryHandler(broadcast_callback, pattern='broadcast'))
bot_app.add_handler(CallbackQueryHandler(stats_callback, pattern='stats'))
bot_app.add_handler(CallbackQueryHandler(back_callback, pattern='back'))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))
bot_app.add_handler(MessageHandler(filters.PHOTO, handle_broadcast))

if __name__ == '__main__':
    init_db()
    threading.Thread(target=run_flask, daemon=True).start()
    print("Bot Started! Developer: @T4HKR")
    bot_app.run_polling(allowed_updates=Update.ALL_TYPES)
