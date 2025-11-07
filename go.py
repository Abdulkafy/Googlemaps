# مثال مبسط على دالة في البوت لاستقبال بيانات التقييم
async def receive_review_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    # نفترض أن context.args يحتوي على [رابط المكان, التقييم, التقييم بالنجوم]
    place_url = context.args[0]
    review_text = context.args[1]
    rating = int(context.args[2])
    
    # حفظ البيانات في قاعدة البيانات
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reviews (user_id, place_url, review_text, rating)
        VALUES (?, ?, ?, ?)
    ''', (user_id, place_url, review_text, rating))
    conn.commit()
    conn.close()
    
    await update.message.reply_text("✅ تم حفظ بيانات التقييم بنجاح. (ملاحظة: هذا لا يضمن نشره على جوجل مابس)")