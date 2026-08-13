import telebot
from telebot import types

# আপনার Bot Token এবং Admin Telegram ID দিন
API_TOKEN = '8660582903:AAELmYdRuEXwjzOtJzxPanF-iIySm-buSw0'  # @BotFather থেকে পাওয়া টোকেন
ADMIN_ID = 1919042009              # আপনার আইডি

bot = telebot.TeleBot(API_TOKEN)

# ইউজার ব্যালেন্স ডাটাবেজ
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
    bot.send_message(user_id, f"💳 আপনার বর্তমান ব্যালেন্স: {bal} BDT")

# Add Money হ্যান্ডলার
@bot.message_handler(func=lambda message: message.text == '💰 Add Money')
def add_money(message):
    text = (
        "💰 **Add Money Information**\n\n"
        "বিকাশ/নগদ পার্সোনাল: `017XXXXXXXX` (Send Money)\n\n"
        "টাকা পাঠানোর পর নিচের ফরম্যাটে সঠিকভাবে লিখুন:\n"
        "`TrxID, Amount, PaymentMethod`\n\n"
        "যেমন: `TRX123890 500 bKash`"
    )
    msg = bot.send_message(message.chat.id, text, parse_mode='Markdown')
    bot.register_next_step_handler(msg, process_add_money)

def process_add_money(message):
    user_id = message.chat.id
    user_input = message.text

    # যদি ইউজার কোনো মেনু বাটন চেপে দেয়
    if user_input in ['📱 Mobile Recharge', '💰 Add Money', '💳 My Balance']:
        bot.send_message(user_id, "❌ টাকা জমার প্রসেস বাতিল করা হয়েছে। আবার চেষ্টা করুন।")
        return

    # অ্যাডমিনকে নোটিফিকেশন পাঠানো
    markup = types.InlineKeyboardMarkup()
    approve_btn = types.InlineKeyboardButton("✅ Approve", callback_data=f"app_{user_id}")
    reject_btn = types.InlineKeyboardButton("❌ Reject", callback_data=f"rej_{user_id}")
    markup.add(approve_btn, reject_btn)

    bot.send_message(
        ADMIN_ID,
        f"📩 **New Add Money Request!**\n\n"
        f"👤 User: {message.from_user.first_name} (`{user_id}`)\n"
        f"📝 Details: `{user_input}`",
        reply_markup=markup,
        parse_mode='Markdown'
    )
    bot.send_message(user_id, "✅ আপনার টাকা জমার রিকোয়েস্ট অ্যাডমিনের কাছে পাঠানো হয়েছে। অপেক্ষা করুন।")

# রিচার্জ অপশন
@bot.message_handler(func=lambda message: message.text == '📱 Mobile Recharge')
def recharge_start(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    operators = ['Grameenphone', 'Robi', 'Airtel', 'Banglalink']
    buttons = [types.InlineKeyboardButton(op, callback_data=f"op_{op}") for op in operators]
    markup.add(*buttons)
    
    bot.send_message(message.chat.id, "যেকোনো একটি সিম অপারেটর সিলেক্ট করুন:", reply_markup=markup)

# Callback Query Handler (Button Clicks)
@bot.callback_query_handler(func=lambda call: True)
def callback_listener(call):
    # অপারেটর সিলেক্ট
    if call.data.startswith("op_"):
        operator = call.data.split("_")[1]
        msg = bot.send_message(call.message.chat.id, f"আপনার {operator} নম্বর এবং টাকার পরিমাণ লিখুন:\nউদাহরণ: `01700000000 50`", parse_mode='Markdown')
        bot.register_next_step_handler(msg, process_recharge_req, operator)

    # অ্যাডমিন: Add Money Approve
    elif call.data.startswith("app_"):
        target_user = int(call.data.split("_")[1])
        msg = bot.send_message(ADMIN_ID, f"ইউজার `{target_user}`-কে কত টাকা যোগ করতে চান? (শুধু নম্বর লিখুন, যেমন: 500):", parse_mode='Markdown')
        bot.register_next_step_handler(msg, confirm_approve, target_user, call.message.message_id)

    # অ্যাডমিন: Add Money Reject
    elif call.data.startswith("rej_"):
        target_user = int(call.data.split("_")[1])
        bot.send_message(target_user, "❌ আপনার টাকা জমার রিকোয়েস্টটি বাতিল করা হয়েছে। সঠিক তথ্য দিয়ে আবার চেষ্টা করুন।")
        bot.edit_message_text("❌ Request Rejected!", ADMIN_ID, call.message.message_id)

def confirm_approve(message, target_user, old_msg_id):
    try:
        amount = float(message.text)
        users_balance[target_user] = users_balance.get(target_user, 0.0) + amount
        
        bot.send_message(target_user, f"🎉 অভিনন্দন! আপনার অ্যাকাউন্টে {amount} BDT যোগ করা হয়েছে।")
        bot.send_message(ADMIN_ID, f"✅ সফলভাবে ইউজারকে {amount} BDT ব্যালেন্স যোগ করা হয়েছে।")
    except Exception as e:
        bot.send_message(ADMIN_ID, "❌ ভুল ইনপুট! শুধু সংখ্যা লিখুন (যেমন: 100)।")

def process_recharge_req(message, operator):
    user_id = message.chat.id
    try:
        num, amount = message.text.split()
        amount = float(amount)
        
        current_bal = users_balance.get(user_id, 0.0)
        if current_bal < amount:
            bot.send_message(user_id, f"❌ আপনার অ্যাকাউন্টে পর্যাপ্ত ব্যালেন্স নেই!\nবর্তমান ব্যালেন্স: {current_bal} BDT")
            return
        
        users_balance[user_id] -= amount
        
        bot.send_message(
            ADMIN_ID,
            f"⚡ **NEW RECHARGE REQUEST!**\n\n"
            f"👤 User: {message.from_user.first_name} (`{user_id}`)\n"
            f"📱 Operator: {operator}\n"
            f"📞 Number: `{num}`\n"
            f"💵 Amount: {amount} BDT",
            parse_mode='Markdown'
        )
        bot.send_message(user_id, f"✅ আপনার {operator} নম্বরে ({num}) {amount} টাকা রিচার্জ রিকোয়েস্ট প্রসেসিংয়ে আছে।")
        
    except Exception as e:
        bot.send_message(user_id, "❌ ভুল ফরম্যাট! দয়া করে ঠিকভাবে লিখুন (উদাহরণ: 01700000000 50)।")

print("Bot is running...")
bot.infinity_polling()
