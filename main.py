import telebot
from telebot import types
from flask import Flask
from threading import Thread
import os

# --- 1. SERVERI PËR RENDER ---
app = Flask('')
@app.route('/')
def home(): return "Boti Infos Road Switzerland është LIVE!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# --- 2. KONFIGURIMI I BOTIT ---
TOKEN = "8621899161:AAEqoto5KAVDRO0oAaQE6qLSGzva4t4fNU8"
ADMIN_ID = 7888974036
bot = telebot.TeleBot(TOKEN)

# LISTA E RE E KANALEVE (Vendos ID-të e sakta këtu)
CHANNELS = {
    "Zürich 🇨🇭": "-100XXXXXXXXXX",
    "Solothurn 🇨🇭": "-100XXXXXXXXXX",
    "Basel 🇨🇭": "-100XXXXXXXXXX",
    "St. Gallen 🇨🇭": "-100XXXXXXXXXX",
    "Macedonia 🛣️": "-1002447915570"  # Mbajta një nga qytetet e vjetra si shembull
}

user_data = {}

# --- 3. KOMANDA /START ---
@bot.message_handler(commands=['start'])
def welcome(message):
    welcome_msg = (
        "👋 **Mirësevini!**\n\n"
        "Ky bot ju lejon të raportoni gjendjen në rrugë në mënyrë **ANONIME**.\n"
        "Zgjidhni qytetin ku dëshironi të postoni pasi të dërgoni lajmin.\n\n"
        "👉 **Dërgoni tani** mesazhin, foton ose videon tuaj."
    )
    bot.send_message(message.chat.id, welcome_msg, parse_mode="Markdown")

# --- 4. MARRJA E LAJMIT ---
@bot.message_handler(content_types=['text', 'photo', 'video'])
def collect_report(message):
    user_id = message.chat.id
    if message.text in list(CHANNELS.keys()) + ["Po, posto-je ✅", "Jo, kam bërë gabim ❌"]:
        return

    user_data[user_id] = {'msg': message}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [types.KeyboardButton(name) for name in CHANNELS.keys()]
    markup.add(*buttons)
    
    bot.send_message(user_id, "📍 Në cilin qytet dëshironi ta publikoni këtë lajm?", reply_markup=markup)

# --- 5. ZGJEDHJA E QYTETIT ---
@bot.message_handler(func=lambda message: message.text in CHANNELS.keys())
def handle_channel_selection(message):
    user_id = message.chat.id
    if user_id in user_data:
        user_data[user_id]['target_channel'] = CHANNELS[message.text]
        user_data[user_id]['channel_name'] = message.text
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Po, posto-je ✅", "Jo, kam bërë gabim ❌")
        
        bot.send_message(user_id, f"Zgjodhët: **{message.text}**\n\nA jeni i sigurt?", reply_markup=markup, parse_mode="Markdown")

# --- 6. KONFIRMIMI DHE POSTIMI ---
@bot.message_handler(func=lambda message: message.text in ["Po, posto-je ✅", "Jo, kam bërë gabim ❌"])
def handle_final_confirmation(message):
    user_id = message.chat.id
    data = user_data.get(user_id)

    if not data or 'target_channel' not in data:
        bot.send_message(user_id, "Gabim. Dërgoni lajmin përsëri.", reply_markup=types.ReplyKeyboardRemove())
        return

    if message.text == "Po, posto-je ✅":
        try:
            target = data['target_channel']
            msg = data['msg']
            
            if msg.content_type == 'text':
                bot.send_message(target, msg.text)
            elif msg.content_type == 'photo':
                bot.send_photo(target, msg.photo[-1].file_id, caption=msg.caption)
            elif msg.content_type == 'video':
                bot.send_video(target, msg.video.file_id, caption=msg.caption)
            
            bot.send_message(user_id, f"✅ U publikua në {data['channel_name']}!", reply_markup=types.ReplyKeyboardRemove())
        except Exception as e:
            bot.send_message(user_id, "❌ Boti nuk është admin në këtë kanal.")
    else:
        bot.send_message(user_id, "❌ Postimi u anulua.", reply_markup=types.ReplyKeyboardRemove())

    user_data.pop(user_id, None)

if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
