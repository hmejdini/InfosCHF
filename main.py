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

# LISTA E QYTETEVE TË ZVICRËS
CHANNELS = {
    "Zürich 🇨🇭": "-1003898417751",
    "Solothurn 🇨🇭": "-1003967254117",
    "Basel 🇨🇭": "-1003718494977",
    "St. Gallen 🇨🇭": "-1003808639054",
    "Bern 🇨🇭": "-1003959656124"
}

user_data = {}

# --- 3. KOMANDA /START ---
@bot.message_handler(commands=['start'])
def welcome(message):
    user_data.pop(message.chat.id, None)
    welcome_msg = (
        "👋 **Willkommen bei InfoStrasse Switzerland!**\n\n"
        "Hier können Sie Strassenzustände anonym melden.\n\n"
        "👉 **Bitte senden Sie uns jetzt Ihr Foto, Video oder Ihre Nachricht.**"
    )
    bot.send_message(message.chat.id, welcome_msg, parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())

# --- 4. MARRJA E LAJMIT ---
@bot.message_handler(content_types=['text', 'photo', 'video'])
def collect_report(message):
    user_id = message.chat.id
    
    # Injoro klikimet e butonave si mesazhe të reja
    if message.text in list(CHANNELS.keys()) or message.text in ["Ja, posten ✅", "Nein, Fehler korrigieren ❌"]:
        return

    user_data[user_id] = {'msg': message}

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    buttons = [types.KeyboardButton(name) for name in CHANNELS.keys()]
    markup.add(*buttons)
    
    bot.send_message(user_id, "📍 In welcher Stadt möchten Sie dies veröffentlichen?", reply_markup=markup)

# --- 5. ZGJEDHJA E QYTETIT + PREVIEW DHE KONFIRMIMI ---
@bot.message_handler(func=lambda message: message.text in CHANNELS.keys())
def handle_channel_selection(message):
    user_id = message.chat.id
    if user_id in user_data:
        user_data[user_id]['target_channel'] = CHANNELS[message.text]
        user_data[user_id]['channel_name'] = message.text
        
        original_msg = user_data[user_id]['msg']
        
        # Butonat e konfirmimit
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add(types.KeyboardButton("Ja, posten ✅"), types.KeyboardButton("Nein, Fehler korrigieren ❌"))
        
        bot.send_message(user_id, f"📝 **Vorschau für {message.text}:**", parse_mode="Markdown")
        
        # Shfaqja e preview me mbrojtje nga gabimet
        try:
            if original_msg.content_type == 'text':
                bot.send_message(user_id, f"_{original_msg.text}_", parse_mode="Markdown")
            elif original_msg.content_type == 'photo':
                bot.send_photo(user_id, original_msg.photo[-1].file_id, caption=original_msg.caption)
            elif original_msg.content_type == 'video':
                bot.send_video(user_id, original_msg.video.file_id, caption=original_msg.caption)
        except Exception as e:
            print(f"Preview error: {e}")

        # Kjo pyetje aktivizon butonat e konfirmimit poshtë
        bot.send_message(user_id, "Soll dieser Beitrag veröffentlicht werden?", reply_markup=markup)

# --- 6. KONFIRMIMI FINAL DHE POSTIMI ---
@bot.message_handler(func=lambda message: message.text in ["Ja, posten ✅", "Nein, Fehler korrigieren ❌"])
def handle_final_confirmation(message):
    user_id = message.chat.id
    data = user_data.get(user_id)

    if not data or 'target_channel' not in data:
        bot.send_message(user_id, "Bitte starten Sie mit /start neu.", reply_markup=types.ReplyKeyboardRemove())
        return

    if message.text == "Ja, posten ✅":
        try:
            target = data['target_channel']
            msg = data['msg']
            
            # Postimi real në kanal
            if msg.content_type == 'text':
                bot.send_message(target, msg.text)
            elif msg.content_type == 'photo':
                bot.send_photo(target, msg.photo[-1].file_id, caption=msg.caption)
            elif msg.content_type == 'video':
                bot.send_video(target, msg.video.file_id, caption=msg.caption)
            
            bot.send_message(user_id, f"✅ Erfolgreich in **{data['channel_name']}** gepostet!", reply_markup=types.ReplyKeyboardRemove())
        except Exception as e:
            bot.send_message(user_id, "❌ Fehler: Der Bot ist kein Admin in diesem Kanal.")
            print(f"Post error: {e}")
    else:
        bot.send_message(user_id, "❌ Vorgang abgebrochen.", reply_markup=types.ReplyKeyboardRemove())

    user_data.pop(user_id, None)

if __name__ == "__main__":
    keep_alive()
    bot.remove_webhook()
    bot.infinity_polling(skip_pending=True)
