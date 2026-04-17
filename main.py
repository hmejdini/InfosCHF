import telebot
from telebot import types
from flask import Flask
from threading import Thread
import os

# --- 1. SERVERI PËR RENDER ---
app = Flask('')
@app.route('/')
def home(): return "InfoStrasse Bot ist LIVE!"

def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    Thread(target=run).start()

# --- 2. KONFIGURIMI I BOTIT ---
TOKEN = "8621899161:AAEqoto5KAVDRO0oAaQE6qLSGzva4t4fNU8"
bot = telebot.TeleBot(TOKEN)

# LISTA E KANALEVE (VETËM ZVICRA)
CHANNELS = {
    "Zürich 🇨🇭": "-1003898417751",
    "Solothurn 🇨🇭": "-1003967254117",
    "Basel 🇨🇭": "-1003718494977",
    "St. Gallen 🇨🇭": "-1003808639054",
    "Bern 🇨🇭": "-1003959656124"
}

user_data = {}

# --- 3. KOMANDA /START (Gjermanisht) ---
@bot.message_handler(commands=['start'])
def welcome(message):
    welcome_msg = (
        "👋 **Willkommen bei InfoStrasse Switzerland!**\n\n"
        "Mit diesem Bot können Sie Strassenzustände **ANONYM** melden.\n"
        "Wählen Sie die Stadt aus, in der Sie posten möchten, nachdem Sie Ihre Nachricht gesendet haben.\n\n"
        "👉 **Senden Sie jetzt** Ihre Nachricht, Ihr Foto oder Ihr Video."
    )
    bot.send_message(message.chat.id, welcome_msg, parse_mode="Markdown")

# --- 4. MARRJA E LAJMIT ---
@bot.message_handler(content_types=['text', 'photo', 'video'])
def collect_report(message):
    user_id = message.chat.id
    if message.text in list(CHANNELS.keys()) + ["Ja, posten ✅", "Nein, Fehler korrigieren ❌"]:
        return

    user_data[user_id] = {'msg': message}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [types.KeyboardButton(name) for name in CHANNELS.keys()]
    markup.add(*buttons)
    
    bot.send_message(user_id, "📍 In welchem Kanal möchten Sie diese Nachricht anonym veröffentlichen?", reply_markup=markup)

# --- 5. ZGJEDHJA E QYTETIT ---
@bot.message_handler(func=lambda message: message.text in CHANNELS.keys())
def handle_channel_selection(message):
    user_id = message.chat.id
    if user_id in user_data:
        user_data[user_id]['target_channel'] = CHANNELS[message.text]
        user_data[user_id]['channel_name'] = message.text
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("Ja, posten ✅", "Nein, Fehler korrigieren ❌")
        
        bot.send_message(user_id, f"Ausgewählt: **{message.text}**\n\nSind Sie sicher?", reply_markup=markup, parse_mode="Markdown")

# --- 6. KONFIRMIMI DHE POSTIMI ---
@bot.message_handler(func=lambda message: message.text in ["Ja, posten ✅", "Nein, Fehler korrigieren ❌"])
def handle_final_confirmation(message):
    user_id = message.chat.id
    data = user_data.get(user_id)

    if not data or 'target_channel' not in data:
        bot.send_message(user_id, "Bitte senden Sie die Nachricht erneut.", reply_markup=types.ReplyKeyboardRemove())
        return

    if message.text == "Ja, posten ✅":
        try:
            target = data['target_channel']
            msg = data['msg']
            
            if msg.content_type == 'text':
                bot.send_message(target, msg.text)
            elif msg.content_type == 'photo':
                bot.send_photo(target, msg.photo[-1].file_id, caption=msg.caption)
            elif msg.content_type == 'video':
                bot.send_video(target, msg.video.file_id, caption=msg.caption)
            
            bot.send_message(user_id, f"✅ Ihr Beitrag wurde anonym in {data['channel_name']} veröffentlicht!", reply_markup=types.ReplyKeyboardRemove())
        except Exception as e:
            bot.send_message(user_id, "❌ Fehler: Der Bot ist kein Admin in diesem Kanal.")
    else:
        bot.send_message(user_id, "❌ Post abgebrochen.", reply_markup=types.ReplyKeyboardRemove())

    user_data.pop(user_id, None)

if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
