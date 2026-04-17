import telebot
from telebot import types

TOKEN = "8621899161:AAEqoto5KAVDRO0oAaQE6qLSGzva4t4fNU8"
ADMIN_ID = "6190547024" 
bot = telebot.TeleBot(TOKEN)

# Kjo rresht heq çdo bllokim të vjetër
bot.remove_webhook()

CHANNELS = {
    "Zürich": "-1003898417751",
    "Basel": "-1003718494977",
    "Solothurn": "-1003967254117",
    "Bern": "-1003959656124",
    "St. Gallen": "-1003808639054"
}

user_posts = {}

@bot.message_handler(commands=['start'])
def start(message):
    # Kjo heq butonat e vjetër që po të bllokojnë në foto
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "👋 Willkommen! Senden Sie Ihren Text.", reply_markup=markup)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    if message.text.startswith('/'): return
    user_posts[message.chat.id] = message.text
    
    # Butonat e rinj INLINE (këta funksionojnë me Admin)
    markup = types.InlineKeyboardMarkup(row_width=2)
    btns = [types.InlineKeyboardButton(text=f"{k} 🇨🇭", callback_data=f"sel_{k}") for k in CHANNELS.keys()]
    markup.add(*btns)
    bot.send_message(message.chat.id, "📍 Stadt wählen:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sel_"))
def confirm(call):
    kanton = call.data.replace("sel_", "")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Ja, posten ✅", callback_data=f"pub_{kanton}"),
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
        bot.edit_message_text(f"✅ Veröffentlicht in {kanton}!", call.message.chat.id, call.message.message_id)
        bot.send_message(ADMIN_ID, f"✅ @{call.from_user.username} gepostet in {kanton}")
    except:
        bot.edit_message_text(f"❌ Error: Boti nuk është Admin në {kanton}!", call.message.chat.id, call.message.message_id)

# skip_pending=True injoron mesazhet e vjetra që shkaktojnë Error 409
bot.infinity_polling(skip_pending=True)
