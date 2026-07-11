# main.py
import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import requests
import json
from flask import Flask, request
import threading
import sqlite3
from datetime import datetime, timedelta
import io
import random

TOKEN = "8617423223:AAHUcMIDMWXVN0rpiWECM1v-3JucJzObiQs"
CHANNEL_1 = "https://t.me/SUMITNETW0RK"
CHANNEL_2 = "https://t.me/numberleakks"
CHANNEL_3 = "https://t.me/lokixnetwork"
CHANNEL_4 = "https://t.me/SlotsByPhoenix"
ADMIN_IDS = [7515864015, 8242927146]
API_URL = "https://numinfo-eris.vercel.app/info?key=sumit128&id="

REMINDER_INTERVAL = 30  # minutes

def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, last_name TEXT, join_date TEXT, last_active TEXT, total_queries INTEGER DEFAULT 0, reminded BOOLEAN DEFAULT 0)''')
    c.execute('''CREATE TABLE IF NOT EXISTS queries (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, number TEXT, timestamp TEXT, result TEXT)''')
    conn.commit()
    conn.close()

def add_user(user_id, username, first_name, last_name):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, join_date, last_active, total_queries, reminded) VALUES (?, ?, ?, ?, ?, ?, 0, 0)''', (user_id, username, first_name, last_name, datetime.now().isoformat(), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def update_user_activity(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''UPDATE users SET last_active = ?, total_queries = total_queries + 1, reminded = 0 WHERE user_id = ?''', (datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()

def get_total_users():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    count = c.fetchone()[0]
    conn.close()
    return count

def get_inactive_users():
    """Get users who haven't used bot in last 30 mins"""
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    cutoff = (datetime.now() - timedelta(minutes=REMINDER_INTERVAL)).isoformat()
    c.execute('''SELECT user_id, first_name, reminded FROM users 
                 WHERE last_active < ? AND reminded = 0''', (cutoff,))
    users = c.fetchall()
    conn.close()
    return users

def mark_reminded(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''UPDATE users SET reminded = 1 WHERE user_id = ?''', (user_id,))
    conn.commit()
    conn.close()

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

def is_admin(user_id):
    return user_id in ADMIN_IDS

# ============ REMINDER MESSAGES ============
REMINDER_MESSAGES = [
    "**👋 HELLO I'M READY TO USE!**\n\nSend any 10-digit number to get info 💪",
    "**👋 HELLO WHERE ARE YOU?**\n\nSearch any number now! 📱💖",
    "**🌟 STILL WAITING FOR YOU!**\n\nSend a number and get instant results 🚀",
    "**⚡ DON'T FORGET!**\n\nI'm here to help you with number lookups 💯",
    "**💫 READY WHEN YOU ARE!**\n\nJust send a 10-digit number and boom! 💥",
    "**👀 I CAN SEE YOU'RE BUSY!**\n\nBut I'm always here for number searches 🔍"
]

# ============ REMINDER SYSTEM ============
async def send_reminders(context: ContextTypes.DEFAULT_TYPE):
    """Send reminder messages to inactive users"""
    try:
        inactive_users = get_inactive_users()
        
        for user_id, first_name, reminded in inactive_users:
            if reminded == 0:  # Only send if not reminded yet
                try:
                    msg = random.choice(REMINDER_MESSAGES)
                    await context.bot.send_message(
                        chat_id=user_id,
                        text=msg,
                        parse_mode='Markdown'
                    )
                    mark_reminded(user_id)
                    print(f"✅ Reminder sent to {first_name} ({user_id})")
                except Exception as e:
                    print(f"❌ Failed to send reminder to {user_id}: {e}")
    except Exception as e:
        print(f"❌ Reminder error: {e}")

def schedule_reminders(app):
    """Schedule reminder messages every 30 minutes"""
    job_queue = app.job_queue
    
    # Run every 30 minutes
    job_queue.run_repeating(
        send_reminders,
        interval=REMINDER_INTERVAL * 60,  # Convert to seconds
        first=60  # Start after 1 minute
    )
    print(f"✅ Reminders scheduled every {REMINDER_INTERVAL} minutes")

# ============ BUTTONS ============
def get_main_buttons(user_id):
    buttons = [
        [InlineKeyboardButton("📱 LOOKUP NOW", callback_data='lookup')],
    ]
    if is_admin(user_id):
        buttons.append([
            InlineKeyboardButton("📢 BROADCAST", callback_data='broadcast'),
            InlineKeyboardButton("📊 TOTAL USERS", callback_data='total_users')
        ])
    buttons.append([InlineKeyboardButton("🔙 BACK TO HOME", callback_data='home')])
    return InlineKeyboardMarkup(buttons)

def get_join_buttons():
    buttons = [
        [InlineKeyboardButton("🔗 JOIN CHANNEL 1", url=CHANNEL_1)],
        [InlineKeyboardButton("🔗 JOIN CHANNEL 2", url=CHANNEL_2)],
        [InlineKeyboardButton("🔗 JOIN CHANNEL 3", url=CHANNEL_3)],
        [InlineKeyboardButton("🔗 JOIN CHANNEL 4", url=CHANNEL_4)],
        [InlineKeyboardButton("✅ I HAVE JOINED ALL", callback_data='check_join')],
    ]
    return InlineKeyboardMarkup(buttons)

async def is_member(user_id, context):
    channels = ["@SUMITNETW0RK", "@numberleakks", "@lokixnetwork", "@SlotsByPhoenix"]
    for channel in channels:
        try:
            member = await context.bot.get_chat_member(channel, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except:
            return False
    return True

async def notify_admins(context, message):
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=message, parse_mode='Markdown')
        except:
            pass

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
                
                if 'Api' in data:
                    del data['Api']
                if 'Developer' in data:
                    del data['Developer']
                
                data['Developer'] = '@T4HKR'
                
                json_data = json.dumps(data, indent=2)
                return ("JSON", json_data)
                
            except json.JSONDecodeError:
                return ("TEXT", response.text)
        else:
            return ("ERROR", f"Status Code: {response.status_code}")
    except Exception as e:
        return ("ERROR", str(e))

# ============ HANDLERS ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    
    add_user(user_id, user.username, user.first_name, user.last_name)
    verified_users.add(user_id)
    
    await notify_admins(
        context,
        f"🆕 **New User Joined!**\n\n"
        f"👤 Name: {user.first_name}\n"
        f"🆔 ID: `{user_id}`\n"
        f"📛 Username: @{user.username if user.username else 'None'}\n"
        f"📊 Total Users: {get_total_users()}"
    )
    
    if not await is_member(user_id, context):
        await update.message.reply_text(
            "⚠️ **Please join all 4 channels first!**\n\nAfter joining, click the button below:",
            reply_markup=get_join_buttons(),
            parse_mode='Markdown'
        )
        return
    
    await update.message.reply_text(
        f"👋 **Welcome {user.first_name}!**\n\n"
        f"📱 Send any 10-digit number to get info\n"
        f"👨‍💻 Developer: @T4HKR",
        reply_markup=get_main_buttons(user_id),
        parse_mode='Markdown'
    )

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if await is_member(user_id, context):
        try:
            await query.message.delete()
        except:
            pass
        
        await query.message.reply_text(
            f"👋 **Welcome {query.from_user.first_name}!**\n\n"
            f"📱 Send any 10-digit number to get info\n"
            f"👨‍💻 Developer: @T4HKR",
            reply_markup=get_main_buttons(user_id),
            parse_mode='Markdown'
        )
    else:
        await query.edit_message_text(
            "❌ **Still not joined all channels!**\n\nPlease join all 4 channels first:",
            reply_markup=get_join_buttons(),
            parse_mode='Markdown'
        )

async def lookup(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    await query.edit_message_text(
        "📱 **Send a 10-digit number**\n"
        "Example: `9876543210`\n\n"
        "⚠️ Without +91",
        reply_markup=get_main_buttons(user_id),
        parse_mode='Markdown'
    )

async def home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user = query.from_user
    
    await query.edit_message_text(
        f"👋 **Welcome {user.first_name}!**\n\n"
        f"📱 Send any 10-digit number to get info\n"
        f"👨‍💻 Developer: @T4HKR",
        reply_markup=get_main_buttons(user_id),
        parse_mode='Markdown'
    )

async def total_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.edit_message_text(
            "❌ **Access Denied!**",
            reply_markup=get_main_buttons(user_id),
            parse_mode='Markdown'
        )
        return
    
    total = get_total_users()
    await query.edit_message_text(
        f"📊 **Total Users**\n\n"
        f"👥 Total Users: `{total}`\n\n"
        f"👨‍💻 Developer: @T4HKR",
        reply_markup=get_main_buttons(user_id),
        parse_mode='Markdown'
    )

async def broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if not is_admin(user_id):
        await query.edit_message_text(
            "❌ **Access Denied!**",
            reply_markup=get_main_buttons(user_id),
            parse_mode='Markdown'
        )
        return
    
    await query.edit_message_text(
        "📢 **BROADCAST MODE**\n\n"
        "Send the message you want to broadcast\n"
        "Type /cancel to stop",
        reply_markup=get_main_buttons(user_id),
        parse_mode='Markdown'
    )
    context.user_data['broadcast_mode'] = True

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text.strip()
    
    if user_id not in verified_users:
        verified_users.add(user_id)
    
    # Check if in broadcast mode
    if context.user_data.get('broadcast_mode'):
        if is_admin(user_id):
            conn = sqlite3.connect('users.db')
            c = conn.cursor()
            c.execute('SELECT user_id FROM users')
            users = c.fetchall()
            conn.close()
            
            if not users:
                await update.message.reply_text("❌ No users!", reply_markup=get_main_buttons(user_id))
                return
            
            success = 0
            for u in users:
                try:
                    await context.bot.send_message(
                        chat_id=u[0],
                        text=f"📢 **BROADCAST**\n\n{text}",
                        parse_mode='Markdown'
                    )
                    success += 1
                except:
                    pass
            
            await update.message.reply_text(
                f"✅ Broadcast sent to {success} users",
                reply_markup=get_main_buttons(user_id),
                parse_mode='Markdown'
            )
            context.user_data['broadcast_mode'] = False
            return
        else:
            await update.message.reply_text("❌ Access Denied!", reply_markup=get_main_buttons(user_id))
            return
    
    # Check membership
    if not await is_member(user_id, context):
        await update.message.reply_text(
            "⚠️ **Please join all 4 channels first!**",
            reply_markup=get_join_buttons(),
            parse_mode='Markdown'
        )
        return
    
    # Check if number
    if not text.isdigit() or len(text) < 10:
        await update.message.reply_text(
            "❌ Send a valid 10-digit number\nExample: `9876543210`",
            reply_markup=get_main_buttons(user_id),
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
            caption=f"✅ Search Completed!\n\nTarget: {text}",
            reply_markup=get_main_buttons(user_id),
            parse_mode='Markdown'
        )
    elif result_type == "JSON" and result_data:
        json_file = io.BytesIO(result_data.encode('utf-8'))
        await msg.delete()
        await update.message.reply_document(
            document=InputFile(json_file, filename=f"info_{text}.json"),
            caption=f"✅ Search Completed!\n\nTarget: {text}",
            reply_markup=get_main_buttons(user_id),
            parse_mode='Markdown'
        )
    elif result_type == "TEXT" and result_data:
        txt_file = io.BytesIO(result_data.encode('utf-8'))
        await msg.delete()
        await update.message.reply_document(
            document=InputFile(txt_file, filename=f"search_result_{text}.txt"),
            caption=f"✅ Search Completed!\n\nTarget: {text}",
            reply_markup=get_main_buttons(user_id),
            parse_mode='Markdown'
        )
    else:
        await msg.edit_text(
            f"❌ **Error!**\n\n{result_data}",
            reply_markup=get_main_buttons(user_id),
            parse_mode='Markdown'
        )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['broadcast_mode'] = False
    user_id = update.effective_user.id
    await update.message.reply_text(
        "❌ Cancelled",
        reply_markup=get_main_buttons(user_id),
        parse_mode='Markdown'
    )

# ============ REGISTER ============
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("cancel", cancel))
bot_app.add_handler(CallbackQueryHandler(check_join, pattern='check_join'))
bot_app.add_handler(CallbackQueryHandler(lookup, pattern='lookup'))
bot_app.add_handler(CallbackQueryHandler(home, pattern='home'))
bot_app.add_handler(CallbackQueryHandler(total_users, pattern='total_users'))
bot_app.add_handler(CallbackQueryHandler(broadcast_callback, pattern='broadcast'))
bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

if __name__ == '__main__':
    init_db()
    
    # Start Flask thread
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Start bot with job queue for reminders
    print("✅ Bot Started! Developer: @T4HKR")
    print(f"👑 Admins: {ADMIN_IDS}")
    print(f"⏰ Reminders every {REMINDER_INTERVAL} minutes")
    print(f"📢 Channels: {CHANNEL_1}, {CHANNEL_2}, {CHANNEL_3}, {CHANNEL_4}")
    
    # Schedule reminders
    schedule_reminders(bot_app)
    
    bot_app.run_polling(allowed_updates=Update.ALL_TYPES)
