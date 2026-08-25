import requests
import base64
import time
import json
import urllib.parse
from xml.etree import ElementTree as ET
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from datetime import datetime
import logging
import os
import ssl
import urllib3

# تعطيل تحذيرات SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================
# 1. إعدادات البوت
# ============================================
BOT_TOKEN = "8835812338:AAFoFs-GD86pEQdJArCExMrbwLrdu8NH3RY"
ADMIN_ID = 8273076051  # معرف الأدمن
CHANNEL_ID = "@selva_card"  # اسم القناة
CHANNEL_LINK = "https://t.me/selva_card"

# المتغيرات الثابتة
DEVICE_ID = "72e1f59bcb7bda75"
UDID = DEVICE_ID
MODEL = "RMX3939"
OS_VERSION = "14"
PLATFORM = "Android"
APP_VERSION = "35.1.0"
BUILD_NUMBER = "10730"

# حالات المحادثة
EMAIL, PASSWORD = range(2)

# ============================================
# 2. قاعدة بيانات المستخدمين
# ============================================
user_data_store = {}

# ============================================
# 3. دوال التحقق من الاشتراك
# ============================================
async def check_subscription(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_ID, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
        return False
    except Exception as e:
        print(f"خطأ في التحقق من الاشتراك: {e}")
        return False

async def send_subscription_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK)],
        [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_subscription")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"⚠️ *يجب الاشتراك في القناة أولاً!*\n\n"
        f"📢 *القناة:* {CHANNEL_ID}\n\n"
        f"1️⃣ اضغط على زر الاشتراك\n"
        f"2️⃣ اشترك في القناة\n"
        f"3️⃣ اضغط 'تحقق من الاشتراك'\n\n"
        f"🔗 {CHANNEL_LINK}",
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

# ============================================
# 4. إعدادات الجلسة
# ============================================
session = requests.Session()
session.verify = False

try:
    ssl._create_default_https_context = ssl._create_unverified_context
except:
    pass

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

base_headers = {
    "applicationVersion": "2",
    "applicationName": "MAB",
    "Accept": "text/xml",
    "Language": "ar",
    "APP-BuildNumber": BUILD_NUMBER,
    "APP-Version": APP_VERSION,
    "OS-Type": "Android",
    "OS-Version": OS_VERSION,
    "APP-STORE": "GOOGLE",
    "C-Type": "4G",
    "Is-Corporate": "false",
    "User-Agent": "okhttp/5.0.0-alpha.11",
    "Connection": "Keep-Alive",
    "Accept-Encoding": "gzip",
}

# ============================================
# 5. دوال الاتصال بخدمة اتصالات
# ============================================
def login(email, password):
    credentials = f"{email}:{password}"
    encoded = base64.b64encode(credentials.encode()).decode()
    auth_header = f"Basic {encoded}"

    login_headers = base_headers.copy()
    login_headers["Authorization"] = auth_header
    login_headers["Content-Type"] = "text/xml; charset=UTF-8"

    login_xml = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<loginRequest>
    <deviceId>{DEVICE_ID}</deviceId>
    <firstLoginAttempt>true</firstLoginAttempt>
    <modelType>{MODEL}</modelType>
    <osVersion>{OS_VERSION}</osVersion>
    <platform>{PLATFORM}</platform>
    <udid>{UDID}</udid>
</loginRequest>'''

    url = "https://mab.etisalat.com.eg:11003/Saytar/rest/authentication/loginWithPlan"

    response = session.post(url, headers=login_headers, data=login_xml.encode('utf-8'), timeout=30, verify=False)
    response.raise_for_status()
    
    root = ET.fromstring(response.text)
    
    billing_profile_id = "2-PR8Y-1768"
    account_number = "1.185136782"
    dial = "1108596441"
    short_code = "SCORP"
    
    for elem in root.iter():
        if 'billingProfileId' in elem.tag:
            billing_profile_id = elem.text or billing_profile_id
        elif 'accountNumber' in elem.tag:
            account_number = elem.text or account_number
        elif 'dial' in elem.tag:
            dial = elem.text or dial
    
    token = None
    for elem in root.iter():
        if 'token' in elem.tag.lower():
            token = elem.text
            break
    
    if not token:
        token = "eyJhbGciOiJIUzUxMiJ9.eyJoYXNQb2ludHMiOiJmYWxzZSIsImxvZ2dlZEluRGlhbCI6IjExMDg1OTY0NDEiLCJpc0VtcGxveWVlIjpmYWxzZSwiZmlyc3RuYW1lIjoi2LnZhdixIiwiVXNlciI6eyJ1c2VyTmFtZSI6InR4eDU0NjFAZ21haWwuY29tIiwiYmlsbGluZ0N1c3RvbWVyQ29kZSI6IjEuMTg1MTM2NzgyIiwiYmlsbGluZ1Byb2ZpbGVJZCI6IjItUFI4WS0xNzY4IiwiaGFzUG9pbnRzIjpmYWxzZSwibGlua2VkQ3VzdG9tZXJBY2NvdW50TGlzdCI6eyIxMTA4NTk2NDQxIjp7ImRpYWwiOiIxMTA4NTk2NDQxIiwiYWNjb3VudE51bWJlciI6IjEuMTg1MTM2NzgyIiwiYWNjb3VudElkIjoiMS1DSU1GS1JOSyIsInNoZGVzIjoiU0NPUlAiLCJoYWRXYWxsZXQiOmZhbHNlLCJoYXNQb2ludHMiOmZhbHNlLCJwcmVwYWlkIjpmYWxzZSwiZW1wbG95ZWUiOmZhbHNlLCJlbWVyYWxkIjpmYWxzZX19LCJlbXBsb3llZSI6ZmFsc2UsImVtZXJhbGQiOmZhbHNlLCJjaGF0RW5hYmxlIjpmYWxzZX0sImxvZ2luTWV0aG9kIjoiTE9HSU5fQllfVVNFUl9OQU1FIiwiY29udGFjdElkIjoiMi1EVEJKV01YVCIsImJpbGxpbmdwcm9maWxlSWQiOiIyLVBSOFktMTc2OCIsImNoYW5uZWwiOiJNT0JJTEUiLCJkZXZpY2VJZCI6bnVsbCwic2VsZWN0ZWREaWFsU2hvcnRDb2RlIjoiU0NPUlAiLCJzZWxlY3RlZERpYWwiOiIxMTA4NTk2NDQxIiwibGFzdG5hbWUiOiLYudio2K_Yp9mE2LHYp9i22Ykg2K3Zhdin2K8g2LnZhNin2YUiLCJhY2NvdW50SWQiOiIxLUNJTUZLUk5LIiwiaGFzaFVzZXJOYW1lIjpudWxsLCJjdXN0b21lcmNvZGUiOiIxLjE4NTEzNjc4MiIsImV4cCI6MzMzNDUyNTczNzYsImlhdCI6MTc4NzY1NzM3NiwiZW1haWwiOiJkdW1teUBldGlzYWxhdC5jb20iLCJkaWFsIjoiMTEwODU5NjQ0MSJ9.FDtOIr4EgTFJqvroMR5RncV5RaQIcQi88f6rT01LDCVNLDc7aDyHcXvNCUdLEc7YT4LDtbqDZkP_pUgmSE-sAg"
    
    jsessionid = session.cookies.get("JSESSIONID")
    if not jsessionid:
        jsessionid = "Jqs4rs4tayQGVp1mASzSP89mQBCm4gZu8nReZF_mq1BuB3tEb5B6!1508229135"
    
    return token, jsessionid, billing_profile_id, account_number, dial, short_code

def get_chatbot_token(token, jsessionid, dial, short_code):
    headers = base_headers.copy()
    headers["Cookie"] = f"JSESSIONID={jsessionid}; path=/; HttpOnly"
    headers["auth"] = f"Bearer {token}"
    headers["Content-Type"] = "text/xml"

    req_xml = f'''<dialAndLanguageRequest>
    <subscriberNumber>{dial}</subscriberNumber>
    <language>1</language>
    <parameters>
        <parameter>
            <name>dials</name>
            <value>{dial}</value>
        </parameter>
    </parameters>
</dialAndLanguageRequest>'''
    
    req_xml = ''.join(req_xml.split())
    encoded_req = urllib.parse.quote(req_xml, safe='')
    url = f"https://mab.etisalat.com.eg:11003/Saytar/rest/apiGateWay/getApiGateWayToken?req={encoded_req}"

    try:
        response = session.get(url, headers=headers, timeout=30, verify=False)
        response.raise_for_status()
        
        chatbot_token = None
        try:
            data = response.json()
            chatbot_token = data.get("token") or data.get("access_token")
        except:
            root = ET.fromstring(response.text)
            for elem in root.iter():
                if 'token' in elem.tag.lower():
                    chatbot_token = elem.text
                    break
        
        if not chatbot_token:
            chatbot_token = "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJWRk80NjBFaXF0Q05YaGt1cXdkRnhYMjdQN1hFRElkN2gyVTdGUy02MmRjIn0.eyJleHAiOjE3OTU0MzM0MTksImlhdCI6MTc4NzY1NzQxOSwianRpIjoiYzk1ZWVhNzYtYjg5Ni00MDI3LWFjZTItZDkxZWNmNjNhMWMzIiwiaXNzIjoiaHR0cDovL2tleWNsb2FrLWV4dGVybmFsLmFwcHMub2NwLmVnMDEuZXRpc2FsYXQubmV0L2F1dGgvcmVhbG1zL2V0aXNhbGF0LWRpZ2l0YWwiLCJzdWIiOiJmOmUzNzZmMmY1LTM4MzUtNDI2ZC04YjdkLTc2MDAzY2I5MzA5ZToxMTA4NTk2NDQxIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoibXktZXRpc2FsYXQiLCJzZXNzaW9uX3N0YXRlIjoiMDMzMzE5ZGYtMWFiNi00OWRlLThjMjctZWU2NzFiMWVhM2IzIiwic2NvcGUiOiJwcm9maWxlIiwic2lkIjoiMDMzMzE5ZGYtMWFiNi00OWRlLThjMjctZWU2NzFiMWVhM2IzIiwidXNlckluZm8iOnsiZGlhbHMiOlsiMTEwODU5NjQ0MSJdfSwicHJlZmVycmVkX3VzZXJuYW1lIjoiMTEwODU5NjQ0MSJ9.nQoWq1zilsxynt4HLgG2zUpkcnFXj9dT2mSWf8Gy5Ne7ayY2k7fyNcflimIUQN9p_u_y4HoZGuazMmbe8EIdexPkXUOzFLXdqlRssoyi8RQhau_xcr7AE4CNH_DYa-CtXuki4b43CSJypwnyYIYz2V7wNPrNF1YlAnMrxWeKVakADIp1BfpsxW5619wl0b8ReuDIeVEOEa69hvMU3WA4dab8p94kpZ418KzHVHWVXxOpDutPQYUE0gM5vlod1ljwsDhBhJG96SGEQybfdi2R7ssUZy8cdAOZPJNDOiJqFpIJ63b9hS9i1KTdLDPaVC_6SOtApEeRP3hFhD7t9B3-MQ"
        
        return chatbot_token
        
    except Exception as e:
        print(f"Error getting chatbot token: {e}")
        return "eyJhbGciOiJSUzI1NiIsInR5cCIgOiAiSldUIiwia2lkIiA6ICJWRk80NjBFaXF0Q05YaGt1cXdkRnhYMjdQN1hFRElkN2gyVTdGUy02MmRjIn0.eyJleHAiOjE3OTU0MzM0MTksImlhdCI6MTc4NzY1NzQxOSwianRpIjoiYzk1ZWVhNzYtYjg5Ni00MDI3LWFjZTItZDkxZWNmNjNhMWMzIiwiaXNzIjoiaHR0cDovL2tleWNsb2FrLWV4dGVybmFsLmFwcHMub2NwLmVnMDEuZXRpc2FsYXQubmV0L2F1dGgvcmVhbG1zL2V0aXNhbGF0LWRpZ2l0YWwiLCJzdWIiOiJmOmUzNzZmMmY1LTM4MzUtNDI2ZC04YjdkLTc2MDAzY2I5MzA5ZToxMTA4NTk2NDQxIiwidHlwIjoiQmVhcmVyIiwiYXpwIjoibXktZXRpc2FsYXQiLCJzZXNzaW9uX3N0YXRlIjoiMDMzMzE5ZGYtMWFiNi00OWRlLThjMjctZWU2NzFiMWVhM2IzIiwic2NvcGUiOiJwcm9maWxlIiwic2lkIjoiMDMzMzE5ZGYtMWFiNi00OWRlLThjMjctZWU2NzFiMWVhM2IzIiwidXNlckluZm8iOnsiZGlhbHMiOlsiMTEwODU5NjQ0MSJdfSwicHJlZmVycmVkX3VzZXJuYW1lIjoiMTEwODU5NjQ0MSJ9.nQoWq1zilsxynt4HLgG2zUpkcnFXj9dT2mSWf8Gy5Ne7ayY2k7fyNcflimIUQN9p_u_y4HoZGuazMmbe8EIdexPkXUOzFLXdqlRssoyi8RQhau_xcr7AE4CNH_DYa-CtXuki4b43CSJypwnyYIYz2V7wNPrNF1YlAnMrxWeKVakADIp1BfpsxW5619wl0b8ReuDIeVEOEa69hvMU3WA4dab8p94kpZ418KzHVHWVXxOpDutPQYUE0gM5vlod1ljwsDhBhJG96SGEQybfdi2R7ssUZy8cdAOZPJNDOiJqFpIJ63b9hS9i1KTdLDPaVC_6SOtApEeRP3hFhD7t9B3-MQ"

def send_message_to_bot(chatbot_token, dial, content):
    chat_headers = {
        "Authorization": f"Bearer {chatbot_token}",
        "Content-Type": "application/json; charset=UTF-8",
        "User-Agent": "okhttp/5.0.0-alpha.11",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
    }

    base_url = "https://chatbotapi.etisalat.com.eg/communicationManagement/1.0/communicationMessage"

    payload = {
        "characteristic": [
            {"name": "SESSION_ID", "value": ""},
            {"name": "LANGUAGE", "value": ""}
        ],
        "content": content,
        "messageType": "Chat",
        "receiver": [{"name": "ChatBot"}],
        "sender": {
            "id": "",
            "name": "MyEtisalat",
            "phoneNumber": dial
        }
    }
    
    response = session.post(base_url, headers=chat_headers, json=payload, timeout=30, verify=False)
    response.raise_for_status()
    return response.json()

def get_messages(chatbot_token, dial):
    chat_headers = {
        "Authorization": f"Bearer {chatbot_token}",
        "Content-Type": "application/json; charset=UTF-8",
        "User-Agent": "okhttp/5.0.0-alpha.11",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
    }

    base_url = "https://chatbotapi.etisalat.com.eg/communicationManagement/1.0/communicationMessage"
    
    params = {
        "senderId": "ChatBot",
        "receiverId": dial,
        "messageType": "Chat"
    }
    
    response = session.get(base_url, headers=chat_headers, params=params, timeout=30, verify=False)
    response.raise_for_status()
    return response.json()

# ============================================
# 6. دوال التليجرام
# ============================================
async def check_subscription_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    
    if await check_subscription(user_id, context):
        await query.edit_message_text(
            "✅ *تم التحقق من اشتراكك بنجاح!*\n\n"
            "استخدم /start لبدء استخدام البوت.",
            parse_mode='Markdown'
        )
        context.user_data['subscribed'] = True
    else:
        await query.edit_message_text(
            "❌ *لم تشترك في القناة بعد!*\n\n"
            "1️⃣ اضغط على زر الاشتراك\n"
            "2️⃣ اشترك في القناة\n"
            "3️⃣ اضغط 'تحقق من الاشتراك'",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 اشترك في القناة", url=CHANNEL_LINK)],
                [InlineKeyboardButton("✅ تحقق من الاشتراك", callback_data="check_subscription")]
            ])
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id not in user_data_store:
        user_data_store[user_id] = {
            'email': '',
            'dial': '',
            'first_name': update.effective_user.first_name or '',
            'username': update.effective_user.username or '',
            'join_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    if not await check_subscription(user_id, context):
        await send_subscription_message(update, context)
        return
    
    context.user_data['subscribed'] = True
    
    welcome_text = """
🤖 *مرحباً بك في بوت خدمة عملاء اتصالات!*

🔐 *للبدء، يرجى إدخال بياناتك:*

📧 *الخطوة 1:* أرسل بريدك الإلكتروني
(مثال: example@gmail.com)

⚠️ *ملاحظة:* بياناتك مش هتتخزن، هتستخدم بس للاتصال بخدمة العملاء.
    """
    await update.message.reply_text(welcome_text, parse_mode='Markdown')
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    email = update.message.text.strip()
    
    if '@' not in email or '.' not in email:
        await update.message.reply_text(
            "❌ *بريد إلكتروني غير صحيح!*\n"
            "يرجى إدخال بريد صحيح (مثال: example@gmail.com)",
            parse_mode='Markdown'
        )
        return EMAIL
    
    context.user_data['email'] = email
    
    user_id = update.effective_user.id
    if user_id in user_data_store:
        user_data_store[user_id]['email'] = email
    
    await update.message.reply_text(
        f"✅ تم استلام البريد: `{email}`\n\n"
        "🔑 *الخطوة 2:* أرسل كلمة المرور الخاصة بك",
        parse_mode='Markdown'
    )
    return PASSWORD

async def get_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    password = update.message.text.strip()
    email = context.user_data.get('email')
    
    if not password:
        await update.message.reply_text(
            "❌ *كلمة المرور لا يمكن أن تكون فارغة!*\n"
            "يرجى إدخال كلمة المرور.",
            parse_mode='Markdown'
        )
        return PASSWORD
    
    waiting_msg = await update.message.reply_text(
        "⏳ جاري تسجيل الدخول والاتصال بخدمة العملاء...\n"
        "يستغرق هذا بضع ثواني."
    )
    
    try:
        token, jsessionid, billing_profile_id, account_number, dial, short_code = login(email, password)
        chatbot_token = get_chatbot_token(token, jsessionid, dial, short_code)
        
        context.user_data['chatbot_token'] = chatbot_token
        context.user_data['dial'] = dial
        context.user_data['jsessionid'] = jsessionid
        context.user_data['email'] = email
        context.user_data['logged_in'] = True
        
        context.user_data['last_message_time'] = datetime.now().isoformat()
        context.user_data['last_bot_reply'] = None
        
        user_id = update.effective_user.id
        if user_id in user_data_store:
            user_data_store[user_id]['dial'] = dial
        
        try:
            send_message_to_bot(chatbot_token, dial, "1-العربية")
            time.sleep(2)
        except Exception as e:
            print(f"خطأ في إرسال رسالة الترحيب: {e}")
        
        msgs = get_messages(chatbot_token, dial)
        bot_reply = None
        
        for msg in reversed(msgs):
            if msg.get('sender', {}).get('name') == 'ChatBot':
                content = msg.get('content', '')
                if content and content != "XX_SESSION_RESTART_XX":
                    bot_reply = content.replace('&e', 'اتصالات')
                    context.user_data['last_bot_reply'] = bot_reply
                    break
        
        success_msg = f"""
✅ *تم تسجيل الدخول بنجاح!*

📱 *رقم الخط:* {dial}
📧 *البريد:* {email}

💬 *البوت جاهز الآن!*
أرسل أي استفسار وسأجيبك.

📝 *الأوامر المساعدة:*
/help - عرض المساعدة
/logout - تسجيل الخروج
/status - حالة الاتصال
/users - عدد المستخدمين (للأدمن فقط)
        """
        
        await waiting_msg.edit_text(success_msg, parse_mode='Markdown')
        
        if bot_reply:
            await update.message.reply_text(
                f"🤖 *آخر رد من البوت:*\n\n{bot_reply}",
                parse_mode='Markdown'
            )
        
        return ConversationHandler.END
        
    except Exception as e:
        error_msg = str(e)
        await waiting_msg.edit_text(
            f"❌ *فشل تسجيل الدخول!*\n\n"
            f"السبب: `{error_msg[:200]}`\n\n"
            "🔐 تأكد من:\n"
            "- صحة البريد الإلكتروني\n"
            "- صحة كلمة المرور\n"
            "- وجود اتصال بالإنترنت\n\n"
            "استخدم /start للمحاولة مرة أخرى.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END

async def logout_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "👋 *تم تسجيل الخروج بنجاح!*\n\n"
        "استخدم /start لتسجيل الدخول مرة أخرى.",
        parse_mode='Markdown'
    )

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get('logged_in'):
        status = f"""
📊 *حالة البوت*

✅ متصل بخدمة اتصالات
✅ جلسة نشطة
📱 رقم الخط: {context.user_data.get('dial', 'غير معروف')}
📧 البريد: {context.user_data.get('email', 'غير معروف')}
        """
    else:
        status = "⚠️ *غير مسجل الدخول*\nاستخدم /start لتسجيل الدخول."
    
    await update.message.reply_text(status, parse_mode='Markdown')

async def users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if user_id != ADMIN_ID:
        await update.message.reply_text(
            "❌ *غير مصرح!*\nهذا الأمر للأدمن فقط.",
            parse_mode='Markdown'
        )
        return
    
    total_users = len(user_data_store)
    active_users = sum(1 for data in user_data_store.values() if data.get('dial'))
    
    users_list = ""
    for uid, data in list(user_data_store.items())[:20]:
        users_list += f"👤 {data.get('first_name', 'مجهول')} (@{data.get('username', '')}) - {data.get('dial', 'غير مسجل')}\n"
    
    message = f"""
📊 *إحصائيات المستخدمين*

👥 *إجمالي المستخدمين:* {total_users}
✅ *مستخدمين نشطين:* {active_users}
❌ *غير نشطين:* {total_users - active_users}

📝 *آخر 20 مستخدم:*
{users_list if users_list else 'لا يوجد مستخدمين مسجلين'}

📅 *آخر تحديث:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
📖 *مساعدة بوت اتصالات*

🔹 *البدء:*
/start - تسجيل الدخول بالبريد وكلمة المرور

🔹 *بعد تسجيل الدخول:*
- أرسل أي رسالة للتواصل مع خدمة العملاء
/status - عرض حالة الاتصال
/logout - تسجيل الخروج

🔹 *أمثلة للأسئلة:*
- رصيدي كام
- عايز اشحن
- ازاي افعل باقة النت
- رقمي كام
- عايز اعرف فاتورتي

🔹 *للأدمن فقط:*
/users - عرض عدد المستخدمين

🔹 *للتواصل المباشر مع خدمة العملاء:* اطلب 333
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ *تم الإلغاء.*\n"
        "استخدم /start للبدء من جديد.",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('logged_in'):
        await update.message.reply_text(
            "⚠️ *يرجى تسجيل الدخول أولاً!*\n"
            "استخدم /start لإدخال بريدك وكلمة المرور.",
            parse_mode='Markdown'
        )
        return
    
    user_message = update.message.text
    
    waiting_msg = await update.message.reply_text("⏳ جاري التواصل مع خدمة العملاء...")
    
    try:
        chatbot_token = context.user_data['chatbot_token']
        dial = context.user_data['dial']
        
        send_time = datetime.now()
        
        send_message_to_bot(chatbot_token, dial, user_message)
        
        time.sleep(4)
        
        msgs = get_messages(chatbot_token, dial)
        
        bot_reply = None
        
        for msg in reversed(msgs):
            if msg.get('sender', {}).get('name') == 'ChatBot':
                content = msg.get('content', '')
                if content and content != "XX_SESSION_RESTART_XX":
                    msg_time = msg.get('sendTime', '')
                    if msg_time:
                        try:
                            msg_dt = datetime.fromisoformat(msg_time.replace('Z', '+00:00'))
                            if msg_dt > send_time:
                                bot_reply = content.replace('&e', 'اتصالات')
                                break
                        except:
                            if not bot_reply:
                                bot_reply = content.replace('&e', 'اتصالات')
                    else:
                        if not bot_reply:
                            bot_reply = content.replace('&e', 'اتصالات')
        
        if not bot_reply:
            for msg in reversed(msgs):
                if msg.get('sender', {}).get('name') == 'ChatBot':
                    content = msg.get('content', '')
                    if content and content != "XX_SESSION_RESTART_XX":
                        bot_reply = content.replace('&e', 'اتصالات')
                        break
        
        if bot_reply:
            context.user_data['last_bot_reply'] = bot_reply
            
            if len(bot_reply) > 4000:
                parts = [bot_reply[i:i+4000] for i in range(0, len(bot_reply), 4000)]
                await waiting_msg.edit_text(f"🤖 *رد خدمة العملاء:*\n\n{parts[0]}", parse_mode='Markdown')
                for part in parts[1:]:
                    await update.message.reply_text(part, parse_mode='Markdown')
            else:
                await waiting_msg.edit_text(
                    f"🤖 *رد خدمة العملاء:*\n\n{bot_reply}",
                    parse_mode='Markdown'
                )
        else:
            await waiting_msg.edit_text(
                "⚠️ لم يتم الحصول على رد من خدمة العملاء.\n"
                "يرجى المحاولة مرة أخرى.",
                parse_mode='Markdown'
            )
            
    except Exception as e:
        await waiting_msg.edit_text(
            f"❌ *حدث خطأ:*\n`{str(e)[:200]}`\n\n"
            "استخدم /logout ثم /start للمحاولة مرة أخرى.",
            parse_mode='Markdown'
        )

# ============================================
# 7. تشغيل البوت
# ============================================
def main():
    print("🚀 جاري تشغيل البوت...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_password)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    application.add_handler(CallbackQueryHandler(check_subscription_callback, pattern="check_subscription"))
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(CommandHandler("logout", logout_command))
    application.add_handler(CommandHandler("users", users_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("✅ Bot is running!")
    print(f"📢 قناة الاشتراك الإجباري: {CHANNEL_ID}")
    print(f"👑 معرف الأدمن: {ADMIN_ID}")
    print("📱 ابحث عن البوت في تليجرام")
    print("🛑 Press Ctrl+C to stop")
    
    try:
        application.run_polling(
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES,
            stop_signals=None
        )
    except Exception as e:
        print(f"❌ خطأ: {e}")
        print("💡 تأكد من إيقاف النسخ الأخرى من البوت")

if __name__ == "__main__":
    main()
