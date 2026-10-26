"""
BOT BÁN CODE TELEGRAM - BẢN POSTGRESQL + EMOJI PREMIUM
Biến môi trường bắt buộc: BOT_TOKEN, DATABASE_URL
Tùy chọn: PREMIUM_EMOJI=0 để tắt emoji premium (dùng emoji thường)
Chạy: python bot.py
"""
import asyncio
import html
import logging
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone

import asyncpg
from aiogram import BaseMiddleware, Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BotCommand, BotCommandScopeChat, CallbackQuery, ErrorEvent,
    InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, Message,
    ReplyKeyboardMarkup,
)
from aiohttp import web

# ===================== CẤU HÌNH (đọc từ biến môi trường) =====================
try:                                    # chạy trên máy: tự đọc file .env nếu có
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not BOT_TOKEN or not DATABASE_URL:
    sys.exit("Thiếu BOT_TOKEN hoặc DATABASE_URL. Xem file .env.example")

ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "7884394252").replace(" ", "").split(",") if x}
SUPPORT = os.getenv("SUPPORT", "@dinhcong98")

BANK_CODE = os.getenv("BANK_CODE", "MB")
BANK_NAME = os.getenv("BANK_NAME", "MBBANK")
ACCOUNT_NO = os.getenv("ACCOUNT_NO", "0003456712345")
ACCOUNT_NAME = os.getenv("ACCOUNT_NAME", "LY THI CHAM")
TRANSFER_PREFIX = os.getenv("TRANSFER_PREFIX", "lixisinhnhat")

SEPAY_KEY = os.getenv("SEPAY_KEY", "")
WEB_PORT = int(os.getenv("PORT", "8080"))

MIN_DEPOSIT = 10_000
MAX_DEPOSIT = 50_000_000
THROTTLE = 0.5
VN_TZ = timezone(timedelta(hours=7))

DEFAULT_GATES = {
    "LLWIN": (90_000, "188 ĐIỂM"),
    "XX88": (80_000, "188 ĐIỂM"),
    "8KBET": (8_000, "18-28-38 ĐIỂM"),
    "SHBET": (80_000, "188 ĐIỂM"),
    "78WIN": (90_000, "188 ĐIỂM"),
    "C168": (75_000, "188 ĐIỂM"),
    "HI88": (90_000, "188 ĐIỂM"),
    "QQ88": (90_000, "188 ĐIỂM"),
    "FLY88": (75_000, "188 ĐIỂM"),
    "ON68": (82_000, "188 ĐIỂM"),
    "SC88": (77_000, "188 ĐIỂM"),
    "OK9": (10_000, "RANDOM"),
}
EXTRA = [(140_000, "288 ĐIỂM"), (280_000, "588 ĐIỂM"), (450_000, "888 ĐIỂM")]

# ===================== EMOJI PREMIUM =====================
# Đặt PREMIUM_EMOJI=0 trong Railway Variables để quay về emoji thường.
PREMIUM = os.getenv("PREMIUM_EMOJI", "1") != "0"


def ce(char: str, eid: str) -> str:
    """Emoji premium (tg-emoji). Nếu tắt hoặc bot không đủ quyền thì Telegram hiện emoji thường."""
    return f'<tg-emoji emoji-id="{eid}">{char}</tg-emoji>' if PREMIUM else char


def icon(eid: str) -> dict:
    return {"icon_custom_emoji_id": eid} if PREMIUM else {}


E_OK = ce("✅", "6165926565638051547")
E_NO = ce("❌", "5238037944064811339")
E_BAN = ce("🚫", "5238037944064811339")
E_WARN = ce("⚠️", "5395695537687123235")
E_WAIT = ce("⏳", "5386367538735104399")
E_CARD = ce("💳", "5445353829304387411")
E_MONEY = ce("💰", "5278467510604160626")
E_CASH = ce("💵", "5231005931550030290")
E_BANK = ce("🏦", "5332455502917949981")
E_CART = ce("🛒", "5312361253610475399")
E_IN = ce("📥", "5443127283898405358")
E_NOTE = ce("📝", "5395444784611480792")
E_EDIT = ce("✍️", "5395444784611480792")
E_LIST = ce("📜", "5397782960512444700")
E_HELP = ce("🆘", "5285238101344544669")
E_GAME = ce("🎮", "5280816565657300091")
E_NEW = ce("🛎", "5253742260054409879")
E_ADMIN = ce("🛠", "5193177581888755275")
E_INFO = ce("ℹ️", "5262844652964303985")
E_USER = ce("👤", "5251203410396458957")
E_HI = ce("👋", "6190629722876023613")
E_HEART = ce("💙", "5197387964098813812")
E_PLUS = ce("➕", "5397916757333654639")
E_MEGA = ce("📢", "5415655814079723871")
E_TARGET = ce("🎯", "5256131095094652290")
E_WELCOME = ce("👅", "6192771593001767805")

# 6 emoji premium cho menu: 5 nút + 1 ở lời chào (E_WELCOME)
MENU_ICONS = {
    "TÀI KHOẢN": "5217822164362739968",   # 👑
    "NẠP TIỀN": "5427168083074628963",    # 💎
    "MUA HÀNG": "6102831593389299866",    # 🌟
    "LỊCH SỬ": "6280407793631498213",     # 🚗
    "HỖ TRỢ": "5314504236132747481",      # ⁉️
}


def make_menu(use_icons: bool) -> ReplyKeyboardMarkup:
    def b(text):
        extra = icon(MENU_ICONS[text]) if use_icons else {}
        return KeyboardButton(text=text, **extra)

    return ReplyKeyboardMarkup(
        keyboard=[
            [b("TÀI KHOẢN"), b("NẠP TIỀN")],
            [b("MUA HÀNG"), b("LỊCH SỬ")],
            [b("HỖ TRỢ")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Chọn chức năng bên dưới 👇",
    )


MENU = make_menu(True)
MENU_PLAIN = make_menu(False)


async def answer_menu(m: Message, text: str):
    """Gửi kèm menu; nếu Telegram từ chối icon premium thì gửi menu thường."""
    try:
        await m.answer(text, reply_markup=MENU)
    except TelegramBadRequest:
        await m.answer(text, reply_markup=MENU_PLAIN)


# ===================== DATABASE (PostgreSQL) =====================
SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
    id BIGINT PRIMARY KEY,
    balance BIGINT NOT NULL DEFAULT 0,
    total_deposit BIGINT NOT NULL DEFAULT 0,
    joined TIMESTAMPTZ NOT NULL DEFAULT now(),
    name TEXT, username TEXT,
    banned BOOLEAN NOT NULL DEFAULT FALSE);
CREATE TABLE IF NOT EXISTS deposits(
    id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL, amount BIGINT NOT NULL,
    note TEXT, created TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS orders(
    id BIGSERIAL PRIMARY KEY, user_id BIGINT NOT NULL, gate TEXT NOT NULL,
    price BIGINT NOT NULL, points TEXT, login TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE TABLE IF NOT EXISTS bank_tx(id TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS products(
    gate TEXT PRIMARY KEY, price BIGINT NOT NULL, points TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE, pos INT NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_deposits_user ON deposits(user_id);
"""

pool: asyncpg.Pool = None


async def init_db():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    async with pool.acquire() as c:
        await c.execute(SCHEMA)
        for pos, (g, (p, pt)) in enumerate(DEFAULT_GATES.items()):
            await c.execute("INSERT INTO products(gate, price, points, pos) VALUES($1,$2,$3,$4) "
                            "ON CONFLICT (gate) DO NOTHING", g, p, pt, pos)


def fmt(dt):
    return dt.astimezone(VN_TZ).strftime("%H:%M:%S %d/%m/%Y")


def money(n):
    return f"{int(n):,}".replace(",", ".") + "đ"


def esc(s):
    return html.escape(str(s or ""))


def parse_amount(s: str):
    """'30000' | '30.000' | '30k' -> int, hoặc None nếu sai."""
    s = s.lower().replace(".", "").replace(",", "")
    mult = 1
    if s.endswith("k"):
        s, mult = s[:-1], 1000
    return int(s) * mult if s.isdigit() and int(s) * mult < 10**12 else None


def user_link(uid, name, username):
    tag = f" (@{esc(username)})" if username else ""
    return f'<a href="tg://user?id={uid}">{esc(name) or uid}</a>{tag}'


async def touch_user(u) -> bool:
    """Lưu/cập nhật người dùng, trả về True nếu đang bị khóa."""
    return await pool.fetchval(
        "INSERT INTO users(id, name, username) VALUES($1,$2,$3) "
        "ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, username=EXCLUDED.username "
        "RETURNING banned", u.id, u.full_name, u.username)


async def balance_of(uid):
    return await pool.fetchval("SELECT balance FROM users WHERE id=$1", uid) or 0


async def add_deposit(uid, amount, note):
    async with pool.acquire() as c, c.transaction():
        await c.execute("INSERT INTO users(id) VALUES($1) ON CONFLICT DO NOTHING", uid)
        bal = await c.fetchval(
            "UPDATE users SET balance=balance+$2, total_deposit=total_deposit+$2 "
            "WHERE id=$1 RETURNING balance", uid, amount)
        await c.execute("INSERT INTO deposits(user_id, amount, note) VALUES($1,$2,$3)", uid, amount, note)
    return bal


async def credit_bank(tx_id, uid, amount):
    """Cộng tiền từ ngân hàng, chống cộng trùng. Trả về (trạng thái, số dư)."""
    async with pool.acquire() as c, c.transaction():
        new = await c.fetchval("INSERT INTO bank_tx(id) VALUES($1) ON CONFLICT DO NOTHING RETURNING id", tx_id)
        if new is None:
            return "dup", None
        bal = await c.fetchval(
            "UPDATE users SET balance=balance+$2, total_deposit=total_deposit+$2 "
            "WHERE id=$1 RETURNING balance", uid, amount)
        if bal is None:
            return "nouser", None
        await c.execute("INSERT INTO deposits(user_id, amount, note) VALUES($1,$2,$3)",
                        uid, amount, f"bank:{tx_id}")
        return "ok", bal


async def get_gates(active_only=True):
    sql = "SELECT * FROM products" + (" WHERE active" if active_only else "") + " ORDER BY pos, gate"
    return await pool.fetch(sql)


async def get_gate(name):
    return await pool.fetchrow("SELECT * FROM products WHERE gate=$1", name)


def packages(g):
    return [(g["price"], g["points"])] + EXTRA


# ===================== KHỞI TẠO BOT =====================
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
admin = F.from_user.id.in_(ADMIN_IDS)


class Buy(StatesGroup):
    login = State()


async def safe_send(chat_id, text, **kw) -> bool:
    try:
        await bot.send_message(chat_id, text, **kw)
        return True
    except Exception:
        return False


async def to_admins(text, **kw):
    for a in ADMIN_IDS:
        await safe_send(a, text, **kw)


async def send_long(chat_id, text):
    for i in range(0, len(text), 3800):
        await bot.send_message(chat_id, text[i:i + 3800])


def qr_url(uid, amount):
    return (f"https://img.vietqr.io/image/{BANK_CODE}-{ACCOUNT_NO}-compact2.png"
            f"?amount={amount}&addInfo={TRANSFER_PREFIX}{uid}"
            f"&accountName={ACCOUNT_NAME.replace(' ', '%20')}")


# ===================== MIDDLEWARE: CHỐNG SPAM + KHÓA TÀI KHOẢN =====================
LAST = {}


class Guard(BaseMiddleware):
    async def __call__(self, handler, event, data):
        u = event.from_user
        if u is None or u.is_bot:
            return
        banned = await touch_user(u)
        if u.id not in ADMIN_IDS:
            t = time.monotonic()
            if t - LAST.get(u.id, 0) < THROTTLE:
                if isinstance(event, CallbackQuery):
                    await event.answer("Bạn thao tác quá nhanh, vui lòng thử lại.")
                return
            LAST[u.id] = t
            if banned:
                txt = f"🚫 Tài khoản của bạn đã bị khóa. Liên hệ {SUPPORT} để được hỗ trợ."
                if isinstance(event, CallbackQuery):
                    await event.answer(txt, show_alert=True)
                else:
                    await event.answer(txt)
                return
        return await handler(event, data)


dp.message.outer_middleware(Guard())
dp.callback_query.outer_middleware(Guard())


# ===================== NGƯỜI DÙNG =====================
@dp.message(Command("start"))
async def start(m: Message, state: FSMContext):
    await state.clear()
    await answer_menu(
        m,
        f"{E_HI} Xin chào <b>{esc(m.from_user.full_name)}</b>!\n\n"
        "Chào mừng bạn đến với hệ thống mua code tự động.\n"
        f"{E_WELCOME} Vui lòng chọn chức năng ở menu bên dưới.")


@dp.message(F.text == "TÀI KHOẢN")
async def account(m: Message, state: FSMContext):
    await state.clear()
    uid = m.from_user.id
    u = await pool.fetchrow("SELECT * FROM users WHERE id=$1", uid)
    spent = await pool.fetchval(
        "SELECT COALESCE(SUM(price),0) FROM orders WHERE user_id=$1 AND status='done'", uid)
    pending = await pool.fetchval(
        "SELECT COUNT(*) FROM orders WHERE user_id=$1 AND status='pending'", uid)
    await m.answer(
        f"{E_USER} <b>THÔNG TIN TÀI KHOẢN</b>\n"
        "━━━━━━━━━━━━━━━\n"
        f"🆔 ID: <code>{uid}</code>\n"
        f"{E_MONEY} SỐ DƯ: <b>{money(u['balance'])}</b>\n"
        f"{E_IN} TỔNG NẠP: {money(u['total_deposit'])}\n"
        f"{E_CART} TỔNG SỐ TIỀN MUA CODE: {money(spent)}\n"
        f"{E_WAIT} ĐƠN ĐANG XỬ LÝ: {pending}\n"
        f"🕒 NGÀY THAM GIA: {fmt(u['joined'])}")


NAP_HELP = (
    f"{E_CARD} <b>NẠP TIỀN</b>\n"
    "━━━━━━━━━━━━━━━\n"
    "Vui lòng dùng lệnh <code>/nap số tiền</code>\n"
    "Ví dụ: <code>/nap 30000</code> hoặc <code>/nap 30k</code>\n\n"
    "Bot sẽ tự động tạo mã thanh toán cho bạn. Lưu ý chuyển <b>đúng số tiền, nội dung "
    "và thông tin người nhận</b> để hệ thống tự động cập nhật chuẩn và nhanh nhất, "
    "tránh sự cố không mong muốn.\n"
    f"Cần hỗ trợ vui lòng liên hệ chăm sóc khách hàng {SUPPORT}")


@dp.message(F.text == "NẠP TIỀN")
async def nap_menu(m: Message, state: FSMContext):
    await state.clear()
    await m.answer(NAP_HELP)


@dp.message(Command("nap"))
async def nap_cmd(m: Message, command: CommandObject, state: FSMContext):
    await state.clear()
    args = (command.args or "").split()

    # Admin: /nap id số_tiền -> nạp thủ công
    if m.from_user.id in ADMIN_IDS and len(args) == 2:
        amount = parse_amount(args[1])
        if not args[0].isdigit() or not amount:
            return await m.answer("Cú pháp: <code>/nap id số_tiền</code>")
        uid = int(args[0])
        bal = await add_deposit(uid, amount, f"admin:{m.from_user.id}")
        await m.answer(f"{E_OK} Đã nạp {money(amount)} cho ID <code>{uid}</code>. Số dư mới: {money(bal)}")
        ok = await safe_send(uid, f"{E_OK} <b>NẠP TIỀN THÀNH CÔNG</b>\n"
                                  f"Số tiền: <b>{money(amount)}</b>\nSố dư hiện tại: {money(bal)}")
        if not ok:
            await m.answer(f"{E_WARN} Không gửi được thông báo cho người dùng (họ chưa /start hoặc đã chặn bot).")
        return

    # Người dùng: /nap số_tiền
    amount = parse_amount(args[0]) if args else None
    if not amount:
        return await m.answer(NAP_HELP)
    if not MIN_DEPOSIT <= amount <= MAX_DEPOSIT:
        return await m.answer(f"{E_WARN} Số tiền nạp từ {money(MIN_DEPOSIT)} đến {money(MAX_DEPOSIT)}.")
    uid = m.from_user.id
    caption = (
        f"{E_CARD} <b>THÔNG TIN NẠP TIỀN ĐÂY BẠN NHÉ</b>\n"
        "━━━━━━━━━━━━━━━\n"
        f"{E_USER} CHỦ TÀI KHOẢN: <b>{ACCOUNT_NAME}</b>\n"
        f"{E_BANK} SỐ TÀI KHOẢN: <code>{ACCOUNT_NO}</code>\n"
        f"{E_BANK} NGÂN HÀNG: <b>{BANK_NAME}</b>\n"
        f"{E_CASH} SỐ TIỀN: <b>{money(amount)}</b>\n"
        f"{E_NOTE} NỘI DUNG CHUYỂN KHOẢN: <code>{TRANSFER_PREFIX}{uid}</code>\n\n"
        f"{E_WARN} Chuyển <b>đúng số tiền và nội dung</b> để hệ thống tự động cập nhật. "
        "Nội dung này là riêng của bạn, không dùng chung với người khác.")
    try:
        await m.answer_photo(qr_url(uid, amount), caption=caption)
    except Exception:
        await m.answer(caption)


@dp.message(F.text == "MUA HÀNG")
async def shop(m: Message, state: FSMContext):
    await state.clear()
    gates = await get_gates()
    if not gates:
        return await m.answer("Hiện chưa có sản phẩm nào, vui lòng quay lại sau.")
    rows = [[InlineKeyboardButton(text=g["gate"], callback_data=f"gate:{g['gate']}")
             for g in gates[i:i + 2]] for i in range(0, len(gates), 2)]
    lines = "\n".join(f"• <b>{g['gate']}</b>: {g['price'] // 1000}K [ {g['points']} ]" for g in gates)
    extra = "\n".join(f"• {p // 1000}K [ {pt} ]" for p, pt in EXTRA)
    await m.answer(
        f"{E_CART} <b>BẢNG GIÁ CODE</b>\n━━━━━━━━━━━━━━━\n"
        f"{lines}\n\n{E_PLUS} Mỗi cổng có thêm các mệnh giá:\n{extra}\n\n"
        f"{E_TARGET} Chọn cổng game bạn muốn mua bên dưới:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


@dp.callback_query(F.data.startswith("gate:"))
async def pick_gate(c: CallbackQuery):
    g = await get_gate(c.data.split(":", 1)[1])
    if not g or not g["active"]:
        return await c.answer("Cổng này tạm ngưng bán.", show_alert=True)
    rows = [[InlineKeyboardButton(text=f"{p // 1000}K - {pt}", callback_data=f"pkg:{g['gate']}:{j}")]
            for j, (p, pt) in enumerate(packages(g))]
    await c.message.answer(f"{E_GAME} Cổng <b>{g['gate']}</b> — chọn mệnh giá:",
                           reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await c.answer()


@dp.callback_query(F.data.startswith("pkg:"))
async def pick_pkg(c: CallbackQuery, state: FSMContext):
    _, name, j = c.data.split(":")
    g = await get_gate(name)
    if not g or not g["active"]:
        return await c.answer("Cổng này tạm ngưng bán.", show_alert=True)
    price, points = packages(g)[int(j)]
    await state.set_state(Buy.login)
    await state.update_data(gate=name, price=price, points=points, login=None)
    await c.message.answer(
        f"Bạn chọn <b>{name}</b> — {money(price)} [{points}]\n\n"
        f"{E_EDIT} Vui lòng gửi <b>TÊN ĐĂNG NHẬP</b> của bạn:\n"
        "<i>(bấm một nút trên menu để hủy)</i>")
    await c.answer()


@dp.callback_query(F.data == "buy_no")
async def buy_no(c: CallbackQuery, state: FSMContext):
    await state.clear()
    await c.message.edit_text(f"{E_NO} Đã hủy đơn hàng.")
    await c.answer()


@dp.callback_query(F.data == "buy_ok")
async def buy_ok(c: CallbackQuery, state: FSMContext):
    d = await state.get_data()
    await state.clear()                      # xóa ngay để bấm 2 lần không bị mua đúp
    if not d.get("login"):
        return await c.answer("Phiên đã hết hạn, vui lòng chọn lại từ MUA HÀNG.", show_alert=True)
    g = await get_gate(d["gate"])
    if not g or not g["active"]:
        return await c.answer("Cổng này vừa tạm ngưng bán.", show_alert=True)
    uid = c.from_user.id
    async with pool.acquire() as conn, conn.transaction():
        bal = await conn.fetchval(
            "UPDATE users SET balance=balance-$2 WHERE id=$1 AND balance>=$2 RETURNING balance",
            uid, d["price"])
        oid = None
        if bal is not None:
            oid = await conn.fetchval(
                "INSERT INTO orders(user_id, gate, price, points, login) VALUES($1,$2,$3,$4,$5) RETURNING id",
                uid, d["gate"], d["price"], d["points"], d["login"])
    if oid is None:
        bal = await balance_of(uid)
        await c.message.edit_text(
            f"{E_NO} <b>SỐ DƯ KHÔNG ĐỦ</b>\nSố dư: {money(bal)} — cần: {money(d['price'])}\n"
            f"Thiếu: <b>{money(d['price'] - bal)}</b>. Dùng <code>/nap số_tiền</code> để nạp thêm.")
        return await c.answer()
    await c.message.edit_text(
        f"{E_OK} <b>ĐÃ MUA THÀNH CÔNG</b>\nMã đơn: <b>#{oid}</b>\n"
        "Đơn hàng sẽ được xử lý trong vòng <b>24-72H</b>.\n"
        "Theo dõi trạng thái tại mục LỊCH SỬ.")
    await c.answer()
    await notify_admin_order(oid)


async def notify_admin_order(oid, chat_id=None):
    o = await pool.fetchrow(
        "SELECT o.*, u.name, u.username FROM orders o JOIN users u ON u.id=o.user_id WHERE o.id=$1", oid)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ DUYỆT", callback_data=f"ok:{oid}"),
        InlineKeyboardButton(text="❌ TỪ CHỐI", callback_data=f"no:{oid}")]])
    text = (f"{E_NEW} <b>ĐƠN MỚI #{oid}</b>\n━━━━━━━━━━━━━━━\n"
            f"Khách: {user_link(o['user_id'], o['name'], o['username'])}\n"
            f"ID: <code>{o['user_id']}</code>\n"
            f"Cổng: <b>{o['gate']}</b> — {money(o['price'])} [{o['points']}]\n"
            f"Tên đăng nhập: <code>{esc(o['login'])}</code>\n"
            f"Thời gian: {fmt(o['created'])}")
    if chat_id:
        await bot.send_message(chat_id, text, reply_markup=kb)
    else:
        await to_admins(text, reply_markup=kb)


STATUS = {"pending": f"{E_WAIT} ĐANG XỬ LÝ",
          "done": f"{E_OK} MUA THÀNH CÔNG (ADMIN ĐÃ XỬ LÝ)",
          "rejected": f"{E_NO} BỊ TỪ CHỐI (ĐÃ HOÀN TIỀN)"}


@dp.message(F.text == "LỊCH SỬ")
async def history(m: Message, state: FSMContext):
    await state.clear()
    uid = m.from_user.id
    deps = await pool.fetch("SELECT * FROM deposits WHERE user_id=$1 ORDER BY id DESC LIMIT 10", uid)
    ords = await pool.fetch("SELECT * FROM orders WHERE user_id=$1 ORDER BY id DESC LIMIT 10", uid)
    t = f"{E_LIST} <b>LỊCH SỬ NẠP TIỀN</b> (10 gần nhất)\n━━━━━━━━━━━━━━━\n"
    t += "\n".join(f"{E_OK} NẠP TIỀN THÀNH CÔNG: <b>{money(d['amount'])}</b> — {fmt(d['created'])}"
                   for d in deps) if deps else "Chưa có giao dịch nạp tiền."
    t += f"\n\n{E_CART} <b>LỊCH SỬ MUA CODE</b> (10 gần nhất)\n━━━━━━━━━━━━━━━\n"
    t += "\n\n".join(f"#{o['id']} • {o['gate']} • {money(o['price'])} [{o['points']}]\n"
                     f"{STATUS[o['status']]} — {fmt(o['created'])}"
                     for o in ords) if ords else "Chưa có đơn hàng."
    await m.answer(t)


@dp.message(F.text == "HỖ TRỢ")
async def support(m: Message, state: FSMContext):
    await state.clear()
    await m.answer(f"{E_HELP} CẦN HỖ TRỢ XIN VUI LÒNG NHẮN QUA {SUPPORT}")


# ===================== ADMIN =====================
ADMIN_HELP = (
    f"{E_ADMIN} <b>LỆNH ADMIN</b>\n━━━━━━━━━━━━━━━\n"
    "<code>/nap id số_tiền</code> — nạp tiền thủ công (có báo khách)\n"
    "<code>/tru id số_tiền</code> — trừ số dư\n"
    "<code>/donhang</code> — đơn đang chờ xử lý\n"
    "<code>/muatc</code> — đơn mua thành công\n"
    "<code>/thongke</code> — thống kê\n"
    "<code>/user id</code> — xem thông tin khách\n"
    "<code>/ban id</code> | <code>/unban id</code> — khóa / mở khóa khách\n"
    "<code>/thongbao nội dung</code> — gửi thông báo cho tất cả khách\n"
    "<code>/sanpham</code> — danh sách cổng và giá\n"
    "<code>/setgia CỔNG giá [điểm]</code> — đổi giá (VD: /setgia LLWIN 95000 188 ĐIỂM)\n"
    "<code>/themcong CỔNG giá điểm</code> — thêm cổng mới\n"
    "<code>/tat CỔNG</code> | <code>/bat CỔNG</code> — tạm ngưng / mở bán")


@dp.message(Command("admin"), admin)
async def admin_help(m: Message):
    await m.answer(ADMIN_HELP)


@dp.callback_query(F.data.regexp(r"^(ok|no):\d+$"))
async def admin_decide(c: CallbackQuery):
    if c.from_user.id not in ADMIN_IDS:
        return await c.answer("Bạn không phải admin.", show_alert=True)
    act, oid = c.data.split(":")
    oid = int(oid)
    new = "done" if act == "ok" else "rejected"
    async with pool.acquire() as conn, conn.transaction():
        o = await conn.fetchrow(
            "UPDATE orders SET status=$2 WHERE id=$1 AND status='pending' RETURNING *", oid, new)
        if o and new == "rejected":
            await conn.execute("UPDATE users SET balance=balance+$2 WHERE id=$1", o["user_id"], o["price"])
    if not o:
        return await c.answer("Đơn này đã được xử lý rồi.", show_alert=True)
    if new == "done":
        await safe_send(o["user_id"], f"{E_OK} <b>Đơn #{oid}</b> ({o['gate']} - {o['points']}) "
                                      f"đã được admin xử lý thành công!\nCảm ơn bạn đã ủng hộ {E_HEART}")
    else:
        await safe_send(o["user_id"], f"{E_NO} <b>Đơn #{oid}</b> ({o['gate']}) bị từ chối. "
                                      f"Đã hoàn <b>{money(o['price'])}</b> vào số dư.\n"
                                      f"Cần hỗ trợ vui lòng liên hệ {SUPPORT}")
    who = esc(c.from_user.full_name)
    mark = f"{E_OK} ĐÃ DUYỆT" if new == "done" else f"{E_NO} ĐÃ TỪ CHỐI"
    await c.message.edit_text(c.message.html_text + f"\n\n<b>{mark}</b> bởi {who}")
    await c.answer("Xong")


@dp.message(Command("tru"), admin)
async def tru(m: Message, command: CommandObject):
    a = (command.args or "").split()
    amt = parse_amount(a[1]) if len(a) == 2 else None
    if not amt or not a[0].isdigit():
        return await m.answer("Cú pháp: <code>/tru id số_tiền</code>")
    uid = int(a[0])
    bal = await pool.fetchval(
        "UPDATE users SET balance=GREATEST(balance-$2,0) WHERE id=$1 RETURNING balance", uid, amt)
    if bal is None:
        return await m.answer("Không tìm thấy người dùng này.")
    await m.answer(f"{E_OK} Đã trừ {money(amt)} của ID <code>{uid}</code>. Số dư còn: {money(bal)}")
    await safe_send(uid, f"{E_INFO} Admin đã điều chỉnh trừ <b>{money(amt)}</b> trong số dư của bạn.\n"
                         f"Số dư hiện tại: {money(bal)}\nLiên hệ {SUPPORT} nếu cần hỗ trợ.")


@dp.message(Command("donhang"), admin)
async def donhang(m: Message):
    rows = await pool.fetch("SELECT id FROM orders WHERE status='pending' ORDER BY id")
    if not rows:
        return await m.answer(f"{E_OK} Không có đơn nào đang chờ xử lý.")
    await m.answer(f"{E_WAIT} Có <b>{len(rows)}</b> đơn đang chờ xử lý:")
    for r in rows:
        await notify_admin_order(r["id"], m.chat.id)


@dp.message(Command("muatc"), admin)
async def muatc(m: Message):
    rows = await pool.fetch("SELECT * FROM orders WHERE status='done' ORDER BY id DESC")
    if not rows:
        return await m.answer("Chưa có đơn thành công.")
    await send_long(m.chat.id, f"{E_OK} <b>ĐƠN MUA THÀNH CÔNG ({len(rows)})</b>\n\n" + "\n".join(
        f"#{o['id']} | ID {o['user_id']} | {o['gate']} {money(o['price'])} [{o['points']}] | "
        f"{esc(o['login'])} | {fmt(o['created'])}" for o in rows))


@dp.message(Command("thongke"), admin)
async def thongke(m: Message):
    v = pool.fetchval
    today = datetime.now(VN_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
    await m.answer(
        "📊 <b>THỐNG KÊ</b>\n━━━━━━━━━━━━━━━\n"
        f"{E_MONEY} Tổng tiền nạp: <b>{money(await v('SELECT COALESCE(SUM(total_deposit),0) FROM users'))}</b>\n"
        f"👥 Tổng thành viên: <b>{await v('SELECT COUNT(*) FROM users')}</b>\n"
        f"{E_WAIT} Đơn chờ xử lý: <b>{await v('SELECT COUNT(*) FROM orders WHERE status=$1', 'pending')}</b>\n"
        f"{E_OK} Đơn mua thành công: <b>{await v('SELECT COUNT(*) FROM orders WHERE status=$1', 'done')}</b>\n"
        f"{E_CART} Tổng tiền mua code thành công: "
        f"<b>{money(await v('SELECT COALESCE(SUM(price),0) FROM orders WHERE status=$1', 'done'))}</b>\n"
        f"{E_CASH} Tổng số dư khách đang giữ: {money(await v('SELECT COALESCE(SUM(balance),0) FROM users'))}\n\n"
        "📅 <b>HÔM NAY</b>\n"
        f"• Khách mới: {await v('SELECT COUNT(*) FROM users WHERE joined >= $1', today)}\n"
        f"• Tiền nạp: {money(await v('SELECT COALESCE(SUM(amount),0) FROM deposits WHERE created >= $1', today))}\n"
        f"• Đơn mới: {await v('SELECT COUNT(*) FROM orders WHERE created >= $1', today)}")


@dp.message(Command("user"), admin)
async def user_info(m: Message, command: CommandObject):
    a = (command.args or "").strip()
    if not a.isdigit():
        return await m.answer("Cú pháp: <code>/user id</code>")
    u = await pool.fetchrow("SELECT * FROM users WHERE id=$1", int(a))
    if not u:
        return await m.answer("Không tìm thấy người dùng này.")
    spent = await pool.fetchval(
        "SELECT COALESCE(SUM(price),0) FROM orders WHERE user_id=$1 AND status='done'", u["id"])
    n_ord = await pool.fetchval("SELECT COUNT(*) FROM orders WHERE user_id=$1", u["id"])
    status = f"{E_BAN} ĐANG BỊ KHÓA" if u["banned"] else "🟢 Bình thường"
    await m.answer(
        f"{E_USER} {user_link(u['id'], u['name'], u['username'])}\n"
        f"ID: <code>{u['id']}</code>\nSố dư: <b>{money(u['balance'])}</b>\n"
        f"Tổng nạp: {money(u['total_deposit'])}\nTổng mua thành công: {money(spent)}\n"
        f"Số đơn: {n_ord}\nTham gia: {fmt(u['joined'])}\n"
        f"Trạng thái: {status}")


@dp.message(Command("ban", "unban"), admin)
async def ban(m: Message, command: CommandObject):
    a = (command.args or "").strip()
    if not a.isdigit() or int(a) in ADMIN_IDS:
        return await m.answer(f"Cú pháp: <code>/{command.command} id</code>")
    flag = command.command == "ban"
    found = await pool.fetchval("UPDATE users SET banned=$2 WHERE id=$1 RETURNING id", int(a), flag)
    if found is None:
        return await m.answer("Không tìm thấy người dùng này.")
    head = f"{E_BAN} Đã khóa" if flag else f"{E_OK} Đã mở khóa"
    await m.answer(f"{head} ID <code>{a}</code>")


@dp.message(Command("thongbao"), admin)
async def broadcast(m: Message, command: CommandObject):
    text = command.args
    if not text:
        return await m.answer("Cú pháp: <code>/thongbao nội dung</code>")
    try:
        await bot.send_message(m.chat.id, text)           # xem thử (và kiểm tra lỗi HTML)
    except TelegramBadRequest:
        return await m.answer(f"{E_WARN} Nội dung có thẻ HTML sai, vui lòng kiểm tra lại.")
    ids = [r["id"] for r in await pool.fetch("SELECT id FROM users WHERE NOT banned") if r["id"] != m.chat.id]
    await m.answer(f"{E_MEGA} Đang gửi cho {len(ids)} người...")
    ok = 0
    for uid in ids:
        ok += await safe_send(uid, text)
        await asyncio.sleep(0.05)                          # tránh bị Telegram giới hạn
    await m.answer(f"{E_OK} Gửi xong: {ok}/{len(ids)} người nhận được.")


@dp.message(Command("sanpham"), admin)
async def sanpham(m: Message):
    rows = await get_gates(active_only=False)
    await m.answer(f"{E_CART} <b>DANH SÁCH CỔNG</b>\n\n" + "\n".join(
        f"{'🟢' if g['active'] else '🔴'} <b>{g['gate']}</b> — {money(g['price'])} [{g['points']}]"
        for g in rows))


@dp.message(Command("setgia"), admin)
async def setgia(m: Message, command: CommandObject):
    a = (command.args or "").split(maxsplit=2)
    price = parse_amount(a[1]) if len(a) >= 2 else None
    name = a[0].upper() if a else ""
    if not price or not await get_gate(name):
        return await m.answer("Cú pháp: <code>/setgia CỔNG giá [điểm]</code>\n"
                              "VD: <code>/setgia LLWIN 95000 188 ĐIỂM</code>")
    if len(a) == 3:
        await pool.execute("UPDATE products SET price=$2, points=$3 WHERE gate=$1", name, price, a[2].upper())
    else:
        await pool.execute("UPDATE products SET price=$2 WHERE gate=$1", name, price)
    await m.answer(f"{E_OK} Đã cập nhật <b>{name}</b>: {money(price)}")


@dp.message(Command("themcong"), admin)
async def themcong(m: Message, command: CommandObject):
    a = (command.args or "").split(maxsplit=2)
    price = parse_amount(a[1]) if len(a) == 3 else None
    name = a[0].upper() if a else ""
    if not price or not re.fullmatch(r"[A-Z0-9]{2,12}", name):
        return await m.answer("Cú pháp: <code>/themcong CỔNG giá điểm</code>\n"
                              "VD: <code>/themcong ABC88 85000 188 ĐIỂM</code>")
    if await get_gate(name):
        return await m.answer("Cổng này đã tồn tại, dùng /setgia để đổi giá.")
    pos = await pool.fetchval("SELECT COALESCE(MAX(pos),0)+1 FROM products")
    await pool.execute("INSERT INTO products(gate, price, points, pos) VALUES($1,$2,$3,$4)",
                       name, price, a[2].upper(), pos)
    await m.answer(f"{E_OK} Đã thêm cổng <b>{name}</b>: {money(price)} [{a[2].upper()}]")


@dp.message(Command("tat", "bat"), admin)
async def toggle_gate(m: Message, command: CommandObject):
    name = (command.args or "").strip().upper()
    if not await get_gate(name):
        return await m.answer(f"Cú pháp: <code>/{command.command} CỔNG</code>")
    flag = command.command == "bat"
    await pool.execute("UPDATE products SET active=$2 WHERE gate=$1", name, flag)
    head = f"{E_OK} Đã mở bán" if flag else f"{E_NO} Đã tạm ngưng bán"
    await m.answer(f"{head} <b>{name}</b>")


# Đặt cuối cùng: lệnh không tồn tại
@dp.message(F.text.startswith("/"))
async def unknown_cmd(m: Message):
    await answer_menu(m, "Lệnh không tồn tại. Vui lòng dùng menu bên dưới nhé.")


# Đặt SAU các nút menu và lệnh để bấm menu/lệnh khi đang nhập tên vẫn hoạt động
@dp.message(Buy.login, F.text)
async def get_login(m: Message, state: FSMContext):
    login = m.text.strip()
    if not re.fullmatch(r"[\w.@\-]{3,40}", login):
        return await m.answer(f"{E_WARN} Tên đăng nhập không hợp lệ (3-40 ký tự, không dấu cách). Vui lòng gửi lại.")
    await state.update_data(login=login)
    d = await state.get_data()
    bal = await balance_of(m.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ XÁC NHẬN MUA", callback_data="buy_ok"),
        InlineKeyboardButton(text="❌ HỦY", callback_data="buy_no")]])
    await m.answer(
        f"{E_NOTE} <b>XÁC NHẬN ĐƠN HÀNG</b>\n━━━━━━━━━━━━━━━\n"
        "DỊCH VỤ: CODE LDC\n"
        f"CỔNG: <b>{d['gate']}</b>\n"
        f"GIÁ TIỀN: <b>{money(d['price'])}</b>\n"
        f"ĐIỂM: {d['points']}\n"
        f"TÊN ĐĂNG NHẬP: <code>{esc(login)}</code>\n"
        f"SỐ DƯ HIỆN TẠI: {money(bal)}\n\n"
        f"{E_WARN} VUI LÒNG KIỂM TRA LẠI THÔNG TIN TRÁNH SAI SÓT",
        reply_markup=kb)


@dp.error()
async def on_error(event: ErrorEvent):
    logging.error("Lỗi xử lý update: %s", event.exception, exc_info=event.exception)
    return True


# ===================== WEB: HEALTH CHECK + NẠP TỰ ĐỘNG (SePay) =====================
async def health(request: web.Request):
    return web.Response(text="OK")


async def sepay_hook(request: web.Request):
    if SEPAY_KEY and request.headers.get("Authorization") != f"Apikey {SEPAY_KEY}":
        return web.json_response({"success": False}, status=401)
    try:
        data = await request.json()
        if data.get("transferType") != "in":
            return web.json_response({"success": True})
        tx_id = str(data.get("id") or data.get("referenceCode"))
        mt = re.search(rf"{re.escape(TRANSFER_PREFIX)}(\d+)", str(data.get("content", "")), re.I)
        amount = int(float(data.get("transferAmount", 0)))
    except Exception:
        return web.json_response({"success": False}, status=400)
    if not mt or amount <= 0:
        return web.json_response({"success": True})
    uid = int(mt.group(1))
    status, bal = await credit_bank(tx_id, uid, amount)
    if status == "ok":
        await safe_send(uid, f"{E_OK} <b>NẠP TIỀN THÀNH CÔNG</b>\nSố tiền: <b>{money(amount)}</b>\n"
                             f"Số dư hiện tại: {money(bal)}")
        await to_admins(f"{E_MONEY} Khách <code>{uid}</code> vừa nạp tự động {money(amount)}")
    elif status == "nouser":
        await to_admins(f"{E_WARN} Nhận {money(amount)} với nội dung có ID <code>{uid}</code> "
                        "nhưng ID này chưa có trong hệ thống. Vui lòng kiểm tra thủ công.")
    return web.json_response({"success": True})


async def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    logging.info("Đang khởi động bot...")
    await init_db()
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_post("/sepay", sepay_hook)
    runner = web.AppRunner(app)
    await runner.setup()
    await web.TCPSite(runner, "0.0.0.0", WEB_PORT).start()
    try:
        await bot.set_my_commands([BotCommand(command="start", description="Mở menu"),
                                   BotCommand(command="nap", description="Nạp tiền: /nap 30000")])
        for a in ADMIN_IDS:
            await bot.set_my_commands(
                [BotCommand(command="start", description="Mở menu"),
                 BotCommand(command="admin", description="Danh sách lệnh admin"),
                 BotCommand(command="donhang", description="Đơn đang chờ"),
                 BotCommand(command="thongke", description="Thống kê")],
                scope=BotCommandScopeChat(chat_id=a))
    except Exception:
        logging.warning("Không đặt được danh sách lệnh (admin cần /start bot trước).")
    try:
        await dp.start_polling(bot)
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
