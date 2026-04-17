import telebot
from telebot import types
import threading
from flask import Flask

# SERVERI I VOGËL PËR RENDER (FALAS)
app = Flask('')
@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# KONFIGURIMI I BOTIT
TOKEN = "8621899161:AAHhl4jLg5Ntvv4oLc1qe6NV88KJFP4hkPU"
ADMIN_ID = "6190547024" 
bot = telebot.TeleBot(TOKEN)
bot.remove_webhook()

CHANNELS = {
    "Zürich": "-1003898417751", "Basel": "-1003718494977",
    "Solothurn": "-1003967254117", "Bern": "-1003959656124",
    "St. Gallen": "-1003808639054"
}
user_posts = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "👋 Willkommen! Senden Sie Ihren Text.", reply_markup=markup)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text.startswith('/'): return
    user_posts[message.chat.id] = message.text
    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(text=f"{k} 🇨🇭", callback_data=f"sel_{k}") for k in CHANNELS.keys()]
    markup.add(*btns)
    bot.send_message(message.chat.id, "📍 Stadt wählen:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sel_"))
def preview(call):
    kanton = call.data.replace("sel_", "")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Ja ✅", callback_data=f"pub_{kanton}"),
               types.InlineKeyboardButton("Nein ❌", callback_data="cancel"))
    bot.edit_message_text(f"📌 Posten in {kanton}?\n\n{user_posts.get(call.message.chat.id)}", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pub_") or call.data == "cancel")
def final(call):
    if call.data == "cancel":
        bot.edit_message_text("❌ Abgebrochen.", call.message.chat.id, call.message.message_id)
        return
    kanton = call.data.replace("pub_", "")
    try:
        bot.send_message(CHANNELS[kanton], user_posts[call.message.chat.id])
        bot.edit_message_text(f"✅ Gepostet in {kanton}!", call.message.chat.id, call.message.message_id)
    except:
        bot.edit_message_text(f"❌ Error: Admin?", call.message.chat.id, call.message.message_id)

# NISJA E TË DYJAVE (SERVERI + BOTI)
if __name__ == "__main__":
    t = threading.Thread(target=run_flask)
    t.start()
    bot.infinity_polling(skip_pending=True)
