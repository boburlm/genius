
import sqlite3
import os
from telebot import TeleBot, types

# Bot tokenini shu yerga kiriting
TOKEN = "8651002727:AAEDcWu3DeD2-9Ll882jV5MukQOzwrkasfQ"
bot = TeleBot("8651002727:AAEDcWu3DeD2-9Ll882jV5MukQOzwrkasfQ")

# Bazani ruxsat berilgan xavfsiz papkada yaratamiz (/Users/aa/ombor.db)
BAZA_FAYLI = os.path.expanduser("~/ombor.db")

# ==========================================
# BAZA BILAN ISHLASH (SQLite)
# ==========================================
def baza_yaratish():
    conn = sqlite3.connect(BAZA_FAYLI)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ombor (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nomi TEXT UNIQUE,
            miqdor INTEGER,
            narx REAL
        )
    ''')
    conn.commit()
    conn.close()

baza_yaratish()

# ==========================================
# ASOSIY MENU BUTTONLARI
# ==========================================
def bosh_menu():
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton("➕ Tovar qo'shish")
    btn2 = types.KeyboardButton("🗑️ Tovar o'chirish")
    btn3 = types.KeyboardButton("🔄 Miqdorni o'zgartirish")
    btn4 = types.KeyboardButton("📦 Tovarlarni ko'rish")
    markup.add(btn1, btn2, btn3, btn4)
    return markup

@bot.message_handler(commands=['start', 'help'])
def start_cmd(message):
    bot.send_message(
        message.chat.id, 
        "👋 Ombor boshqaruv botiga xush kelibsiz!\nQuyidagi menyudan foydalaning:", 
        reply_markup=bosh_menu()
    )

# ==========================================
# 4 - TOVARLARNI KO'RISH
# ==========================================
@bot.message_handler(func=lambda msg: msg.text == "📦 Tovarlarni ko'rish")
def tovarlarni_korish(message):
    conn = sqlite3.connect(BAZA_FAYLI)
    cursor = conn.cursor()
    cursor.execute("SELECT nomi, miqdor, narx FROM ombor")
    tovarlar = cursor.fetchall()
    conn.close()

    if not tovarlar:
        bot.send_message(message.chat.id, "📭 Ombor hozircha bo'sh!")
        return

    matn = "<b>📦 Ombordagi tovarlar ro'yxati:</b>\n\n"
    for i, tovar in enumerate(tovarlar, 1):
        matn += f"{i}. <b>{tovar[0]}</b>\n🔹 Miqdori: {tovar[1]} ta/kg\n🔸 Narxi: {tovar[2]:,} so'm\n\n"
    
    bot.send_message(message.chat.id, matn, parse_mode="HTML")

# ==========================================
# 1 - TOVAR QO'SHISH (Bosqichma-bosqich)
# ==========================================
@bot.message_handler(func=lambda msg: msg.text == "➕ Tovar qo'shish")
def tovar_qoshish_boshlash(message):
    msg = bot.send_message(message.chat.id, "📝 Tovar nomini kiriting:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, tovar_nomi_olish)

def tovar_nomi_olish(message):
    nomi = message.text.strip().capitalize()
    
    conn = sqlite3.connect(BAZA_FAYLI)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ombor WHERE nomi = ?", (nomi,))
    tovar = cursor.fetchone()
    conn.close()

    if tovar:
        bot.send_message(message.chat.id, f"❌ '{nomi}' allaqachon omborda bor!", reply_markup=bosh_menu())
    else:
        msg = bot.send_message(message.chat.id, f"🔢 '{nomi}' miqdorini kiriting (faqat son):")
        bot.register_next_step_handler(msg, tovar_miqdori_olish, nomi)

def tovar_miqdori_olish(message, nomi):
    try:
        miqdor = int(message.text)
        msg = bot.send_message(message.chat.id, f"💰 Tovar narxini kiriting (so'mda):")
        bot.register_next_step_handler(msg, tovar_narxi_olish, nomi, miqdor)
    except ValueError:
        msg = bot.send_message(message.chat.id, "❌ Miqdorni faqat sonda kiriting! Qaytadan kiriting:")
        bot.register_next_step_handler(msg, tovar_miqdori_olish, nomi)

def tovar_narxi_olish(message, nomi, miqdor):
    try:
        narx = float(message.text)
        
        conn = sqlite3.connect(BAZA_FAYLI)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO ombor (nomi, miqdor, narx) VALUES (?, ?, ?)", (nomi, miqdor, narx))
        conn.commit()
        conn.close()

        bot.send_message(message.chat.id, f"✅ Tovar qo'shildi:\n📦 {nomi} - {miqdor} ta - {narx:,} so'm", reply_markup=bosh_menu())
    except ValueError:
        msg = bot.send_message(message.chat.id, "❌ Narxni faqat sonda kiriting! Qaytadan kiriting:")
        bot.register_next_step_handler(msg, tovar_narxi_olish, nomi, miqdor)

# ==========================================
# 2 - TOVAR O'CHIRISH
# ==========================================
@bot.message_handler(func=lambda msg: msg.text == "🗑️ Tovar o'chirish")
def tovar_ochirish_boshlash(message):
    msg = bot.send_message(message.chat.id, "🗑️ O'chiriladigan tovar nomini kiriting:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, tovar_ochirish_yakunlash)

def tovar_ochirish_yakunlash(message):
    nomi = message.text.strip().capitalize()
    
    conn = sqlite3.connect(BAZA_FAYLI)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ombor WHERE nomi = ?", (nomi,))
    tovar = cursor.fetchone()

    if tovar:
        cursor.execute("DELETE FROM ombor WHERE nomi = ?", (nomi,))
        conn.commit()
        bot.send_message(message.chat.id, f"🗑️ '{nomi}' ombordan o'chirildi.", reply_markup=bosh_menu())
    else:
        bot.send_message(message.chat.id, "❌ Bunday tovar topilmadi!", reply_markup=bosh_menu())
    
    conn.close()

# ==========================================
# 3 - MIQDORNI O'ZGARTIRISH
# ==========================================
@bot.message_handler(func=lambda msg: msg.text == "🔄 Miqdorni o'zgartirish")
def miqdor_ozgartirish_boshlash(message):
    msg = bot.send_message(message.chat.id, "🔄 Miqdori o'zgartiriladigan tovar nomini kiriting:", reply_markup=types.ReplyKeyboardRemove())
    bot.register_next_step_handler(msg, miqdor_ozgartirish_nomi)

def miqdor_ozgartirish_nomi(message):
    nomi = message.text.strip().capitalize()
    
    conn = sqlite3.connect(BAZA_FAYLI)
    cursor = conn.cursor()
    cursor.execute("SELECT miqdor FROM ombor WHERE nomi = ?", (nomi,))
    tovar = cursor.fetchone()
    conn.close()

    if tovar:
        msg = bot.send_message(message.chat.id, f"Hozirgi miqdor: {tovar[0]} ta/kg.\n🆕 Yangi miqdorni kiriting:")
        bot.register_next_step_handler(msg, miqdor_ozgartirish_yakunlash, nomi)
    else:
        bot.send_message(message.chat.id, "❌ Bunday tovar topilmadi!", reply_markup=bosh_menu())

def miqdor_ozgartirish_yakunlash(message, nomi):
    try:
        yangi_miqdor = int(message.text)
        
        conn = sqlite3.connect(BAZA_FAYLI)
        cursor = conn.cursor()
        cursor.execute("UPDATE ombor SET miqdor = ? WHERE nomi = ?", (yangi_miqdor, nomi))
        conn.commit()
        conn.close()

        bot.send_message(message.chat.id, f"🔄 '{nomi}' miqdori {yangi_miqdor} ga yangilandi.", reply_markup=bosh_menu())
    except ValueError:
        msg = bot.send_message(message.chat.id, "❌ Miqdorni faqat butun sonda kiriting! Qaytadan kiriting:")
        bot.register_next_step_handler(msg, miqdor_ozgartirish_yakunlash, nomi)

# Botni uzluksiz ishga tushirish
print("Bot muvaffaqiyatli ishga tushdi...")
bot.polling(none_stop=True)
