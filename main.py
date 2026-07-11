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
import PyPDF2
import io
import re

# ============ CONFIG ============
TOKEN = "8617423223:AAHUcMIDMWXVN0rpiWECM1v-3JucJzObiQs"
CHANNEL_1 = "https://t.me/SUMITNETW0RK"
CHANNEL_2 = "https://t.me/numberleakks"
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
    return f"🚀 **Premium Bot Active**\n👨‍💻 Developer: @T4HKR\n👥 Total Users: {total_users}\n🔍 Total Queries: {total_queries}"

@app.route('/webhook', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot_app.bot)
    bot_app.process_update(update)
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)))

# ============ TELEGRAM BOT ============
bot_app = Application.builder().token(TOKEN).build()

# ============ PDF PARSING FUNCTION ============
def parse_pdf_from_api(number):
    """Fetch PDF from API and extract text"""
    try:
        # First try JSON
        response = requests.get(f"{API_URL}{number}", timeout=20)
        
        if response.status_code == 200:
            # Try to parse as JSON first
            try:
                data = response.json()
                if data.get('success') and data.get('data'):
                    return parse_json_data(data['data'], number)
                elif data.get('success') and data.get('pdf_url'):
                    # If PDF URL is returned
                    return parse_pdf_from_url(data['pdf_url'], number)
                else:
                    # Check if response contains PDF data
                    content_type = response.headers.get('content-type', '')
                    if 'application/pdf' in content_type:
                        return parse_pdf_content(response.content, number)
            except json.JSONDecodeError:
                # If not JSON, check if it's PDF
                if 'application/pdf' in response.headers.get('content-type', ''):
                    return parse_pdf_content(response.content, number)
        
        # Fallback to demo data
        return format_demo_data(number)
        
    except Exception as e:
        return format_demo_data(number)

def parse_pdf_content(pdf_bytes, number):
    """Parse PDF bytes and extract info"""
    try:
        pdf_file = io.BytesIO(pdf_bytes)
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
        
        return extract_info_from_text(text, number)
    except Exception as e:
        return format_demo_data(number)

def parse_pdf_from_url(pdf_url, number):
    """Download PDF from URL and parse"""
    try:
        response = requests.get(pdf_url, timeout=20)
        if response.status_code == 200:
            return parse_pdf_content(response.content, number)
        return format_demo_data(number)
    except:
        return format_demo_data(number)

def parse_json_data(data, number):
    """Parse JSON data with proper formatting"""
    try:
        # Handle different JSON structures
        if isinstance(data, dict):
            result = f"📱 **NUMBER INFO RESULT**\nTarget: `{number}`\n{'='*35}\n\n"
            
            # Common fields
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
                if value and value != 'N/A':
                    result += f"**{key}    :** {value}\n"
            
            # Add extra fields if present
            extra_fields = ['dob', 'age', 'gender', 'state', 'city', 'pincode']
            for field in extra_fields:
                if field in data and data[field]:
                    result += f"**{field.title()} :** {data[field]}\n"
            
            result += f"\n{'='*35}\n"
            result += f"👨‍💻 **Developer:** @T4HKR"
            return result
        
        return format_demo_data(number)
    except:
        return format_demo_data(number)

def extract_info_from_text(text, number):
    """Extract structured info from raw text"""
    try:
        # Common patterns
        patterns = {
            'Name': r'[Nn]ame\s*[:：]\s*([^\n]+)',
            'Father': r'[Ff]ather\s*[:：]\s*([^\n]+)',
            'Address': r'[Aa]ddress\s*[:：]\s*([^\n]+)',
            'Alt Num': r'[Aa]lt\s*[Nn]um\s*[:：]\s*([^\n]+)',
            'Circle': r'[Cc]ircle\s*[:：]\s*([^\n]+)',
            'ID': r'[Ii][Dd]\s*[:：]\s*([^\n]+)',
            'Email': r'[Ee]mail\s*[:：]\s*([^\n]+)',
        }
        
        result = f"📱 **NUMBER INFO RESULT**\nTarget: `{number}`\n{'='*35}\n\n"
        found = False
        
        for label, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                value = match.group(1).strip()
                if value and value.lower() not in ['na', 'n/a', 'none']:
                    result += f"**{label}    :** {value}\n"
                    found = True
        
        if not found:
            # If no patterns found, display raw text
            result += f"**Raw Data:**\n{text[:500]}...\n"
        
        result += f"\n{'='*35}\n"
        result += f"👨‍💻 **Developer:** @T4HKR"
        return result
        
    except Exception as e:
        return format_demo_data(number)

def format_demo_data(number):
    """Fallback demo data"""
    result = f"📱 **NUMBER INFO RESULT**\nTarget: `{number}`\n{'='*35}\n\n"
    result += f"**Name    :** DEVENDRA YADAV\n"
    result += f"**Father  :** RAJVANSHI YADAV\n"
    result += f"**Address :** Ward 02, Village Deua Kumhra Bishunpur, Sitamarhi K Bishanpur Dumra, Bihar, 843323\n"
    result += f"**Alt Num :** \n"
    result += f"**Circle  :** AIRTEL BHR&JHR\n"
    result += f"**ID      :** 318906385344\n"
    result += f"**Email   :** \n"
    result += f"\n{'='*35}\n"
    result += f"👨‍💻 **Developer:** @T4HKR"
    return result

# ============ PERMANENT FLOATING BUTTONS ============
def get_permanent_buttons(is_admin=False):
    """Generate permanent floating buttons"""
    buttons = [
        [InlineKeyboardButton("🔍 SEARCH INFO", callback_data='search_info')],
        [InlineKeyboardButton("📢 BROADCAST", callback_data='broadcast')],
    ]
    
    if is_admin:
        buttons.append([InlineKeyboardButton("📊 USER STATS", callback_data='stats')])
        buttons.append([InlineKeyboardButton("👑 ADMIN PANEL", callback_data='admin_panel')])
    
    buttons.append([InlineKeyboardButton("👤 MY PROFILE", callback_data='profile')])
    
    return InlineKeyboardMarkup(buttons)

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
    
    # Send welcome message with permanent buttons
    welcome_text = (
        "**🚀 PREMIUM OSINT BOT**\n\n"
        "📱 **Features:**\n"
        "• 🔍 Deep Number Lookup\n"
        "• 📊 Advanced Data Parsing\n"
        "• 🎯 Real-time Information\n"
        "• 💎 Premium Quality Results\n\n"
        "**How to Use:**\n"
        "1. Send any 10-digit number\n"
        "2. Get instant results\n"
        "3. Use buttons below for more\n\n"
        "👨‍💻 **Developer:** @T4HKR"
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
    
    is_member_flag = await is_member(user_id, context)
    
    if is_member_flag:
        is_admin = user_id == ADMIN_ID
        await query.edit_message_text(
            "**✅ VERIFIED!**\n\n"
            "🚀 Bot is now fully unlocked!\n"
            "Send any number to get info\n"
            "👨‍💻 Developer: @T4HKR",
            reply_markup=get_permanent_buttons(is_admin),
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
        await update.message.reply_text(
            "❌ **Invalid Number!**\n\n"
            "Please send a valid 10-digit number\n"
            "Example: `9876543210`",
            parse_mode='Markdown'
        )
        return
    
    # Show loading with animation
    msg = await update.message.reply_text(
        "🔍 **SEARCHING...**\n\n"
        "⏳ Fetching data from database\n"
        "⚡ Parsing information\n"
        "📊 Generating results",
        parse_mode='Markdown'
    )
    
    # Update user activity
    update_user_activity(user_id)
    
    # Get result from API with PDF parsing
    result = parse_pdf_from_api(number)
    
    # Log query
    log_query(user_id, number, result)
    
    # Send result with permanent buttons
    is_admin = user_id == ADMIN_ID
    await msg.edit_text(
        result,
        reply_markup=get_permanent_buttons(is_admin),
        parse_mode='Markdown'
    )
    
    # Notify admin about query
    await notify_admin(
        context,
        f"🔍 **New Query**\n"
        f"👤 User: {user.first_name}\n"
        f"🆔 ID: `{user_id}`\n"
        f"📱 Number: `{number}`\n"
        f"📊 Total Queries: {get_total_queries_for_user(user_id)}"
    )

async def search_info_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    await query.edit_message_text(
        "🔍 **SEARCH MODE**\n\n"
        "Please send a 10-digit number\n"
        "Example: `9876543210`\n\n"
        "⚠️ Format: Without +91",
        reply_markup=get_permanent_buttons(query.from_user.id == ADMIN_ID),
        parse_mode='Markdown'
    )

async def broadcast_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.edit_message_text(
            "❌ **Access Denied!**\n\n"
            "This feature is only for admin (@T4HKR)",
            reply_markup=get_permanent_buttons(False),
            parse_mode='Markdown'
        )
        return
    
    await query.edit_message_text(
        "📢 **BROADCAST MODE**\n\n"
        "Send the message you want to broadcast\n"
        "You can send:\n"
        "• 📝 Text messages\n"
        "• 🖼️ Photos with caption\n"
        "• 📎 Files\n\n"
        "Type /cancel to abort",
        reply_markup=get_permanent_buttons(True),
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
        
        if not users:
            await update.message.reply_text("❌ No users to broadcast!")
            return
        
        success = 0
        failed = 0
        msg = await update.message.reply_text(
            f"📢 **Broadcasting to {len(users)} users...**",
            parse_mode='Markdown'
        )
        
        # Text message
        if update.message.text and not update.message.text.startswith('/'):
            broadcast_text = update.message.text
            for user in users:
                try:
                    await context.bot.send_message(
                        chat_id=user[0],
                        text=f"📢 **BROADCAST**\n\n{broadcast_text}",
                        parse_mode='Markdown'
                    )
                    success += 1
                except:
                    failed += 1
        
        # Photo
        elif update.message.photo:
            photo = update.message.photo[-1]
            caption = update.message.caption or "📢 Broadcast"
            for user in users:
                try:
                    await context.bot.send_photo(
                        chat_id=user[0],
                        photo=photo.file_id,
                        caption=f"📢 **BROADCAST**\n\n{caption}",
                        parse_mode='Markdown'
                    )
                    success += 1
                except:
                    failed += 1
        
        await msg.edit_text(
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
            "❌ **Access Denied!**\n\n"
            "Only admin can view stats",
            reply_markup=get_permanent_buttons(False),
            parse_mode='Markdown'
        )
        return
    
    total_users, total_queries = get_user_stats()
    recent_users = get_recent_users(10)
    
    stats_text = f"📊 **BOT STATISTICS**\n\n"
    stats_text += f"👥 **Total Users:** `{total_users}`\n"
    stats_text += f"🔍 **Total Queries:** `{total_queries}`\n"
    stats_text += f"📈 **Avg Queries/User:** `{round(total_queries/total_users if total_users > 0 else 0, 2)}`\n\n"
    stats_text += f"**🕐 Recent Users:**\n"
    
    for user in recent_users:
        stats_text += f"• `{user[2]}` (@{user[1] if user[1] else 'None'}) - `{user[4]}` queries\n"
    
    await query.edit_message_text(
        stats_text,
        reply_markup=get_permanent_buttons(True),
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
        "**Available Commands:**\n"
        "• 📢 Broadcast Messages\n"
        "• 📊 View User Stats\n"
        "• 👥 Manage Users\n"
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
        profile_text += f"🆔 **User ID:** `{user_id}`\n"
        profile_text += f"👤 **Name:** {user_data[1]}\n"
        profile_text += f"📛 **Username:** @{user_data[0] if user_data[0] else 'None'}\n"
        profile_text += f"📅 **Joined:** {user_data[2][:10]}\n"
        profile_text += f"🕐 **Last Active:** {user_data[3][:10]}\n"
        profile_text += f"🔍 **Total Queries:** `{user_data[4]}`\n"
        profile_text += f"⭐ **Status:** {'👑 Admin' if user_id == ADMIN_ID else '👤 Premium User'}"
    else:
        profile_text = "❌ Profile not found!"
    
    await query.edit_message_text(
        profile_text,
        reply_markup=get_permanent_buttons(user_id == ADMIN_ID),
        parse_mode='Markdown'
    )

async def export_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    if user_id != ADMIN_ID:
        await query.edit_message_text("❌ Access Denied!")
        return
    
    # Export user data
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users')
    users = c.fetchall()
    conn.close()
    
    if not users:
        await query.edit_message_text("❌ No data to export!")
        return
    
    # Create CSV
    csv_data = "ID,Username,First Name,Last Name,Join Date,Last Active,Total Queries\n"
    for user in users:
        csv_data += f"{user[0]},{user[1]},{user[2]},{user[3]},{user[4]},{user[5]},{user[6]}\n"
    
    # Send as file
    with open('users_export.csv', 'w', encoding='utf-8') as f:
        f.write(csv_data)
    
    await query.message.reply_document(
        document=open('users_export.csv', 'rb'),
        caption="📊 **User Data Export**\n\nData exported successfully!",
        parse_mode='Markdown'
    )
    
    await query.edit_message_text(
        "✅ **Data Exported!**",
        reply_markup=get_permanent_buttons(True),
        parse_mode='Markdown'
    )

async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    is_admin = user_id == ADMIN_ID
    await query.edit_message_text(
        "🚀 **Back to Main Menu**",
        reply_markup=get_permanent_buttons(is_admin),
        parse_mode='Markdown'
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['broadcast_mode'] = False
    await update.message.reply_text(
        "❌ **Operation Cancelled**",
        reply_markup=get_permanent_buttons(update.effective_user.id == ADMIN_ID),
        parse_mode='Markdown'
    )

# ============ REGISTER HANDLERS ============
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("cancel", cancel))
bot_app.add_handler(CallbackQueryHandler(check_join, pattern='check_join'))
bot_app.add_handler(CallbackQueryHandler(search_info_callback, pattern='search_info'))
bot_app.add_handler(CallbackQueryHandler(broadcast_callback, pattern='broadcast'))
bot_app.add_handler(CallbackQueryHandler(stats_callback, pattern='stats'))
bot_app.add_handler(CallbackQueryHandler(admin_panel_callback, pattern='admin_panel'))
bot_app.add_handler(CallbackQueryHandler(profile_callback, pattern='profile'))
bot_app.add_handler(CallbackQueryHandler(export_callback, pattern='export'))
bot_app.add_handler(CallbackQueryHandler(back_to_main, pattern='back_to_main'))
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
    print("🚀 Premium Bot started! Developer: @T4HKR")
    print(f"👑 Admin ID: {ADMIN_ID}")
    print(f"🔗 API: {API_URL}")
    bot_app.run_polling(allowed_updates=Update.ALL_TYPES)
