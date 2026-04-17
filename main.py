import telebot
from telebot import types

TOKEN = "8621899161:AAEqoto5KAVDRO0oAaQE6qLSGzva4t4fNU8"
ADMIN_ID = "6190547024"  # ID-ja jote
bot = telebot.TeleBot(TOKEN)

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
    bot.reply_to(message, "Willkommen! Senden Sie einen Text oder ein Foto, das Sie posten möchten.")

@bot.message_handler(content_types=['text', 'photo'])
def handle_message(message):
    # Ruajmë mesazhin
    pending_posts[message.chat.id] = message
    
    # --- NJOFTIMI PËR ADMININ (Vjen menjëherë këtu) ---
    user = message.from_user
    admin_info = f"⚠️ **Neuer Versuch!**\n👤 Von: {user.first_name} (@{user.username})\n🆔 ID: {user.id}\n\n"
    
    try:
        if message.content_type == 'text':
            bot.send_message(ADMIN_ID, admin_info + f"📝 Nachricht: {message.text}")
        elif message.content_type == 'photo':
            bot.send_photo(ADMIN_ID, message.photo[-1].file_id, caption=admin_info + "🖼 Foto gesendet.")
    except Exception as e:
        print(f"Njoftimi adminit dështoi: {e}")
    # ------------------------------------------------

    # Vazhdon procedura për përdoruesin
    markup = types.InlineKeyboardMarkup(row_width=2)
    buttons = [types.InlineKeyboardButton(text=k, callback_data=f"sel_{k}") for k in CHANNELS.keys()]
    markup.add(*buttons)
    
    bot.send_message(message.chat.id, "In welchem Kanton möchten Sie posten?", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sel_"))
def preview_post(call):
    kanton = call.data.replace("sel_", "")
    chat_id = call.message.chat.id
    
    markup = types.InlineKeyboardMarkup()
    btn_yes = types.InlineKeyboardButton(text="Ja, posten ✅", callback_data=f"pub_{kanton}")
    btn_no = types.InlineKeyboardButton(text="Nein, abbrechen ❌", callback_data="cancel")
    markup.add(btn_yes, btn_no)
    
    text_preview = f"📌 **Ihre Post-Vorschau**\n\n📍 Kanton: {kanton}\n\nMöchten Sie diesen Beitrag jetzt veröffentlichen?"
    bot.edit_message_text(text_preview, chat_id, call.message.message_id, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pub_") or call.data == "cancel")
def publish_action(call):
    chat_id = call.message.chat.id
    
    if call.data == "cancel":
        bot.edit_message_text("Vorgang wurde abgebrochen. ❌", chat_id, call.message.message_id)
        return

    kanton = call.data.replace("pub_", "")
    channel_id = CHANNELS.get(kanton)
    msg = pending_posts.get(chat_id)

    if msg:
        try:
            if msg.content_type == 'text':
                bot.send_message(channel_id, msg.text)
            elif msg.content_type == 'photo':
                bot.send_photo(channel_id, msg.photo[-1].file_id, caption=msg.caption)
            
            bot.edit_message_text(f"✅ Ihr Beitrag wurde in **{kanton}** veröffentlicht.", chat_id, call.message.message_id, parse_mode="Markdown")
            
            # Njoftim final për Adminin që postimi u krye me sukses
            bot.send_message(ADMIN_ID, f"✅ Post erfolgreich veröffentlicht in: {kanton} (von @{call.from_user.username})")

        except Exception as e:
            bot.send_message(chat_id, "❌ Fehler: Der Bot hat keine Admin-Rechte.")
    else:
        bot.send_message(chat_id, "Sitzung abgelaufen.")

print("Boti po ndizet...")
bot.infinity_polling()
