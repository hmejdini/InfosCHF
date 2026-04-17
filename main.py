import telebot
from telebot import types

TOKEN = "8621899161:AAEqoto5KAVDRO0oAaQE6qLSGzva4t4fNU8"
ADMIN_ID = "6190547024" 
bot = telebot.TeleBot(TOKEN)

# Kjo bën që butoni "START" të shfaqet automatikisht te menuja e Telegramit
bot.set_my_commands([
    telebot.types.BotCommand("start", "Bot starten / Startoni botin")
])

CHANNELS = {
    "Zürich": "-1003898417751",
    "Basel": "-1003718494977",
    "Solothurn": "-1003967254117",
    "Bern": "-1003959656124",
    "St. Gallen": "-1003808639054"
}

pending_posts = {}

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(
        message.chat.id, 
        "Willkommen! ℹ️\n\nBitte senden Sie den **Text**, den Sie posten möchten.\n\n*(Nur Textnachrichten sind erlaubt)*"
    )

@bot.message_handler(content_types=['text'])
def handle_message(message):
    # Mos reago nëse është komanda start
    if message.text == "/start":
        return

    pending_posts[message.chat.id] = message.text
    
    # Njoftimi i menjëhershëm për Adminin
    user = message.from_user
    admin_msg = f"⚠️ **Neuer Text-Versuch!**\n👤 Von: {user.first_name} (@{user.username})\n📝 Text: {message.text}"
    
    try:
        bot.send_message(ADMIN_ID, admin_msg)
    except Exception as e:
        print(f"Admin Error: {e}")

    # Menuja e kantoneve
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text=k, callback_data=f"sel_{k}") for k in CHANNELS.keys()]
    markup.add(*buttons)
    
    bot.send_message(message.chat.id, "In welchem Kanton möchten Sie posten?", reply_markup=markup)

@bot.message_handler(content_types=['photo', 'video', 'document', 'audio'])
def handle_others(message):
    bot.reply_to(message, "❌ Nur Textnachrichten sind erlaubt. Bitte senden Sie nur Text.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("sel_"))
def preview_post(call):
    kanton = call.data.replace("sel_", "")
    chat_id = call.message.chat.id
    
    markup = types.InlineKeyboardMarkup()
    btn_yes = types.InlineKeyboardButton(text="Ja, posten ✅", callback_data=f"pub_{kanton}")
    btn_no = types.InlineKeyboardButton(text="Nein, abbrechen ❌", callback_data="cancel")
    markup.add(btn_yes, btn_no)
    
    text_preview = f"📌 **Vorschau für {kanton}**\n\n{pending_posts.get(chat_id)}\n\n_Möchten Sie diesen Beitrag jetzt veröffentlichen?_"
    
    bot.edit_message_text(text_preview, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pub_") or call.data == "cancel")
def publish_action(call):
    chat_id = call.message.chat.id
    
    if call.data == "cancel":
        bot.edit_message_text("❌ Vorgang abgebrochen.", chat_id, call.message.message_id)
        return

    kanton = call.data.replace("pub_", "")
    channel_id = CHANNELS.get(kanton)
    post_text = pending_posts.get(chat_id)

    if post_text:
        try:
            bot.send_message(channel_id, post_text)
            bot.edit_message_text(f"✅ Veröffentlicht in **{kanton}**.", chat_id, call.message.message_id, parse_mode="Markdown")
            bot.send_message(ADMIN_ID, f"✅ @{call.from_user.username} hat in {kanton} gepostet.")
        except Exception as e:
            bot.edit_message_text("❌ Fehler: Bot ist kein Admin im Kanal.", chat_id, call.message.message_id)
    else:
        bot.send_message(chat_id, "Sitzung abgelaufen.")

print("Boti po ndizet...")
bot.infinity_polling()
