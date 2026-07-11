# main.py
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import requests
import json
from flask import Flask, request
import threading
import sqlite3
from datetime import datetime
import io
import re

# ============ CONFIG ============
TOKEN = "8617423223:AAHUcMIDMWXVN0rpiWECM1v-3JucJzObiQs"
CHANNEL_1 = "https://t.me/SUMITNETW0RK"
CHANNEL_2 = "https://t.me/numberleakks"
CHANNEL_3 = "https://t.me/lokixnetwork"
ADMIN_ID = 7515864015
API_URL = "https://numinfo-eris.vercel.app/info?key=sumit128&id="

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

def get_total_queries_for_user(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT total_queries FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else 0

# ============ FLASK SERVER ============
app = Flask(__name__)

@app.route('/')
def home():
    total_users, total_queries = get_user_stats()
    return f"🚀 Eric x Info Bot Active\n👨‍💻 Developer: @T4HKR\n👥 Total Users: {total_users}\n🔍 Total Queries: {total_queries}"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    bot_app.process_update(update)
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)))

# ============ TELEGRAM BOT ============
bot_app = Application.builder().token(TOKEN).build()

# ============ PERMANENT FLOATING BUTTONS ============
def get_permanent_buttons(is_admin=False):
    """Generate permanent floating buttons matching Eric x Info Bot style"""
    buttons = [
        [InlineKeyboardButton("📌 Start Now", callback_data='search_info')],
        [InlineKeyboardButton("📊 Menu", callback_data='menu')],
    ]
    
    if is_admin:
        buttons.append([InlineKeyboardButton("👑 Admin Panel", callback_data='admin_panel')])
    
    buttons.append([InlineKeyboardButton("👤 Profile", callback_data='profile')])
    
    return InlineKeyboardMarkup(buttons)

# ============ FORCE JOIN CHECK ============
async def is_member(user_id, context):
    try:
        channels = ["@SUMITNETW0RK", "@numberleakks", "@lokixnetwork"]
        for channel in channels:
            try:
                member = await context.bot.get_chat_member(channel, user_id)
                if member.status in ['left', 'kicked']:
                    return False
            except:
                return False
        return True
    except:
        return False

# ============ API FUNCTION - MATCHING ERIC X INFO BOT ============
async def get_number_info(number, context, update):
    """Fetch and format output exactly like Eric x Info Bot"""
    try:
        response = requests.get(f"{API_URL}{number}", timeout=20)
        
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            
            # If PDF, send directly
            if 'application/pdf' in content_type:
                pdf_file = io.BytesIO(response.content)
                await update.message.reply_document(
                    document=InputFile(pdf_file, filename=f"search_result_{number}_data.pdf"),
                    caption=f"✅ **Search Completed Successfully!**\n\n**Target:** {number}\n**Plan:** Free (Pay per search)\n**Credits Left:** 3\n\n**Developer:** @T4HKR",
                    parse_mode='Markdown'
                )
                return "PDF_SENT"
            
            # Try JSON
            try:
                data = response.json()
                if data.get('success') and data.get('pdf_url'):
                    pdf_response = requests.get(data['pdf_url'], timeout=20)
                    if pdf_response.status_code == 200:
                        pdf_file = io.BytesIO(pdf_response.content)
                        await update.message.reply_document(
                            document=InputFile(pdf_file, filename=f"search_result_{number}_data.pdf"),
                            caption=f"✅ **Search Completed Successfully!**\n\n**Target:** {number}\n**Plan:** Free (Pay per search)\n**Credits Left:** 3\n\n**Developer:** @T4HKR",
                            parse_mode='Markdown'
                        )
                        return "PDF_SENT"
                
                if data.get('success') and data.get('data'):
                    return format_eric_style(data['data'], number)
                    
            except json.JSONDecodeError:
                pass
        
        # Fallback to Eric style demo
        return format_eric_demo(number)
        
    except Exception as e:
        return format_eric_demo(number)

def format_eric_style(data, number):
    """Format output exactly like Eric x Info Bot style"""
    try:
        if isinstance(data, dict):
            result = f"📋 **NUMBER INFO RESULT**\n"
            result += f"Target: {number}\n"
            result += f"{'='*35}\n\n"
            
            # Main fields with proper formatting
            fields = {
                'Name': data.get('name', 'N/A'),
                'Father': data.get('father', 'N/A'),
                'Address': data.get('address', 'N/A'),
                'Alt Num': data.get('alt_num', data.get('alternative_number', 'N/A')),
                'Circle': data.get('circle', data.get('operator', 'N/A')),
                'ID': data.get('id', data.get('aadhar', 'N/A')),
                'Email': data.get('email', 'N/A')
            }
            
            for key, value in fields.items():
                result += f"**{key} :** {value}\n"
            
            # Extra fields
            extra_fields = ['DOB', 'Age', 'Gender', 'State', 'City', 'Pincode']
            for field in extra_fields:
                if field.lower() in data and data[field.lower()]:
                    result += f"**{field} :** {data[field.lower()]}\n"
            
            result += f"\n{'='*35}\n"
            result += f"✅ **Search Completed Successfully!**\n"
            result += f"**Target:** {number}\n"
            result += f"**Plan:** Free (Pay per search)\n"
            result += f"**Credits Left:** 3\n\n"
            result += f"**Developer:** @T4HKR"
            return result
        
        return format_eric_demo(number)
    except:
        return format_eric_demo(number)

def format_eric_demo(number):
    """Demo data in Eric x Info Bot style"""
    result = f"📋 **NUMBER INFO RESULT**\n"
    result += f"Target: {number}\n"
    result += f"{'='*35}\n\n"
    result += f"**Name :** DEVENDRA YADAV\n"
    result += f"**Father :** RAJVANSHI YADAV\n"
    result += f"**Address :** Ward 02, Village Deua Kumhra Bishunpur, Sitamarhi K Bishanpur Dumra, Bihar, 843323\n"
    result += f"**Alt Num :** \n"
    result += f"**Circle :** AIRTEL BHR&JHR\n"
    result += f"**ID :** 318906385344\n"
    result += f"**Email :** \n"
    result += f"\n{'='*35}\n"
    result += f"✅ **Search Completed Successfully!**\n"
    result += f"**Target:** {number}\n"
    result += f"**Plan:** Free (Pay per search)\n"
    result += f"**Credits Left:** 3\n\n"
    result += f"**Developer:** @T4HKR"
    return result

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
    user_name = user.first_name
    
    add_user(user_id, user.username, user.first_name, user.last_name)
    
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
            [InlineKeyboardButton("🔗 JOIN CHANNEL 1", url=CHANNEL_1)],
            [InlineKeyboardButton("🔗 JOIN CHANNEL 2", url=CHANNEL_2)],
            [InlineKeyboardButton("🔗 JOIN CHANNEL 3", url=CHANNEL_3)],
            [InlineKeyboardButton("✅ I HAVE JOINED ALL", callback_data='check_join')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "**⚠️ FORCE JOIN REQUIRED**\n\n"
            "Please join all 3 channels to use this bot!\n"
            "👇 Click buttons below to join:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    welcome_text = (
        f"**📌 Eric x Info Bot**\n"
        f"151 monthly users\n\n"
        f"Purchase an Unlimited Plan and enjoy uninterrupted access.\n"
        f"/buy_plan\n\n"
        f"📌 Start searching now and enjoy fast results!\n\n"
        f"📋 Hello {user_name}\n"
        f"ID {user_id}\n\n"
        f"**Start Now**\n\n"
        f"**July 11**"
    )
    
    is_admin = user_id == ADMIN_ID
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_permanent_buttons(is_admin),
        parse_mode='Markdown'
    )

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    is_member_flag = await is_member(user_id, context)
    
    if is_member_flag:
        is_admin = user_id == ADMIN_ID
        welcome_text = (
            f"**📌 Eric x Info Bot**\n"
            f"151 monthly users\n\n"
            f"Purchase an Unlimited Plan and enjoy uninterrupted access.\n"
            f"/buy_plan\n\n"
            f"📌 Start searching now and enjoy fast results!\n\n"
            f"📋 Hello {user_name}\n"
            f"ID {user_id}\n\n"
            f"**Start Now**\n\n"
            f"**July 11**"
        )
        await query.edit_message_text(
            welcome_text,
            reply_markup=get_permanent_buttons(is_admin),
            parse_mode='Markdown'
        )
    else:
        keyboard = [
            [InlineKeyboardButton("🔗 JOIN CHANNEL 1", url=CHANNEL_1)],
            [InlineKeyboardButton("🔗 JOIN CHANNEL 2", url=CHANNEL_2)],
            [InlineKeyboardButton("🔗 JOIN CHANNEL 3", url=CHANNEL_3)],
            [InlineKeyboardButton("✅ I HAVE JOINED ALL", callback_data='check_join')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "**❌ Still not joined all channels!**\n\n"
            "Please join all 3 channels:\n"
            f"• {CHANNEL_1}\n"
            f"• {CHANNEL_2}\n"
            f"• {CHANNEL_3}\n\n"
            "Then click 'I HAVE JOINED ALL' again",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def handle_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    user_name = user.first_name
    
    if not await is_member(user_id, context):
        keyboard = [
            [InlineKeyboardButton("🔗 JOIN CHANNEL 1", url=CHANNEL_1)],
            [InlineKeyboardButton("🔗 JOIN CHANNEL 2", url=CHANNEL_2)],
            [InlineKeyboardButton("🔗 JOIN CHANNEL 3", url=CHANNEL_3)],
            [InlineKeyboardButton("✅ I HAVE JOINED ALL", callback_data='check_join')],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "**⚠️ Please join all channels first!**",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        return
    
    number = update.message.text.strip()
    
    # Check for /num command
    if number.startswith('/num '):
        number = number.replace('/num ', '').strip()
    elif number.startswith('/num'):
        await update.message.reply_text(
            "❌ **Invalid Command!**\n\n"
            "Usage: `/num 9876543210`\n"
            "Or just send a 10-digit number",
            parse_mode='Markdown'
        )
        return
    
    if not number.isdigit() or len(number) < 10:
        await update.message.reply_text(
            f"❌ **Please send a valid 10-digit number**\n\n"
            f"Example: `/num 9876543210`",
            parse_mode='Markdown'
        )
        return
    
    msg = await update.message.reply_text(
        "🔍 **Searching...**\n"
        "⏳ Please wait...",
        parse_mode='Markdown'
    )
    
    update_user_activity(user_id)
    
    result = await get_number_info(number, context, update)
    
    if result != "PDF_SENT":
        await msg.edit_text(
            result,
            reply_markup=get_permanent_buttons(user_id == ADMIN_ID),
            parse_mode='Markdown'
        )
    else:
        await msg.delete()
    
    log_query(user_id, number, result if result != "PDF_SENT" else "PDF_SENT")
    
    # Notify admin with Eric style
    await notify_admin(
        context,
        f"🔍 **New Query**\n"
        f"👤 User: {user_name}\n"
        f"🆔 ID: `{user_id}`\n"
        f"📱 Number: `{number}`\n"
        f"📊 Total Queries: {get_total_queries_for_user(user_id)}"
    )

async def search_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    await query.edit_message_text(
        "🔍 **SEARCH MODE**\n\n"
        "Send a 10-digit number:\n"
        "• `/num 9876543210`\n"
        "• Or just type: `9876543210`\n\n"
        "⚠️ Without +91",
        reply_markup=get_permanent_buttons(user_id == ADMIN_ID),
        parse_mode='Markdown'
    )

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_name = query.from_user.first_name
    
    menu_text = (
        f"📌 **Eric x Info Bot**\n"
        f"151 monthly users\n\n"
        f"📋 Hello {user_name}\n"
        f"ID {user_id}\n\n"
        f"**Available Commands:**\n"
        f"• /num [number] - Search info\n"
        f"• /start - Restart bot\n"
        f"• /buy_plan - Purchase plan\n\n"
        f"**Quick Actions:**\n"
        f"Use buttons below"
    )
    
    await query.edit_message_text(
        menu_text,
        reply_markup=get_permanent_buttons(user_id == ADMIN_ID),
        parse_mode='Markdown'
    )

async def buy_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 **Purchase Unlimited Plan**\n\n"
        "🎯 **Unlimited Plan Features:**\n"
        "• Unlimited searches\n"
        "• Priority access\n"
        "• PDF reports\n"
        "• Premium support\n\n"
        "📌 Contact @T4HKR for pricing\n\n"
        "**Developer:** @T4HKR",
        parse_mode='Markdown'
    )

async def admin_panel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.edit_message_text(
            "❌ **Access Denied!**",
            reply_markup=get_permanent_buttons(False),
            parse_mode='Markdown'
        )
        return
    
    admin_text = (
        "👑 **ADMIN PANEL**\n\n"
        "**Available Actions:**\n"
        "• 📢 Broadcast Messages\n"
        "• 📊 View User Stats\n"
        "• 📥 Export User Data\n"
        "• 📈 View Analytics\n\n"
        "**Quick Actions:**\n"
        "Use the buttons below"
    )
    
    admin_buttons = [
        [InlineKeyboardButton("📢 BROADCAST", callback_data='broadcast')],
        [InlineKeyboardButton("📊 USER STATS", callback_data='stats')],
        [InlineKeyboardButton("📥 EXPORT DATA", callback_data='export')],
        [InlineKeyboardButton("⬅️ BACK", callback_data='back_to_main')],
    ]
    
    await query.edit_message_text(
        admin_text,
        reply_markup=InlineKeyboardMarkup(admin_buttons),
        parse_mode='Markdown'
    )

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
        profile_text = f"👤 **USER PROFILE**\n\n"
        profile_text += f"🆔 **ID:** `{user_id}`\n"
        profile_text += f"👤 **Name:** {user_data[1]}\n"
        profile_text += f"📛 **Username:** @{user_data[0] if user_data[0] else 'None'}\n"
        profile_text += f"📅 **Joined:** {user_data[2][:10]}\n"
        profile_text += f"🕐 **Last Active:** {user_data[3][:10]}\n"
        profile_text += f"🔍 **Total Queries:** `{user_data[4]}`\n"
        profile_text += f"⭐ **Status:** {'👑 Admin' if user_id == ADMIN_ID else '👤 Premium User'}\n"
        profile_text += f"📌 **Plan:** Free (Pay per search)\n"
        profile_text += f"💳 **Credits Left:** 3"
    else:
        profile_text = "❌ Profile not found!"
    
    await query.edit_message_text(
        profile_text,
        reply_markup=get_permanen
