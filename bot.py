import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import sqlite3
import json

# إعدادات البوت
TOKEN = "8392043927:AAGiPIvU3s6ekEsBhaO7dDaqGnu8_zIK6tk"
ADMIN_ID = 7700286311
PRICE_PER_20_REVIEWS = 25

# إعداد التسجيل
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# قاعدة البيانات
def init_db():
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    
    # جدول المستخدمين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            balance INTEGER DEFAULT 0,
            total_reviews INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول الحسابات الخاصة
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS private_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            account_name TEXT,
            account_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
    ''')
    
    conn.commit()
    conn.close()

# أوامر الأدمن
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ ليس لديك صلاحية للوصول إلى هذه الصفحة.")
        return
    
    keyboard = [
        [InlineKeyboardButton("إحصائيات البوت", callback_data="admin_stats")],
        [InlineKeyboardButton("إدارة المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton("إضافة رصيد", callback_data="admin_add_balance")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛠 لوحة تحكم الأدمن:", reply_markup=reply_markup)

# أوامر المستخدمين
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    # إضافة المستخدم إلى قاعدة البيانات
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name) 
        VALUES (?, ?, ?)
    ''', (user_id, username, first_name))
    conn.commit()
    conn.close()
    
    keyboard = [
        [InlineKeyboardButton("📊 إحصائياتي", callback_data="my_stats")],
        [InlineKeyboardButton("👤 الحسابات الخاصة", callback_data="private_accounts")],
        [InlineKeyboardButton("💰 السعر والدفع", callback_data="pricing")],
        [InlineKeyboardButton("📝 إضافة تقييم", callback_data="add_review")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    welcome_text = f"""
    🎯 أهلاً بك {first_name}!

    هذا البوت مخصص لإدارة تقييمات جوجل مابس.

    المميزات:
    • إنشاء حسابات خاصة للتقييمات
    • متابعة الإحصائيات والأرباح
    • سعر ثابت لكل 20 تقييم: {PRICE_PER_20_REVIEWS}$ 
    
    اختر من الأزرار أدناه:
    """
    
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

# معالجة الأزرار
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    if data == "my_stats":
        await show_my_stats(query, user_id)
    elif data == "private_accounts":
        await show_private_accounts(query, user_id)
    elif data == "pricing":
        await show_pricing(query)
    elif data == "add_review":
        await add_review_menu(query, user_id)
    elif data == "add_private_account":
        await add_private_account(query, user_id)
    elif data.startswith("admin_"):
        await admin_button_handler(query, data)

async def show_my_stats(query, user_id):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT balance, total_reviews FROM users WHERE user_id = ?', (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    
    if user_data:
        balance, total_reviews = user_data
        earned_money = (total_reviews // 20) * PRICE_PER_20_REVIEWS
        remaining_for_payment = 20 - (total_reviews % 20)
        
        stats_text = f"""
        📊 إحصائياتك:

        • إجمالي التقييمات: {total_reviews}
        • الرصيد المستحق: {earned_money}$
        • التقيمات المتبقية للدفع: {remaining_for_payment}
        • السعر: {PRICE_PER_20_REVIEWS}$ لكل 20 تقييم
        
        💰 سيتم الدفع عند إكمال 20 تقييم
        """
        
        await query.edit_message_text(stats_text)
    else:
        await query.edit_message_text("❌ لم يتم العثور على بياناتك.")

async def show_pricing(query):
    pricing_text = f"""
    💰 باقة الأسعار:

    • كل 20 تقييم = {PRICE_PER_20_REVIEWS}$ 
    • الدفع بعد إكمال 20 تقييم
    • التقييمات يجب أن تكون حقيقية وليست وهمية
    • يمكنك إنشاء حسابات خاصة متعددة
    
    📝 كيفية العمل:
    1. أنشئ حساب خاص من قسم "الحسابات الخاصة"
    2. أضف التقييمات من خلال البوت
    3. تابع إحصائياتك وأرباحك
    4. استلم دفعتك بعد إكمال 20 تقييم
    """
    
    await query.edit_message_text(pricing_text)

async def show_private_accounts(query, user_id):
    conn = sqlite3.connect('bot.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT account_name, created_at FROM private_accounts WHERE user_id = ?', (user_id,))
    accounts = cursor.fetchall()
    conn.close()
    
    if accounts:
        accounts_text = "👤 حساباتك الخاصة:\n\n"
        for i, (account_name, created_at) in enumerate(accounts, 1):
            accounts_text += f"{i}. {account_name} - {created_at[:10]}\n"
        
        keyboard = [[InlineKeyboardButton("➕ إضافة حساب جديد", callback_data="add_private_account")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(accounts_text, reply_markup=reply_markup)
    else:
        keyboard = [[InlineKeyboardButton("➕ إضافة حساب جديد", callback_data="add_private_account")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("❌ ليس لديك أي حسابات خاصة.", reply_markup=reply_markup)

async def add_private_account(query, user_id):
    await query.edit_message_text("✍️ أرسل اسم الحساب الجديد:")

async def add_review_menu(query, user_id):
    # هذه الوظيفة تحتاج إلى تطوير لإضافة التقييمات الفعلية
    # حالياً هي مجرد واجهة توضيحية
    
    review_text = """
    📝 إضافة تقييم جديد:

    ⚠️ ملاحظة: هذا جزء توضيحي ويحتاج إلى تطوير.

    لإضافة تقييم حقيقي، تحتاج إلى:
    1. ربط البوت مع واجهة برمجة جوجل مابس
    2. التأكد من صحة الحسابات
    3. متابعة التقييمات المضافه
    
    هذا الجزء يتطلب تطويراً إضافياً.
    """
    
    await query.edit_message_text(review_text)

async def admin_button_handler(query, data):
    if query.from_user.id != ADMIN_ID:
        await query.edit_message_text("❌ ليس لديك صلاحية للوصول إلى هذه الصفحة.")
        return
    
    if data == "admin_stats":
        conn = sqlite3.connect('bot.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM users')
        total_users = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM private_accounts')
        total_accounts = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(total_reviews) FROM users')
        total_reviews = cursor.fetchone()[0] or 0
        
        conn.close()
        
        stats_text = f"""
        📊 إحصائيات البوت:

        • إجمالي المستخدمين: {total_users}
        • إجمالي الحسابات: {total_accounts}
        • إجمالي التقييمات: {total_reviews}
        • التكلفة المستحقة: {(total_reviews // 20) * PRICE_PER_20_REVIEWS}$
        """
        
        await query.edit_message_text(stats_text)

def main():
    # تهيئة قاعدة البيانات
    init_db()
    
    # إنشاء تطبيق البوت
    application = Application.builder().token(TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # بدء البوت
    print("🤖 البوت يعمل...")
    application.run_polling()

if __name__ == '__main__':
    main()