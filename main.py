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

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot Active! Developer: @T4HKR"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    bot_app.process_update(update)
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)))

bot_app = Application.builder().token(TOKEN).build()

verified_users = set()

# ============ BUTTONS ============
def get_main_buttons(is_admin=False):
    buttons = [
        [InlineKeyboardButton("📱 Lookup Now", callback_data='lookup')],
        [InlineKeyboardButton("💳 My Credits", callback_data='credits')],
        [InlineKeyboardButton("👥 Refer & Earn", callback_data='refer')],
        [InlineKeyboardButton("❓ Help", callback_data='help')],
    ]
    if is_admin:
        buttons.append([InlineKeyboardButton("👑 Owner Dashboard", callback_data='admin')])
    buttons.append([InlineKeyboardButton("👤 Profile", callback_data='profile')])
    return InlineKeyboardMarkup(buttons)

def get_admin_buttons():
    buttons = [
        [InlineKeyboardButton("📊 Total Users", callback_data='total_users')],
        [InlineKeyboardButton("➕ Add Credits", callback_data='add_credits')],
        [InlineKeyboardButton("📢 Broadcast", callback_data='broadcast')],
        [InlineKeyboardButton("⬅️ Back", callback_data='back')],
    ]
    return InlineKeyboardMarkup(buttons)

# ============ API ============
async def get_number_info(number):
    try:
        response = requests.get(f"{API_URL}{number}", timeout=20)
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'application/pdf' in content_type:
                return ("PDF", response.content)
            try:
                data = response.json()
                if data.get('success') and data.get('pdf_url'):
                    pdf_response = requests.get(data['pdf_url'], timeout=20)
                    if pdf_response.status_code == 200:
                        return ("PDF", pdf_response.content)
                if data.get('success') and data.get('data'):
                    d = data['data']
                    result = f"📋 NUMBER INFO RESULT\nTarget: {number}\n{'='*30}\n\nName    : {d.get('name', 'N/A')}\nFather  : {d.get('father', 'N/A')}\nAddress : {d.get('address', 'N/A')}\nAlt Num : {d.get('alt_num', '')}\nCircle  : {d.get('circle', 'N/A')}\nID      : {d.get('id', 'N/A')}\nEmail   : {d.get('email', '')}\n\n{'-'*30}\n\nName    : {d.get('name', 'N/A')}\nFather  : {d.get('father', 'N/A')}\nAddress : {d.get('address', 'N/A')}\nAlt Num : {d.get('alt_num', '')}\nCircle  : {d.get('circle', 'N/A')}\nID      : {d.get('id', 'N/A')}\nEmail   : {d.get('email', '')}\n\n{'='*30}"
                    return ("TEXT", result)
            except:
                pass
    except:
        pass
    return ("ERROR", None)

# ============ HANDLERS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    add_user(user.id, user.username, user.first_name, user.last_name)
    verified_users.add(user.id)
    
    await update.message.reply_text(
        f"👋 Welcome {user.first_name}!\n\n📱 Send any 10-digit number to get info\n\n👨‍💻 Developer: @T4HKR",
        reply_markup=get_main_buttons(user.id == ADMIN_ID),
        parse_mode='Markdown'
    )

async def lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📱 **Send a 10-digit number**\nExample: `9876543210`\n\nWithout +91",
        reply_markup=get_main_buttons(query.from_user.id == ADMIN_ID),
        parse_mode='Markdown'
    )

async def credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "💳 **My Credits**\n\nYou have 0 credits\n\n💰 Buy credits:\n100 credits - ₹99\n500 credits - ₹399\n1000 credits - ₹699\n\nContact @T4HKR",
        reply_markup=get_main_buttons(query.from_user.id == ADMIN_ID),
        parse_mode='Markdown'
    )

async def refer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "👥 **Refer & Earn**\n\nRefer a friend and earn 10 credits!\n\nYour referral link:\n`https://t.me/SumitOsintBot?start=ref_{}`\n\nShare and earn! 🚀",
        reply_markup=get_main_buttons(query.from_user.id == ADMIN_ID),
        parse_mode='Markdown'
    )

async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "❓ **Help**\n\n📱 Send any 10-digit number to get info\n💰 Buy credits for unlimited searches\n👥 Refer friends to earn free credits\n\n👨‍💻 Developer: @T4HKR\n\n📌 Channel: @SUMITNETW0RK",
        reply_markup=get_main_buttons(query.from_user.id == ADMIN_ID),
        parse_mode='Markdown'
    )

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = query.from_user
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT join_date, total_queries FROM users WHERE user_id = ?', (user_id,))
    data = c.fetchone()
    conn.close()
    
    if data:
        profile_text = f"""👤 **Profile**

Name: {user.first_name}
Username: @{user.username if user.username else 'None'}
ID: {user_id}
Joined: {data[0][:10]}
Total Queries: {data[1]}
Credits: 0

👨‍💻 Developer: @T4HKR"""
    else:
        profile_text = "❌ Profile not found!"
    
    await query.edit_message_text(
        profile_text,
        reply_markup=get_main_buttons(user_id == ADMIN_ID),
        parse_mode='Markdown'
    )

async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.edit_message_text("❌ Access Denied!")
        return
    
    await query.edit_message_text(
        "👑 **Owner Dashboard**\n\nSelect an option:",
        reply_markup=get_admin_buttons(),
        parse_mode='Markdown'
    )

async def total_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("❌ Access Denied!")
        return
    
    total = get_total_users()
    await query.edit_message_text(
        f"📊 **Total Users**\n\n👥 Total Users: {total}\n\n👨‍💻 Developer: @T4HKR",
        reply_markup=get_admin_buttons(),
        parse_mode='Markdown'
    )

async def add_credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("❌ Access Denied!")
        return
    
    await query.edit_message_text(
        "➕ **Add Credits**\n\nSend user ID and credits:\n`/addcredits user_id amount`\n\nExample:\n`/addcredits 7515864015 100`",
        reply_markup=get_admin_buttons(),
        parse_mode='Markdown'
    )

async def broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("❌ Access Denied!")
        return
    
    await query.edit_message_text(
        "📢 **Broadcast Mode**\n\nSend the message you want to broadcast\nType /cancel to stop",
        reply_markup=get_admin_buttons(),
        parse_mode='Markdown'
    )
    context.user_data['broadcast_mode'] = True

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = query.from_user
    
    await query.edit_message_text(
        f"👋 Welcome {user.first_name}!\n\n📱 Send any 10-digit number to get info\n\n👨‍💻 Developer: @T4HKR",
        reply_markup=get_main_buttons(user_id == ADMIN_ID),
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text.strip()
    
    if user_id not in verified_users:
        verified_users.add(user_id)
    
    if not text.isdigit() or len(text) < 10:
        await update.message.reply_text(
            "❌ Send a valid 10-digit number\nExample: `9876543210`",
            parse_mode='Markdown'
        )
        return
    
    msg = await update.message.reply_text("⏳ Searching...")
    update_user_activity(user_id)
    
    result_type, result_data = await get_number_info(text)
    
    if result_type == "PDF" and result_data:
        pdf_file = io.BytesIO(result_data)
        await msg.delete()
        await update.message.reply_document(
            document=InputFile(pdf_file, filename=f"search_result_{text}.pdf"),
            caption=f"✅ Search Completed!\nTarget: {text}\n\n👨‍💻 Developer: @T4HKR",
            parse_mode='Markdown'
        )
    elif result_type == "TEXT" and result_data:
        await msg.edit_text(
            result_data,
            reply_markup=get_main_buttons(user_id == ADMIN_ID),
            parse_mode='Markdown'
        )
    else:
        await msg.edit_text(
            "❌ **API Failed!**\n\nPlease try again later.\n\n👨‍💻 Developer: @T4HKR",
            reply_markup=get_main_buttons(user_id == ADMIN_ID),
            parse_mode='Markdown'
        )

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('broadcast_mode'):
        if update.effective_user.id != ADMIN_ID:
            await update.message.reply_text("❌ Access Denied!")
            return
        
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
                await context.bot.send_message(
                    chat_id=user[0],
                    text=f"📢 **BROADCAST**\n\n{update.message.text}",
                    parse_mode='Markdown'
                )
                success += 1
            except:
                pass
        
        await update.message.reply_text(f"✅ Broadcast sent to {success} users")
        context.user_data['broadcast_mode'] = False

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['broadcast_mode'] = False
    await update.message.reply_text("❌ Cancelled")

# ============ REGISTER ============
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("cancel", cancel))
bot_app.add_handler(CallbackQueryHandler(lookup, pattern='lookup'))
bot_app.add_handler(CallbackQueryHandler(credits, pattern='credits'))
bot_app.add_handler(CallbackQueryHandler(refer, pattern='refer'))
bot_app.add_handler(CallbackQueryHandler(help_callback, pattern='help'))
bot_app.add_handler(CallbackQueryHandler(profile, pattern='profile'))
bot_app.add_handler(CallbackQueryHandler(admin_dashboard, pattern='admin'))
bot_app.add_handler(CallbackQueryHandler(total_users, pattern='total_users'))
bot_app.add_handler(CallbackQueryHandler(add_credits, pattern='add_credits'))
bot_app.add_handler(CallbackQueryHandler(broadcast_callback, pattern='broadcast'))
bot_app.add_handler(CallbackQueryHandler(back, pattern='back'))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
bot_app.add_handler(MessageHandler(filters.PHOTO, handle_broadcast))

if __name__ == '__main__':
    init_db()
    threading.Thread(target=run_flask, daemon=True).start()
    print("✅ Bot Started! Developer: @T4HKR")
    print(f"👑 Admin ID: {ADMIN_ID}")
    bot_app.run_polling(allowed_updates=Update.ALL_TYPES)
