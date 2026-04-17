import telebot
from telebot import types
import threading
from flask import Flask

# SERVERI PËR RENDER (Versioni FALAS)
app = Flask('')
@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# KONFIGURIMI
TOKEN = "8621899161:AAHhl4jLg5Ntvv4oLc1qe6NV88KJFP4hkPU"
ADMIN_ID = "6190547024" 
bot = telebot.TeleBot(TOKEN)
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
    
    # Ruajmë tekstin
    user_data[message.chat.id] = message.text
    
    # Të dhënat e përdoruesit
    name = message.from_user.first_name or ""
    surname = message.from_user.last_name or ""
    username = f"@{message.from_user.username}" if message.from_user.username else "Nuk ka username"
    
    # 1. NJOFTIMI I PARË: Dikush po shkruan
    admin_info = (f"📩 **Mesazh i ri (Tentativë)**\n"
                  f"👤 Nga: {name} {surname} ({username})\n"
                  f"📝 Teksti: {message.text}")
    bot.send_message(ADMIN_ID, admin_info)

    # 2. FSHIRJA E TASTIERËS DHE SHFAQJA E QYTETEVE
    # Përdorim një mesazh të ri për të hequr tastierën dhe dërguar butonat inline
    remove_kb = types.ReplyKeyboardRemove()
    temp_msg = bot.send_message(message.chat.id, "📍 Bitte wählen Sie die Stadt:", reply_markup=remove_kb)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(text=f"{k} 🇨🇭", callback_data=f"sel_{k}") for k in CHANNELS.keys()]
    markup.add(*btns)
    
    # Redaktojmë mesazhin e mësipërm që të shfaqen butonat e qyteteve
    bot.edit_message_text("📍 In welcher Stadt möchten Sie dies veröffentlichen?", 
                          message.chat.id, temp_msg.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sel_"))
def preview(call):
    kanton = call.data.replace("sel_", "")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Ja, posten ✅", callback_data=f"pub_{kanton}"),
               types.InlineKeyboardButton("Nein, abbrechen ❌", callback_data="cancel"))
    
    bot.edit_message_text(f"📌 **Vorschau für {kanton}:**\n\n{user_data.get(call.message.chat.id)}\n\nPosten?", 
                          call.message.chat.id, call.message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pub_") or call.data == "cancel")
def final(call):
    name = call.from_user.first_name or ""
    username = f"@{call.from_user.username}" if call.from_user.username else "Nuk ka username"
    
    if call.data == "cancel":
        bot.edit_message_text("❌ Vorgang abgebrochen.", call.message.chat.id, call.message.message_id)
        bot.send_message(ADMIN_ID, f"🚫 {name} ({username}) e **anuloi** postimin.")
        return
    
    kanton = call.data.replace("pub_", "")
    try:
        # Postimi në kanal
        bot.send_message(CHANNELS[kanton], user_data[call.message.chat.id])
        bot.edit_message_text(f"✅ Erfolgreich in {kanton} gepostet!", call.message.chat.id, call.message.message_id)
        
        # 3. NJOFTIMI I DYTË: Postimi u krye me sukses
        bot.send_message(ADMIN_ID, f"✅ {name} ({username}) **postoi** në {kanton}.")
    except:
        bot.edit_message_text(f"❌ Error: Bot ist kein Admin in {kanton}!", call.message.chat.id, call.message.message_id)

if __name__ == "__main__":
    threading.Thread(target=run_flask).start()
    bot.infinity_polling(skip_pending=True)
