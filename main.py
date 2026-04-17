import telebot
from telebot import types

# KONFIGURIMI KRYESOR
TOKEN = "8621899161:AAEqoto5KAVDRO0oAaQE6qLSGzva4t4fNU8"
ADMIN_ID = "6190547024" 
bot = telebot.TeleBot(TOKEN)

# Zgjidhja për Error 409: Pastron lidhjet e vjetra para se të niset
bot.remove_webhook()

# Regjistrimi i komandës START në menu
bot.set_my_commands([
    telebot.types.BotCommand("start", "Bot starten")
])

# Kantonet dhe ID-të e kanaleve
CHANNELS = {
    "Zürich": "-1003898417751",
    "Basel": "-1003718494977",
    "Solothurn": "-1003967254117",
    "Bern": "-1003959656124",
    "St. Gallen": "-1003808639054"
}

user_posts = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    # Fshijmë butonat e vjetër të tastierës (ReplyKeyboardMarkup)
    markup = types.ReplyKeyboardRemove()
    welcome_text = (
        "👋 **Willkommen bei InfoStrasse Switzerland!**\n\n"
        "Hier können Sie Strassenzustände anonym melden.\n\n"
        "👉 Bitte senden Sie uns jetzt Ihre Nachricht (nur Text)."
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text.startswith('/'):
        return

    # Ruajmë tekstin e përdoruesit
    user_posts[message.chat.id] = message.text
    
    # NJOFTIMI PËR ADMININ (Me try/except që të mos rrëzohet boti)
    try:
        admin_msg = f"⚠️ **Neuer Post-Versuch!**\n👤 Von: @{message.from_user.username}\n📝 Text: {message.text}"
        bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
    except:
        print("Admini nuk e ka bere start botin.")

    # Krijimi i butonave INLINE (poshtë mesazhit)
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text=f"{k} 🇨🇭", callback_data=f"sel_{k}") for k in CHANNELS.keys()]
    markup.add(*buttons)
    
    bot.send_message(message.chat.id, "📍 In welcher Stadt möchten Sie dies veröffentlichen?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sel_"))
def preview_step(call):
    kanton = call.data.replace("sel_", "")
    chat_id = call.message.chat.id
    
    markup = types.InlineKeyboardMarkup()
    btn_yes = types.InlineKeyboardButton(text="Ja, posten ✅", callback_data=f"pub_{kanton}")
    btn_no = types.InlineKeyboardButton(text="Nein, abbrechen ❌", callback_data="cancel")
    markup.add(btn_yes, btn_no)
    
    preview_text = f"📌 **Vorschau për {kanton}**\n\n{user_posts.get(chat_id)}\n\n_Möchten Sie dies wirklich posten?_"
    bot.edit_message_text(preview_text, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pub_") or call.data == "cancel")
def final_step(call):
    chat_id = call.message.chat.id
    
    if call.data == "cancel":
        bot.edit_message_text("❌ Vorgang abgebrochen.", chat_id, call.message.message_id)
        return

    kanton = call.data.replace("pub_", "")
    channel_id = CHANNELS.get(kanton)
    post_content = user_posts.get(chat_id)

    if post_content:
        try:
            # POSTIMI REAL NË KANAL
            bot.send_message(channel_id, post_content)
            bot.edit_message_text(f"✅ Erfolgreich in **{kanton}** gepostet!", chat_id, call.message.message_id, parse_mode="Markdown")
            bot.send_message(ADMIN_ID, f"✅ @{call.from_user.username} gepostet in {kanton}.")
        except Exception as e:
            bot.edit_message_text(f"❌ Fehler: Bot ist kein Admin in {kanton}.", chat_id, call.message.message_id)
    else:
        bot.send_message(chat_id, "Sitzung abgelaufen. Bitte erneut senden.")

# Ndezja e botit (skip_pending=True shmang konfliktet e mesazheve të vjetra)
print("Boti po punon...")
bot.infinity_polling(skip_pending=True)
