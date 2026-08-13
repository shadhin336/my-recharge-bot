import telebot
from telebot import types

# ১. আপনার Bot Token এবং Admin Telegram ID দিন
API_TOKEN = 'YOUR_8660582903:AAELmYdRuEXwjzOtJzxPanF-iIySm-buSw0_TOKEN_HERE'  # @BotFather থেকে পাওয়া টোকেন দিন
ADMIN_ID = 1919042009  # আপনার টেলিগ্রাম আইডি (আপনার ID জানতে @userinfobot এ মেসেজ দিন)

bot = telebot.TeleBot(API_TOKEN)

# ফেইক ডাটাবেজ (স্মৃতিতে ডাটা সেভ রাখার জন্য)
users_balance = {}

# /start কমান্ড
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.chat.id
    if user_id not in users_balance:
        users_balance[user_id] = 0.0

    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn_recharge = types.KeyboardButton('📱 Mobile Recharge')
    btn_add_money = types.KeyboardButton('💰 Add Money')
    btn_balance = types.KeyboardButton('💳 My Balance')
    markup.add(btn_recharge, btn_add_money, btn_balance)

    bot.send_message(
        user_id,
        f"স্বাগতম {message.from_user.first_name}!\nআমাদের রিচার্জ বটে আপনাকে স্বাগতম।",
        reply_markup=markup
    )

# ব্যালেন্স দেখার হ্যান্ডলার
@bot.message_handler(func=lambda message: message.text == '💳 My Balance')
def show_balance(message):
    user_id = message.chat.id
    bal = users_balance.get(user_id, 0.0)
    bot.send_message(user_id, f"আপনার বর্তমান ব্যালেন্স: {bal} BDT")

# Add Money হ্যান্ডলার
@bot.message_handler(func=lambda message: message.text == '💰 Add Money')
def add_money(message):
    text = (
        "💰 **Add Money Information**\n\n"
        "বিকাশ/নগদ পার্সোনাল: `017XXXXXXXX` (Send Money)\n\n"
        "টাকা পাঠানোর পর নিচের ফরম্যাটে মেসেজ দিন:\n"
        "`TrxID Amount PaymentMethod`\n"
        "উদাহরণ: `TRX123890 500 bKash`"
    )
    msg = bot.send_message(message.chat.id, text, parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_add_money)

def process_add_money(message):
    user_id = message.chat.id
    user_input = message.text

    # অ্যাডমিনকে নোটিফিকেশন পাঠানো
    markup = types.InlineKeyboardMarkup()
    approve_btn = types.InlineKeyboardButton("✅ Approve", callback_data=f"add_app_{user_id}_{user_input}")
    reject_btn = types.InlineKeyboardButton("❌ Reject", callback_data=f"add_rej_{user_id}")
    markup.add(approve_btn, reject_btn)

    bot.send_message(
        ADMIN_ID,
        f"📩 **New Add Money Request!**\nUser: {message.from_user.first_name} (`{user_id}`)\nDetails: {user_input}",
        reply_markup=markup,
        parse_mode='Markdown'
    )
    bot.send_message(user_id, "আপনার টাকা জমার রিকোয়েস্ট অ্যাডমিনের কাছে পাঠানো হয়েছে। অনুগ্রহ করে অপেক্ষা করুন।")

# রিচার্জ সিস্টেম
@bot.message_handler(func=lambda message: message.text == '📱 Mobile Recharge')
def recharge_start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    operators = ['Grameenphone', 'Robi', 'Airtel', 'Banglalink']
    buttons = [types.InlineKeyboardButton(op, callback_data=f"op_{op}") for op in operators]
    markup.add(*buttons)
    
    bot.send_message(message.chat.id, "যেকোনো একটি সিম অপারেটর সিলেক্ট করুন:", reply_markup=markup)

# Callback Query Handler (Button Actions)
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    # অপারেটর সিলেক্ট
    if call.data.startswith("op_"):
        operator = call.data.split("_")[1]
        msg = bot.send_message(call.message.chat.id, f"আপনার {operator} নম্বর এবং টাকার পরিমাণ লিখুন:\nফরম্যাট: `01700000000 50`", parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_recharge_req, operator)

    # অ্যাডমিন প্যানেল: Add Money Approve
    elif call.data.startswith("add_app_"):
        data = call.data.split("_")
        target_user = int(data[2])
        req_details = data[3]
        
        # অনুমান করে অ্যামাউন্ট বের করা (সরলীকৃত)
        try:
            amount = float(req_details.split()[1])
            users_balance[target_user] = users_balance.get(target_user, 0.0) + amount
            bot.send_message(target_user, f"🎉 আপনার অ্যাকাউন্টে {amount} BDT সফলভাবে যোগ করা হয়েছে!")
            bot.edit_message_text("✅ Add Money Request Approved!", ADMIN_ID, call.message.message_id)
        except:
            bot.send_message(ADMIN_ID, "ফরম্যাট ভুলের কারণে অটো যোগ করা সম্ভব হয়নি। ম্যানুয়ালি করুন।")

    # অ্যাডমিন প্যানেল: Add Money Reject
    elif call.data.startswith("add_rej_"):
        target_user = int(call.data.split("_")[2])
        bot.send_message(target_user, "❌ আপনার টাকা জমার রিকোয়েস্টটি বাতিল করা হয়েছে। সঠিক তথ্য দিয়ে আবার চেষ্টা করুন।")
        bot.edit_message_text("❌ Request Rejected!", ADMIN_ID, call.message.message_id)

def process_recharge_req(message, operator):
    user_id = message.chat.id
    try:
        num, amount = message.text.split()
        amount = float(amount)
        
        current_bal = users_balance.get(user_id, 0.0)
        if current_bal < amount:
            bot.send_message(user_id, "❌ আপনার অ্যাকাউন্টে পর্যাপ্ত ব্যালেন্স নেই! দয়া করে Add Money করুন।")
            return
        
        # ব্যালেন্স কেটে নেওয়া
        users_balance[user_id] -= amount
        
        # অ্যাডমিনকে পাঠানো ম্যানুয়াল রিচার্জের জন্য
        bot.send_message(
            ADMIN_ID,
            f"⚡ **NEW RECHARGE REQUEST!**\n\n"
            f"👤 User ID: `{user_id}`\n"
            f"📱 Operator: {operator}\n"
            f"📞 Number: `{num}`\n"
            f"💵 Amount: {amount} BDT",
            parse_mode='Markdown'
        )
        bot.send_message(user_id, f"✅ আপনার {operator} নম্বরে {amount} টাকা রিচার্জ রিকোয়েস্ট প্রসেসিংয়ে আছে।")
        
    except Exception as e:
        bot.send_message(user_id, "❌ ভুল ফরম্যাট! দয়া করে ঠিকভাবে লিখুন (যেমন: 01700000000 50)।")

print("Bot is running...")
bot.infinity_polling()
