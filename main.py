import telebot
from telebot import types
import threading
from flask import Flask
import os

# SERVERI I VOGËL PËR RENDER
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    # Render përdor portin 10000 ose atë që i jep sistemi
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# KONFIGURIMI I BOTIT
TOKEN = "8621899161:AAHhl4jLg5Ntvv4oLc1qe6NV88KJFP4hkPU"
ADMIN_ID = "6190547024" 
bot = telebot.TeleBot(TOKEN)

# KJO ËSHTË E RËNDËSISHME: Pastron lidhjet e vjetra
bot.remove_webhook()

CHANNELS = {
    "Zürich": "-1003898417751", "Basel": "-1003718494977",
    "Solothurn": "-1003967254117", "Bern": "-1003959656124",
    "St. Gallen": "-1003808639054"
}
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "👋 Willkommen! Bitte senden Sie Ihren Text (Strassenzustand).", reply_markup=markup)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text.startswith('/'): return
    
    user_data[message.chat.id] = message.text
    
    # Njoftimi Adminit me të dhëna të plota
    u = message.from_user
    bot.send_message(ADMIN_ID, f"📩 **Tentativë e re**\n👤 {u.first_name} {u.last_name or ''} (@{u.username})\n📝 {message.text}")

    # Fshirja e tastierës dhe shfaqja e qyteteve
    msg = bot.send_message(message.chat.id, "📍 Bitte wählen...", reply_markup=types.ReplyKeyboardRemove())
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(text=f"{k} 🇨🇭", callback_data=f"sel_{k}") for k in CHANNELS.keys()]
    markup.add(*btns)
    
    bot.edit_message_text("📍 In welcher Stadt posten?", message.chat.id, msg.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    chat_id = call.message.chat.id
    u = call.from_user
    
    if call.data.startswith("sel_"):
        kanton = call.data.replace("sel_", "")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("Ja ✅", callback_data=f"pub_{kanton}"),
                   types.InlineKeyboardButton("Nein ❌", callback_data="cancel"))
        bot.edit_message_text(f"📌 Posten in {kanton}?\n\n{user_data.get(chat_id)}", chat_id, call.message.message_id, reply_markup=markup)
        
    elif call.data == "cancel":
        bot.edit_message_text("❌ Abgebrochen.", chat_id, call.message.message_id)
        bot.send_message(ADMIN_ID, f"🚫 {u.first_name} e anuloi.")
        
    elif call.data.startswith("pub_"):
        kanton = call.data.replace("pub_", "")
        try:
            bot.send_message(CHANNELS[kanton], user_data[chat_id])
            bot.edit_message_text(f"✅ Gepostet in {kanton}!", chat_id, call.message.message_id)
            bot.send_message(ADMIN_ID, f"✅ {u.first_name} (@{u.username}) postoi në {kanton}.")
        except:
            bot.edit_message_text("❌ Error: Bot Jo Admin!", chat_id, call.message.message_id)

if __name__ == "__main__":
    # Nisim serverin që Render të shohë "pika të gjelbër"
    threading.Thread(target=run_flask).start()
    # Nisim botin me skip_pending që të mos bllokohet nga mesazhet e vjetra
    bot.infinity_polling(skip_pending=True)
