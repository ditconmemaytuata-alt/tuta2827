from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto, ChatPermissions
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler
from telegram.constants import ParseMode
import psycopg2
from psycopg2 import extras
from datetime import datetime, timedelta
import os
import re
import asyncio
import random
import csv
import hashlib
from io import BytesIO
import pytz
import html
import traceback

# ============================================================
# CUSTOM EMOJI MAPPING
# ============================================================
CUSTOM_EMOJI = {
    "🥰": "5238188302279909462", "👋": "5235701688014217208", "🙂": "5238185738184435219",
    "⌨️": "5242451907724716893", "❤️": "6307296870179804027", "🆗": "6307624533234815952",
    "💰": "6307538509334844759", "🍀": "6307381081603577097", "⁉️": "5314504236132747481",
    "⚠️": "5420323339723881652", "☄️": "5224607267797606837", "🛍": "5229064374403998351",
    "⛔️": "5260293700088511294", "🚫": "5240241223632954241", "❗️": "5274099962655816924",
    "👀": "5210956306952758910", "❌": "5210952531676504517", "💸": "5231449120635370684",
    "💱": "5402186569006210455", "▶️": "5264919878082509254", "💥": "5276032951342088188",
    "🔗": "5271604874419647061", "🔄": "5375338737028841420", "🔝": "5415655814079723871",
    "➕": "5397916757333654639", "✉️": "5253742260054409879", "📍": "5391032818111363540",
    "💎": "5427168083074628963", "⭐️": "5438496463044752972", "⭐": "5267500801240092311",
    "🗑": "5445267414562389170", "🔖": "5222444124698853913", "🔒": "5296369303661067030",
    "😮": "5303479226882603449", "📎": "5305265301917549162", "⚙️": "5341715473882955310",
    "🎮": "5361741454685256344", "🔈": "5388632425314140043", "⌛": "5386367538735104399",
    "⬇️": "5406745015365943482", "🌧": "5399913388845322366", "❄️": "5449449325434266744",
    "🌈": "5409109841538994759", "💧": "5393512611968995988", "🥇": "5440539497383087970",
    "🥈": "5447203607294265305", "🥉": "5453902265922376865", "🆓": "5406756500108501710",
    "🚨": "5395695537687123235", "🏠": "5416041192905265756", "🚩": "5460755126761312667",
    "🎉": "5461151367559141950", "🔥": "6309824960944673394", "🐣": "6307545381282517559",
    "🐺": "6309898817202295364", "⚡": "6143242687274291080", "😎": "6224009027584528984",
    "🚗": "6280407793631498213", "👅": "6192771593001767805", "😘": "6172246648668821119",
    "🦉": "6172679422458467366", "🏳️": "6336979307558081524", "🎁": "6064301746719562425",
    "🇻🇳": "6111496780103292027", "🌟": "6111754757313926362", "😃": "6111737246732262016",
    "😞": "6199453007336184702", "😍": "6273945156341209192", "👍": "5440910346334255336",
    "🔔": "5440833702642857683", "🤭": "5253821918812862724", "🍭": "5255858639549251782",
    "💳": "5472250091332993630", "🎰": "5235989279024373566", "⚖️": "5461152608804689572",
    "🧲": "5202106638508512484", "📞": "5213179235996294999", "📥": "5443127283898405358",
    "📤": "5445355530111437729", "🐻": "5411089297476441876", "🖼": "5262517101578443800",
    "👥": "5453957997418004470", "📊": "5231200819986047254", "💬": "5386691718571646404",
    "🦌": "5422516277010774456", "🦀": "5319247469165433798", "💿": "5429118663946945233",
    "🃏": "5298499667569425533", "🎯": "5256131095094652290", "💍": "5262922516426420894",
    "🍬": "5404573776253825754", "🏅": "5204271353565300127", "➖": "5382261056078881010",
    "📈": "5244837092042750681", "📉": "5246762912428603768", "✨": "5325547803936572038",
    "✅": "6003745186042089867", "🔓": "5291873529464122510", "🔑": "5278573677900752088",
    "✔️": "5780463361175066565", "🆘": "5429262837409138106", "✏️": "5395444784611480792",
    "🗓": "5413879192267805083", "🔜": "5440621591387980068", "🚀": "5372917041193828849",
    "☀️": "5373021138316186413", "🌛": "5438362704878250587", "🏆": "5188344996356448758",
    "👑": "5217822164362739968", "🛒": "5400090058030075645", "⏰": "5386415655253730366",
    "💵": "5409048419211682843", "💠": "5461151367559141950", "📫": "5287533898803211359",
    "🛠": "5462921117423384478", "📌": "5397782960512444700", "✍️": "5258500400918587241",
    "🆔": "5443038326535759644", "📜": "6098288123580518916", "🛡": "5197288647275071607",
    "🔮": "5278651867780377852", "🐯": "5456463412393342595", "🐉": "5395493912344353272",
    "🫵": "5461098492216752942", "😮‍💨": "5192886773948107844", "🤕": "5350584327946127806",
    "😯": "5350392879778908359", "🥸": "5391112412445288650", "🥷": "5217514674769120391",
    "👤": "5332455502917949981", "🏦": "5332455502917949981", "🎴": "5276239041052828276",
    "1️⃣": "5305763715692377402", "2️⃣": "5307907239380528763", "3️⃣": "5305783000095537258",
    "4️⃣": "5382054253403577563", "5️⃣": "5391197405553107640", "6️⃣": "5390966190283694453",
    "7️⃣": "5382132232829804982", "8️⃣": "5391038994274329680", "9️⃣": "5391234698754138414",
    "🟢": "5416081784641168838", "🔙": "5352759161945867747",
    "⬅️": "5363896514655564837", "➡️": "5416117059207572332", "📣": "5298609030321691620",
    "😵": "5465137208878969279", "⚰️": "5463186335948878489", "⬆️": "5463122435425448565",
    "❓": "5463139580934892960", "👌": "5463423955014529788", "step_1": "5415655814079723871",
    "step_2": "5375338737028841420", "step_3": "5382357040008021292", "😆": "5375135722514685501",
    "game_icon_1": "5217822164362739968", "game_icon_2": "5386367538735104399",
    "game_icon_3": "5361741454685256344", "game_icon_4": "5422439311196834318",
    "game_icon_5": "5406683434124859552", "game_icon_6": "5416041192905265756",
    "game_icon_7": "5460755126761312667", "🪙": "5379773896352355687",
    # ---------- EMOJI MỚI THÊM ----------
    "🎲": "5280816565657300091", "💡": "5262844652964303985", "🤑": "5427107837568360763",
    "🖥": "5282843764451195532", "💻": "5193177581888755275", "🔋": "5307905813451397794",
    "⛏": "5197371802136892976", "↗️": "5429651785352501917", "↔️": "5271837459783638319",
    "🌐": "5447410659077661506", "🥐": "6075743256128263137", "👨‍💻": "6066579956287148786",
    "😂": "6138433913040671508", "😀": "6138749335438889769", "😱": "5253478445983222118",
    "☺️": "5238015713314086319", "🖐": "5237759703198474072", "💩": "5235622845299565321",
    "🚘": "5240037474679398914", "😳": "5238083517962793068", "😏": "5237903859480796749",
    "🏃‍♀️": "5237981615568723131", "🤩": "5195357093107868151", "😕": "5197226061011623665",
    "🍌": "5237784970491074950", "🤓": "5240209101572545926", "😡": "5240408207666455054",
    "🔫": "5235762367312173706", "😨": "5242500342070909767", "😭": "5460630100263312018",
    "🤪": "5240076365608264313", "🍔": "5239948040575393823", "🐶": "5242395424609803673",
    "🤫": "6226686020570584326", "🤘": "6163685838250054493", "🎖": "6165926565638051547",
    "🤬": "6168156972219635148", "🍑": "6165529117954413678", "🕺": "6186015776948885249",
    "🌷": "6197378228894568973", "😇": "6195191910152279859", "🚊": "6208671312823456804",
    "🤨": "6208304964998010180", "🎶": "6235381315005325678", "😝": "6273634436932179409",
    "🤜": "5375161616872520280", "✈️": "5456216132308462012", "🧪": "5294451377425106537",
    "💃": "5373112999076699207", "ℹ️": "5334544901428229844", "©": "5323442290708985472",
    "🫦": "5395444514028529554", "😧": "5237721297600912488",
}

# Emoji chưa có ID premium riêng -> dùng tạm emoji premium gần nghĩa nhất cho ICON NÚT BẤM
ICON_ALIAS = {
    "🌸": "🌷", "🍕": "🍭", "🔍": "👀", "🔴": "🚩", "⚪": "🏳️", "⚪️": "🏳️",
    "🔐": "🔒", "🧑‍🤝‍🧑": "👥", "₿": "💸", "⚫": "🔒", "🔵": "🔝",
}

def ce(emoji: str) -> str:
    emoji_id = CUSTOM_EMOJI.get(emoji)
    if emoji_id:
        return f'<tg-emoji emoji-id="{emoji_id}">{emoji}</tg-emoji>'
    return emoji

def ce_id(custom_id: str) -> str:
    return f'<tg-emoji emoji-id="{custom_id}">•</tg-emoji>'

def _icon_id(emoji):
    if not emoji:
        return None
    return CUSTOM_EMOJI.get(emoji) or CUSTOM_EMOJI.get(ICON_ALIAS.get(emoji, ""))

def btn(text, emoji=None, callback_data=None, url=None):
    """Nút inline có icon emoji premium (icon_custom_emoji_id, Bot API 9.4+)."""
    cid = _icon_id(emoji)
    if cid:
        return InlineKeyboardButton(text, callback_data=callback_data, url=url,
                                    api_kwargs={"icon_custom_emoji_id": cid})
    if emoji:
        text = f"{emoji} {text}"
    return InlineKeyboardButton(text, callback_data=callback_data, url=url)

def kbtn(text, emoji=None):
    """Nút bàn phím trả lời (ReplyKeyboard) có icon emoji premium."""
    cid = _icon_id(emoji)
    if cid:
        return KeyboardButton(text, api_kwargs={"icon_custom_emoji_id": cid})
    if emoji:
        text = f"{emoji} {text}"
    return KeyboardButton(text)

def fmt_money(amount: int) -> str:
    return f"{amount:,}".replace(",", ".")

VIETNAM_TZ = pytz.timezone('Asia/Ho_Chi_Minh')

def get_vietnam_time():
    return datetime.now(VIETNAM_TZ)

def get_vietnam_date():
    return get_vietnam_time().strftime("%d/%m/%Y")

def get_vietnam_datetime_db():
    return get_vietnam_time().strftime("%H:%M - %d/%m/%Y")

TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

ADMIN_IDS = [5633649201, 7884394252]
BOT_USERNAME = "Jav88gamebot"
ROOM_LINK = "https://t.me/Jav88gamebot"
MIN_WITHDRAW = 50000
LOG_GROUP_ID = -1004375247819

BANK_ID = "MB"
ACCOUNT_NO = "0003456712345"
ACCOUNT_NAME = "LY THI CHAM"

_bot_instance = None
GROUP_IDS = [-1004375247819]

group_games = {}
room_betting_enabled = {}
game_history = {}
SESSION_COUNTER = {"value": 0}
pending_inputs = {}

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def query(q, args=()):
    conn = get_db_connection()
    cur = conn.cursor()
    res = None
    try:
        # Không có tham số thì truyền None để dấu % trong câu SQL không bị psycopg2 xử lý
        cur.execute(q, args if args else None)
        if cur.description:
            res = cur.fetchall()
        conn.commit()
    except Exception as e:
        print(f"Database Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()
    return res

# TẠO CÁC BẢNG
query("CREATE TABLE IF NOT EXISTS codes (code TEXT PRIMARY KEY, reward INTEGER, uses INTEGER)")
query("""
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    balance BIGINT DEFAULT 0,
    refs INTEGER DEFAULT 0,
    refed INTEGER DEFAULT 0,
    bank TEXT DEFAULT NULL,
    stk TEXT DEFAULT NULL,
    name TEXT DEFAULT NULL,
    last_checkin TEXT,
    last_withdraw TEXT,
    total_bet BIGINT DEFAULT 0,
    rate_bonus INTEGER DEFAULT NULL,
    bank_linked INTEGER DEFAULT 0
)
""")
query("CREATE TABLE IF NOT EXISTS banned_games (user_id BIGINT, game_id INTEGER, PRIMARY KEY (user_id, game_id))")
query("CREATE TABLE IF NOT EXISTS banned_features (user_id BIGINT, feature TEXT, PRIMARY KEY (user_id, feature))")
query("CREATE TABLE IF NOT EXISTS banned_admins (admin_id BIGINT PRIMARY KEY, banned_by BIGINT, reason TEXT, banned_at TEXT)")
query("""
CREATE TABLE IF NOT EXISTS user_bonus (
    user_id BIGINT PRIMARY KEY,
    bonus_amount BIGINT DEFAULT 0,
    required_bet BIGINT DEFAULT 0,
    current_bet BIGINT DEFAULT 0,
    created_at TEXT
)
""")
query("""
CREATE TABLE IF NOT EXISTS deposit_history (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    amount BIGINT,
    admin_id BIGINT,
    status TEXT DEFAULT 'pending',
    time TEXT
)
""")
query("""
CREATE TABLE IF NOT EXISTS withdraw_history (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    amount BIGINT,
    status TEXT DEFAULT 'pending',
    time TEXT,
    admin_id BIGINT,
    admin_note TEXT
)
""")
query("""
CREATE TABLE IF NOT EXISTS banned_admin_commands (
    admin_id BIGINT,
    command TEXT,
    banned_by BIGINT,
    reason TEXT,
    banned_at TEXT,
    PRIMARY KEY (admin_id, command)
)
""")
query("""
CREATE TABLE IF NOT EXISTS code_usage (
    user_id BIGINT,
    code TEXT,
    used_date TEXT,
    PRIMARY KEY (user_id, code, used_date)
)
""")
query("""
CREATE TABLE IF NOT EXISTS group_interactions (
    user_id BIGINT,
    group_id BIGINT,
    interaction_count INTEGER DEFAULT 0,
    last_interaction TEXT,
    PRIMARY KEY (user_id, group_id)
)
""")
query("""
CREATE TABLE IF NOT EXISTS daily_top_interactions (
    user_id BIGINT,
    group_id BIGINT,
    interaction_count INTEGER DEFAULT 0,
    date TEXT,
    rank INTEGER,
    reward_amount BIGINT DEFAULT 0,
    rewarded INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, group_id, date)
)
""")
query("""
CREATE TABLE IF NOT EXISTS tanthu_code (
    user_id BIGINT PRIMARY KEY,
    code TEXT,
    received_at TEXT,
    used INTEGER DEFAULT 0
)
""")
query("""
CREATE TABLE IF NOT EXISTS codenap (
    code TEXT PRIMARY KEY,
    reward BIGINT,
    required_amount BIGINT,
    wager INTEGER,
    expiry TEXT,
    used INTEGER DEFAULT 0,
    created_by BIGINT,
    created_at TEXT
)
""")
query("""
CREATE TABLE IF NOT EXISTS ket_sat (
    user_id BIGINT PRIMARY KEY,
    amount BIGINT DEFAULT 0,
    term TEXT,
    interest BIGINT DEFAULT 0,
    start_time TEXT
)
""")
query("""
CREATE TABLE IF NOT EXISTS tich_luy_nap (
    user_id BIGINT,
    milestone INTEGER,
    claimed BOOLEAN DEFAULT FALSE,
    date TEXT,
    PRIMARY KEY (user_id, milestone, date)
)
""")

query("ALTER TABLE users ADD COLUMN IF NOT EXISTS total_bet BIGINT DEFAULT 0")
query("ALTER TABLE users ADD COLUMN IF NOT EXISTS rate_bonus INTEGER DEFAULT NULL")
query("ALTER TABLE users ADD COLUMN IF NOT EXISTS bank_linked INTEGER DEFAULT 0")
query("ALTER TABLE users ADD COLUMN IF NOT EXISTS vip_spent BIGINT DEFAULT 0")
query("""
CREATE TABLE IF NOT EXISTS bet_daily (
    user_id BIGINT,
    day DATE,
    bet BIGINT DEFAULT 0,
    win BIGINT DEFAULT 0,
    PRIMARY KEY (user_id, day)
)
""")
query("""
CREATE TABLE IF NOT EXISTS rewards (
    id SERIAL PRIMARY KEY,
    user_id BIGINT,
    rtype TEXT,
    period TEXT,
    base BIGINT DEFAULT 0,
    amount BIGINT DEFAULT 0,
    claimed INTEGER DEFAULT 0,
    created_at TEXT,
    claimed_at TEXT,
    UNIQUE (user_id, rtype, period)
)
""")
query("""
CREATE TABLE IF NOT EXISTS giftcodes (
    code TEXT PRIMARY KEY,
    ctype TEXT,
    reward BIGINT,
    wager INTEGER DEFAULT 1,
    expiry TIMESTAMPTZ,
    require_deposit INTEGER DEFAULT 0,
    required_amount BIGINT DEFAULT 0,
    bound_user BIGINT,
    used INTEGER DEFAULT 0,
    used_by BIGINT,
    used_at TEXT,
    created_by BIGINT,
    created_at TEXT
)
""")

query("CREATE TABLE IF NOT EXISTS history (user_id BIGINT, amount BIGINT, note TEXT, time TEXT)")
# Thêm cột id tự tăng để sắp xếp lịch sử đúng thứ tự (cột time là chữ nên ORDER BY time bị sai)
query("ALTER TABLE history ADD COLUMN IF NOT EXISTS id SERIAL")
query("CREATE TABLE IF NOT EXISTS banned (user_id BIGINT PRIMARY KEY)")
query("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")

maintenance_keys = ['mt_taixiu_room', 'mt_xucxac_don', 'mt_longho', 'mt_minipoker', 'mt_baccarat', 'mt_xocdia4', 'mt_taixiumd5', 'mt_baucua', 'mt_xocdia6', 'mt_nap', 'mt_rut']
for k in maintenance_keys:
    res = query("SELECT 1 FROM settings WHERE key=%s", (k,))
    if not res:
        query("INSERT INTO settings VALUES(%s, '0')", (k,))

res_name = query("SELECT 1 FROM settings WHERE key='bot_display_name'")
if not res_name:
    query("INSERT INTO settings(key, value) VALUES('bot_display_name', 'Hệ thống Game Uy Tín')")

res_system_mt = query("SELECT 1 FROM settings WHERE key='system_maintenance'")
if not res_system_mt:
    query("INSERT INTO settings VALUES('system_maintenance', '0')")

res_tongbao = query("SELECT 1 FROM settings WHERE key='mt_tongbao'")
if not res_tongbao:
    query("INSERT INTO settings VALUES('mt_tongbao', '0')")

res_jackpot = query("SELECT 1 FROM settings WHERE key='jackpot_amount'")
if not res_jackpot:
    query("INSERT INTO settings VALUES('jackpot_amount', '100000')")

def is_system_maintenance():
    res = query("SELECT value FROM settings WHERE key='system_maintenance'")
    return res[0][0] == '1' if res else False

def is_total_maintenance():
    res = query("SELECT value FROM settings WHERE key='mt_tongbao'")
    return res[0][0] == '1' if res else False

def is_admin_banned(admin_id):
    res = query("SELECT 1 FROM banned_admins WHERE admin_id=%s", (admin_id,))
    return len(res) > 0 if res else False

def is_admin_command_banned(admin_id, command):
    res = query("SELECT 1 FROM banned_admin_commands WHERE admin_id=%s AND command=%s", (admin_id, command))
    return len(res) > 0 if res else False

def admin_only(func):
    async def wrapper(update: Update, ctx: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        msg_obj = update.effective_message
        if is_system_maintenance() and user_id not in ADMIN_IDS:
            await msg_obj.reply_text(
                f'{ce("⚡")} <b>HỆ THỐNG ĐANG BẢO TRÌ</b>\n\nVui lòng quay lại sau ít phút!',
                parse_mode=ParseMode.HTML
            )
            return
        if user_id in ADMIN_IDS and is_admin_banned(user_id):
            await msg_obj.reply_text(
                f'{ce("🚫")} <b>Bạn đã bị cấm sử dụng các lệnh Admin!</b>',
                parse_mode=ParseMode.HTML
            )
            return
        if user_id not in ADMIN_IDS:
            await msg_obj.reply_text(f'{ce("❌")} Bạn không có quyền sử dụng lệnh này!', parse_mode=ParseMode.HTML)
            return
        return await func(update, ctx, *args, **kwargs)
    return wrapper

def check_mt(key):
    res = query("SELECT value FROM settings WHERE key=%s", (key,))
    if res:
        return res[0][0] == '1'
    query("INSERT INTO settings (key, value) VALUES (%s, '0') ON CONFLICT (key) DO NOTHING", (key,))
    return False

def get_bot_name():
    res = query("SELECT value FROM settings WHERE key='bot_display_name'")
    return res[0][0] if res else "Hệ thống Game Uy Tín"

def is_game_banned(uid, gid):
    res = query("SELECT 1 FROM banned_games WHERE user_id=%s AND game_id=%s", (uid, gid))
    return len(res) > 0 if res else False

def is_feature_banned(uid, feature):
    res = query("SELECT 1 FROM banned_features WHERE user_id=%s AND feature=%s", (uid, feature))
    return len(res) > 0 if res else False

def get_vip_info(total_bet):
    vip_points = total_bet // 300000
    if vip_points >= 100000: return "VIP 9 (Chí Tôn)", vip_points
    if vip_points >= 50000: return "VIP 8 (Huyền Thoại)", vip_points
    if vip_points >= 10000: return "VIP 7 (Đại Tướng)", vip_points
    if vip_points >= 5000: return "VIP 6 (Chiến Tướng)", vip_points
    if vip_points >= 1000: return "VIP 5 (Cao Thủ)", vip_points
    if vip_points >= 500: return "VIP 4 (Kim Cương)", vip_points
    if vip_points >= 100: return "VIP 3 (Bạch Kim)", vip_points
    if vip_points >= 50: return "VIP 2 (Vàng)", vip_points
    if vip_points >= 10: return "VIP 1 (Bạc)", vip_points
    return "VIP 0 (Đồng)", vip_points

def get_user(uid):
    res = query("SELECT 1 FROM users WHERE user_id=%s", (uid,))
    if not res:
        query("INSERT INTO users(user_id) VALUES(%s)", (uid,))

def get_balance(uid):
    get_user(uid)
    res = query("SELECT balance FROM users WHERE user_id=%s", (uid,))
    return res[0][0] if res else 0

def is_banned(uid):
    res = query("SELECT 1 FROM banned WHERE user_id=%s", (uid,))
    return len(res) > 0 if res else False

def add_money(uid, amt, note):
    get_user(uid)
    now_str = get_vietnam_datetime_db()
    query("UPDATE users SET balance=balance+%s WHERE user_id=%s", (amt, uid))
    query("INSERT INTO history(user_id, amount, note, time) VALUES(%s,%s,%s,%s)", (uid, amt, note, now_str))
    if amt > 0 and note.startswith(WIN_NOTE_PREFIXES):
        record_daily(uid, win=amt)

def sub_money(uid, amt, note="withdraw"):
    get_user(uid)
    bal = get_balance(uid)
    if bal < amt:
        return False
    now_str = get_vietnam_datetime_db()
    query("UPDATE users SET balance=balance-%s WHERE user_id=%s", (amt, uid))
    query("INSERT INTO history(user_id, amount, note, time) VALUES(%s,%s,%s,%s)", (uid, -amt, note, now_str))
    if (note != "Rút tiền" and note != "withdraw" and "Admin" not in note
            and "Chuyển tiền" not in note and not note.startswith("Mua giftcode")):
        query("UPDATE users SET total_bet=total_bet+%s WHERE user_id=%s", (amt, uid))
        record_daily(uid, bet=amt)
        update_bet_progress(uid, amt)
    return True

def add_bonus_with_requirement(user_id, bonus_amount, required_multiplier=2):
    required_bet = bonus_amount * required_multiplier
    now_str = get_vietnam_datetime_db()
    query("DELETE FROM user_bonus WHERE user_id=%s", (user_id,))
    query("INSERT INTO user_bonus (user_id, bonus_amount, required_bet, current_bet, created_at) VALUES (%s, %s, %s, %s, %s)",
          (user_id, bonus_amount, required_bet, 0, now_str))
    add_money(user_id, bonus_amount, f"Khuyến mãi nạp +{bonus_amount:,}đ (yêu cầu cược x{required_multiplier})")
    return required_bet

def get_remaining_bet_required(user_id):
    bonus_data = query("SELECT required_bet, current_bet FROM user_bonus WHERE user_id=%s", (user_id,))
    if not bonus_data or bonus_data[0][0] == 0:
        return 0
    required_bet, current_bet = bonus_data[0]
    return max(0, required_bet - current_bet)

async def check_and_notify_bet_completion(user_id: int, current_bet: int, required_bet: int):
    if current_bet >= required_bet:
        bonus_data = query("SELECT bonus_amount, required_bet, current_bet FROM user_bonus WHERE user_id=%s", (user_id,))
        if bonus_data:
            bonus_amount, req_bet, curr_bet = bonus_data[0]
            message = (
                f'{ce("🎉")} <b>CHÚC MỪNG! BẠN ĐÃ HOÀN THÀNH YÊU CẦU CƯỢC!</b> {ce("🎉")}\n'
                f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
                f'{ce("💰")} <b>Tiền khuyến mãi đã nhận:</b> <code>+{fmt_money(bonus_amount)}đ</code>\n'
                f'{ce("🎯")} <b>Yêu cầu cược:</b> <code>{fmt_money(req_bet)}đ</code>\n'
                f'{ce("✅")} <b>Tổng cược đã thực hiện:</b> <code>{fmt_money(curr_bet)}đ</code>\n'
                f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
                f'{ce("🔓")} <b>Bạn đã có thể rút tiền bình thường!</b>'
            )
            try:
                if _bot_instance:
                    await _bot_instance.send_message(user_id, message, parse_mode=ParseMode.HTML)
            except:
                pass
            query("DELETE FROM user_bonus WHERE user_id=%s", (user_id,))
            return True
    return False

def update_bet_progress(user_id: int, bet_amount: int):
    bonus_data = query("SELECT required_bet, current_bet FROM user_bonus WHERE user_id=%s", (user_id,))
    if not bonus_data or bonus_data[0][0] == 0:
        return False
    required_bet, current_bet = bonus_data[0]
    new_bet = current_bet + bet_amount
    query("UPDATE user_bonus SET current_bet=%s WHERE user_id=%s", (new_bet, user_id))
    if new_bet >= required_bet:
        try:
            asyncio.get_running_loop().create_task(check_and_notify_bet_completion(user_id, new_bet, required_bet))
        except RuntimeError:
            pass
        return True
    return False

def get_bet_progress_status(user_id: int):
    bonus_data = query("SELECT bonus_amount, required_bet, current_bet FROM user_bonus WHERE user_id=%s", (user_id,))
    if not bonus_data or bonus_data[0][1] == 0:
        return None
    bonus_amount, required_bet, current_bet = bonus_data[0]
    percent = (current_bet / required_bet * 100) if required_bet > 0 else 0
    remaining = required_bet - current_bet
    return {
        'bonus_amount': bonus_amount,
        'required_bet': required_bet,
        'current_bet': current_bet,
        'percent': percent,
        'remaining': remaining,
        'is_completed': current_bet >= required_bet
    }

def gen_code():
    return ''.join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789") for _ in range(8))

def get_deposit_info(user_id, amount=0):
    qr_url = f"https://img.vietqr.io/image/{BANK_ID}-{ACCOUNT_NO}-qr_only.png?amount={amount}&addInfo=Ndech%20{user_id}&accountName={ACCOUNT_NAME}"

    caption = (
        f'{ce("💳")} <b>THÔNG TIN NẠP TIỀN</b>\n\n'
        f'{ce("💳")} Ngân hàng: <b>MBBANK</b>\n'
        f'{ce("👥")} CTK: <b>{ACCOUNT_NAME}</b>\n'
        f'{ce("💰")} STK: <code>{ACCOUNT_NO}</code>\n'
        f'{ce("✍️")} Nội dung: <code>Ndech {user_id}</code>\n'
        f'{ce("💰")} Số tiền: <code>{fmt_money(amount)}đ</code>\n\n'
        f'{ce("⚡")} <i>Lưu ý: Quét mã QR để tự động điền nội dung. Hệ thống cộng tiền sau 1-3 phút.</i>'
    )
    return qr_url, caption

def deposit_menu_content(uid):
    """Menu chọn mệnh giá nạp (dùng cho nút NẠP TIỀN và nút đổi mệnh giá)."""
    kb = InlineKeyboardMarkup([
        [btn("10k", "💵", "dep_10000"), btn("20k", "💵", "dep_20000"), btn("50k", "💵", "dep_50000")],
        [btn("100k", "💵", "dep_100000"), btn("200k", "💵", "dep_200000"), btn("500k", "💵", "dep_500000")],
        [btn("1m", "💰", "dep_1000000"), btn("2m", "💰", "dep_2000000"), btn("5m", "💰", "dep_5000000")],
        [btn("10m", "💎", "dep_10000000"), btn("20m", "💎", "dep_20000000"), btn("50m", "💎", "dep_50000000")],
        [btn("Hỗ Trợ", "🔔", "dep_support")]
    ])
    s1 = f'<tg-emoji emoji-id="{CUSTOM_EMOJI["step_1"]}">🔝</tg-emoji>'
    s2 = f'<tg-emoji emoji-id="{CUSTOM_EMOJI["step_2"]}">🔄</tg-emoji>'
    s3 = f'<tg-emoji emoji-id="{CUSTOM_EMOJI["step_3"]}">🆕</tg-emoji>'
    caption = (
        f'{ce("🎁")} <b>Khuyến Mãi 10% NẠP TIỀN SIÊU TỐC</b> {ce("😃")}\n\n'
        f'{s1} <b>Bước 1:</b> Quét QR hoặc chuyển khoản tới STK\n'
        f'{s2} <b>Bước 2:</b> Ghi đúng nội dung: <code>Ndech {uid}</code>\n'
        f'{s3} <b>Bước 3:</b> Chờ 1-3 phút, tiền tự động cộng vào ví {ce("✍️")}\n\n'
        f'{ce("⚡")} <i>Chọn mệnh giá bên dưới để lấy QR có sẵn số tiền hoặc dùng lệnh /nap [số_tiền]</i> {ce("🫵")}'
    )
    qr_url, _ = get_deposit_info(uid, 0)
    return qr_url, caption, kb

def format_money(amount):
    return f"{amount:,}".replace(",", ".")

# ============================================================
# ===== [MỚI] TIỆN ÍCH CÀI ĐẶT / THỐNG KÊ CƯỢC THEO NGÀY ======
# ============================================================
def get_setting(key, default=None):
    res = query("SELECT value FROM settings WHERE key=%s", (key,))
    return res[0][0] if res else default

def set_setting(key, value):
    query("INSERT INTO settings(key, value) VALUES(%s, %s) "
          "ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value", (key, str(value)))

WIN_NOTE_PREFIXES = ("Thắng", "Nổ hũ", "Hoàn tiền Long Hổ", "Hoàn tiền Baccarat")

def record_daily(uid, bet=0, win=0):
    """Ghi cược / tiền thắng theo ngày (giờ Việt Nam) để tính hoàn cược - hoàn thua."""
    day = get_vietnam_time().date()
    query(
        "INSERT INTO bet_daily(user_id, day, bet, win) VALUES(%s,%s,%s,%s) "
        "ON CONFLICT (user_id, day) DO UPDATE SET "
        "bet=bet_daily.bet+EXCLUDED.bet, win=bet_daily.win+EXCLUDED.win",
        (uid, day, bet, win))

def backfill_bet_daily():
    """Chạy 1 lần: dựng bảng bet_daily từ lịch sử cũ (8 ngày gần nhất)."""
    if get_setting('bet_daily_backfill') == '1':
        return
    sql = """
    INSERT INTO bet_daily(user_id, day, bet, win)
    SELECT user_id, d,
           COALESCE(SUM(CASE WHEN amount<0 AND note LIKE 'Cược%' THEN -amount ELSE 0 END),0),
           COALESCE(SUM(CASE WHEN amount>0 AND (note LIKE 'Thắng%' OR note LIKE 'Nổ hũ%'
                     OR note LIKE 'Hoàn tiền Long Hổ%' OR note LIKE 'Hoàn tiền Baccarat%')
                     THEN amount ELSE 0 END),0)
    FROM (
        SELECT user_id, amount, note,
               CASE WHEN "time" ~ '[0-9]{2}/[0-9]{2}/[0-9]{4}$'
                    THEN to_date(right("time",10),'DD/MM/YYYY') END AS d
        FROM history
    ) h
    WHERE d >= (current_date - 8)
    GROUP BY user_id, d
    ON CONFLICT (user_id, day) DO NOTHING
    """
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute(sql)
        conn.commit()
        set_setting('bet_daily_backfill', '1')
        print("✅ Đã dựng bet_daily từ lịch sử cũ")
    except Exception as e:
        conn.rollback()
        print(f"Backfill bet_daily lỗi: {e}")
    finally:
        cur.close()
        conn.close()

def week_start(d):
    return d - timedelta(days=d.weekday())

def period_stats(uid, d1, d2):
    res = query("SELECT COALESCE(SUM(bet),0), COALESCE(SUM(win),0) FROM bet_daily "
                "WHERE user_id=%s AND day BETWEEN %s AND %s", (uid, d1, d2))
    if not res:
        return 0, 0
    return int(res[0][0] or 0), int(res[0][1] or 0)

def get_bet_stats(uid):
    """(cược hôm nay, cược tuần này)"""
    today = get_vietnam_time().date()
    ws = week_start(today)
    day_bet, _ = period_stats(uid, today, today)
    week_bet, _ = period_stats(uid, ws, ws + timedelta(days=6))
    return day_bet, week_bet

def deposited_today(uid):
    today_str = get_vietnam_date()
    res = query("SELECT COALESCE(SUM(amount),0) FROM deposit_history "
                "WHERE user_id=%s AND status='success' AND right(\"time\",10)=%s", (uid, today_str))
    return int(res[0][0] or 0) if res else 0

def total_deposited(uid):
    res = query("SELECT COALESCE(SUM(amount),0) FROM deposit_history WHERE user_id=%s AND status='success'", (uid,))
    return int(res[0][0] or 0) if res else 0

def fmt_duration(minutes):
    if minutes >= 1440 and minutes % 1440 == 0:
        return f"{minutes // 1440} ngày"
    if minutes >= 60 and minutes % 60 == 0:
        return f"{minutes // 60} tiếng"
    return f"{minutes} phút"

async def safe_answer(q, text=None, alert=False):
    try:
        await q.answer(text, show_alert=alert) if text else await q.answer()
    except Exception:
        pass

# ============================================================
# ===== [MỚI] VIP ============================================
# ============================================================
VIP_POINT_BET = 300000
# (cấp, emoji, tên, điểm yêu cầu, 1 điểm = ? đ)
VIP_LEVELS = [
    (0, "🥉", "Đồng", 0, 0),
    (1, "🥈", "Bạc", 10, 100),
    (2, "🥇", "Vàng", 50, 200),
    (3, "⭐", "Bạch Kim", 100, 300),
    (4, "💎", "Kim Cương", 500, 400),
    (5, "🏆", "Cao Thủ", 1000, 500),
    (6, "⚔️", "Chiến Tướng", 5000, 600),
    (7, "💎", "Đại Tướng", 10000, 700),
    (8, "👑", "Huyền Thoại", 50000, 800),
    (9, "💰", "Chí Tôn", 100000, 1000),
]

def get_vip_level(points):
    lvl = 0
    for item in VIP_LEVELS:
        if points >= item[3]:
            lvl = item[0]
    return lvl

def vip_info(uid):
    get_user(uid)
    res = query("SELECT COALESCE(total_bet,0), COALESCE(vip_spent,0) FROM users WHERE user_id=%s", (uid,))
    total_bet, spent = (int(res[0][0]), int(res[0][1])) if res else (0, 0)
    points = total_bet // VIP_POINT_BET
    lvl = get_vip_level(points)
    redeemable = max(0, points - spent) if lvl >= 1 else 0
    return {"points": points, "lvl": lvl, "spent": spent,
            "redeemable": redeemable, "rate": VIP_LEVELS[lvl][4]}

def vip_screen(uid):
    info = vip_info(uid)
    lvl = info["lvl"]
    _, icon, name, _, _ = VIP_LEVELS[lvl]
    if lvl < 9:
        nxt = VIP_LEVELS[lvl + 1]
        progress = f'{info["points"]}/{nxt[3]} up VIP {nxt[0]}'
    else:
        progress = f'{info["points"]} (cấp tối đa)'

    level_lines = "\n".join(f'VIP {v[0]}: {ce(v[1])} ({v[2]})' for v in VIP_LEVELS)
    need_lines = "\n".join(f'VIP {v[0]}: {v[3]}' for v in VIP_LEVELS[1:])
    rate_lines = "\n".join(f'VIP {v[0]}: 1 điểm = {fmt_money(v[4])}' for v in VIP_LEVELS[1:])

    text = (
        f'{ce("👑")} <b>Cấp VIP hiện tại:</b> {ce(icon)} ({name})\n'
        f'{ce("🚀")} <b>Điểm VIP:</b> <b>{progress}</b>\n'
        f'{ce("🖐")} <b>Số điểm VIP có thể đổi:</b> <b>{fmt_money(info["redeemable"])}</b>\n\n'
        f'Với mỗi <b>300K</b> tiền cược, bạn nhận <b>1 điểm VIP</b>.\n'
        f'Điểm này dùng để xét tăng cấp VIP và đổi thưởng.\n\n'
        f'{ce("💎")} Tỉ lệ quy đổi: đạt VIP 1 để mở đổi điểm (VIP 1: 1 điểm = 100đ)\n\n'
        f'{ce("🏆")} <b>CẤP VIP VÀ BIỂU TƯỢNG</b>\n{level_lines}\n\n'
        f'{ce("📌")} <b>ĐIỂM YÊU CẦU ĐỂ ĐẠT CẤP VIP</b>\n{need_lines}\n\n'
        f'{ce("💎")} <b>TỈ LỆ QUY ĐỔI ĐIỂM</b>\n{rate_lines}\n\n'
        f'{ce("❤️")} <b>Cách đổi điểm VIP</b>\n'
        f'<code>/doidiemvip [số điểm]</code>\n'
        f'VD: <code>/doidiemvip 100</code>'
    )
    kb = InlineKeyboardMarkup([[btn("Đổi điểm VIP", "🪙", callback_data="vip_doi")]])
    return text, kb

def vip_exchange(uid, pts):
    """Đổi điểm VIP -> tiền. Trả về (ok, html)."""
    info = vip_info(uid)
    if info["lvl"] < 1:
        return False, f'{ce("❌")} Bạn cần đạt <b>VIP 1</b> (10 điểm VIP) để mở tính năng đổi điểm.'
    if pts <= 0:
        return False, f'{ce("❌")} Số điểm đổi phải lớn hơn 0.'
    if pts > info["redeemable"]:
        return False, (f'{ce("❌")} Bạn chỉ có thể đổi tối đa <b>{fmt_money(info["redeemable"])}</b> điểm VIP.')
    r = query(
        "UPDATE users SET vip_spent=COALESCE(vip_spent,0)+%s WHERE user_id=%s "
        "AND (COALESCE(total_bet,0)/%s - COALESCE(vip_spent,0)) >= %s RETURNING vip_spent",
        (pts, uid, VIP_POINT_BET, pts))
    if not r:
        return False, f'{ce("❌")} Không đủ điểm VIP để đổi, vui lòng thử lại.'
    money = pts * info["rate"]
    add_money(uid, money, f"Đổi {pts} điểm VIP (VIP {info['lvl']})")
    return True, (
        f'{ce("🎉")} <b>ĐỔI ĐIỂM VIP THÀNH CÔNG!</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("🖐")} Điểm đã đổi: <code>{fmt_money(pts)}</code>\n'
        f'{ce("💎")} Tỉ lệ: <code>1 điểm = {fmt_money(info["rate"])}đ</code> (VIP {info["lvl"]})\n'
        f'{ce("💰")} Nhận được: <code>+{fmt_money(money)}đ</code>\n'
        f'{ce("🏆")} Điểm còn lại: <code>{fmt_money(info["redeemable"] - pts)}</code>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("💰")} Số dư hiện tại: <code>{fmt_money(get_balance(uid))}đ</code>'
    )

async def doi_diem_vip_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg_obj = update.effective_message
    uid = update.effective_user.id
    if is_banned(uid):
        return
    args = ctx.args or []
    info = vip_info(uid)
    if not args:
        return await msg_obj.reply_text(
            f'{ce("💎")} <b>Cách đổi điểm VIP:</b>\n'
            f'<code>/doidiemvip [số điểm]</code>\n'
            f'VD: <code>/doidiemvip 100</code> hoặc <code>/doidiemvip all</code>\n\n'
            f'{ce("🖐")} Điểm có thể đổi: <b>{fmt_money(info["redeemable"])}</b>',
            parse_mode=ParseMode.HTML)
    arg = args[0].lower()
    if arg in ("all", "max"):
        pts = info["redeemable"]
    else:
        try:
            pts = int(arg.replace(",", "").replace(".", ""))
        except ValueError:
            return await msg_obj.reply_text(f'{ce("❌")} Số điểm không hợp lệ! VD: <code>/doidiemvip 100</code>', parse_mode=ParseMode.HTML)
    ok, text = vip_exchange(uid, pts)
    await msg_obj.reply_text(text, parse_mode=ParseMode.HTML)

async def vip_exchange_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE, d: str):
    q = update.callback_query
    uid = q.from_user.id
    info = vip_info(uid)
    if d == "vip_doi":
        if info["lvl"] < 1:
            return await safe_answer(q, "Bạn cần đạt VIP 1 (10 điểm VIP) để mở đổi điểm!", True)
        if info["redeemable"] <= 0:
            return await safe_answer(q, "Bạn chưa có điểm VIP nào để đổi!", True)
        await safe_answer(q)
        money = info["redeemable"] * info["rate"]
        kb = InlineKeyboardMarkup([[btn(f"Đổi tất cả {fmt_money(info['redeemable'])} điểm", "🪙", callback_data="vip_doi_all")]])
        return await q.message.reply_text(
            f'{ce("🪙")} <b>ĐỔI ĐIỂM VIP</b>\n'
            f'{ce("🖐")} Điểm có thể đổi: <b>{fmt_money(info["redeemable"])}</b>\n'
            f'{ce("💎")} Tỉ lệ: <code>1 điểm = {fmt_money(info["rate"])}đ</code>\n'
            f'{ce("💰")} Tổng nhận: <code>{fmt_money(money)}đ</code>\n\n'
            f'Đổi một phần: <code>/doidiemvip [số điểm]</code>',
            reply_markup=kb, parse_mode=ParseMode.HTML)
    # vip_doi_all
    ok, text = vip_exchange(uid, info["redeemable"])
    await safe_answer(q)
    try:
        await q.message.edit_text(text, parse_mode=ParseMode.HTML)
    except Exception:
        await q.message.reply_text(text, parse_mode=ParseMode.HTML)

# ============================================================
# ===== [MỚI] TRUNG TÂM NHẬN THƯỞNG ==========================
# ============================================================
MIN_REWARD_BASE = 100000
# (mốc tối thiểu, % hoàn) - hoàn thua theo bậc
LOSS_TIERS_DAY = [(1_000_000_000, 12), (100_000_000, 8), (10_000_000, 6), (1_000_000, 4), (100_000, 2)]
LOSS_TIERS_WEEK = [(1_000_000_000, 5), (100_000_000, 3), (10_000_000, 2.5), (1_000_000, 2), (100_000, 1)]

RTYPE_LABEL = {
    "cuoc_ngay": ("HOÀN CƯỢC NGÀY", "🔥"),
    "cuoc_tuan": ("HOÀN CƯỢC TUẦN", "🚀"),
    "thua_ngay": ("HOÀN THUA NGÀY", "📉"),
    "thua_tuan": ("HOÀN THUA TUẦN", "🗓"),
}

def get_rebate_pct(kind):
    """kind: 'ngay' | 'tuan' -> % hoàn cược (mặc định 2%)."""
    try:
        return float(get_setting(f"rebate_{kind}_pct", "2"))
    except (TypeError, ValueError):
        return 2.0

def fmt_pct(p):
    return f"{p:g}"

def reward_calc(rtype, bet, win):
    """Trả về (doanh số/thua ròng, tiền hoàn dự kiến)."""
    if rtype.startswith("cuoc"):
        base = bet
        if base < MIN_REWARD_BASE:
            return base, 0
        pct = get_rebate_pct("ngay" if rtype == "cuoc_ngay" else "tuan")
        return base, int(base * pct / 100)
    base = max(0, bet - win)
    if base < MIN_REWARD_BASE:
        return base, 0
    tiers = LOSS_TIERS_DAY if rtype == "thua_ngay" else LOSS_TIERS_WEEK
    for threshold, pct in tiers:
        if base >= threshold:
            return base, int(base * pct / 100)
    return base, 0

def fmt_remaining(delta):
    total = max(0, int(delta.total_seconds()))
    days, rem = divmod(total, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    if days:
        return f"{days} ngày {h:02d}:{m:02d}:{s:02d}"
    return f"{h:02d}:{m:02d}:{s:02d}"

def _end_of_day(d):
    return VIETNAM_TZ.localize(datetime.combine(d, datetime.max.time().replace(microsecond=0)))

def fmt_period(rtype, period):
    try:
        d = datetime.strptime(period, "%Y-%m-%d").date()
    except Exception:
        return period
    if rtype.endswith("ngay"):
        return d.strftime("%d/%m")
    return f"{d.strftime('%d/%m')} - {(d + timedelta(days=6)).strftime('%d/%m')}"

def _reward_card(rtype, label, value, amount, remain):
    title, icon = RTYPE_LABEL[rtype]
    if amount > 0:
        status = f'{ce("✅")} Đạt mốc • Dự kiến hoàn: <b>{fmt_money(amount)}đ</b>'
    else:
        status = f'{ce("❌")} Chưa đạt mốc tối thiểu <b>{fmt_money(MIN_REWARD_BASE)}đ</b>'
    return (f'<blockquote>{ce(icon)} <b>{title}</b>\n'
            f'{label}: {fmt_money(value)}\n'
            f'{status}\n'
            f'{ce("⌛")} Còn {remain}</blockquote>')

def reward_center(uid):
    now = get_vietnam_time()
    today = now.date()
    ws = week_start(today)
    we = ws + timedelta(days=6)
    d_bet, d_win = period_stats(uid, today, today)
    w_bet, w_win = period_stats(uid, ws, we)
    day_left = fmt_remaining(_end_of_day(today) - now)
    week_left = fmt_remaining(_end_of_day(we) - now)

    cards = []
    for rtype, bet, win, left, label in (
        ("cuoc_ngay", d_bet, d_win, day_left, "Doanh số"),
        ("cuoc_tuan", w_bet, w_win, week_left, "Doanh số"),
        ("thua_ngay", d_bet, d_win, day_left, "Thua ròng"),
        ("thua_tuan", w_bet, w_win, week_left, "Thua ròng"),
    ):
        value, amount = reward_calc(rtype, bet, win)
        cards.append(_reward_card(rtype, label, value, amount, left))

    pending = query("SELECT rtype, period, amount FROM rewards WHERE user_id=%s AND claimed=0 AND amount>0 "
                    "ORDER BY id", (uid,)) or []
    text = (
        f'{ce("🎁")} <b>TRUNG TÂM NHẬN THƯỞNG</b>\n'
        f'<i>Theo dõi tiến độ và khoản thưởng dự kiến của bạn</i>\n\n'
        + "\n\n".join(cards) + "\n\n"
    )
    kb = None
    if pending:
        total = sum(int(p[2]) for p in pending)
        text += f'{ce("🎉")} <b>THƯỞNG ĐÃ CHỐT - CHỜ NHẬN</b>\n'
        for rtype, period, amount in pending[:10]:
            text += f'• {RTYPE_LABEL[rtype][0].capitalize()} ({fmt_period(rtype, period)}): <code>+{fmt_money(int(amount))}đ</code>\n'
        if len(pending) > 10:
            text += f'• ... và {len(pending) - 10} khoản khác\n'
        text += "\n"
        kb = InlineKeyboardMarkup([[btn(f"Nhận thưởng +{fmt_money(total)}đ", "🎉", callback_data="rw_claim")]])
    text += (
        f'{ce("📌")} Ngày chốt lúc <b>23:59</b>. Tuần chung toàn hệ thống: <b>Thứ Hai 00:00 — Chủ Nhật 23:59</b>.\n'
        f'{ce("💡")} Khi có khoản thưởng đã chốt, nút <b>Nhận thưởng</b> sẽ tự động xuất hiện bên dưới.\n'
        f'{ce("📜")} Số liệu chỉ tính các giao dịch và cược hợp lệ đã hoàn tất.'
    )
    return text, kb

async def claim_rewards(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    rows = query(
        "UPDATE rewards SET claimed=1, claimed_at=%s WHERE user_id=%s AND claimed=0 AND amount>0 "
        "RETURNING rtype, period, amount", (get_vietnam_datetime_db(), uid))
    if not rows:
        return await safe_answer(q, "Hiện chưa có khoản thưởng nào đã chốt để nhận!", True)
    total = sum(int(r[2]) for r in rows)
    add_money(uid, total, "Nhận thưởng hoàn trả")
    await safe_answer(q)
    lines = "\n".join(
        f'• {RTYPE_LABEL[r[0]][0].capitalize()} ({fmt_period(r[0], r[1])}): <code>+{fmt_money(int(r[2]))}đ</code>'
        for r in rows)
    text = (
        f'{ce("🎉")} <b>NHẬN THƯỞNG THÀNH CÔNG!</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n{lines}\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("💰")} Tổng nhận: <code>+{fmt_money(total)}đ</code>\n'
        f'{ce("💎")} Số dư hiện tại: <code>{fmt_money(get_balance(uid))}đ</code>'
    )
    try:
        await q.message.edit_text(text, parse_mode=ParseMode.HTML)
    except Exception:
        await q.message.reply_text(text, parse_mode=ParseMode.HTML)

def event_screen(uid, kind):
    """Màn hình EVENT (hoàn cược / hoàn thua) với số liệu thật."""
    today = get_vietnam_time().date()
    ws = week_start(today)
    is_day = kind.endswith("ngay")
    bet, win = period_stats(uid, today, today) if is_day else period_stats(uid, ws, ws + timedelta(days=6))
    rtype = {"hc_ngay": "cuoc_ngay", "hc_tuan": "cuoc_tuan", "ht_ngay": "thua_ngay", "ht_tuan": "thua_tuan"}[kind]
    value, amount = reward_calc(rtype, bet, win)
    when = "ngày" if is_day else "tuần"
    notice = (f'{ce("📌")} Chỉ tính cược đã có kết quả. Cược đang chờ, bị hủy hoặc được hoàn tiền không tính vào doanh số.\n'
              if kind.startswith("hc") else
              f'{ce("📌")} Nếu kết quả nhỏ hơn hoặc bằng 0 thì không phát sinh hoàn thua.\n')
    if kind.startswith("hc"):
        pct = get_rebate_pct("ngay" if is_day else "tuan")
        title = f'{ce("📈" if is_day else "📉")} <b>HOÀN CƯỢC {when.upper()}</b>\n<i>(Hoàn {fmt_pct(pct)}% tổng cược {when})</i>\n'
        body = (f'{ce("💰")} <b>Mốc tối thiểu:</b> doanh số từ {fmt_money(MIN_REWARD_BASE)}đ\n'
                f'{ce("💰")} <b>Tỉ lệ hoàn:</b> {fmt_pct(pct)}% tổng cược {when}\n')
        label = "Kỳ hôm nay" if is_day else "Kỳ tuần này"
    else:
        tiers = LOSS_TIERS_DAY if is_day else LOSS_TIERS_WEEK
        names = {1_000_000_000: "Mốc 1 Tỷ trở lên", 100_000_000: "Mốc 100M - dưới 1 Tỷ",
                 10_000_000: "Mốc 10M - dưới 100M", 1_000_000: "Mốc 1M - dưới 10M", 100_000: "Mốc 100K - dưới 1M"}
        title = (f'{ce("💸")} <b>HOÀN THUA {when.upper()}</b>\n'
                 f'<i>(Thua ròng = Tổng cược - Tổng tiền thắng trong {when})</i>\n')
        body = "".join(f'{ce("💰")} <b>{names[t]}:</b> Hoàn {fmt_pct(p)}%\n' for t, p in reversed(tiers))
        label = "Kỳ hôm nay" if is_day else "Kỳ tuần này"
    text = (
        f'{title}━━━━━━━━━━━━━━━━━━━━━\n{body}━━━━━━━━━━━━━━━━━━━━━\n{notice}'
        f'{ce("⏰")} Số liệu chốt {"23:59 mỗi ngày" if is_day else "Chủ Nhật 23:59"}, thưởng tự động có tại <b>Tài khoản → Nhận thưởng</b>.\n\n'
        f'{ce("📊")} {label}: <code>{fmt_money(value)}</code>\n'
        f'{ce("🎁")} Dự kiến hoàn: <code>{fmt_money(amount)}</code>'
    )
    kb = InlineKeyboardMarkup([[btn("Nhận Thưởng", "🎁", callback_data=f"ev_nhan_{kind}")]])
    return text, kb

# ---------- CHỐT THƯỞNG TỰ ĐỘNG ----------
def _insert_reward(uid, rtype, period, base, amount):
    if amount <= 0:
        return False
    r = query(
        "INSERT INTO rewards(user_id, rtype, period, base, amount, claimed, created_at) "
        "VALUES(%s,%s,%s,%s,%s,0,%s) ON CONFLICT (user_id, rtype, period) DO NOTHING RETURNING id",
        (uid, rtype, period, base, amount, get_vietnam_datetime_db()))
    return bool(r)

def settle_day_sync(day):
    """Chốt thưởng cho ngày `day`; nếu là Chủ Nhật thì chốt luôn tuần. Trả về {uid: [(rtype, period, amount)]}."""
    created = {}

    def _add(uid_, rtype, period, base, amount):
        if _insert_reward(uid_, rtype, period, base, amount):
            created.setdefault(uid_, []).append((rtype, period, amount))

    rows = query("SELECT user_id, bet, win FROM bet_daily WHERE day=%s", (day,)) or []
    for uid_, bet, win in rows:
        for rtype in ("cuoc_ngay", "thua_ngay"):
            base, amount = reward_calc(rtype, int(bet or 0), int(win or 0))
            _add(uid_, rtype, day.isoformat(), base, amount)

    if day.weekday() == 6:  # Chủ Nhật -> tổng kết tuần
        ws = week_start(day)
        wrows = query("SELECT user_id, SUM(bet), SUM(win) FROM bet_daily WHERE day BETWEEN %s AND %s GROUP BY user_id",
                      (ws, day)) or []
        for uid_, bet, win in wrows:
            for rtype in ("cuoc_tuan", "thua_tuan"):
                base, amount = reward_calc(rtype, int(bet or 0), int(win or 0))
                _add(uid_, rtype, ws.isoformat(), base, amount)
    return created

async def settle_due(bot):
    today = get_vietnam_time().date()
    yesterday = today - timedelta(days=1)
    last = get_setting('rw_last_day')
    if last == yesterday.isoformat():
        return
    try:
        last_d = datetime.strptime(last, "%Y-%m-%d").date() if last else yesterday - timedelta(days=1)
    except Exception:
        last_d = yesterday - timedelta(days=1)
    if (yesterday - last_d).days > 8:
        last_d = yesterday - timedelta(days=8)
    d = last_d + timedelta(days=1)
    while d <= yesterday:
        created = await asyncio.to_thread(settle_day_sync, d)
        set_setting('rw_last_day', d.isoformat())
        print(f"✅ Đã chốt thưởng ngày {d.isoformat()}: {len(created)} người")
        for uid_, items in created.items():
            total = sum(i[2] for i in items)
            lines = "\n".join(f'• {RTYPE_LABEL[i[0]][0].capitalize()} ({fmt_period(i[0], i[1])}): <code>+{fmt_money(i[2])}đ</code>' for i in items)
            kb = InlineKeyboardMarkup([[btn(f"Nhận thưởng +{fmt_money(total)}đ", "🎉", callback_data="rw_claim")]])
            try:
                await bot.send_message(
                    uid_,
                    f'{ce("🎁")} <b>THƯỞNG ĐÃ CHỐT!</b>\n━━━━━━━━━━━━━━━━━━━━━\n{lines}\n━━━━━━━━━━━━━━━━━━━━━\n'
                    f'{ce("💰")} Tổng: <code>+{fmt_money(total)}đ</code>\nBấm nút bên dưới để nhận thưởng.',
                    reply_markup=kb, parse_mode=ParseMode.HTML)
            except Exception:
                pass
            await asyncio.sleep(0.05)
        d += timedelta(days=1)

async def reward_settle_loop(bot):
    while True:
        try:
            await settle_due(bot)
        except Exception as e:
            print(f"Lỗi chốt thưởng: {e}")
            traceback.print_exc()
        await asyncio.sleep(60)

@admin_only
async def sethoancuoc_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args or []
    if len(args) < 2 or args[0].lower() not in ("ngay", "tuan"):
        return await update.effective_message.reply_text(
            f'{ce("📌")} <b>Hoàn cược hiện tại:</b> ngày <code>{fmt_pct(get_rebate_pct("ngay"))}%</code> | '
            f'tuần <code>{fmt_pct(get_rebate_pct("tuan"))}%</code>\n'
            f'Đổi: <code>/sethoancuoc ngay 2</code> hoặc <code>/sethoancuoc tuan 2</code>',
            parse_mode=ParseMode.HTML)
    try:
        pct = float(args[1].replace(",", "."))
        if pct < 0 or pct > 100:
            raise ValueError
    except ValueError:
        return await update.effective_message.reply_text(f'{ce("❌")} Tỉ lệ % không hợp lệ!', parse_mode=ParseMode.HTML)
    set_setting(f"rebate_{args[0].lower()}_pct", pct)
    await update.effective_message.reply_text(
        f'{ce("✅")} Đã đặt hoàn cược {args[0].lower()} = <code>{fmt_pct(pct)}%</code>', parse_mode=ParseMode.HTML)

# ============================================================
# ===== [MỚI] GIFTCODE 5 LOẠI ================================
# ============================================================
GIFT_TYPES = {
    "TANTHU":  {"name": "Code Tân Thủ",  "icon": "🎁", "fmt": "JAV88-TANTHU-xxxxxxx"},
    "CODEMUA": {"name": "Code Mua",      "icon": "🛒", "fmt": "JAV88-CODEMUA-xxxxxxx"},
    "GIOVANG": {"name": "Code Giờ Vàng", "icon": "⏰", "fmt": "JAV88-GIOVANG-xxxxxxx"},
    "NAP":     {"name": "Code Nạp",      "icon": "💳", "fmt": "JAV88-1234567-ABCDEFG"},
    "TRIAN":   {"name": "Code Tri Ân",   "icon": "🎉", "fmt": "JAV88-TRIAN-xxxxxxx"},
}
GIFT_BUY_EXPIRE_DAYS = 30
_DIGITS = "0123456789"
_LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_ALNUM = _LETTERS + _DIGITS

def _rand(chars, n):
    return ''.join(random.choice(chars) for _ in range(n))

def gen_gift_code(ctype):
    while True:
        if ctype == "NAP":
            code = f"JAV88-{_rand(_DIGITS, 7)}-{_rand(_LETTERS, 7)}"
        else:
            code = f"JAV88-{ctype}-{_rand(_ALNUM, 7)}"
        if not query("SELECT 1 FROM giftcodes WHERE code=%s", (code,)):
            return code

def add_wager_requirement(uid, bonus_amount, required_bet):
    """Cộng dồn yêu cầu cược (không ghi đè yêu cầu cũ chưa hoàn thành)."""
    ex = query("SELECT required_bet FROM user_bonus WHERE user_id=%s", (uid,))
    if ex and (ex[0][0] or 0) > 0:
        query("UPDATE user_bonus SET bonus_amount=bonus_amount+%s, required_bet=required_bet+%s WHERE user_id=%s",
              (bonus_amount, required_bet, uid))
    else:
        query("DELETE FROM user_bonus WHERE user_id=%s", (uid,))
        query("INSERT INTO user_bonus (user_id, bonus_amount, required_bet, current_bet, created_at) VALUES (%s,%s,%s,0,%s)",
              (uid, bonus_amount, required_bet, get_vietnam_datetime_db()))

async def redeem_giftcode(update: Update, uid: int, code_str: str) -> bool:
    """Nhập giftcode loại mới. Trả về True nếu mã thuộc hệ thống giftcode mới (đã xử lý xong)."""
    msg = update.effective_message
    row = query("SELECT ctype, reward, wager, expiry, require_deposit, required_amount, bound_user, used "
                "FROM giftcodes WHERE code=%s", (code_str,))
    if not row:
        return False
    ctype, reward, wager, expiry, require_deposit, required_amount, bound_user, used = row[0]
    gname = GIFT_TYPES.get(ctype, {}).get("name", "Giftcode")

    if bound_user and int(bound_user) != uid:
        await msg.reply_text(f'{ce("❌")} Mã quà tặng không tồn tại hoặc không dành cho tài khoản của bạn.', parse_mode=ParseMode.HTML)
        return True
    if used:
        await msg.reply_text(f'{ce("❌")} Mã này đã được sử dụng!', parse_mode=ParseMode.HTML)
        return True
    if expiry and get_vietnam_time() > expiry:
        await msg.reply_text(f'{ce("❌")} Mã này đã hết hạn sử dụng!', parse_mode=ParseMode.HTML)
        return True

    if require_deposit:
        dep = deposited_today(uid)
        if dep < (required_amount or 0):
            await msg.reply_text(
                f'{ce("⚠️")} <b>CHƯA ĐỦ ĐIỀU KIỆN NHẬP CODE!</b>\n'
                f'━━━━━━━━━━━━━━━━━━━━━\n'
                f'{ce("🔑")} Mã: <code>{code_str}</code>\n'
                f'{ce("💰")} Giá trị code: <code>{fmt_money(int(reward))}đ</code>\n'
                f'{ce("💳")} Cần nạp trong ngày: <code>{fmt_money(int(required_amount))}đ</code>\n'
                f'{ce("📥")} Hôm nay bạn đã nạp: <code>{fmt_money(dep)}đ</code>\n'
                f'{ce("📌")} Còn thiếu: <code>{fmt_money(int(required_amount) - dep)}đ</code>\n'
                f'━━━━━━━━━━━━━━━━━━━━━\n'
                f'Nạp đủ số tiền trên trong hôm nay rồi nhập lại mã nhé!',
                parse_mode=ParseMode.HTML)
            return True

    claimed = query("UPDATE giftcodes SET used=1, used_by=%s, used_at=%s WHERE code=%s AND used=0 RETURNING code",
                    (uid, get_vietnam_datetime_db(), code_str))
    if not claimed:
        await msg.reply_text(f'{ce("❌")} Mã này đã được sử dụng!', parse_mode=ParseMode.HTML)
        return True

    reward = int(reward)
    wager = int(wager or 0)
    add_money(uid, reward, f"Giftcode {gname}: {code_str}")
    required_bet = reward * wager
    if required_bet > 0:
        add_wager_requirement(uid, reward, required_bet)
    await msg.reply_text(
        f'{ce("🎉")} <b>NHẬN CODE THÀNH CÔNG!</b> {ce("🎉")}\n'
        f'┏━━━━━━━━━━━━━━━━━━━━━━━━━\n'
        f'┃ {ce("🔑")} <b>Loại:</b> {gname}\n'
        f'┃ {ce("🔑")} <b>Mã code:</b> <code>{code_str}</code>\n'
        f'┃ {ce("💰")} <b>Đã nhận:</b> <code>+{fmt_money(reward)}đ</code>\n'
        f'┃ {ce("🎯")} <b>Vòng cược yêu cầu:</b> <code>x{wager}</code>\n'
        f'┃ {ce("📊")} <b>Tổng cược cần:</b> <code>{fmt_money(required_bet)}đ</code>\n'
        f'┗━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'
        f'{ce("💰")} Số dư hiện tại: <code>{fmt_money(get_balance(uid))}đ</code>',
        parse_mode=ParseMode.HTML)
    return True

# ---------- MUA GIFTCODE (tự động, không cần admin duyệt) ----------
async def mua_gift_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg_obj = update.effective_message
    uid = update.effective_user.id
    if is_banned(uid):
        return
    args = ctx.args or []
    usage = (
        f'{ce("🛒")} <b>Mua giftcode theo cú pháp:</b>\n'
        f'<code>/muagift [số lượng] [giá trị mỗi code]</code>\n'
        f'VD: <code>/muagift 5 20000</code> hoặc <code>/muagift 3 5000</code>\n\n'
        f'{ce("⚠️")} Phí 5%. Mệnh giá mỗi code tối thiểu 1.000đ. Cần tổng nạp >50k.\n'
        f'{ce("🎯")} Code mua chỉ cần cược <b>x1</b> vòng. Code được gửi ngay sau khi mua.'
    )
    if len(args) < 2:
        return await msg_obj.reply_text(usage, parse_mode=ParseMode.HTML)
    try:
        qty = int(args[0])
        value = int(args[1].replace(",", "").replace(".", ""))
    except ValueError:
        return await msg_obj.reply_text(f'{ce("❌")} Số lượng hoặc giá trị không hợp lệ!\n\n' + usage, parse_mode=ParseMode.HTML)
    if qty < 1 or qty > 20:
        return await msg_obj.reply_text(f'{ce("❌")} Mỗi lần chỉ mua từ 1 đến 20 code!', parse_mode=ParseMode.HTML)
    if value < 1000 or value > 10_000_000:
        return await msg_obj.reply_text(f'{ce("❌")} Mệnh giá mỗi code từ 1.000đ đến 10.000.000đ!', parse_mode=ParseMode.HTML)
    if total_deposited(uid) <= 50000:
        return await msg_obj.reply_text(f'{ce("⚠️")} Bạn cần có tổng nạp trên <b>50.000đ</b> mới được mua giftcode!', parse_mode=ParseMode.HTML)

    cost = qty * value
    fee = int(cost * 0.05)
    total = cost + fee
    if get_balance(uid) < total:
        return await msg_obj.reply_text(
            f'{ce("❌")} Số dư không đủ! Cần <code>{fmt_money(total)}đ</code> (gồm phí 5% = {fmt_money(fee)}đ).',
            parse_mode=ParseMode.HTML)
    if not sub_money(uid, total, f"Mua giftcode {qty} code x {fmt_money(value)}đ"):
        return await msg_obj.reply_text(f'{ce("❌")} Số dư không đủ!', parse_mode=ParseMode.HTML)

    expiry = get_vietnam_time() + timedelta(days=GIFT_BUY_EXPIRE_DAYS)
    codes = []
    try:
        for _ in range(qty):
            code = gen_gift_code("CODEMUA")
            query("INSERT INTO giftcodes (code, ctype, reward, wager, expiry, require_deposit, required_amount, "
                  "bound_user, used, created_by, created_at) VALUES (%s,'CODEMUA',%s,1,%s,0,0,NULL,0,%s,%s)",
                  (code, value, expiry, uid, get_vietnam_datetime_db()))
            codes.append(code)
    except Exception as e:
        print(f"Lỗi tạo CODEMUA: {e}")
    if len(codes) < qty:  # hoàn tiền phần chưa tạo được
        miss = qty - len(codes)
        refund = miss * value + int(miss * value * 0.05)
        add_money(uid, refund, "Hoàn tiền mua giftcode lỗi")
    if not codes:
        return await msg_obj.reply_text(f'{ce("❌")} Lỗi hệ thống, đã hoàn tiền. Vui lòng thử lại!', parse_mode=ParseMode.HTML)

    code_lines = "\n".join(f'{i}. <code>{c}</code>' for i, c in enumerate(codes, 1))
    await msg_obj.reply_text(
        f'{ce("✅")} <b>MUA GIFTCODE THÀNH CÔNG!</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("🛒")} Số lượng: <code>{len(codes)}</code>\n'
        f'{ce("💰")} Giá trị mỗi code: <code>{fmt_money(value)}đ</code>\n'
        f'{ce("💳")} Phí 5%: <code>{fmt_money(int(len(codes) * value * 0.05))}đ</code>\n'
        f'{ce("🎯")} Vòng cược khi nhập: <code>x1</code>\n'
        f'{ce("⏰")} Hạn dùng: <code>{GIFT_BUY_EXPIRE_DAYS} ngày</code>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("🔑")} <b>Danh sách code:</b>\n{code_lines}\n\n'
        f'{ce("📌")} Nhập code bằng lệnh <code>/code [mã]</code> hoặc gửi thẳng mã cho bot.\n'
        f'{ce("💰")} Số dư hiện tại: <code>{fmt_money(get_balance(uid))}đ</code>',
        parse_mode=ParseMode.HTML)

# ---------- ADMIN: TẠO GIFTCODE NHIỀU LOẠI ----------
def parse_money_text(s):
    s = s.lower().replace(",", "").replace(".", "").replace("đ", "").replace(" ", "")
    mult = 1
    if s.endswith("k"):
        mult, s = 1000, s[:-1]
    elif s.endswith("m"):
        mult, s = 1_000_000, s[:-1]
    return int(s) * mult

def gift_summary(st):
    t = GIFT_TYPES[st["ctype"]]
    lines = [f'{ce("🔑")} Loại: <b>{t["name"]}</b> <code>({t["fmt"]})</code>']
    if "require_deposit" in st:
        if st["require_deposit"]:
            lines.append(f'{ce("💳")} Yêu cầu nạp trong ngày: <b>{fmt_money(st.get("required_amount", 0))}đ</b>' if "required_amount" in st
                         else f'{ce("💳")} Yêu cầu nạp: <b>Có</b>')
        else:
            lines.append(f'{ce("💳")} Yêu cầu nạp: <b>Không</b>')
    if "wager" in st:
        lines.append(f'{ce("🎯")} Vòng cược: <b>x{st["wager"]}</b>')
    if "reward" in st:
        lines.append(f'{ce("💰")} Giá trị: <b>{fmt_money(st["reward"])}đ</b>')
    if "duration" in st:
        lines.append(f'{ce("⏰")} Hạn dùng: <b>{fmt_duration(st["duration"])}</b>')
    if "qty" in st:
        lines.append(f'{ce("📦")} Số lượng: <b>{st["qty"]}</b>')
    return "\n".join(lines)

def _cancel_kb(extra_rows=None):
    rows = list(extra_rows or [])
    rows.append([btn("Hủy", "❌", callback_data="gcn_cancel")])
    return InlineKeyboardMarkup(rows)

@admin_only
async def gift_flow_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    pending_inputs.pop(uid, None)
    rows = []
    for key, t in GIFT_TYPES.items():
        rows.append([btn(f'{t["name"]} ({t["fmt"]})', t["icon"], callback_data=f"gcn_type_{key}")])
    await update.effective_message.reply_text(
        f'{ce("🎁")} <b>TẠO GIFTCODE</b>\n━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("✍️")} Chọn <b>loại code</b> cần tạo:',
        reply_markup=_cancel_kb(rows), parse_mode=ParseMode.HTML)

async def handle_gift_flow_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE, d: str):
    q = update.callback_query
    uid = q.from_user.id
    if uid not in ADMIN_IDS:
        return await safe_answer(q, "❌ Không có quyền!", True)
    await safe_answer(q)

    async def _edit(text, kb=None):
        try:
            await q.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception:
            await q.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

    if d == "gcn_cancel":
        pending_inputs.pop(uid, None)
        return await _edit(f'{ce("🚫")} Đã hủy tạo giftcode.')

    if d.startswith("gcn_type_"):
        ctype = d[len("gcn_type_"):]
        if ctype not in GIFT_TYPES:
            return
        st = {"flow": "gift", "step": "ask_req", "ctype": ctype}
        pending_inputs[uid] = st
        kb = _cancel_kb([[btn("Có yêu cầu nạp", "💳", callback_data="gcn_req_1"),
                          btn("Không yêu cầu", "🚫", callback_data="gcn_req_0")]])
        return await _edit(
            f'{ce("🎁")} <b>TẠO GIFTCODE</b>\n━━━━━━━━━━━━━━━━━━━━━\n{gift_summary(st)}\n━━━━━━━━━━━━━━━━━━━━━\n'
            f'{ce("✍️")} Người dùng có cần <b>nạp tiền trong ngày</b> mới được nhập code không?', kb)

    st = pending_inputs.get(uid)
    if not st or st.get("flow") != "gift":
        return await q.message.reply_text(f'{ce("⚠️")} Phiên tạo code đã hết hạn, hãy gõ /taogift để tạo lại.', parse_mode=ParseMode.HTML)

    if d in ("gcn_req_1", "gcn_req_0") and st["step"] == "ask_req":
        st["require_deposit"] = 1 if d == "gcn_req_1" else 0
        if st["require_deposit"]:
            st["step"] = "req_amount"
            return await _edit(
                f'{ce("🎁")} <b>TẠO GIFTCODE</b>\n━━━━━━━━━━━━━━━━━━━━━\n{gift_summary(st)}\n━━━━━━━━━━━━━━━━━━━━━\n'
                f'{ce("✍️")} Nhập <b>số tiền phải nạp trong ngày</b> để được nhập code:\nVD: <code>50000</code> hoặc <code>50k</code>\n'
                f'<i>(Gõ "huy" để hủy)</i>')
        st["step"] = "wager"
        return await _edit(
            f'{ce("🎁")} <b>TẠO GIFTCODE</b>\n━━━━━━━━━━━━━━━━━━━━━\n{gift_summary(st)}\n━━━━━━━━━━━━━━━━━━━━━\n'
            f'{ce("✍️")} Nhập <b>số vòng cược</b> của code:\nVD: <code>2</code> (x2 vòng cược)\n<i>(Gõ "huy" để hủy)</i>')

    if d in ("gcn_bind_0", "gcn_bind_1") and st["step"] == "ask_bind":
        if d == "gcn_bind_0":
            st["bound_user"] = None
            return await _finalize_gift(q.message, uid, st)
        st["step"] = "bind_id"
        return await _edit(
            f'{ce("🎁")} <b>TẠO GIFTCODE</b>\n━━━━━━━━━━━━━━━━━━━━━\n{gift_summary(st)}\n━━━━━━━━━━━━━━━━━━━━━\n'
            f'{ce("✍️")} Nhập <b>ID tài khoản</b> được phép nhập code:\n<i>(Gõ "huy" để hủy)</i>')

def _create_gift_codes(st, admin_id):
    expiry = get_vietnam_time() + timedelta(minutes=st["duration"])
    codes = []
    for _ in range(st["qty"]):
        code = gen_gift_code(st["ctype"])
        query("INSERT INTO giftcodes (code, ctype, reward, wager, expiry, require_deposit, required_amount, "
              "bound_user, used, created_by, created_at) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,0,%s,%s)",
              (code, st["ctype"], st["reward"], st["wager"], expiry, st.get("require_deposit", 0),
               st.get("required_amount", 0), st.get("bound_user"), admin_id, get_vietnam_datetime_db()))
        codes.append(code)
    return codes, expiry

async def _finalize_gift(message, uid, st):
    pending_inputs.pop(uid, None)
    try:
        codes, expiry = await asyncio.to_thread(_create_gift_codes, st, uid)
    except Exception as e:
        print(f"Lỗi tạo giftcode: {e}")
        return await message.reply_text(f'{ce("❌")} Lỗi khi tạo code, vui lòng thử lại!', parse_mode=ParseMode.HTML)
    t = GIFT_TYPES[st["ctype"]]
    bound = st.get("bound_user")
    head = (
        f'{ce("🎉")} <b>TẠO {len(codes)} {t["name"].upper()} THÀNH CÔNG!</b> {ce("🎉")}\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("💰")} <b>Giá trị mỗi code:</b> <code>{fmt_money(st["reward"])}đ</code>\n'
        f'{ce("🎯")} <b>Vòng cược:</b> <code>x{st["wager"]}</code>\n'
        f'{ce("⏰")} <b>Hạn dùng:</b> <code>{fmt_duration(st["duration"])}</code> <i>(đến {expiry.strftime("%d/%m/%Y %H:%M")})</i>\n'
        + (f'{ce("💳")} <b>Yêu cầu nạp trong ngày:</b> <code>{fmt_money(st["required_amount"])}đ</code>\n' if st.get("require_deposit")
           else f'{ce("💳")} <b>Yêu cầu nạp:</b> Không\n')
        + (f'{ce("🔒")} <b>Chỉ tài khoản:</b> <code>{bound}</code>\n' if bound else f'{ce("🔓")} <b>Tài khoản nhập:</b> Tất cả\n')
        + '━━━━━━━━━━━━━━━━━━━━━\n'
    )
    body = "\n".join(f'{i}. <code>{c}</code>' for i, c in enumerate(codes, 1))
    full = head + f'{ce("🔑")} <b>Danh sách code:</b>\n{body}\n\n{ce("📌")} Nhập bằng <code>/code [mã]</code> hoặc gửi thẳng mã cho bot.'
    if len(full) > 3900:
        bio = BytesIO("\n".join(codes).encode("utf-8"))
        bio.name = f"giftcode_{st['ctype']}.txt"
        await message.reply_text(head + f'{ce("📎")} Danh sách {len(codes)} code ở file đính kèm.', parse_mode=ParseMode.HTML)
        await message.reply_document(document=bio)
    else:
        await message.reply_text(full, parse_mode=ParseMode.HTML)

async def handle_gift_flow_text(update: Update, uid: int, st: dict, text: str):
    msg = update.effective_message
    if text.lower() in ("huy", "hủy", "cancel"):
        pending_inputs.pop(uid, None)
        await msg.reply_text(f'{ce("🚫")} Đã hủy tạo giftcode.', parse_mode=ParseMode.HTML)
        return True
    step = st.get("step")

    async def _err(t):
        await msg.reply_text(f'{ce("❌")} {t}', parse_mode=ParseMode.HTML)
        return True

    async def _ask(t, kb=None):
        await msg.reply_text(
            f'{ce("🎁")} <b>TẠO GIFTCODE</b>\n━━━━━━━━━━━━━━━━━━━━━\n{gift_summary(st)}\n━━━━━━━━━━━━━━━━━━━━━\n{t}',
            reply_markup=kb, parse_mode=ParseMode.HTML)
        return True

    if step in ("ask_req", "ask_bind"):
        return await _err('Vui lòng bấm nút ở tin nhắn phía trên, hoặc gõ <code>huy</code> để hủy.')

    if step == "req_amount":
        try:
            val = parse_money_text(text)
        except ValueError:
            return await _err('Số tiền không hợp lệ! VD: <code>50000</code> hoặc <code>50k</code>')
        if val < 1000:
            return await _err('Số tiền nạp tối thiểu là 1.000đ. Nhập lại:')
        st["required_amount"] = val
        st["step"] = "wager"
        return await _ask(f'{ce("✍️")} Nhập <b>số vòng cược</b> của code:\nVD: <code>2</code> (x2 vòng cược)\n<i>(Gõ "huy" để hủy)</i>')

    if step == "wager":
        try:
            wager = int(text.lower().replace("x", "").strip())
        except ValueError:
            return await _err('Vui lòng nhập số hợp lệ! VD: <code>2</code>')
        if wager < 0 or wager > 100:
            return await _err('Số vòng cược từ 0 đến 100. Nhập lại:')
        st["wager"] = wager
        st["step"] = "reward"
        return await _ask(f'{ce("✍️")} Nhập <b>giá trị code</b> (VNĐ):\nVD: <code>50000</code> hoặc <code>50k</code>')

    if step == "reward":
        try:
            val = parse_money_text(text)
        except ValueError:
            return await _err('Giá trị không hợp lệ! VD: <code>50000</code> hoặc <code>50k</code>')
        if val < 1000:
            return await _err('Giá trị tối thiểu là 1.000đ. Nhập lại:')
        st["reward"] = val
        st["step"] = "duration"
        return await _ask(
            f'{ce("✍️")} Nhập <b>hạn sử dụng</b> của code:\n• <code>1n</code> = 1 ngày\n• <code>1h</code> = 1 tiếng\n• <code>1p</code> = 1 phút\nVD: <code>7n</code>')

    if step == "duration":
        minutes = parse_duration(text)
        if not minutes or minutes <= 0:
            return await _err('Định dạng không hợp lệ! Nhập <code>1n</code> (ngày), <code>1h</code> (giờ) hoặc <code>1p</code> (phút).')
        st["duration"] = minutes
        st["step"] = "qty"
        return await _ask(f'{ce("✍️")} Nhập <b>số lượng code</b> cần tạo (1 - 100):')

    if step == "qty":
        try:
            qty = int(text.strip())
        except ValueError:
            return await _err('Vui lòng nhập số hợp lệ!')
        if qty < 1 or qty > 100:
            return await _err('Số lượng từ 1 đến 100. Nhập lại:')
        st["qty"] = qty
        st["step"] = "ask_bind"
        kb = _cancel_kb([[btn("Tất cả tài khoản", "🔓", callback_data="gcn_bind_0"),
                          btn("Chỉ định tài khoản", "🔒", callback_data="gcn_bind_1")]])
        return await _ask(f'{ce("✍️")} Code này cho <b>tất cả tài khoản</b> nhập hay <b>chỉ định 1 tài khoản</b>?', kb)

    if step == "bind_id":
        try:
            target = int(text.strip())
        except ValueError:
            return await _err('ID không hợp lệ! Nhập số ID Telegram của tài khoản.')
        if not query("SELECT 1 FROM users WHERE user_id=%s", (target,)):
            return await _err('ID này chưa từng dùng bot. Nhập lại ID khác:')
        st["bound_user"] = target
        await _finalize_gift(msg, uid, st)
        return True

    pending_inputs.pop(uid, None)
    return False

async def handle_pending_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    st = pending_inputs.get(uid)
    if not st:
        return False
    text = (update.effective_message.text or "").strip()
    if st.get("flow") == "gift":
        return await handle_gift_flow_text(update, uid, st, text)
    pending_inputs.pop(uid, None)
    return False

@admin_only
async def xoagift_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        return await update.effective_message.reply_text(f'{ce("❌")} <b>Cú pháp:</b> <code>/xoagift [mã]</code>', parse_mode=ParseMode.HTML)
    code_str = ctx.args[0].strip().upper()
    r = query("DELETE FROM giftcodes WHERE code=%s RETURNING reward", (code_str,))
    if not r:
        return await update.effective_message.reply_text(f'{ce("❌")} Code <code>{code_str}</code> không tồn tại!', parse_mode=ParseMode.HTML)
    await update.effective_message.reply_text(f'{ce("✅")} Đã xóa code <code>{code_str}</code> ({fmt_money(int(r[0][0]))}đ)', parse_mode=ParseMode.HTML)

@admin_only
async def dsgift_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    rows = query("SELECT code, ctype, reward, wager, used, bound_user, expiry FROM giftcodes ORDER BY expiry DESC LIMIT 30") or []
    if not rows:
        return await update.effective_message.reply_text(f'{ce("📌")} Chưa có giftcode nào.', parse_mode=ParseMode.HTML)
    lines = []
    for code, ctype, reward, wager, used, bound, expiry in rows:
        st = "đã dùng" if used else ("hết hạn" if expiry and get_vietnam_time() > expiry else "còn")
        extra = f" | ID {bound}" if bound else ""
        lines.append(f'<code>{code}</code> | {fmt_money(int(reward))}đ x{wager} | {st}{extra}')
    await update.effective_message.reply_text(f'{ce("🎁")} <b>30 GIFTCODE GẦN NHẤT</b>\n\n' + "\n".join(lines), parse_mode=ParseMode.HTML)

backfill_bet_daily()

async def track_interaction(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        return
    uid = update.effective_user.id
    gid = update.effective_chat.id
    today = get_vietnam_date()
    now_str = get_vietnam_datetime_db()
    query("""
        INSERT INTO group_interactions (user_id, group_id, interaction_count, last_interaction)
        VALUES (%s, %s, 1, %s)
        ON CONFLICT (user_id, group_id) DO UPDATE SET 
            interaction_count = group_interactions.interaction_count + 1,
            last_interaction = %s
    """, (uid, gid, now_str, now_str))
    query("""
        INSERT INTO daily_top_interactions (user_id, group_id, interaction_count, date)
        VALUES (%s, %s, 1, %s)
        ON CONFLICT (user_id, group_id, date) DO UPDATE SET 
            interaction_count = daily_top_interactions.interaction_count + 1
    """, (uid, gid, today))
    total = query("SELECT interaction_count FROM group_interactions WHERE user_id=%s AND group_id=%s", (uid, gid))
    if total and total[0][0] >= 200:
        rewarded = query("SELECT 1 FROM daily_top_interactions WHERE user_id=%s AND group_id=%s AND rewarded=1 AND interaction_count>=200", (uid, gid))
        if not rewarded:
            query("UPDATE group_interactions SET interaction_count = -200 WHERE user_id=%s AND group_id=%s", (uid, gid))
            try:
                await ctx.bot.send_message(uid,
                    f'{ce("🎉")} <b>CHÚC MỪNG!</b> {ce("🎉")}\n{ce("🔥")} Bạn đã đạt <b>200 lượt tương tác</b>!',
                    parse_mode=ParseMode.HTML)
            except Exception:
                pass
            query("UPDATE daily_top_interactions SET rewarded=1 WHERE user_id=%s AND group_id=%s", (uid, gid))

def get_jackpot():
    res = query("SELECT value FROM settings WHERE key='jackpot_amount'")
    if res:
        return int(res[0][0])
    query("INSERT INTO settings (key, value) VALUES ('jackpot_amount', '100000') ON CONFLICT (key) DO NOTHING")
    return 100000

def update_jackpot(amount):
    query("UPDATE settings SET value=%s WHERE key='jackpot_amount'", (str(amount),))

def get_result_code(res_tx, res_cl):
    tx_code = "T" if res_tx == "tai" else "X"
    cl_code = "C" if res_cl == "chan" else "L"
    return f"{tx_code}{cl_code}"

def get_result_icons(res_tx, res_cl):
    tx_icon = "🔵" if res_tx == "tai" else "🔴"
    cl_icon = "⚪️" if res_cl == "chan" else "⚫️"
    return f"{tx_icon}{cl_icon}"

def get_full_result_text(res_tx, res_cl):
    tx_text = "TÀI" if res_tx == "tai" else "XỈU"
    cl_text = "CHẴN" if res_cl == "chan" else "LẺ"
    return f"{tx_text} {cl_text}"

FULL_PERMS = ChatPermissions(
    can_send_messages=True, can_send_audios=True, can_send_documents=True,
    can_send_photos=True, can_send_videos=True, can_send_video_notes=True,
    can_send_voice_notes=True, can_send_polls=True, can_send_other_messages=True,
    can_add_web_page_previews=True
)

async def run_dice_game_cycle(bot, group_id: int, chat_id: int):
    while True:
        try:
            if not room_betting_enabled.get(group_id, True):
                await asyncio.sleep(10)
                continue

            SESSION_COUNTER["value"] += 1
            session_id = SESSION_COUNTER["value"]

            game_state = {
                "status": "betting",
                "bets": {},
                "message_id": None,
                "session_id": session_id,
                "cycle_start": datetime.now()
            }
            group_games[group_id] = game_state

            jackpot_now = get_jackpot()

            start_text = (
                f'{ce("🎯")} <b>Xin mời đặt cược phiên XX #{session_id}</b> {ce("🎯")}\n'
                f'{ce("💰")} Min: 1.000 | Max: 1.000.000\n'
                f'{ce("🎮")} Cách chơi: [Cửa cược] [số tiền]\n'
                f'🔵 Tài: T | 🔴 Xỉu: X | ⚪ Chẵn: C | ⚫ Lẻ: L\n'
                f'{ce("👅")} Ẩn danh thường: TT/XX/CC/LL, VD TT 50000, XX 50000\n\n'
                f'{ce("🔥")} T/X/C/L trả x2.3: thua tổng khi 3 XX 9/10/11/12 điểm\n'
                f'{ce("👅")} Tất tay: VD T MAX hoặc T ALL <i>(Lưu ý: MAX là tất tay)</i>\n'
                f'{ce("🎰")} D1 [mặt] x5: đoán viên đầu, VD D1 4 20k\n'
                f'{ce("🎰")} D2 [2 mặt] x10: đoán viên 1 và 2 đúng thứ tự, VD D2 46 20k\n'
                f'{ce("🎰")} D3 [tổng]: 9/10/11/12 x7; 8/13 x9; 7/14 x12; 6/15 x15; 5/16 x18; 4/17 x25; 3/18 x30, VD: D3 13 20000 hoặc D3 13 max\n'
                f'{ce("💎")} Xiên TC/TL/XC/XL trả x3, VD: TC 50000, XC 50000,\n\n'
                f'{ce("✅")} <b>VD tổng hợp:</b> T 50000, X 50000, XX MAX, TT MAX hoặc TC max\n\n'
                f'{ce("🎁")} Hũ jackpot: <code>{fmt_money(jackpot_now)}đ</code>'
            )

            try:
                await bot.send_message(chat_id, start_text, parse_mode=ParseMode.HTML)
            except Exception as e:
                print(f"Lỗi gửi tin nhắn bắt đầu phiên: {e}")
                await asyncio.sleep(5)
                continue

            current_second = 60
            stats_msg_id = None

            while current_second > 0:
                await asyncio.sleep(10)
                current_second -= 10
                if current_second < 0:
                    current_second = 0

                tai_count = sum(b["amount"] for b in game_state['bets'].values() if b["choice"] == "tai")
                xiu_count = sum(b["amount"] for b in game_state['bets'].values() if b["choice"] == "xiu")
                chan_count = sum(b["amount"] for b in game_state['bets'].values() if b["choice"] == "chan")
                le_count = sum(b["amount"] for b in game_state['bets'].values() if b["choice"] == "le")
                tl_count = sum(b["amount"] for b in game_state['bets'].values() if b["choice"] == "tl")
                tc_count = sum(b["amount"] for b in game_state['bets'].values() if b["choice"] == "tc")
                xl_count = sum(b["amount"] for b in game_state['bets'].values() if b["choice"] == "xl")
                xc_count = sum(b["amount"] for b in game_state['bets'].values() if b["choice"] == "xc")

                d1_count = sum(b["amount"] for b in game_state['bets'].values() if b["choice"].startswith("d1_"))
                d2_count = sum(b["amount"] for b in game_state['bets'].values() if b["choice"].startswith("d2_"))
                d3_count = sum(b["amount"] for b in game_state['bets'].values() if b["choice"].startswith("d3_"))

                total_players = len(set(b["user_id"] for b in game_state['bets'].values()))

                header = f'{ce("🚫")} <b>SẮP ĐÓNG CƯỢC!</b>\n' if current_second <= 10 else ''

                stats_text = (
                    f'{header}'
                    f'{ce("⌛")} <b>Còn {current_second} giây phiên #{session_id}</b>\n'
                    f'🔵 <b>TÀI:</b> {fmt_money(tai_count)}\n'
                    f'🔴 <b>XỈU:</b> {fmt_money(xiu_count)}\n'
                    f'⚪ <b>CHẴN:</b> {fmt_money(chan_count)}\n'
                    f'⚫ <b>LẺ:</b> {fmt_money(le_count)}\n'
                )

                if tl_count > 0 or tc_count > 0 or xl_count > 0 or xc_count > 0:
                    stats_text += f'\n{ce("💎")} <b>Xiên:</b>\n'
                    if tl_count > 0: stats_text += f' - TL (Tài+Lẻ): {fmt_money(tl_count)}\n'
                    if tc_count > 0: stats_text += f' - TC (Tài+Chẵn): {fmt_money(tc_count)}\n'
                    if xl_count > 0: stats_text += f' - XL (Xỉu+Lẻ): {fmt_money(xl_count)}\n'
                    if xc_count > 0: stats_text += f' - XC (Xỉu+Chẵn): {fmt_money(xc_count)}\n'

                if d1_count > 0 or d2_count > 0 or d3_count > 0:
                    stats_text += f'\n{ce("🎰")} <b>Dự đoán:</b>\n'
                    if d1_count > 0: stats_text += f' - D1 (Mặt 1): {fmt_money(d1_count)}\n'
                    if d2_count > 0: stats_text += f' - D2 (2 Mặt): {fmt_money(d2_count)}\n'
                    if d3_count > 0: stats_text += f' - D3 (Tổng): {fmt_money(d3_count)}\n'

                stats_text += (
                    f'━━━━━━━━━━━━━━━━━━━━━\n'
                    f'{ce("👥")} Tổng người chơi: {total_players}\n'
                    f'{ce("🎁")} Hũ jackpot: {fmt_money(jackpot_now)}đ'
                )

                if stats_msg_id:
                    try:
                        await bot.delete_message(chat_id, stats_msg_id)
                    except Exception:
                        pass

                try:
                    new_stats_msg = await bot.send_message(chat_id, stats_text, parse_mode=ParseMode.HTML)
                    stats_msg_id = new_stats_msg.message_id
                except Exception as e:
                    print(f"Lỗi gửi thống kê: {e}")

            game_state["status"] = "rolling"

            if stats_msg_id:
                try:
                    await bot.delete_message(chat_id, stats_msg_id)
                except Exception:
                    pass

            try:
                await bot.set_chat_permissions(chat_id, ChatPermissions(can_send_messages=False))
            except Exception as e:
                print(f"Lỗi khóa chat: {e}")

            try:
                await bot.send_message(
                    chat_id=chat_id,
                    text=f'{ce("🔒")} <b>ĐÃ ĐÓNG CƯỢC PHIÊN #{session_id}!</b>\n{ce("⏰")} Đang lắc 3 xúc xắc...',
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                pass

            d1 = await bot.send_dice(chat_id, emoji="🎲")
            d2 = await bot.send_dice(chat_id, emoji="🎲")
            d3 = await bot.send_dice(chat_id, emoji="🎲")
            await asyncio.sleep(4)

            dice_values = [d1.dice.value, d2.dice.value, d3.dice.value]
            total = sum(dice_values)
            res_tx = "tai" if total >= 11 else "xiu"
            res_cl = "chan" if total % 2 == 0 else "le"
            result_code = get_result_code(res_tx, res_cl)
            result_icons = get_result_icons(res_tx, res_cl)
            result_text = get_full_result_text(res_tx, res_cl)
            dice_str = " ".join(map(str, dice_values))

            total_win = 0
            total_lose = 0

            for bet_key, bet in game_state["bets"].items():
                uid = bet["user_id"]
                amt = bet["amount"]
                choice = bet["choice"]

                is_win = False
                multiplier = 1.95

                if choice.startswith("d1_"):
                    target_face = int(choice.split("_")[1])
                    if dice_values[0] == target_face: is_win = True; multiplier = 5
                elif choice.startswith("d2_"):
                    target_faces = choice.split("_")[1]
                    if str(dice_values[0]) == target_faces[0] and str(dice_values[1]) == target_faces[1]:
                        is_win = True; multiplier = 10
                elif choice.startswith("d3_"):
                    target_sum = int(choice.split("_")[1])
                    if total == target_sum:
                        is_win = True
                        if target_sum in [9, 10, 11, 12]: multiplier = 7
                        elif target_sum in [8, 13]: multiplier = 9
                        elif target_sum in [7, 14]: multiplier = 12
                        elif target_sum in [6, 15]: multiplier = 15
                        elif target_sum in [5, 16]: multiplier = 18
                        elif target_sum in [4, 17]: multiplier = 25
                        elif target_sum in [3, 18]: multiplier = 30
                elif choice == "tai" and res_tx == "tai": is_win = True; multiplier = 2.3
                elif choice == "xiu" and res_tx == "xiu": is_win = True; multiplier = 2.3
                elif choice == "chan" and res_cl == "chan": is_win = True; multiplier = 2.3
                elif choice == "le" and res_cl == "le": is_win = True; multiplier = 2.3
                elif choice == "tl" and res_tx == "tai" and res_cl == "le": is_win = True; multiplier = 3
                elif choice == "tc" and res_tx == "tai" and res_cl == "chan": is_win = True; multiplier = 3
                elif choice == "xl" and res_tx == "xiu" and res_cl == "le": is_win = True; multiplier = 3
                elif choice == "xc" and res_tx == "xiu" and res_cl == "chan": is_win = True; multiplier = 3
                elif choice.startswith("a"):
                    target_triple = int(choice[1])
                    if dice_values == [target_triple, target_triple, target_triple]:
                        is_win = True; multiplier = 150

                if is_win:
                    win_amt = int(amt * multiplier)
                    add_money(uid, win_amt, f"Thắng Tài Xỉu Room {choice.upper()}")
                    total_win += win_amt
                    new_balance = get_balance(uid)
                    try:
                        await bot.send_message(uid,
                            f'{ce("✅")} <b>THẮNG RỒI</b>  #{session_id}  ({dice_str} {result_code})\n'
                            f'{ce("✅")} <b>Lệnh Cược:</b> {choice.upper()} {fmt_money(amt)}đ\n'
                            f'{ce("💰")} <b>Tiền thắng:</b> +{fmt_money(win_amt)}đ\n'
                            f'{ce("💎")} <b>Số dư mới:</b> {fmt_money(new_balance)}đ\n'
                            f'{ce("🎉")} Chúc ông chủ may mắn',
                            parse_mode=ParseMode.HTML)
                    except: pass
                else:
                    total_lose += amt
                    new_balance = get_balance(uid)
                    try:
                        await bot.send_message(uid,
                            f'{ce("❌")} <b>THUA</b>  #{session_id}  ({dice_str} {result_code})\n'
                            f'{ce("❌")} <b>Lệnh Cược:</b> {choice.upper()} {fmt_money(amt)}đ\n'
                            f'{ce("❌")} <b>Tiền Thắng:</b> 0đ\n'
                            f'{ce("💵")} <b>Số dư mới:</b> {fmt_money(new_balance)}đ\n'
                            f'Chúc ông chủ may mắn',
                            parse_mode=ParseMode.HTML)
                    except: pass

            jackpot_amount = get_jackpot()
            jackpot_contribution = 0

            if total_lose > total_win:
                jackpot_contribution = int(total_lose * 0.044)
                jackpot_amount += jackpot_contribution
                update_jackpot(jackpot_amount)

            jackpot_winners = []
            count_1 = dice_values.count(1)
            count_6 = dice_values.count(6)

            if count_6 >= 3:
                winners = [b for b in game_state["bets"].values() if b["choice"] == "tai"]
                if winners and jackpot_amount > 0:
                    total_bet_tai = sum(w["amount"] for w in winners)
                    for w in winners:
                        share = int(jackpot_amount * (w["amount"] / total_bet_tai))
                        add_money(w["user_id"], share, f"Nổ hũ Jackpot (3 con 6) +{share:,}đ")
                        jackpot_winners.append(f'{ce("👥")} <code>{w["user_id"]}</code>: <code>+{fmt_money(share)}đ</code>')
                    update_jackpot(100000)
                    jackpot_amount = 100000
            elif count_1 >= 3:
                winners = [b for b in game_state["bets"].values() if b["choice"] == "xiu"]
                if winners and jackpot_amount > 0:
                    total_bet_xiu = sum(w["amount"] for w in winners)
                    for w in winners:
                        share = int(jackpot_amount * (w["amount"] / total_bet_xiu))
                        add_money(w["user_id"], share, f"Nổ hũ Jackpot (3 con 1) +{share:,}đ")
                        jackpot_winners.append(f'{ce("👥")} <code>{w["user_id"]}</code>: <code>+{fmt_money(share)}đ</code>')
                    update_jackpot(100000)
                    jackpot_amount = 100000

            if group_id not in game_history:
                game_history[group_id] = []
            game_history[group_id].append({'tx': res_tx, 'cl': res_cl})
            if len(game_history[group_id]) > 10:
                game_history[group_id].pop(0)

            cau_tx = ""
            cau_cl = ""
            for h in game_history.get(group_id, []):
                cau_tx += "🔵" if h['tx'] == "tai" else "🔴"
                cau_cl += "⚪️" if h['cl'] == "chan" else "⚫️"

            final_msg = (
                f'{ce("📊")} <b>Kết quả Phiên #{session_id}</b>\n'
                f'┏━━━━━━━━━━━━━\n'
                f'┃ {dice_str} {ce("➡️")} {total} {result_text} {result_icons}\n'
                f'┃\n'
                f'┃ {ce("💰")} Tổng thắng: {fmt_money(total_win)}\n'
                f'┃ {ce("❌")} Tổng thua: {fmt_money(total_lose)}\n'
                f'┃\n'
                f'┃ {ce("🤑")} Trích hũ (4.4% tổng thua): +{fmt_money(jackpot_contribution)}\n'
                f'┃ {ce("🎁")} Hũ hiện tại: {fmt_money(jackpot_amount)}đ\n'
                f'┗━━━━━━━━━━━━━\n'
                f'<b>Cầu gần đây:</b>\n'
                f'{cau_tx if cau_tx else "Chưa có"}\n'
                f'      🔵  Tài             🔴  XỈU\n'
                f'{cau_cl if cau_cl else "Chưa có"}\n'
                f'      ⚪️  Chẵn        ⚫️  Lẻ.'
            )

            if jackpot_winners:
                final_msg += (
                    f'\n\n{ce("🎉")} <b>NỔ HŨ JACKPOT!</b> {ce("🎉")}\n'
                    f'┏━━━━━━━━━━━━━\n'
                    f'┃ {ce("💰")} Chia theo tỉ lệ tiền cược:\n'
                    + "\n".join([f'┃ {w}' for w in jackpot_winners]) +
                    f'\n┗━━━━━━━━━━━━━\n'
                    f'{ce("🔄")} Hũ đã reset về 100.000đ'
                )

            try:
                await bot.set_chat_permissions(chat_id, FULL_PERMS)
            except Exception as e:
                print(f"Lỗi mở khóa chat: {e}")

            await bot.send_message(chat_id, final_msg, parse_mode=ParseMode.HTML)
            group_games.pop(group_id, None)
            await asyncio.sleep(10)

        except Exception as e:
            print(f"Lỗi run_dice_game_cycle: {e}")
            traceback.print_exc()
            try:
                await bot.set_chat_permissions(chat_id, FULL_PERMS)
            except Exception:
                pass
            await asyncio.sleep(5)

def choices_conflict(c1, c2):
    def get_props(c):
        if c == "tai": return {"tai"}
        if c == "xiu": return {"xiu"}
        if c == "chan": return {"chan"}
        if c == "le": return {"le"}
        if c == "tl": return {"tai", "le"}
        if c == "tc": return {"tai", "chan"}
        if c == "xl": return {"xiu", "le"}
        if c == "xc": return {"xiu", "chan"}
        return set()

    p1 = get_props(c1)
    p2 = get_props(c2)

    if "tai" in p1 and "xiu" in p2: return True
    if "xiu" in p1 and "tai" in p2: return True
    if "chan" in p1 and "le" in p2: return True
    if "le" in p1 and "chan" in p2: return True
    return False

async def place_bet_in_group(bot, user_id, group_id, choice, amount, username=""):
    if not room_betting_enabled.get(group_id, True):
        return False, f'{ce("🔒")} <b>PHÒNG ĐÃ BỊ KHÓA CƯỢC!</b>'
    game = group_games.get(group_id)
    if not game or game["status"] != "betting":
        return False, f'{ce("❌")} Hiện tại không có phiên cược nào đang mở!'
    balance = get_balance(user_id)
    if balance < amount:
        return False, f'{ce("❌")} Số dư không đủ! Cần <code>{fmt_money(amount)}đ</code> nhưng chỉ có <code>{fmt_money(balance)}đ</code>.'
    if amount < 1000:
        return False, f'{ce("❌")} Số tiền cược tối thiểu là <code>1,000đ</code>!'

    bet_key = f"{user_id}_{choice}"
    if bet_key in game["bets"]:
        old_amount = game["bets"][bet_key]["amount"]
        new_total = old_amount + amount
        if not sub_money(user_id, amount, f"Cược {choice.upper()} nhóm - {amount:,}đ"):
            return False, f'{ce("❌")} Lỗi trừ tiền, vui lòng thử lại!'
        game["bets"][bet_key]["amount"] = new_total
    else:
        conflict = False
        for existing_bet in game["bets"].values():
            if existing_bet["user_id"] == user_id:
                if choices_conflict(choice, existing_bet["choice"]):
                    conflict = True
                    break
        if conflict:
            return False, f'{ce("🚫")} <b>KHÔNG ĐƯỢC ĐẶT NGƯỢC CỬA!</b>\nBạn đã có cược xung đột trong phiên này.'

        if not sub_money(user_id, amount, f"Cược {choice.upper()} nhóm - {amount:,}đ"):
            return False, f'{ce("❌")} Lỗi trừ tiền, vui lòng thử lại!'

        game["bets"][bet_key] = {
            "user_id": user_id,
            "amount": amount,
            "choice": choice,
            "username": username,
            "anonymous": False
        }

    new_balance = get_balance(user_id)

    choice_display_map = {
        "tai": "TÀI", "xiu": "XỈU", "chan": "CHẴN", "le": "LẺ",
        "tl": "TÀI + LẺ", "tc": "TÀI + CHẴN", "xl": "XỈU + LẺ", "xc": "XỈU + CHẴN",
        "a1": "BỘ BA 1-1-1", "a2": "BỘ BA 2-2-2", "a3": "BỘ BA 3-3-3",
        "a4": "BỘ BA 4-4-4", "a5": "BỘ BA 5-5-5", "a6": "BỘ BA 6-6-6",
    }.get(choice, choice.upper())

    session_id = game.get("session_id", 0)
    multiplier = 2.3
    if choice in ["tl", "tc", "xl", "xc"]: multiplier = 3
    elif choice.startswith("a"): multiplier = 150
    elif choice.startswith("d1"): multiplier = 5
    elif choice.startswith("d2"): multiplier = 10
    elif choice.startswith("d3"): multiplier = "7-30"

    msg = (
        f'{ce("✅")} Đặt thành công — Phiên #{session_id}\n\n'
        f'{ce("🥷")} Công khai\n'
        f'{ce("🎯")} {choice_display_map} · {fmt_money(game["bets"][bet_key]["amount"])}\n'
        f'{ce("💵")} Tỷ lệ x{multiplier}\n'
        f'{ce("💰")} Số dư: {fmt_money(new_balance)}'
    )
    return True, msg

async def place_anonymous_bet(bot, user_id, group_id, choice, amount):
    if not room_betting_enabled.get(group_id, True):
        return False, f'{ce("🔒")} <b>PHÒNG ĐÃ BỊ KHÓA CƯỢC!</b>'
    game = group_games.get(group_id)
    if not game or game["status"] != "betting":
        return False, f'{ce("❌")} Hiện tại không có phiên cược nào đang mở!'
    balance = get_balance(user_id)
    if balance < amount:
        return False, f'{ce("❌")} Số dư không đủ! Cần <code>{fmt_money(amount)}đ</code> nhưng chỉ có <code>{fmt_money(balance)}đ</code>.'
    if amount < 1000:
        return False, f'{ce("❌")} Số tiền cược tối thiểu là <code>1,000đ</code>!'

    bet_key = f"{user_id}_{choice}"
    if bet_key in game["bets"]:
        old_amount = game["bets"][bet_key]["amount"]
        new_total = old_amount + amount
        if not sub_money(user_id, amount, f"Cược ẩn danh {choice.upper()} - {amount:,}đ"):
            return False, f'{ce("❌")} Lỗi trừ tiền, vui lòng thử lại!'
        game["bets"][bet_key]["amount"] = new_total
        game["bets"][bet_key]["anonymous"] = True
    else:
        conflict = False
        for existing_bet in game["bets"].values():
            if existing_bet["user_id"] == user_id:
                if choices_conflict(choice, existing_bet["choice"]):
                    conflict = True
                    break
        if conflict:
            return False, f'{ce("🚫")} <b>KHÔNG ĐƯỢC ĐẶT NGƯỢC CỬA!</b>\nBạn đã có cược xung đột trong phiên này.'

        if not sub_money(user_id, amount, f"Cược ẩn danh {choice.upper()} - {amount:,}đ"):
            return False, f'{ce("❌")} Lỗi trừ tiền, vui lòng thử lại!'

        game["bets"][bet_key] = {
            "user_id": user_id,
            "amount": amount,
            "choice": choice,
            "username": "Ẩn Danh",
            "anonymous": True
        }

    new_balance = get_balance(user_id)
    session_id = game.get("session_id", 0)

    short_choice = {"tai": "T", "xiu": "X", "chan": "C", "le": "L", "tl": "TL", "tc": "TC", "xl": "XL", "xc": "XC"}.get(choice, choice.upper())

    group_notification = (
        f'{ce("💬")} Ẩn danh cược phiên #{session_id}\n'
        f'{ce("💬")} {short_choice} - {fmt_money(amount)}'
    )
    try:
        await bot.send_message(group_id, group_notification, parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"Lỗi gửi thông báo ẩn danh lên nhóm: {e}")

    msg = (
        f'{ce("✅")} Đặt ẩn danh thành công — Phiên #{session_id}\n\n'
        f'{ce("🥷")} Ẩn Danh\n'
        f'{ce("🎯")} {short_choice} · {fmt_money(game["bets"][bet_key]["amount"])}\n'
        f'{ce("💰")} Số dư: {fmt_money(new_balance)}'
    )
    return True, msg

def get_group_game_status(group_id):
    game = group_games.get(group_id)
    if not game:
        return None
    return game["status"]

async def bet_group_handler(update: Update, ctx, choice: str, amount=None):
    if update.effective_chat.type == "private":
        await update.effective_message.reply_text(
            f'{ce("⚡")} Lệnh này chỉ sử dụng được trong NHÓM game!',
            parse_mode=ParseMode.HTML)
        return
    user_id = update.effective_user.id
    group_id = update.effective_chat.id
    username = update.effective_user.username or update.effective_user.first_name
    if is_banned(user_id):
        await update.effective_message.reply_text(f'{ce("🚫")} Bạn đã bị khóa tài khoản!', parse_mode=ParseMode.HTML)
        return

    if amount is None:
        if not ctx.args:
            await update.effective_message.reply_text(
                f'{ce("❌")} Cú pháp: <code>{choice} [số_tiền]</code> hoặc <code>{choice} max</code>',
                parse_mode=ParseMode.HTML)
            return

        arg = ctx.args[0].lower()
        if arg in ["max", "all"]:
            amount = get_balance(user_id)
            if amount < 1000:
                await update.effective_message.reply_text(f'{ce("❌")} Số dư không đủ (tối thiểu 1,000đ)!', parse_mode=ParseMode.HTML)
                return
        else:
            try:
                amount = int(arg)
            except ValueError:
                await update.effective_message.reply_text(f'{ce("❌")} Số tiền không hợp lệ! VD: 50000 hoặc <code>max</code>', parse_mode=ParseMode.HTML)
                return

    success, message = await place_bet_in_group(ctx.bot, user_id, group_id, choice, amount, username)
    await update.effective_message.reply_text(message, parse_mode=ParseMode.HTML)

async def group_status_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await update.effective_message.reply_text(f'{ce("⚡")} Lệnh này chỉ sử dụng được trong NHÓM!', parse_mode=ParseMode.HTML)
        return
    group_id = update.effective_chat.id
    status = get_group_game_status(group_id)
    if status == "betting":
        await update.effective_message.reply_text(
            f'{ce("🎲")} <b>Đang MỞ CƯỢC!</b>\nHãy đặt cược ngay: <code>T [tiền]</code> hoặc <code>T max</code>',
            parse_mode=ParseMode.HTML)
    elif status == "rolling":
        await update.effective_message.reply_text(f'{ce("🎲")} <b>ĐANG TUNG XÚC SẮC!</b>', parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(f'⏸️ <b>CHƯA CÓ PHIÊN CƯỢC NÀO</b>', parse_mode=ParseMode.HTML)

async def sd_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    balance = get_balance(uid)
    await update.effective_message.reply_text(
        f'{ce("💰")} <b>SỐ DƯ HIỆN CÓ</b>\n'
        f'{ce("👥")} ID: <code>{uid}</code>\n'
        f'{ce("💵")} Số dư: <code>{fmt_money(balance)}đ</code>',
        parse_mode=ParseMode.HTML)

# ================= CÁC GAME LẺ =================
async def play_xucxac_don(update, ctx, choice_code, amount):
    uid = update.effective_user.id
    if is_game_banned(uid, 2):
        return await update.effective_message.reply_text(f'{ce("🚫")} Bạn đã bị cấm chơi trò chơi này!', parse_mode=ParseMode.HTML)
    if check_mt('mt_xucxac_don') and uid not in ADMIN_IDS:
        return await update.effective_message.reply_text(f'{ce("⚙️")} Game Xúc Xắc Đơn đang bảo trì!', parse_mode=ParseMode.HTML)
    if amount < 1000:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền cược tối thiểu là 1.000đ!', parse_mode=ParseMode.HTML)
    if not sub_money(uid, amount, f"Cược Xúc Xắc Đơn {choice_code}"):
        return await update.effective_message.reply_text(f'{ce("❌")} Bạn không đủ số dư.', parse_mode=ParseMode.HTML)

    msg_status = await update.effective_message.reply_text(f'{ce("🎲")} <b>ĐANG LẮC XÚC XẮC...</b>', parse_mode=ParseMode.HTML)
    dice = await update.effective_message.reply_dice(emoji="🎲")
    await asyncio.sleep(4)

    result = dice.dice.value
    c = choice_code.upper()

    win = False
    multiplier = 1.95

    if c in ["XXC", "XXL", "XXT", "XXX"]:
        if c == "XXC" and result in [2, 4, 6]: win = True
        elif c == "XXL" and result in [1, 3, 5]: win = True
        elif c == "XXT" and result in [4, 5, 6]: win = True
        elif c == "XXX" and result in [1, 2, 3]: win = True
    elif c.startswith("D"):
        try:
            target = int(c[1])
            if result == target:
                win = True
                multiplier = 5
        except:
            pass

    if win:
        win_amt = int(amount * multiplier)
        add_money(uid, win_amt, f"Thắng Xúc Xắc Đơn {c}")
        status = f'{ce("✅")} <b>THẮNG</b> | Nhận: <code>+{fmt_money(win_amt)}đ</code>'
    else:
        status = f'{ce("❌")} <b>THUA</b>'

    await msg_status.edit_text(
        f'{ce("🎲")} <b>KẾT QUẢ XÚC XẮC ĐƠN</b>\n\n'
        f'{ce("🎲")} Xúc xắc: <b>{result}</b>\n'
        f'{ce("✍️")} Bạn chọn: <b>{c}</b>\n\n'
        f'{status}\n'
        f'{ce("💰")} Số dư: <code>{fmt_money(get_balance(uid))}đ</code>',
        parse_mode=ParseMode.HTML)

async def play_longho(update, ctx, choice, amount):
    uid = update.effective_user.id
    if is_game_banned(uid, 3):
        return await update.effective_message.reply_text(f'{ce("🚫")} Bạn đã bị cấm chơi trò chơi này!', parse_mode=ParseMode.HTML)
    if check_mt('mt_longho') and uid not in ADMIN_IDS:
        return await update.effective_message.reply_text(f'{ce("⚙️")} Game Long Hổ đang bảo trì!', parse_mode=ParseMode.HTML)
    if amount < 1000:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền cược tối thiểu là 1.000đ!', parse_mode=ParseMode.HTML)
    if not sub_money(uid, amount, f"Cược Long Hổ {choice.upper()}"):
        return await update.effective_message.reply_text(f'{ce("❌")} Bạn không đủ số dư.', parse_mode=ParseMode.HTML)

    msg_status = await update.effective_message.reply_text(f'{ce("🎲")} <b>ĐANG CHIA BÀI...</b>', parse_mode=ParseMode.HTML)
    await asyncio.sleep(2)

    try:
        long_card = random.randint(1, 13)
        ho_card = random.randint(1, 13)
        card_names = {1: "A", 11: "J", 12: "Q", 13: "K"}

        if long_card == ho_card:
            add_money(uid, amount, "Hoàn tiền Long Hổ (Hòa)")
            await msg_status.edit_text(
                f'{ce("⚰️")} <b>LONG HỔ</b>\n\n'
                f'{ce("🐯")} LONG: <b>{card_names.get(long_card, long_card)}</b>\n'
                f'{ce("🐉")} HỔ: <b>{card_names.get(ho_card, ho_card)}</b>\n\n'
                f'{ce("⚖️")} <b>HÒA!</b> Hoàn tiền: <code>{fmt_money(amount)}đ</code>\n'
                f'{ce("💰")} Số dư: <code>{fmt_money(get_balance(uid))}đ</code>',
                parse_mode=ParseMode.HTML)
            return

        result = "long" if long_card > ho_card else "ho"
        is_win = (choice == result)

        if is_win:
            win_amt = int(amount * 1.95)
            add_money(uid, win_amt, f"Thắng Long Hổ {choice.upper()}")
            status = f'{ce("🎉")} <b>THẮNG!</b> Nhận: <code>+{fmt_money(win_amt)}đ</code>'
        else:
            status = f'{ce("❌")} <b>THUA!</b>'

        await msg_status.edit_text(
            f'{ce("⚰️")} <b>LONG HỔ</b>\n\n'
            f'{ce("🐯")} LONG: <b>{card_names.get(long_card, long_card)}</b>\n'
            f'{ce("🐉")} HỔ: <b>{card_names.get(ho_card, ho_card)}</b>\n\n'
            f'Kết quả: <b>{"LONG" if result == "long" else "HỔ"}</b>\n'
            f'{status}\n'
            f'{ce("💰")} Số dư: <code>{fmt_money(get_balance(uid))}đ</code>',
            parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"Lỗi play_longho: {e}")
        try:
            await msg_status.edit_text(
                f'{ce("⚠️")} Có lỗi xảy ra, vui lòng thử lại!\n{ce("💰")} Số dư: <code>{fmt_money(get_balance(uid))}đ</code>',
                parse_mode=ParseMode.HTML)
        except:
            pass

async def lh_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        return await update.effective_message.reply_text(
            f'{ce("❌")} Cú pháp: <code>/lh [long/ho] [số_tiền]</code>',
            parse_mode=ParseMode.HTML)
    choice = ctx.args[0].lower()
    if choice not in ["long", "ho"]:
        return await update.effective_message.reply_text(
            f'{ce("❌")} Chỉ chọn <code>long</code> hoặc <code>ho</code>!',
            parse_mode=ParseMode.HTML)
    try:
        amt = int(ctx.args[1])
    except:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền không hợp lệ!', parse_mode=ParseMode.HTML)
    await play_longho(update, ctx, choice, amt)

async def play_minipoker(update, ctx, amount):
    uid = update.effective_user.id
    if is_game_banned(uid, 4):
        return await update.effective_message.reply_text(f'{ce("🚫")} Bạn đã bị cấm chơi trò chơi này!', parse_mode=ParseMode.HTML)
    if check_mt('mt_minipoker') and uid not in ADMIN_IDS:
        return await update.effective_message.reply_text(f'{ce("⚙️")} Game Mini Poker đang bảo trì!', parse_mode=ParseMode.HTML)
    if amount < 1000:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền cược tối thiểu là 1.000đ!', parse_mode=ParseMode.HTML)
    if not sub_money(uid, amount, f"Cược Mini Poker"):
        return await update.effective_message.reply_text(f'{ce("❌")} Bạn không đủ số dư.', parse_mode=ParseMode.HTML)

    msg_status = await update.effective_message.reply_text(f'{ce("🃏")} <b>ĐANG CHIA BÀI...</b>', parse_mode=ParseMode.HTML)
    await asyncio.sleep(2)

    suits = ["♠️", "♥️", "♦️", "♣️"]
    ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

    cards = []
    for _ in range(5):
        suit = random.choice(suits)
        rank = random.choice(ranks)
        cards.append((rank, suit))

    rank_counts = {}
    for rank, suit in cards:
        rank_counts[rank] = rank_counts.get(rank, 0) + 1

    max_count = max(rank_counts.values())

    if max_count == 4:
        multiplier = 100
        hand_name = "TỨ QUÝ"
    elif max_count == 3:
        multiplier = 25
        hand_name = "BỘ BA"
    elif max_count == 2:
        pairs = sum(1 for c in rank_counts.values() if c == 2)
        if pairs == 2:
            multiplier = 10
            hand_name = "HAI ĐÔI"
        else:
            multiplier = 2
            hand_name = "MỘT ĐÔI"
    else:
        multiplier = 0
        hand_name = "BÀI RÁC"

    cards_str = " ".join([f"{r}{s}" for r, s in cards])

    if multiplier > 0:
        win_amt = int(amount * multiplier)
        add_money(uid, win_amt, f"Thắng Mini Poker {hand_name} x{multiplier}")
        status = f'{ce("🎉")} <b>THẮNG {hand_name}!</b> x{multiplier}\nNhận: <code>+{fmt_money(win_amt)}đ</code>'
    else:
        status = f'{ce("❌")} <b>THUA!</b> Bài rác'

    await msg_status.edit_text(
        f'{ce("🔝")} <b>MINI POKER</b>\n\n'
        f'{ce("🎴")} Bài của bạn: {cards_str}\n'
        f'{ce("🏆")} Bộ: <b>{hand_name}</b>\n\n'
        f'{status}\n'
        f'{ce("💰")} Số dư: <code>{fmt_money(get_balance(uid))}đ</code>',
        parse_mode=ParseMode.HTML)

async def mp_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 1:
        return await update.effective_message.reply_text(
            f'{ce("❌")} Cú pháp: <code>/mp [số_tiền]</code>',
            parse_mode=ParseMode.HTML)
    try:
        amt = int(ctx.args[0])
    except:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền không hợp lệ!', parse_mode=ParseMode.HTML)
    await play_minipoker(update, ctx, amt)

async def play_baccarat(update, ctx, choice, amount):
    uid = update.effective_user.id
    if is_game_banned(uid, 5):
        return await update.effective_message.reply_text(f'{ce("🚫")} Bạn đã bị cấm chơi trò chơi này!', parse_mode=ParseMode.HTML)
    if check_mt('mt_baccarat') and uid not in ADMIN_IDS:
        return await update.effective_message.reply_text(f'{ce("⚙️")} Game Baccarat đang bảo trì!', parse_mode=ParseMode.HTML)
    if amount < 1000:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền cược tối thiểu là 1.000đ!', parse_mode=ParseMode.HTML)
    if not sub_money(uid, amount, f"Cược Baccarat {choice.upper()}"):
        return await update.effective_message.reply_text(f'{ce("❌")} Bạn không đủ số dư.', parse_mode=ParseMode.HTML)

    msg_status = await update.effective_message.reply_text(f'{ce("🎰")} <b>ĐANG CHIA BÀI BACCARAT...</b>', parse_mode=ParseMode.HTML)
    await asyncio.sleep(2)

    def draw_card():
        return random.randint(0, 9)

    player_score = (draw_card() + draw_card()) % 10
    banker_score = (draw_card() + draw_card()) % 10

    if player_score < 6:
        player_score = (player_score + draw_card()) % 10
    if banker_score < 6:
        banker_score = (banker_score + draw_card()) % 10

    if player_score > banker_score:
        result = "player"
        result_name = "PLAYER"
    elif banker_score > player_score:
        result = "banker"
        result_name = "BANKER"
    else:
        result = "tie"
        result_name = "TIE"

    is_win = (choice == result)

    if result == "tie" and choice != "tie":
        add_money(uid, amount, "Hoàn tiền Baccarat (Hòa)")
        status = f'{ce("⚖️")} <b>HÒA!</b> Hoàn tiền: <code>{fmt_money(amount)}đ</code>'
    elif is_win:
        multiplier = 9 if choice == "tie" else 2
        win_amt = int(amount * multiplier)
        add_money(uid, win_amt, f"Thắng Baccarat {choice.upper()} x{multiplier}")
        status = f'{ce("🎉")} <b>THẮNG!</b> x{multiplier}\nNhận: <code>+{fmt_money(win_amt)}đ</code>'
    else:
        status = f'{ce("❌")} <b>THUA!</b>'

    await msg_status.edit_text(
        f'{ce("⬆️")} <b>BACCARAT</b>\n\n'
        f'{ce("👤")} PLAYER: <b>{player_score}</b>\n'
        f'{ce("🏦")} BANKER: <b>{banker_score}</b>\n\n'
        f'Kết quả: <b>{result_name}</b>\n'
        f'{status}\n'
        f'{ce("💰")} Số dư: <code>{fmt_money(get_balance(uid))}đ</code>',
        parse_mode=ParseMode.HTML)

async def baccarat_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        return await update.effective_message.reply_text(
            f'{ce("❌")} Cú pháp: <code>/bcr [player/banker/tie] [số_tiền]</code>',
            parse_mode=ParseMode.HTML)
    choice = ctx.args[0].lower()
    if choice not in ["player", "banker", "tie"]:
        return await update.effective_message.reply_text(
            f'{ce("❌")} Chỉ chọn <code>player</code>, <code>banker</code> hoặc <code>tie</code>!',
            parse_mode=ParseMode.HTML)
    try:
        amt = int(ctx.args[1])
    except:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền không hợp lệ!', parse_mode=ParseMode.HTML)
    await play_baccarat(update, ctx, choice, amt)

async def play_xocdia4(update, ctx, choice, amount):
    uid = update.effective_user.id
    if is_game_banned(uid, 7):
        return await update.effective_message.reply_text(f'{ce("🚫")} Bạn đã bị cấm chơi trò chơi này!', parse_mode=ParseMode.HTML)
    if check_mt('mt_xocdia4') and uid not in ADMIN_IDS:
        return await update.effective_message.reply_text(f'{ce("⚙️")} Game Xóc Đĩa 4 Vị đang bảo trì!', parse_mode=ParseMode.HTML)
    if amount < 1000:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền cược tối thiểu là 1.000đ!', parse_mode=ParseMode.HTML)
    if not sub_money(uid, amount, f"Cược Xóc Đĩa 4 Vị {choice.upper()}"):
        return await update.effective_message.reply_text(f'{ce("❌")} Bạn không đủ số dư.', parse_mode=ParseMode.HTML)

    msg_status = await update.effective_message.reply_text(f'{ce("💿")} <b>ĐANG XÓC ĐĨA 4 VỊ...</b>', parse_mode=ParseMode.HTML)
    await asyncio.sleep(2)

    results = [random.randint(0, 1) for _ in range(4)]
    red_count = sum(results)
    icons = "".join(["🔴" if r == 1 else "⚪️" for r in results])
    is_chan = (red_count % 2 == 0)

    win = (choice == "chan" and is_chan) or (choice == "le" and not is_chan)

    if win:
        win_amt = int(amount * 1.95)
        add_money(uid, win_amt, f"Thắng Xóc Đĩa 4 Vị {choice.upper()}")
        status = f'{ce("🎉")} <b>THẮNG!</b> Nhận: <code>+{fmt_money(win_amt)}đ</code>'
    else:
        status = f'{ce("❌")} <b>THUA!</b>'

    await msg_status.edit_text(
        f'{ce("❓")} <b>XÓC ĐĨA 4 VỊ</b>\n\n'
        f'{icons}\n'
        f'{ce("✍️")} {"CHẴN" if is_chan else "LẺ"} ({red_count} Đỏ)\n\n'
        f'{status}\n'
        f'{ce("💰")} Số dư: <code>{fmt_money(get_balance(uid))}đ</code>',
        parse_mode=ParseMode.HTML)

async def xd4_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        return await update.effective_message.reply_text(
            f'{ce("❌")} Cú pháp: <code>/xd4 [chan/le] [số_tiền]</code>',
            parse_mode=ParseMode.HTML)
    choice = ctx.args[0].lower()
    if choice not in ["chan", "le"]:
        return await update.effective_message.reply_text(
            f'{ce("❌")} Chỉ chọn <code>chan</code> hoặc <code>le</code>!',
            parse_mode=ParseMode.HTML)
    try:
        amt = int(ctx.args[1])
    except:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền không hợp lệ!', parse_mode=ParseMode.HTML)
    await play_xocdia4(update, ctx, choice, amt)

async def play_taixiumd5(update, ctx, choice, amount):
    uid = update.effective_user.id
    if is_game_banned(uid, 8):
        return await update.effective_message.reply_text(f'{ce("🚫")} Bạn đã bị cấm chơi trò chơi này!', parse_mode=ParseMode.HTML)
    if check_mt('mt_taixiumd5') and uid not in ADMIN_IDS:
        return await update.effective_message.reply_text(f'{ce("⚙️")} Game Tài Xỉu MD5 đang bảo trì!', parse_mode=ParseMode.HTML)
    if amount < 1000:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền cược tối thiểu là 1.000đ!', parse_mode=ParseMode.HTML)
    if not sub_money(uid, amount, f"Cược Tài Xỉu MD5 {choice.upper()}"):
        return await update.effective_message.reply_text(f'{ce("❌")} Bạn không đủ số dư.', parse_mode=ParseMode.HTML)

    msg_status = await update.effective_message.reply_text(f'{ce("🎲")} <b>ĐANG RANDOM MD5...</b>', parse_mode=ParseMode.HTML)
    await asyncio.sleep(2)

    seed_str = f"{uid}{get_vietnam_time().timestamp()}{random.randint(1, 999999)}"
    md5_hash = hashlib.md5(seed_str.encode()).hexdigest()

    d1 = int(md5_hash[0:2], 16) % 6 + 1
    d2 = int(md5_hash[2:4], 16) % 6 + 1
    d3 = int(md5_hash[4:6], 16) % 6 + 1

    total = d1 + d2 + d3
    is_tai = total >= 11
    is_chan = total % 2 == 0

    win = False
    if choice == "tai" and is_tai: win = True
    elif choice == "xiu" and not is_tai: win = True
    elif choice == "chan" and is_chan: win = True
    elif choice == "le" and not is_chan: win = True

    if win:
        win_amt = int(amount * 1.95)
        add_money(uid, win_amt, f"Thắng Tài Xỉu MD5 {choice.upper()}")
        status = f'{ce("🎉")} <b>THẮNG!</b> Nhận: <code>+{fmt_money(win_amt)}đ</code>'
    else:
        status = f'{ce("❌")} <b>THUA!</b>'

    await msg_status.edit_text(
        f'{ce("👌")} <b>TÀI XỈU MD5</b>\n\n'
        f'{ce("🎲")} Xúc xắc: <b>{d1} - {d2} - {d3}</b>\n'
        f'{ce("📊")} Tổng: <b>{total}</b> {ce("➡️")} {"TÀI" if is_tai else "XỈU"} {"CHẴN" if is_chan else "LẺ"}\n'
        f'{ce("🔒")} MD5: <code>{md5_hash[:16]}...</code>\n\n'
        f'{status}\n'
        f'{ce("💰")} Số dư: <code>{fmt_money(get_balance(uid))}đ</code>',
        parse_mode=ParseMode.HTML)

async def txmd5_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        return await update.effective_message.reply_text(
            f'{ce("❌")} Cú pháp: <code>/txmd5 [tai/xiu/chan/le] [số_tiền]</code>',
            parse_mode=ParseMode.HTML)
    choice = ctx.args[0].lower()
    if choice not in ["tai", "xiu", "chan", "le"]:
        return await update.effective_message.reply_text(
            f'{ce("❌")} Chỉ chọn <code>tai</code>, <code>xiu</code>, <code>chan</code> hoặc <code>le</code>!',
            parse_mode=ParseMode.HTML)
    try:
        amt = int(ctx.args[1])
    except:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền không hợp lệ!', parse_mode=ParseMode.HTML)
    await play_taixiumd5(update, ctx, choice, amt)

async def play_baucua(update, ctx, choice, amount):
    uid = update.effective_user.id
    if is_game_banned(uid, 9):
        return await update.effective_message.reply_text(f'{ce("🚫")} Bạn đã bị cấm chơi trò chơi này!', parse_mode=ParseMode.HTML)
    if check_mt('mt_baucua') and uid not in ADMIN_IDS:
        return await update.effective_message.reply_text(f'{ce("⚙️")} Game Bầu Cua đang bảo trì!', parse_mode=ParseMode.HTML)
    if amount < 1000:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền cược tối thiểu là 1.000đ!', parse_mode=ParseMode.HTML)
    if not sub_money(uid, amount, f"Cược Bầu Cua {choice.upper()}"):
        return await update.effective_message.reply_text(f'{ce("❌")} Bạn không đủ số dư.', parse_mode=ParseMode.HTML)

    msg_status = await update.effective_message.reply_text(f'{ce("🎲")} <b>ĐANG LẮC BẦU CUA...</b>', parse_mode=ParseMode.HTML)
    await asyncio.sleep(2)

    names = ["bau", "cua", "tom", "ca", "ga", "nai"]
    icons = ["🎃", "🦀", "🦐", "🐟", "🐓", "🦌"]  # đúng thứ tự: bầu, cua, tôm, cá, gà, nai
    results = [random.randint(0, 5) for _ in range(3)]

    count = results.count(names.index(choice))
    multiplier = count + 1 if count > 0 else 0

    dice_str = " ".join([icons[r] for r in results])

    if multiplier > 0:
        win_amt = int(amount * multiplier)
        add_money(uid, win_amt, f"Thắng Bầu Cua {choice.upper()}")
        status = f'{ce("🎉")} <b>THẮNG!</b> x{multiplier}\nNhận: <code>+{fmt_money(win_amt)}đ</code>'
    else:
        status = f'{ce("❌")} <b>THUA!</b>'

    await msg_status.edit_text(
        f'{ce("🎲")} <b>BẦU CUA</b>\n\n'
        f'{dice_str}\n\n'
        f'Bạn chọn: <b>{choice.upper()}</b>\n'
        f'{status}\n'
        f'{ce("💰")} Số dư: <code>{fmt_money(get_balance(uid))}đ</code>',
        parse_mode=ParseMode.HTML)

async def bc_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        return await update.effective_message.reply_text(
            f'{ce("❌")} Cú pháp: <code>/bc [bau/cua/tom/ca/ga/nai] [số_tiền]</code>',
            parse_mode=ParseMode.HTML)
    choice = ctx.args[0].lower()
    if choice not in ["bau", "cua", "tom", "ca", "ga", "nai"]:
        return await update.effective_message.reply_text(
            f'{ce("❌")} Chỉ chọn <code>bau</code>, <code>cua</code>, <code>tom</code>, <code>ca</code>, <code>ga</code>, <code>nai</code>!',
            parse_mode=ParseMode.HTML)
    try:
        amt = int(ctx.args[1])
    except:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền không hợp lệ!', parse_mode=ParseMode.HTML)
    await play_baucua(update, ctx, choice, amt)

async def play_xocdia6(update, ctx, choice, amount):
    uid = update.effective_user.id
    if is_game_banned(uid, 10):
        return await update.effective_message.reply_text(f'{ce("🚫")} Bạn đã bị cấm chơi trò chơi này!', parse_mode=ParseMode.HTML)
    if check_mt('mt_xocdia6') and uid not in ADMIN_IDS:
        return await update.effective_message.reply_text(f'{ce("⚙️")} Game Xóc Đĩa 6 Vị đang bảo trì!', parse_mode=ParseMode.HTML)
    if amount < 1000:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền cược tối thiểu là 1.000đ!', parse_mode=ParseMode.HTML)
    if not sub_money(uid, amount, f"Cược Xóc Đĩa 6 Vị {choice.upper()}"):
        return await update.effective_message.reply_text(f'{ce("❌")} Bạn không đủ số dư.', parse_mode=ParseMode.HTML)

    msg_status = await update.effective_message.reply_text(f'{ce("💿")} <b>ĐANG XÓC ĐĨA 6 VỊ...</b>', parse_mode=ParseMode.HTML)
    await asyncio.sleep(2)

    results = [random.randint(0, 1) for _ in range(6)]
    red_count = sum(results)
    icons = "".join(["🔴" if r == 1 else "⚪️" for r in results])
    is_chan = (red_count % 2 == 0)

    win = (choice == "chan" and is_chan) or (choice == "le" and not is_chan)

    if win:
        win_amt = int(amount * 1.95)
        add_money(uid, win_amt, f"Thắng Xóc Đĩa 6 Vị {choice.upper()}")
        status = f'{ce("🎉")} <b>THẮNG!</b> Nhận: <code>+{fmt_money(win_amt)}đ</code>'
    else:
        status = f'{ce("❌")} <b>THUA!</b>'

    await msg_status.edit_text(
        f'{ce("❓")} <b>XÓC ĐĨA 6 VỊ</b>\n\n'
        f'{icons}\n'
        f'{ce("✍️")} {"CHẴN" if is_chan else "LẺ"} ({red_count} Đỏ)\n\n'
        f'{status}\n'
        f'{ce("💰")} Số dư: <code>{fmt_money(get_balance(uid))}đ</code>',
        parse_mode=ParseMode.HTML)

async def xd6_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        return await update.effective_message.reply_text(
            f'{ce("❌")} Cú pháp: <code>/xd6 [chan/le] [số_tiền]</code>',
            parse_mode=ParseMode.HTML)
    choice = ctx.args[0].lower()
    if choice not in ["chan", "le"]:
        return await update.effective_message.reply_text(
            f'{ce("❌")} Chỉ chọn <code>chan</code> hoặc <code>le</code>!',
            parse_mode=ParseMode.HTML)
    try:
        amt = int(ctx.args[1])
    except:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền không hợp lệ!', parse_mode=ParseMode.HTML)
    await play_xocdia6(update, ctx, choice, amt)

# ================= CÁC HÀM DÙNG CHO NÚT TÀI KHOẢN (ĐÃ SỬA) =================
# Dùng update.effective_message (có cả khi bấm nút inline) và ctx.args or []
async def chuyen_tien_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg_obj = update.effective_message
    uid = update.effective_user.id
    args = ctx.args or []
    if len(args) < 2:
        return await msg_obj.reply_text(
            f'{ce("💸")} <b>Chuyển tiền theo cú pháp:</b>\n'
            f'<code>/chuyen [ID nhận tiền] [số tiền]</code>\n'
            f'VD: <code>/chuyen 123456789 10000</code>\n\n'
            f'{ce("⚠️")} Phí chuyển tiền là 5%, người chuyển chịu phí (tối thiểu 1.000).',
            parse_mode=ParseMode.HTML
        )
    try:
        target_id = int(args[0])
        amount = int(args[1])
        if amount < 1000:
            return await msg_obj.reply_text(f'{ce("❌")} Số tiền chuyển tối thiểu là 1.000đ!', parse_mode=ParseMode.HTML)
        if target_id == uid:
            return await msg_obj.reply_text(f'{ce("❌")} Không thể tự chuyển tiền cho chính mình!', parse_mode=ParseMode.HTML)

        fee = max(1000, int(amount * 0.05))
        total_deduct = amount + fee

        if get_balance(uid) < total_deduct:
            return await msg_obj.reply_text(f'{ce("❌")} Số dư không đủ! Bạn cần {fmt_money(total_deduct)}đ (bao gồm phí 5%).', parse_mode=ParseMode.HTML)

        if not query("SELECT 1 FROM users WHERE user_id=%s", (target_id,)):
            return await msg_obj.reply_text(f'{ce("❌")} ID người nhận không tồn tại!', parse_mode=ParseMode.HTML)

        if sub_money(uid, total_deduct, f"Chuyển tiền cho {target_id} (phí {fee}đ)"):
            add_money(target_id, amount, f"Nhận tiền từ {uid}")
            await msg_obj.reply_text(
                f'{ce("✅")} <b>CHUYỂN TIỀN THÀNH CÔNG</b>\n'
                f'Người nhận: <code>{target_id}</code>\n'
                f'Số tiền: <code>{fmt_money(amount)}đ</code>\n'
                f'Phí: <code>{fmt_money(fee)}đ</code>\n'
                f'Số dư còn lại: <code>{fmt_money(get_balance(uid))}đ</code>',
                parse_mode=ParseMode.HTML
            )
            try:
                await ctx.bot.send_message(target_id, f'{ce("💰")} Bạn vừa nhận được <code>{fmt_money(amount)}đ</code> từ ID <code>{uid}</code>.', parse_mode=ParseMode.HTML)
            except:
                pass
    except ValueError:
        await msg_obj.reply_text(f'{ce("❌")} ID hoặc số tiền không hợp lệ!', parse_mode=ParseMode.HTML)

async def ls_choi_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg_obj = update.effective_message
    uid = update.effective_user.id
    data = query("SELECT amount, note, time FROM history WHERE user_id=%s AND note LIKE '%%Cược%%' ORDER BY id DESC LIMIT 10", (uid,))
    if not data:
        return await msg_obj.reply_text(f'{ce("📜")} Bạn chưa có lịch sử chơi game nào.', parse_mode=ParseMode.HTML)
    msg = f'{ce("📜")} <b>LỊCH SỬ CHƠI GẦN ĐÂY:</b>\n\n'
    for row in data:
        msg += f'{ce("🎮")} {html.escape(row[1])} | <code>{fmt_money(abs(row[0]))}đ</code> | <i>{row[2]}</i>\n'
    await msg_obj.reply_text(msg, parse_mode=ParseMode.HTML)

async def ls_room_tx_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg_obj = update.effective_message
    uid = update.effective_user.id
    data = query(
        "SELECT amount, note, time FROM history WHERE user_id=%s AND "
        "(note LIKE '%%Tài Xỉu Room%%' OR note LIKE '%%nhóm%%' OR note LIKE '%%ẩn danh%%' OR note LIKE '%%Jackpot%%') "
        "ORDER BY id DESC LIMIT 10", (uid,))
    if not data:
        return await msg_obj.reply_text(f'{ce("📜")} Bạn chưa có lịch sử đánh Room TX nào.', parse_mode=ParseMode.HTML)
    msg = f'{ce("📜")} <b>LỊCH SỬ ROOM TX GẦN ĐÂY:</b>\n\n'
    for row in data:
        msg += f'{ce("🎲")} {html.escape(row[1])} | <code>{fmt_money(abs(row[0]))}đ</code> | <i>{row[2]}</i>\n'
    await msg_obj.reply_text(msg, parse_mode=ParseMode.HTML)


# ================= START & MAIN MENU =================
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_banned(uid):
        return
    if is_total_maintenance() and uid not in ADMIN_IDS:
        await update.effective_message.reply_text(
            f'{ce("⚡")} <b>HỆ THỐNG ĐANG BẢO TRÌ TOÀN BỘ</b>\n\nVui lòng quay lại sau ít phút!',
            parse_mode=ParseMode.HTML)
        return
    if is_system_maintenance() and uid not in ADMIN_IDS:
        await update.effective_message.reply_text(
            f'{ce("⚡")} <b>HỆ THỐNG ĐANG BẢO TRÌ</b>\n\nVui lòng quay lại sau ít phút!',
            parse_mode=ParseMode.HTML)
        return
    get_user(uid)
    if ctx.args:
        try:
            ref = int(ctx.args[0])
            if ref != uid:
                row = query("SELECT refed FROM users WHERE user_id=%s", (uid,))
                if row and row[0][0] == 0:
                    if query("SELECT 1 FROM users WHERE user_id=%s", (ref,)):
                        add_money(ref, 500, "Ref bonus")
                        query("UPDATE users SET refs=refs+1 WHERE user_id=%s", (ref,))
                        query("UPDATE users SET refed=1 WHERE user_id=%s", (uid,))
        except:
            pass

    menu = ReplyKeyboardMarkup([
        [kbtn("DANH SÁCH GAME", "👑"), kbtn("TÀI KHOẢN", "📜")],
        [kbtn("NẠP TIỀN", "💵"), kbtn("RÚT TIỀN", "₿")],
        [kbtn("GIỚI THIỆU", "🌸"), kbtn("ĐUA TOP", "🍕")],
        [kbtn("EVENT", "🎁"), kbtn("LỆNH", "🔍")]
    ], resize_keyboard=True)

    welcome_text = (
        f'{ce("🎉")} <b>CHÀO MỪNG {html.escape(update.effective_user.first_name.upper())} ĐÃ THAM GIA!</b>\n\n'
        f'{ce("🛡")} <b>{html.escape(get_bot_name())}</b>\n'
        f'Hệ thống trò chơi minh bạch — uy tín hàng đầu.\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("💰")} <b>MIN RÚT TIỀN:</b> <code>50,000đ</code>\n'
        f'{ce("💵")} <b>MIN NẠP TIỀN:</b> <code>10,000đ</code>\n\n'
        f'{ce("⚖️")} <b>CAM KẾT MINH BẠCH:</b>\n'
        f'• <b>100%</b> Kết quả hoàn toàn ngẫu nhiên.\n'
        f'• {ce("🔥")} <b>KHÔNG</b> can thiệp kết quả dưới mọi hình thức.\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("🎯")} Chúc bạn có những trải nghiệm may mắn và thú vị!'
    )
    await update.effective_message.reply_text(welcome_text, reply_markup=menu, parse_mode=ParseMode.HTML)

async def lien_ket(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_banned(uid):
        return
    if is_total_maintenance() and uid not in ADMIN_IDS:
        await update.effective_message.reply_text(f'{ce("⚡")} <b>HỆ THỐNG ĐANG BẢO TRÌ TOÀN BỘ</b>', parse_mode=ParseMode.HTML)
        return
    res = query("SELECT bank FROM users WHERE user_id=%s", (uid,))
    if res and res[0][0] is not None:
        return await update.effective_message.reply_text(
            f'{ce("❌")} Bạn đã liên kết ngân hàng rồi. Để thay đổi, vui lòng liên hệ Admin!',
            parse_mode=ParseMode.HTML)
    if not ctx.args or len(ctx.args) < 3:
        return await update.effective_message.reply_text(
            f'{ce("⚡")} <b>Cú pháp liên kết:</b>\n'
            f'<code>/lienket [Ngân_hàng] [STK] [Chủ_TK]</code>\n\n'
            f'VD: <code>/lienket MBBANK 0123456 NGUYEN VAN A</code>',
            parse_mode=ParseMode.HTML)
    bank = ctx.args[0].upper()
    stk = ctx.args[1]
    name = " ".join(ctx.args[2:]).upper()
    get_user(uid)
    query("UPDATE users SET bank=%s, stk=%s, name=%s, bank_linked=1 WHERE user_id=%s", (bank, stk, name, uid))
    await update.effective_message.reply_text(
        f'{ce("✅")} <b>LIÊN KẾT THÀNH CÔNG</b>\n\n'
        f'{ce("💳")} Ngân hàng: {html.escape(bank)}\n'
        f'{ce("💰")} STK: <code>{html.escape(stk)}</code>\n'
        f'{ce("👥")} Chủ TK: {html.escape(name)}\n\n'
        f'{ce("🎮")} Bạn đã có thể tham gia chơi game!',
        parse_mode=ParseMode.HTML)

async def rut(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    msg_obj = update.effective_message
    args = ctx.args or []
    if is_banned(uid):
        return
    if is_feature_banned(uid, 'rut'):
        return await msg_obj.reply_text(
            f'{ce("🚫")} Tính năng RÚT TIỀN của bạn đã bị khóa. Vui lòng liên hệ Admin!',
            parse_mode=ParseMode.HTML)
    if check_mt('mt_rut') and uid not in ADMIN_IDS:
        return await msg_obj.reply_text(f'{ce("⚙️")} Hệ thống Rút Tiền đang bảo trì, vui lòng quay lại sau!', parse_mode=ParseMode.HTML)
    if is_total_maintenance() and uid not in ADMIN_IDS:
        await msg_obj.reply_text(f'{ce("⚡")} <b>HỆ THỐNG ĐANG BẢO TRÌ TOÀN BỘ</b>', parse_mode=ParseMode.HTML)
        return
    get_user(uid)
    res = query("SELECT bank, stk, name, balance FROM users WHERE user_id=%s", (uid,))
    if not res or not res[0][0] or not res[0][1]:
        return await msg_obj.reply_text(
            f'{ce("❌")} Bạn chưa liên kết tài khoản ngân hàng.\n'
            f'Hãy dùng lệnh: <code>/lienket [Ngân_hàng] [STK] [Tên]</code>\n\n'
            f'{ce("📌")} <b>MIN RÚT:</b> <code>50,000đ</code>',
            parse_mode=ParseMode.HTML)
    u = res[0]
    if not args:
        return await msg_obj.reply_text(
            f'{ce("💰")} <b>Số dư:</b> <code>{fmt_money(u[3])}đ</code>\n'
            f'{ce("📌")} <b>MIN RÚT:</b> <code>50,000đ</code>\n\n'
            f'{ce("✍️")} Nhập số tiền muốn rút: <code>/rut [số_tiền]</code>',
            parse_mode=ParseMode.HTML)
    try:
        amount = int(args[0])
    except ValueError:
        return await msg_obj.reply_text(f'{ce("❌")} Số tiền không hợp lệ.', parse_mode=ParseMode.HTML)
    if amount < MIN_WITHDRAW:
        return await msg_obj.reply_text(
            f'{ce("❌")} Số tiền rút tối thiểu là <code>{fmt_money(MIN_WITHDRAW)}đ</code>',
            parse_mode=ParseMode.HTML)
    remaining = get_remaining_bet_required(uid)
    if remaining > 0:
        return await msg_obj.reply_text(
            f'{ce("⚠️")} <b>CHƯA ĐỦ ĐIỀU KIỆN RÚT TIỀN!</b>\n\n'
            f'{ce("💰")} Bạn đang có tiền khuyến mãi cần cược đủ <b>x2</b> vòng.\n'
            f'{ce("📊")} <b>Cần cược thêm:</b> <code>{fmt_money(remaining)}đ</code>',
            parse_mode=ParseMode.HTML)
    if sub_money(uid, amount, "Rút tiền"):
        bank, stk, name = u[0], u[1], u[2]
        now_str = get_vietnam_datetime_db()
        query("INSERT INTO withdraw_history (user_id, amount, status, time) VALUES (%s, %s, %s, %s)", (uid, amount, 'pending', now_str))
        keyboard = InlineKeyboardMarkup([[
            btn("Duyệt", "✅", callback_data=f"ok_{uid}_{amount}"),
            btn("Từ chối", "❌", callback_data=f"no_{uid}_{amount}")
        ]])
        for admin_id in ADMIN_IDS:
            try:
                await ctx.bot.send_message(admin_id,
                    f'{ce("🎁")} <b>YÊU CẦU RÚT TIỀN MỚI</b> {ce("🎁")}\n'
                    f'━━━━━━━━━━━━━━━━━━━━━\n'
                    f'{ce("👥")} <b>ID:</b> <code>{uid}</code>\n'
                    f'{ce("💰")} <b>Số tiền:</b> <code>{fmt_money(amount)}đ</code>\n'
                    f'{ce("💳")} <b>Ngân hàng:</b> <code>{html.escape(str(bank))}</code>\n'
                    f'{ce("💰")} <b>STK:</b> <code>{html.escape(str(stk))}</code>\n'
                    f'{ce("👥")} <b>Chủ TK:</b> <code>{html.escape(str(name))}</code>\n'
                    f'{ce("⏰")} <b>Thời gian:</b> <code>{now_str}</code>',
                    reply_markup=keyboard, parse_mode=ParseMode.HTML)
            except Exception as e:
                print(f"Không thể gửi tin nhắn đến admin {admin_id}: {e}")
        await msg_obj.reply_text(
            f'{ce("✅")} <b>GỬI YÊU CẦU RÚT THÀNH CÔNG!</b>\n\n'
            f'{ce("💰")} Số tiền: <code>{fmt_money(amount)}đ</code>\n'
            f'{ce("⏰")} Vui lòng chờ Admin duyệt (1-5 phút).',
            parse_mode=ParseMode.HTML)
    else:
        await msg_obj.reply_text(f'{ce("❌")} Số dư không đủ.', parse_mode=ParseMode.HTML)

async def nap_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    msg_obj = update.effective_message
    if is_banned(uid):
        return
    if is_total_maintenance() and uid not in ADMIN_IDS:
        await msg_obj.reply_text(f'{ce("⚡")} <b>HỆ THỐNG ĐANG BẢO TRÌ TOÀN BỘ</b>', parse_mode=ParseMode.HTML)
        return
    if is_feature_banned(uid, 'nap'):
        return await msg_obj.reply_text(f'{ce("🚫")} Tính năng NẠP TIỀN đã bị khóa!', parse_mode=ParseMode.HTML)
    if check_mt('mt_nap') and uid not in ADMIN_IDS:
        return await msg_obj.reply_text(f'{ce("⚙️")} Nạp Tiền đang bảo trì!', parse_mode=ParseMode.HTML)

    if not ctx.args:
        try:
            qr_url, caption, kb = deposit_menu_content(uid)
            return await msg_obj.reply_photo(photo=qr_url, caption=caption, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception as e:
            print(f"nap menu lỗi: {e}")
            return await msg_obj.reply_text(
                f'{ce("❌")} Cú pháp: <code>/nap [số_tiền]</code>\nVD: <code>/nap 50000</code>',
                parse_mode=ParseMode.HTML
            )
    try:
        arg = ctx.args[0].lower().replace(",", "").replace(".", "").replace("đ", "").strip()
        if arg.endswith("m"):
            amount = int(float(arg.replace("m", "")) * 1000000)
        elif arg.endswith("k"):
            amount = int(float(arg.replace("k", "")) * 1000)
        else:
            amount = int(arg)

        if amount < 10000:
            return await msg_obj.reply_text(f'{ce("❌")} Số tiền nạp tối thiểu là 10,000đ!', parse_mode=ParseMode.HTML)

        qr_url, caption = get_deposit_info(uid, amount)
        kb = InlineKeyboardMarkup([
            [btn(f"Đã Thanh Toán", "🔄", callback_data=f"paid_dep_{amount}")],
            [btn("Hỗ Trợ", "🔔", callback_data="dep_support")]
        ])
        await msg_obj.reply_photo(photo=qr_url, caption=caption, reply_markup=kb, parse_mode=ParseMode.HTML)
    except ValueError:
        await msg_obj.reply_text(f'{ce("❌")} Số tiền không hợp lệ! VD: <code>/nap 50000</code>', parse_mode=ParseMode.HTML)

async def nhap_code(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_banned(uid):
        return
    if not ctx.args:
        await update.effective_message.reply_text(
            f'{ce("❌")} Vui lòng nhập kèm mã. VD: <code>/code ABC123</code>',
            parse_mode=ParseMode.HTML)
        return

    code_str = ctx.args[0].strip().upper()

    # [MỚI] Giftcode JAV88-xxx (5 loại)
    if await redeem_giftcode(update, uid, code_str):
        return

    codenap_data = query(
        "SELECT reward, required_amount, wager, expiry, used FROM codenap WHERE code=%s",
        (code_str,)
    )
    if codenap_data:
        reward, required_amount, wager, expiry_str, used = codenap_data[0]
        if used:
            return await update.effective_message.reply_text(
                f'{ce("❌")} Code này đã được sử dụng!',
                parse_mode=ParseMode.HTML)

        try:
            expiry_time = datetime.strptime(expiry_str, "%d/%m/%Y %H:%M")
            expiry_time = VIETNAM_TZ.localize(expiry_time)
            if get_vietnam_time() > expiry_time:
                return await update.effective_message.reply_text(
                    f'{ce("❌")} Code này đã hết hạn sử dụng!',
                    parse_mode=ParseMode.HTML)
        except:
            pass

        total_deposit = query(
            "SELECT SUM(amount) FROM deposit_history WHERE user_id=%s AND status='success'",
            (uid,)
        )
        total_deposit = (total_deposit[0][0] or 0) if total_deposit else 0
        if total_deposit < required_amount:
            return await update.effective_message.reply_text(
                f'{ce("⚠️")} <b>CHƯA ĐỦ ĐIỀU KIỆN!</b>\n\n'
                f'{ce("💳")} Bạn cần nạp đủ <code>{fmt_money(required_amount)}đ</code>\n'
                f'{ce("💰")} Bạn đã nạp: <code>{fmt_money(total_deposit)}đ</code>\n'
                f'{ce("📌")} Còn thiếu: <code>{fmt_money(required_amount - total_deposit)}đ</code>',
                parse_mode=ParseMode.HTML)

        query("UPDATE codenap SET used=1 WHERE code=%s", (code_str,))
        add_money(uid, reward, f"Code nạp: {code_str}")

        required_bet = reward * wager
        now_str = get_vietnam_datetime_db()
        query("DELETE FROM user_bonus WHERE user_id=%s", (uid,))
        query(
            "INSERT INTO user_bonus (user_id, bonus_amount, required_bet, current_bet, created_at) "
            "VALUES (%s, %s, %s, 0, %s)",
            (uid, reward, required_bet, now_str)
        )

        await update.effective_message.reply_text(
            f'{ce("🎉")} <b>NHẬN CODE NẠP THÀNH CÔNG!</b> {ce("🎉")}\n'
            f'┏━━━━━━━━━━━━━━━━━━━━━━━━━\n'
            f'┃ {ce("🔑")} <b>Mã code:</b> <code>{code_str}</code>\n'
            f'┃ {ce("💰")} <b>Đã nhận:</b> <code>+{fmt_money(reward)}đ</code>\n'
            f'┃ {ce("🎯")} <b>Vòng cược yêu cầu:</b> <code>x{wager}</code>\n'
            f'┃ {ce("📊")} <b>Tổng cược cần:</b> <code>{fmt_money(required_bet)}đ</code>\n'
            f'┗━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'
            f'{ce("💰")} Số dư hiện tại: <code>{fmt_money(get_balance(uid))}đ</code>',
            parse_mode=ParseMode.HTML
        )
        return

    today = get_vietnam_date()
    code_count = query("SELECT COUNT(*) FROM code_usage WHERE user_id=%s AND used_date=%s", (uid, today))
    if code_count and code_count[0][0] >= 3:
        await update.effective_message.reply_text(
            f'{ce("🚫")} <b>GIỚI HẠN CODE HÔM NAY!</b>\n\n'
            f'Bạn chỉ có thể nhập tối đa <b>3 CODE/ngày</b>.',
            parse_mode=ParseMode.HTML)
        return

    data = query("SELECT * FROM codes WHERE code=%s", (code_str,))
    if not data:
        await update.effective_message.reply_text(f'{ce("❌")} Mã quà tặng không tồn tại.', parse_mode=ParseMode.HTML)
        return
    reward, uses = data[0][1], data[0][2]
    if uses <= 0:
        await update.effective_message.reply_text(f'{ce("❌")} Mã quà tặng này đã hết lượt sử dụng.', parse_mode=ParseMode.HTML)
        return
    query("INSERT INTO code_usage VALUES(%s, %s, %s) ON CONFLICT DO NOTHING", (uid, code_str, today))
    add_money(uid, reward, f"Code: {code_str}")
    query("UPDATE codes SET uses=uses-1 WHERE code=%s", (code_str,))
    used_today = code_count[0][0] + 1 if code_count else 1
    remaining = 3 - used_today
    await update.effective_message.reply_text(
        f'{ce("🎉")} <b>NHẬN QUÀ THÀNH CÔNG!</b>\n\n'
        f'{ce("💰")} Bạn nhận được: <code>+{fmt_money(reward)}đ</code>\n'
        f'{ce("📊")} Hôm nay còn: <code>{remaining}/3</code> lượt nhập code.',
        parse_mode=ParseMode.HTML)

async def history_pro(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    data = query("SELECT amount, note, time FROM history WHERE user_id=%s ORDER BY id DESC LIMIT 20", (uid,))
    title_icon = ce_id("5210956306952758910")
    clock_icon = ce_id("5386367538735104399")
    if not data:
        await update.effective_message.reply_text(f'{title_icon} <b>LỊCH SỬ CHI TIẾT:</b>\n━━━━━━━━━━━━━━━━━━━━━\n{ce("📥")} Lịch sử trống.', parse_mode=ParseMode.HTML)
    else:
        msg = f'{title_icon} <b>LỊCH SỬ CHI TIẾT:</b>\n'
        msg += f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
        for d in data:
            icon = ce("✔️") if d[0] > 0 else ce("❌")
            msg += f'{icon} <code>{fmt_money(abs(d[0]))}đ</code> | {html.escape(d[1])}\n'
            msg += f'     <i>{clock_icon} {d[2]}</i>\n'
        msg += f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━'
        if len(msg) > 4000:
            for x in range(0, len(msg), 4000):
                await update.effective_message.reply_text(msg[x:x+4000], parse_mode=ParseMode.HTML)
        else:
            await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)

async def check_bet_progress_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_banned(uid):
        return
    status = get_bet_progress_status(uid)
    if not status:
        await update.effective_message.reply_text(
            f'{ce("📊")} <b>KHÔNG CÓ KHUYẾN MÃI NÀO ĐANG HOẠT ĐỘNG</b>\n'
            f'━━━━━━━━━━━━━━━━━━━━━\n'
            f'{ce("💰")} Bạn hiện không có tiền khuyến mãi cần hoàn thành cược.',
            parse_mode=ParseMode.HTML)
        return
    percent = min(status['percent'], 100)
    bar_length = 20
    filled = int(bar_length * percent / 100)
    bar = "█" * filled + "░" * (bar_length - filled)
    message = (
        f'{ce("📊")} <b>TIẾN ĐỘ HOÀN THÀNH CƯỢC</b> {ce("📊")}\n'
        f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("🎁")} <b>Tiền khuyến mãi đã nhận:</b> <code>+{fmt_money(status["bonus_amount"])}đ</code>\n'
        f'{ce("🎯")} <b>Yêu cầu cược:</b> <code>{fmt_money(status["required_bet"])}đ</code>\n'
        f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("📈")} <b>Tiến độ:</b>\n'
        f'<code>{bar}</code> <code>{percent:.1f}%</code>\n'
        f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("✅")} <b>Đã cược:</b> <code>{fmt_money(status["current_bet"])}đ</code>\n'
        f'{ce("⚠️")} <b>Cần cược thêm:</b> <code>{fmt_money(max(0, status["remaining"]))}đ</code>\n'
    )
    if status['is_completed']:
        message += f'{ce("🎉")} <b>CHÚC MỪNG! BẠN ĐÃ HOÀN THÀNH!</b> {ce("🎉")}'
    else:
        message += f'{ce("🔥")} <b>CỐ GẮNG LÊN!</b>'
    await update.effective_message.reply_text(message, parse_mode=ParseMode.HTML)


# ================= XỬ LÝ MENU CHÍNH =================
async def handle(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid, txt = update.effective_user.id, update.effective_message.text
    if not txt or is_banned(uid):
        return

    if uid in pending_inputs:
        handled = await handle_pending_input(update, ctx)
        if handled:
            return

    if is_total_maintenance() and uid not in ADMIN_IDS:
        await update.effective_message.reply_text(f'{ce("⚡")} <b>HỆ THỐNG ĐANG BẢO TRÌ TOÀN BỘ</b>', parse_mode=ParseMode.HTML)
        return
    if is_system_maintenance() and uid not in ADMIN_IDS:
        await update.effective_message.reply_text(f'{ce("⚡")} <b>HỆ THỐNG ĐANG BẢO TRÌ</b>', parse_mode=ParseMode.HTML)
        return
    user_reply = update.effective_message
    key = re.sub(r'^[^\w]+', '', txt).strip()

    # [MỚI] Người dùng gửi thẳng mã giftcode trong chat riêng
    if update.effective_chat.type == "private" and re.fullmatch(r'JAV88-[A-Z0-9]+(?:-[A-Z0-9]+)?', txt.strip().upper()):
        code_in = txt.strip().upper()
        if await redeem_giftcode(update, uid, code_in):
            return
        return await user_reply.reply_text(f'{ce("❌")} Mã quà tặng không tồn tại.', parse_mode=ParseMode.HTML)

    # 1. TÀI KHOẢN
    if key == "TÀI KHOẢN":
        get_user(uid)
        res = query("SELECT balance, bank, stk, name, refs, total_bet FROM users WHERE user_id=%s", (uid,))
        u = res[0] if res else (0, None, None, None, 0, 0)
        vip_name, _ = get_vip_info(u[5] or 0)

        today_str = get_vietnam_time().strftime("%d/%m/%Y")
        nap_res = query("SELECT SUM(amount) FROM deposit_history WHERE user_id=%s AND status='success'", (uid,))
        tong_nap = nap_res[0][0] if nap_res and nap_res[0][0] else 0
        rut_res = query("SELECT SUM(amount) FROM withdraw_history WHERE user_id=%s AND status='success'", (uid,))
        tong_rut = rut_res[0][0] if rut_res and rut_res[0][0] else 0
        cuoc_hom_nay, cuoc_tuan = get_bet_stats(uid)

        kb = InlineKeyboardMarkup([
            [btn("LS nạp", "📈", callback_data="acc_ls_nap"), btn("LS rút", "📉", callback_data="acc_ls_rut")],
            [btn("LS chơi", "🎮", callback_data="acc_ls_choi"), btn("LS Room TX", "🎲", callback_data="acc_ls_tx")],
            [btn("Nhập giftcode", "🎁", callback_data="acc_nhap_gift"), btn("Mua giftcode", "🛒", callback_data="acc_mua_gift")],
            [btn("Nhận thưởng", "🎉", callback_data="acc_nhan_thuong"), btn("Chuyển tiền", "💸", callback_data="acc_chuyen_tien")],
            [btn("VIP", "👑", callback_data="acc_vip"), btn("Fan cứng +30k", "🔥", callback_data="acc_fan_cung")],
            [btn("Tích lũy nạp", "💎", callback_data="acc_tich_luy"), btn("Kết Sát", "🔐", callback_data="acc_ket_sat")],
            [btn("Hỗ trợ", "🆘", url="https://tply.me/echcutodz")]
        ])

        msg = (
            f'{ce("✅")} ID: <code>{uid}</code>\n'
            f'{ce("💰")} Số dư: <code>{fmt_money(u[0])}</code>\n'
            f'{ce("👑")} Cấp VIP: <code>{vip_name}</code>\n\n'
            f'{ce("📊")} <b>THỐNG KÊ</b>\n'
            f'• Cược hôm nay: {fmt_money(cuoc_hom_nay)}\n'
            f'• Cược tuần này: {fmt_money(cuoc_tuan)}\n'
            f'• Tổng cược: {fmt_money(u[5] or 0)}\n'
            f'• Tổng nạp: {fmt_money(tong_nap)}\n'
            f'• Tổng rút: {fmt_money(tong_rut)}\n\n'
            f'{ce("🗓")} {today_str}\n'
            f'• Chuỗi thắng: 0\n'
            f'• Chuỗi thua: 0\n'
        )
        return await user_reply.reply_text(msg, reply_markup=kb, parse_mode=ParseMode.HTML)

    if key == "DANH SÁCH GAME":
        return await user_reply.reply_text(GAME_LIST_TEXT, reply_markup=game_list_kb(), parse_mode=ParseMode.HTML)

    if key == "NẠP TIỀN":
        return await nap_cmd(update, ctx)

    if key == "RÚT TIỀN":
        return await rut(update, ctx)

    # 2. GIỚI THIỆU
    if key == "GIỚI THIỆU":
        ref_link = f"https://t.me/{BOT_USERNAME}?start={uid}"
        res_ref = query("SELECT refs FROM users WHERE user_id=%s", (uid,))
        so_de_tu = res_ref[0][0] if res_ref else 0

        kb = InlineKeyboardMarkup([
            [btn("Nhận hoa hồng", "🎁", callback_data="ref_nhan_hh")],
            [btn("Chia sẻ ngay", "✉️", url=f"https://t.me/share/url?url={ref_link}&text=Tham%20gia%20ngay!")],
            [btn("Rương đệ tử 28-58k", "🎁", callback_data="ref_ruong")]
        ])

        msg = (
            f'{ce("🔗")} Link mời: {ref_link}\n\n'
            f'{ce("🌷")} Hoa hồng đệ tử: {ce("🐺")} 2% tiền cược thua đệ (không HH nạp)\n\n'
            f'{ce("👥")} Số đệ tử: {so_de_tu} | Hợp lệ event: 0\n\n'
            f'Hoa hồng hôm nay: 0\n'
            f'Tổng hoa hồng: 0\n'
            f'{ce("🎁")} Có thể nhận: 0\n'
            f'• Nhận tối thiểu: 20.000\n'
        )
        return await user_reply.reply_text(msg, reply_markup=kb, parse_mode=ParseMode.HTML)

    # 3. ĐUA TOP
    if key == "ĐUA TOP":
        kb = InlineKeyboardMarkup([
            [btn("Top cược ngày", "🏆", callback_data="top_cuoc_ngay")],
            [btn("Top đua đây (thắng/thua)", "🎖", callback_data="top_thang_thua")]
        ])
        return await user_reply.reply_text(f'{ce("🍭")} <b>ĐUA TOP</b>\nVui lòng chọn bảng xếp hạng:', reply_markup=kb, parse_mode=ParseMode.HTML)

    # 4. EVENT
    if key == "EVENT":
        kb = InlineKeyboardMarkup([
            [btn("Hoàn cược ngày", "📈", callback_data="ev_hc_ngay"), btn("Hoàn cược tuần", "📉", callback_data="ev_hc_tuan")],
            [btn("Hoàn thua ngày", "💸", callback_data="ev_ht_ngay"), btn("Hoàn thua tuần", "💸", callback_data="ev_ht_tuan")],
            [btn("Nhận thưởng VIP", "👑", callback_data="ev_nhan_vip")],
            [btn("Tương tác nhóm +50k", "🎁", callback_data="ev_tuong_tac")],
            [btn("Mời đệ tử", "🧑‍🤝‍🧑", callback_data="ev_moi_de_tu")]
        ])
        return await user_reply.reply_text(
            f'{ce("🎁")} <b>TRUNG TÂM EVENT ET88</b>\nChọn chương trình bạn muốn xem hoặc nhận thưởng:',
            reply_markup=kb, parse_mode=ParseMode.HTML)

    # 5. LỆNH
    if key == "LỆNH":
        msg = (
            f'{ce("👀")} <b>DANH SÁCH LỆNH</b>\n\n'
            f'<b>Game:</b>\n'
            f'• <code>T [tiền]</code> / <code>X [tiền]</code> / <code>C [tiền]</code> / <code>L [tiền]</code> (Cược Room TX)\n'
            f'• <code>/sd</code> - Xem số dư\n'
            f'• <code>/nap [tiền]</code> - Nạp tiền\n'
            f'• <code>/rut [tiền]</code> - Rút tiền\n'
            f'• <code>/chuyen [ID] [tiền]</code> - Chuyển tiền\n'
            f'• <code>/code [mã]</code> - Nhập giftcode\n'
            f'• <code>/muagift [SL] [giá]</code> - Mua giftcode\n'
            f'• <code>/doidiemvip [điểm]</code> - Đổi điểm VIP\n'
            f'• <code>/lienket [Bank] [STK] [Tên]</code> - Liên kết bank\n'
            f'• <code>/lschoi</code> - Lịch sử chơi\n'
        )
        return await user_reply.reply_text(msg, parse_mode=ParseMode.HTML)

    # Xúc xắc đơn (XXC, XXL, XXT, XXX, D1-D6)
    if len(txt.split()) == 2:
        parts = txt.split()
        code, amt_str = parts[0].upper(), parts[1]
        if code in ["XXC", "XXL", "XXX", "XXT", "D1", "D2", "D3", "D4", "D5", "D6"]:
            if check_mt('mt_xucxac_don') and uid not in ADMIN_IDS:
                return await update.effective_message.reply_text(f'{ce("⚙️")} Game Xúc Xắc Đơn đang bảo trì!', parse_mode=ParseMode.HTML)
            try:
                amt = get_balance(uid) if amt_str.lower() in ["max", "all"] else int(amt_str)
                return await play_xucxac_don(update, ctx, code, amt)
            except ValueError:
                pass

    parts = txt.strip().split()
    if len(parts) == 2:
        anon_cmd = parts[0].upper()
        anon_map = {
            "TT": "tai", "T": "tai",
            "XX": "xiu", "X": "xiu",
            "CC": "chan", "C": "chan",
            "LL": "le", "L": "le",
            "TL": "tl", "TC": "tc", "XL": "xl", "XC": "xc"
        }
        if anon_cmd in anon_map:
            choice = anon_map[anon_cmd]
            arg = parts[1].lower()
            if arg in ["max", "all"]:
                amount = get_balance(uid)
                if amount < 1000:
                    return await update.effective_message.reply_text(
                        f'{ce("❌")} Số dư không đủ (tối thiểu 1,000đ)!',
                        parse_mode=ParseMode.HTML)
            else:
                try:
                    amount = int(arg)
                except ValueError:
                    return await update.effective_message.reply_text(
                        f'{ce("❌")} Số tiền không hợp lệ! VD: <code>T 5000</code> hoặc <code>t max</code>',
                        parse_mode=ParseMode.HTML)

            if not GROUP_IDS:
                return await update.effective_message.reply_text(
                    f'{ce("❌")} Chưa có nhóm game nào được cấu hình!',
                    parse_mode=ParseMode.HTML)
            target_group = GROUP_IDS[0]
            success, message = await place_anonymous_bet(ctx.bot, uid, target_group, choice, amount)
            return await update.effective_message.reply_text(message, parse_mode=ParseMode.HTML)

async def main_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    if update.effective_chat.type == "private":
        text = update.effective_message.text
        if text and not is_banned(uid):
            parts = text.strip().split()
            if len(parts) >= 2:
                cmd = parts[0].upper()
                anon_map = {
                    "TT": "tai", "T": "tai",
                    "XX": "xiu", "X": "xiu",
                    "CC": "chan", "C": "chan",
                    "LL": "le", "L": "le",
                    "TL": "tl", "TC": "tc", "XL": "xl", "XC": "xc"
                }
                if cmd in anon_map:
                    choice = anon_map[cmd]
                    arg = parts[1].lower()
                    try:
                        amount = get_balance(uid) if arg in ["max", "all"] else int(arg)
                        if amount >= 1000:
                            success, msg = await place_anonymous_bet(ctx.bot, uid, GROUP_IDS[0], choice, amount)
                            await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)
                            return
                    except: pass

                if cmd == "D1" and len(parts) == 3:
                    face = parts[1]
                    if face in "123456" and len(face) == 1:
                        try:
                            amount = get_balance(uid) if parts[2].lower() in ["max", "all"] else int(parts[2])
                            if amount >= 1000:
                                success, msg = await place_anonymous_bet(ctx.bot, uid, GROUP_IDS[0], f"d1_{face}", amount)
                                await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)
                                return
                        except: pass
                if cmd == "D2" and len(parts) == 3:
                    faces = parts[1]
                    if len(faces) == 2 and all(c in "123456" for c in faces):
                        try:
                            amount = get_balance(uid) if parts[2].lower() in ["max", "all"] else int(parts[2])
                            if amount >= 1000:
                                success, msg = await place_anonymous_bet(ctx.bot, uid, GROUP_IDS[0], f"d2_{faces}", amount)
                                await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)
                                return
                        except: pass
                if cmd == "D3" and len(parts) == 3:
                    try:
                        sum_val = int(parts[1])
                        if 3 <= sum_val <= 18:
                            amount = get_balance(uid) if parts[2].lower() in ["max", "all"] else int(parts[2])
                            if amount >= 1000:
                                success, msg = await place_anonymous_bet(ctx.bot, uid, GROUP_IDS[0], f"d3_{sum_val}", amount)
                                await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)
                                return
                    except: pass

    if is_total_maintenance() and uid not in ADMIN_IDS:
        await update.effective_message.reply_text(f'{ce("⚡")} <b>HỆ THỐNG ĐANG BẢO TRÌ TOÀN BỘ</b>', parse_mode=ParseMode.HTML)
        return
    await handle(update, ctx)

class FakeCtx:
    def __init__(self, bot, args, user_data, chat_data, message):
        self.bot = bot
        self.args = args
        self.user_data = user_data
        self.chat_data = chat_data
        self.message = message

async def handle_group_message(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type == "private":
        await main_handler(update, ctx)
        return
    if is_total_maintenance() and update.effective_user.id not in ADMIN_IDS:
        return
    await track_interaction(update, ctx)
    text = update.effective_message.text
    if not text:
        return
    parts = text.strip().split()
    if not parts:
        return
    command = parts[0].lower()

    fake_ctx = FakeCtx(ctx.bot, parts[1:], ctx.user_data, ctx.chat_data, update.effective_message)

    bet_commands = {
        "t": "tai", "tai": "tai",
        "x": "xiu", "xiu": "xiu",
        "c": "chan", "chan": "chan",
        "l": "le", "le": "le",
        "tl": "tl", "tc": "tc", "xl": "xl", "xc": "xc",
        "a1": "a1", "a2": "a2", "a3": "a3", "a4": "a4", "a5": "a5", "a6": "a6",
    }

    def parse_amt(s):
        s = s.lower().replace(",", "").replace(".", "")
        if s in ["max", "all"]:
            return get_balance(update.effective_user.id)
        if s.endswith("k"):
            return int(float(s[:-1]) * 1000)
        if s.endswith("m"):
            return int(float(s[:-1]) * 1000000)
        return int(s)

    if command in bet_commands:
        choice = bet_commands[command]
        await bet_group_handler(update, fake_ctx, choice)
        return

    if command == "d1" and len(parts) >= 3:
        face = parts[1]
        if face in "123456" and len(face) == 1:
            try:
                amt = parse_amt(parts[2])
                await bet_group_handler(update, fake_ctx, f"d1_{face}", amt)
                return
            except: pass

    if command == "d2" and len(parts) >= 3:
        faces = parts[1]
        if len(faces) == 2 and all(c in "123456" for c in faces):
            try:
                amt = parse_amt(parts[2])
                await bet_group_handler(update, fake_ctx, f"d2_{faces}", amt)
                return
            except: pass

    if command == "d3" and len(parts) >= 3:
        try:
            sum_val = int(parts[1])
            if 3 <= sum_val <= 18:
                amt = parse_amt(parts[2])
                await bet_group_handler(update, fake_ctx, f"d3_{sum_val}", amt)
                return
        except: pass

    if command in ["tt", "xx", "cc", "ll"]:
        await update.effective_message.reply_text(
            f'{ce("🥷")} <b>CƯỢC ẨN DANH</b>\n\n'
            f'Vui lòng <b>nhắn riêng cho bot</b> để đặt cược ẩn danh!\n'
            f'Cú pháp: <code>{command.upper()} [số_tiền]</code>\n'
            f'VD: <code>{command.upper()} 5000</code>',
            parse_mode=ParseMode.HTML)
        return

    await main_handler(update, ctx)

def parse_duration(s):
    s = s.lower().strip()
    if s.endswith("n"):
        try:
            return int(s[:-1]) * 24 * 60
        except:
            return None
    if s.endswith("h"):
        try:
            return int(s[:-1]) * 60
        except:
            return None
    if s.endswith("p"):
        try:
            return int(s[:-1])
        except:
            return None
    return None

# ================= ADMIN COMMANDS =================
@admin_only
async def naptien_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        target_id = int(ctx.args[0])
        amount = int(ctx.args[1])
        if amount < 10000:
            await update.effective_message.reply_text(f'{ce("❌")} Số tiền nạp tối thiểu là <code>10,000đ</code>!', parse_mode=ParseMode.HTML)
            return
        now_str = get_vietnam_datetime_db()
        get_user(target_id)
        query("INSERT INTO deposit_history (user_id, amount, admin_id, status, time) VALUES (%s, %s, %s, %s, %s)", (target_id, amount, update.effective_user.id, 'success', now_str))
        add_money(target_id, amount, f"Nạp tiền +{amount:,}đ")
        try:
            await ctx.bot.send_message(chat_id=LOG_GROUP_ID,
                text=f'{ce("✅")} <b>THÔNG BÁO NẠP TIỀN</b>\n{ce("👥")} ID: <code>{target_id}</code>\n{ce("💰")} Số tiền: <code>+{fmt_money(amount)}đ</code>\n{ce("👑")} Admin: <code>{update.effective_user.id}</code>',
                parse_mode=ParseMode.HTML)
        except: pass

        bonus_amount = int(amount * 0.10)
        if bonus_amount > 0:
            required_bet = bonus_amount * 2
            keyboard = InlineKeyboardMarkup([[
                btn("NHẬN KHUYẾN MÃI", "🎁", callback_data=f"accept_bonus_{target_id}_{bonus_amount}_{required_bet}"),
                btn("TỪ CHỐI", "❌", callback_data=f"reject_bonus_{target_id}")
            ]])
            try:
                await ctx.bot.send_message(target_id,
                    f'{ce("✅")} <b>NẠP TIỀN THÀNH CÔNG!</b>\n\n'
                    f'{ce("💰")} Số tiền nạp: <code>+{fmt_money(amount)}đ</code>\n'
                    f'{ce("💎")} Số dư hiện tại: <code>{fmt_money(get_balance(target_id))}đ</code>\n\n'
                    f'{ce("🎁")} <b>BẠN CÓ MUỐN NHẬN THÊM KHUYẾN MÃI?</b>\n'
                    f'━━━━━━━━━━━━━━━━━━━━━\n'
                    f'{ce("✨")} <b>Thưởng nạp 10%:</b> <code>+{fmt_money(bonus_amount)}đ</code>\n'
                    f'{ce("🎯")} <b>Yêu cầu cược:</b> x2 vòng (<code>{fmt_money(required_bet)}đ</code>)\n'
                    f'{ce("⚠️")} <b>Lưu ý:</b> Sau khi nhận thưởng phải x2 vòng cược tổng số dư tài khoản\n'
                    f'━━━━━━━━━━━━━━━━━━━━━\n\n'
                    f'Vui lòng chọn bên dưới:',
                    reply_markup=keyboard, parse_mode=ParseMode.HTML)
            except Exception as e: pass
        else:
            try:
                bill = (
                    f'{ce("✅")} <b>NẠP TIỀN THÀNH CÔNG</b>\n'
                    f'━━━━━━━━━━━━━━━━━━━━━\n'
                    f'{ce("📥")} <b>Số tiền:</b> <code>+{fmt_money(amount)}đ</code>\n'
                    f'{ce("⏰")} <b>Thời gian:</b> {now_str}\n'
                    f'━━━━━━━━━━━━━━━━━━━━━\n'
                    f'{ce("💰")} Số dư hiện tại: <code>{fmt_money(get_balance(target_id))}đ</code>'
                )
                await ctx.bot.send_message(chat_id=target_id, text=bill, parse_mode=ParseMode.HTML)
            except Exception as e: pass
        await update.effective_message.reply_text(
            f'{ce("✅")} <b>NẠP TIỀN THÀNH CÔNG</b>\n\n'
            f'{ce("👥")} ID: <code>{target_id}</code>\n'
            f'{ce("💰")} Số tiền: <code>+{fmt_money(amount)}đ</code>',
            parse_mode=ParseMode.HTML)
    except (IndexError, ValueError):
        await update.effective_message.reply_text(
            f'{ce("❌")} Cú pháp: <code>/naptien [ID] [Số tiền]</code>\n{ce("📌")} Min nạp: <code>10,000đ</code>',
            parse_mode=ParseMode.HTML)

@admin_only
async def add(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        uid, amt = int(ctx.args[0]), int(ctx.args[1])
        add_money(uid, amt, "Admin cộng tiền")
        await update.effective_message.reply_text(f'{ce("✅")} Đã cộng <code>{fmt_money(amt)}đ</code> cho ID <code>{uid}</code>', parse_mode=ParseMode.HTML)
    except (IndexError, ValueError):
        await update.effective_message.reply_text(f'{ce("❌")} Cú pháp: <code>/add [ID] [số tiền]</code>', parse_mode=ParseMode.HTML)

@admin_only
async def sub(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        uid, amt = int(ctx.args[0]), int(ctx.args[1])
        if sub_money(uid, amt, "Admin trừ tiền"):
            await update.effective_message.reply_text(f'{ce("✅")} Đã trừ <code>{fmt_money(amt)}đ</code> của ID <code>{uid}</code>', parse_mode=ParseMode.HTML)
        else:
            await update.effective_message.reply_text(f'{ce("❌")} Số dư của ID <code>{uid}</code> không đủ để trừ!', parse_mode=ParseMode.HTML)
    except (IndexError, ValueError):
        await update.effective_message.reply_text(f'{ce("❌")} Cú pháp: <code>/sub [ID] [số tiền]</code>', parse_mode=ParseMode.HTML)

@admin_only
async def ban(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        uid = int(ctx.args[0])
        query("INSERT INTO banned(user_id) VALUES(%s) ON CONFLICT (user_id) DO NOTHING", (uid,))
        await update.effective_message.reply_text(f'{ce("🚫")} Đã chặn người dùng <code>{uid}</code>', parse_mode=ParseMode.HTML)
    except (IndexError, ValueError):
        await update.effective_message.reply_text(f'{ce("❌")} Cú pháp: <code>/ban [ID]</code>', parse_mode=ParseMode.HTML)

@admin_only
async def unban(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        uid = int(ctx.args[0])
        query("DELETE FROM banned WHERE user_id=%s", (uid,))
        await update.effective_message.reply_text(f'{ce("✅")} Đã bỏ chặn người dùng <code>{uid}</code>', parse_mode=ParseMode.HTML)
    except (IndexError, ValueError):
        await update.effective_message.reply_text(f'{ce("❌")} Cú pháp: <code>/unban [ID]</code>', parse_mode=ParseMode.HTML)

@admin_only
async def stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    res = query("SELECT COUNT(*) FROM users")
    total = res[0][0] if res else 0
    await update.effective_message.reply_text(
        f'{ce("📊")} <b>THỐNG KÊ:</b>\n\n{ce("👥")} Tổng số người dùng: <code>{total}</code>',
        parse_mode=ParseMode.HTML)

@admin_only
async def all_user(update: Update, ctx: ContextTypes.DEFAULT_TYPE, page=0):
    limit = 20
    offset = page * limit
    users = query("SELECT user_id, balance FROM users ORDER BY user_id DESC LIMIT %s OFFSET %s", (limit, offset))
    res_total = query("SELECT COUNT(*) FROM users")
    total_users = res_total[0][0] if res_total else 0
    total_pages = max(1, (total_users + limit - 1) // limit)
    if not users:
        return await update.effective_message.reply_text(f'Chưa có người dùng nào.', parse_mode=ParseMode.HTML)
    kb = []
    for u in users:
        u_id, bal = u[0], u[1]
        status = "🚫" if is_banned(u_id) else "🟢"
        kb.append([btn(f"ID: {u_id} | {bal:,}đ", "🚫" if status == "🚫" else "✅", callback_data=f"adm_manage_{u_id}_{page}")])
    nav_buttons = []
    if page > 0:
        nav_buttons.append(btn("Trước", "⬅️", callback_data=f"adm_page_{page-1}"))
    nav_buttons.append(btn(f"Trang {page+1}/{total_pages}", "📍", callback_data="none"))
    if (page + 1) < total_pages:
        nav_buttons.append(btn("Sau", "➡️", callback_data=f"adm_page_{page+1}"))
    kb.append(nav_buttons)
    kb.append([btn("ĐÓNG BẢNG", "❌", callback_data="close_admin")])
    text = f'{ce("👥")} <b>DANH SÁCH NGƯỜI DÙNG</b> (Tổng: {total_users})\nBấm vào User để xem chi tiết:'
    if update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)

@admin_only
async def admin_info(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        target_id = int(ctx.args[0])
        res = query("SELECT balance, refs, bank, stk, name, last_checkin, total_bet FROM users WHERE user_id=%s", (target_id,))
        if not res:
            return await update.effective_message.reply_text(f'{ce("❌")} Không tìm thấy người dùng này.', parse_mode=ParseMode.HTML)
        u = res[0]
        msg = (
            f'{ce("📜")} <b>THÔNG TIN CHI TIẾT USER</b> <code>{target_id}</code>\n'
            f'━━━━━━━━━━━━━━━━━━━━━\n'
            f'{ce("💰")} Số dư: <code>{fmt_money(u[0])}đ</code>\n'
            f'{ce("📊")} Tổng cược: <code>{fmt_money(u[6] or 0)}đ</code>\n'
            f'{ce("👥")} Số người mời: <code>{u[1]}</code>\n'
            f'{ce("💳")} Ngân hàng: <code>{html.escape(u[2] or "Chưa cập nhật")}</code>\n'
            f'{ce("💰")} STK: <code>{html.escape(u[3] or "Chưa cập nhật")}</code>\n'
            f'{ce("👥")} Tên: <code>{html.escape(u[4] or "Chưa cập nhật")}</code>\n'
            f'━━━━━━━━━━━━━━━━━━━━━'
        )
        await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)
    except (IndexError, ValueError):
        await update.effective_message.reply_text(f'{ce("❌")} Cú pháp: <code>/info [ID]</code>', parse_mode=ParseMode.HTML)

@admin_only
async def history_all_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    data = query("SELECT user_id, amount, note FROM history ORDER BY id DESC LIMIT 50")
    msg = f'{ce("📊")} <b>LỊCH SỬ TOÀN HỆ THỐNG:</b>\n\n'
    if data:
        for d in data:
            msg += f'{ce("👥")} <code>{d[0]}</code> | <code>{fmt_money(d[1])}đ</code> | {html.escape(d[2])}\n'
    if len(msg) > 4000:
        for x in range(0, len(msg), 4000):
            await update.effective_message.reply_text(msg[x:x+4000], parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)

@admin_only
async def broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        return await update.effective_message.reply_text(f'{ce("❌")} Cú pháp: <code>/send [nội dung]</code>', parse_mode=ParseMode.HTML)
    msg_to_send = " ".join(ctx.args)
    users = query("SELECT user_id FROM users") or []
    sent, failed = 0, 0
    status_msg = await update.effective_message.reply_text(f'{ce("🚀")} Đang gửi tới {len(users)} người...', parse_mode=ParseMode.HTML)
    for user in users:
        try:
            await ctx.bot.send_message(chat_id=user[0],
                text=f'{ce("🔔")} <b>THÔNG BÁO MỚI</b>\n\n{html.escape(msg_to_send)}',
                parse_mode=ParseMode.HTML)
            sent += 1
            if sent % 20 == 0:
                await asyncio.sleep(1)
        except: failed += 1
    await status_msg.edit_text(
        f'{ce("✅")} <b>HOÀN THÀNH</b>\n\n'
        f'{ce("📊")} Thành công: <code>{sent}</code>\n'
        f'{ce("❌")} Thất bại: <code>{failed}</code>',
        parse_mode=ParseMode.HTML)

@admin_only
async def reply_user(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        uid = int(ctx.args[0])
        msg_reply = " ".join(ctx.args[1:])
        await ctx.bot.send_message(chat_id=uid,
            text=f'{ce("✍️")} <b>PHẢN HỒI TỪ ADMIN:</b>\n\n{html.escape(msg_reply)}',
            parse_mode=ParseMode.HTML)
        await update.effective_message.reply_text(f'{ce("✅")} Đã gửi phản hồi tới <code>{uid}</code>', parse_mode=ParseMode.HTML)
    except:
        await update.effective_message.reply_text(f'{ce("❌")} Cú pháp: <code>/rep [ID] [Nội dung]</code>', parse_mode=ParseMode.HTML)

@admin_only
async def check_user_history(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        uid = int(ctx.args[0])
        data = query("SELECT amount, note, time FROM history WHERE user_id=%s ORDER BY id DESC LIMIT 100", (uid,))
        if not data:
            await update.effective_message.reply_text(f'{ce("📥")} User <code>{uid}</code> chưa có giao dịch.', parse_mode=ParseMode.HTML)
        else:
            msg = f'{ce("📜")} <b>LỊCH SỬ USER <code>{uid}</code>:</b>\n\n'
            for d in data:
                msg += f'{ce("💰")} <code>{fmt_money(d[0])}</code> | {html.escape(d[1])} | <i>{d[2]}</i>\n'
            if len(msg) > 4000:
                for x in range(0, len(msg), 4000):
                    await update.effective_message.reply_text(msg[x:x+4000], parse_mode=ParseMode.HTML)
            else:
                await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)
    except (IndexError, ValueError):
        await update.effective_message.reply_text(f'{ce("❌")} Cú pháp: <code>/check [ID]</code>', parse_mode=ParseMode.HTML)

def _sum(q, args=()):
    r = query(q, args)
    return (r[0][0] or 0) if r else 0

@admin_only
async def dashboard_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    today = get_vietnam_date()
    this_month = get_vietnam_time().strftime("/%m/%Y")
    nap_today = _sum("SELECT SUM(amount) FROM history WHERE amount > 0 AND note ILIKE '%%nạp%%' AND time LIKE %s", (f"%{today}%",))
    rut_today = _sum("SELECT SUM(amount) FROM history WHERE amount < 0 AND note ILIKE '%%Rút%%' AND time LIKE %s", (f"%{today}%",))
    nap_month = _sum("SELECT SUM(amount) FROM history WHERE amount > 0 AND note ILIKE '%%nạp%%' AND time LIKE %s", (f"%{this_month}%",))
    rut_month = _sum("SELECT SUM(amount) FROM history WHERE amount < 0 AND note ILIKE '%%Rút%%' AND time LIKE %s", (f"%{this_month}%",))
    total_cuoc = _sum("SELECT SUM(amount) FROM history WHERE amount < 0 AND note NOT ILIKE '%Rút%' AND note NOT ILIKE '%trừ tiền%' AND note NOT ILIKE '%Chuyển tiền%'")
    total_thang = _sum("SELECT SUM(amount) FROM history WHERE amount > 0 AND note NOT ILIKE '%nạp%' AND note NOT ILIKE '%Code%' AND note NOT ILIKE '%Checkin%' AND note NOT ILIKE '%Admin%' AND note NOT ILIKE '%Nhận tiền%' AND note NOT ILIKE '%Hoàn%' AND note NOT ILIKE '%Khuyến mãi%' AND note NOT ILIKE '%Ref%'")
    loi_nhuan = abs(total_cuoc) - total_thang
    msg = (
        f'{ce("📊")} <b>BẢNG THỐNG KÊ DOANH THU</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("🗓")} <b>Hôm nay ({today}):</b>\n'
        f'  {ce("📥")} Tổng nạp: <code>+{fmt_money(nap_today)}đ</code>\n'
        f'  {ce("📤")} Tổng rút: <code>{fmt_money(rut_today)}đ</code>\n\n'
        f'{ce("🗓")} <b>Tháng này ({get_vietnam_time().month}):</b>\n'
        f'  {ce("📥")} Tổng nạp: <code>+{fmt_money(nap_month)}đ</code>\n'
        f'  {ce("📤")} Tổng rút: <code>{fmt_money(rut_month)}đ</code>\n\n'
        f'{ce("📈")} <b>Tổng kết Game (All time):</b>\n'
        f'  {ce("💰")} Lợi nhuận ròng: <code>{fmt_money(loi_nhuan)}đ</code>\n'
        f'━━━━━━━━━━━━━━━━━━━━━'
    )
    await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)

@admin_only
async def tong_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    t_nap = _sum("SELECT SUM(amount) FROM history WHERE amount > 0 AND note ILIKE '%nạp%'")
    t_rut = _sum("SELECT SUM(amount) FROM history WHERE amount < 0 AND note ILIKE '%Rút%'")
    t_cuoc = _sum("SELECT SUM(amount) FROM history WHERE amount < 0 AND note NOT ILIKE '%Rút%' AND note NOT ILIKE '%trừ tiền%' AND note NOT ILIKE '%Chuyển tiền%'")
    t_thang = _sum("SELECT SUM(amount) FROM history WHERE amount > 0 AND note NOT ILIKE '%nạp%' AND note NOT ILIKE '%Code%' AND note NOT ILIKE '%Checkin%' AND note NOT ILIKE '%Admin%' AND note NOT ILIKE '%Nhận tiền%' AND note NOT ILIKE '%Hoàn%' AND note NOT ILIKE '%Khuyến mãi%' AND note NOT ILIKE '%Ref%'")
    loi_nhuan = abs(t_cuoc) - t_thang
    msg = (
        f'{ce("📊")} <b>TỔNG QUAN TÀI CHÍNH HỆ THỐNG</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("📥")} <b>Tổng Nạp:</b> <code>+{fmt_money(t_nap)}đ</code>\n'
        f'{ce("📤")} <b>Tổng Rút:</b> <code>{fmt_money(abs(t_rut))}đ</code>\n'
        f'{ce("💰")} <b>Lợi Nhuận Thực Tế (Game):</b> <code>{fmt_money(loi_nhuan)}đ</code>\n'
        f'━━━━━━━━━━━━━━━━━━━━━'
    )
    await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)

@admin_only
async def soduall_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    users = query("SELECT user_id, balance FROM users WHERE balance > 0 ORDER BY balance DESC")
    if not users:
        return await update.effective_message.reply_text(f'Hiện không có ai có số dư lớn hơn 0.', parse_mode=ParseMode.HTML)
    text = f'{ce("💰")} <b>DANH SÁCH SỐ DƯ TẤT CẢ ID:</b>\n'
    for u in users:
        text += f'ID: <code>{u[0]}</code> | Số dư: <code>{fmt_money(u[1])}đ</code>\n'
    if len(text) > 4000:
        for x in range(0, len(text), 4000):
            await update.effective_message.reply_text(text[x:x+4000], parse_mode=ParseMode.HTML)
    else:
        await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

@admin_only
async def resetsdall_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query("UPDATE users SET balance = 0")
    await update.effective_message.reply_text(f'{ce("✅")} Đã xóa toàn bộ số dư của tất cả người dùng về 0!', parse_mode=ParseMode.HTML)

@admin_only
async def xoalsall_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query("DELETE FROM history")
    await update.effective_message.reply_text(f'{ce("✅")} Đã xoá toàn bộ lịch sử cược, nạp và rút của hệ thống!', parse_mode=ParseMode.HTML)

@admin_only
async def xoals_user_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        return await update.effective_message.reply_text(f'{ce("❌")} Cú pháp: <code>/xoals [ID]</code>', parse_mode=ParseMode.HTML)
    try:
        uid = int(ctx.args[0])
        query("DELETE FROM history WHERE user_id=%s", (uid,))
        await update.effective_message.reply_text(f'{ce("✅")} Đã xoá sạch lịch sử của người dùng: <code>{uid}</code>', parse_mode=ParseMode.HTML)
    except:
        await update.effective_message.reply_text(f'{ce("❌")} ID không hợp lệ.', parse_mode=ParseMode.HTML)

@admin_only
async def set_bot_name_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        return await update.effective_message.reply_text(f'{ce("❌")} Cú pháp: <code>/setname [Tên mới]</code>', parse_mode=ParseMode.HTML)
    new_name = " ".join(ctx.args)
    query("UPDATE settings SET value=%s WHERE key='bot_display_name'", (new_name,))
    await update.effective_message.reply_text(f'{ce("✅")} Đã đổi tên hiển thị của Bot thành: <b>{html.escape(new_name)}</b>', parse_mode=ParseMode.HTML)

@admin_only
async def sethu_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        current_jackpot = get_jackpot()
        return await update.effective_message.reply_text(
            f'{ce("🎁")} <b>QUẢN LÝ HŨ JACKPOT</b>\n\n'
            f'{ce("💰")} Số tiền hũ hiện tại: <code>{fmt_money(current_jackpot)}đ</code>\n\n'
            f'{ce("✍️")} <b>Cú pháp:</b> <code>/sethu [số_tiền]</code>\n'
            f'VD: <code>/sethu 50000000</code> (50 triệu)\n'
            f'Hoặc: <code>/sethu 11tỷ</code> (hỗ trợ đơn vị k, m, tỷ)',
            parse_mode=ParseMode.HTML)
    try:
        arg = ctx.args[0].lower().replace(".", "").replace(",", "")
        if arg.endswith("ty") or arg.endswith("tỷ"):
            amount = int(float(arg.replace("ty", "").replace("tỷ", "")) * 1000000000)
        elif arg.endswith("m"):
            amount = int(float(arg.replace("m", "")) * 1000000)
        elif arg.endswith("k"):
            amount = int(float(arg.replace("k", "")) * 1000)
        else:
            amount = int(arg)

        if amount < 0:
            return await update.effective_message.reply_text(f'{ce("❌")} Số tiền không được âm!', parse_mode=ParseMode.HTML)

        old_jackpot = get_jackpot()
        update_jackpot(amount)

        await update.effective_message.reply_text(
            f'{ce("✅")} <b>ĐÃ CẬP NHẬT HŨ JACKPOT</b>\n'
            f'━━━━━━━━━━━━━━━━━━━━━\n'
            f'{ce("📊")} <b>Số cũ:</b> <code>{fmt_money(old_jackpot)}đ</code>\n'
            f'{ce("💰")} <b>Số mới:</b> <code>{fmt_money(amount)}đ</code>\n'
            f'━━━━━━━━━━━━━━━━━━━━━',
            parse_mode=ParseMode.HTML)
    except ValueError:
        await update.effective_message.reply_text(
            f'{ce("❌")} Số tiền không hợp lệ!\n'
            f'VD: <code>/sethu 50000000</code> hoặc <code>/sethu 50m</code> hoặc <code>/sethu 11tỷ</code>',
            parse_mode=ParseMode.HTML)

@admin_only
async def tao_code(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        reward, uses = int(ctx.args[0]), int(ctx.args[1])
        code = gen_code()
        query("INSERT INTO codes (code, reward, uses) VALUES(%s,%s,%s)", (code, reward, uses))
        await update.effective_message.reply_text(
            f'{ce("✅")} <b>TẠO CODE THÀNH CÔNG</b>\n\n'
            f'{ce("🎁")} Code: <code>{code}</code>\n'
            f'{ce("💰")} Thưởng: <code>{fmt_money(reward)}đ</code>\n'
            f'{ce("🔄")} Lượt: <code>{uses}</code>',
            parse_mode=ParseMode.HTML)
    except (IndexError, ValueError):
        await update.effective_message.reply_text(f'{ce("❌")} Cú pháp: <code>/taocode [số tiền] [lượt dùng]</code>', parse_mode=ParseMode.HTML)

@admin_only
async def taocodeall_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        return await update.effective_message.reply_text(f'{ce("❌")} <b>Cú pháp:</b> <code>/taocodeall [số_tiền] [số_lượng]</code>', parse_mode=ParseMode.HTML)
    try:
        reward = int(ctx.args[0])
        quantity = int(ctx.args[1])
        if quantity < 1 or quantity > 100:
            return await update.effective_message.reply_text(f'{ce("❌")} Số lượng code phải từ 1 đến 100!', parse_mode=ParseMode.HTML)
        if reward < 1000:
            return await update.effective_message.reply_text(f'{ce("❌")} Số tiền thưởng tối thiểu là 1,000đ!', parse_mode=ParseMode.HTML)
        codes = []
        for i in range(quantity):
            code = gen_code()
            query("INSERT INTO codes (code, reward, uses) VALUES(%s, %s, %s)", (code, reward, 1))
            codes.append(code)
        msg = f'{ce("🎁")} <b>TẠO {quantity} CODE THÀNH CÔNG!</b>\n━━━━━━━━━━━━━━━━━━━━━\n{ce("💰")} Mỗi code: <code>{fmt_money(reward)}đ</code>\n\n'
        for i, code in enumerate(codes, 1):
            msg += f'{i}. <code>{code}</code>\n'
        msg += f'\n{ce("📌")} Dùng lệnh <code>/code [mã]</code> để nhận thưởng!'
        if len(msg) > 4000:
            bio = BytesIO("\n".join(codes).encode("utf-8"))
            bio.name = "codes.txt"
            await update.effective_message.reply_document(document=bio, caption=f"🎁 {quantity} code, mỗi code {fmt_money(reward)}đ")
        else:
            await update.effective_message.reply_text(msg, parse_mode=ParseMode.HTML)
    except ValueError:
        await update.effective_message.reply_text(f'{ce("❌")} Số tiền hoặc số lượng không hợp lệ!', parse_mode=ParseMode.HTML)

@admin_only
async def xoacode_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        return await update.effective_message.reply_text(f'{ce("❌")} <b>Cú pháp:</b> <code>/xoacode [mã_code]</code>', parse_mode=ParseMode.HTML)
    code_str = ctx.args[0].strip().upper()
    data = query("SELECT reward, uses FROM codes WHERE code=%s", (code_str,))
    if not data:
        return await update.effective_message.reply_text(f'{ce("❌")} Code <code>{code_str}</code> không tồn tại!', parse_mode=ParseMode.HTML)
    reward, uses = data[0]
    query("DELETE FROM codes WHERE code=%s", (code_str,))
    await update.effective_message.reply_text(f'{ce("✅")} <b>ĐÃ XÓA CODE</b>\n{ce("🎁")} Mã: <code>{code_str}</code>\n{ce("💰")} Giá trị: <code>{fmt_money(reward)}đ</code>', parse_mode=ParseMode.HTML)

@admin_only
async def kmnap_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        return await update.effective_message.reply_text(f'{ce("❌")} <b>Cú pháp:</b> <code>/kmnap [ID] [số_tiền]</code>', parse_mode=ParseMode.HTML)
    try:
        target_id = int(ctx.args[0])
        bonus_amount = int(ctx.args[1])
        if bonus_amount <= 0:
            return await update.effective_message.reply_text(f'{ce("❌")} Số tiền khuyến mãi phải lớn hơn 0!', parse_mode=ParseMode.HTML)
        required_bet = add_bonus_with_requirement(target_id, bonus_amount, 2)
        await update.effective_message.reply_text(
            f'{ce("✅")} <b>KHUYẾN MÃI NẠP THÀNH CÔNG!</b>\n\n'
            f'{ce("👥")} <b>ID:</b> <code>{target_id}</code>\n'
            f'{ce("💰")} <b>Tiền thưởng:</b> <code>+{fmt_money(bonus_amount)}đ</code>\n'
            f'{ce("🎯")} <b>Yêu cầu cược:</b> <code>{fmt_money(required_bet)}đ</code>',
            parse_mode=ParseMode.HTML)
        try:
            await ctx.bot.send_message(target_id,
                f'{ce("🎁")} <b>THÔNG BÁO KHUYẾN MÃI</b>\n\n'
                f'Bạn vừa nhận được khuyến mãi nạp: <code>+{fmt_money(bonus_amount)}đ</code>\n\n'
                f'{ce("📌")} <b>Điều kiện rút tiền:</b>\n'
                f'• Cần cược <b>x2</b> vòng\n'
                f'• Số tiền cược yêu cầu: <code>{fmt_money(required_bet)}đ</code>',
                parse_mode=ParseMode.HTML)
        except Exception:
            pass
    except ValueError:
        await update.effective_message.reply_text(f'{ce("❌")} ID hoặc số tiền không hợp lệ!', parse_mode=ParseMode.HTML)

@admin_only
async def kmnapvc_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        return await update.effective_message.reply_text(f'{ce("❌")} <b>Cú pháp:</b> <code>/kmnapvc [ID] [số_tiền]</code>', parse_mode=ParseMode.HTML)
    try:
        target_id = int(ctx.args[0])
        bet_amount = int(ctx.args[1])
        bonus_data = query("SELECT required_bet, current_bet FROM user_bonus WHERE user_id=%s", (target_id,))
        if not bonus_data or bonus_data[0][0] == 0:
            return await update.effective_message.reply_text(f'{ce("❌")} ID <code>{target_id}</code> không có yêu cầu cược nào!', parse_mode=ParseMode.HTML)
        required_bet, current_bet = bonus_data[0]
        new_bet = current_bet + bet_amount
        query("UPDATE user_bonus SET current_bet=%s WHERE user_id=%s", (new_bet, target_id))
        remaining = required_bet - new_bet
        remaining_text = f'Còn thiếu <code>{fmt_money(remaining)}đ</code>' if remaining > 0 else f'{ce("✅")} ĐÃ HOÀN THÀNH!'
        await update.effective_message.reply_text(
            f'{ce("✅")} <b>CẬP NHẬT CƯỢC THÀNH CÔNG!</b>\n\n'
            f'{ce("👥")} <b>ID:</b> <code>{target_id}</code>\n'
            f'{ce("➕")} <b>Cược thêm:</b> <code>+{fmt_money(bet_amount)}đ</code>\n'
            f'{ce("📊")} <b>Tổng cược:</b> <code>{fmt_money(new_bet)}đ</code>\n'
            f'{ce("🎯")} <b>Yêu cầu:</b> <code>{fmt_money(required_bet)}đ</code>\n'
            f'{ce("📌")} <b>Trạng thái:</b> {remaining_text}',
            parse_mode=ParseMode.HTML)
    except ValueError:
        await update.effective_message.reply_text(f'{ce("❌")} ID hoặc số tiền không hợp lệ!', parse_mode=ParseMode.HTML)

@admin_only
async def admin_check_bet_progress_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 1:
        return await update.effective_message.reply_text(f'{ce("❌")} <b>Cú pháp:</b> <code>/checkprogressadmin [ID]</code>', parse_mode=ParseMode.HTML)
    try:
        target_id = int(ctx.args[0])
    except ValueError:
        return await update.effective_message.reply_text(f'{ce("❌")} ID không hợp lệ!', parse_mode=ParseMode.HTML)
    status = get_bet_progress_status(target_id)
    if not status:
        return await update.effective_message.reply_text(f'{ce("📊")} Người dùng <code>{target_id}</code> không có khuyến mãi nào đang hoạt động!', parse_mode=ParseMode.HTML)
    percent = min(status['percent'], 100)
    bar_length = 20
    filled = int(bar_length * percent / 100)
    bar = "█" * filled + "░" * (bar_length - filled)
    message = (
        f'{ce("📊")} <b>TIẾN ĐỘ CƯỢC CỦA USER</b> <code>{target_id}</code>\n'
        f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("🎁")} <b>Tiền khuyến mãi:</b> <code>+{fmt_money(status["bonus_amount"])}đ</code>\n'
        f'{ce("🎯")} <b>Yêu cầu cược:</b> <code>{fmt_money(status["required_bet"])}đ</code>\n'
        f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("📈")} <b>Tiến độ:</b>\n<code>{bar}</code> <code>{percent:.1f}%</code>\n'
        f'━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("✅")} <b>Đã cược:</b> <code>{fmt_money(status["current_bet"])}đ</code>\n'
        f'{ce("⚠️")} <b>Còn thiếu:</b> <code>{fmt_money(max(0, status["remaining"]))}đ</code>'
    )
    await update.effective_message.reply_text(message, parse_mode=ParseMode.HTML)

@admin_only
async def reset_progress(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 1:
        return await update.effective_message.reply_text(f'{ce("❌")} <b>Cú pháp:</b> <code>/resetprogress [ID]</code>', parse_mode=ParseMode.HTML)
    try:
        uid = int(ctx.args[0])
        query("DELETE FROM user_bonus WHERE user_id=%s", (uid,))
        await update.effective_message.reply_text(f'{ce("✅")} Đã reset tiến độ cược cho ID <code>{uid}</code>', parse_mode=ParseMode.HTML)
    except:
        await update.effective_message.reply_text(f'{ce("❌")} ID không hợp lệ.', parse_mode=ParseMode.HTML)

# ---------- BẢO TRÌ ----------
MT_ITEMS = {
    'mt_taixiu_room': {'name': 'TÀI XỈU ROOM', 'type': 'game', 'icon': '😵'},
    'mt_xucxac_don': {'name': 'XÚC XẮC ĐƠN', 'type': 'game', 'icon': '🚫'},
    'mt_longho': {'name': 'LONG HỔ', 'type': 'game', 'icon': '⚰️'},
    'mt_minipoker': {'name': 'MINI POKER', 'type': 'game', 'icon': '🔝'},
    'mt_baccarat': {'name': 'BACCARAT', 'type': 'game', 'icon': '⬆️'},
    'mt_xocdia4': {'name': 'XÓC ĐĨA 4 VỊ', 'type': 'game', 'icon': '❓'},
    'mt_taixiumd5': {'name': 'TÀI XỈU MD5', 'type': 'game', 'icon': '👌'},
    'mt_baucua': {'name': 'BẦU CUA', 'type': 'game', 'icon': '🦌'},
    'mt_xocdia6': {'name': 'XÓC ĐĨA 6 VỊ', 'type': 'game', 'icon': '⚪'},
    'mt_nap': {'name': 'NẠP TIỀN', 'type': 'feature', 'icon': '💳'},
    'mt_rut': {'name': 'RÚT TIỀN', 'type': 'feature', 'icon': '💸'},
}

async def send_or_edit(update: Update, text: str, kb=None):
    """Gửi mới nếu là lệnh, sửa tin nhắn nếu là nút bấm."""
    markup = InlineKeyboardMarkup(kb) if kb else None
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)
        except Exception as e:
            print(f"edit_message_text lỗi: {e}")
    else:
        await update.effective_message.reply_text(text, reply_markup=markup, parse_mode=ParseMode.HTML)

@admin_only
async def baotri_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    def st(k):
        return "OFF" if check_mt(k) else "ON"
    def ic(k):
        return "❌" if check_mt(k) else "✅"
    kb = [
        [btn(f"Tài Xỉu Room: {st('mt_taixiu_room')}", ic('mt_taixiu_room'), callback_data="tg_mt_taixiu_room")],
        [btn(f"Xúc Xắc Đơn: {st('mt_xucxac_don')}", ic('mt_xucxac_don'), callback_data="tg_mt_xucxac_don")],
        [btn(f"Long Hổ: {st('mt_longho')}", ic('mt_longho'), callback_data="tg_mt_longho")],
        [btn(f"Mini Poker: {st('mt_minipoker')}", ic('mt_minipoker'), callback_data="tg_mt_minipoker")],
        [btn(f"Baccarat: {st('mt_baccarat')}", ic('mt_baccarat'), callback_data="tg_mt_baccarat")],
        [btn(f"Xóc Đĩa 4 Vị: {st('mt_xocdia4')}", ic('mt_xocdia4'), callback_data="tg_mt_xocdia4")],
        [btn(f"Tài Xỉu MD5: {st('mt_taixiumd5')}", ic('mt_taixiumd5'), callback_data="tg_mt_taixiumd5")],
        [btn(f"Bầu Cua: {st('mt_baucua')}", ic('mt_baucua'), callback_data="tg_mt_baucua")],
        [btn(f"Xóc Đĩa 6 Vị: {st('mt_xocdia6')}", ic('mt_xocdia6'), callback_data="tg_mt_xocdia6")],
        [btn(f"Nạp Tiền: {st('mt_nap')}", ic('mt_nap'), callback_data="tg_mt_nap"),
         btn(f"Rút Tiền: {st('mt_rut')}", ic('mt_rut'), callback_data="tg_mt_rut")],
        [btn("ĐÓNG BẢNG", "❌", callback_data="close_admin")]
    ]
    await send_or_edit(update,
        f'{ce("🛠")} <b>BẢNG QUẢN LÝ BẢO TRÌ</b>\n(Bấm để chuyển trạng thái On/Off)', kb)

@admin_only
async def baotri_he_thong_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = []
    kb.append([btn("GAME", "🎮", callback_data="none")])
    game_items = [(k, v) for k, v in MT_ITEMS.items() if v['type'] == 'game']
    for i in range(0, len(game_items), 2):
        row = []
        for j in range(2):
            if i + j < len(game_items):
                key, item = game_items[i + j]
                status = "🔴 OFF" if check_mt(key) else "🟢 ON"
                row.append(btn(f"{item['name']}: {'OFF' if check_mt(key) else 'ON'}", "❌" if check_mt(key) else "✅", callback_data=f"mt_toggle_{key}"))
        kb.append(row)
    kb.append([btn("TÍNH NĂNG", "⚙️", callback_data="none")])
    feature_items = [(k, v) for k, v in MT_ITEMS.items() if v['type'] == 'feature']
    for i in range(0, len(feature_items), 2):
        row = []
        for j in range(2):
            if i + j < len(feature_items):
                key, item = feature_items[i + j]
                status = "🔴 OFF" if check_mt(key) else "🟢 ON"
                row.append(btn(f"{item['name']}: {'OFF' if check_mt(key) else 'ON'}", "❌" if check_mt(key) else "✅", callback_data=f"mt_toggle_{key}"))
        kb.append(row)
    kb.append([btn("TẮT TẤT CẢ", "🔴", callback_data="mt_turnoff_all"),
               btn("BẬT TẤT CẢ", "🟢", callback_data="mt_turnon_all")])
    kb.append([btn("ĐÓNG BẢNG", "❌", callback_data="close_admin")])
    await send_or_edit(update,
        f'{ce("🛠")} <b>BẢNG BẢO TRÌ HỆ THỐNG</b> {ce("🛠")}\n'
        f'<b>Bấm vào từng mục để bật/tắt:</b>', kb)

async def handle_mt_toggle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = q.from_user.id
    if uid not in ADMIN_IDS:
        await q.answer("❌ Bạn không có quyền!", show_alert=True)
        return
    data = q.data
    keys = list(MT_ITEMS.keys())
    if data == "mt_turnoff_all":
        for key in keys:
            query("UPDATE settings SET value='1' WHERE key=%s", (key,))
        await q.answer("✅ Đã BẬT BẢO TRÌ tất cả!", show_alert=True)
        await baotri_he_thong_cmd(update, ctx)
    elif data == "mt_turnon_all":
        for key in keys:
            query("UPDATE settings SET value='0' WHERE key=%s", (key,))
        await q.answer("✅ Đã bật HOẠT ĐỘNG tất cả!", show_alert=True)
        await baotri_he_thong_cmd(update, ctx)
    elif data.startswith("mt_toggle_"):
        key = data.replace("mt_toggle_", "")
        new_val = "1" if not check_mt(key) else "0"
        query("UPDATE settings SET value=%s WHERE key=%s", (new_val, key))
        name = MT_ITEMS.get(key, {}).get('name', key)
        status = "🔴 ĐANG BẢO TRÌ" if new_val == "1" else "🟢 HOẠT ĐỘNG"
        await q.answer(f"{name}: {status}", show_alert=True)
        await baotri_he_thong_cmd(update, ctx)

async def baotri_hethong_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.effective_message.reply_text(f'{ce("❌")} Bạn không có quyền!', parse_mode=ParseMode.HTML)
        return
    if len(ctx.args) < 1:
        current_status = f'{ce("🔒")} ĐANG BẢO TRÌ' if is_system_maintenance() else f'{ce("🔓")} HOẠT ĐỘNG'
        await update.effective_message.reply_text(
            f'{ce("🛠")} <b>TRẠNG THÁI</b>\n{ce("📊")} {current_status}\n\n'
            f'{ce("✍️")} <code>/baotriall on</code> hoặc <code>/baotriall off</code>',
            parse_mode=ParseMode.HTML)
        return
    action = ctx.args[0].lower()
    if action == "on":
        query("UPDATE settings SET value='1' WHERE key='system_maintenance'")
        await update.effective_message.reply_text(f'{ce("🔒")} <b>ĐÃ BẬT BẢO TRÌ TOÀN HỆ THỐNG</b>', parse_mode=ParseMode.HTML)
    elif action == "off":
        query("UPDATE settings SET value='0' WHERE key='system_maintenance'")
        await update.effective_message.reply_text(f'{ce("✅")} <b>ĐÃ TẮT BẢO TRÌ</b>', parse_mode=ParseMode.HTML)

async def baotri_tong_cong_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.effective_message.reply_text(f'{ce("❌")} Chỉ Admin mới dùng được!', parse_mode=ParseMode.HTML)
        return
    if len(ctx.args) < 1:
        current_status = f'{ce("🔒")} Đang BẢO TRÌ TOÀN BỘ' if is_total_maintenance() else f'{ce("🔓")} HOẠT ĐỘNG'
        await update.effective_message.reply_text(
            f'{ce("🛠")} <b>BẢO TRÌ TOÀN BỘ</b>\n{ce("📊")} {current_status}\n\n'
            f'<code>/baotritc on</code> hoặc <code>/baotritc off</code>',
            parse_mode=ParseMode.HTML)
        return
    action = ctx.args[0].lower()
    if action == "on":
        query("UPDATE settings SET value='1' WHERE key='mt_tongbao'")
        await update.effective_message.reply_text(f'{ce("🔒")} <b>ĐÃ BẬT BẢO TRÌ TOÀN BỘ</b>', parse_mode=ParseMode.HTML)
    elif action == "off":
        query("UPDATE settings SET value='0' WHERE key='mt_tongbao'")
        await update.effective_message.reply_text(f'{ce("✅")} <b>ĐÃ TẮT BẢO TRÌ TOÀN BỘ</b>', parse_mode=ParseMode.HTML)

async def tatroom_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.effective_message.reply_text(f'{ce("❌")} Bạn không có quyền!', parse_mode=ParseMode.HTML)
        return
    chat_id = update.effective_chat.id
    if update.effective_chat.type == "private":
        await update.effective_message.reply_text(f'{ce("❌")} Lệnh này chỉ dùng trong NHÓM!', parse_mode=ParseMode.HTML)
        return
    if len(ctx.args) < 1:
        current_status = f'{ce("🔒")} ĐÃ TẮT' if not room_betting_enabled.get(chat_id, True) else f'{ce("🔓")} ĐANG BẬT'
        await update.effective_message.reply_text(
            f'{ce("🎮")} <b>TRẠNG THÁI CƯỢC</b>\n{ce("📊")} Hiện tại: {current_status}\n\n'
            f'{ce("✍️")} Cú pháp:\n• Tắt: <code>/tatroom off</code>\n• Bật: <code>/tatroom on</code>',
            parse_mode=ParseMode.HTML)
        return
    action = ctx.args[0].lower()
    if action == "off":
        room_betting_enabled[chat_id] = False
        await update.effective_message.reply_text(f'{ce("🔒")} <b>ĐÃ TẮT CƯỢC TRONG NHÓM!</b>', parse_mode=ParseMode.HTML)
    elif action == "on":
        room_betting_enabled[chat_id] = True
        await update.effective_message.reply_text(f'{ce("🔓")} <b>ĐÃ BẬT CƯỢC TRONG NHÓM!</b>', parse_mode=ParseMode.HTML)

async def show_user_manage(q, target_id: int, current_page: int):
    res = query("SELECT balance, refs, bank, stk, name, last_checkin, total_bet FROM users WHERE user_id=%s", (target_id,))
    if not res:
        return await q.answer("Không tìm thấy user!")
    u = res[0]
    status_text = f'{ce("🚫")} ĐANG CHẶN' if is_banned(target_id) else f'{ce("✅")} HOẠT ĐỘNG'
    msg = (f'{ce("👥")} <b>USER:</b> <code>{target_id}</code>\n'
           f'{ce("💰")} <code>{fmt_money(u[0])}đ</code>\n'
           f'{ce("📊")} Tổng cược: <code>{fmt_money(u[6] or 0)}đ</code>\n'
           f'{ce("🚩")} {status_text}')
    kb = [[btn("BAN", "🚫", callback_data=f"adm_act_ban_{target_id}_{current_page}"),
           btn("UNBAN", "✅", callback_data=f"adm_act_unban_{target_id}_{current_page}")],
          [btn("QUAY LẠI", "🔙", callback_data=f"adm_page_{current_page}")]]
    try:
        await q.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.HTML)
    except Exception:
        pass

# ================= HỆ THỐNG DANH SÁCH GAME (DẠNG NÚT BẤM) =================
# Luồng: DANH SÁCH GAME -> chọn game (gm_) -> chọn cửa (gc_) -> chọn số tiền (gb_) -> chơi
AMOUNT_BUTTONS = [("1k", 1000), ("5k", 5000), ("10k", 10000), ("20k", 20000), ("50k", 50000),
                  ("100k", 100000), ("200k", 200000), ("500k", 500000), ("1m", 1000000)]

GAMES = {
    "room": {"name": "TÀI XỈU ROOM", "icon": "🎲", "rows": None},
    "xx": {"name": "XÚC XẮC ĐƠN", "icon": "🎰", "rows": [
        [("CHẴN (x1.95)", "XXC", "🆗"), ("LẺ (x1.95)", "XXL", "❓")],
        [("TÀI (x1.95)", "XXT", "⬆️"), ("XỈU (x1.95)", "XXX", "⬇️")],
        [("Mặt 1 (x5)", "D1", "1️⃣"), ("Mặt 2 (x5)", "D2", "2️⃣"), ("Mặt 3 (x5)", "D3", "3️⃣")],
        [("Mặt 4 (x5)", "D4", "4️⃣"), ("Mặt 5 (x5)", "D5", "5️⃣"), ("Mặt 6 (x5)", "D6", "6️⃣")],
    ]},
    "lh": {"name": "LONG HỔ", "icon": "🐯", "rows": [
        [("LONG", "long", "🐯"), ("HỔ", "ho", "🐉")],
    ]},
    "mp": {"name": "MINI POKER", "icon": "🃏", "rows": None},
    "bcr": {"name": "BACCARAT", "icon": "🏦", "rows": [
        [("PLAYER (x2)", "player", "👤")],
        [("BANKER (x2)", "banker", "🏦")],
        [("TIE (x9)", "tie", "⚖️")],
    ]},
    "xd4": {"name": "XÓC ĐĨA 4 VỊ", "icon": "💿", "rows": [
        [("CHẴN", "chan", "🆗"), ("LẺ", "le", "❓")],
    ]},
    "md5": {"name": "TÀI XỈU MD5", "icon": "👌", "rows": [
        [("TÀI", "tai", "⬆️"), ("XỈU", "xiu", "⬇️")],
        [("CHẴN", "chan", "🆗"), ("LẺ", "le", "❓")],
    ]},
    "bc": {"name": "BẦU CUA", "icon": "🦌", "rows": [
        [("BẦU", "bau", "🍀"), ("CUA", "cua", "🦀"), ("TÔM", "tom", "☄️")],
        [("CÁ", "ca", "💧"), ("GÀ", "ga", "🐣"), ("NAI", "nai", "🦌")],
    ]},
    "xd6": {"name": "XÓC ĐĨA 6 VỊ", "icon": "💿", "rows": [
        [("CHẴN", "chan", "🆗"), ("LẺ", "le", "❓")],
    ]},
}

GAME_ROWS = [["room", "xx"], ["lh", "mp"], ["bcr", "xd4"], ["md5", "bc"], ["xd6"]]

GAME_RULES = {
    "room": (
        f'{ce("🎲")} <b>TÀI XỈU ROOM</b>\n\n'
        f'{ce("🔗")} <b>Link vào phòng:</b>\n'
        f'<code>{ROOM_LINK}</code>\n\n'
        f'{ce("🎯")} <b>LUẬT CHƠI:</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'• Hệ thống lắc 3 viên xúc xắc ngẫu nhiên.\n'
        f'• Cửa chính:\n'
        f'  - Tài (T): Tổng điểm 3 viên từ 11 đến 18.\n'
        f'  - Xỉu (X): Tổng điểm từ 3 đến 10.\n'
        f'  - Chẵn (C): Tổng điểm là số chẵn.\n'
        f'  - Lẻ (L): Tổng điểm là số lẻ.\n'
        f'• Cửa kết hợp (trả thưởng x3):\n'
        f'  - TL (Tài + Lẻ)\n'
        f'  - TC (Tài + Chẵn)\n'
        f'  - XL (Xỉu + Lẻ)\n'
        f'  - XC (Xỉu + Chẵn)\n'
        f'• Cửa D1, D2, D3 (trả thưởng x5 đến x30).\n'
        f'• Nổ hũ Jackpot:\n'
        f'  - Ra 3 con 6 (cửa Tài trúng hũ).\n'
        f'  - Ra 3 con 1 (cửa Xỉu trúng hũ).\n'
        f'• Tỷ lệ trả thưởng:\n'
        f'  - Tài / Xỉu / Chẵn / Lẻ: x2.3\n'
        f'  - Cửa kết hợp: x3\n'
        f'  - Bộ ba đồng nhất: x150\n\n'
        f'{ce("💡")} <b>Cách chơi:</b> Bấm nút bên dưới để vào phòng, nhắn lệnh VD: <code>T 20000</code> hoặc cược ẩn danh nhắn riêng cho bot.'
    ),
    "xx": (
        f'{ce("🎰")} <b>XÚC XẮC ĐƠN (Xúc Xắc Telegram)</b>\n\n'
        f'{ce("🎯")} <b>LUẬT CHƠI:</b>\n'
        f'• Dự đoán kết quả của 1 viên xúc xắc do Telegram quay.\n\n'
        f'{ce("📊")} <b>Các cửa cược & Tỷ lệ trả thưởng:</b>\n'
        f'• <code>XXC</code> (Chẵn - các mặt 2, 4, 6): x1.95\n'
        f'• <code>XXL</code> (Lẻ - các mặt 1, 3, 5): x1.95\n'
        f'• <code>XXT</code> (Tài - các mặt 4, 5, 6): x1.95\n'
        f'• <code>XXX</code> (Xỉu - các mặt 1, 2, 3): x1.95\n'
        f'• <code>D1</code> đến <code>D6</code> (Đoán chính xác mặt xúc xắc): x5\n\n'
        f'{ce("💡")} <b>Nhập tay:</b> <code>[Mã_cửa] [số_tiền]</code> VD: <code>XXC 50000</code>'
    ),
    "lh": (
        f'{ce("🐯")} <b>LONG HỔ</b>\n\n'
        f'{ce("🎯")} <b>LUẬT CHƠI:</b>\n'
        f'• So sánh điểm số của 2 lá bài chia cho cửa LONG và HỔ.\n'
        f'• Bên nào có điểm lớn hơn (A nhỏ nhất, K lớn nhất) thì bên đó thắng.\n'
        f'• Nếu điểm bằng nhau → Hòa (hoàn lại tiền cược).\n\n'
        f'{ce("💵")} <b>Tỷ lệ trả thưởng:</b> x1.95\n\n'
        f'{ce("💡")} <b>Nhập tay:</b> <code>/lh [long/ho] [số_tiền]</code>'
    ),
    "mp": (
        f'{ce("🃏")} <b>MINI POKER</b>\n\n'
        f'{ce("🎯")} <b>LUẬT CHƠI:</b>\n'
        f'• Bot bốc ngẫu nhiên 5 lá bài để phân định thắng thua dựa trên các tay bài Poker.\n\n'
        f'{ce("📊")} <b>Các tổ hợp & Tỷ lệ trả thưởng:</b>\n'
        f'• Tứ Quý (4 lá cùng số): x100\n'
        f'• Bộ Ba (3 lá cùng số): x25\n'
        f'• Hai Đôi: x10\n'
        f'• Một Đôi: x2\n'
        f'• Bài rác (Không có đôi nào): Thua.\n\n'
        f'{ce("💡")} <b>Nhập tay:</b> <code>/mp [số_tiền]</code>'
    ),
    "bcr": (
        f'{ce("🏦")} <b>BACCARAT</b>\n\n'
        f'{ce("🎯")} <b>LUẬT CHƠI:</b>\n'
        f'• So sánh điểm giữa cửa PLAYER và BANKER (tính điểm từ 0 đến 9, gần 9 nhất là thắng, có luật rút thêm lá thứ 3 nếu điểm dưới 6).\n'
        f'• Cửa TIE là cửa Hòa.\n\n'
        f'{ce("💵")} <b>Tỷ lệ trả thưởng:</b>\n'
        f'• Player: x2\n'
        f'• Banker: x2\n'
        f'• Tie (Hòa): x9\n\n'
        f'{ce("💡")} <b>Nhập tay:</b> <code>/bcr [player/banker/tie] [số_tiền]</code>'
    ),
    "xd4": (
        f'{ce("💿")} <b>XÓC ĐĨA 4 VỊ</b>\n\n'
        f'{ce("🎯")} <b>LUẬT CHƠI:</b>\n'
        f'• Xóc ngẫu nhiên 4 đồng xu (mỗi đồng xu có mặt Đỏ hoặc Trắng).\n'
        f'• Chẵn: Tổng số mặt đỏ là 0, 2 hoặc 4 đỏ.\n'
        f'• Lẻ: Tổng số mặt đỏ là 1 hoặc 3 đỏ.\n\n'
        f'{ce("💵")} <b>Tỷ lệ trả thưởng:</b> x1.95\n\n'
        f'{ce("💡")} <b>Nhập tay:</b> <code>/xd4 [chan/le] [số_tiền]</code>'
    ),
    "md5": (
        f'{ce("👌")} <b>TÀI XỈU MD5</b>\n\n'
        f'{ce("🎯")} <b>LUẬT CHƠI:</b>\n'
        f'• Sử dụng mã hóa MD5 từ chuỗi ngẫu nhiên của hệ thống để tạo ra kết quả 3 viên xúc xắc.\n'
        f'• Tổng điểm 11-18 là Tài, 3-10 là Xỉu. Tổng chẵn là Chẵn, lẻ là Lẻ.\n\n'
        f'{ce("💵")} <b>Tỷ lệ trả thưởng:</b> x1.95\n\n'
        f'{ce("💡")} <b>Nhập tay:</b> <code>/txmd5 [tai/xiu/chan/le] [số_tiền]</code>'
    ),
    "bc": (
        f'{ce("🦌")} <b>BẦU CUA</b>\n\n'
        f'{ce("🎯")} <b>LUẬT CHƠI:</b>\n'
        f'• Lắc 3 viên xúc xắc, mỗi viên có 6 mặt: Bầu, Cua, Tôm, Cá, Gà, Nai.\n'
        f'• Đặt cược vào một linh vật, xuất hiện 1 lần ăn x2, 2 lần ăn x3, 3 lần ăn x4.\n\n'
        f'{ce("💡")} <b>Nhập tay:</b> <code>/bc [bau/cua/tom/ca/ga/nai] [số_tiền]</code>'
    ),
    "xd6": (
        f'{ce("💿")} <b>XÓC ĐĨA 6 VỊ</b>\n\n'
        f'{ce("🎯")} <b>LUẬT CHƠI:</b>\n'
        f'• Xóc ngẫu nhiên 6 đồng xu.\n'
        f'• Chẵn: Tổng số mặt đỏ là 0, 2, 4 hoặc 6.\n'
        f'• Lẻ: Tổng số mặt đỏ là 1, 3 hoặc 5.\n\n'
        f'{ce("💵")} <b>Tỷ lệ trả thưởng:</b> x1.95\n\n'
        f'{ce("💡")} <b>Nhập tay:</b> <code>/xd6 [chan/le] [số_tiền]</code>'
    ),
}

GAME_LIST_TEXT = (
    f'{ce("🛍")} <b>DANH SÁCH GAME</b>\n'
    f'{ce("😃")} Chúc bạn chơi vui vẻ! {ce("✍️")}\n\n'
    f'{ce("🫵")} Vui lòng chọn game bên dưới: {ce("😮‍💨")}'
)

OLD_MENU_ALIAS = {
    "menu_taixiu_room": "gm_room", "menu_xucxac_don": "gm_xx", "menu_longho": "gm_lh",
    "menu_minipoker": "gm_mp", "menu_baccarat": "gm_bcr", "menu_xocdia4": "gm_xd4",
    "menu_taixiumd5": "gm_md5", "menu_baucua": "gm_bc", "menu_xocdia6": "gm_xd6",
}

def game_list_kb():
    rows = []
    for r in GAME_ROWS:
        rows.append([btn(GAMES[k]["name"], GAMES[k]["icon"], callback_data=f"gm_{k}") for k in r])
    return InlineKeyboardMarkup(rows)

def game_choice_label(g, c):
    for row in GAMES[g].get("rows") or []:
        for label, code, _ in row:
            if code == c:
                return label
    return c

def game_valid_choice(g, c):
    rows = GAMES[g].get("rows")
    if not rows:
        return c == "x"
    return any(code == c for row in rows for _, code, _ in row)

def game_amount_kb(g, c):
    rows = []
    for i in range(0, len(AMOUNT_BUTTONS), 3):
        rows.append([btn(label, "💵", callback_data=f"gb_{g}_{c}_{val}") for label, val in AMOUNT_BUTTONS[i:i+3]])
    rows.append([btn("TẤT TAY (MAX)", "🔥", callback_data=f"gb_{g}_{c}_max")])
    back_cb = f"gm_{g}" if GAMES[g].get("rows") else "game_list"
    rows.append([btn("Quay lại", "🔙", callback_data=back_cb)])
    return InlineKeyboardMarkup(rows)

async def safe_edit(q, text, kb=None):
    """Sửa tin nhắn; nếu không sửa được thì gửi tin mới (không để nút 'đơ')."""
    try:
        await q.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception as e:
        if "not modified" in str(e).lower():
            return
        print(f"safe_edit lỗi: {e}")
        try:
            await q.message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception as e2:
            print(f"safe_edit gửi mới lỗi: {e2}")

async def run_game(update, ctx, g, choice, amount):
    if g == "xx":
        return await play_xucxac_don(update, ctx, choice, amount)
    if g == "lh":
        return await play_longho(update, ctx, choice, amount)
    if g == "mp":
        return await play_minipoker(update, ctx, amount)
    if g == "bcr":
        return await play_baccarat(update, ctx, choice, amount)
    if g == "xd4":
        return await play_xocdia4(update, ctx, choice, amount)
    if g == "md5":
        return await play_taixiumd5(update, ctx, choice, amount)
    if g == "bc":
        return await play_baucua(update, ctx, choice, amount)
    if g == "xd6":
        return await play_xocdia6(update, ctx, choice, amount)

async def handle_game_callbacks(update: Update, ctx: ContextTypes.DEFAULT_TYPE, d: str):
    q = update.callback_query
    uid = q.from_user.id

    if d == "game_list":
        await q.answer()
        return await safe_edit(q, GAME_LIST_TEXT, game_list_kb())

    # ---- Mở game ----
    if d.startswith("gm_"):
        g = d[3:]
        game = GAMES.get(g)
        if not game:
            return await q.answer("Game không tồn tại!", show_alert=True)
        await q.answer()
        if g == "room":
            kb = InlineKeyboardMarkup([
                [btn("VÀO PHÒNG CHƠI", "🎮", url=ROOM_LINK)],
                [btn("Quay lại", "🔙", callback_data="game_list")]
            ])
            return await safe_edit(q, GAME_RULES["room"], kb)
        if not game.get("rows"):
            text = GAME_RULES[g] + f'\n\n{ce("⬇️")} <b>Chọn số tiền cược:</b>'
            return await safe_edit(q, text, game_amount_kb(g, "x"))
        rows = [[btn(label, em, callback_data=f"gc_{g}_{code}") for label, code, em in row] for row in game["rows"]]
        rows.append([btn("Quay lại", "🔙", callback_data="game_list")])
        text = GAME_RULES[g] + f'\n\n{ce("⬇️")} <b>Chọn cửa để đặt cược:</b>'
        return await safe_edit(q, text, InlineKeyboardMarkup(rows))

    # ---- Chọn cửa ----
    if d.startswith("gc_"):
        try:
            _, g, c = d.split("_", 2)
        except ValueError:
            return await q.answer()
        if g not in GAMES or not game_valid_choice(g, c):
            return await q.answer("Lựa chọn không hợp lệ!", show_alert=True)
        await q.answer()
        text = (
            f'{ce(GAMES[g]["icon"])} <b>{GAMES[g]["name"]}</b>\n\n'
            f'{ce("🎯")} Bạn chọn: <b>{html.escape(game_choice_label(g, c))}</b>\n'
            f'{ce("💰")} Số dư: <code>{fmt_money(get_balance(uid))}đ</code>\n\n'
            f'{ce("⬇️")} <b>Chọn số tiền cược:</b>'
        )
        return await safe_edit(q, text, game_amount_kb(g, c))

    # ---- Đặt cược & chơi ----
    if d.startswith("gb_"):
        parts = d.split("_")
        if len(parts) < 4:
            return await q.answer()
        g, c, a = parts[1], parts[2], parts[3]
        if g not in GAMES or not game_valid_choice(g, c):
            return await q.answer("Lựa chọn không hợp lệ!", show_alert=True)
        if is_total_maintenance() and uid not in ADMIN_IDS:
            return await q.answer("⚡ Hệ thống đang bảo trì!", show_alert=True)
        if is_system_maintenance() and uid not in ADMIN_IDS:
            return await q.answer("⚡ Hệ thống đang bảo trì!", show_alert=True)
        try:
            amount = get_balance(uid) if a == "max" else int(a)
        except ValueError:
            return await q.answer("Số tiền không hợp lệ!", show_alert=True)
        if amount < 1000:
            return await q.answer("❌ Số dư không đủ (tối thiểu 1.000đ)!", show_alert=True)
        await q.answer("🎲 Đang chơi...")
        return await run_game(update, ctx, g, c, amount)

    await q.answer()


async def handle_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    d = q.data
    uid = q.from_user.id

    if d == "none":
        return await q.answer()

    if is_banned(uid) and uid not in ADMIN_IDS:
        return await q.answer("🚫 Tài khoản của bạn đã bị khóa!", show_alert=True)

    # ===== DANH SÁCH GAME (nút bấm) =====
    d = OLD_MENU_ALIAS.get(d, d)
    if d.startswith("lh_choice_"):
        d = "gc_lh_" + d[len("lh_choice_"):]
    elif d.startswith("bcr_choice_"):
        d = "gc_bcr_" + d[len("bcr_choice_"):]
    if d == "game_list" or d.startswith(("gm_", "gc_", "gb_")):
        return await handle_game_callbacks(update, ctx, d)

    # ===== [MỚI] GIFTCODE ADMIN / VIP / NHẬN THƯỞNG =====
    if d.startswith("gcn_"):
        return await handle_gift_flow_callback(update, ctx, d)
    if d in ("vip_doi", "vip_doi_all"):
        return await vip_exchange_callback(update, ctx, d)
    if d == "rw_claim":
        return await claim_rewards(update, ctx)

    # ===== TÀI KHOẢN =====
    if d == "acc_ls_nap":
        await q.answer()
        data = query("SELECT amount, time FROM deposit_history WHERE user_id=%s AND status='success' ORDER BY id DESC LIMIT 10", (uid,))
        text = f'{ce("📥")} <b>10 GIAO DỊCH NẠP GẦN NHẤT:</b>\n\n'
        if not data: text += "Trống."
        else:
            for row in data: text += f'{ce("✔️")} <code>+{fmt_money(row[0])}đ</code> | <i>{row[1]}</i>\n'
        return await q.message.reply_text(text, parse_mode=ParseMode.HTML)

    if d == "acc_ls_rut":
        await q.answer()
        data = query("SELECT amount, status, time FROM withdraw_history WHERE user_id=%s ORDER BY id DESC LIMIT 10", (uid,))
        text = f'{ce("📤")} <b>10 GIAO DỊCH RÚT GẦN NHẤT:</b>\n\n'
        if not data: text += "Trống."
        else:
            for row in data:
                status_icon = ce("✔️") if row[1] == "success" else ce("❌") if row[1] == "rejected" else ce("⏰")
                text += f'{status_icon} <code>{fmt_money(row[0])}đ</code> | {row[1]} | <i>{row[2]}</i>\n'
        return await q.message.reply_text(text, parse_mode=ParseMode.HTML)

    if d == "acc_ls_choi":
        await q.answer()
        return await ls_choi_cmd(update, ctx)

    if d == "acc_ls_tx":
        await q.answer()
        return await ls_room_tx_cmd(update, ctx)

    if d == "acc_nhap_gift":
        await q.answer()
        return await q.message.reply_text(f'{ce("🎁")} Vui lòng nhập lệnh <code>/code [mã]</code> để nhập giftcode.', parse_mode=ParseMode.HTML)

    if d == "acc_mua_gift":
        await q.answer()
        return await mua_gift_cmd(update, ctx)

    if d == "acc_nhan_thuong":
        await q.answer()
        rw_text, rw_kb = reward_center(uid)
        return await q.message.reply_text(rw_text, reply_markup=rw_kb, parse_mode=ParseMode.HTML)

    if d == "acc_chuyen_tien":
        await q.answer()
        return await chuyen_tien_cmd(update, ctx)

    if d == "acc_vip":
        await q.answer()
        vip_text, vip_kb = vip_screen(uid)
        return await q.message.reply_text(vip_text, reply_markup=vip_kb, parse_mode=ParseMode.HTML)

    if d == "acc_fan_cung":
        await q.answer("Tính năng đang được cập nhật!", show_alert=True)
        return

    if d == "acc_tich_luy":
        await q.answer()
        return await q.message.reply_text(
            f'{ce("💎")} <b>TÍCH LŨY NẠP</b>\n\n'
            f'Mốc 1: Nạp 50K - Cược 1M - Giftcode 20K\n'
            f'Mốc 2: Nạp 1M - Cược 15M - Giftcode 60K\n'
            f'Mốc 3: Nạp 5M - Cược 50M - Giftcode 170K\n'
            f'... (Xem chi tiết tại BOT)\n\n'
            f'{ce("⏰")} Code chỉ có hạn sử dụng trong ngày!',
            parse_mode=ParseMode.HTML)

    if d == "acc_ket_sat":
        await q.answer()
        return await q.message.reply_text(
            f'{ce("🔒")} <b>KẾT SÁT</b>\n\n'
            f'Số dư kết: 0\n'
            f'Số tiền gửi: 0\n'
            f'Kỳ hạn: Chưa có\n'
            f'Lãi dự kiến: 0\n\n'
            f'Tính năng đang được bảo trì, vui lòng quay lại sau!',
            parse_mode=ParseMode.HTML)

    # ===== GIỚI THIỆU =====
    if d == "ref_nhan_hh":
        await q.answer("Bạn chưa có hoa hồng để nhận!", show_alert=True)
        return
    if d == "ref_ruong":
        await q.answer("Bạn chưa đủ điều kiện nhận rương!", show_alert=True)
        return

    # ===== ĐUA TOP =====
    if d == "top_cuoc_ngay":
        await q.answer()
        return await q.message.reply_text(
            f'{ce("🔥")} <b>TOP CƯỢC NGÀY</b> {ce("🔥")}\n'
            f'Trả thưởng lúc 00:00 mỗi ngày\n\n'
            f'{ce("🥇")} Top 1: 100.000\n'
            f'{ce("🥈")} Top 2: 50.000\n'
            f'{ce("🥉")} Top 3: 30.000\n'
            f'🍕 Top 4: 25.000\n'
            f'🍕 Top 5-10: 10.000\n\n'
            f'Hiện chưa có dữ liệu xếp hạng!',
            parse_mode=ParseMode.HTML)
    if d == "top_thang_thua":
        await q.answer()
        return await q.message.reply_text(f'{ce("🎖")} <b>TOP THẮNG/THUA</b>\n\nHiện chưa có dữ liệu!', parse_mode=ParseMode.HTML)

    # ===== EVENT =====
    if d.startswith("ev_"):
        if not d.startswith("ev_nhan_") or d == "ev_nhan_vip":
            await q.answer()
        if d in ("ev_hc_ngay", "ev_hc_tuan", "ev_ht_ngay", "ev_ht_tuan"):
            ev_text, ev_kb = event_screen(uid, d[3:])
            return await q.message.reply_text(ev_text, reply_markup=ev_kb, parse_mode=ParseMode.HTML)
        if d == "ev_nhan_vip":
            return await q.message.reply_text(f'{ce("👑")} <b>NHẬN THƯỞNG VIP</b>\n\nCấp hiện tại: Đồng\nĐiểm VIP: 0\n\nMốc VIP 1: Thưởng 10.000 - Cần thêm 10 điểm\n...\n\nKhi đạt mốc VIP mới, nút Nhận thưởng VIP sẽ xuất hiện!', parse_mode=ParseMode.HTML)
        if d == "ev_tuong_tac":
            return await q.message.reply_text(f'{ce("🎁")} <b>TƯƠNG TÁC NHÓM +50K</b>\n\nTương tác đủ 200 tin nhắn trong nhóm để nhận 50.000đ!', parse_mode=ParseMode.HTML)
        if d == "ev_moi_de_tu":
            return await q.message.reply_text(f'{ce("👥")} <b>MỜI ĐỆ TỬ</b>\n\nVui lòng vào mục GIỚI THIỆU để lấy link mời!', parse_mode=ParseMode.HTML)
        
        # Xử lý nút Nhận Thưởng
        if d.startswith("ev_nhan_"):
            return await claim_rewards(update, ctx)

    # ===== NẠP TIỀN =====
    if d.startswith("paid_dep_"):
        try:
            amount = int(d.split("_")[2])
            now_str = get_vietnam_datetime_db()
            query("INSERT INTO deposit_history (user_id, amount, status, time) VALUES (%s, %s, %s, %s)", (uid, amount, 'pending', now_str))

            admin_kb = InlineKeyboardMarkup([
                [
                    btn("Duyệt", "✅", callback_data=f"app_dep_{uid}_{amount}"),
                    btn("Từ chối", "❌", callback_data=f"rej_dep_{uid}_{amount}")
                ]
            ])
            for admin_id in ADMIN_IDS:
                try:
                    await ctx.bot.send_message(
                        chat_id=admin_id,
                        text=(
                            f'{ce("🎁")} <b>YÊU CẦU XÁC NHẬN NẠP TIỀN</b>\n'
                            f'━━━━━━━━━━━━━━━━━━━━━\n'
                            f'{ce("👥")} <b>ID:</b> <code>{uid}</code>\n'
                            f'{ce("💰")} <b>Số tiền:</b> <code>{fmt_money(amount)}đ</code>\n'
                            f'{ce("⏰")} <b>Thời gian:</b> <code>{now_str}</code>'
                        ),
                        reply_markup=admin_kb,
                        parse_mode=ParseMode.HTML
                    )
                except Exception as e: pass

            await q.answer("✅ Đã gửi yêu cầu xác nhận thanh toán đến Admin!", show_alert=True)
            if q.message.caption:
                await q.message.edit_caption(
                    caption=q.message.caption_html + f"\n\n{ce('✅')} <b>Đã gửi yêu cầu xác nhận thanh toán. Vui lòng chờ Admin duyệt!</b>",
                    parse_mode=ParseMode.HTML,
                    reply_markup=None
                )
        except Exception as e:
            print(f"Lỗi paid_dep: {e}")
        return

    if d.startswith("app_dep_"):
        if uid not in ADMIN_IDS: return await q.answer("❌ Không có quyền!", show_alert=True)
        parts = d.split("_")
        target_id = int(parts[2])
        amount = int(parts[3])

        pending = query("SELECT id FROM deposit_history WHERE user_id=%s AND amount=%s AND status='pending' ORDER BY id DESC LIMIT 1", (target_id, amount))
        if not pending:
            await q.answer("⚠️ Yêu cầu này đã được xử lý rồi!", show_alert=True)
            try: await q.edit_message_text(f'{ce("⚠️")} Yêu cầu nạp này đã được xử lý trước đó.', parse_mode=ParseMode.HTML)
            except: pass
            return
        query("UPDATE deposit_history SET status='success', admin_id=%s WHERE id=%s", (uid, pending[0][0]))
        add_money(target_id, amount, f"Nạp tiền +{amount:,}đ")

        try:
            await ctx.bot.send_message(chat_id=LOG_GROUP_ID, text=f'{ce("✅")} <b>THÔNG BÁO DUYỆT NẠP TIỀN</b>\n{ce("👥")} ID: <code>{target_id}</code>\n{ce("💰")} Số tiền: <code>+{fmt_money(amount)}đ</code>\n{ce("👑")} Admin: <code>{uid}</code>', parse_mode=ParseMode.HTML)
        except: pass

        bonus_amount = int(amount * 0.10)
        if bonus_amount > 0:
            required_bet = bonus_amount * 2
            keyboard = InlineKeyboardMarkup([[
                btn("NHẬN KHUYẾN MÃI", "🎁", callback_data=f"accept_bonus_{target_id}_{bonus_amount}_{required_bet}"),
                btn("TỪ CHỐI", "❌", callback_data=f"reject_bonus_{target_id}")
            ]])
            try:
                await ctx.bot.send_message(target_id,
                    f'{ce("✅")} <b>NẠP TIỀN THÀNH CÔNG!</b>\n\n{ce("💰")} Số tiền nạp: <code>+{fmt_money(amount)}đ</code>\n{ce("💎")} Số dư hiện tại: <code>{fmt_money(get_balance(target_id))}đ</code>\n\n{ce("🎁")} <b>BẠN CÓ MUỐN NHẬN THÊM KHUYẾN MÃI?</b>\n━━━━━━━━━━━━━━━━━━━━━\n{ce("✨")} <b>Thưởng nạp 10%:</b> <code>+{fmt_money(bonus_amount)}đ</code>\n{ce("🎯")} <b>Yêu cầu cược:</b> x2 vòng (<code>{fmt_money(required_bet)}đ</code>)\n{ce("⚠️")} <b>Lưu ý:</b> Sau khi nhận thưởng phải x2 vòng cược tổng số dư tài khoản\n━━━━━━━━━━━━━━━━━━━━━\n\nVui lòng chọn bên dưới:',
                    reply_markup=keyboard, parse_mode=ParseMode.HTML)
            except Exception as e: pass

        await q.edit_message_text(f'{ce("✅")} ĐÃ DUYỆT NẠP ID <code>{target_id}</code> | <code>{fmt_money(amount)}đ</code>', parse_mode=ParseMode.HTML)
        return

    if d.startswith("rej_dep_"):
        if uid not in ADMIN_IDS: return await q.answer("❌ Không có quyền!", show_alert=True)
        parts = d.split("_")
        target_id = int(parts[2])
        amount = int(parts[3])
        query("UPDATE deposit_history SET status='rejected', admin_id=%s WHERE user_id=%s AND amount=%s AND status='pending'", (uid, target_id, amount))
        try: await ctx.bot.send_message(chat_id=target_id, text=f'{ce("❌")} Yêu cầu nạp <code>{fmt_money(amount)}đ</code> của bạn đã bị từ chối bởi Admin.', parse_mode=ParseMode.HTML)
        except: pass
        await q.edit_message_text(f'{ce("❌")} ĐÃ TỪ CHỐI NẠP ID <code>{target_id}</code> | <code>{fmt_money(amount)}đ</code>', parse_mode=ParseMode.HTML)
        return

    # dep_change phải xử lý TRƯỚC dep_ chung (trước đây bị nuốt mất)
    if d == "dep_change":
        await q.answer()
        qr_url, caption, kb = deposit_menu_content(uid)
        try:
            if q.message.photo:
                return await q.edit_message_media(media=InputMediaPhoto(media=qr_url, caption=caption, parse_mode=ParseMode.HTML), reply_markup=kb)
            else:
                await q.message.delete()
                return await ctx.bot.send_photo(chat_id=uid, photo=qr_url, caption=caption, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception as e:
            print(f"dep_change lỗi: {e}")
        return

    if d.startswith("dep_"):
        if d == "dep_support":
            await q.answer()
            return await q.message.reply_text(f'{ce("🔔")} <b>HỖ TRỢ NẠP TIỀN</b>\n\nVui lòng liên hệ Admin: @echcutodz\nHoặc dùng lệnh <code>/nap [số_tiền]</code> để tạo QR.', parse_mode=ParseMode.HTML)
        try:
            await q.answer()
            amount = int(d.split("_")[1])
            qr_url, caption = get_deposit_info(uid, amount)
            kb = InlineKeyboardMarkup([[btn("Đã Thanh Toán", "🔄", callback_data=f"paid_dep_{amount}")], [btn("Hỗ Trợ", "🔔", callback_data="dep_support")]])
            if q.message.photo:
                return await q.edit_message_media(media=InputMediaPhoto(media=qr_url, caption=caption, parse_mode=ParseMode.HTML), reply_markup=kb)
            else:
                await q.message.delete()
                return await ctx.bot.send_photo(chat_id=uid, photo=qr_url, caption=caption, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception as e: pass
        return

    if d.startswith("mt_toggle_") or d in ["mt_turnoff_all", "mt_turnon_all"]:
        return await handle_mt_toggle_callback(update, ctx)

    if d == "his_deposit":
        await q.answer()
        data = query("SELECT amount, time FROM deposit_history WHERE user_id=%s AND status='success' ORDER BY id DESC LIMIT 10", (uid,))
        text = f'{ce("📥")} <b>10 GIAO DỊCH NẠP GẦN NHẤT:</b>\n\n'
        if not data: text += "Trống."
        else:
            for row in data: text += f'{ce("✔️")} <code>+{fmt_money(row[0])}đ</code> | <i>{row[1]}</i>\n'
        return await ctx.bot.send_message(uid, text, parse_mode=ParseMode.HTML)

    if d == "his_withdraw":
        await q.answer()
        data = query("SELECT amount, status, time FROM withdraw_history WHERE user_id=%s ORDER BY id DESC LIMIT 10", (uid,))
        text = f'{ce("📤")} <b>10 GIAO DỊCH RÚT GẦN NHẤT:</b>\n\n'
        if not data: text += "Trống."
        else:
            for row in data:
                status_icon = ce("✔️") if row[1] == "success" else ce("❌") if row[1] == "rejected" else ce("⏰")
                text += f'{status_icon} <code>{fmt_money(row[0])}đ</code> | {row[1]} | <i>{row[2]}</i>\n'
        return await ctx.bot.send_message(uid, text, parse_mode=ParseMode.HTML)

    if d.startswith("accept_bonus_"):
        parts = d.split("_")
        target_id = int(parts[2])
        bonus_amount = int(parts[3])
        required_bet = int(parts[4])
        if q.from_user.id != target_id: return await q.answer("❌ Không phải yêu cầu của bạn!", show_alert=True)
        existing = query("SELECT 1 FROM user_bonus WHERE user_id=%s", (target_id,))
        if existing:
            await q.answer("❌ Bạn đang có khuyến mãi chưa hoàn thành cược!", show_alert=True)
            return
        add_bonus_with_requirement(target_id, bonus_amount, 2)
        await q.message.edit_text(
            f'{ce("🎁")} <b>ĐÃ NHẬN KHUYẾN MÃI!</b>\n'
            f'{ce("💰")} <code>+{fmt_money(bonus_amount)}đ</code>\n'
            f'{ce("🎯")} Yêu cầu cược: <code>{fmt_money(required_bet)}đ</code>\n'
            f'{ce("⚠️")} <b>Lưu ý:</b> Sau khi nhận thưởng phải x2 vòng cược',
            parse_mode=ParseMode.HTML)
        return

    if d.startswith("reject_bonus_"):
        target_id = int(d.split("_")[2])
        if q.from_user.id != target_id: return await q.answer("❌ Không phải yêu cầu của bạn!", show_alert=True)
        await q.message.edit_text(
            f'{ce("❌")} <b>Đã từ chối khuyến mãi!</b>\n{ce("💰")} Số dư: <code>{fmt_money(get_balance(target_id))}đ</code>',
            parse_mode=ParseMode.HTML)
        return

    # ===== ADMIN: QUẢN LÝ USER =====
    if d.startswith("adm_page_"):
        if uid not in ADMIN_IDS: return await q.answer()
        await q.answer()
        new_page = int(d.split("_")[2])
        return await all_user(update, ctx, page=new_page)

    if d.startswith("adm_manage_"):
        if uid not in ADMIN_IDS: return await q.answer()
        await q.answer()
        parts = d.split("_")
        target_id = int(parts[2])
        current_page = int(parts[3]) if len(parts) > 3 else 0
        return await show_user_manage(q, target_id, current_page)

    if d.startswith("adm_act_"):
        if uid not in ADMIN_IDS: return await q.answer()
        parts = d.split("_")
        act = parts[2]
        tid = int(parts[3])
        current_page = int(parts[4]) if len(parts) > 4 else 0
        if act == "ban": query("INSERT INTO banned VALUES(%s) ON CONFLICT (user_id) DO NOTHING", (tid,))
        elif act == "unban": query("DELETE FROM banned WHERE user_id=%s", (tid,))
        await q.answer("✅ OK!")
        # Trước đây gọi lại handle_callback -> lặp vô hạn. Giờ chỉ vẽ lại bảng user.
        return await show_user_manage(q, tid, current_page)

    if d.startswith("tg_mt_"):
        if uid not in ADMIN_IDS: return await q.answer("❌ Không có quyền!", show_alert=True)
        key = d.replace("tg_", "")
        new_val = "0" if check_mt(key) else "1"
        query("UPDATE settings SET value=%s WHERE key=%s", (new_val, key))
        await q.answer("✅ Đã cập nhật!")
        return await baotri_cmd(update, ctx)

    if d == "close_admin":
        if uid not in ADMIN_IDS: return await q.answer()
        await q.message.delete()
        return

    # ===== DUYỆT / TỪ CHỐI RÚT =====
    if d.startswith("ok_") or d.startswith("no_"):
        if uid not in ADMIN_IDS: return await q.answer()
        act, u_id, amt = d.split("_")
        u_id, amt = int(u_id), int(amt)
        pending = query("SELECT id FROM withdraw_history WHERE user_id=%s AND amount=%s AND status='pending' ORDER BY id DESC LIMIT 1", (u_id, amt))
        if not pending:
            await q.answer("⚠️ Yêu cầu này đã được xử lý rồi!", show_alert=True)
            try: await q.edit_message_text(f'{ce("⚠️")} Yêu cầu rút này đã được xử lý trước đó.', parse_mode=ParseMode.HTML)
            except: pass
            return
        wid = pending[0][0]
        if act == "ok":
            query("UPDATE withdraw_history SET status='success', admin_id=%s WHERE id=%s", (uid, wid))
            try: await ctx.bot.send_message(chat_id=LOG_GROUP_ID, text=f'{ce("📤")} <b>THÔNG BÁO RÚT TIỀN</b>\n{ce("👥")} ID: <code>{u_id}</code>\n{ce("💰")} Số tiền: <code>{fmt_money(amt)}đ</code>\n{ce("✅")} Đã duyệt!', parse_mode=ParseMode.HTML)
            except Exception as e: pass
            try: await ctx.bot.send_message(u_id, f'{ce("✅")} Yêu cầu rút <code>{fmt_money(amt)}đ</code> đã được duyệt!', parse_mode=ParseMode.HTML)
            except: pass
            await q.edit_message_text(f'{ce("✅")} ĐÃ DUYỆT ID <code>{u_id}</code> | <code>{fmt_money(amt)}đ</code>', parse_mode=ParseMode.HTML)
        else:
            query("UPDATE withdraw_history SET status='rejected', admin_id=%s, admin_note='Từ chối' WHERE id=%s", (uid, wid))
            add_money(u_id, amt, "Hoàn tiền rút")
            try: await ctx.bot.send_message(chat_id=LOG_GROUP_ID, text=f'{ce("❌")} <b>THÔNG BÁO TỪ CHỐI RÚT</b>\n{ce("👥")} ID: <code>{u_id}</code>\n{ce("💰")} Số tiền: <code>{fmt_money(amt)}đ</code>\n{ce("🔄")} Đã hoàn tiền về ví!', parse_mode=ParseMode.HTML)
            except Exception as e: pass
            try: await ctx.bot.send_message(u_id, f'{ce("❌")} Yêu cầu rút <code>{fmt_money(amt)}đ</code> bị từ chối.\n{ce("🔄")} Tiền đã được hoàn về số dư của bạn.', parse_mode=ParseMode.HTML)
            except: pass
            await q.edit_message_text(f'{ce("❌")} TỪ CHỐI ID <code>{u_id}</code> | <code>{fmt_money(amt)}đ</code>', parse_mode=ParseMode.HTML)
        return

    await q.answer()

application = ApplicationBuilder().token(TOKEN).build()

application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("lienket", lien_ket))
application.add_handler(CommandHandler("rut", rut))
application.add_handler(CommandHandler("nap", nap_cmd))
application.add_handler(CommandHandler("code", nhap_code))
application.add_handler(CommandHandler("his", history_pro))
application.add_handler(CommandHandler("checkprogress", check_bet_progress_cmd))
application.add_handler(CommandHandler("sd", sd_cmd))
application.add_handler(CommandHandler("lh", lh_cmd))
application.add_handler(CommandHandler("mp", mp_cmd))
application.add_handler(CommandHandler("bcr", baccarat_cmd))
application.add_handler(CommandHandler("xd4", xd4_cmd))
application.add_handler(CommandHandler("txmd5", txmd5_cmd))
application.add_handler(CommandHandler("bc", bc_cmd))
application.add_handler(CommandHandler("xd6", xd6_cmd))
application.add_handler(CommandHandler("group_status", group_status_cmd))

application.add_handler(CommandHandler("chuyen", chuyen_tien_cmd))
application.add_handler(CommandHandler("muagift", mua_gift_cmd))
application.add_handler(CommandHandler("doidiemvip", doi_diem_vip_cmd))
application.add_handler(CommandHandler("lschoi", ls_choi_cmd))
application.add_handler(CommandHandler("lschtx", ls_room_tx_cmd))

application.add_handler(CommandHandler("naptien", naptien_admin))
application.add_handler(CommandHandler("add", add))
application.add_handler(CommandHandler("sub", sub))
application.add_handler(CommandHandler("ban", ban))
application.add_handler(CommandHandler("unban", unban))
application.add_handler(CommandHandler("stats", stats))
application.add_handler(CommandHandler("all", all_user))
application.add_handler(CommandHandler("info", admin_info))
application.add_handler(CommandHandler("hisall", history_all_admin))
application.add_handler(CommandHandler("send", broadcast))
application.add_handler(CommandHandler("rep", reply_user))
application.add_handler(CommandHandler("check", check_user_history))
application.add_handler(CommandHandler("thongke", dashboard_cmd))
application.add_handler(CommandHandler("tong", tong_cmd))
application.add_handler(CommandHandler("soduall", soduall_cmd))
application.add_handler(CommandHandler("resetsdall", resetsdall_cmd))
application.add_handler(CommandHandler("resetall", resetsdall_cmd))
application.add_handler(CommandHandler("xoalsall", xoalsall_cmd))
application.add_handler(CommandHandler("xoals", xoals_user_cmd))
application.add_handler(CommandHandler("setname", set_bot_name_cmd))
application.add_handler(CommandHandler("sethu", sethu_cmd))
application.add_handler(CommandHandler("taocode", tao_code))
application.add_handler(CommandHandler("taocodeall", taocodeall_cmd))
application.add_handler(CommandHandler("xoacode", xoacode_cmd))
application.add_handler(CommandHandler("kmnap", kmnap_cmd))
application.add_handler(CommandHandler("kmnapvc", kmnapvc_cmd))
application.add_handler(CommandHandler("checkprogressadmin", admin_check_bet_progress_cmd))
application.add_handler(CommandHandler("resetprogress", reset_progress))
application.add_handler(CommandHandler("codenap", gift_flow_start))
application.add_handler(CommandHandler("taogift", gift_flow_start))
application.add_handler(CommandHandler("xoagift", xoagift_cmd))
application.add_handler(CommandHandler("dsgift", dsgift_cmd))
application.add_handler(CommandHandler("sethoancuoc", sethoancuoc_cmd))
application.add_handler(CommandHandler("baotri", baotri_cmd))
application.add_handler(CommandHandler("baotriht", baotri_he_thong_cmd))
application.add_handler(CommandHandler("baotriall", baotri_hethong_cmd))
application.add_handler(CommandHandler("baotritc", baotri_tong_cong_cmd))
application.add_handler(CommandHandler("tatroom", tatroom_cmd))

application.add_handler(CallbackQueryHandler(handle_callback))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_message))

_bg_tasks = []

async def main():
    global _bot_instance
    await application.initialize()
    await application.start()
    _bot_instance = application.bot
    _bg_tasks.append(asyncio.create_task(reward_settle_loop(application.bot)))
    for gid in GROUP_IDS:
        try:
            room_betting_enabled[gid] = True
            asyncio.create_task(run_dice_game_cycle(application.bot, gid, gid))
            print(f"✅ Đã khởi động game cho nhóm {gid}")
        except Exception as e:
            print(f"Lỗi nhóm {gid}: {e}")
    await application.updater.start_polling(drop_pending_updates=True)
    print("🤖 BOT ĐÃ ONLINE...")
    await asyncio.Event().wait()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        print("🛑 Bot đã dừng.")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        traceback.print_exc()
