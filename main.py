import telebot
from telebot import types

# KONFIGURIMI
TOKEN = "8621899161:AAEqoto5KAVDRO0oAaQE6qLSGzva4t4fNU8"
ADMIN_ID = "6190547024" 
bot = telebot.TeleBot(TOKEN)

# Regjistrimi i komandës START në menu që të dalë automatikisht
bot.set_my_commands([
    telebot.types.BotCommand("start", "Bot starten / Startoni botin")
])

# ID-të e kanaleve tua
CHANNELS = {
    "Zürich": "-1003898417751",
    "Basel": "-1003718494977",
    "Solothurn": "-1003967254117",
    "Bern": "-1003959656124",
    "St. Gallen": "-1003808639054"
}

# Ruajtja e përkohshme e mesazheve në memorie
user_posts = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Fshijmë çdo tastierë të vjetër që mund të ketë mbetur në ekran
    markup = types.ReplyKeyboardRemove()
    bot.send_message(
        message.chat.id, 
        "👋 **Willkommen bei InfoStrasse Switzerland!**\n\nHier können Sie Strassenzustände anonym melden.\n\n👉 Bitte senden Sie uns jetzt Ihre Nachricht (nur Text).",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(content_types=['text'])
def handle_text(message):
    # Injoro komandën start që të mos postohet si tekst
    if message.text.startswith('/'):
        return

    # Ruajmë tekstin e përdoruesit
    user_posts[message.chat.id] = message.text
    
    # --- NJOFTIMI PËR ADMININ (Ty) ---
    user = message.from_user
    admin_info = (f"⚠️ **Neuer Post-Versuch!**\n"
                  f"👤 Von: {user.first_name} (@{user.username})\n"
                  f"📝 Inhalt: {message.text}")
    try:
        bot.send_message(ADMIN_ID, admin_info)
    except:
        pass # Admini duhet t'i ketë bërë /start botit të tij

    # Menuja me kantonet (Inline Buttons)
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text=f"{k} 🇨🇭", callback_data=f"sel_{k}") for k in CHANNELS.keys()]
    markup.add(*buttons)
    
    bot.send_message(message.chat.id, "📍 In welcher Stadt möchten Sie dies veröffentlichen?", reply_markup=markup)

@bot.message_handler(content_types=['photo', 'video', 'document', 'audio'])
def handle_others(message):
    bot.reply_to(message, "❌ **Nur Textnachrichten sind erlaubt.** Bitte senden Sie keine Fotos oder Videos.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("sel_"))
def preview_step(call):
    kanton = call.data.replace("sel_", "")
    chat_id = call.message.chat.id
    
    markup = types.InlineKeyboardMarkup()
    btn_yes = types.InlineKeyboardButton(text="Ja, posten ✅", callback_data=f"pub_{kanton}")
    btn_no = types.InlineKeyboardButton(text="Nein, abbrechen ❌", callback_data="cancel")
    markup.add(btn_yes, btn_no)
    
    preview_msg = (f"📌 **Vorschau për {kanton}**\n\n"
                   f"{user_posts.get(chat_id)}\n\n"
                   f"_Möchten Sie diesen Beitrag jetzt veröffentlichen?_")
    
    bot.edit_message_text(preview_msg, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pub_") or call.data == "cancel")
def final_step(call):
    chat_id = call.message.chat.id
    
    if call.data == "cancel":
        bot.edit_message_text("❌ Vorgang wurde abgebrochen.", chat_id, call.message.message_id)
        return

    kanton = call.data.replace("pub_", "")
    channel_id = CHANNELS.get(kanton)
    final_text = user_posts.get(chat_id)

    if final_text:
        try:
            # POSTIMI REAL NË KANAL
            bot.send_message(channel_id, final_text)
            
            # Konfirmimi për përdoruesin
            bot.edit_message_text(f"✅ Ihr Beitrag wurde in **{kanton}** veröffentlicht.", chat_id, call.message.message_id, parse_mode="Markdown")
            
            # Njoftimi i dytë për Adminin (Suksesi)
            bot.send_message(ADMIN_ID, f"✅ @{call.from_user.username} hat erfolgreich in {kanton} gepostet.")
            
        except Exception as e:
            bot.edit_message_text(f"❌ Fehler: Bot ist kein Admin in {kanton}.", chat_id, call.message.message_id)
            bot.send_message(ADMIN_ID, f"❌ ERROR: Bot konnte nicht in {kanton} posten. Check Admin permissions!")
    else:
        bot.send_message(chat_id, "Sitzung abgelaufen. Bitte senden Sie den Text erneut.")

# Ndezja e botit
print("Boti po punon...")
bot.infinity_polling()
