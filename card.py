# مثال على دالة لتسجيل طلب سحب الأرباح
async def request_withdrawal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    user_balance = cursor.fetchone()[0]
    
    # تحقق إذا كان الرصيد يكفي للسحب (مثلاً، 25 دولارًا مقابل 20 تقييمًا)
    if user_balance >= 25:
        # إعلام الأدمن بطلب السحب وربط user_id بعنوان المحفظة
        # هنا، قد تطلب من المستخدم إدخال عنوان محفظته أو تستخدم العنوان المسجل مسبقًا
        await update.message.reply_text(f"✅ تم إرسال طلب السبق بقيمة {user_balance}$ إلى الأدمن. سيتم التحويل إلى المحفظة المسجلة.")
        # إعلام الأدمن
        admin_id = ADMIN_ID  # من إعدادات البوت
        await context.bot.send_message(chat_id=admin_id, text=f"User {user_id} requested withdrawal of ${user_balance}. Binance Wallet: 933609958")
    else:
        await update.message.reply_text("❌ رصيدك غير كافٍ لطلب السحب.")
    
    conn.close()