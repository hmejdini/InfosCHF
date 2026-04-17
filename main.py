import telebot
from telebot import types
import threading
from flask import Flask
import os

# --- KONFIGURIMI I SERVERIT PËR RENDER (FALAS) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    # Render kërkon që boti të dëgjojë në një portë specifike
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- KONFIGURIMI I BOTIT ---
TOKEN = "8621899161:AAHhl4jLg5Ntvv4oLc1qe6NV88KJFP4hkPU"
ADMIN_ID = "6190547024" 
bot = telebot.TeleBot(TOKEN)

# Zgjidhja për Error 409: Pastron çdo lidhje të vjetër fantazmë
bot.remove_webhook()

# Kanalet për kantonet përkatëse
CHANNELS = {
    "Zürich": "-1003898417751",
    "Basel": "-1003718494977",
    "Solothurn": "-1003967254117",
    "Bern": "-1003959656124",
    "St. Gallen": "-1003808639054"
}

user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Fshijmë butonat e vjetër të tastierës sapo shtypet /start
    markup = types.ReplyKeyboardRemove()
    bot.send_message(
        message.chat.id, 
        "👋 **Willkommen bei InfoStrasse Switzerland!**\n\nHier können Sie Strassenzustände anonym melden.\n\n👉 Bitte senden Sie uns jetzt Ihre Nachricht (nur Text).",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text.startswith('/'):
        return

    # Ruajmë tekstin e përdoruesit
    user_data[message.chat.id] = message.text
    
    # Mbledhim të dhënat e përdoruesit për Adminin
    u = message.from_user
    emri_plote = f"{u.first_name} {u.last_name or ''}"
    username = f"@{u.username}" if u.username else "Nuk ka username"
    
    # 1. NJOFTIMI I PARË TE ADMINI (Kush po shkruan)
    admin_msg = (f"📩 **Tentativë e re mesazhi**\n"
                 f"👤 Emri: {emri_plote}\n"
                 f"🆔 Username: {username}\n"
                 f"📝 Teksti: {message.text}")
    try:
        bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
    except:
        pass

    # 2. FSHIRJA E TASTIERËS DHE SHFAQJA E QYTETEVE (Inline)
    # Dërgojmë një mesazh që fshin tastierën dhe pastaj butonat e qyteteve
    remove_kb = types.ReplyKeyboardRemove()
    temp_msg = bot.send_message(message.chat.id, "📍 Bitte wählen Sie die Stadt:", reply_markup=remove_kb)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text=f"{k} 🇨🇭", callback_data=f"sel_{k}") for k in CHANNELS.keys()]
    markup.add(*buttons)
    
    bot.edit_message_text("📍 In welcher Stadt möchten Sie dies veröffentlichen?", 
                          message.chat.id, temp_msg.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    chat_id = call.message.chat.id
    u = call.from_user
    username = f"@{u.username}" if u.username else "Nuk ka username"

    if call.data.startswith("sel_"):
        kanton = call.data.replace("sel_", "")
        
        markup = types.InlineKeyboardMarkup()
        btn_yes = types.InlineKeyboardButton(text="Ja, posten ✅", callback_data=f"pub_{kanton}")
        btn_no = types.InlineKeyboardButton(text="Nein, abbrechen ❌", callback_data="cancel")
        markup.add(btn_yes, btn_no)
        
        preview_text = f"📌 **Vorschau für {kanton}**\n\n{user_data.get(chat_id)}\n\n_Möchten Sie dies wirklich posten?_"
        bot.edit_message_text(preview_text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

    elif call.data == "cancel":
        bot.edit_message_text("❌ Vorgang abgebrochen.", chat_id, call.message.message_id)
        bot.send_message(ADMIN_ID, f"🚫 {u.first_name} ({username}) e **anuloi** postimin.")

    elif call.data.startswith("pub_"):
        kanton = call.data.replace("pub_", "")
        channel_id = CHANNELS.get(kanton)
        post_content = user_data.get(chat_id)

        if post_content:
            try:
                # Postimi në kanalin përkatës
                bot.send_message(channel_id, post_content)
                bot.edit_message_text(f"✅ Erfolgreich in **{kanton}** gepostet!", chat_id, call.message.message_id, parse_mode="Markdown")
                
                # Njoftimi final te Admini
                bot.send_message(ADMIN_ID, f"✅ {u.first_name} ({username}) **postoi** me sukses në {kanton}.")
            except:
                bot.edit_message_text(f"❌ Fehler: Bot ist kein Admin in {kanton}.", chat_id, call.message.message_id)

# --- NISJA ---
if __name__ == "__main__":
    # Nisim Flask në një thread që Render të jetë i kënaqur (Pika e gjelbër)
    threading.Thread(target=run_flask).start()
    
    # Nisim botin (skip_pending=True injoron mesazhet e vjetra që shkaktojnë gabime)
    print("Boti po punon...")
    bot.infinity_polling(skip_pending=True)
