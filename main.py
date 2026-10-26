"""
BOT BÁN CODE TELEGRAM — PostgreSQL + Emoji Premium
--------------------------------------------------
Biến môi trường bắt buộc : BOT_TOKEN, DATABASE_URL
Biến tùy chọn            : ADMIN_IDS, SUPPORT, BANK_CODE, BANK_NAME, SEPAY_BANK, ACCOUNT_NO,
                           ACCOUNT_NAME, TRANSFER_PREFIX, SEPAY_KEY, PREMIUM_EMOJI=0
Chạy                     : python main.py
"""
import asyncio
import html
import logging
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import aiohttp
import asyncpg
from aiogram import BaseMiddleware, Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    BotCommand, BotCommandScopeChat, BufferedInputFile, CallbackQuery, ErrorEvent,
    InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, Message,
    ReplyKeyboardMarkup,
)
from aiohttp import web

# ===================== CẤU HÌNH =====================
try:  # chạy trên máy: tự đọc file .env nếu có
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
DATABASE_URL = os.getenv("DATABASE_URL", "")
if not BOT_TOKEN or not DATABASE_URL:
    sys.exit("Thiếu BOT_TOKEN hoặc DATABASE_URL. Hãy thêm 2 biến này trong tab Variables.")

ADMIN_IDS = {int(x) for x in os.getenv("ADMIN_IDS", "7884394252").replace(" ", "").split(",") if x}
SUPPORT = os.getenv("SUPPORT", "@dinhcong98")

# ---- Thông tin ngân hàng nhận tiền (MBBANK - 0003456712345 - LY THI CHAM) ----
BANK_CODE = os.getenv("BANK_CODE", "MB")          # mã ngân hàng cho VietQR
BANK_NAME = os.getenv("BANK_NAME", "MBBANK")      # tên hiển thị
SEPAY_BANK = os.getenv("SEPAY_BANK", "MBBank")    # tên ngân hàng cho mã QR dự phòng (qr.sepay.vn)
ACCOUNT_NO = os.getenv("ACCOUNT_NO", "0003456712345")
ACCOUNT_NAME = os.getenv("ACCOUNT_NAME", "LY THI CHAM")
TRANSFER_PREFIX = os.getenv("TRANSFER_PREFIX", "lixisinhnhat")

SEPAY_KEY = os.getenv("SEPAY_KEY", "")
WEB_PORT = int(os.getenv("PORT", "8080"))

MIN_DEPOSIT = 20_000
MAX_DEPOSIT = 50_000_000
QUICK_AMOUNTS = [20_000, 50_000, 100_000, 200_000, 500_000, 1_000_000]
THROTTLE = 0.5
VN_TZ = timezone(timedelta(hours=7))
EPOCH = datetime.fromtimestamp(0, timezone.utc)

MIN_PRICE = 1_000                                  # giá thấp nhất khi admin sửa giá
PRICE_STEPS = [1_000, 5_000, 10_000, 50_000]       # các bước tăng/giảm trong menu /setgia

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
# Giá các gói thêm (đã giảm: 450K -> 350K, 280K -> 230K). Chỉ dùng làm giá khởi tạo,
# sau đó mỗi cổng có giá riêng trong DB và admin sửa bằng /set hoặc /setgia.
EXTRA = [(140_000, "288 ĐIỂM"), (230_000, "588 ĐIỂM"), (350_000, "888 ĐIỂM")]
SINGLE_PACKAGE_GATES = {"8KBET", "OK9"}  # cổng chỉ bán đúng 1 mệnh giá, không có gói EXTRA

# ===================== EMOJI PREMIUM =====================
# Đặt PREMIUM_EMOJI=0 trong Railway Variables để quay về emoji thường.
PREMIUM = os.getenv("PREMIUM_EMOJI", "1") != "0"


def ce(char: str, eid: str) -> str:
    """Emoji premium trong văn bản (tg-emoji); tắt/không đủ quyền thì hiện emoji thường."""
    return f'<tg-emoji emoji-id="{eid}">{char}</tg-emoji>' if PREMIUM else char


# ID emoji
ID_OK, ID_NO, ID_BAN = "6165926565638051547", "5210952531676504517", "5240241223632954241"
ID_WARN, ID_WAIT = "5447644880824181073", "5386367538735104399"
ID_CARD, ID_MONEY, ID_CASH = "5445353829304387411", "5278467510604160626", "5409048419211682843"
ID_BANK, ID_CART = "5332455502917949981", "5406683434124859552"
ID_IN, ID_NOTE, ID_LIST = "5443127283898405358", "5395444784611480792", "5397782960512444700"
ID_HELP, ID_GAME, ID_NEW = "5285238101344544669", "5319247469165433798", "5253742260054409879"
ID_ADMIN, ID_INFO, ID_USER = "5193177581888755275", "5334544901428229844", "5251203410396458957"
ID_HI, ID_HEART, ID_PLUS = "5235701688014217208", "5197387964098813812", "5397916757333654639"
ID_MEGA, ID_TARGET, ID_WELCOME = "5415655814079723871", "5256131095094652290", "6192771593001767805"
ID_STAT, ID_DATE, ID_ON, ID_OFF = "5231200819986047254", "5472279086657199080", "5206607081334906820", "5411225014148014586"
ID_RESET = "5375338737028841420"

E_OK, E_NO, E_BAN = ce("✅", ID_OK), ce("❌", ID_NO), ce("🚫", ID_BAN)
E_WARN, E_WAIT = ce("⚠️", ID_WARN), ce("⏳", ID_WAIT)
E_CARD, E_MONEY, E_CASH = ce("💳", ID_CARD), ce("💰", ID_MONEY), ce("💵", ID_CASH)
E_BANK, E_CART = ce("🏦", ID_BANK), ce("🛍", ID_CART)
E_IN, E_NOTE, E_EDIT, E_LIST = ce("📥", ID_IN), ce("📝", ID_NOTE), ce("✍️", ID_NOTE), ce("📜", ID_LIST)
E_HELP, E_GAME, E_NEW = ce("🆘", ID_HELP), ce("🎮", ID_GAME), ce("🛎", ID_NEW)
E_ADMIN, E_INFO, E_USER = ce("🛠", ID_ADMIN), ce("ℹ️", ID_INFO), ce("👤", ID_USER)
E_HI, E_HEART, E_PLUS = ce("👋", ID_HI), ce("💙", ID_HEART), ce("➕", ID_PLUS)
E_MEGA, E_TARGET, E_WELCOME = ce("📢", ID_MEGA), ce("🎯", ID_TARGET), ce("👅", ID_WELCOME)
E_STAT, E_DATE = ce("📊", ID_STAT), ce("🗓️", ID_DATE)
E_ON, E_OFF = ce("✔️", ID_ON), ce("🔴", ID_OFF)
E_ID, E_USERS, E_RESET = ce("ℹ️", ID_INFO), ce("👤", ID_USER), ce("🔄", ID_RESET)

# Emoji premium cho 5 nút menu
MENU_ICONS = {
    "TÀI KHOẢN": "5217822164362739968",   # 👑
    "NẠP TIỀN": "5427168083074628963",    # 💎
    "MUA HÀNG": "6102831593389299866",    # 🌟
    "LỊCH SỬ": "6280407793631498213",     # 🚗
    "HỖ TRỢ": "5314504236132747481",      # ⁉️
}


def btn(text: str, data: str, eid: str, char: str) -> InlineKeyboardButton:
    """Nút inline có emoji premium; nếu tắt premium thì dùng emoji thường trong chữ."""
    if PREMIUM:
        return InlineKeyboardButton(text=text, callback_data=data, icon_custom_emoji_id=eid)
    return InlineKeyboardButton(text=f"{char} {text}", callback_data=data)


def make_menu(use_icons: bool) -> ReplyKeyboardMarkup:
    def b(text):
        extra = {"icon_custom_emoji_id": MENU_ICONS[text]} if (use_icons and PREMIUM) else {}
        return KeyboardButton(text=text, **extra)

    return ReplyKeyboardMarkup(
        keyboard=[
            [b("TÀI KHOẢN"), b("NẠP TIỀN")],
            [b("MUA HÀNG"), b("LỊCH SỬ")],
            [b("HỖ TRỢ")],
        ],
        resize_keyboard=True,
        input_field_placeholder="Chọn chức năng bên dưới",
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
ALTER TABLE orders ADD COLUMN IF NOT EXISTS reason TEXT;
CREATE TABLE IF NOT EXISTS bank_tx(id TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS products(
    gate TEXT PRIMARY KEY, price BIGINT NOT NULL, points TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE, pos INT NOT NULL DEFAULT 0);
ALTER TABLE products ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'ok';
CREATE TABLE IF NOT EXISTS packages(
    gate TEXT NOT NULL, idx INT NOT NULL, price BIGINT NOT NULL, points TEXT NOT NULL,
    PRIMARY KEY (gate, idx));
ALTER TABLE packages ADD COLUMN IF NOT EXISTS status TEXT NOT NULL DEFAULT 'ok';
CREATE TABLE IF NOT EXISTS stat_reset(
    key TEXT PRIMARY KEY, at TIMESTAMPTZ NOT NULL DEFAULT now());
CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_deposits_user ON deposits(user_id);
"""
# status (products và packages): 'ok' = đang bán | 'full' = FULL SLOT | 'maint' = BẢO TRÌ
# products.status  = trạng thái CẢ CỔNG
# packages.status  = trạng thái TỪNG MỆNH GIÁ (VD: chỉ bảo trì 90K, các giá khác vẫn mua được)

pool: asyncpg.Pool = None


async def seed_packages(c, gate: str, price: int, points: str):
    """Tạo các mệnh giá cho một cổng: gói gốc + các gói EXTRA (trừ cổng chỉ bán 1 mệnh giá)."""
    pk = [(price, points)] + ([] if gate in SINGLE_PACKAGE_GATES else EXTRA)
    for i, (p, pt) in enumerate(pk):
        await c.execute("INSERT INTO packages(gate, idx, price, points) VALUES($1,$2,$3,$4) "
                        "ON CONFLICT DO NOTHING", gate, i, p, pt)


async def init_db():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL, min_size=1, max_size=5)
    async with pool.acquire() as c:
        await c.execute(SCHEMA)
        for pos, (g, (p, pt)) in enumerate(DEFAULT_GATES.items()):
            await c.execute("INSERT INTO products(gate, price, points, pos) VALUES($1,$2,$3,$4) "
                            "ON CONFLICT (gate) DO NOTHING", g, p, pt, pos)
        # Cổng nào chưa có bảng mệnh giá thì tạo (giữ nguyên giá gốc đang có trong DB)
        for g in await c.fetch("SELECT gate, price, points FROM products"):
            if not await c.fetchval("SELECT 1 FROM packages WHERE gate=$1 LIMIT 1", g["gate"]):
                await seed_packages(c, g["gate"], g["price"], g["points"])


# ===================== TIỆN ÍCH =====================
def fmt(dt):
    return dt.astimezone(VN_TZ).strftime("%H:%M:%S %d/%m/%Y")


def money(n):
    return f"{int(n):,}".replace(",", ".") + "đ"


def kfmt(n):
    """90000 -> 90K (nếu không tròn nghìn thì hiện đầy đủ)."""
    n = int(n)
    return f"{n // 1000}K" if n % 1000 == 0 else money(n)


def esc(s):
    return html.escape(str(s or ""))


def parse_amount(s: str):
    """'30000' | '30.000' | '30k' -> int, hoặc None nếu sai."""
    s = s.lower().replace(".", "").replace(",", "").strip()
    mult = 1
    if s.endswith("k"):
        s, mult = s[:-1], 1000
    return int(s) * mult if s.isdigit() and int(s) * mult < 10**12 else None


def quick_label(a: int) -> str:
    """Nhãn nút nạp nhanh: 20K, 50K, ... 1M."""
    return f"{a // 1_000_000}M" if a >= 1_000_000 and a % 1_000_000 == 0 else f"{a // 1000}K"


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


async def get_packages(gate):
    """Các mệnh giá của một cổng (giá đang bán thật, admin sửa trực tiếp)."""
    return await pool.fetch("SELECT * FROM packages WHERE gate=$1 ORDER BY idx", gate)


async def packages_map() -> dict:
    """{cổng: [các mệnh giá]} — lấy 1 lần cho cả bảng giá."""
    d = {}
    for r in await pool.fetch("SELECT * FROM packages ORDER BY gate, idx"):
        d.setdefault(r["gate"], []).append(r)
    return d


STATUS_LABEL = {"full": "FULL SLOT", "maint": "BẢO TRÌ"}


def fmt_pkgs(pk) -> str:
    """'90K [188 ĐIỂM] • 140K [288 ĐIỂM] (BẢO TRÌ) • ...' — hiển thị đủ mệnh giá và trạng thái từng giá."""
    def one(p):
        s = f"{kfmt(p['price'])} [{p['points']}]"
        if p["status"] in STATUS_LABEL:
            s += f" 🔴 <b>{STATUS_LABEL[p['status']]}</b>"
        return s
    return " • ".join(one(p) for p in pk) or "(chưa có mệnh giá)"


def block_alert(g) -> str:
    """Thông báo khi khách bấm vào CẢ CỔNG đang FULL SLOT / BẢO TRÌ (văn bản thường, ≤200 ký tự)."""
    if g["status"] == "full":
        return (f"🔴 {g['gate']} ĐÃ FULL SLOT.\n"
                "Hiện chưa thể mua, vui lòng quay lại sau khi admin mở lại.")
    return (f"🛠 {g['gate']} ĐANG BẢO TRÌ.\n"
            "Hiện chưa thể mua, vui lòng quay lại sau khi admin mở lại.")


def pkg_block_alert(gate: str, pkg) -> str:
    """Thông báo khi khách bấm vào MỘT mệnh giá đang FULL SLOT / BẢO TRÌ."""
    if pkg["status"] == "full":
        return (f"🔴 {gate} {kfmt(pkg['price'])} ĐÃ FULL SLOT.\n"
                "Mệnh giá này chưa thể mua, bạn có thể chọn mệnh giá khác hoặc quay lại sau.")
    return (f"🛠 {gate} {kfmt(pkg['price'])} ĐANG BẢO TRÌ.\n"
            "Mệnh giá này chưa thể mua, bạn có thể chọn mệnh giá khác hoặc quay lại sau.")


def transfer_note(uid):
    return f"{TRANSFER_PREFIX}{uid}"


def qr_urls(uid, amount):
    """Các nguồn tạo mã QR (thử lần lượt): VietQR rồi SePay. Đều điền sẵn số tiền, nội dung, chủ tài khoản."""
    note = transfer_note(uid)
    vietqr = (f"https://img.vietqr.io/image/{BANK_CODE}-{ACCOUNT_NO}-compact2.png?"
              + urlencode({"amount": amount, "addInfo": note, "accountName": ACCOUNT_NAME}))
    sepay = "https://qr.sepay.vn/img?" + urlencode(
        {"acc": ACCOUNT_NO, "bank": SEPAY_BANK, "amount": amount, "des": note})
    return [vietqr, sepay]


async def fetch_qr(uid, amount):
    """Tự tải ảnh QR về rồi gửi lên Telegram (ổn định hơn để Telegram tự tải link)."""
    errs = []
    timeout = aiohttp.ClientTimeout(total=20)
    async with aiohttp.ClientSession(timeout=timeout) as s:
        for url in qr_urls(uid, amount):
            host = url.split("?")[0].split("/")[2]
            try:
                async with s.get(url) as r:
                    data = await r.read()
                    if r.status == 200 and r.content_type.startswith("image") and len(data) > 1000:
                        return data, errs
                    errs.append(f"{host}: HTTP {r.status} ({r.content_type})")
            except Exception as e:
                errs.append(f"{host}: {type(e).__name__} {e}")
    for e in errs:
        logging.warning("QR lỗi %s", e)
    return None, errs


# ===================== KHỞI TẠO BOT =====================
bot = Bot(BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
admin = F.from_user.id.in_(ADMIN_IDS)


class Buy(StatesGroup):
    login = State()


class Nap(StatesGroup):
    amount = State()


class Reject(StatesGroup):
    reason = State()


async def safe_send(chat_id, text, **kw) -> bool:
    try:
        await bot.send_message(chat_id, text, **kw)
        return True
    except Exception:
        return False


async def safe_edit(msg: Message, text: str, kb=None):
    """Sửa tin nhắn tại chỗ; bỏ qua lỗi 'message is not modified'."""
    try:
        await msg.edit_text(text, reply_markup=kb)
    except TelegramBadRequest:
        pass


async def to_admins(text, **kw):
    for a in ADMIN_IDS:
        await safe_send(a, text, **kw)


async def send_long(chat_id, text):
    for i in range(0, len(text), 3800):
        await bot.send_message(chat_id, text[i:i + 3800])


# ===================== FILE BIÊN NHẬN ĐƠN HÀNG =====================
RECEIPT_STATUS = {
    "pending": "ĐANG XỬ LÝ",
    "done": "THÀNH CÔNG",
    "rejected": "BỊ TỪ CHỐI",
}


def receipt_file(o, reason=None) -> BufferedInputFile:
    """File .html biên nhận dạng bảng có đường kẻ: CỔNG | TRẠNG THÁI | SỐ TIỀN, số điểm, tên đăng nhập."""
    status = RECEIPT_STATUS.get(o["status"], str(o["status"]).upper())
    e = html.escape
    head = "".join(f"<th>{t}</th>" for t in ("CỔNG", "TRẠNG THÁI", "SỐ TIỀN"))
    vals = "".join(f"<td>{e(str(t))}</td>" for t in (o["gate"], status, money(o["price"])))
    info = [
        ("SỐ ĐIỂM:", o["points"]),
        ("TÊN ĐĂNG NHẬP:", o["login"]),
        ("MÃ ĐƠN:", f"#{o['id']}"),
        ("THỜI GIAN ĐẶT:", fmt(o["created"])),
    ]
    if reason:
        info += [("LÝ DO TỪ CHỐI:", reason), ("", "(Đơn bị từ chối không được hoàn tiền)")]
    rows = "".join(f"<tr><td class='k'>{e(k)}</td><td>{e(str(v))}</td></tr>" for k, v in info)
    page = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>"
        f"<title>Đơn #{o['id']}</title><style>"
        "body{font-family:'Times New Roman',serif;font-size:14px;margin:8px}"
        "table{border-collapse:collapse;margin-bottom:10px;width:100%}"
        "th,td{border:1px solid #b9b9d6;padding:4px 8px;text-align:left}"
        "th{background:#e25c70;color:#fff;text-align:center}"
        "td.k{font-weight:bold;white-space:nowrap;width:1%}"
        f"</style></head><body><table><tr>{head}</tr><tr>{vals}</tr></table>"
        f"<table>{rows}</table></body></html>"
    )
    return BufferedInputFile(page.encode("utf-8"), filename=f"don_{o['id']}.html")


async def send_receipt(chat_id, o, caption, reason=None) -> bool:
    try:
        await bot.send_document(chat_id, receipt_file(o, reason), caption=caption)
        return True
    except Exception as e:
        logging.warning("Không gửi được file biên nhận cho %s: %s", chat_id, e)
        return False


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
                if isinstance(event, CallbackQuery):
                    await event.answer(f"Tài khoản của bạn đã bị khóa. Liên hệ {SUPPORT} để được hỗ trợ.",
                                       show_alert=True)
                else:
                    await event.answer(f"{E_BAN} Tài khoản của bạn đã bị khóa. "
                                       f"Liên hệ {SUPPORT} để được hỗ trợ.")
                return
        return await handler(event, data)


dp.message.outer_middleware(Guard())
dp.callback_query.outer_middleware(Guard())


# ===================== NGƯỜI DÙNG: BẮT ĐẦU & TÀI KHOẢN =====================
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
        f"{E_ID} ID: <code>{uid}</code>\n"
        f"{E_MONEY} Số dư: <b>{money(u['balance'])}</b>\n"
        f"{E_IN} Tổng nạp: {money(u['total_deposit'])}\n"
        f"{E_CART} Tổng tiền mua code: {money(spent)}\n"
        f"{E_WAIT} Đơn đang xử lý: {pending}\n"
        f"{E_DATE} Ngày tham gia: {fmt(u['joined'])}")


# ===================== NẠP TIỀN (TỰ ĐỘNG TẠO QR) =====================
def nap_keyboard() -> InlineKeyboardMarkup:
    amounts = [btn(quick_label(a), f"nap:{a}", ID_CASH, "💵") for a in QUICK_AMOUNTS]
    rows = [amounts[i:i + 3] for i in range(0, len(amounts), 3)]
    rows.append([btn("NHẬP SỐ TIỀN KHÁC", "nap:custom", ID_NOTE, "✍️")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


NAP_HELP = (
    f"{E_CARD} <b>NẠP TIỀN TỰ ĐỘNG</b>\n"
    "━━━━━━━━━━━━━━━\n"
    "Chọn nhanh số tiền bên dưới, hoặc dùng lệnh <code>/nap số_tiền</code>\n"
    "Ví dụ: <code>/nap 30000</code> hoặc <code>/nap 30k</code>\n"
    f"Nạp tối thiểu: <b>{money(MIN_DEPOSIT)}</b>\n\n"
    "Bot sẽ tạo mã QR có sẵn số tiền, nội dung và thông tin người nhận. "
    "Bạn chỉ cần quét mã và chuyển khoản, số dư được cộng tự động sau ít phút.\n\n"
    f"{E_WARN} Vui lòng chuyển <b>đúng số tiền và nội dung</b> để hệ thống ghi nhận chính xác.\n"
    f"Cần hỗ trợ, liên hệ {SUPPORT}")


def qr_caption(user, amount: int, has_qr: bool) -> str:
    uid = user.id
    hint = (f"{E_INFO} Quét mã QR bên trên, thông tin đã được điền sẵn.\n" if has_qr else
            f"{E_INFO} Vui lòng chuyển khoản theo thông tin bên trên.\n")
    return (
        f"{E_CARD} <b>THÔNG TIN NẠP TIỀN</b>\n"
        "━━━━━━━━━━━━━━━\n"
        f"{E_USER} Người nạp: <b>{esc(user.full_name)}</b> (ID <code>{uid}</code>)\n"
        f"{E_BANK} Chủ tài khoản: <b>{esc(ACCOUNT_NAME)}</b>\n"
        f"{E_BANK} Số tài khoản: <code>{esc(ACCOUNT_NO)}</code>\n"
        f"{E_BANK} Ngân hàng: <b>{esc(BANK_NAME)}</b>\n"
        f"{E_CASH} Số tiền: <b>{money(amount)}</b>\n"
        f"{E_NOTE} Nội dung chuyển khoản: <code>{transfer_note(uid)}</code>\n\n"
        f"{hint}"
        f"{E_WARN} Chuyển <b>đúng số tiền và nội dung</b> để hệ thống tự động cộng tiền. "
        "Nội dung này là riêng của bạn, không dùng chung với người khác.")


async def send_qr(m: Message, user, amount: int):
    """Gửi mã QR đã điền sẵn thông tin cho người dùng (có phương án dự phòng)."""
    data, errs = await fetch_qr(user.id, amount)
    if data:
        try:
            await m.answer_photo(BufferedInputFile(data, filename="qr.png"),
                                 caption=qr_caption(user, amount, True))
            return
        except Exception as e:
            errs.append(f"gửi ảnh lên Telegram: {type(e).__name__} {e}")
    for url in qr_urls(user.id, amount):  # thử để Telegram tự tải link
        try:
            await m.answer_photo(url, caption=qr_caption(user, amount, True))
            return
        except Exception as e:
            errs.append(f"Telegram tải link: {type(e).__name__} {e}")
    for e in errs:
        logging.warning("QR lỗi %s", e)
    await m.answer(qr_caption(user, amount, False))
    # Báo lý do lỗi cho admin để dễ sửa (không hiện cho khách)
    await to_admins(f"{E_WARN} <b>Không tạo được mã QR</b> cho ID <code>{user.id}</code>:\n"
                    + "\n".join(f"• {esc(x)[:200]}" for x in errs[:5]))


@dp.message(F.text == "NẠP TIỀN")
async def nap_menu(m: Message, state: FSMContext):
    await state.clear()
    await m.answer(NAP_HELP, reply_markup=nap_keyboard())


@dp.callback_query(F.data.startswith("nap:"))
async def nap_pick(c: CallbackQuery, state: FSMContext):
    value = c.data.split(":", 1)[1]
    if value == "custom":
        await state.set_state(Nap.amount)
        await c.message.answer(
            f"{E_EDIT} Vui lòng gửi <b>số tiền</b> muốn nạp "
            f"(từ {money(MIN_DEPOSIT)} đến {money(MAX_DEPOSIT)}).\n"
            "Ví dụ: <code>75000</code> hoặc <code>75k</code>\n"
            "<i>(bấm một nút trên menu để hủy)</i>")
        return await c.answer()
    if not value.isdigit():
        return await c.answer()
    await state.clear()
    await c.answer("Đang tạo mã QR...")
    await send_qr(c.message, c.from_user, int(value))


async def admin_deposit(m: Message, args):
    """Admin nạp tiền thủ công: /naptay id số_tiền (hoặc /nap id số_tiền)."""
    amount = parse_amount(args[1]) if len(args) == 2 else None
    if len(args) != 2 or not args[0].isdigit() or not amount:
        return await m.answer("Cú pháp: <code>/naptay id số_tiền</code>\n"
                              "Ví dụ: <code>/naptay 123456789 50k</code>")
    uid = int(args[0])
    bal = await add_deposit(uid, amount, f"admin:{m.from_user.id}")
    await m.answer(f"{E_OK} Đã nạp {money(amount)} cho ID <code>{uid}</code>. Số dư mới: {money(bal)}")
    ok = await safe_send(uid, f"{E_OK} <b>NẠP TIỀN THÀNH CÔNG</b>\n"
                              f"Số tiền: <b>{money(amount)}</b>\nSố dư hiện tại: {money(bal)}")
    if not ok:
        await m.answer(f"{E_WARN} Không gửi được thông báo cho người dùng (họ chưa /start hoặc đã chặn bot).")


@dp.message(Command("naptay", "congtien"), admin)
async def naptay_cmd(m: Message, command: CommandObject, state: FSMContext):
    await state.clear()
    await admin_deposit(m, (command.args or "").split())


@dp.message(Command("nap"))
async def nap_cmd(m: Message, command: CommandObject, state: FSMContext):
    await state.clear()
    args = (command.args or "").split()

    # Admin: /nap id số_tiền -> nạp thủ công (giữ lệnh cũ)
    if m.from_user.id in ADMIN_IDS and len(args) == 2:
        return await admin_deposit(m, args)

    # Người dùng: /nap số_tiền -> tự tạo QR
    amount = parse_amount(args[0]) if args else None
    if not amount:
        return await m.answer(NAP_HELP, reply_markup=nap_keyboard())
    if not MIN_DEPOSIT <= amount <= MAX_DEPOSIT:
        return await m.answer(f"{E_WARN} Số tiền nạp từ {money(MIN_DEPOSIT)} đến {money(MAX_DEPOSIT)}.")
    await send_qr(m, m.from_user, amount)


# ===================== MUA HÀNG =====================
def gate_button(g) -> InlineKeyboardButton:
    """Nút cổng; cổng FULL SLOT / BẢO TRÌ (cả cổng) có thêm chữ trên nút."""
    tag = f" • {STATUS_LABEL[g['status']]}" if g["status"] in STATUS_LABEL else ""
    return btn(f"{g['gate']}{tag}", f"gate:{g['gate']}", ID_GAME, "🎮")


@dp.message(F.text == "MUA HÀNG")
async def shop(m: Message, state: FSMContext):
    await state.clear()
    gates = await get_gates()
    if not gates:
        return await m.answer("Hiện chưa có sản phẩm nào, vui lòng quay lại sau.")
    pmap = await packages_map()
    rows = [[gate_button(g) for g in gates[i:i + 2]] for i in range(0, len(gates), 2)]
    lines = []
    for g in gates:
        tag = f" — {E_OFF} <b>{STATUS_LABEL[g['status']]}</b>" if g["status"] in STATUS_LABEL else ""
        lines.append(f"• <b>{g['gate']}</b>{tag}\n   {fmt_pkgs(pmap.get(g['gate'], []))}")
    await m.answer(
        f"{E_CART} <b>BẢNG GIÁ CODE</b>\n━━━━━━━━━━━━━━━\n"
        + "\n".join(lines) +
        f"\n\n{E_TARGET} Chọn cổng game bạn muốn mua bên dưới:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))


async def ask_login(c: CallbackQuery, state: FSMContext, g, pkg):
    price, points = pkg["price"], pkg["points"]
    await state.set_state(Buy.login)
    await state.update_data(gate=g["gate"], idx=pkg["idx"], price=price, points=points, login=None)
    await c.message.answer(
        f"Bạn chọn <b>{g['gate']}</b> — {money(price)} [{points}]\n\n"
        f"{E_EDIT} Vui lòng gửi <b>TÊN ĐĂNG NHẬP</b> của bạn:\n"
        "<i>(bấm một nút trên menu để hủy)</i>")


@dp.callback_query(F.data.startswith("gate:"))
async def pick_gate(c: CallbackQuery, state: FSMContext):
    g = await get_gate(c.data.split(":", 1)[1])
    if not g or not g["active"]:
        return await c.answer("Cổng này tạm ngưng bán.", show_alert=True)
    if g["status"] != "ok":  # cả cổng FULL SLOT / BẢO TRÌ -> không cho mua
        return await c.answer(block_alert(g), show_alert=True)
    pk = await get_packages(g["gate"])
    if not pk:
        return await c.answer("Cổng này chưa có mệnh giá.", show_alert=True)
    if all(p["status"] != "ok" for p in pk):  # mọi mệnh giá đều đang khóa
        return await c.answer(pkg_block_alert(g["gate"], pk[0]) if len(pk) == 1 else
                              f"🛠 {g['gate']}: tất cả mệnh giá đang FULL SLOT / BẢO TRÌ.\n"
                              "Vui lòng quay lại sau khi admin mở lại.", show_alert=True)
    if len(pk) == 1:  # chỉ có 1 mệnh giá -> hỏi tên đăng nhập luôn
        await ask_login(c, state, g, pk[0])
        return await c.answer()

    def pkg_label(p):
        tag = f" • {STATUS_LABEL[p['status']]}" if p["status"] in STATUS_LABEL else ""
        return f"{kfmt(p['price'])} - {p['points']}{tag}"

    rows = [[btn(pkg_label(p), f"pkg:{g['gate']}:{p['idx']}", ID_CASH, "💵")] for p in pk]
    await c.message.answer(f"{E_GAME} Cổng <b>{g['gate']}</b> — chọn mệnh giá:",
                           reply_markup=InlineKeyboardMarkup(inline_keyboard=rows))
    await c.answer()


@dp.callback_query(F.data.startswith("pkg:"))
async def pick_pkg(c: CallbackQuery, state: FSMContext):
    _, name, j = c.data.split(":")
    g = await get_gate(name)
    if not g or not g["active"]:
        return await c.answer("Cổng này tạm ngưng bán.", show_alert=True)
    if g["status"] != "ok":
        return await c.answer(block_alert(g), show_alert=True)
    pkg = await pool.fetchrow("SELECT * FROM packages WHERE gate=$1 AND idx=$2", name, int(j)) \
        if j.isdigit() else None
    if not pkg:
        return await c.answer("Mệnh giá không hợp lệ.", show_alert=True)
    if pkg["status"] != "ok":  # riêng mệnh giá này đang FULL SLOT / BẢO TRÌ
        return await c.answer(pkg_block_alert(name, pkg), show_alert=True)
    await ask_login(c, state, g, pkg)
    await c.answer()


@dp.callback_query(F.data == "buy_no")
async def buy_no(c: CallbackQuery, state: FSMContext):
    await state.clear()
    await c.message.edit_text(f"{E_NO} Đã hủy đơn hàng.")
    await c.answer()


@dp.callback_query(F.data == "buy_ok")
async def buy_ok(c: CallbackQuery, state: FSMContext):
    d = await state.get_data()
    await state.clear()  # xóa ngay để bấm 2 lần không bị mua đúp
    if not d.get("login"):
        return await c.answer("Phiên đã hết hạn, vui lòng chọn lại từ MUA HÀNG.", show_alert=True)
    g = await get_gate(d["gate"])
    if not g or not g["active"]:
        return await c.answer("Cổng này vừa tạm ngưng bán.", show_alert=True)
    if g["status"] != "ok":  # admin vừa bật FULL SLOT / BẢO TRÌ trong lúc khách đang nhập
        await c.message.edit_text(
            f"{E_BAN} Cổng <b>{g['gate']}</b> hiện đang <b>{STATUS_LABEL[g['status']]}</b>, "
            "chưa thể mua. Vui lòng quay lại sau.")
        return await c.answer()
    pkg = await pool.fetchrow("SELECT * FROM packages WHERE gate=$1 AND idx=$2", d["gate"], d.get("idx", -1))
    if not pkg or pkg["price"] != d["price"]:  # admin vừa đổi giá
        await c.message.edit_text(f"{E_WARN} Giá vừa được cập nhật. Vui lòng vào MUA HÀNG và chọn lại.")
        return await c.answer()
    if pkg["status"] != "ok":  # admin vừa khóa riêng mệnh giá này
        await c.message.edit_text(
            f"{E_BAN} Mệnh giá <b>{g['gate']} {kfmt(pkg['price'])}</b> hiện đang "
            f"<b>{STATUS_LABEL[pkg['status']]}</b>, chưa thể mua. "
            "Vui lòng chọn mệnh giá khác hoặc quay lại sau.")
        return await c.answer()
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
        f"{E_WAIT} <b>ĐÃ TẠO ĐƠN — ĐANG XỬ LÝ</b>\nMã đơn: <b>#{oid}</b>\n"
        "Đơn hàng sẽ được xử lý trong vòng <b>24-72H</b>.\n"
        "Theo dõi trạng thái tại mục LỊCH SỬ.")
    await c.answer()
    o = await pool.fetchrow("SELECT * FROM orders WHERE id=$1", oid)
    await send_receipt(uid, o, f"{E_WAIT} Đơn #{oid} — <b>ĐANG XỬ LÝ</b>")
    await notify_admin_order(oid)


async def notify_admin_order(oid, chat_id=None):
    o = await pool.fetchrow(
        "SELECT o.*, u.name, u.username FROM orders o JOIN users u ON u.id=o.user_id WHERE o.id=$1", oid)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        btn("DUYỆT", f"ok:{oid}", ID_OK, "✅"),
        btn("TỪ CHỐI", f"no:{oid}", ID_NO, "❌")]])
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
          "rejected": f"{E_NO} BỊ TỪ CHỐI (KHÔNG HOÀN TIỀN)"}


@dp.message(F.text == "LỊCH SỬ")
async def history(m: Message, state: FSMContext):
    await state.clear()
    uid = m.from_user.id
    deps = await pool.fetch("SELECT * FROM deposits WHERE user_id=$1 ORDER BY id DESC LIMIT 10", uid)
    ords = await pool.fetch("SELECT * FROM orders WHERE user_id=$1 ORDER BY id DESC LIMIT 10", uid)
    t = f"{E_LIST} <b>LỊCH SỬ NẠP TIỀN</b> (10 gần nhất)\n━━━━━━━━━━━━━━━\n"
    t += "\n".join(f"{E_OK} Nạp thành công: <b>{money(d['amount'])}</b> — {fmt(d['created'])}"
                   for d in deps) if deps else "Chưa có giao dịch nạp tiền."
    t += f"\n\n{E_CART} <b>LỊCH SỬ MUA CODE</b> (10 gần nhất)\n━━━━━━━━━━━━━━━\n"

    def order_line(o):
        s = (f"#{o['id']} • {o['gate']} • {money(o['price'])} [{o['points']}]\n"
             f"{STATUS[o['status']]} — {fmt(o['created'])}")
        if o["status"] == "rejected" and o["reason"]:
            s += f"\nLý do: {esc(o['reason'])}"
        return s

    t += "\n\n".join(order_line(o) for o in ords) if ords else "Chưa có đơn hàng."
    await m.answer(t)


@dp.message(F.text == "HỖ TRỢ")
async def support(m: Message, state: FSMContext):
    await state.clear()
    await m.answer(f"{E_HELP} Cần hỗ trợ, vui lòng nhắn qua {SUPPORT}")


# ===================== ADMIN =====================
ADMIN_HELP = (
    f"{E_ADMIN} <b>LỆNH ADMIN</b>\n━━━━━━━━━━━━━━━\n"
    "<code>/naptay id số_tiền</code> — nạp tiền thủ công cho khách (có báo khách)\n"
    "<code>/tru id số_tiền</code> — trừ số dư\n"
    "<code>/donhang</code> — đơn đang chờ xử lý\n"
    "<code>/muatc</code> — đơn mua thành công\n"
    "<code>/thongke</code> — thống kê (có nút reset từng mục)\n"
    "<code>/reset</code> — reset từng mục thống kê\n"
    "<code>/user id</code> — xem thông tin khách\n"
    "<code>/ban id</code> | <code>/unban id</code> — khóa / mở khóa khách\n"
    "<code>/thongbao nội dung</code> — gửi thông báo cho tất cả khách\n"
    "<code>/sanpham</code> — danh sách cổng, đủ mệnh giá và trạng thái\n"
    "<code>/setgia</code> — menu nút ➖/➕ tăng giảm giá từng mệnh giá\n"
    "<code>/set CỔNG giá_cũ giá_mới</code> — sửa trực tiếp giá "
    "(VD: /set LLWIN 450000 350000 = đổi 450K thành 350K)\n"
    "<code>/baotri</code> — menu bật/tắt <b>FULL SLOT</b> và <b>BẢO TRÌ</b>: "
    "chọn cổng rồi khóa <b>từng mệnh giá</b> (VD: chỉ bảo trì 90K) hoặc khóa cả cổng\n"
    "<code>/themcong CỔNG giá điểm</code> — thêm cổng mới\n"
    "<code>/tat CỔNG</code> | <code>/bat CỔNG</code> — ẩn / hiện cổng khỏi menu mua\n"
    "<code>/huy</code> — hủy thao tác nhập lý do từ chối đang dở\n\n"
    "<i>Bấm TỪ CHỐI ở đơn: bot sẽ hỏi lý do, đơn bị từ chối không hoàn tiền.</i>")


@dp.message(Command("admin"), admin)
async def admin_help(m: Message):
    await m.answer(ADMIN_HELP)


@dp.callback_query(F.data.regexp(r"^(ok|no):\d+$"))
async def admin_decide(c: CallbackQuery, state: FSMContext):
    if c.from_user.id not in ADMIN_IDS:
        return await c.answer("Bạn không phải admin.", show_alert=True)
    act, oid = c.data.split(":")
    oid = int(oid)

    # ----- TỪ CHỐI: hỏi admin nhập lý do trước -----
    if act == "no":
        status = await pool.fetchval("SELECT status FROM orders WHERE id=$1", oid)
        if status != "pending":
            return await c.answer("Đơn này đã được xử lý rồi.", show_alert=True)
        await state.set_state(Reject.reason)
        await state.update_data(oid=oid, chat_id=c.message.chat.id,
                                msg_id=c.message.message_id, html=c.message.html_text)
        await c.message.answer(
            f"{E_EDIT} Nhập <b>LÝ DO TỪ CHỐI</b> đơn <b>#{oid}</b>.\n"
            f"{E_WARN} Đơn bị từ chối sẽ <b>KHÔNG hoàn tiền</b> cho khách.\n"
            "Lý do sẽ được gửi kèm thông báo cho khách.\n"
            "<i>Gửi /huy để hủy thao tác.</i>")
        return await c.answer()

    # ----- DUYỆT -----
    o = await pool.fetchrow(
        "UPDATE orders SET status='done' WHERE id=$1 AND status='pending' RETURNING *", oid)
    if not o:
        return await c.answer("Đơn này đã được xử lý rồi.", show_alert=True)
    await send_receipt(
        o["user_id"], o,
        f"{E_OK} <b>Đơn #{oid}</b> ({o['gate']} - {o['points']}) đã được admin xử lý "
        f"<b>THÀNH CÔNG</b>!\nCảm ơn bạn đã ủng hộ {E_HEART}")
    who = esc(c.from_user.full_name)
    await c.message.edit_text(c.message.html_text + f"\n\n<b>{E_OK} ĐÃ DUYỆT</b> bởi {who}")
    await c.answer("Xong")


@dp.message(Command("huy"), admin)
async def cancel_reject(m: Message, state: FSMContext):
    if await state.get_state() == Reject.reason.state:
        await state.clear()
        return await m.answer(f"{E_NO} Đã hủy thao tác từ chối. Đơn vẫn đang chờ xử lý.")
    await m.answer("Không có thao tác nào đang chờ.")


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


# ---------- Thống kê + reset từng mục ----------
# Reset chỉ đặt lại mốc tính thống kê, KHÔNG xóa số dư, đơn hàng hay lịch sử của khách.
RESET_ITEMS = {
    "deposit": "TIỀN NẠP",
    "members": "THÀNH VIÊN",
    "done": "ĐƠN THÀNH CÔNG",
    "spent": "TIỀN MUA CODE",
}


async def reset_points() -> dict:
    rows = await pool.fetch("SELECT key, at FROM stat_reset")
    pts = {k: EPOCH for k in RESET_ITEMS}
    pts.update({r["key"]: r["at"] for r in rows})
    return pts


def since_text(dt) -> str:
    return "" if dt <= EPOCH else f" <i>(từ {dt.astimezone(VN_TZ).strftime('%d/%m/%Y %H:%M')})</i>"


def reset_keyboard() -> InlineKeyboardMarkup:
    rows = [[btn(f"RESET {name}", f"rs:{key}", ID_RESET, "🔄")] for key, name in RESET_ITEMS.items()]
    rows.append([btn("RESET TẤT CẢ", "rs:all", ID_RESET, "🔄")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def build_stats() -> str:
    v = pool.fetchval
    p = await reset_points()
    today = datetime.now(VN_TZ).replace(hour=0, minute=0, second=0, microsecond=0)
    dep = await v("SELECT COALESCE(SUM(amount),0) FROM deposits WHERE created >= $1", p["deposit"])
    mem = await v("SELECT COUNT(*) FROM users WHERE joined >= $1", p["members"])
    done = await v("SELECT COUNT(*) FROM orders WHERE status='done' AND created >= $1", p["done"])
    spent = await v("SELECT COALESCE(SUM(price),0) FROM orders WHERE status='done' AND created >= $1", p["spent"])
    return (
        f"{E_STAT} <b>THỐNG KÊ</b>\n━━━━━━━━━━━━━━━\n"
        f"{E_MONEY} Tổng tiền nạp: <b>{money(dep)}</b>{since_text(p['deposit'])}\n"
        f"{E_USERS} Tổng thành viên: <b>{mem}</b>{since_text(p['members'])}\n"
        f"{E_WAIT} Đơn chờ xử lý: <b>{await v('SELECT COUNT(*) FROM orders WHERE status=$1', 'pending')}</b>\n"
        f"{E_OK} Đơn mua thành công: <b>{done}</b>{since_text(p['done'])}\n"
        f"{E_CART} Tổng tiền mua code thành công: <b>{money(spent)}</b>{since_text(p['spent'])}\n"
        f"{E_CASH} Tổng số dư khách đang giữ: {money(await v('SELECT COALESCE(SUM(balance),0) FROM users'))}\n\n"
        f"{E_DATE} <b>HÔM NAY</b>\n"
        f"• Khách mới: {await v('SELECT COUNT(*) FROM users WHERE joined >= $1', today)}\n"
        f"• Tiền nạp: {money(await v('SELECT COALESCE(SUM(amount),0) FROM deposits WHERE created >= $1', today))}\n"
        f"• Đơn mới: {await v('SELECT COUNT(*) FROM orders WHERE created >= $1', today)}\n\n"
        f"{E_INFO} Đơn chờ xử lý và số dư khách là dữ liệu thật nên không reset được.")


@dp.message(Command("thongke"), admin)
async def thongke(m: Message):
    await m.answer(await build_stats(), reply_markup=reset_keyboard())


@dp.message(Command("reset"), admin)
async def reset_cmd(m: Message):
    await m.answer(
        f"{E_RESET} <b>RESET THỐNG KÊ</b>\n━━━━━━━━━━━━━━━\n"
        "Chọn mục muốn reset về 0. Chỉ đặt lại mốc tính thống kê, "
        "<b>không xóa</b> số dư, đơn hàng hay lịch sử của khách.",
        reply_markup=reset_keyboard())


@dp.callback_query(F.data.regexp(r"^rs:(deposit|members|done|spent|all)$"))
async def reset_ask(c: CallbackQuery):
    if c.from_user.id not in ADMIN_IDS:
        return await c.answer("Bạn không phải admin.", show_alert=True)
    key = c.data.split(":")[1]
    name = "TẤT CẢ CÁC MỤC" if key == "all" else RESET_ITEMS[key]
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        btn("XÁC NHẬN", f"rsy:{key}", ID_OK, "✅"),
        btn("HỦY", "rsn", ID_NO, "❌")]])
    await c.message.answer(f"{E_WARN} Xác nhận reset <b>{name}</b> về 0?", reply_markup=kb)
    await c.answer()


@dp.callback_query(F.data == "rsn")
async def reset_cancel(c: CallbackQuery):
    await c.message.edit_text(f"{E_NO} Đã hủy reset.")
    await c.answer()


@dp.callback_query(F.data.regexp(r"^rsy:(deposit|members|done|spent|all)$"))
async def reset_do(c: CallbackQuery):
    if c.from_user.id not in ADMIN_IDS:
        return await c.answer("Bạn không phải admin.", show_alert=True)
    key = c.data.split(":")[1]
    keys = list(RESET_ITEMS) if key == "all" else [key]
    for k in keys:
        await pool.execute(
            "INSERT INTO stat_reset(key, at) VALUES($1, now()) "
            "ON CONFLICT (key) DO UPDATE SET at=now()", k)
    name = "tất cả các mục" if key == "all" else RESET_ITEMS[key]
    await c.message.edit_text(f"{E_OK} Đã reset <b>{name}</b> về 0.")
    await c.message.answer(await build_stats(), reply_markup=reset_keyboard())
    await c.answer("Đã reset")


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
    status = f"{E_BAN} Đang bị khóa" if u["banned"] else f"{E_ON} Bình thường"
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
        await bot.send_message(m.chat.id, text)  # xem thử (và kiểm tra lỗi HTML)
    except TelegramBadRequest:
        return await m.answer(f"{E_WARN} Nội dung có thẻ HTML sai, vui lòng kiểm tra lại.")
    ids = [r["id"] for r in await pool.fetch("SELECT id FROM users WHERE NOT banned") if r["id"] != m.chat.id]
    await m.answer(f"{E_MEGA} Đang gửi cho {len(ids)} người...")
    ok = 0
    for uid in ids:
        ok += await safe_send(uid, text)
        await asyncio.sleep(0.05)  # tránh bị Telegram giới hạn
    await m.answer(f"{E_OK} Gửi xong: {ok}/{len(ids)} người nhận được.")


# ---------- Danh sách cổng ----------
@dp.message(Command("sanpham"), admin)
async def sanpham(m: Message):
    rows = await get_gates(active_only=False)
    pmap = await packages_map()
    lines = []
    for g in rows:
        tag = f" — <b>{STATUS_LABEL[g['status']]}</b>" if g["status"] in STATUS_LABEL else ""
        if not g["active"]:
            tag += " — <b>ĐANG ẨN</b>"
        lines.append(f"{E_ON if g['active'] and g['status'] == 'ok' else E_OFF} <b>{g['gate']}</b>{tag}\n"
                     f"    {fmt_pkgs(pmap.get(g['gate'], []))}")
    await send_long(m.chat.id, f"{E_CART} <b>DANH SÁCH CỔNG</b>\n\n" + "\n".join(lines))


# ---------- Sửa giá: /set (gõ nhanh) và /setgia (menu nút tăng giảm) ----------
# Giá sửa trực tiếp vào bảng packages nên menu MUA HÀNG đổi ngay lập tức.
@dp.message(Command("set"), admin)
async def set_price(m: Message, command: CommandObject):
    usage = ("Cú pháp: <code>/set CỔNG giá_cũ giá_mới</code>\n"
             "VD: <code>/set LLWIN 450000 350000</code> (sửa giá 450K thành 350K)")
    a = (command.args or "").split()
    if len(a) != 3:
        return await m.answer(usage)
    name = a[0].upper()
    old, new = parse_amount(a[1]), parse_amount(a[2])
    if not old or not new:
        return await m.answer(usage)
    if not await get_gate(name):
        return await m.answer(f"{E_NO} Không có cổng <b>{esc(name)}</b>.\n\n{usage}")
    if new < MIN_PRICE:
        return await m.answer(f"{E_WARN} Giá mới tối thiểu {money(MIN_PRICE)}.")
    if new == old:
        return await m.answer(f"{E_WARN} Giá mới trùng giá cũ, không có gì thay đổi.")
    pk = await pool.fetchrow(
        "SELECT * FROM packages WHERE gate=$1 AND price=$2 ORDER BY idx LIMIT 1", name, old)
    if not pk:
        cur = fmt_pkgs(await get_packages(name))
        return await m.answer(f"{E_NO} Cổng <b>{name}</b> không có mệnh giá {money(old)}.\n"
                              f"Hiện có: {cur}")
    await pool.execute("UPDATE packages SET price=$3 WHERE gate=$1 AND idx=$2", name, pk["idx"], new)
    if pk["idx"] == 0:  # giữ đồng bộ giá gốc trong bảng products
        await pool.execute("UPDATE products SET price=$2 WHERE gate=$1", name, new)
    await m.answer(
        f"{E_OK} Đã sửa giá <b>{name}</b> [{pk['points']}]: {money(old)} ➜ <b>{money(new)}</b>\n"
        "Giá mới đã áp dụng ngay trên menu MUA HÀNG.\n\n"
        f"Hiện tại: {fmt_pkgs(await get_packages(name))}")


async def price_list_view():
    """Màn hình chọn cổng: hiện đủ mọi mệnh giá của mọi cổng."""
    gates = await get_gates(active_only=False)
    pmap = await packages_map()
    lines = "\n".join(f"• <b>{g['gate']}</b>: {fmt_pkgs(pmap.get(g['gate'], []))}" for g in gates)
    rows = [[InlineKeyboardButton(text=g["gate"], callback_data=f"pv:{g['gate']}:10000")
             for g in gates[i:i + 3]] for i in range(0, len(gates), 3)]
    text = (f"{E_CASH} <b>SỬA GIÁ CODE</b>\n━━━━━━━━━━━━━━━\n{lines}\n\n"
            f"{E_TARGET} Chọn cổng bên dưới để tăng/giảm giá.\n"
            "<i>Hoặc gõ nhanh: /set CỔNG giá_cũ giá_mới</i>")
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


async def price_view(gate: str, step: int):
    """Màn hình sửa giá của 1 cổng: mỗi mệnh giá có nút ➖ / ➕, đổi bước nhảy ở hàng dưới."""
    pk = await get_packages(gate)
    lines = "\n".join(f"• {money(p['price'])} [{p['points']}]" for p in pk)
    text = (f"{E_CASH} <b>SỬA GIÁ {gate}</b>\n━━━━━━━━━━━━━━━\n{lines}\n\n"
            f"Bước chỉnh: <b>{kfmt(step)}</b> — bấm ➖ để giảm, ➕ để tăng giá từng mệnh giá.\n"
            "Giá đổi là áp dụng ngay trên menu MUA HÀNG.")
    rows = []
    for p in pk:
        i = p["idx"]
        rows.append([
            InlineKeyboardButton(text=f"➖ {kfmt(step)}", callback_data=f"pp:{gate}:{i}:d:{step}"),
            InlineKeyboardButton(text=f"{kfmt(p['price'])} [{p['points']}]", callback_data="noop"),
            InlineKeyboardButton(text=f"➕ {kfmt(step)}", callback_data=f"pp:{gate}:{i}:u:{step}"),
        ])
    rows.append([InlineKeyboardButton(text=(f"✓ {kfmt(s)}" if s == step else kfmt(s)),
                                      callback_data=f"pv:{gate}:{s}") for s in PRICE_STEPS])
    rows.append([InlineKeyboardButton(text="⬅️ QUAY LẠI DANH SÁCH", callback_data="pl")])
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


@dp.message(Command("setgia"), admin)
async def setgia_menu(m: Message, state: FSMContext):
    await state.clear()
    text, kb = await price_list_view()
    await m.answer(text, reply_markup=kb)


@dp.callback_query(F.data == "pl", admin)
async def price_back(c: CallbackQuery):
    text, kb = await price_list_view()
    await safe_edit(c.message, text, kb)
    await c.answer()


@dp.callback_query(F.data.regexp(r"^pv:[A-Z0-9]+:\d+$"), admin)
async def price_open(c: CallbackQuery):
    _, gate, step = c.data.split(":")
    step = int(step)
    if step not in PRICE_STEPS or not await get_gate(gate):
        return await c.answer("Không hợp lệ.", show_alert=True)
    text, kb = await price_view(gate, step)
    await safe_edit(c.message, text, kb)
    await c.answer()


@dp.callback_query(F.data.regexp(r"^pp:[A-Z0-9]+:\d+:[ud]:\d+$"), admin)
async def price_step(c: CallbackQuery):
    _, gate, idx, sign, step = c.data.split(":")
    step = int(step)
    if step not in PRICE_STEPS:
        return await c.answer("Không hợp lệ.", show_alert=True)
    delta = step if sign == "u" else -step
    new = await pool.fetchval(
        "UPDATE packages SET price=GREATEST(price+$3::bigint, $4::bigint) "
        "WHERE gate=$1 AND idx=$2 RETURNING price", gate, int(idx), delta, MIN_PRICE)
    if new is None:
        return await c.answer("Không tìm thấy mệnh giá này.", show_alert=True)
    if int(idx) == 0:  # giữ đồng bộ giá gốc trong bảng products
        await pool.execute("UPDATE products SET price=$2 WHERE gate=$1", gate, new)
    text, kb = await price_view(gate, step)
    await safe_edit(c.message, text, kb)
    await c.answer(f"{gate}: {money(new)}")


@dp.callback_query(F.data == "noop")
async def noop(c: CallbackQuery):
    await c.answer()


# ---------- Bảo trì / Full slot (khóa cả cổng HOẶC từng mệnh giá) ----------
# Màn 1 (/baotri): danh sách cổng + trạng thái từng mệnh giá, bấm tên cổng để vào chỉnh.
# Màn 2: mỗi mệnh giá có 2 nút FULL SLOT / BẢO TRÌ riêng; ngoài ra có 2 nút khóa cả cổng.
# Khóa 1 mệnh giá (VD 90K) thì khách vẫn mua được các mệnh giá khác của cổng đó.
async def maint_view():
    """Màn hình tổng: mỗi cổng 1 nút để vào chỉnh từng mệnh giá."""
    gates = await get_gates(active_only=False)
    pmap = await packages_map()
    lines, buttons = [], []
    for g in gates:
        n, st = g["gate"], g["status"]
        pk = pmap.get(n, [])
        locked = sum(1 for p in pk if p["status"] != "ok")
        tag = f" — <b>{STATUS_LABEL[st]} (CẢ CỔNG)</b>" if st in STATUS_LABEL else ""
        ok_all = st == "ok" and locked == 0
        lines.append(f"{E_ON if ok_all else E_OFF} <b>{n}</b>{tag}\n    {fmt_pkgs(pk)}")
        mark = "🔴" if (st != "ok" or locked) else "⚪"
        buttons.append(InlineKeyboardButton(text=f"{mark} {n}", callback_data=f"bmv:{n}"))
    rows = [buttons[i:i + 3] for i in range(0, len(buttons), 3)]
    rows.append([InlineKeyboardButton(text="🛠 BẢO TRÌ TẤT CẢ", callback_data="bta:m"),
                 InlineKeyboardButton(text="✅ MỞ LẠI TẤT CẢ", callback_data="bta:o")])
    text = (f"{E_ADMIN} <b>BẢO TRÌ / FULL SLOT</b>\n━━━━━━━━━━━━━━━\n"
            + "\n".join(lines) +
            "\n\n🔴 = có mệnh giá/cổng đang bị khóa • ⚪ = đang bán bình thường\n"
            f"{E_TARGET} Bấm tên cổng bên dưới để khóa <b>từng mệnh giá</b> "
            "(VD: chỉ bảo trì 90K, các giá khác vẫn mua được).")
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


async def maint_gate_view(name: str):
    """Màn hình chỉnh của 1 cổng: nút FULL SLOT / BẢO TRÌ cho từng mệnh giá và cho cả cổng."""
    g = await get_gate(name)
    pk = await get_packages(name)
    st = g["status"]
    lines = []
    for p in pk:
        label = f" — <b>{STATUS_LABEL[p['status']]}</b>" if p["status"] in STATUS_LABEL else ""
        lines.append(f"{E_OFF if p['status'] != 'ok' else E_ON} {kfmt(p['price'])} [{p['points']}]{label}")
    rows = []
    for p in pk:
        s, i, k = p["status"], p["idx"], kfmt(p["price"])
        rows.append([
            InlineKeyboardButton(text=f"{'🔴' if s == 'full' else '⚪'} {k} FULL SLOT",
                                 callback_data=f"bp:{name}:{i}:f"),
            InlineKeyboardButton(text=f"{'🔴' if s == 'maint' else '⚪'} {k} BẢO TRÌ",
                                 callback_data=f"bp:{name}:{i}:m"),
        ])
    rows.append([
        InlineKeyboardButton(text=f"{'🔴' if st == 'full' else '⚪'} CẢ CỔNG FULL SLOT",
                             callback_data=f"bt:{name}:f"),
        InlineKeyboardButton(text=f"{'🔴' if st == 'maint' else '⚪'} CẢ CỔNG BẢO TRÌ",
                             callback_data=f"bt:{name}:m"),
    ])
    rows.append([InlineKeyboardButton(text="⬅️ QUAY LẠI DANH SÁCH", callback_data="bml")])
    gate_tag = f"\nTrạng thái cả cổng: <b>{STATUS_LABEL[st]}</b>" if st in STATUS_LABEL else ""
    text = (f"{E_ADMIN} <b>{name} — BẢO TRÌ / FULL SLOT</b>\n━━━━━━━━━━━━━━━\n"
            + "\n".join(lines) + gate_tag +
            "\n\n🔴 = đang BẬT (khách bấm vào sẽ thấy thông báo và không mua được mệnh giá đó)\n"
            "⚪ = đang TẮT. Bấm lại nút để tắt/mở bán lại.\n"
            "Nút <b>CẢ CỔNG</b> khóa toàn bộ mệnh giá của cổng này cùng lúc.")
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


@dp.message(Command("baotri"), admin)
async def baotri_menu(m: Message, state: FSMContext):
    await state.clear()
    text, kb = await maint_view()
    await m.answer(text, reply_markup=kb)


@dp.callback_query(F.data == "bml", admin)
async def maint_back(c: CallbackQuery):
    text, kb = await maint_view()
    await safe_edit(c.message, text, kb)
    await c.answer()


@dp.callback_query(F.data.regexp(r"^bmv:[A-Z0-9]+$"), admin)
async def maint_open(c: CallbackQuery):
    name = c.data.split(":")[1]
    if not await get_gate(name):
        return await c.answer("Không tìm thấy cổng.", show_alert=True)
    text, kb = await maint_gate_view(name)
    await safe_edit(c.message, text, kb)
    await c.answer()


@dp.callback_query(F.data.regexp(r"^bp:[A-Z0-9]+:\d+:[fm]$"), admin)
async def maint_pkg_toggle(c: CallbackQuery):
    """Bật/tắt FULL SLOT hoặc BẢO TRÌ cho RIÊNG MỘT mệnh giá."""
    _, name, idx, kind = c.data.split(":")
    target = "full" if kind == "f" else "maint"
    pkg = await pool.fetchrow("SELECT * FROM packages WHERE gate=$1 AND idx=$2", name, int(idx))
    if not pkg:
        return await c.answer("Không tìm thấy mệnh giá.", show_alert=True)
    new = "ok" if pkg["status"] == target else target  # bấm lần nữa để tắt
    await pool.execute("UPDATE packages SET status=$3 WHERE gate=$1 AND idx=$2", name, int(idx), new)
    text, kb = await maint_gate_view(name)
    await safe_edit(c.message, text, kb)
    await c.answer(f"{name} {kfmt(pkg['price'])}: {STATUS_LABEL.get(new, 'ĐÃ MỞ BÁN')}")


@dp.callback_query(F.data.regexp(r"^bt:[A-Z0-9]+:[fm]$"), admin)
async def maint_toggle(c: CallbackQuery):
    """Bật/tắt FULL SLOT hoặc BẢO TRÌ cho CẢ CỔNG."""
    _, name, kind = c.data.split(":")
    target = "full" if kind == "f" else "maint"
    g = await get_gate(name)
    if not g:
        return await c.answer("Không tìm thấy cổng.", show_alert=True)
    new = "ok" if g["status"] == target else target  # bấm lần nữa để tắt
    await pool.execute("UPDATE products SET status=$2 WHERE gate=$1", name, new)
    text, kb = await maint_gate_view(name)
    await safe_edit(c.message, text, kb)
    await c.answer(f"{name} (cả cổng): {STATUS_LABEL.get(new, 'ĐÃ MỞ BÁN')}")


@dp.callback_query(F.data.regexp(r"^bta:[mo]$"), admin)
async def maint_all(c: CallbackQuery):
    new = "maint" if c.data.endswith("m") else "ok"
    await pool.execute("UPDATE products SET status=$1", new)
    if new == "ok":  # mở lại tất cả -> mở luôn từng mệnh giá đang bị khóa
        await pool.execute("UPDATE packages SET status='ok'")
    text, kb = await maint_view()
    await safe_edit(c.message, text, kb)
    await c.answer("Đã bảo trì tất cả" if new == "maint" else "Đã mở bán tất cả")


@dp.message(Command("themcong"), admin)
async def themcong(m: Message, command: CommandObject):
    a = (command.args or "").split(maxsplit=2)
    price = parse_amount(a[1]) if len(a) == 3 else None
    name = a[0].upper() if a else ""
    if not price or not re.fullmatch(r"[A-Z0-9]{2,12}", name):
        return await m.answer("Cú pháp: <code>/themcong CỔNG giá điểm</code>\n"
                              "VD: <code>/themcong ABC88 85000 188 ĐIỂM</code>")
    if await get_gate(name):
        return await m.answer("Cổng này đã tồn tại, dùng /set hoặc /setgia để đổi giá.")
    pos = await pool.fetchval("SELECT COALESCE(MAX(pos),0)+1 FROM products")
    pts = a[2].upper()
    await pool.execute("INSERT INTO products(gate, price, points, pos) VALUES($1,$2,$3,$4)",
                       name, price, pts, pos)
    async with pool.acquire() as c:
        await seed_packages(c, name, price, pts)
    await m.answer(f"{E_OK} Đã thêm cổng <b>{name}</b>\n{fmt_pkgs(await get_packages(name))}")


@dp.message(Command("tat", "bat"), admin)
async def toggle_gate(m: Message, command: CommandObject):
    name = (command.args or "").strip().upper()
    if not await get_gate(name):
        return await m.answer(f"Cú pháp: <code>/{command.command} CỔNG</code>")
    flag = command.command == "bat"
    await pool.execute("UPDATE products SET active=$2 WHERE gate=$1", name, flag)
    head = f"{E_OK} Đã hiện" if flag else f"{E_NO} Đã ẩn"
    await m.answer(f"{head} <b>{name}</b> {'trên' if flag else 'khỏi'} menu mua hàng")


# Đặt cuối cùng: lệnh không tồn tại
@dp.message(F.text.startswith("/"))
async def unknown_cmd(m: Message):
    await answer_menu(m, f"{E_INFO} Lệnh không tồn tại. Vui lòng dùng menu bên dưới nhé.")


# Các handler theo trạng thái đặt SAU nút menu và lệnh,
# để bấm menu/lệnh khi đang nhập dở vẫn hoạt động bình thường.
@dp.message(Nap.amount, F.text)
async def nap_custom_amount(m: Message, state: FSMContext):
    amount = parse_amount(m.text)
    if not amount or not MIN_DEPOSIT <= amount <= MAX_DEPOSIT:
        return await m.answer(f"{E_WARN} Số tiền không hợp lệ. Vui lòng nhập từ "
                              f"{money(MIN_DEPOSIT)} đến {money(MAX_DEPOSIT)} (VD: 75000 hoặc 75k).")
    await state.clear()
    await send_qr(m, m.from_user, amount)


@dp.message(Buy.login, F.text)
async def get_login(m: Message, state: FSMContext):
    login = m.text.strip()
    if not re.fullmatch(r"[\w.@\-]{3,40}", login):
        return await m.answer(f"{E_WARN} Tên đăng nhập không hợp lệ (3-40 ký tự, không dấu cách). "
                              "Vui lòng gửi lại.")
    await state.update_data(login=login)
    d = await state.get_data()
    bal = await balance_of(m.from_user.id)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        btn("XÁC NHẬN MUA", "buy_ok", ID_OK, "✅"),
        btn("HỦY", "buy_no", ID_NO, "❌")]])
    await m.answer(
        f"{E_NOTE} <b>XÁC NHẬN ĐƠN HÀNG</b>\n━━━━━━━━━━━━━━━\n"
        "Dịch vụ: CODE LDC\n"
        f"Cổng: <b>{d['gate']}</b>\n"
        f"Giá tiền: <b>{money(d['price'])}</b>\n"
        f"Điểm: {d['points']}\n"
        f"Tên đăng nhập: <code>{esc(login)}</code>\n"
        f"Số dư hiện tại: {money(bal)}\n\n"
        f"{E_WARN} Vui lòng kiểm tra lại thông tin trước khi xác nhận.",
        reply_markup=kb)


@dp.message(Reject.reason, F.text, admin)
async def reject_reason(m: Message, state: FSMContext):
    """Admin nhập lý do từ chối -> từ chối đơn (KHÔNG hoàn tiền) và báo khách kèm lý do."""
    reason = m.text.strip()[:500]
    if not reason:
        return await m.answer(f"{E_WARN} Lý do không được để trống. Vui lòng nhập lại hoặc /huy.")
    d = await state.get_data()
    await state.clear()
    oid = d["oid"]
    o = await pool.fetchrow(
        "UPDATE orders SET status='rejected', reason=$2 WHERE id=$1 AND status='pending' RETURNING *",
        oid, reason)
    if not o:
        return await m.answer(f"{E_WARN} Đơn #{oid} đã được xử lý rồi.")

    sent = await send_receipt(
        o["user_id"], o,
        f"{E_NO} <b>Đơn #{oid}</b> ({o['gate']}) bị <b>TỪ CHỐI</b>.\n"
        f"{E_NOTE} Lý do: {esc(reason)}\n"
        f"{E_WARN} Đơn bị từ chối không được hoàn tiền.\n"
        f"Cần hỗ trợ vui lòng liên hệ {SUPPORT}",
        reason=reason)
    if not sent:  # gửi file lỗi thì vẫn báo bằng tin nhắn thường
        await safe_send(o["user_id"],
                        f"{E_NO} <b>Đơn #{oid}</b> ({o['gate']}) bị <b>TỪ CHỐI</b>.\n"
                        f"{E_NOTE} Lý do: {esc(reason)}\n"
                        f"{E_WARN} Đơn bị từ chối không được hoàn tiền.\n"
                        f"Cần hỗ trợ vui lòng liên hệ {SUPPORT}")

    who = esc(m.from_user.full_name)
    try:  # cập nhật tin đơn cũ, bỏ nút duyệt/từ chối
        await bot.edit_message_text(
            d["html"] + f"\n\n<b>{E_NO} ĐÃ TỪ CHỐI</b> bởi {who}\nLý do: {esc(reason)}",
            chat_id=d["chat_id"], message_id=d["msg_id"])
    except Exception:
        pass
    await m.answer(f"{E_OK} Đã từ chối đơn <b>#{oid}</b> (không hoàn tiền) và gửi lý do cho khách.")


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
                 BotCommand(command="naptay", description="Nạp tiền thủ công: /naptay id số_tiền"),
                 BotCommand(command="donhang", description="Đơn đang chờ"),
                 BotCommand(command="thongke", description="Thống kê"),
                 BotCommand(command="reset", description="Reset từng mục thống kê"),
                 BotCommand(command="setgia", description="Menu tăng/giảm giá code"),
                 BotCommand(command="set", description="Sửa giá: /set CỔNG giá_cũ giá_mới"),
                 BotCommand(command="baotri", description="Bật/tắt Full slot - Bảo trì từng giá")],
                scope=BotCommandScopeChat(chat_id=a))
    except Exception:
        logging.warning("Không đặt được danh sách lệnh (admin cần /start bot trước).")
    try:
        await dp.start_polling(bot)
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
