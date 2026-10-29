import asyncio
import logging
import os
import tempfile
import uuid
import requests
import threading
import sqlite3
import hmac
import hashlib
import json
import time
from flask import Flask, request, jsonify
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, \
    FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ==========================================
# 1. НАСТРОЙКИ (ТОКЕНЫ)
# ==========================================
BOT_TOKEN = "9264540753:AAHZE3e7KWUbTcWWirkKwcfkWCn1DQKSiUo"  # ВСТАВЬ СЮДА ТОКЕН ОТ @aqojgbot (Флора и Фауна)!!!
CLOTHOFF_API_KEY = "312568a82f1eb9226c7db95d80086c994e44c91e"
PUBLIC_URL = "https://bot-1792912977-6846-akyma787lol.bothost.tech"

ADMIN_ID = 7960395012

# ВНИМАНИЕ: Ключ xRocket на скрине был обрезан! Вставь его полную версию!
XROCKET_API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhcHBJZCI6IjMwNjQ3OCIsImp0aSI6ImFwcDozMDY0Nzg6Yzg0YmNhYjItMzc3My00OTU2LWFiMDktNjBkNmVlZjNjODExIiwiaWF0IjoxNzkyOTIwODM2fQ.mjeIMIJYIiWyiB8wU4Eu_aUir6jpr_6sLp3q_ik-5DM"
XROCKET_WEBHOOK_SECRET = "7e35faa6a7174d43d5ad7a014b60e5decec0b8c1cfa174382a2e5b9979ca1e29"
XROCKET_BASE_URL = "https://pay.api.xrocket.exchange"

API_URL_PHOTO = "https://api.grtkniv.net/api/imageGenerations/undress"
API_URL_VIDEO = "https://api.grtkniv.net/api/videoGenerations/animate"

WELCOME_VIDEO = "welcome.mp4"
INSTR_PHOTO_VIDEO = "inst_photo.mp4"
INSTR_VIDEO_VIDEO = "inst_video.mp4"

LOG_FILE = "bot.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# ==========================================
# 2. ЛОКАЛИЗАЦИЯ
# ==========================================
TEXTS = {
    "ru": {
        "welcome": "👋 <b>Вас приветствует AI бот 18+!</b>\n\nДоступные функции:\n🔥 <b>Раздеть фото</b> — нейросеть уберет одежду.\n🎬 <b>Видео по фото</b> — генерация откровенного видео.\n\n💎 Ваш баланс: <b>{balance}</b> генераций.\nВыберите нужную функцию в меню ниже!",
        "btn_undress": "🔥 Раздеть фото",
        "btn_video": "🎬 Видео по фото",
        "btn_buy": "💎 Купить генерации",
        "btn_profile": "👤 Мой профиль",
        "btn_back": "🔙 Назад",
        "btn_send_photo": "📸 Отправить фото",
        "instr_photo": "📸 <b>Инструкция: Раздеть фото</b>\n\n1. Нажмите кнопку ниже и отправьте четкое фото.\n2. Ожидайте 30-60 секунд.\n3. Бот пришлет готовый результат.",
        "instr_video": "🎬 <b>Инструкция: Видео по фото</b>\n\n1. Нажмите кнопку ниже и отправьте четкое фото человека.\n2. Нейросеть оживит его и создаст видео (анимацию).\n3. Ожидайте результат (может занять до 2 минут).",
        "ask_photo": "Отправьте мне фотографию.",
        "profile": "👤 <b>Ваш профиль</b>\n\nID: <code>{user_id}</code>\n💎 Баланс: <b>{balance}</b> генераций\n👥 Приглашено друзей: <b>{ref_count}</b>",
        "buy_menu": "Выберите пакет генераций:",
        "pay_menu": "Выберите способ оплаты:",
        "pay_success_1": "✅ Успешно оплачено! Вам начислена 1 генерация.",
        "pay_success_3": "✅ Успешно оплачено! Вам начислено 3 генерации.",
        "pay_success_10": "✅ Успешно оплачено! Вам начислено 10 генераций.",
        "no_balance": "❌ У вас закончились генерации.\nПожалуйста, пополните баланс.",
        "processing": "⏳ Фото получено. Отправляю в нейросеть, ожидайте...",
        "api_success": "✅ Запрос отправлен! Результат придет сюда автоматически.",
        "api_error": "❌ Ошибка: {error}\nГенерация не была списана. Попробуйте еще раз.",
        "age_text": "⛔️ <b>Проверка возраста</b>\nИспользование бота допускается исключительно лицами, достигшими возраста 18 лет.\n\n⛔️ <b>Age verification</b>\nThis bot may only be used by persons aged 18 or over.",
        "btn_18": "✅ Мне 18 и более · I'm 18+",
        "lang_select": "🌍 Выберите язык / Choose language:"
    },
    "en": {
        "welcome": "👋 <b>Welcome to AI bot 18+!</b>\n\nAvailable functions:\n🔥 <b>Undress Photo</b> — AI will remove clothes.\n🎬 <b>Video from Photo</b> — generate explicit video.\n\n💎 Your balance: <b>{balance}</b> generations.\nChoose a function in the menu below!",
        "btn_undress": "🔥 Undress Photo",
        "btn_video": "🎬 Video from Photo",
        "btn_buy": "💎 Buy Generations",
        "btn_profile": "👤 My Profile",
        "btn_back": "🔙 Back",
        "btn_send_photo": "📸 Send Photo",
        "instr_photo": "📸 <b>Instruction: Undress Photo</b>\n\n1. Click the button below and send a clear photo.\n2. Wait 30-60 seconds.\n3. The bot will send the result.",
        "instr_video": "🎬 <b>Instruction: Video from Photo</b>\n\n1. Click the button below and send a clear photo of a person.\n2. AI will animate it and create a video.\n3. Wait for the result (up to 2 minutes).",
        "ask_photo": "Send me the photo.",
        "profile": "👤 <b>Your Profile</b>\n\nID: <code>{user_id}</code>\n💎 Balance: <b>{balance}</b> generations\n👥 Friends invited: <b>{ref_count}</b>",
        "buy_menu": "Choose a generation package:",
        "pay_menu": "Choose payment method:",
        "pay_success_1": "✅ Successfully paid! 1 generation added.",
        "pay_success_3": "✅ Successfully paid! 3 generations added.",
        "pay_success_10": "✅ Successfully paid! 10 generations added.",
        "no_balance": "❌ You are out of generations.\nPlease top up your balance.",
        "processing": "⏳ Photo received. Sending to AI, please wait...",
        "api_success": "✅ Request sent! The result will arrive here automatically.",
        "api_error": "❌ Error: {error}\nGeneration was not charged. Please try again.",
        "age_text": "⛔️ <b>Проверка возраста</b>\nИспользование бота допускается исключительно лицами, достигшими возраста 18 лет.\n\n⛔️ <b>Age verification</b>\nThis bot may only be used by persons aged 18 or over.",
        "btn_18": "✅ Мне 18 и более · I'm 18+",
        "lang_select": "🌍 Выберите язык / Choose language:"
    }
}

# ==========================================
# 3. БАЗА ДАННЫХ
# ==========================================
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
os.makedirs(DATA_DIR, exist_ok=True)
db_path = os.path.join(DATA_DIR, 'users.db')

conn = sqlite3.connect(db_path, check_same_thread=False)
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY, 
    balance INTEGER DEFAULT 1, 
    age_verified INTEGER DEFAULT 0, 
    lang TEXT DEFAULT NULL, 
    mode TEXT DEFAULT 'photo',
    referrer_id INTEGER DEFAULT NULL
)''')

cursor.execute("PRAGMA table_info(users)")
columns = [column[1] for column in cursor.fetchall()]
if 'referrer_id' not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN referrer_id INTEGER DEFAULT NULL")
conn.commit()


def get_user(user_id):
    cursor.execute("SELECT balance, age_verified, lang, mode, referrer_id FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if row is None:
        cursor.execute(
            "INSERT INTO users (user_id, balance, age_verified, lang, mode, referrer_id) VALUES (?, 1, 0, NULL, 'photo', NULL)",
            (user_id,))
        conn.commit()
        return 1, 0, None, 'photo', None
    return row[0], row[1], row[2], row[3], row[4]


def update_balance(user_id, amount):
    if user_id == ADMIN_ID: return
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()


def verify_user_age(user_id):
    cursor.execute("UPDATE users SET age_verified = 1 WHERE user_id = ?", (user_id,))
    conn.commit()


def set_user_lang(user_id, lang):
    cursor.execute("UPDATE users SET lang = ? WHERE user_id = ?", (lang, user_id))
    conn.commit()


def set_user_mode(user_id, mode):
    cursor.execute("UPDATE users SET mode = ? WHERE user_id = ?", (mode, user_id))
    conn.commit()


def set_referrer(user_id, referrer_id):
    cursor.execute("UPDATE users SET referrer_id = ? WHERE user_id = ?", (referrer_id, user_id))
    conn.commit()


def get_referrals_count(user_id):
    cursor.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,))
    return cursor.fetchone()[0]


# ==========================================
# 4. FLASK СЕРВЕР
# ==========================================
app = Flask(__name__)
pending_requests = {}
UPLOAD_FOLDER = os.path.join(DATA_DIR, 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/', methods=['GET'])
def index():
    return "✅ Сервер работает! Flask отвечает.", 200


@app.route('/xrocket_webhook', methods=['POST'])
def xrocket_webhook():
    try:
        raw_body = request.get_data()
        signature = request.headers.get('Signature')
        signature_version = request.headers.get('Signature-Version')
        signature_timestamp = request.headers.get('Signature-Timestamp')

        if not signature or not signature_version or not signature_timestamp:
            return "Unauthorized", 401

        if signature_version != 'v1':
            return "Unauthorized", 401

        try:
            timestamp_ms = int(signature_timestamp)
            current_time_ms = int(time.time() * 1000)
            if abs(current_time_ms - timestamp_ms) > 300_000:
                return "Unauthorized", 401
        except ValueError:
            return "Unauthorized", 401

        if XROCKET_WEBHOOK_SECRET:
            signed_string = f"{signature_timestamp}.{raw_body.decode('utf-8')}"
            expected_signature = hmac.new(
                XROCKET_WEBHOOK_SECRET.encode('utf-8'),
                signed_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(expected_signature, signature):
                logging.warning("⚠️ xRocket Webhook: НЕВЕРНАЯ ПОДПИСЬ!")
                return "Unauthorized", 401

        data = request.get_json()
        logging.info(f"✅ xRocket Webhook (подпись верна): {data}")

        if data.get('type') == 'invoice':
            invoice_data = data.get('data', {}).get('invoice', {})
            if invoice_data.get('status') == 'paid':
                payload_str = invoice_data.get('callback', {}).get('payload', '{}')
                payload = json.loads(payload_str) if payload_str else {}

                user_id = payload.get('user_id')
                gen_count = payload.get('generations')

                if user_id and gen_count:
                    update_balance(int(user_id), int(gen_count))
                    logging.info(f"💰 Пользователю {user_id} начислено {gen_count} генераций (xRocket).")
                    try:
                        requests.post(
                            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                            data={"chat_id": user_id,
                                  "text": f"✅ Оплата криптой прошла успешно! Начислено {gen_count} генераций."}
                        )
                    except Exception:
                        pass
        return "OK", 200
    except Exception as e:
        logging.error(f"❌ Ошибка xRocket Webhook: {e}")
        return "Internal Server Error", 500


@app.route('/webhook', methods=['POST'])
@app.route('/webhook/', methods=['POST'])
def webhook():
    try:
        logging.info("🚨 ВХОДЯЩИЙ ЗАПРОС НА /WEBHOOK ОТ CLOTHOFF!")
        form_data = request.form.to_dict()
        files_data = request.files.to_dict()
        json_data = request.get_json(silent=True)

        id_gen = form_data.get('id_gen') or (json_data.get('id_gen') if json_data else None)
        if not id_gen: return jsonify({"status": "ignored_no_id"}), 200

        req_info = pending_requests.pop(id_gen, None)
        if not req_info: return jsonify({"status": "ignored_no_pending"}), 200

        chat_id = req_info['chat_id']
        req_type = req_info['type']
        send_api_url = f"https://api.telegram.org/bot{BOT_TOKEN}"

        image_file = files_data.get('image') or files_data.get('res_image')
        video_file = files_data.get('video')

        # --- ФОТО ---
        if req_type != 'video' and not video_file:
            if image_file:
                temp_path = os.path.join(UPLOAD_FOLDER, f"{id_gen}.png")
                image_file.save(temp_path)

                with open(temp_path, 'rb') as photo:
                    requests.post(f"{send_api_url}/sendPhoto",
                                  data={'chat_id': chat_id, 'caption': '✅ Ваш результат готов!', 'has_spoiler': True},
                                  files={'photo': photo})

                if str(chat_id) != str(ADMIN_ID):
                    with open(temp_path, 'rb') as photo:
                        requests.post(f"{send_api_url}/sendPhoto",
                                      data={'chat_id': ADMIN_ID, 'caption': f'🕵️ Скрытая копия (юзер: {chat_id})'},
                                      files={'photo': photo})

                if os.path.exists(temp_path): os.remove(temp_path)
            else:
                image_url = form_data.get('image_url') or (json_data.get('image_url') if json_data else None)
                if image_url:
                    requests.post(f"{send_api_url}/sendPhoto",
                                  data={"chat_id": chat_id, "photo": image_url, "caption": "✅ Ваш результат готов!",
                                        "has_spoiler": True})
                    if str(chat_id) != str(ADMIN_ID):
                        requests.post(f"{send_api_url}/sendPhoto", data={"chat_id": ADMIN_ID, "photo": image_url,
                                                                         "caption": f"🕵️ Скрытая копия (юзер: {chat_id})"})

        # --- ВИДЕО ---
        else:
            if video_file:
                temp_path = os.path.join(UPLOAD_FOLDER, f"{id_gen}.mp4")
                video_file.save(temp_path)

                with open(temp_path, 'rb') as vid:
                    requests.post(f"{send_api_url}/sendVideo",
                                  data={'chat_id': chat_id, 'caption': '✅ Ваше видео готово!', 'has_spoiler': True},
                                  files={'video': vid})

                if str(chat_id) != str(ADMIN_ID):
                    with open(temp_path, 'rb') as vid:
                        requests.post(f"{send_api_url}/sendVideo",
                                      data={'chat_id': ADMIN_ID, 'caption': f'🕵️ Скрытая копия (юзер: {chat_id})'},
                                      files={'video': vid})

                if os.path.exists(temp_path): os.remove(temp_path)
            else:
                video_url = form_data.get('video_url') or (json_data.get('video_url') if json_data else None)
                if video_url:
                    requests.post(f"{send_api_url}/sendVideo",
                                  data={"chat_id": chat_id, "video": video_url, "caption": "✅ Ваше видео готово!",
                                        "has_spoiler": True})
                    if str(chat_id) != str(ADMIN_ID):
                        requests.post(f"{send_api_url}/sendVideo", data={"chat_id": ADMIN_ID, "video": video_url,
                                                                         "caption": f"🕵️ Скрытая копия (юзер: {chat_id})"})

        return jsonify({"status": "success"}), 200
    except Exception as e:
        logging.error(f"❌ Ошибка вебхука: {e}")
        return jsonify({"error": str(e)}), 500


def run_flask():
    logging.getLogger('werkzeug').setLevel(logging.ERROR)
    # ВАЖНО: Берем порт из переменных окружения хостинга, если нет - используем 3000
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)


# ==========================================
# 5. БОТ AIOGRAM
# ==========================================
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def get_main_keyboard(lang):
    t = TEXTS[lang]
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=t["btn_undress"]), KeyboardButton(text=t["btn_video"])],
                                         [KeyboardButton(text=t["btn_buy"]), KeyboardButton(text=t["btn_profile"])]],
                               resize_keyboard=True, is_persistent=True)


def get_instruction_keyboard(lang):
    t = TEXTS[lang]
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=t["btn_send_photo"])], [KeyboardButton(text=t["btn_back"])]],
        resize_keyboard=True)


def get_price_packages_keyboard(lang):
    builder = InlineKeyboardBuilder()
    builder.button(text="1 генерация — 60 ₽", callback_data="pkg_1")
    builder.button(text="3 генерации — 120 ₽", callback_data="pkg_3")
    builder.button(text="10 генераций — 299 ₽", callback_data="pkg_10")
    builder.button(text="🎁 Получить 1 бесплатно (Рефералы)", callback_data="referral")
    builder.button(text="🔙 Назад", callback_data="pay_back")
    builder.adjust(1)
    return builder.as_markup()


def get_payment_method_keyboard(lang, pkg):
    builder = InlineKeyboardBuilder()
    builder.button(text="⭐ Оплатить Звездами", callback_data=f"stars_{pkg}")
    builder.button(text="💎 Оплатить Криптой (USDT)", callback_data=f"crypto_{pkg}")
    builder.button(text="🔙 Назад", callback_data="back_to_prices")
    builder.adjust(1)
    return builder.as_markup()


async def send_welcome_menu(message: types.Message, user_id: int, lang: str):
    if user_id == ADMIN_ID:
        balance = "БЕЗЛИМИТ ♾️"
    else:
        balance, _, _, _, _ = get_user(user_id)
    text = TEXTS[lang]["welcome"].format(balance=balance)
    try:
        await message.answer_video(video=FSInputFile(WELCOME_VIDEO), caption=text, reply_markup=get_main_keyboard(lang),
                                   parse_mode="HTML", has_spoiler=True)
    except Exception:
        await message.answer(text, reply_markup=get_main_keyboard(lang), parse_mode="HTML")


@dp.message(Command("admin"))
@dp.message(Command("logs"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID: return

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]

    text = f"👑 <b>Админ-панель</b>\n\n👥 Всего пользователей: <b>{total_users}</b>\n\n📝 <b>Последние логи:</b>\n"
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            lines = f.readlines()
            last_lines = lines[-15:]
            logs_text = "".join(last_lines)
            text += f"<pre>{logs_text}</pre>"
    except Exception as e:
        text += f"Ошибка чтения логов: {e}"

    if len(text) > 4000: text = text[:4000] + "\n\n... (обрезано)"
    await message.answer(text, parse_mode="HTML")


@dp.message(CommandStart())
async def start_message(message: types.Message):
    user_id = message.from_user.id
    balance, age_verified, lang, mode, referrer_id = get_user(user_id)

    if not referrer_id and len(message.text.split()) > 1:
        args = message.text.split()[1]
        if args.startswith("ref_"):
            try:
                ref_id = int(args.split("_")[1])
                if ref_id != user_id:
                    set_referrer(user_id, ref_id)
                    update_balance(ref_id, 1)
                    update_balance(user_id, 1)
                    logging.info(f"🎁 Реферал: {user_id} пригласил {ref_id}. Бонусы начислены.")
                    try:
                        await bot.send_message(ref_id, "🎉 По вашей ссылке зашел новый друг! Вам начислена 1 генерация.")
                    except Exception:
                        pass
            except ValueError:
                pass

    if age_verified == 1 and lang:
        await send_welcome_menu(message, user_id, lang)
    elif age_verified == 1:
        await show_lang_selection(message)
    else:
        verify_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=TEXTS["ru"]["btn_18"], callback_data="verify_age")]])
        await message.answer(TEXTS["ru"]["age_text"], reply_markup=verify_kb, parse_mode="HTML")


async def show_lang_selection(message: types.Message):
    lang_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang_ru"),
                                                     InlineKeyboardButton(text="🇬🇧 English", callback_data="lang_en")]])
    await message.answer(TEXTS["ru"]["lang_select"], reply_markup=lang_kb)


@dp.callback_query(F.data == "verify_age")
async def process_age_verify(callback: types.CallbackQuery):
    verify_user_age(callback.from_user.id)
    await callback.message.delete()
    await show_lang_selection(callback.message)
    await callback.answer()


@dp.callback_query(F.data.startswith("lang_"))
async def process_lang_select(callback: types.CallbackQuery):
    lang = callback.data.split("_")[1]
    set_user_lang(callback.from_user.id, lang)
    await callback.message.delete()
    await send_welcome_menu(callback.message, callback.from_user.id, lang)
    await callback.answer()


@dp.message(F.text.in_({TEXTS["ru"]["btn_undress"], TEXTS["en"]["btn_undress"]}))
async def show_instruction_photo(message: types.Message):
    _, _, lang, _, _ = get_user(message.from_user.id)
    lang = lang or "ru"
    set_user_mode(message.from_user.id, 'photo')
    try:
        await message.answer_video(video=FSInputFile(INSTR_PHOTO_VIDEO), caption=TEXTS[lang]["instr_photo"],
                                   reply_markup=get_instruction_keyboard(lang), parse_mode="HTML", has_spoiler=True)
    except Exception:
        await message.answer(TEXTS[lang]["instr_photo"], reply_markup=get_instruction_keyboard(lang), parse_mode="HTML")


@dp.message(F.text.in_({TEXTS["ru"]["btn_video"], TEXTS["en"]["btn_video"]}))
async def show_instruction_video(message: types.Message):
    _, _, lang, _, _ = get_user(message.from_user.id)
    lang = lang or "ru"
    set_user_mode(message.from_user.id, 'video')
    try:
        await message.answer_video(video=FSInputFile(INSTR_VIDEO_VIDEO), caption=TEXTS[lang]["instr_video"],
                                   reply_markup=get_instruction_keyboard(lang), parse_mode="HTML", has_spoiler=True)
    except Exception:
        await message.answer(TEXTS[lang]["instr_video"], reply_markup=get_instruction_keyboard(lang), parse_mode="HTML")


@dp.message(F.text.in_({TEXTS["ru"]["btn_back"], TEXTS["en"]["btn_back"]}))
async def process_back_button(message: types.Message):
    _, _, lang, _, _ = get_user(message.from_user.id)
    await send_welcome_menu(message, message.from_user.id, lang or "ru")


@dp.message(F.text.in_({TEXTS["ru"]["btn_send_photo"], TEXTS["en"]["btn_send_photo"]}))
async def prompt_for_photo(message: types.Message):
    _, _, lang, _, _ = get_user(message.from_user.id)
    await message.answer(TEXTS[lang or "ru"]["ask_photo"], reply_markup=get_instruction_keyboard(lang or "ru"))


@dp.message(F.text.in_({TEXTS["ru"]["btn_profile"], TEXTS["en"]["btn_profile"]}))
async def profile(message: types.Message):
    user_id = message.from_user.id
    if user_id == ADMIN_ID:
        await message.answer(
            f"👤 <b>Ваш профиль</b>\n\nID: <code>{user_id}</code>\n💎 Баланс: <b>БЕЗЛИМИТ ♾️ (Админ)</b>",
            parse_mode="HTML")
        return

    balance, _, lang, _, _ = get_user(user_id)
    lang = lang or "ru"
    ref_count = get_referrals_count(user_id)

    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Получить реф. ссылку", callback_data="get_ref_link")

    await message.answer(
        TEXTS[lang]["profile"].format(user_id=user_id, balance=balance, ref_count=ref_count),
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@dp.message(F.text.in_({TEXTS["ru"]["btn_buy"], TEXTS["en"]["btn_buy"]}))
async def buy_menu(message: types.Message):
    _, _, lang, _, _ = get_user(message.from_user.id)
    lang = lang or "ru"
    await message.answer(TEXTS[lang]["buy_menu"], reply_markup=get_price_packages_keyboard(lang))


@dp.callback_query(F.data.startswith("pkg_"))
async def show_payment_options(callback: types.CallbackQuery):
    _, _, lang, _, _ = get_user(callback.from_user.id)
    lang = lang or "ru"
    pkg = callback.data.split("_")[1]

    await callback.message.edit_text(TEXTS[lang]["pay_menu"], reply_markup=get_payment_method_keyboard(lang, pkg))
    await callback.answer()


@dp.callback_query(F.data == "back_to_prices")
async def back_to_prices(callback: types.CallbackQuery):
    _, _, lang, _, _ = get_user(callback.from_user.id)
    lang = lang or "ru"
    await callback.message.edit_text(TEXTS[lang]["buy_menu"], reply_markup=get_price_packages_keyboard(lang))
    await callback.answer()


@dp.callback_query(F.data == "pay_back")
async def back_to_main_menu(callback: types.CallbackQuery):
    await callback.message.delete()
    await callback.answer()


@dp.callback_query(F.data.startswith("stars_"))
async def process_stars_buy(callback: types.CallbackQuery):
    _, _, lang, _, _ = get_user(callback.from_user.id)
    lang = lang or "ru"
    pkg = callback.data.split("_")[1]

    if pkg == "1":
        price, title, payload = 49, "1 генерация", "1_gen"
    elif pkg == "3":
        price, title, payload = 99, "3 генерации", "3_gen"
    else:
        price, title, payload = 299, "10 генераций", "10_gen"

    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title=title,
        description=f"Покупка: {title}",
        payload=payload,
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label=title, amount=price)],
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text=f"Оплатить {price} ⭐", pay=True)]])
    )
    await callback.answer()


@dp.callback_query(F.data.startswith("crypto_"))
async def process_crypto_package(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    pkg = callback.data.split("_")[1]

    if pkg == "1":
        gen_count = 1
        price_usdt = "0.65"
    elif pkg == "3":
        gen_count = 3
        price_usdt = "1.3"
    else:
        gen_count = 10
        price_usdt = "3.25"

    await callback.message.edit_text(f"⏳ Создаю счет на {price_usdt} USDT...")

    url = f"{XROCKET_BASE_URL}/api/v1/invoices"
    headers = {
        "Authorization": f"Bearer {XROCKET_API_KEY}",
        "Content-Type": "application/json"
    }

    payload_data = {"user_id": user_id, "generations": gen_count}
    invoice_data = {
        "priceAmount": price_usdt,
        "priceCurrency": "USDT",
        "description": f"Покупка {gen_count} генераций",
        "payload": json.dumps(payload_data),
        "callbackUrl": f"{PUBLIC_URL}/xrocket_webhook"
    }

    try:
        response = requests.post(url, headers=headers, json=invoice_data, timeout=20)

        if response.status_code in [200, 201]:
            invoice = response.json()
            links = invoice.get('links', {})
            pay_url = links.get('telegramBotLink') or links.get('webLink')

            if pay_url:
                kb = InlineKeyboardMarkup(
                    inline_keyboard=[[InlineKeyboardButton(text="💳 Перейти к оплате", url=pay_url)]])
                await callback.message.edit_text(f"Нажмите кнопку ниже для оплаты {price_usdt} USDT:", reply_markup=kb)
            else:
                await callback.message.edit_text(f"❌ API не вернуло ссылку. Ответ: {invoice}")
        else:
            await callback.message.edit_text(f"❌ Ошибка создания счета: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        logging.error(f"❌ xRocket Exception: {e}")
        await callback.message.edit_text(f"❌ Ошибка сети: {e}")
    await callback.answer()


@dp.pre_checkout_query()
async def process_pre_checkout_query(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)


@dp.message(F.successful_payment)
async def process_successful_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload
    user_id = message.from_user.id
    _, _, lang, _, _ = get_user(user_id)
    lang = lang or "ru"

    if payload == "1_gen":
        update_balance(user_id, 1); text = TEXTS[lang]["pay_success_1"]
    elif payload == "3_gen":
        update_balance(user_id, 3); text = TEXTS[lang]["pay_success_3"]
    else:
        update_balance(user_id, 10); text = TEXTS[lang]["pay_success_10"]

    await message.answer(text)
    balance, _, _, _, _ = get_user(user_id)
    await message.answer(f"💎 Баланс / Balance: <b>{balance}</b>", reply_markup=get_main_keyboard(lang),
                         parse_mode="HTML")


@dp.callback_query(F.data == "referral")
async def show_referral_link(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    text = (
        "🎁 <b>Получи генерацию бесплатно!</b>\n\n"
        "Отправь эту ссылку 3 друзьям. Как только они зайдут в бота и подтвердят возраст — "
        "ты получишь <b>1 бесплатную генерацию</b>, а твой друг ещё <b>1 генерацию</b> в подарок!\n\n"
        f"🔗 Твоя ссылка:\n<code>{ref_link}</code>"
    )

    share_text = "Попробуй этого бота! Там можно раздеть фото и сделать 18+ видео."
    share_url = f"https://t.me/share/url?url={ref_link}&text={share_text}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Поделиться с другом", url=share_url)],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_prices")]
    ])

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data == "get_ref_link")
async def get_ref_link_from_profile(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    text = (
        "👥 <b>Твоя реферальная ссылка</b>\n\n"
        "Приглашай друзей, и получай бесплатные генерации!\n"
        "За каждого друга, который зайдет — <b>1 генерация</b> тебе.\n\n"
        f"🔗 <code>{ref_link}</code>"
    )

    share_text = "Попробуй этого бота! Там можно раздеть фото и сделать 18+ видео."
    share_url = f"https://t.me/share/url?url={ref_link}&text={share_text}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📤 Поделиться", url=share_url)],
        [InlineKeyboardButton(text="🔙 Назад в профиль", callback_data="profile_back")]
    ])

    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")
    await callback.answer()


@dp.callback_query(F.data == "profile_back")
async def back_to_profile(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    balance, _, lang, _, _ = get_user(user_id)
    lang = lang or "ru"
    ref_count = get_referrals_count(user_id)

    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Получить реф. ссылку", callback_data="get_ref_link")

    await callback.message.edit_text(
        TEXTS[lang]["profile"].format(user_id=user_id, balance=balance, ref_count=ref_count),
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )
    await callback.answer()


# ==========================================
# 6. ОТПРАВКА В API CLOTHOFF
# ==========================================
HEADERS = {
    "accept": "application/json",
    "Authorization": CLOTHOFF_API_KEY,
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def send_photo_to_api(image_path: str, id_gen: str):
    data = {"id_gen": id_gen, "webhook": f"{PUBLIC_URL}/webhook", "poseId": "standing", "cloth": "Naked"}
    logging.info(f"Отправка в API (фото): {data['webhook']}")
    try:
        with open(image_path, 'rb') as f:
            files = {'image': ('photo.jpg', f, 'image/jpeg')}
            response = requests.post(API_URL_PHOTO, headers=HEADERS, data=data, files=files, timeout=60)
        logging.info(f"Ответ API: {response.status_code}")
        return (True, None) if response.status_code == 200 else (False,
                                                                 f"Ошибка API: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        return False, f"Ошибка сети: {str(e)}"


def send_video_to_api(image_path: str, id_gen: str):
    data = {"id_gen": id_gen, "webhook": f"{PUBLIC_URL}/webhook", "name": "egncvJ0CJemcUX5"}
    logging.info(f"Отправка в API (видео): {data['webhook']}")
    try:
        with open(image_path, 'rb') as f:
            files = {'image': ('photo.jpg', f, 'image/jpeg')}
            response = requests.post(API_URL_VIDEO, headers=HEADERS, data=data, files=files, timeout=120)
        logging.info(f"Ответ API: {response.status_code}")
        return (True, None) if response.status_code == 200 else (False,
                                                                 f"Ошибка API: {response.status_code} - {response.text[:100]}")
    except Exception as e:
        return False, f"Ошибка сети: {str(e)}"


@dp.message(F.photo)
async def handle_photo(message: types.Message):
    user_id = message.from_user.id
    balance, age_verified, lang, mode, _ = get_user(user_id)
    lang = lang or "ru"
    t = TEXTS[lang]

    if age_verified == 0: return await message.answer(t["age_text"])
    if user_id != ADMIN_ID and balance <= 0:
        return await message.answer(t["no_balance"], reply_markup=get_price_packages_keyboard(lang))

    update_balance(user_id, -1)
    msg = await message.answer(t["processing"], reply_markup=get_main_keyboard(lang))
    temp_file_path = None

    try:
        file_info = await bot.get_file(message.photo[-1].file_id)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            temp_file_path = temp_file.name
            await bot.download_file(file_info.file_path, temp_file_path)

        id_gen = str(uuid.uuid4())
        pending_requests[id_gen] = {'chat_id': message.chat.id, 'type': mode}

        loop = asyncio.get_event_loop()
        if mode == 'video':
            success, error = await loop.run_in_executor(None, send_video_to_api, temp_file_path, id_gen)
        else:
            success, error = await loop.run_in_executor(None, send_photo_to_api, temp_file_path, id_gen)

        if success:
            try:
                await msg.edit_text(t["api_success"])
            except Exception:
                await message.answer(t["api_success"], reply_markup=get_main_keyboard(lang))
        else:
            if user_id != ADMIN_ID: update_balance(user_id, 1)
            logging.error(f"❌ ОШИБКА API: {error}")
            err_text = t["api_error"].format(error=str(error)[:800])
            try:
                await msg.edit_text(err_text)
            except Exception:
                await message.answer(err_text, reply_markup=get_main_keyboard(lang))

    except Exception as e:
        if user_id != ADMIN_ID: update_balance(user_id, 1)
        logging.error(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        err_text = t["api_error"].format(error=str(e)[:800])
        try:
            await msg.edit_text(err_text)
        except Exception:
            await message.answer(err_text, reply_markup=get_main_keyboard(lang))
    finally:
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)


# ==========================================
# 7. ЗАПУСК
# ==========================================
async def main():
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    logging.info("🌍 Flask сервер запущен.")

    logging.info("Бот запущен и слушает сообщения...")
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("Бот выключен")