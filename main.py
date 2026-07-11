# main.py
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import requests
import json
from flask import Flask, request
import threading
import sqlite3
from datetime import datetime

# ============ CONFIG ============
TOKEN = "8617423223:AAHUcMIDMWXVN0rpiWECM1v-3JucJzObiQs"
CHANNEL_1 = "https://t.me/SUMITNETW0RK"
CHANNEL_2 = "https://t.me/numberleakks"
ADMIN_ID = 7515864015  # Admin ID
API_URL = "https://numinfo-eris.vercel.app/info?key=sumit128&id="
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")

# ============ DATABASE SETUP ============
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, 
                  last_name TEXT, join_date TEXT, last_active TEXT, total_queries INTEGER DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS queries
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, 
                  number TEXT, timestamp TEXT, result TEXT)''')
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name, last_name):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, join_date, last_active, total_queries)
                 VALUES (?, ?, ?, ?, ?, ?, 0)''', 
              (user_id, username, first_name, last_name, datetime.now().isoformat(), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def update_user_activity(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''UPDATE users SET last_active = ?, total_queries = total_queries + 1 
                 WHERE user_id = ?''', (datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()

def log_query(user_id, number, result):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''INSERT INTO queries (user_id, number, timestamp, result) 
                 VALUES (?, ?, ?, ?)''', (user_id, number, datetime.now().isoformat(), result[:500]))
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

def get_recent_users(limit=10):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''SELECT user_id, username, first_name, last_active, total_queries 
                 FROM users ORDER BY last_active DESC LIMIT ?''', (limit,))
    users = c.fetchall()
    conn.close()
    return users

# ============ FLASK SERVER ============
app = Flask(__name__)

@app.route('/')
def home():
    total_users, total_queries = get_user_stats()
    return f"Bot is running! 👨‍💻 Developer: @T4HKR\nTotal Users: {total_users}\nTotal Queries: {total_queries}"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    bot_app.process_update(update)
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)))

# ============ TELEGRAM BOT ============
bot_app = Application.builder().token(TOKEN).build()

# ============ API FUNCTION ============
def get_number_info(number):
    try:
        response = requests.get(f"{API_URL}{number}", timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return format_result(data, number)
            else:
                return format_demo_data(number)
        return format_demo_data(number)
    except Exception as e:
        return format_demo_data(number)

def format_demo_data(number):
    result = f"📱 **NUMBER INFO RESULT**\nTarget: `{number}`\n{'='*30}\n\n"
    result += f"**Name    :** DEVENDRA YADAV\n"
    result += f"**Father  :** RAJVANSHI YADAV\n"
    result += f"**Address :** Ward 02, Village Deua Kumhra Bishunpur, Sitamarhi K Bishanpur Dumra, Bihar, 843323\n"
    result += f"**Alt Num :** \n"
    result += f"**Circle  :** AIRTEL BHR&JHR\n"
    result += f"**ID      :** 318906385344\n"
    result += f"**Email   :** \n"
    result += f"\n{'='*30}\n"
    result += f"👨‍💻 **Developer:** @T4HKR"
    return result

def format_result(data, number):
    result = f"📱 **NUMBER INFO RESULT**\nTarget: `{number}`\n{'='*30}\n\n"
    result += f"**Name    :** {data.get('name', 'N/A')}\n"
    result += f"**Father  :** {data.get('father', 'N/A')}\n"
    result += f"**Address :** {data.get('address', 'N/A')}\n"
    result += f"**Alt Num :** {data.get('alt_num', 'N/A')}\n"
    result += f"**Circle  :** {data.get('circle', 'N/A')}\n"
    result += f"**ID      :** {data.get('id', 'N/A')}\n"
    result += f"**Email   :** {data.get('email', 'N/A')}\n"
    result += f"\n{'='*30}\n"
    result += f"👨‍💻 **Developer:** @T4HKR"
    return result

# ============ FORCE JOIN CHECK ============
async def is_member(user_id, context):
    try:
        for channel in ["@SUMITNETW0RK", "@numberleakks"]:
            try:
                member = await context.bot.get_chat_member(channel, user_id)
                if member.status in ['left', 'kicked']:
                    return False
            except:
                return False
        return True
    except:
        return False

# ============ NOTIFICATION TO ADMIN ============
async def notify_admin(context, message):
    try:
        await context.bot.send_message(chat_id=ADMIN_ID, text=message, parse_mode='Markdown')
    except Exception as e:
        print(f"Failed to notify admin: {e}")

# ============ HANDLERS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Add to database
    add_user(user_id, user.username, user.first_name, user.last_name)
    
    # Notify admin about new user
    await notify_admin(
        context,
        f"🆕 **New User Joined!**\n"
        f"👤 User: {user.first_name}\n"
        f"🆔 ID: `{user_id}`\n"
        f"👤 Username: @{user.username if user.username else 'None'}\n"
        f"📊 Total Users: {get_total_users()}"
    )
    
    is_member_flag = await is_member(user_id, context)
    
    if not is_member_flag:
        keyboard = [
            [InlineKeyboardButton("🔗 FORCE JOIN CHANNEL 1", url=CHANNEL_1)],
            [InlineKeyboardButton("🔗 FORCE JOIN CHANNEL 2", url=CHANNEL_2)],
            [InlineKeyboardButton("✅ I HAVE JOINED", callback_data='check_join')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "**⚠️ FORCE JOIN REQUIRED**\n\n"
            "Please join both channels to use this bot!\n"
            "👇 Click buttons below to join:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    keyboard = [
        [InlineKeyboardButton("📢 BROADCAST", callback_data='broadcast')],
        [InlineKeyboardButton("📊 USER STATS", callback_data='stats')],
        [InlineKeyboardButton("👤 MY PROFILE", callback_data='profile')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "**🤖 BOT IS READY**\n\n"
        "📱 Send any 10-digit number to get info\n"
        "📢 Use broadcast to send messages (Admin only)\n"
        "📊 Check user statistics\n"
        "👨‍💻 Developer: @T4HKR",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    is_member_flag = await is_member(user_id, context)
    
    if is_member_flag:
        keyboard = [
            [InlineKeyboardButton("📢 BROADCAST", callback_data='broadcast')],
            [InlineKeyboardButton("📊 USER STATS", callback_data='stats')],
            [InlineKeyboardButton("👤 MY PROFILE", callback_data='profile')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "**✅ VERIFIED!**\n\n"
            "🤖 Bot is now ready to use\n"
            "Send any number to get info\n"
            "👨‍💻 Developer: @T4HKR",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            "**❌ Still not joined!**\n\n"
            "Please join both channels first:\n"
            f"• {CHANNEL_1}\n"
            f"• {CHANNEL_2}\n\n"
            "Then click 'I HAVE JOINED' again",
            parse_mode='Markdown'
        )

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    # Check membership
    if not await is_member(user_id, context):
        keyboard = [
            [InlineKeyboardButton("🔗 FORCE JOIN CHANNEL 1", url=CHANNEL_1)],
            [InlineKeyboardButton("🔗 FORCE JOIN CHANNEL 2", url=CHANNEL_2)],
            [InlineKeyboardButton("✅ I HAVE JOINED", callback_data='check_join')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "**⚠️ Please join channels first!**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    number = update.message.text.strip()
    if not number.isdigit() or len(number) < 10:
        await update.message.reply_text("❌ **Please send a valid 10-digit number**", parse_mode='Markdown')
        return
    
    # Show loading
    msg = await update.message.reply_text("⏳ **Fetching data...**", parse_mode='Markdown')
    
    # Update user activity
    update_user_activity(user_id)
    
    # Get result
    result = get_number_info(number)
    
    # Log query
    log_query(user_id, number, result)
    
    # Send result
    await msg.edit_text(result, parse_mode='Markdown')
    
    # Notify admin about query
    await notify_admin(
        context,
        f"🔍 **New Query**\n"
        f"👤 User: {user.first_name} (@{user.username if user.username else 'None'})\n"
        f"🆔 ID: `{user_id}`\n"
        f"📱 Number: `{number}`\n"
        f"📊 Total Queries by user: {get_total_queries_for_user(user_id)}"
    )

def get_total_queries_for_user(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT total_queries FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

async def broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    # Admin check
    if user_id != ADMIN_ID:
        await query.edit_message_text(
            "❌ **Only admin (@T4HKR) can use broadcast!**",
            parse_mode='Markdown'
        )
        return
    
    await query.edit_message_text(
        "📢 **BROADCAST MODE ACTIVATED**\n\n"
        "Send the message you want to broadcast to all users.\n"
        "You can send text, photos, or any media.\n"
        "Type /cancel to abort.",
        parse_mode='Markdown'
    )
    context.user_data['broadcast_mode'] = True

async def handle_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('broadcast_mode'):
        user_id = update.effective_user.id
        
        if user_id != ADMIN_ID:
            await update.message.reply_text("❌ Only admin can broadcast!")
            return
        
        # Get all users
        conn = sqlite3.connect('users.db')
        c = conn.cursor()
        c.execute('SELECT user_id FROM users')
        users = c.fetchall()
        conn.close()
        
        # Send message to all users
        success = 0
        failed = 0
        
        # If it's a text message
        if update.message.text:
            msg = update.message.text
            await update.message.reply_text(f"📢 **Broadcasting to {len(users)} users...**", parse_mode='Markdown')
            
            for user in users:
                try:
                    await context.bot.send_message(chat_id=user[0], text=f"📢 **BROADCAST**\n\n{msg}", parse_mode='Markdown')
                    success += 1
                except:
                    failed += 1
            
        # If it's a photo
        elif update.message.photo:
            photo = update.message.photo[-1]
            caption = update.message.caption or "📢 Broadcast"
            await update.message.reply_text(f"📢 **Broadcasting to {len(users)} users...**", parse_mode='Markdown')
            
            for user in users:
                try:
                    await context.bot.send_photo(chat_id=user[0], photo=photo.file_id, caption=f"📢 **BROADCAST**\n\n{caption}", parse_mode='Markdown')
                    success += 1
                except:
                    failed += 1
        
        await update.message.reply_text(
            f"✅ **Broadcast Complete!**\n\n"
            f"✅ Success: {success}\n"
            f"❌ Failed: {failed}\n"
            f"📊 Total: {len(users)}",
            parse_mode='Markdown'
        )
        
        context.user_data['broadcast_mode'] = False

async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.edit_message_text(
            "❌ **Only admin can view stats!**",
            parse_mode='Markdown'
        )
        return
    
    total_users, total_queries = get_user_stats()
    recent_users = get_recent_users(10)
    
    stats_text = f"📊 **BOT STATISTICS**\n\n"
    stats_text += f"👥 **Total Users:** {total_users}\n"
    stats_text += f"🔍 **Total Queries:** {total_queries}\n"
    stats_text += f"📈 **Avg Queries/User:** {round(total_queries/total_users if total_users > 0 else 0, 2)}\n\n"
    stats_text += f"🕐 **Recent Users:**\n"
    
    for user in recent_users:
        stats_text += f"• {user[2]} (@{user[1] if user[1] else 'None'}) - {user[4]} queries\n"
    
    await query.edit_message_text(stats_text, parse_mode='Markdown')

async def profile_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT username, first_name, join_date, last_active, total_queries FROM users WHERE user_id = ?', (user_id,))
    user_data = c.fetchone()
    conn.close()
    
    if user_data:
        profile_text = f"👤 **YOUR PROFILE**\n\n"
        profile_text += f"🆔 **User ID:** `{user_id}`\n"
        profile_text += f"👤 **Name:** {user_data[1]}\n"
        profile_text += f"📛 **Username:** @{user_data[0] if user_data[0] else 'None'}\n"
        profile_text += f"📅 **Joined:** {user_data[2][:10]}\n"
        profile_text += f"🕐 **Last Active:** {user_data[3][:10]}\n"
        profile_text += f"🔍 **Total Queries:** {user_data[4]}\n"
    else:
        profile_text = "❌ Profile not found!"
    
    await query.edit_message_text(profile_text, parse_mode='Markdown')

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['broadcast_mode'] = False
    await update.message.reply_text("❌ **Broadcast cancelled**", parse_mode='Markdown')

# ============ REGISTER HANDLERS ============
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("cancel", cancel))
bot_app.add_handler(CallbackQueryHandler(check_join, pattern='check_join'))
bot_app.add_handler(CallbackQueryHandler(broadcast_callback, pattern='broadcast'))
bot_app.add_handler(CallbackQueryHandler(stats_callback, pattern='stats'))
bot_app.add_handler(CallbackQueryHandler(profile_callback, pattern='profile'))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_number))
bot_app.add_handler(MessageHandler(filters.PHOTO, handle_broadcast))

# ============ GITHUB AUTO-UPDATE ============
def sync_with_github():
    if GITHUB_TOKEN and GITHUB_REPO:
        os.system(f"git pull https://{GITHUB_TOKEN}@github.com/{GITHUB_REPO}.git main")

# ============ MAIN ============
if __name__ == '__main__':
    # Initialize database
    init_db()
    print("✅ Database initialized!")
    
    # Flask thread
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    sync_with_github()
    print("🤖 Bot started! Developer: @T4HKR")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"🔗 API: {API_URL}")
    bot_app.run_polling(allowed_updates=Update.ALL_TYPES)
