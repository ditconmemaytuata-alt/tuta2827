import os
import re
import random
import asyncio
import hashlib
import csv
import traceback
import html
from urllib.parse import urlencode
from datetime import datetime, timedelta
from io import BytesIO

import psycopg2
from psycopg2 import extras
import pytz
from telegram import (Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto, ChatPermissions, BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats, ForceReply)
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler, ApplicationHandlerStop
from telegram.constants import ParseMode
import aiohttp
from aiohttp import web

# ============================================================
# CẤU HÌNH CHUNG
# ============================================================
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
SEPAY_API_KEY = os.getenv("SEPAY_API_KEY", "")  # Bắt buộc cấu hình bằng biến môi trường; không hardcode khóa bí mật

ADMIN_IDS = [5633649201, 7884394252]
BOT_USERNAME = "Jav88gamebot"
ROOM_LINK = "https://t.me/jav88sanhu"
MIN_WITHDRAW = 50000
LOG_GROUP_ID = -1004375247819

# THÔNG TIN NGÂN HÀNG MỚI
BANK_ID = "MB"
ACCOUNT_NO = "007399999"
ACCOUNT_NAME = "NGO VIET HOANG"

_bot_instance = None
GROUP_IDS = [-1004375247819]

group_games = {}
room_betting_enabled = {}
game_history = {}
SESSION_COUNTER = {"value": 0}
pending_inputs = {}

VIETNAM_TZ = pytz.timezone('Asia/Ho_Chi_Minh')

def get_vietnam_time():
    return datetime.now(VIETNAM_TZ)

def get_vietnam_date():
    return get_vietnam_time().strftime("%d/%m/%Y")

def get_vietnam_datetime_db():
    return get_vietnam_time().strftime("%H:%M - %d/%m/%Y")

# ============================================================
# CUSTOM EMOJI MAPPING (CẬP NHẬT THEO DANH SÁCH MỚI)
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
    "✔️": "5206607081334906820", "🆘": "5429262837409138106", "✏️": "5395444784611480792",
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
    # Cập nhật từ danh sách mới
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
    "🛫": "5463424023734014980", "🧩": "5213306719215577669", "🌱": "5474417568053745249",
    "🪧": "5429278861932124623", "🗺": "5235794253149394263", "🫴": "5440457429147997980",
    "🏷️": "5298877105000439431", "📩": "5472239203590888751", "⛏️": "5204006143629744642",
    "🪂": "5461128651477111908", "🧾": "5204242830687494041", "👛": "5215420556089776398",
    "🔑": "5307843983102204243", "💶": "5197369495739455200", "💷": "5377775044342599336",
    "💴": "5197161121106123533", "🪣": "5399909394525737759", "🌎": "5224450179368767019",
    "🐂": "5411233191765759009", "📇": "5332724926216428039", "🧮": "5303214794336125778",
    "⏱": "5382194935057372936", "🐳": "5400362079783770689", "🔭": "5379999674193172777",
    "💼": "5445221832074483553", "🛡": "5197288647275071607", "🪙": "5382164415019768638",
    "🛒": "5440841102871517055", "🔗": "5440410042773824003", "🎁": "5442939099906325301",
    "💱": "5377336227533969892", "📊": "5203993413346680064", "🏦": "5238132025323444613",
    "🪙": "5296339823005557585", "🏅": "5424746623462823358", "💵": "5201873447554145566",
    "🪙": "5296355151743838259", "🚀": "5188481279963715781", "🎯": "5461009483314517035",
    "💬": "5235570365094188078", "⛏": "5461047575379466857", "🪙": "5381975814415866082",
    "⌨️": "5298975240708187753", "💵": "5197434882321567830", "🪙": "5377505475015235101",
    "🪙": "5377746319601324795", "🪙": "5202064723922670546", "🪙": "5202113974312653146",
    "🪙": "5377620962390857342", "💵": "5201692367437974073", "🪙": "5199552030615558774",
    "💳": "5445353829304387411", "✍️": "5197269100878907942", "🗺": "5330320040883411678",
    "🛫": "5201691993775818138", "💬": "5303138782004924588", "🎯": "5310278924616356636",
    "🛍": "5294167145079395967", "🧾": "5444856076954520455", "📉": "5429518319243775957",
    "🛒": "5312361253610475399", "⚖️": "5400250414929041085", "📊": "5190806721286657692",
    "🍀": "5305699699204837855", "🐷": "5312123810638483121", "💰": "5278467510604160626",
    "📈": "5197503331215361533", "🚀": "5195033767969839232", "🧮": "5190741648237161191",
    "💵": "5291914649481007565", "🪙": "5264713049637409446", "💸": "5231005931550030290",
    "💰": "6307611167296590395", "🍀": "6307395821931335527", "❤️": "6307312246162723113",
    "👋": "6309717230279986734", "🥰": "6336722047606985714", "🇻🇳": "6114176908415472855",
    "🎁": "6093579821516854607", "🎁": "6057343663476839832", "🎁": "6057478581284509420",
    "😘": "6251474231045921194", "🛍": "5278702045883292456", "💱": "5312441427764989435",
    "🗓": "5274055917766202507", "🧲": "5377535110289576661"
}

# Ưu tiên ID emoji premium mới do chủ bot cung cấp.
CUSTOM_EMOJI.update({
    "🗑": "5445267414562389170", "⌛": "5386367538735104399",
    "🚨": "5395695537687123235", "✏️": "5395444784611480792",
    "✉️": "5253742260054409879", "➕": "5397916757333654639",
    "📍": "5391032818111363540", "🔄": "5375338737028841420",
    "🔝": "5415655814079723871", "🔗": "5271604874419647061",
    "🖥": "5282843764451195532", "🛡": "5251203410396458957",
    "➡️": "5416117059207572332", "💸": "5231005931550030290",
    "📌": "5397782960512444700", "🚗": "6280407793631498213",
    "😃": "6111737246732262016", "🇻🇳": "6190651897792174993",
    "🔋": "5307905813451397794", "💳": "5445353829304387411",
    "⛏": "5197371802136892976", "📥": "5443127283898405358",
    "💰": "5278467510604160626", "🏦": "5332455502917949981",
    "↗️": "5429651785352501917", "🛒": "5312361253610475399",
    "⚖️": "5400250414929041085", "💻": "5193177581888755275",
    "🖼": "5262517101578443800", "💡": "5262844652964303985",
    "🎯": "5256131095094652290", "📞": "5285238101344544669",
    "🎲": "5280816565657300091", "🔓": "5291873529464122510",
    "☺️": "5238015713314086319", "🖐": "5237759703198474072",
    "💩": "5235622845299565321", "🚘": "5240037474679398914",
    "😳": "5238083517962793068", "😏": "5237903859480796749",
    "🏃‍♀️": "5237981615568723131", "😱": "5235640209852343235",
    "🤩": "5195357093107868151", "😕": "5197226061011623665",
    "🍌": "5237784970491074950", "🤓": "5240209101572545926",
    "😡": "5240408207666455054", "🔫": "5235762367312173706",
    "😨": "5242500342070909767", "😭": "5460741258311900209",
    "🤪": "5240076365608264313", "👅": "5239944638961294456",
    "😧": "5237721297600912488", "🍔": "5239948040575393823",
    "🐶": "5242395424609803673", "🤫": "6226686020570584326",
    "🤘": "6163685838250054493", "🌟": "6195233300752111114",
    "🍀": "6161347086823461532", "💥": "6161101981629814014",
    "🎖": "6165926565638051547", "🤬": "6168156972219635148",
    "🍑": "6165529117954413678", "🕺": "6186015776948885249",
    "🌷": "6197378228894568973", "🐉": "6188171511229060434",
    "👋": "6190629722876023613", "😍": "6192639363843626187",
    "😇": "6195191910152279859", "🚊": "6208671312823456804",
    "🤨": "6208304964998010180",
})
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

# ============================================================
# ENGINE EMOJI PREMIUM — TỰ ĐỘNG ĐỔI MỌI EMOJI THƯỜNG -> EMOJI PREMIUM
#  • Mọi tin nhắn / caption gửi qua bot (HTML hoặc văn bản thường) đều được đổi.
#  • Mọi nút inline có emoji đứng đầu sẽ được chuyển thành icon premium của nút.
#  • Emoji chưa có bản premium riêng sẽ dùng emoji premium gần nghĩa nhất (bảng ICON_ALIAS).
# ============================================================
import functools
import telegram as _tg

# Bổ sung bảng quy đổi cho các emoji chưa có ID premium riêng (giữ nguyên các biểu tượng
# mang ý nghĩa game như ♠♥♦♣ và 🦐🐟🐓 của Bầu Cua để không bị sai nghĩa).
ICON_ALIAS.update({
    "📅": "🗓", "🎟": "🎁", "🏁": "🚩", "📦": "🛍", "⏸️": "⌛", "⏸": "⌛",
    "🧰": "🛠", "🔎": "🔭", "📋": "🧾", "📄": "📜", "📝": "✏️", "🤖": "💻",
    "🛑": "⛔️", "🎃": "🎉", "⚔️": "🔥", "⚔": "🔥", "⚫️": "🔒", "⚪️": "🏳️",
})

def _norm_emoji(s: str) -> str:
    return s.replace("\ufe0f", "")

_PREMIUM_MAP = {}
for _k, _v in CUSTOM_EMOJI.items():
    if _k.isascii() or _k == "©":
        continue
    _PREMIUM_MAP[_norm_emoji(_k)] = _v
for _k, _target in ICON_ALIAS.items():
    _eid = CUSTOM_EMOJI.get(_target)
    if _eid and _norm_emoji(_k) not in _PREMIUM_MAP:
        _PREMIUM_MAP[_norm_emoji(_k)] = _eid

# Giữ nguyên các bi tròn màu thường (🔵 🔴 ⚪ ⚫) trong tin nhắn - không đổi sang cờ/khiên/khóa premium
for _plain in ("🔵", "🔴", "⚪", "⚫"):
    _PREMIUM_MAP.pop(_norm_emoji(_plain), None)

def _emoji_pattern(key: str) -> str:
    # Cho phép (tuỳ chọn) ký tự variation selector U+FE0F sau từng ký tự.
    return "".join(re.escape(ch) + "\ufe0f?" for ch in key)

_EMOJI_ALT = "|".join(_emoji_pattern(k) for k in sorted(_PREMIUM_MAP, key=len, reverse=True))
# Nhóm 1: thẻ tg-emoji có sẵn (giữ nguyên) | Nhóm 2: thẻ HTML (giữ nguyên) | Nhóm 3: emoji thường
_EMOJI_RE = re.compile(r"(<tg-emoji\b[^>]*>.*?</tg-emoji>)|(<[^>]+>)|(" + _EMOJI_ALT + r")", re.S)
_BTN_EMOJI_RE = re.compile(_EMOJI_ALT)

def premiumize(text):
    """Đổi toàn bộ emoji thường trong chuỗi HTML thành <tg-emoji> premium."""
    if not text or not isinstance(text, str):
        return text
    def _sub(m):
        if m.group(1) or m.group(2):
            return m.group(0)
        raw = m.group(3)
        eid = _PREMIUM_MAP.get(_norm_emoji(raw))
        return f'<tg-emoji emoji-id="{eid}">{raw}</tg-emoji>' if eid else raw
    return _EMOJI_RE.sub(_sub, text)

def _has_plain_emoji(text: str) -> bool:
    return any(m.group(3) for m in _EMOJI_RE.finditer(text))

def _prep_text(text, parse_mode):
    """Trả về (text_mới, parse_mode_mới). Văn bản thường sẽ được escape rồi chuyển sang HTML."""
    pm = getattr(parse_mode, "value", parse_mode)
    if isinstance(pm, str) and pm.upper() == "HTML":
        return premiumize(text), parse_mode
    if pm is None and _has_plain_emoji(text):
        return premiumize(html.escape(text, quote=False)), "HTML"
    return text, parse_mode

def _wrap_bot_text_method(name, text_kw, text_pos=None, pm_pos=None):
    orig = getattr(_tg.Bot, name, None)
    if orig is None or getattr(orig, "_premium_wrapped", False):
        return
    @functools.wraps(orig)
    async def wrapper(self, *args, **kwargs):
        try:
            args = list(args)
            where = None
            if text_kw in kwargs:
                where = "kw"
            elif text_pos is not None and len(args) > text_pos:
                where = "pos"
            if where and not kwargs.get("entities") and not kwargs.get("caption_entities"):
                val = kwargs[text_kw] if where == "kw" else args[text_pos]
                # Nếu parse_mode truyền theo vị trí mà không biết vị trí -> bỏ qua để an toàn.
                extra_pos = text_pos is not None and len(args) > text_pos + 1 and pm_pos is None
                if isinstance(val, str) and val and not extra_pos:
                    if "parse_mode" in kwargs:
                        pm = kwargs["parse_mode"]
                    elif pm_pos is not None and len(args) > pm_pos:
                        pm = args[pm_pos]
                    else:
                        pm = None
                    new_val, new_pm = _prep_text(val, pm)
                    if new_val != val or new_pm is not pm:
                        if where == "kw":
                            kwargs[text_kw] = new_val
                        else:
                            args[text_pos] = new_val
                        if "parse_mode" in kwargs or not (pm_pos is not None and len(args) > pm_pos):
                            kwargs["parse_mode"] = new_pm
                        else:
                            args[pm_pos] = new_pm
        except Exception as _e:
            print(f"[premium-emoji] bỏ qua do lỗi: {_e}")
        return await orig(self, *args, **kwargs)
    wrapper._premium_wrapped = True
    setattr(_tg.Bot, name, wrapper)

def _prep_media(media):
    try:
        cap = getattr(media, "caption", None)
        if cap and isinstance(cap, str):
            old_pm = getattr(media, "parse_mode", None)
            new_cap, new_pm = _prep_text(cap, old_pm)
            if new_cap != cap:
                object.__setattr__(media, "caption", new_cap)
                if new_pm is not old_pm:
                    object.__setattr__(media, "parse_mode", new_pm)
    except Exception as _e:
        print(f"[premium-emoji] media bỏ qua: {_e}")

def _wrap_bot_media_method(name):
    orig = getattr(_tg.Bot, name, None)
    if orig is None or getattr(orig, "_premium_wrapped", False):
        return
    @functools.wraps(orig)
    async def wrapper(self, *args, **kwargs):
        media = kwargs.get("media")
        if media is not None:
            if isinstance(media, (list, tuple)):
                for m in media:
                    _prep_media(m)
            else:
                _prep_media(media)
        return await orig(self, *args, **kwargs)
    wrapper._premium_wrapped = True
    setattr(_tg.Bot, name, wrapper)

_wrap_bot_text_method("send_message", "text", text_pos=1, pm_pos=2)
_wrap_bot_text_method("edit_message_text", "text", text_pos=0)
for _m in ("send_photo", "send_document", "send_animation", "send_video", "send_audio",
           "send_voice", "edit_message_caption", "copy_message"):
    _wrap_bot_text_method(_m, "caption")
for _m in ("edit_message_media", "send_media_group"):
    _wrap_bot_media_method(_m)

from telegram import InlineKeyboardButton as _PTBInlineKeyboardButton

class InlineKeyboardButton(_PTBInlineKeyboardButton):
    """Nút inline: emoji đứng đầu tự thành icon premium; emoji thường còn sót trong chữ được loại bỏ."""
    __slots__ = ()

    def __init__(self, text, *args, **kwargs):
        try:
            original = text
            api_kwargs = dict(kwargs.get("api_kwargs") or {})
            body = str(text).strip()
            if "icon_custom_emoji_id" not in api_kwargs:
                m = _BTN_EMOJI_RE.match(body)
                if m:
                    eid = _PREMIUM_MAP.get(_norm_emoji(m.group(0)))
                    rest = body[m.end():].strip()
                    if eid and rest:
                        api_kwargs["icon_custom_emoji_id"] = eid
                        body = rest
            cleaned = re.sub(r"\s{2,}", " ", _BTN_EMOJI_RE.sub("", body)).strip()
            text = cleaned or original
            if api_kwargs:
                kwargs["api_kwargs"] = api_kwargs
        except Exception as _e:
            print(f"[premium-emoji] nút bỏ qua: {_e}")
        super().__init__(text, *args, **kwargs)


def fmt_money(amount: int) -> str:
    return f"{amount:,}".replace(",", ".")

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def query(q, args=()):
    conn = get_db_connection()
    cur = conn.cursor()
    res = None
    try:
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
    time TEXT,
    ref_code TEXT
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
CREATE TABLE IF NOT EXISTS interaction_reward_claims (
    user_id BIGINT NOT NULL,
    group_id BIGINT NOT NULL,
    date TEXT NOT NULL,
    milestone INTEGER NOT NULL,
    code TEXT,
    reward_amount BIGINT DEFAULT 0,
    created_at TEXT,
    PRIMARY KEY (user_id, group_id, date, milestone)
)
""")
query("""
CREATE TABLE IF NOT EXISTS interaction_message_guard (
    user_id BIGINT NOT NULL,
    group_id BIGINT NOT NULL,
    last_text TEXT,
    last_at TIMESTAMPTZ,
    PRIMARY KEY (user_id, group_id)
)
""")
query("""
CREATE TABLE IF NOT EXISTS interaction_top_rewards (
    user_id BIGINT NOT NULL,
    group_id BIGINT NOT NULL,
    date TEXT NOT NULL,
    rank INTEGER NOT NULL,
    reward_amount BIGINT NOT NULL DEFAULT 0,
    code TEXT,
    created_at TEXT,
    PRIMARY KEY (user_id, group_id, date)
)
""")
query("""
CREATE TABLE IF NOT EXISTS interaction_top_settlements (
    group_id BIGINT NOT NULL,
    date TEXT NOT NULL,
    settled_at TEXT,
    PRIMARY KEY (group_id, date)
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
query("ALTER TABLE giftcodes ADD COLUMN IF NOT EXISTS milestone INTEGER")
query("ALTER TABLE giftcodes ADD COLUMN IF NOT EXISTS claim_date DATE")
query("CREATE UNIQUE INDEX IF NOT EXISTS uq_tichluy_user_milestone_day ON giftcodes(bound_user, milestone, claim_date) WHERE ctype='TICHLUY' AND bound_user IS NOT NULL AND milestone IS NOT NULL AND claim_date IS NOT NULL")

query("CREATE TABLE IF NOT EXISTS history (user_id BIGINT, amount BIGINT, note TEXT, time TEXT)")
query("ALTER TABLE history ADD COLUMN IF NOT EXISTS id SERIAL")
query("CREATE TABLE IF NOT EXISTS banned (user_id BIGINT PRIMARY KEY)")
query("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")

# Thêm cột ref_code nếu chưa có
query("ALTER TABLE deposit_history ADD COLUMN IF NOT EXISTS ref_code TEXT")

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

def add_bonus_with_requirement(user_id, bonus_amount, required_multiplier=None):
    if required_multiplier is None:
        required_multiplier = PROMO_WAGER_MULT
    required_bet = int(round(bonus_amount * required_multiplier))
    now_str = get_vietnam_datetime_db()
    query("DELETE FROM user_bonus WHERE user_id=%s", (user_id,))
    query("INSERT INTO user_bonus (user_id, bonus_amount, required_bet, current_bet, created_at) VALUES (%s, %s, %s, %s, %s)",
          (user_id, bonus_amount, required_bet, 0, now_str))
    add_money(user_id, bonus_amount, f"Khuyến mãi nạp +{bonus_amount:,}đ (yêu cầu cược x{required_multiplier})")
    return required_bet

# ============================================================
# KHUYẾN MÃI NẠP
#  • 15% mỗi lần nạp, MỖI NGÀY CHỈ NHẬN 1 LẦN (đang có vòng cược khác vẫn nhận, cược được cộng dồn)
#  • +3% thưởng thêm cho MỖI lệnh nạp (không giới hạn số lần)
#  • GIỜ VÀNG tự động bật/tắt hằng ngày: 10:00-11:00 và 20:00-21:00 (giờ Việt Nam)
#  • Admin có thể ép bật/tắt bằng /kmgio on|off|auto
# ============================================================
PROMO_PCT = 15                              # % khuyến mãi nạp (1 lần/ngày)
PROMO_ORDER_PCT = 3                         # % thưởng thêm cho mỗi lệnh nạp
PROMO_WAGER_MULT = 2.8                      # khuyến mãi (15%, admin tặng...) phải cược x2.8 vòng
PROMO_ORDER_WAGER_MULT = 1                  # thưởng 3% mỗi lệnh nạp chỉ cần cược x1 vòng
PROMO_GOLDEN_WINDOWS = ((10, 11), (20, 21)) # [giờ bắt đầu, giờ kết thúc) -> 10:00-11:00 và 20:00-21:00
PROMO_ALWAYS_ON = False                     # True = khuyến mãi 15% luôn mở cả ngày (không phụ thuộc giờ vàng)

query("CREATE TABLE IF NOT EXISTS promo_daily_claims (user_id BIGINT, claim_date TEXT, amount BIGINT DEFAULT 0, PRIMARY KEY (user_id, claim_date))")
query("CREATE TABLE IF NOT EXISTS promo_offer_done (chat_id BIGINT, message_id BIGINT, PRIMARY KEY (chat_id, message_id))")

def promo_mode():
    m = (get_setting("promo_mode", "auto") or "auto").lower()
    return m if m in ("auto", "on", "off") else "auto"

def promo_golden_now():
    h = get_vietnam_time().hour
    return any(a <= h < b for a, b in PROMO_GOLDEN_WINDOWS)

def promo_is_active():
    m = promo_mode()
    if m == "on":
        return True
    if m == "off":
        return False
    return PROMO_ALWAYS_ON or promo_golden_now()

def promo_windows_text():
    return " và ".join(f"{a:02d}:00-{b:02d}:00" for a, b in PROMO_GOLDEN_WINDOWS)

def promo_today_key():
    return get_vietnam_time().strftime("%Y-%m-%d")

def promo_claimed_today(uid):
    return bool(query("SELECT 1 FROM promo_daily_claims WHERE user_id=%s AND claim_date=%s", (uid, promo_today_key())))

def promo_claim_daily(uid, amount):
    """Đánh dấu đã nhận 15% hôm nay. Trả về True nếu lần đầu trong ngày."""
    r = query("INSERT INTO promo_daily_claims (user_id, claim_date, amount) VALUES (%s,%s,%s) "
              "ON CONFLICT DO NOTHING RETURNING user_id", (uid, promo_today_key(), amount))
    return bool(r)

def add_promo_bonus(uid, bonus_main, bonus_order=0, note="Khuyến mãi nạp"):
    """Cộng thưởng + CỘNG DỒN yêu cầu cược vào vòng cược hiện có (nếu đang có).
    bonus_main: phần khuyến mãi phải cược x2.8; bonus_order: phần thưởng 3%/lệnh chỉ cược x1."""
    total = bonus_main + bonus_order
    required = int(round(bonus_main * PROMO_WAGER_MULT)) + int(round(bonus_order * PROMO_ORDER_WAGER_MULT))
    add_wager_requirement(uid, total, required)
    add_money(uid, total, f"{note} +{total:,}đ (yêu cầu cược {fmt_money(required)}đ)")
    return required

def promo_build_offer(uid, amount):
    """Trả về (text, keyboard) của lời mời nhận khuyến mãi sau khi nạp, hoặc None nếu không có gì để tặng."""
    p3 = int(amount * PROMO_ORDER_PCT / 100)
    eligible15 = promo_is_active() and not promo_claimed_today(uid)
    p15 = int(amount * PROMO_PCT / 100) if eligible15 else 0
    total = p15 + p3
    if total <= 0:
        return None
    req_main = int(round(p15 * PROMO_WAGER_MULT))
    req_order = int(round(p3 * PROMO_ORDER_WAGER_MULT))
    required = req_main + req_order
    lines = [
        f'{ce("🎁")} <b>BẠN CÓ MUỐN NHẬN THÊM KHUYẾN MÃI?</b>',
        '━━━━━━━━━━━━━━━━━━━━━',
    ]
    if eligible15 and promo_mode() == "auto" and promo_golden_now():
        lines.append(f'{ce("⏰")} <b>ĐANG LÀ GIỜ VÀNG NẠP!</b>')
    if eligible15:
        lines.append(f'{ce("✨")} <b>Thưởng nạp {PROMO_PCT}% (1 lần/ngày):</b> <code>+{fmt_money(p15)}đ</code>')
    lines.append(f'{ce("➕")} <b>Thưởng thêm mỗi lệnh nạp {PROMO_ORDER_PCT}%:</b> <code>+{fmt_money(p3)}đ</code>')
    lines.append(f'{ce("💰")} <b>Tổng nhận:</b> <code>+{fmt_money(total)}đ</code>')
    if eligible15:
        lines.append(f'{ce("🎯")} <b>Cược {PROMO_PCT}%:</b> x{PROMO_WAGER_MULT} vòng (<code>{fmt_money(req_main)}đ</code>)')
    lines.append(f'{ce("🎯")} <b>Cược {PROMO_ORDER_PCT}%:</b> x{PROMO_ORDER_WAGER_MULT} vòng (<code>{fmt_money(req_order)}đ</code>)')
    lines.append(f'{ce("📊")} <b>Tổng yêu cầu cược:</b> <code>{fmt_money(required)}đ</code>')
    lines.append(f'{ce("⚠️")} <b>Lưu ý:</b> Cược đủ yêu cầu mới được rút. '
                 f'Nếu đang có vòng cược khuyến mãi khác, yêu cầu cược sẽ được cộng dồn.')
    if not eligible15:
        if promo_claimed_today(uid):
            lines.append(f'{ce("📌")} <i>Hôm nay bạn đã nhận khuyến mãi {PROMO_PCT}% rồi (mỗi ngày 1 lần).</i>')
        else:
            lines.append(f'{ce("📌")} <i>Khuyến mãi {PROMO_PCT}% mở trong giờ vàng {promo_windows_text()} mỗi ngày.</i>')
    lines.append('━━━━━━━━━━━━━━━━━━━━━\n\nVui lòng chọn bên dưới:')
    kb = InlineKeyboardMarkup([[
        btn("NHẬN KHUYẾN MÃI", "🎁", callback_data=f"accept_promo_{uid}_{amount}_{1 if eligible15 else 0}"),
        btn("TỪ CHỐI", "❌", callback_data=f"reject_bonus_{uid}")
    ]])
    return "\n".join(lines), kb

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

# ============================================================
# HÀM TẠO NỘI DUNG CHUYỂN KHOẢN NGẪU NHIÊN
# ============================================================
PREFIX_WORDS = [
    "anh yeu em", "em yeu anh", "an com chua", "lixi day ne", "chuc mung", "vui ve", "may man",
    "thanh cong", "phat tai", "loc phat", "tien vao nhu nuoc", "dau tu sinh loi", "choi game vui",
    "nap tien nhanh", "giao dich an toan", "ho tro 24/7", "khach hang vip", "thanh toan don hang",
    "mua sam online", "thanh toan hoa don", "chuyen tien mua hang", "nap the dien thoai",
    "mung sinh nhat", "qua tang", "loi chuc", "tinh cam", "gia dinh", "ban be", "dong nghiep",
    "doi tac", "khach hang", "nguoi dung", "thanh vien", "dang ky", "xac nhan", "hoan tien"
]

def generate_transfer_content(user_id):
    prefix = random.choice(PREFIX_WORDS)
    return f"{prefix} {user_id}".lower()

def get_deposit_info(user_id, amount=0):
    content = generate_transfer_content(user_id)
    qr_params = urlencode({"amount": int(amount), "addInfo": content, "accountName": ACCOUNT_NAME})
    qr_url = f"https://img.vietqr.io/image/{BANK_ID}-{ACCOUNT_NO}-compact2.png?{qr_params}"
    
    caption = (
        f'{ce("💳")} <b>THÔNG TIN NẠP TIỀN</b>\n\n'
        f'{ce("🏦")} Ngân hàng: <b>MBBANK</b>\n'
        f'{ce("👤")} CTK: <b>{ACCOUNT_NAME}</b>\n'
        f'{ce("💰")} STK: <code>{ACCOUNT_NO}</code>\n'
        f'{ce("✍️")} Nội dung: <code>{content}</code>\n'
        f'{ce("💰")} Số tiền: <code>{fmt_money(amount)}đ</code>\n\n'
        f'{ce("⚡")} <i>Lưu ý: Quét mã QR để tự điền số tiền và nội dung chuyển khoản. Chỉ cộng tiền tự động khi hệ thống xác nhận được giao dịch.</i>'
    )
    return qr_url, caption, content

async def fetch_qr_image(qr_url: str) -> BytesIO:
    """Tải QR VietQR về bộ nhớ; kiểm tra phản hồi để báo lỗi rõ ràng."""
    timeout = aiohttp.ClientTimeout(total=30)
    headers = {"User-Agent": "Mozilla/5.0 (compatible; TelegramBot/1.0)"}
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async with session.get(qr_url, allow_redirects=True) as response:
            content_type = response.headers.get("Content-Type", "")
            data = await response.read()
            if response.status != 200:
                detail = data[:250].decode("utf-8", errors="replace")
                raise RuntimeError(f"VietQR HTTP {response.status}; Content-Type={content_type}; body={detail}")
            # Một số CDN trả ảnh với Content-Type không chuẩn; chấp nhận các định dạng ảnh phổ biến.
            is_image = (
                "image/" in content_type.lower()
                or data.startswith(b"\x89PNG\r\n\x1a\n")
                or data.startswith(b"\xff\xd8\xff")
                or data.startswith((b"GIF87a", b"GIF89a", b"RIFF"))
            )
            if not data or not is_image:
                detail = data[:200].decode("utf-8", errors="replace")
                raise RuntimeError(f"VietQR không trả về ảnh; Content-Type={content_type}; body={detail}")
    photo = BytesIO(data)
    photo.name = "deposit_qr.png"
    photo.seek(0)
    return photo

# ---- Tạo QR VietQR ngay trên server (không phụ thuộc img.vietqr.io) ----
_BANK_BIN = {"MB": "970422", "MBBANK": "970422", "VCB": "970436", "TCB": "970407",
             "ACB": "970416", "BIDV": "970418", "CTG": "970415", "VPB": "970432",
             "TPB": "970423", "STB": "970403", "VIB": "970441", "OCB": "970448"}

def _crc16_ccitt(text: str) -> str:
    crc = 0xFFFF
    for b in text.encode("ascii"):
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return f"{crc:04X}"

def _tlv(tag: str, value: str) -> str:
    return f"{tag}{len(value):02d}{value}"

def build_vietqr_payload(amount: int, content: str) -> str:
    bin_ = _BANK_BIN.get(str(BANK_ID).upper(), "970422")
    acc = _tlv("00", bin_) + _tlv("01", str(ACCOUNT_NO))
    merchant = _tlv("00", "A000000727") + _tlv("01", acc) + _tlv("02", "QRIBFTTA")
    info = _tlv("08", content)
    body = (
        _tlv("00", "01") + _tlv("01", "12") + _tlv("38", merchant) +
        _tlv("53", "704") + _tlv("54", str(int(amount))) + _tlv("58", "VN") +
        _tlv("62", info) + "6304"
    )
    return body + _crc16_ccitt(body)

def make_local_qr(amount: int, content: str) -> BytesIO:
    import qrcode
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(build_vietqr_payload(amount, content))
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").get_image().convert("RGB")
    img = img.resize((600, 600))
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.name = "deposit_qr.png"
    buf.seek(0)
    return buf

def _reencode_image(raw: bytes) -> BytesIO:
    """Mở ảnh bằng Pillow rồi lưu lại thành PNG RGB chuẩn để Telegram xử lý được."""
    from PIL import Image
    img = Image.open(BytesIO(raw)).convert("RGB")
    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.name = "deposit_qr.png"
    buf.seek(0)
    return buf

async def send_deposit_qr(bot, chat_id, qr_url, caption, kb, amount=0, content=""):
    """Gửi QR theo nhiều bước dự phòng; bước nào lỗi thì in log rồi thử bước kế tiếp."""
    kw = dict(chat_id=chat_id, caption=caption, reply_markup=kb, parse_mode=ParseMode.HTML)
    raw = None
    # 1) Ảnh gốc từ VietQR
    try:
        raw = (await fetch_qr_image(qr_url)).getvalue()
        bio = BytesIO(raw); bio.name = "deposit_qr.png"
        return await bot.send_photo(photo=bio, **kw)
    except Exception as e:
        print(f"[QR bước 1 - ảnh VietQR] {type(e).__name__}: {e}")
    # 2) Chuẩn hoá lại ảnh VietQR bằng Pillow
    if raw:
        try:
            return await bot.send_photo(photo=_reencode_image(raw), **kw)
        except Exception as e:
            print(f"[QR bước 2 - chuẩn hoá ảnh] {type(e).__name__}: {e}")
    # 3) Tự vẽ QR VietQR trên server
    try:
        return await bot.send_photo(photo=make_local_qr(amount, content), **kw)
    except Exception as e:
        print(f"[QR bước 3 - QR tự vẽ] {type(e).__name__}: {e}")
    # 4) Gửi dạng file ảnh (document)
    if raw:
        try:
            bio = BytesIO(raw); bio.name = "deposit_qr.png"
            return await bot.send_document(document=bio, **kw)
        except Exception as e:
            print(f"[QR bước 4 - document] {type(e).__name__}: {e}")
    # 5) Cuối cùng: gửi thông tin chuyển khoản dạng chữ để khách vẫn nạp được
    return await bot.send_message(chat_id=chat_id, text=caption, reply_markup=kb,
                                  parse_mode=ParseMode.HTML)

def deposit_menu_content(uid):
    """Menu chọn mệnh giá nạp (dùng cho nút NẠP TIỀN và nút đổi mệnh giá)."""
    kb = InlineKeyboardMarkup([
        [btn("10.000đ", "💵", "dep_10000"), btn("20.000đ", "💵", "dep_20000"), btn("50.000đ", "💵", "dep_50000")],
        [btn("100.000đ", "💵", "dep_100000"), btn("200.000đ", "💵", "dep_200000"), btn("500.000đ", "💵", "dep_500000")],
        [btn("1.000.000đ", "💰", "dep_1000000"), btn("2.000.000đ", "💰", "dep_2000000"), btn("5.000.000đ", "💰", "dep_5000000")],
        [btn("10.000.000đ", "💎", "dep_10000000"), btn("20.000.000đ", "💎", "dep_20000000"), btn("50.000.000đ", "💎", "dep_50000000")],
        [btn("Hỗ Trợ", "🔔", "dep_support")]
    ])
    
    caption = (
        f'{ce("💵")} <b>CHỌN MỆNH GIÁ NẠP TIỀN</b>\n\n'
        f'{ce("💎")} Nạp tối thiểu: <b>10.000 đ</b>\n'
        f'{ce("💎")} Nạp tối đa: <b>100.000.000 đ</b>\n\n'
        f'Bấm vào mệnh giá bên dưới để nạp tiền qua <b>Chuyển khoản Ngân hàng</b>.\n\n'
        f'{ce("📌")} <b>CÁCH LẤY THÔNG TIN NẠP:</b>\n\n'
        f'{ce("✍️")} Gõ lệnh: <code>/nap số_tiền</code>\n'
        f'Ví dụ: <code>/nap 100000</code> hoặc <code>/nap 100k</code>\n\n'
        f'{ce("➡️")} Hoặc bấm nút số tiền bên dưới để lấy nhanh.\n\n'
        f'{ce("⚠️")} <b>LƯU Ý:</b>\n\n'
        f'{ce("✔️")} Chuyển đúng <b>SỐ TIỀN</b> và <b>NỘI DUNG</b> được cung cấp.\n'
        f'{ce("✔️")} Mỗi lần nạp cần lấy thông tin <b>MỚI</b>.\n'
        f'{ce("❌")} Không dùng thông tin cũ cho giao dịch sau.\n'
        f'{ce("💰")} Nạp tối thiểu: <b>10.000 đ</b>'
    )
    qr_url, _, _ = get_deposit_info(uid, 0)
    return qr_url, caption, kb

def format_money(amount):
    return f"{amount:,}".replace(",", ".")

# ============================================================
# ===== TIỆN ÍCH CÀI ĐẶT / THỐNG KÊ CƯỢC THEO NGÀY ======
# ============================================================
def get_setting(key, default=None):
    res = query("SELECT value FROM settings WHERE key=%s", (key,))
    return res[0][0] if res else default

def set_setting(key, value):
    query("INSERT INTO settings(key, value) VALUES(%s, %s) "
          "ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value", (key, str(value)))

WIN_NOTE_PREFIXES = ("Thắng", "Nổ hũ", "Hoàn tiền Long Hổ", "Hoàn tiền Baccarat")

def record_daily(uid, bet=0, win=0):
    day = get_vietnam_time().date()
    query(
        "INSERT INTO bet_daily(user_id, day, bet, win) VALUES(%s,%s,%s,%s) "
        "ON CONFLICT (user_id, day) DO UPDATE SET "
        "bet=bet_daily.bet+EXCLUDED.bet, win=bet_daily.win+EXCLUDED.win",
        (uid, day, bet, win))

def backfill_bet_daily():
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
# ===== TÍCH LŨY NẠP ============================
# ============================================================
MILESTONES = [
    {"moc": 1, "nap": 50_000, "cuoc": 1_000_000, "gift": 20_000},
    {"moc": 2, "nap": 1_000_000, "cuoc": 15_000_000, "gift": 60_000},
    {"moc": 3, "nap": 5_000_000, "cuoc": 50_000_000, "gift": 170_000},
    {"moc": 4, "nap": 10_000_000, "cuoc": 120_000_000, "gift": 300_000},
    {"moc": 5, "nap": 20_000_000, "cuoc": 200_000_000, "gift": 600_000},
    {"moc": 6, "nap": 50_000_000, "cuoc": 500_000_000, "gift": 1_000_000},
    {"moc": 7, "nap": 1_000_000_000, "cuoc": 10_000_000_000, "gift": 4_000_000},
    {"moc": 8, "nap": 2_000_000_000, "cuoc": 20_000_000_000, "gift": 7_000_000},
    {"moc": 9, "nap": 5_000_000_000, "cuoc": 50_000_000_000, "gift": 10_000_000},
]

def get_tich_luy_text(uid):
    today_str = get_vietnam_time().strftime("%Y-%m-%d")
    
    dep_today = deposited_today(uid)
    bet_today, _ = get_bet_stats(uid)
    
    reached_mocs = []
    next_moc = None
    for m in MILESTONES:
        if dep_today >= m["nap"] and bet_today >= m["cuoc"]:
            reached_mocs.append(m)
        elif not next_moc:
            next_moc = m

    if not next_moc and reached_mocs:
        current_moc_text = f"Mốc {reached_mocs[-1]['moc']} (Tối đa)"
        thieu_nap = 0
        thieu_cuoc = 0
    elif next_moc:
        current_moc_text = f"Chưa đạt" if not reached_mocs else f"Đã đạt mốc {reached_mocs[-1]['moc']}"
        thieu_nap = max(0, next_moc["nap"] - dep_today)
        thieu_cuoc = max(0, next_moc["cuoc"] - bet_today)
    else:
        current_moc_text = "Chưa đạt"
        thieu_nap = MILESTONES[0]["nap"] - dep_today
        thieu_cuoc = MILESTONES[0]["cuoc"] - bet_today

    codes_today = query("SELECT code, used FROM giftcodes WHERE bound_user=%s AND ctype='TICHLUY' AND claim_date=%s ORDER BY milestone", (uid, get_vietnam_time().date())) or []
    da_dung = [c[0] for c in codes_today if c[1] == 1]
    chua_dung = [c[0] for c in codes_today if c[1] == 0]

    msg = (
        f'{ce("🎯")} <b>TÍCH LŨY NẠP, SĂN GIFTCODE</b>\n\n'
        f'<blockquote>'
        f'Mốc | Nạp | Cược | Giftcode\n'
    )
    for m in MILESTONES:
        nap_str = fmt_money(m['nap']).replace('.000', 'K') if m['nap'] < 1_000_000 else (f"{m['nap']//1_000_000}M" if m['nap'] < 1_000_000_000 else f"{m['nap']//1_000_000_000}B")
        cuoc_str = fmt_money(m['cuoc']).replace('.000', 'K') if m['cuoc'] < 1_000_000 else (f"{m['cuoc']//1_000_000}M" if m['cuoc'] < 1_000_000_000 else f"{m['cuoc']//1_000_000_000}B")
        gift_str = fmt_money(m['gift']).replace('.000', 'K') if m['gift'] < 1_000_000 else (f"{m['gift']//1_000_000}M")
        msg += f"{m['moc']} | {nap_str} | {cuoc_str} | {gift_str}\n"
    msg += f'</blockquote>\n'

    msg += (
        f'<blockquote>'
        f'⚡ Cơ chế: tính nạp/cược dồn trong ngày.\n'
        f'Mỗi mốc đạt được sẽ nhận 1 code riêng biệt tương ứng.\n'
        f'⏰ Code chỉ có hạn sử dụng trong ngày, sang 00:00 sẽ tự động reset và hủy code chưa dùng.\n'
        f'📜 Mỗi mốc chỉ nhận 1 lần/ngày.\n'
        f'</blockquote>\n'

        f'📌 Ngày tính: {today_str}\n'
        f'- Nạp hôm nay: {fmt_money(dep_today)}\n'
        f'- Cược hôm nay: {fmt_money(bet_today)}\n\n'

        f'🏁 Mốc hiện tại đạt: <b>{current_moc_text}</b>\n'
    )
    
    if next_moc:
        msg += (
            f'📈 Tiến độ mốc {next_moc["moc"]}:\n'
            f'• Thiếu nạp: {fmt_money(thieu_nap)}\n'
            f'• Thiếu cược: {fmt_money(thieu_cuoc)}\n\n'
        )

    msg += (
        f'🏷 Trạng thái giftcode mốc hôm nay:\n'
        f'• Đã sử dụng: {", ".join(da_dung) if da_dung else "Chưa có"}\n'
        f'• Chưa sử dụng: {", ".join(chua_dung) if chua_dung else "Chưa có"}\n\n'
        f'🎁 <b>Code chưa sử dụng:</b>\n'
        f'• {chr(10).join(chua_dung) if chua_dung else "Chưa có code khả dụng."}\n\n'
        f'💡 Khi đạt mốc mới, bot sẽ tự động gửi code. Bấm 🔄 Làm mới để cập nhật giao diện.'
    )
    
    kb = InlineKeyboardMarkup([[btn("Làm mới", "🔄", callback_data=f"acc_tich_luy_refresh_{uid}")]])
    return msg, kb

async def auto_gen_tich_luy_codes():
    """Tạo tối đa một code cho mỗi user/mốc/ngày; không được gọi từ nút làm mới."""
    today = get_vietnam_time().date()
    today_str = today.strftime("%Y-%m-%d")

    # Code tích lũy chưa dùng sẽ hết hạn và bị dọn sau 00:00 giờ Việt Nam.
    query("DELETE FROM giftcodes WHERE ctype='TICHLUY' AND used=0 AND expiry IS NOT NULL AND expiry <= %s",
          (get_vietnam_time(),))

    users = query(
        'SELECT DISTINCT user_id FROM deposit_history '
        "WHERE status='success' AND right(\"time\",10)=%s",
        (get_vietnam_date(),)
    ) or []

    for (uid,) in users:
        dep_today = deposited_today(uid)
        bet_today, _ = get_bet_stats(uid)
        for m in MILESTONES:
            if dep_today < m["nap"] or bet_today < m["cuoc"]:
                continue

            # Chống race condition: unique index + ON CONFLICT đảm bảo mỗi mốc chỉ tạo 1 code/ngày.
            code = gen_gift_code("TICHLUY")
            expiry = (get_vietnam_time() + timedelta(days=1)).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            inserted = query(
                "INSERT INTO giftcodes "
                "(code, ctype, reward, wager, expiry, bound_user, used, created_by, created_at, milestone, claim_date) "
                "VALUES (%s,'TICHLUY',%s,3,%s,%s,0,0,%s,%s,%s) "
                "ON CONFLICT DO NOTHING RETURNING code",
                (code, m["gift"], expiry, uid, get_vietnam_datetime_db(), m["moc"], today)
            )
            if not inserted:
                continue
            try:
                if _bot_instance:
                    await _bot_instance.send_message(
                        uid,
                        f'{ce("🎁")} <b>CHÚC MỪNG BẠN ĐẠT MỐC {m["moc"]} TÍCH LŨY NẠP!</b>\n'
                        f'Mã code của bạn: <code>{code}</code>\n'
                        f'Giá trị: <b>{fmt_money(m["gift"])}đ</b> (Yêu cầu x3 vòng cược)\n'
                        f'Code hết hạn lúc 00:00 ngày mai theo giờ Việt Nam.',
                        parse_mode=ParseMode.HTML
                    )
            except Exception as e:
                print(f"Không gửi được code tích lũy cho {uid}: {e}")

# ============================================================
# ===== VIP ============================================
# ============================================================
VIP_POINT_BET = 300000
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
    ok, text = vip_exchange(uid, info["redeemable"])
    await safe_answer(q)
    try:
        await q.message.edit_text(text, parse_mode=ParseMode.HTML)
    except Exception:
        await q.message.reply_text(text, parse_mode=ParseMode.HTML)

# ============================================================
# ===== TRUNG TÂM NHẬN THƯỞNG ==========================
# ============================================================
MIN_REWARD_BASE = 100000
LOSS_TIERS_DAY = [(1_000_000_000, 12), (100_000_000, 8), (10_000_000, 6), (1_000_000, 4), (100_000, 2)]
LOSS_TIERS_WEEK = [(1_000_000_000, 5), (100_000_000, 3), (10_000_000, 2.5), (1_000_000, 2), (100_000, 1)]

RTYPE_LABEL = {
    "cuoc_ngay": ("HOÀN CƯỢC NGÀY", "🔥"),
    "cuoc_tuan": ("HOÀN CƯỢC TUẦN", "🚀"),
    "thua_ngay": ("HOÀN THUA NGÀY", "📉"),
    "thua_tuan": ("HOÀN THUA TUẦN", "🗓"),
}

def get_rebate_pct(kind):
    try:
        return float(get_setting(f"rebate_{kind}_pct", "2"))
    except (TypeError, ValueError):
        return 2.0

def fmt_pct(p):
    return f"{p:g}"

def reward_calc(rtype, bet, win):
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

def _insert_reward(uid, rtype, period, base, amount):
    if amount <= 0:
        return False
    r = query(
        "INSERT INTO rewards(user_id, rtype, period, base, amount, claimed, created_at) "
        "VALUES(%s,%s,%s,%s,%s,0,%s) ON CONFLICT (user_id, rtype, period) DO NOTHING RETURNING id",
        (uid, rtype, period, base, amount, get_vietnam_datetime_db()))
    return bool(r)

def settle_day_sync(day):
    created = {}

    def _add(uid_, rtype, period, base, amount):
        if _insert_reward(uid_, rtype, period, base, amount):
            created.setdefault(uid_, []).append((rtype, period, amount))

    rows = query("SELECT user_id, bet, win FROM bet_daily WHERE day=%s", (day,)) or []
    for uid_, bet, win in rows:
        for rtype in ("cuoc_ngay", "thua_ngay"):
            base, amount = reward_calc(rtype, int(bet or 0), int(win or 0))
            _add(uid_, rtype, day.isoformat(), base, amount)

    if day.weekday() == 6:
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
# ===== GIFTCODE 5 LOẠI ================================
# ============================================================
GIFT_TYPES = {
    "TANTHU":  {"name": "Code Tân Thủ",  "icon": "🎁", "fmt": "JAV88-TANTHU-xxxxxxx"},
    "CODEMUA": {"name": "Code Mua",      "icon": "🛒", "fmt": "JAV88-CODEMUA-xxxxxxx"},
    "GIOVANG": {"name": "Code Giờ Vàng", "icon": "⏰", "fmt": "JAV88-GIOVANG-xxxxxxx"},
    "NAP":     {"name": "Code Nạp",      "icon": "💳", "fmt": "JAV88-1234567-ABCDEFG"},
    "TRIAN":   {"name": "Code Tri Ân",   "icon": "🎉", "fmt": "JAV88-TRIAN-xxxxxxx"},
    "TICHLUY": {"name": "Code Tích Lũy", "icon": "🏆", "fmt": "JAV88-TICHLUY-xxxxxxx"},
    "INTERACT": {"name": "Code Tương Tác", "icon": "💬", "fmt": "JAV88-INTERACT-xxxxxxx"},
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
    ex = query("SELECT required_bet FROM user_bonus WHERE user_id=%s", (uid,))
    if ex and (ex[0][0] or 0) > 0:
        query("UPDATE user_bonus SET bonus_amount=bonus_amount+%s, required_bet=required_bet+%s WHERE user_id=%s",
              (bonus_amount, required_bet, uid))
    else:
        query("DELETE FROM user_bonus WHERE user_id=%s", (uid,))
        query("INSERT INTO user_bonus (user_id, bonus_amount, required_bet, current_bet, created_at) VALUES (%s,%s,%s,0,%s)",
              (uid, bonus_amount, required_bet, get_vietnam_datetime_db()))

async def redeem_giftcode(update: Update, uid: int, code_str: str) -> bool:
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
    success_text = (
        f'{ce("🎉")} <b>NHẬN CODE THÀNH CÔNG!</b> {ce("🎉")}\n'
        f'┏━━━━━━━━━━━━━━━━━━━━━━━━━\n'
        f'┃ {ce("🔑")} <b>Loại:</b> {gname}\n'
        f'┃ {ce("🔑")} <b>Mã code:</b> <code>{code_str}</code>\n'
        f'┃ {ce("💰")} <b>Đã nhận:</b> <code>+{fmt_money(reward)}đ</code>\n'
        f'┃ {ce("🎯")} <b>Vòng cược yêu cầu:</b> <code>x{wager}</code>\n'
        f'┃ {ce("📊")} <b>Tổng cược cần:</b> <code>{fmt_money(required_bet)}đ</code>\n'
        f'┗━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'
        f'{ce("💰")} Số dư hiện tại: <code>{fmt_money(get_balance(uid))}đ</code>'
    )
    chat = update.effective_chat
    user = update.effective_user
    if chat and chat.type != "private":
        await msg.reply_text(
            f"✅ Nhập giftcode thành công! ID: <code>{mask_user_id(uid)}</code> · "
            f"Người dùng: {html.escape('@' + user.username if user and user.username else (user.full_name if user else 'Thành viên'))}. "
            f"Chi tiết được gửi riêng qua bot.",
            parse_mode=ParseMode.HTML
        )
        try:
            await update.get_bot().send_message(uid, success_text, parse_mode=ParseMode.HTML)
        except Exception:
            pass
    else:
        await msg.reply_text(success_text, parse_mode=ParseMode.HTML)
    try:
        public_name = ("@" + user.username) if user and user.username else (user.full_name if user else "Thành viên")
        if not chat or chat.id != LOG_GROUP_ID:
            await update.get_bot().send_message(
                LOG_GROUP_ID,
                f"🎟 <b>NHẬP GIFTCODE THÀNH CÔNG</b>\n"
                f"👤 Người dùng: {html.escape(public_name)}\n"
                f"🆔 ID: <code>{mask_user_id(uid)}</code>\n"
                f"💰 Giá trị: <b>{fmt_money(reward)}đ</b> · Vòng cược x{wager}\n"
                f"⏰ Thời gian: <code>{get_vietnam_datetime_db()}</code>",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        print(f"Không gửi được thông báo nhập code: {e}")
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
    if len(codes) < qty:
        miss = qty - len(codes)
        refund = miss * value + int(miss * value * 0.05)
        add_money(uid, refund, "Hoàn tiền mua giftcode lỗi")
    if not codes:
        return await msg_obj.reply_text(f'{ce("❌")} Lỗi hệ thống, đã hoàn tiền. Vui lòng thử lại!', parse_mode=ParseMode.HTML)

    code_lines = "\n".join(f'{i}. <code>{c}</code>' for i, c in enumerate(codes, 1))
    try:
        buyer = update.effective_user
        public_name = ("@" + buyer.username) if buyer and buyer.username else (buyer.full_name if buyer else "Thành viên")
        await ctx.bot.send_message(
            LOG_GROUP_ID,
            f"🛒 <b>CÓ NGƯỜI MUA GIFTCODE</b>\n"
            f"👤 Người mua: {html.escape(public_name)}\n"
            f"🆔 ID: <code>{mask_user_id(uid)}</code>\n"
            f"🎟 Số lượng: <b>{len(codes)}</b> · Giá trị mỗi code: <b>{fmt_money(value)}đ</b>\n"
            f"💰 Tổng thanh toán: <b>{fmt_money(len(codes)*value + int(len(codes)*value*0.05))}đ</b>\n"
            f"⏰ Thời gian: <code>{get_vietnam_datetime_db()}</code>\n"
            f"🔒 Mã code không được công khai.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print(f"Không gửi được thông báo mua giftcode: {e}")

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

INTERACTION_MILESTONES = [
    (50, 5111),
    (100, 12222),
    (200, 22555),
    (500, 44777),
    (1000, 76111),
    (2000, 88222),
    (3000, 89333),
    (4000, 90444),
    (5000, 92555),
    (6000, 155666),
]
TOP_INTERACTION_PRIZES = {1: 18888, 2: 13333, 3: 10000, 4: 9999,
                          5: 7777, 6: 7777, 7: 7777, 8: 7777, 9: 7777, 10: 7777}
_interaction_seen = {}

def mask_user_id(user_id):
    """Ẩn 5 chữ số đầu khi đưa ID lên nhóm công khai."""
    raw = str(user_id or "")
    return "*****" + raw[5:] if len(raw) > 5 else "*****"

def _parse_db_date(value):
    if not value:
        return None
    if hasattr(value, "date") and not isinstance(value, str):
        try:
            return value.date()
        except Exception:
            pass
    value = str(value).strip()
    for fmt in ("%H:%M - %d/%m/%Y", "%d/%m/%Y", "%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(value, fmt).date()
        except (ValueError, TypeError):
            continue
    # Hỗ trợ timestamp ISO có microsecond hoặc múi giờ, ví dụ 2026-10-29T11:59:00+07:00.
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except (ValueError, TypeError):
        pass
    match = re.search(r"(\d{2}/\d{2}/\d{4})", value)
    if match:
        try:
            return datetime.strptime(match.group(1), "%d/%m/%Y").date()
        except ValueError:
            pass
    return None

async def _send_interaction_code(bot, uid, group_id, milestone, reward, date_text):
    # Mỗi người/mốc/ngày chỉ được phát một code; code ràng buộc với user và cược x7.
    code = gen_gift_code("TT")
    expiry = get_vietnam_time() + timedelta(hours=24)
    inserted = query(
        "INSERT INTO giftcodes (code, ctype, reward, wager, expiry, require_deposit, required_amount, "
        "bound_user, used, created_by, created_at) "
        "VALUES (%s,'INTERACT',%s,7,%s,0,0,%s,0,0,%s) ON CONFLICT DO NOTHING RETURNING code",
        (code, reward, expiry, uid, get_vietnam_datetime_db())
    )
    if not inserted:
        return
    claim = query(
        "INSERT INTO interaction_reward_claims (user_id,group_id,date,milestone,code,reward_amount,created_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING milestone",
        (uid, group_id, date_text, milestone, code, reward, get_vietnam_datetime_db())
    )
    if not claim:
        query("DELETE FROM giftcodes WHERE code=%s AND used=0", (code,))
        return
    try:
        await bot.send_message(
            uid,
            f"🎁 <b>QUÀ TƯƠNG TÁC NHÓM</b>\n"
            f"Bạn đã đạt mốc <b>{milestone:,}</b> tin nhắn hợp lệ.\n"
            f"Mã giftcode: <code>{code}</code>\n"
            f"Giá trị: <b>{fmt_money(reward)}đ</b> · Vòng cược: <b>x7</b>\n"
            f"Hạn dùng: 24 giờ kể từ lúc phát. Dùng <code>/code {code}</code> để nhận.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        # Không đăng code công khai; thông báo mở bot để nhận riêng.
        try:
            await bot.send_message(
                group_id,
                f"🎁 Thành viên ID {mask_user_id(uid)} đã đạt mốc tương tác {milestone:,} tin. "
                f"Hãy mở bot riêng và nhắn /start để nhận giftcode (code không đăng trong nhóm)."
            )
        except Exception:
            pass
        print(f"Không gửi được giftcode tương tác cho {uid}: {e}")

async def track_interaction(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not msg or not user or not chat or chat.type == "private" or user.is_bot:
        return
    if GROUP_IDS and chat.id not in GROUP_IDS:
        return
    # Chỉ đếm tin nhắn văn bản tự nhiên; bỏ command, media-only, nội dung quá ngắn.
    text_value = (msg.text or msg.caption or "").strip()
    if not text_value or text_value.startswith("/") or len(text_value) < 2:
        return
    normalized = re.sub(r"\s+", " ", text_value).casefold()
    now = get_vietnam_time()
    key = (user.id, chat.id)
    previous = _interaction_seen.get(key)
    if previous:
        prev_text, prev_at = previous
        # Bỏ tin lặp trong 60 giây và flood nhanh dưới 2 giây.
        if normalized == prev_text and (now - prev_at).total_seconds() < 60:
            return
        if (now - prev_at).total_seconds() < 2:
            return
    _interaction_seen[key] = (normalized, now)
    # Giới hạn cache trong bộ nhớ.
    if len(_interaction_seen) > 10000:
        for old_key in list(_interaction_seen)[:2000]:
            _interaction_seen.pop(old_key, None)

    uid, gid = user.id, chat.id
    today = get_vietnam_date()
    now_str = get_vietnam_datetime_db()
    query("""
        INSERT INTO group_interactions (user_id, group_id, interaction_count, last_interaction)
        VALUES (%s, %s, 1, %s)
        ON CONFLICT (user_id, group_id) DO UPDATE SET
            interaction_count = GREATEST(group_interactions.interaction_count,0) + 1,
            last_interaction = EXCLUDED.last_interaction
    """, (uid, gid, now_str))
    query("""
        INSERT INTO daily_top_interactions (user_id, group_id, interaction_count, date)
        VALUES (%s, %s, 1, %s)
        ON CONFLICT (user_id, group_id, date) DO UPDATE SET
            interaction_count = daily_top_interactions.interaction_count + 1
    """, (uid, gid, today))
    total = query(
        "SELECT interaction_count FROM daily_top_interactions WHERE user_id=%s AND group_id=%s AND date=%s",
        (uid, gid, today)
    )
    count = int(total[0][0] or 0) if total else 0
    for milestone, reward in INTERACTION_MILESTONES:
        if count < milestone:
            continue
        already = query(
            "SELECT 1 FROM interaction_reward_claims WHERE user_id=%s AND group_id=%s AND date=%s AND milestone=%s",
            (uid, gid, today, milestone)
        )
        if not already:
            await _send_interaction_code(ctx.bot, uid, gid, milestone, reward, today)


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
                    new_stats_msg = await bot.send_message(chat_id, stats_text, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([
                        [btn('NẠP TIỀN TẠI ĐÂY', '💰', url=f'https://t.me/{BOT_USERNAME}?start=nap')],
                        [btn('BOT CHƠI GAME', '🎮', url='https://t.me/Jav88gamebot')]
                    ]))
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
                jackpot_contribution = int(total_lose * 0.03)
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
    if check_mt('mt_taixiu_room') and user_id not in ADMIN_IDS:
        return False, f'{ce("⚙️")} Game Tài Xỉu Room đang bảo trì!'
    if is_game_banned(user_id, 1):
        return False, f'{ce("🚫")} Bạn đã bị cấm chơi trò chơi này!'
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
    if check_mt('mt_taixiu_room') and user_id not in ADMIN_IDS:
        return False, f'{ce("⚙️")} Game Tài Xỉu Room đang bảo trì!'
    if is_game_banned(user_id, 1):
        return False, f'{ce("🚫")} Bạn đã bị cấm chơi trò chơi này!'
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
    # Báo riêng về bot để người chơi nhận xác nhận kể cả khi nhóm bị trôi tin.
    if success:
        try:
            await ctx.bot.send_message(chat_id=user_id, text=message, parse_mode=ParseMode.HTML)
        except Exception as e:
            print(f"Không gửi được xác nhận cược riêng uid={user_id}: {e}")

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
    icons = ["🎃", "🦀", "🦐", "🐟", "🐓", "🦌"]
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

# ================= CÁC HÀM DÙNG CHO NÚT TÀI KHOẢN =================
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
    # Menu chính chỉ hiển thị trong chat riêng; /start ở nhóm được bỏ qua.
    chat = update.effective_chat
    if not chat or chat.type != "private":
        return
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
    # Deep link từ nút NẠP TIỀN TẠI ĐÂY: mở thẳng menu nạp tiền.
    if ctx.args and ctx.args[0].lower() == "nap":
        if is_feature_banned(uid, 'nap') and uid not in ADMIN_IDS:
            return await update.effective_message.reply_text(
                f'{ce("🚫")} Tính năng NẠP TIỀN đã bị khóa!',
                parse_mode=ParseMode.HTML
            )
        if check_mt('mt_nap') and uid not in ADMIN_IDS:
            return await update.effective_message.reply_text(
                f'{ce("⚙️")} Nạp Tiền đang bảo trì!',
                parse_mode=ParseMode.HTML
            )
        try:
            _, caption, kb = deposit_menu_content(uid)
            return await update.effective_message.reply_text(
                caption, reply_markup=kb, parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Lỗi mở menu nạp từ deep link: {e}")
            return await update.effective_message.reply_text(
                'Không thể hiển thị menu nạp tiền lúc này. Vui lòng thử lại sau.'
            )
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
        [kbtn("NẠP TIỀN", "💵"), kbtn("RÚT TIỀN", "💸")],
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
    # Điều kiện chống rút của tài khoản chưa nạp: cần ít nhất một lần nạp thành công từ 50.000đ.
    dep_ok = query(
        "SELECT 1 FROM deposit_history WHERE user_id=%s AND amount >= 50000 "
        "AND LOWER(COALESCE(status,'')) IN ('success','successful','completed','approved','done') LIMIT 1",
        (uid,)
    )
    if not dep_ok and uid not in ADMIN_IDS:
        return await msg_obj.reply_text(
            f'{ce("🔐")} <b>CHƯA ĐỦ ĐIỀU KIỆN RÚT TIỀN</b>\n\n'
            f'{ce("💳")} Tài khoản cần có ít nhất <b>1 lần nạp thành công từ 50.000đ</b> trở lên mới được rút.\n'
            f'{ce("🎁")} Vui lòng nạp tiền và chờ hệ thống xác nhận thành công.',
            parse_mode=ParseMode.HTML)
    res = query("SELECT bank, stk, name, balance FROM users WHERE user_id=%s", (uid,))
    if not res or not res[0][0] or not res[0][1]:
        return await msg_obj.reply_text(
            f'{ce("❌")} Bạn chưa liên kết tài khoản ngân hàng.\n'
            f'Hãy dùng lệnh: <code>/lienket [Ngân_hàng] [STK] [Tên]</code>\n\n'
            f'{ce("📌")} <b>MIN RÚT:</b> <code>50,000đ</code>',
            parse_mode=ParseMode.HTML)
    u = res[0]
    if not args:
        remaining = get_remaining_bet_required(uid)
        req_cuoc_text = ""
        if remaining > 0:
            req_cuoc_text = (
                f'{ce("⚠️")} Cần cược thêm <b>{fmt_money(remaining)}đ</b> nữa để được rút.\n\n'
            )
            
        text = (
            f'{ce("🧾")} <b>THÔNG TIN RÚT TIỀN</b>\n\n'
            f'STK đã cài đặt của bạn:\n'
            f'<code>{html.escape(str(u[1]))} - {html.escape(str(u[0]))} - {html.escape(str(u[2]))}</code>\n\n'
            f'Để đổi STK vui lòng liên hệ Admin.\n\n'
            f'{ce("🎰")} <b>Rút tiền về tài khoản trên:</b>\n'
            f'• /rut [số tiền] - VD: /rut 50000\n'
            f'• /rut all - Rút tối đa phần khả dụng (đã trừ phí 0%)\n\n'
            f'{ce("📝")} <b>Điều kiện rút tiền:</b>\n'
            f'• Cược đủ Room TX: {fmt_money(u[3])}\n'
            f'• Hiện đã cược: {fmt_money(get_balance(uid) * 0)}\n\n'
            f'<blockquote>{req_cuoc_text}'
            f'{ce("⚠️")} Phí rút 0%. Rút tối thiểu theo cài đặt bot (thường 50k).</blockquote>'
        )
        return await msg_obj.reply_text(text, parse_mode=ParseMode.HTML)
    
    arg = args[0].lower()
    if arg in ["all", "max"]:
        amount = get_balance(uid)
    else:
        try:
            amount = int(arg)
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
            f'{ce("💰")} Bạn đang có tiền khuyến mãi chưa cược đủ vòng cược yêu cầu.\n'
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
            # Chỉ hiện hướng dẫn và các nút mệnh giá; không tạo QR số tiền 0.
            _, caption, kb = deposit_menu_content(uid)
            return await msg_obj.reply_text(
                caption,
                reply_markup=kb,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"nap menu lỗi: {e}")
            return await msg_obj.reply_text(
                f'{ce("❌")} Không thể hiển thị menu nạp tiền lúc này. Vui lòng thử lại sau.',
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
        if amount > 100000000:
            return await msg_obj.reply_text(f'{ce("❌")} Số tiền nạp tối đa là 100.000.000đ!', parse_mode=ParseMode.HTML)

        qr_url, caption, content = get_deposit_info(uid, amount)
        kb = InlineKeyboardMarkup([
            [btn("Hỗ Trợ", "🔔", callback_data="dep_support")]
        ])
        await send_deposit_qr(ctx.bot, msg_obj.chat_id, qr_url, caption, kb, amount, content)
    except ValueError:
        await msg_obj.reply_text(f'{ce("❌")} Số tiền không hợp lệ! VD: <code>/nap 50000</code>', parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"Tạo QR nạp tiền thất bại uid={uid}: {type(e).__name__}: {e}"); traceback.print_exc()
        await msg_obj.reply_text(
            f'{ce("❌")} Không tải được mã QR lúc này. Vui lòng thử lại sau hoặc liên hệ hỗ trợ.',
            parse_mode=ParseMode.HTML
        )

async def _reply_code_success_safely(update, ctx, uid, code_str, reward, wager, code_type, success_text):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    public_name = ("@" + user.username) if user and user.username else (user.full_name if user else "Thành viên")
    if chat and chat.type != "private":
        await msg.reply_text(
            f"✅ Nhập code thành công!\n"
            f"👤 {html.escape(public_name)} · ID <code>{mask_user_id(uid)}</code>\n"
            f"💰 Giá trị: <b>{fmt_money(int(reward))}đ</b>. Chi tiết đã gửi riêng qua bot.",
            parse_mode=ParseMode.HTML
        )
        try:
            await ctx.bot.send_message(uid, success_text, parse_mode=ParseMode.HTML)
        except Exception:
            pass
    else:
        await msg.reply_text(success_text, parse_mode=ParseMode.HTML)
    try:
        if not chat or chat.id != LOG_GROUP_ID:
            await ctx.bot.send_message(
                LOG_GROUP_ID,
                f"🎟 <b>NHẬP CODE THÀNH CÔNG</b>\n"
                f"👤 Người dùng: {html.escape(public_name)}\n"
                f"🆔 ID: <code>{mask_user_id(uid)}</code>\n"
                f"🏷 Loại: {html.escape(code_type)} · Giá trị: <b>{fmt_money(int(reward))}đ</b>\n"
                f"🎯 Vòng cược: x{int(wager or 0)}\n"
                f"⏰ <code>{get_vietnam_datetime_db()}</code>",
                parse_mode=ParseMode.HTML
            )
    except Exception as e:
        print(f"Không gửi được thông báo nhập code: {e}")

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

        success_text = (
            f'{ce("🎉")} <b>NHẬN CODE NẠP THÀNH CÔNG!</b> {ce("🎉")}\n'
            f'┏━━━━━━━━━━━━━━━━━━━━━━━━━\n'
            f'┃ {ce("🔑")} <b>Mã code:</b> <code>{code_str}</code>\n'
            f'┃ {ce("💰")} <b>Đã nhận:</b> <code>+{fmt_money(reward)}đ</code>\n'
            f'┃ {ce("🎯")} <b>Vòng cược yêu cầu:</b> <code>x{wager}</code>\n'
            f'┃ {ce("📊")} <b>Tổng cược cần:</b> <code>{fmt_money(required_bet)}đ</code>\n'
            f'┗━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'
            f'{ce("💰")} Số dư hiện tại: <code>{fmt_money(get_balance(uid))}đ</code>'
        )
        await _reply_code_success_safely(update, ctx, uid, code_str, reward, wager, "CODE NẠP", success_text)
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
    success_text = (
        f'{ce("🎉")} <b>NHẬN QUÀ THÀNH CÔNG!</b>\n\n'
        f'{ce("💰")} Bạn nhận được: <code>+{fmt_money(reward)}đ</code>\n'
        f'{ce("📊")} Hôm nay còn: <code>{remaining}/3</code> lượt nhập code.\n'
        f'Mã đã nhập: <code>{code_str}</code>'
    )
    await _reply_code_success_safely(update, ctx, uid, code_str, reward, 0, "GIFTCODE", success_text)

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

    if update.effective_chat.type == "private" and re.fullmatch(r'JAV88-[A-Z0-9]+(?:-[A-Z0-9]+)?', txt.strip().upper()):
        code_in = txt.strip().upper()
        if await redeem_giftcode(update, uid, code_in):
            return
        return await user_reply.reply_text(f'{ce("❌")} Mã quà tặng không tồn tại.', parse_mode=ParseMode.HTML)

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
            [btn("Hỗ trợ", "🆘", url="https://t.me/dgfrutil")]
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
        # Hiển thị menu trực tiếp, không gọi nap_cmd để tránh lấy nhầm args
        # từ context của lệnh /nap hoặc rơi vào thông báo cú pháp cũ.
        if is_banned(uid):
            return
        if is_total_maintenance() and uid not in ADMIN_IDS:
            return await user_reply.reply_text(
                f'{ce("⚡")} <b>HỆ THỐNG ĐANG BẢO TRÌ TOÀN BỘ</b>',
                parse_mode=ParseMode.HTML
            )
        if is_feature_banned(uid, 'nap'):
            return await user_reply.reply_text(
                f'{ce("🚫")} Tính năng NẠP TIỀN đã bị khóa!',
                parse_mode=ParseMode.HTML
            )
        if check_mt('mt_nap') and uid not in ADMIN_IDS:
            return await user_reply.reply_text(
                f'{ce("⚙️")} Nạp Tiền đang bảo trì!',
                parse_mode=ParseMode.HTML
            )
        try:
            _, caption, kb = deposit_menu_content(uid)
            return await user_reply.reply_text(
                caption, reply_markup=kb, parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Nút menu NẠP TIỀN lỗi: {e}")
            return await user_reply.reply_text(
                'Không thể hiển thị menu nạp tiền lúc này. Vui lòng thử lại sau.'
            )

    if key == "RÚT TIỀN":
        return await rut(update, ctx)

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
            f'{ce("🌷")} Hoa hồng cược đệ tử: 0% (không nhận hoa hồng từ cược)\n\n'
            f'{ce("👥")} Số đệ tử: {so_de_tu} | Hợp lệ event: 0\n\n'
            f'Hoa hồng hôm nay: 0\n'
            f'Tổng hoa hồng: 0\n'
            f'{ce("🎁")} Có thể nhận: 0\n'
            f'• Nhận tối thiểu: 20.000\n'
        )
        return await user_reply.reply_text(msg, reply_markup=kb, parse_mode=ParseMode.HTML)

    if key == "ĐUA TOP":
        kb = InlineKeyboardMarkup([
            [btn("Top cược ngày", "🏆", callback_data="top_cuoc_ngay")],
            [btn("Top đua đây (thắng/thua)", "🎖", callback_data="top_thang_thua")]
        ])
        return await user_reply.reply_text(f'{ce("🍭")} <b>ĐUA TOP</b>\nVui lòng chọn bảng xếp hạng:', reply_markup=kb, parse_mode=ParseMode.HTML)

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
        
        # Ẩn ID người nạp (5 số đầu)
        masked_id = str(target_id)
        if len(masked_id) > 5:
            masked_id = "*****" + masked_id[5:]
            
        try:
            await ctx.bot.send_message(chat_id=LOG_GROUP_ID,
                text=f'{ce("✅")} <b>THÔNG BÁO NẠP TIỀN</b>\n{ce("👥")} ID: <code>{masked_id}</code>\n{ce("💰")} Số tiền: <code>+{fmt_money(amount)}đ</code>',
                parse_mode=ParseMode.HTML)
        except: pass

        offer = promo_build_offer(target_id, amount)
        if offer:
            offer_text, keyboard = offer
            try:
                await ctx.bot.send_message(target_id,
                    f'{ce("✅")} <b>NẠP TIỀN THÀNH CÔNG!</b>\n\n'
                    f'{ce("💰")} Số tiền nạp: <code>+{fmt_money(amount)}đ</code>\n'
                    f'{ce("💎")} Số dư hiện tại: <code>{fmt_money(get_balance(target_id))}đ</code>\n\n'
                    + offer_text,
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
        required_bet = add_bonus_with_requirement(target_id, bonus_amount)
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
                f'• Cần cược <b>x{PROMO_WAGER_MULT}</b> vòng\n'
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

# ================= TÍNH NĂNG ADMIN MỚI =================
def _today_report_text():
    now = get_vietnam_time()
    d_str = now.strftime("%d/%m/%Y")
    like = f"% - {d_str}"
    def one(sql, args=()):
        rows = query(sql, args) or []
        return rows[0] if rows else None
    dep = one("SELECT COUNT(*), COALESCE(SUM(amount),0), COUNT(DISTINCT user_id) FROM deposit_history WHERE status='success' AND time LIKE %s", (like,)) or (0, 0, 0)
    wd = one("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM withdraw_history WHERE status='success' AND time LIKE %s", (like,)) or (0, 0)
    wd_pending = one("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM withdraw_history WHERE status='pending'") or (0, 0)
    bets = one("SELECT COALESCE(SUM(bet),0), COALESCE(SUM(win),0), COUNT(DISTINCT user_id) FROM bet_daily WHERE day=%s", (now.date(),)) or (0, 0, 0)
    promo = one("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM promo_daily_claims WHERE claim_date=%s", (promo_today_key(),)) or (0, 0)
    jackpot = get_jackpot()
    profit = int(dep[1] or 0) - int(wd[1] or 0)
    return (
        f'{ce("📊")} <b>BÁO CÁO HÔM NAY</b> — <code>{d_str}</code>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("📥")} <b>Nạp:</b> <code>{fmt_money(int(dep[1] or 0))}đ</code> ({dep[0]} lệnh, {dep[2]} người)\n'
        f'{ce("📤")} <b>Rút đã duyệt:</b> <code>{fmt_money(int(wd[1] or 0))}đ</code> ({wd[0]} lệnh)\n'
        f'{ce("⏰")} <b>Rút đang chờ:</b> <code>{fmt_money(int(wd_pending[1] or 0))}đ</code> ({wd_pending[0]} lệnh)\n'
        f'{ce("💵")} <b>Nạp - Rút:</b> <code>{"+" if profit >= 0 else "-"}{fmt_money(abs(profit))}đ</code>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("🎯")} <b>Tổng cược:</b> <code>{fmt_money(int(bets[0] or 0))}đ</code> ({bets[2]} người chơi)\n'
        f'{ce("🏆")} <b>Tổng trả thưởng:</b> <code>{fmt_money(int(bets[1] or 0))}đ</code>\n'
        f'{ce("🎁")} <b>Hũ jackpot:</b> <code>{fmt_money(jackpot)}đ</code>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("✨")} <b>Khuyến mãi {PROMO_PCT}% đã nhận hôm nay:</b> {promo[0]} người '
        f'(<code>+{fmt_money(int(int(promo[1] or 0) * PROMO_PCT / 100))}đ</code>)'
    )

@admin_only
async def homnay_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(_today_report_text(), parse_mode=ParseMode.HTML)

@admin_only
async def kmgio_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if ctx.args:
        act = ctx.args[0].lower()
        if act not in ("on", "off", "auto"):
            return await msg.reply_text(f'{ce("❌")} <b>Cú pháp:</b> <code>/kmgio [on|off|auto]</code>', parse_mode=ParseMode.HTML)
        set_setting("promo_mode", act)
    mode = promo_mode()
    mode_txt = {"auto": "TỰ ĐỘNG theo giờ vàng", "on": "ÉP BẬT cả ngày", "off": "ÉP TẮT"}[mode]
    active = promo_is_active()
    claimed = query("SELECT COUNT(*) FROM promo_daily_claims WHERE claim_date=%s", (promo_today_key(),)) or [(0,)]
    await msg.reply_text(
        f'{ce("⏰")} <b>KHUYẾN MÃI NẠP {PROMO_PCT}% / GIỜ VÀNG</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("⚙️")} <b>Chế độ:</b> {mode_txt}\n'
        f'{ce("🟢") if active else ce("🔴")} <b>Hiện tại:</b> {"ĐANG BẬT" if active else "ĐANG TẮT"}\n'
        f'{ce("🗓")} <b>Khung giờ vàng:</b> <code>{promo_windows_text()}</code> (hằng ngày)\n'
        f'{ce("➕")} <b>Thưởng thêm mỗi lệnh nạp:</b> {PROMO_ORDER_PCT}%\n'
        f'{ce("👥")} <b>Đã nhận {PROMO_PCT}% hôm nay:</b> {claimed[0][0]} người\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'<code>/kmgio on</code> bật cả ngày • <code>/kmgio off</code> tắt • <code>/kmgio auto</code> tự động',
        parse_mode=ParseMode.HTML)

@admin_only
async def dskm_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    rows = query("SELECT user_id, bonus_amount, required_bet, current_bet FROM user_bonus "
                 "WHERE required_bet > 0 ORDER BY (required_bet - current_bet) DESC LIMIT 20") or []
    if not rows:
        return await update.effective_message.reply_text(f'{ce("📊")} Hiện không có ai đang trong vòng cược khuyến mãi.', parse_mode=ParseMode.HTML)
    lines = [f'{ce("🎯")} <b>DANH SÁCH ĐANG CÓ VÒNG CƯỢC KHUYẾN MÃI</b> (top 20)\n']
    for uid_, bonus, req, cur in rows:
        left = max(0, int(req) - int(cur))
        lines.append(f'• <code>{uid_}</code> | thưởng <code>{fmt_money(int(bonus))}đ</code> | còn thiếu <code>{fmt_money(left)}đ</code> '
                     f'({min(100, int(cur * 100 / req)) if req else 0}%)')
    await update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

async def promo_golden_loop(bot):
    """Tự động thông báo bật/tắt giờ vàng vào nhóm + gửi báo cáo cuối ngày cho admin."""
    last = None
    while True:
        try:
            active = promo_is_active()
            if last is None:
                last = active
            elif active != last:
                last = active
                if active:
                    end_h = next((b for a, b in PROMO_GOLDEN_WINDOWS if a <= get_vietnam_time().hour < b), None)
                    until = f" đến hết <b>{end_h:02d}:59</b>" if (end_h and promo_mode() == "auto") else ""
                    text = (f'{ce("⏰")} <b>GIỜ VÀNG NẠP ĐÃ MỞ!</b> {ce("🎉")}\n'
                            f'{ce("✨")} Nạp ngay nhận khuyến mãi <b>{PROMO_PCT}%</b> (mỗi ngày 1 lần){until}\n'
                            f'{ce("➕")} Mỗi lệnh nạp được thưởng thêm <b>{PROMO_ORDER_PCT}%</b>\n'
                            f'{ce("🗓")} Giờ vàng hằng ngày: <code>{promo_windows_text()}</code>')
                else:
                    text = (f'{ce("⌛")} <b>Giờ vàng nạp đã kết thúc.</b>\n'
                            f'{ce("🗓")} Hẹn bạn khung giờ vàng tiếp theo: <code>{promo_windows_text()}</code>')
                for gid in GROUP_IDS:
                    try:
                        await bot.send_message(gid, text, parse_mode=ParseMode.HTML)
                    except Exception as e:
                        print(f"Không gửi được thông báo giờ vàng tới {gid}: {e}")
            # Báo cáo cuối ngày (23:55 - 23:59) gửi cho admin, mỗi ngày 1 lần
            now = get_vietnam_time()
            key = now.strftime("%Y-%m-%d")
            if now.hour == 23 and now.minute >= 55 and get_setting("daily_report_date", "") != key:
                set_setting("daily_report_date", key)
                report = _today_report_text()
                for aid in ADMIN_IDS:
                    try:
                        await bot.send_message(aid, report, parse_mode=ParseMode.HTML)
                    except Exception as e:
                        print(f"Không gửi được báo cáo cho admin {aid}: {e}")
        except Exception as e:
            print(f"Lỗi promo_golden_loop: {e}")
        await asyncio.sleep(20)

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

    d = OLD_MENU_ALIAS.get(d, d)
    if d.startswith("lh_choice_"):
        d = "gc_lh_" + d[len("lh_choice_"):]
    elif d.startswith("bcr_choice_"):
        d = "gc_bcr_" + d[len("bcr_choice_"):]
    if d == "game_list" or d.startswith(("gm_", "gc_", "gb_")):
        return await handle_game_callbacks(update, ctx, d)

    if d.startswith("gcn_"):
        return await handle_gift_flow_callback(update, ctx, d)
    if d in ("vip_doi", "vip_doi_all"):
        return await vip_exchange_callback(update, ctx, d)
    if d == "rw_claim":
        return await claim_rewards(update, ctx)

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
        tl_text, tl_kb = get_tich_luy_text(uid)
        return await q.message.reply_text(tl_text, reply_markup=tl_kb, parse_mode=ParseMode.HTML)
        
    if d == "acc_tich_luy_refresh" or d.startswith("acc_tich_luy_refresh_"):
        # Làm mới chỉ đọc dữ liệu; không phát sinh code. Chỉ chủ panel được làm mới.
        if d.startswith("acc_tich_luy_refresh_"):
            try:
                owner_id = int(d.rsplit("_", 1)[1])
            except (ValueError, IndexError):
                return await q.answer("Nút không hợp lệ.", show_alert=True)
            if uid != owner_id:
                return await q.answer("Đây không phải bảng tích lũy của bạn.", show_alert=True)
        elif q.message and q.message.chat.type != "private":
            return await q.answer("Vui lòng mở bảng tích lũy riêng trong bot.", show_alert=True)
        await q.answer("🔄 Đang cập nhật...")
        tl_text, tl_kb = get_tich_luy_text(uid)
        try:
            await q.message.edit_text(tl_text, reply_markup=tl_kb, parse_mode=ParseMode.HTML)
        except Exception as e:
            print(f"Không thể cập nhật bảng tích lũy: {e}")
        return

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

    if d == "ref_nhan_hh":
        await q.answer("Chương trình hoa hồng cược đệ tử đã tắt (0%).", show_alert=True)
        return
    if d == "ref_ruong":
        await q.answer("Bạn chưa đủ điều kiện nhận rương!", show_alert=True)
        return

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
        
        if d.startswith("ev_nhan_"):
            return await claim_rewards(update, ctx)

    # ===== XỬ LÝ NÚT NẠP TIỀN =====
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
            return await q.message.reply_text(f'{ce("🔔")} <b>HỖ TRỢ NẠP TIỀN</b>\n\nVui lòng liên hệ Admin: @dgfrutil\nHoặc dùng lệnh <code>/nap [số_tiền]</code> để tạo QR.', parse_mode=ParseMode.HTML)
        try:
            await q.answer()
            amount = int(d.split("_")[1])
            if amount < 10000 or amount > 100000000:
                return await q.message.reply_text("Số tiền nạp phải từ 10.000đ đến 100.000.000đ.")
            qr_url, caption, content = get_deposit_info(uid, amount)
            kb = InlineKeyboardMarkup([[btn("Hỗ Trợ", "🔔", callback_data="dep_support")]])
            # Gửi QR mới trước; chỉ xóa menu cũ sau khi gửi thành công để không mất giao diện nếu API lỗi.
            sent = await send_deposit_qr(ctx.bot, uid, qr_url, caption, kb, amount, content)
            try:
                await q.message.delete()
            except Exception:
                pass
            return sent
        except Exception as e:
            print(f"Nút nạp QR lỗi uid={uid}, data={d}: {type(e).__name__}: {e}"); traceback.print_exc()
            try:
                await ctx.bot.send_message(
                    chat_id=uid,
                    text=f'{ce("❌")} Không tạo được QR lúc này. Vui lòng thử lại sau hoặc liên hệ hỗ trợ.',
                    parse_mode=ParseMode.HTML)
            except Exception:
                pass
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

    if d.startswith("accept_promo_"):
        parts = d.split("_")
        target_id = int(parts[2])
        amount = int(parts[3])
        offered15 = len(parts) > 4 and parts[4] == "1"
        if q.from_user.id != target_id: return await q.answer("❌ Không phải yêu cầu của bạn!", show_alert=True)
        # Chống bấm nhận 2 lần trên cùng 1 tin nhắn
        done = query("INSERT INTO promo_offer_done (chat_id, message_id) VALUES (%s,%s) ON CONFLICT DO NOTHING RETURNING chat_id",
                     (q.message.chat_id, q.message.message_id))
        if not done:
            return await q.answer("❌ Khuyến mãi này đã được xử lý rồi!", show_alert=True)
        p15 = 0
        if offered15 and promo_claim_daily(target_id, amount):
            p15 = int(amount * PROMO_PCT / 100)
        p3 = int(amount * PROMO_ORDER_PCT / 100)
        total = p15 + p3
        if total <= 0:
            return await q.answer("❌ Không có khuyến mãi để nhận!", show_alert=True)
        add_promo_bonus(target_id, p15, p3)
        st = get_bet_progress_status(target_id)
        lines = [f'{ce("🎁")} <b>ĐÃ NHẬN KHUYẾN MÃI!</b>']
        if p15:
            lines.append(f'{ce("✨")} Thưởng {PROMO_PCT}%: <code>+{fmt_money(p15)}đ</code>')
        elif offered15:
            lines.append(f'{ce("📌")} <i>Hôm nay bạn đã nhận {PROMO_PCT}% rồi nên chỉ nhận phần {PROMO_ORDER_PCT}%.</i>')
        lines.append(f'{ce("➕")} Thưởng {PROMO_ORDER_PCT}% mỗi lệnh nạp: <code>+{fmt_money(p3)}đ</code>')
        lines.append(f'{ce("💰")} Tổng nhận: <code>+{fmt_money(total)}đ</code>')
        if st:
            lines.append(f'{ce("🎯")} Yêu cầu cược hiện tại: <code>{fmt_money(st["required_bet"])}đ</code> '
                         f'(đã cược <code>{fmt_money(st["current_bet"])}đ</code>)')
        lines.append(f'{ce("⚠️")} <b>Lưu ý:</b> {PROMO_PCT}% cược x{PROMO_WAGER_MULT} vòng, {PROMO_ORDER_PCT}% cược x{PROMO_ORDER_WAGER_MULT} vòng')
        await q.message.edit_text("\n".join(lines), parse_mode=ParseMode.HTML)
        return

    if d.startswith("accept_bonus_"):
        # Nút cũ (tin nhắn khuyến mãi gửi trước khi cập nhật) - vẫn nhận được, cược cộng dồn
        parts = d.split("_")
        target_id = int(parts[2])
        bonus_amount = int(parts[3])
        if q.from_user.id != target_id: return await q.answer("❌ Không phải yêu cầu của bạn!", show_alert=True)
        done = query("INSERT INTO promo_offer_done (chat_id, message_id) VALUES (%s,%s) ON CONFLICT DO NOTHING RETURNING chat_id",
                     (q.message.chat_id, q.message.message_id))
        if not done:
            return await q.answer("❌ Khuyến mãi này đã được xử lý rồi!", show_alert=True)
        required_bet = add_promo_bonus(target_id, bonus_amount, 0)
        await q.message.edit_text(
            f'{ce("🎁")} <b>ĐÃ NHẬN KHUYẾN MÃI!</b>\n'
            f'{ce("💰")} <code>+{fmt_money(bonus_amount)}đ</code>\n'
            f'{ce("🎯")} Yêu cầu cược thêm: <code>{fmt_money(required_bet)}đ</code>\n'
            f'{ce("⚠️")} <b>Lưu ý:</b> Phải cược x{PROMO_WAGER_MULT} vòng',
            parse_mode=ParseMode.HTML)
        return

    if d.startswith("reject_bonus_"):
        target_id = int(d.split("_")[2])
        if q.from_user.id != target_id: return await q.answer("❌ Không phải yêu cầu của bạn!", show_alert=True)
        await q.message.edit_text(
            f'{ce("❌")} <b>Đã từ chối khuyến mãi!</b>\n{ce("💰")} Số dư: <code>{fmt_money(get_balance(target_id))}đ</code>',
            parse_mode=ParseMode.HTML)
        return

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
            try:
                target_chat = await ctx.bot.get_chat(u_id)
                target_name = ("@" + target_chat.username) if getattr(target_chat, "username", None) else (getattr(target_chat, "full_name", None) or "Thành viên")
            except Exception:
                target_name = "Thành viên"
            try: await ctx.bot.send_message(chat_id=LOG_GROUP_ID, text=f'{ce("📤")} <b>RÚT TIỀN THÀNH CÔNG</b>\n👤 Người rút: {html.escape(target_name)}\n🆔 ID: <code>{mask_user_id(u_id)}</code>\n{ce("💰")} Số tiền: <code>{fmt_money(amt)}đ</code>\n{ce("✅")} Trạng thái: Thành công\n⏰ {get_vietnam_datetime_db()}', parse_mode=ParseMode.HTML)
            except Exception as e: pass
            try: await ctx.bot.send_message(u_id, f'{ce("✅")} Yêu cầu rút <code>{fmt_money(amt)}đ</code> đã được duyệt!', parse_mode=ParseMode.HTML)
            except: pass
            await q.edit_message_text(f'{ce("✅")} ĐÃ DUYỆT ID <code>{u_id}</code> | <code>{fmt_money(amt)}đ</code>', parse_mode=ParseMode.HTML)
        else:
            query("UPDATE withdraw_history SET status='rejected', admin_id=%s, admin_note='Từ chối' WHERE id=%s", (uid, wid))
            add_money(u_id, amt, "Hoàn tiền rút")
            try:
                target_chat = await ctx.bot.get_chat(u_id)
                target_name = ("@" + target_chat.username) if getattr(target_chat, "username", None) else (getattr(target_chat, "full_name", None) or "Thành viên")
            except Exception:
                target_name = "Thành viên"
            try: await ctx.bot.send_message(chat_id=LOG_GROUP_ID, text=f'{ce("❌")} <b>RÚT TIỀN BỊ TỪ CHỐI</b>\n👤 Người rút: {html.escape(target_name)}\n🆔 ID: <code>{mask_user_id(u_id)}</code>\n{ce("💰")} Số tiền: <code>{fmt_money(amt)}đ</code>\n{ce("🔄")} Đã hoàn tiền về ví!\n⏰ {get_vietnam_datetime_db()}', parse_mode=ParseMode.HTML)
            except Exception as e: pass
            try: await ctx.bot.send_message(u_id, f'{ce("❌")} Yêu cầu rút <code>{fmt_money(amt)}đ</code> bị từ chối.\n{ce("🔄")} Tiền đã được hoàn về số dư của bạn.', parse_mode=ParseMode.HTML)
            except: pass
            await q.edit_message_text(f'{ce("❌")} TỪ CHỐI ID <code>{u_id}</code> | <code>{fmt_money(amt)}đ</code>', parse_mode=ParseMode.HTML)
        return

    await q.answer()

# ============================================================
# WEBHOOK SEPAY
# ============================================================
async def sepay_webhook(request):
    # Xác thực API Key (Header Authorization: Bearer <API_KEY>)
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer ") or auth_header.split(" ")[1] != SEPAY_API_KEY:
        print("SePay Webhook: Unauthorized")
        return web.Response(status=401, text="Unauthorized")

    try:
        data = await request.json()
        print(f"SePay Webhook Data: {data}")

        # Lấy thông tin từ webhook
        content = data.get("content", "")  # Nội dung chuyển khoản
        amount = int(data.get("transferAmount", 0))  # Số tiền
        ref_code = data.get("referenceCode", "")  # Mã giao dịch

        if amount <= 0:
            return web.Response(status=200, text="Amount <= 0")

        # Tìm user_id từ nội dung chuyển khoản
        # Nội dung có dạng: "anh yeu em 123456" -> tìm số ID ở cuối
        match = re.search(r'(\d+)$', content.strip())
        if not match:
            print(f"SePay Webhook: Không tìm thấy ID trong nội dung: {content}")
            return web.Response(status=200, text="No ID found")

        user_id = int(match.group(1))
        get_user(user_id)

        # Kiểm tra giao dịch đã xử lý chưa (dựa vào ref_code)
        if ref_code:
            check_dup = query("SELECT 1 FROM deposit_history WHERE ref_code=%s", (ref_code,))
            if check_dup:
                print(f"SePay Webhook: Giao dịch {ref_code} đã xử lý")
                return web.Response(status=200, text="Duplicate")

        # Cộng tiền
        now_str = get_vietnam_datetime_db()
        query("INSERT INTO deposit_history (user_id, amount, admin_id, status, time, ref_code) VALUES (%s, %s, %s, %s, %s, %s)",
              (user_id, amount, 0, 'success', now_str, ref_code))
        add_money(user_id, amount, f"Nạp tiền tự động (SePay) +{amount:,}đ")

        # Thông báo cho user
        try:
            await _bot_instance.send_message(
                user_id,
                f'{ce("✅")} <b>NẠP TIỀN TỰ ĐỘNG THÀNH CÔNG!</b>\n'
                f'━━━━━━━━━━━━━━━━━━━━━\n'
                f'{ce("💰")} Số tiền: <code>+{fmt_money(amount)}đ</code>\n'
                f'{ce("📌")} Nội dung: <code>{content}</code>\n'
                f'{ce("⏰")} Thời gian: {now_str}\n'
                f'━━━━━━━━━━━━━━━━━━━━━\n'
                f'{ce("💎")} Số dư hiện tại: <code>{fmt_money(get_balance(user_id))}đ</code>',
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"SePay Webhook: Lỗi gửi tin nhắn cho user {user_id}: {e}")

        # Thông báo cho Admin (Log Group)
        masked_id = str(user_id)
        if len(masked_id) > 5:
            masked_id = "*****" + masked_id[5:]
        try:
            await _bot_instance.send_message(
                LOG_GROUP_ID,
                f'{ce("✅")} <b>THÔNG BÁO NẠP TIỀN TỰ ĐỘNG</b>\n'
                f'{ce("👥")} ID: <code>{masked_id}</code>\n'
                f'{ce("💰")} Số tiền: <code>+{fmt_money(amount)}đ</code>\n'
                f'{ce("📌")} Nội dung: <code>{content}</code>',
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"SePay Webhook: Lỗi gửi log group: {e}")

        # Báo trực tiếp tới toàn bộ admin khi webhook xác nhận nạp thành công.
        user_row = query("SELECT bank, stk, name, balance FROM users WHERE user_id=%s", (user_id,)) or [(None, None, None, 0)]
        bank, stk, account_name, current_balance = user_row[0]
        admin_notice = (
            f'{ce("✅")} <b>NẠP TIỀN THÀNH CÔNG</b>\n'
            f'🆔 ID: <code>{user_id}</code>\n'
            f'👤 Username: <code>không có trong webhook</code>\n'
            f'💵 Số tiền: <code>+{fmt_money(amount)}đ</code>\n'
            f'🏦 Ngân hàng: <code>{html.escape(str(bank or "Chưa liên kết"))}</code>\n'
            f'💳 STK: <code>{html.escape(str(stk or "—"))}</code>\n'
            f'👥 Chủ TK: <code>{html.escape(str(account_name or "—"))}</code>\n'
            f'💰 Số dư mới: <code>{fmt_money(int(current_balance or 0))}đ</code>\n'
            f'🧾 Mã giao dịch: <code>{html.escape(str(ref_code or "—"))}</code>\n'
            f'⏰ Thời gian: <code>{now_str}</code>'
        )
        for admin_id in ADMIN_IDS:
            try:
                await _bot_instance.send_message(admin_id, admin_notice, parse_mode=ParseMode.HTML)
            except Exception as e:
                print(f"Không gửi được thông báo nạp cho admin {admin_id}: {e}")

        # Khuyến mãi nạp: 15% (1 lần/ngày, giờ vàng) + 3% mỗi lệnh nạp
        offer = promo_build_offer(user_id, amount)
        if offer:
            offer_text, keyboard = offer
            try:
                await _bot_instance.send_message(user_id, offer_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            except Exception as e:
                print(f"SePay Webhook: Lỗi gửi khuyến mãi cho user {user_id}: {e}")

        return web.Response(status=200, text="OK")

    except Exception as e:
        print(f"SePay Webhook Error: {e}")
        traceback.print_exc()
        return web.Response(status=500, text="Internal Server Error")

async def start_webhook_server():
    app = web.Application()
    app.router.add_post('/sepay_webhook', sepay_webhook)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    print("✅ Webhook server started on port 8080")

# ============================================================
# ADMIN TOOLS: help, per-game maintenance, bot status and user tools
# ============================================================
ADMIN_GAMES = {
    "room": ("mt_taixiu_room", 1, "Tài Xỉu Room"),
    "xx": ("mt_xucxac_don", 2, "Xúc Xắc Đơn"),
    "lh": ("mt_longho", 3, "Long Hổ"),
    "mp": ("mt_minipoker", 4, "Mini Poker"),
    "bcr": ("mt_baccarat", 5, "Baccarat"),
    "xd4": ("mt_xocdia4", 7, "Xóc Đĩa 4 Vị"),
    "md5": ("mt_taixiumd5", 8, "Tài Xỉu MD5"),
    "bc": ("mt_baucua", 9, "Bầu Cua"),
    "xd6": ("mt_xocdia6", 10, "Xóc Đĩa 6 Vị"),
}
ADMIN_FEATURES = {"nap": ("mt_nap", "Nạp tiền"), "rut": ("mt_rut", "Rút tiền")}
GAME_ALIAS = {"tx":"room", "taixiu":"room", "xucxac":"xx", "longho":"lh", "minipoker":"mp",
              "baccarat":"bcr", "xocdia4":"xd4", "txmd5":"md5", "baucua":"bc", "xocdia6":"xd6",
              "naptien":"nap", "ruttien":"rut"}

def _admin_norm(value):
    value = (value or "").strip().lower()
    return GAME_ALIAS.get(value, value)

def _admin_mt_lines():
    rows = []
    for alias, (key, _gid, name) in ADMIN_GAMES.items():
        rows.append(f'{"🔴 BẢO TRÌ" if check_mt(key) else "🟢 HOẠT ĐỘNG"} <code>{alias}</code> — {name}')
    for alias, (key, name) in ADMIN_FEATURES.items():
        rows.append(f'{"🔴 BẢO TRÌ" if check_mt(key) else "🟢 HOẠT ĐỘNG"} <code>{alias}</code> — {name}')
    return "\n".join(rows)

@admin_only
async def admin_help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = (
        "🛠 <b>BẢNG LỆNH QUẢN TRỊ</b>\n━━━━━━━━━━━━━━━━━━━━\n"
        "<b>🧰 Bảo trì</b>\n"
        "<code>/baotrigame xx lh on</code> — bảo trì nhiều game\n"
        "<code>/baotrigame all on|off</code> — bảo trì/mở tất cả game + nạp/rút\n"
        "<code>/baotrigame games on|off</code> — tất cả game\n"
        "<code>/baotrigame nap rut on|off</code> — nạp/rút\n"
        "<code>/baotriht</code>, <code>/baotriall on|off</code>, <code>/baotritc on|off</code> — bảo trì hệ thống hiện có\n"
        "<code>/trangthai</code> — tổng quan bot\n\n"
        "<b>👥 Người dùng</b>\n<code>/user ID</code> — hồ sơ; <code>/timuser từ_khóa</code> — tìm user\n"
        "<code>/ban ID</code> / <code>/unban ID</code> — khóa/mở tài khoản\n"
        "<code>/camgame ID game</code> / <code>/mogame ID game|all</code> — khóa/mở game\n"
        "<code>/camtn ID nap|rut</code> / <code>/motn ID nap|rut|all</code> — khóa/mở nạp/rút\n"
        "<code>/dsban</code> — danh sách tài khoản bị khóa\n\n"
        "<b>💰 Số dư & giao dịch</b>\n<code>/add ID số_tiền</code>, <code>/sub ID số_tiền</code>, <code>/setsd ID số_tiền</code>\n"
        "<code>/naptien ID số_tiền</code> — nạp tay; <code>/dsnap</code> / <code>/dsrut</code> — danh sách chờ\n\n"
        "<b>📊 Thống kê / code</b>\n<code>/stats</code>, <code>/all</code>, <code>/thongke</code>, <code>/tong</code>, <code>/check ID</code>, <code>/hisall</code>\n"
        "<code>/top</code> — Top tương tác hôm nay; <code>/topsodu [n]</code> — Top số dư; <code>/topcuoc [n]</code>, <code>/taocode</code>, <code>/taocodeall</code>, <code>/xoacode</code>, <code>/taogift</code>, <code>/dsgift</code>, <code>/xoagift</code>\n"
        "<b>🎁 Khuyến mãi & báo cáo</b>\n"
        "<code>/kmgio</code> — xem/điều khiển giờ vàng nạp 15% (<code>on</code> / <code>off</code> / <code>auto</code>)\n"
        "<code>/homnay</code> — báo cáo nhanh hôm nay (nạp, rút, cược, khuyến mãi); tự gửi lúc 23:55 mỗi ngày\n"
        "<code>/dskm</code> — người đang có vòng cược khuyến mãi; <code>/kmnap ID số_tiền</code> — tặng khuyến mãi tay\n\n"
        "<b>🔎 Kiểm tra user (dùng được trong nhóm / chat riêng, có thể reply tin nhắn của user thay ID)</b>\n"
        "<code>/fulluser ID</code> — hồ sơ đầy đủ + bảng nút xem chat / xuất Excel theo ngày\n"
        "<code>/lsuser ID [kỳ]</code> — biến động số dư; <code>/lsnap</code> nạp; <code>/lsrut</code> rút; <code>/lscuoc</code> cược & thắng\n"
        "<code>/lscode ID [kỳ]</code> — code đã nhập; <code>/lsgift</code> giftcode đã dùng; <code>/lsmua</code> giftcode đã mua\n"
        "<code>/tongket ID [kỳ]</code> — tổng kết theo kỳ; <code>/xuatls ID [kỳ]</code> — xuất FULL Excel nhiều sheet\n"
        "<i>[kỳ] = all | số ngày | DD/MM/YYYY | DD/MM/YYYY - DD/MM/YYYY</i>\n"
        "<code>/resetbank ID</code> — gỡ liên kết ngân hàng\n"
        "<code>/checktt</code> — xem số tin hợp lệ, thứ hạng và mốc thưởng hôm nay; <code>/top</code> — Top 10 tương tác; <code>/help</code> — hướng dẫn thành viên; <code>/code MÃ</code> — nhập code.\n"
        "<code>/send nội_dung</code>, <code>/rep ID nội_dung</code> — thông báo/liên hệ user\n\n"
        "<b>Trạng thái bảo trì</b> (🔴 bảo trì, 🟢 hoạt động):\n" + _admin_mt_lines()
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

@admin_only
async def baotrigame_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args or []
    msg = update.effective_message
    if len(args) < 2 or args[-1].lower() not in ("on", "off"):
        return await msg.reply_text("Cú pháp: <code>/baotrigame [game...] on|off</code>\nGame: room xx lh mp bcr xd4 md5 bc xd6; tính năng: nap rut; nhóm: games all\n\n" + _admin_mt_lines(), parse_mode=ParseMode.HTML)
    action = args[-1].lower()
    value = "1" if action == "on" else "0"
    keys, names, invalid = [], [], []
    for raw in args[:-1]:
        key = _admin_norm(raw)
        if key == "all":
            keys.extend(v[0] for v in ADMIN_GAMES.values()); names.extend(v[2] for v in ADMIN_GAMES.values())
            keys.extend(v[0] for v in ADMIN_FEATURES.values()); names.extend(v[1] for v in ADMIN_FEATURES.values())
        elif key == "games":
            keys.extend(v[0] for v in ADMIN_GAMES.values()); names.extend(v[2] for v in ADMIN_GAMES.values())
        elif key in ADMIN_GAMES:
            keys.append(ADMIN_GAMES[key][0]); names.append(ADMIN_GAMES[key][2])
        elif key in ADMIN_FEATURES:
            keys.append(ADMIN_FEATURES[key][0]); names.append(ADMIN_FEATURES[key][1])
        else:
            invalid.append(raw)
    if invalid:
        return await msg.reply_text("Không nhận diện: <code>" + html.escape(", ".join(invalid)) + "</code>", parse_mode=ParseMode.HTML)
    for key in set(keys):
        set_setting(key, value)
    state = "ĐÃ BẬT BẢO TRÌ" if value == "1" else "ĐÃ MỞ LẠI"
    await msg.reply_text(f"🛠 <b>{state}</b>\n" + html.escape(", ".join(dict.fromkeys(names))) + "\n\n" + _admin_mt_lines(), parse_mode=ParseMode.HTML)

@admin_only
async def trangthai_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    def scalar(sql, args=()):
        rows = query(sql, args) or []
        return int(rows[0][0] or 0) if rows else 0
    total_users = scalar("SELECT COUNT(*) FROM users")
    total_balance = scalar("SELECT COALESCE(SUM(balance),0) FROM users")
    banned_users = scalar("SELECT COUNT(*) FROM banned")
    pending_deposits = scalar("SELECT COUNT(*) FROM deposit_history WHERE status='pending'")
    pending_withdrawals = scalar("SELECT COUNT(*) FROM withdraw_history WHERE status='pending'")
    text = ("📊 <b>TRẠNG THÁI BOT</b>\n━━━━━━━━━━━━━━━━━━━━\n"
            f"Bảo trì hệ thống: <b>{'🔴 BẬT' if is_system_maintenance() else '🟢 TẮT'}</b>\n"
            f"Bảo trì toàn bộ: <b>{'🔴 BẬT' if is_total_maintenance() else '🟢 TẮT'}</b>\n"
            f"Tổng user: <code>{total_users}</code> | Bị khóa: <code>{banned_users}</code>\n"
            f"Tổng số dư: <code>{fmt_money(total_balance)}đ</code>\n"
            f"Nạp chờ: <code>{pending_deposits}</code> | Rút chờ: <code>{pending_withdrawals}</code>\n\n"
            "<b>Game / tính năng</b>\n" + _admin_mt_lines())
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

@admin_only
async def user_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        target = int(ctx.args[0])
    except (IndexError, ValueError):
        return await update.effective_message.reply_text("Cú pháp: <code>/user ID</code>", parse_mode=ParseMode.HTML)
    rows = query("SELECT balance, refs, bank, stk, name, total_bet FROM users WHERE user_id=%s", (target,))
    if not rows:
        return await update.effective_message.reply_text("Không tìm thấy user.")
    bal, refs, bank, stk, name, total_bet = rows[0]
    dep = total_deposited(target)
    text = (f"👤 <b>HỒ SƠ USER</b> <code>{target}</code>\n━━━━━━━━━━━━━━━━━━━━\n"
            f"Trạng thái: <b>{'🔴 BỊ KHÓA' if is_banned(target) else '🟢 Hoạt động'}</b>\n"
            f"Số dư: <code>{fmt_money(int(bal or 0))}đ</code>\nTổng nạp: <code>{fmt_money(dep)}đ</code>\n"
            f"Tổng cược: <code>{fmt_money(int(total_bet or 0))}đ</code>\nSố lượt mời: <code>{refs or 0}</code>\n"
            f"Ngân hàng: <code>{html.escape(str(bank or '-'))}</code>\nSTK: <code>{html.escape(str(stk or '-'))}</code>\n"
            f"Tên: <code>{html.escape(str(name or '-'))}</code>")
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔒 Khóa", callback_data=f"admuser_ban_{target}"), InlineKeyboardButton("🔓 Mở khóa", callback_data=f"admuser_unban_{target}")]])
    await update.effective_message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

@admin_only
async def timuser_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        return await update.effective_message.reply_text("Cú pháp: <code>/timuser ID/STK/tên</code>", parse_mode=ParseMode.HTML)
    kw = " ".join(ctx.args).strip(); like = f"%{kw}%"
    rows = query("SELECT user_id,balance,bank,stk,name FROM users WHERE CAST(user_id AS TEXT) LIKE %s OR COALESCE(stk,'') LIKE %s OR COALESCE(name,'') ILIKE %s ORDER BY balance DESC LIMIT 15", (like, like, like)) or []
    if not rows:
        return await update.effective_message.reply_text("Không tìm thấy user phù hợp.")
    text = "🔎 <b>KẾT QUẢ TÌM USER</b>\n\n" + "\n".join(f"<code>{r[0]}</code> | {fmt_money(int(r[1] or 0))}đ | {html.escape(str(r[2] or '-'))} {html.escape(str(r[3] or '-'))} | {html.escape(str(r[4] or '-'))}" for r in rows)
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

@admin_only
async def camgame_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        target = int(ctx.args[0]); game = _admin_norm(ctx.args[1]); gid = ADMIN_GAMES[game][1]
    except (IndexError, ValueError, KeyError):
        return await update.effective_message.reply_text("Cú pháp: <code>/camgame ID room|xx|lh|mp|bcr|xd4|md5|bc|xd6</code>", parse_mode=ParseMode.HTML)
    query("INSERT INTO banned_games(user_id,game_id) VALUES(%s,%s) ON CONFLICT DO NOTHING", (target,gid))
    await update.effective_message.reply_text(f"Đã cấm user <code>{target}</code> chơi {html.escape(ADMIN_GAMES[game][2])}.", parse_mode=ParseMode.HTML)

@admin_only
async def mogame_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        target = int(ctx.args[0]); game = _admin_norm(ctx.args[1])
        if game != "all" and game not in ADMIN_GAMES: raise ValueError
    except (IndexError, ValueError):
        return await update.effective_message.reply_text("Cú pháp: <code>/mogame ID game|all</code>", parse_mode=ParseMode.HTML)
    if game == "all": query("DELETE FROM banned_games WHERE user_id=%s", (target,)); label = "tất cả game"
    else: query("DELETE FROM banned_games WHERE user_id=%s AND game_id=%s", (target, ADMIN_GAMES[game][1])); label = ADMIN_GAMES[game][2]
    await update.effective_message.reply_text(f"Đã gỡ cấm {html.escape(label)} cho <code>{target}</code>.", parse_mode=ParseMode.HTML)

@admin_only
async def camtn_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        target = int(ctx.args[0]); feature = _admin_norm(ctx.args[1])
        if feature not in ("nap", "rut"): raise ValueError
    except (IndexError, ValueError):
        return await update.effective_message.reply_text("Cú pháp: <code>/camtn ID nap|rut</code>", parse_mode=ParseMode.HTML)
    query("INSERT INTO banned_features(user_id,feature) VALUES(%s,%s) ON CONFLICT DO NOTHING", (target, feature))
    await update.effective_message.reply_text(f"Đã khóa {feature.upper()} cho <code>{target}</code>.", parse_mode=ParseMode.HTML)

@admin_only
async def motn_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        target = int(ctx.args[0]); feature = _admin_norm(ctx.args[1])
        if feature not in ("nap", "rut", "all"): raise ValueError
    except (IndexError, ValueError):
        return await update.effective_message.reply_text("Cú pháp: <code>/motn ID nap|rut|all</code>", parse_mode=ParseMode.HTML)
    if feature == "all": query("DELETE FROM banned_features WHERE user_id=%s", (target,))
    else: query("DELETE FROM banned_features WHERE user_id=%s AND feature=%s", (target, feature))
    await update.effective_message.reply_text(f"Đã mở khóa {feature.upper()} cho <code>{target}</code>.", parse_mode=ParseMode.HTML)

@admin_only
async def dsban_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    rows = query("SELECT b.user_id,COALESCE(u.balance,0) FROM banned b LEFT JOIN users u ON u.user_id=b.user_id ORDER BY b.user_id LIMIT 100") or []
    text = "🚫 <b>USER BỊ KHÓA</b>\n\n" + ("\n".join(f"<code>{r[0]}</code> | {fmt_money(int(r[1] or 0))}đ" for r in rows) if rows else "Chưa có user bị khóa.")
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

@admin_only
async def dsrut_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    rows = query("SELECT w.user_id,w.amount,w.time,u.bank,u.stk,u.name FROM withdraw_history w LEFT JOIN users u ON u.user_id=w.user_id WHERE w.status='pending' ORDER BY w.id LIMIT 10") or []
    if not rows:
        return await update.effective_message.reply_text("✅ Không có yêu cầu rút đang chờ.")
    for uid_, amount, time_, bank, stk, name in rows:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Duyệt", callback_data=f"ok_{uid_}_{amount}"), InlineKeyboardButton("❌ Từ chối", callback_data=f"no_{uid_}_{amount}")]])
        await update.effective_message.reply_text(f"📤 <b>RÚT CHỜ DUYỆT</b>\nID: <code>{uid_}</code>\nSố tiền: <code>{fmt_money(int(amount or 0))}đ</code>\nNgân hàng: <code>{html.escape(str(bank or '-'))}</code>\nSTK: <code>{html.escape(str(stk or '-'))}</code>\nTên: <code>{html.escape(str(name or '-'))}</code>\nThời gian: {html.escape(str(time_ or '-'))}", reply_markup=kb, parse_mode=ParseMode.HTML)

@admin_only
async def dsnap_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    rows = query("SELECT user_id,amount,time FROM deposit_history WHERE status='pending' ORDER BY id LIMIT 10") or []
    if not rows:
        return await update.effective_message.reply_text("✅ Không có yêu cầu nạp đang chờ.")
    for uid_, amount, time_ in rows:
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Duyệt", callback_data=f"app_dep_{uid_}_{amount}"), InlineKeyboardButton("❌ Từ chối", callback_data=f"rej_dep_{uid_}_{amount}")]])
        await update.effective_message.reply_text(f"📥 <b>NẠP CHỜ DUYỆT</b>\nID: <code>{uid_}</code>\nSố tiền: <code>{fmt_money(int(amount or 0))}đ</code>\nThời gian: {html.escape(str(time_ or '-'))}", reply_markup=kb, parse_mode=ParseMode.HTML)

@admin_only
async def setsd_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        target = int(ctx.args[0]); raw = ctx.args[1].lower().replace(",", "").replace(".", "").replace("đ", "")
        mult = 1000 if raw.endswith("k") else (1000000 if raw.endswith("m") else 1)
        amount = int(float(raw[:-1]) * mult) if mult != 1 else int(raw)
        if amount < 0: raise ValueError
    except (IndexError, ValueError):
        return await update.effective_message.reply_text("Cú pháp: <code>/setsd ID số_tiền</code> (vd 500k)", parse_mode=ParseMode.HTML)
    if not query("SELECT 1 FROM users WHERE user_id=%s", (target,)):
        return await update.effective_message.reply_text("Không tìm thấy user.")
    old = get_balance(target); diff = amount - old
    if diff: add_money(target, diff, "Admin điều chỉnh số dư")
    await update.effective_message.reply_text(f"Đã cập nhật <code>{target}</code>: {fmt_money(old)}đ → {fmt_money(amount)}đ", parse_mode=ParseMode.HTML)

async def _interaction_top_text(bot, group_id, date_text, limit=10):
    rows = query(
        "SELECT user_id, interaction_count FROM daily_top_interactions "
        "WHERE group_id=%s AND date=%s ORDER BY interaction_count DESC, user_id ASC LIMIT %s",
        (group_id, date_text, limit)
    ) or []
    if not rows:
        return "🏆 <b>TOP 10 TƯƠNG TÁC HÔM NAY</b>\n\nChưa có tin nhắn hợp lệ nào được ghi nhận trong nhóm."
    lines = [
        "🏆 <b>TOP 10 TƯƠNG TÁC HÔM NAY</b>",
        "📌 Tính theo tin nhắn hợp lệ trong nhóm hiện tại.",
        "",
    ]
    medals = ["🥇", "🥈", "🥉"]
    for rank, (user_id, count) in enumerate(rows, 1):
        prize = TOP_INTERACTION_PRIZES.get(rank, 0)
        display = await _telegram_name(bot, user_id, {})
        if not display:
            display = "Thành viên"
        lines.append(f"{medals[rank-1] if rank <= 3 else '⭐️'} {rank}. {html.escape(display)} · {int(count)} tin · 🎁 {fmt_money(prize)}đ")
    lines += [
        "",
        "⏱ Chốt bảng lúc 00:00; giftcode Top 10 được gửi riêng qua bot.",
        "🎁 Giftcode thưởng yêu cầu x7 vòng cược và hết hạn sau 24 giờ.",
        "",
        "⚠️ Không spam, flood, gửi lặp ký tự hoặc dùng bot/farm tương tác. Tin nhắn bị quản trị viên xóa và nội dung quảng cáo/spam không được tính.",
        "💡 Gõ /checktt để xem tiến trình của bạn."
    ]
    return "\n".join(lines)

async def top_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    group_id = chat.id if chat and chat.type != "private" else (GROUP_IDS[0] if GROUP_IDS else None)
    if not group_id:
        return await update.effective_message.reply_text("Chưa cấu hình nhóm tương tác.")
    text = await _interaction_top_text(ctx.bot, group_id, get_vietnam_date(), 10)
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

@admin_only
async def topsodu_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try: n = max(1, min(10, int(ctx.args[0]))) if ctx.args else 10
    except ValueError: n = 10
    rows = query("SELECT user_id,balance FROM users ORDER BY balance DESC LIMIT %s", (n,)) or []
    text = f"🏆 <b>TOP {n} SỐ DƯ</b>\n\n" + ("\n".join(f"{i}. <code>{r[0]}</code> — {fmt_money(int(r[1] or 0))}đ" for i,r in enumerate(rows,1)) or "Chưa có dữ liệu.")
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

async def checktt_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if not user:
        return
    # Trong nhóm: thống kê nhóm đang chat; trong tin nhắn riêng: nhóm tương tác đã cấu hình.
    group_id = chat.id if chat and chat.type != "private" else (GROUP_IDS[0] if GROUP_IDS else None)
    if not group_id:
        return await update.effective_message.reply_text("Chưa cấu hình nhóm tương tác.")
    today = get_vietnam_date()
    row = query("SELECT interaction_count FROM daily_top_interactions WHERE user_id=%s AND group_id=%s AND date=%s",
                (user.id, group_id, today))
    count = int(row[0][0] or 0) if row else 0
    rank_rows = query(
        "SELECT COUNT(*) + 1 FROM daily_top_interactions WHERE group_id=%s AND date=%s AND interaction_count > %s",
        (group_id, today, count)
    ) or []
    rank = int(rank_rows[0][0] or 1) if rank_rows else 1
    claimed_rows = query("SELECT milestone FROM interaction_reward_claims WHERE user_id=%s AND group_id=%s AND date=%s ORDER BY milestone",
                         (user.id, group_id, today)) or []
    claimed = {int(r[0]) for r in claimed_rows}
    next_milestone = next(((m, reward) for m, reward in INTERACTION_MILESTONES if count < m), None)
    if next_milestone:
        m, reward = next_milestone
        progress = f"🎯 Mốc tiếp theo: <b>{m:,}</b> tin — còn <b>{m-count:,}</b> tin để nhận <b>{fmt_money(reward)}đ</b>."
    else:
        progress = "🏆 Bạn đã đạt toàn bộ mốc tương tác trong ngày!"
    earned = "\n".join(f"✅ Mốc {m:,}: {fmt_money(reward)}đ {'(đã phát code)' if m in claimed else '(đang xử lý)'}"
                       for m, reward in INTERACTION_MILESTONES if m in claimed) or "Chưa nhận mốc nào hôm nay."
    await update.effective_message.reply_text(
        f"📊 <b>THỐNG KÊ TƯƠNG TÁC HÔM NAY</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 {html.escape(user.full_name or 'Thành viên')} · ID {mask_user_id(user.id)}\n"
        f"💬 Tin nhắn hợp lệ: <b>{count:,}</b>\n"
        f"🏆 Thứ hạng hiện tại: <b>{('#' + str(rank)) if count else 'Chưa có hạng'}</b>\n\n{progress}\n\n"
        f"🎁 <b>CÁC MỐC ĐÃ NHẬN</b>\n{earned}\n\n"
        f"🔐 Giftcode gửi riêng qua bot, yêu cầu x7 vòng cược và hết hạn sau 24 giờ.\n"
        f"💡 Dùng /top để xem bảng xếp hạng nhóm.",
        parse_mode=ParseMode.HTML
    )

async def interaction_help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🎁 <b>HỆ THỐNG TƯƠNG TÁC NHÓM</b>\n\n"
        "• /checktt — xem tiến trình tương tác hôm nay\n"
        "• /top — Top 10 tương tác hôm nay\n"
        "• /topnap — Top 10 nạp tiền\n"
        "• /topcuoc — Top 10 tổng cược\n"
        "• /code MÃ_CODE — nhập giftcode\n\n"
        "Mốc thưởng: 50 / 100 / 200 / 500 / 1.000 / 2.000 / 3.000 / 4.000 / 5.000 / 6.000 tin.\n"
        "Chỉ tính tin nhắn văn bản tự nhiên; lệnh bot, spam, tin lặp và flood nhanh không được tính.\n"
        "Giftcode được gửi riêng, yêu cầu x7 vòng cược, hạn dùng 24 giờ.",
        parse_mode=ParseMode.HTML
    )

async def settle_interaction_top_loop(bot):
    while True:
        try:
            yesterday_date = get_vietnam_time().date() - timedelta(days=1)
            date_text = yesterday_date.strftime("%d/%m/%Y")
            for group_id in GROUP_IDS:
                settled = query("SELECT 1 FROM interaction_top_settlements WHERE group_id=%s AND date=%s",
                                (group_id, date_text))
                if settled:
                    continue
                rows = query(
                    "SELECT user_id, interaction_count FROM daily_top_interactions "
                    "WHERE group_id=%s AND date=%s ORDER BY interaction_count DESC, user_id ASC LIMIT 10",
                    (group_id, date_text)
                ) or []
                public_lines = [f"🏆 <b>TOP TƯƠNG TÁC NGÀY {date_text}</b>"]
                for rank, (user_id, count) in enumerate(rows, 1):
                    reward = TOP_INTERACTION_PRIZES.get(rank, 0)
                    code = gen_gift_code("TOPTT")
                    expiry = get_vietnam_time() + timedelta(hours=24)
                    created = query(
                        "INSERT INTO giftcodes (code,ctype,reward,wager,expiry,require_deposit,required_amount,bound_user,used,created_by,created_at) "
                        "VALUES (%s,'INTERACT',%s,7,%s,0,0,%s,0,0,%s) ON CONFLICT DO NOTHING RETURNING code",
                        (code, reward, expiry, user_id, get_vietnam_datetime_db())
                    )
                    if created:
                        claim = query(
                            "INSERT INTO interaction_top_rewards (user_id,group_id,date,rank,reward_amount,code,created_at) "
                            "VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING user_id",
                            (user_id, group_id, date_text, rank, reward, code, get_vietnam_datetime_db())
                        )
                        if claim:
                            try:
                                await bot.send_message(
                                    user_id,
                                    f"🏆 <b>BẠN ĐẠT TOP {rank} TƯƠNG TÁC NGÀY {date_text}!</b>\n"
                                    f"💬 Tin hợp lệ: <b>{int(count):,}</b>\n"
                                    f"🎁 Giftcode: <code>{code}</code>\n"
                                    f"💰 Giá trị: <b>{fmt_money(reward)}đ</b> · Vòng cược x7\n"
                                    f"⏰ Hạn dùng 24 giờ. Nhập bằng <code>/code {code}</code>.",
                                    parse_mode=ParseMode.HTML
                                )
                            except Exception:
                                pass
                    display = await _telegram_name(bot, user_id, {})
                    public_lines.append(
                        f"{'🥇' if rank==1 else '🥈' if rank==2 else '🥉' if rank==3 else '⭐️'} "
                        f"{rank}. {html.escape(display or 'Thành viên')} · {int(count):,} tin · 🎁 {fmt_money(reward)}đ"
                    )
                    query("UPDATE daily_top_interactions SET rank=%s,reward_amount=%s,rewarded=1 WHERE user_id=%s AND group_id=%s AND date=%s",
                          (rank, reward, user_id, group_id, date_text))
                public_lines.append("\n🎁 Giftcode Top 10 đã gửi riêng qua bot; không đăng mã trong nhóm.")
                try:
                    await bot.send_message(group_id, "\n".join(public_lines), parse_mode=ParseMode.HTML)
                except Exception as e:
                    print(f"Không gửi được bảng Top tương tác nhóm {group_id}: {e}")
                query("INSERT INTO interaction_top_settlements (group_id,date,settled_at) VALUES (%s,%s,%s) ON CONFLICT DO NOTHING",
                      (group_id, date_text, get_vietnam_datetime_db()))
        except Exception as e:
            print(f"Lỗi settle top tương tác: {e}")
        await asyncio.sleep(30)



async def topnap_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Top 10 người nạp thành công."""
    rows = query(
        "SELECT user_id, SUM(amount) AS total FROM deposit_history "
        "WHERE LOWER(COALESCE(status,'')) IN ('success','successful','completed','approved','done') "
        "GROUP BY user_id ORDER BY total DESC LIMIT 10"
    ) or []
    lines = ["💎 <b>TOP 10 NẠP TIỀN</b>", "━━━━━━━━━━━━━━━━━━"]
    for i, row in enumerate(rows, 1):
        uid, total = row[0], int(row[1] or 0)
        display = await _telegram_name(ctx.bot, uid, {})
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "🏅"
        lines.append(f"{medal} {i}. {html.escape(display or 'Thành viên')} · {fmt_money(total)}đ")
    if not rows:
        lines.append("Chưa có dữ liệu nạp thành công.")
    await update.effective_message.reply_text("\\n".join(lines), parse_mode=ParseMode.HTML)

async def topcuoc_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try: n = max(1, min(10, int(ctx.args[0]))) if ctx.args else 10
    except ValueError: n = 10
    rows = query("SELECT user_id,COALESCE(total_bet,0) FROM users ORDER BY total_bet DESC NULLS LAST LIMIT %s", (n,)) or []
    text = f"🔥 <b>TOP {n} TỔNG CƯỢC</b>\n\n" + ("\n".join(f"{i}. <code>{r[0]}</code> — {fmt_money(int(r[1] or 0))}đ" for i,r in enumerate(rows,1)) or "Chưa có dữ liệu.")
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

async def admin_user_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id not in ADMIN_IDS:
        return await q.answer("Không có quyền!", show_alert=True)
    try: action, target = q.data.split("_")[1:3]; target = int(target)
    except (ValueError, IndexError): return await q.answer("Nút không hợp lệ.", show_alert=True)
    if action == "ban":
        query("INSERT INTO banned(user_id) VALUES(%s) ON CONFLICT DO NOTHING", (target,)); msg = "Đã khóa tài khoản."
    elif action == "unban":
        query("DELETE FROM banned WHERE user_id=%s", (target,)); msg = "Đã mở khóa tài khoản."
    else: return await q.answer()
    await q.answer(msg, show_alert=True)
    rows = query("SELECT balance,refs,bank,stk,name,total_bet FROM users WHERE user_id=%s", (target,))
    if rows:
        bal, refs, bank, stk, name, total_bet = rows[0]
        text = (f"👤 <b>HỒ SƠ USER</b> <code>{target}</code>\n"
                f"Trạng thái: <b>{'🔴 BỊ KHÓA' if is_banned(target) else '🟢 Hoạt động'}</b>\n"
                f"Số dư: <code>{fmt_money(int(bal or 0))}đ</code>\nTổng nạp: <code>{fmt_money(total_deposited(target))}đ</code>\n"
                f"Tổng cược: <code>{fmt_money(int(total_bet or 0))}đ</code>")
        kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔒 Khóa", callback_data=f"admuser_ban_{target}"), InlineKeyboardButton("🔓 Mở khóa", callback_data=f"admuser_unban_{target}")]])
        try: await q.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
        except Exception: pass


application = ApplicationBuilder().token(TOKEN).build()

# ============================================================
# BỘ CÔNG CỤ ADMIN V2 — HỒ SƠ + LỊCH SỬ ĐẦY ĐỦ + XUẤT EXCEL
#  /fulluser ID        — hồ sơ + bảng nút (xem trong chat hoặc xuất file Excel)
#  /lsuser ID [kỳ]     — biến động số dư     /lsnap ID [kỳ]  — lịch sử nạp
#  /lsrut ID [kỳ]      — lịch sử rút         /lscuoc ID [kỳ] — cược & thắng
#  /lscode ID [kỳ]     — code đã nhập        /lsgift ID [kỳ] — giftcode đã dùng
#  /lsmua ID [kỳ]      — giftcode đã mua     /tongket ID [kỳ] — tổng kết theo kỳ
#  /xuatls ID [kỳ]     — xuất FULL Excel nhiều sheet
#  [kỳ] = all | số ngày (7) | DD/MM/YYYY | DD/MM/YYYY - DD/MM/YYYY
#  Có thể reply tin nhắn của user thay cho việc nhập ID.
# ============================================================
RP_KINDS = {
    "all":  ("📊", "FULL HỒ SƠ"),
    "his":  ("💳", "BIẾN ĐỘNG SỐ DƯ"),
    "nap":  ("📥", "LỊCH SỬ NẠP"),
    "rut":  ("📤", "LỊCH SỬ RÚT"),
    "cuoc": ("🎲", "CƯỢC & THẮNG"),
    "code": ("🎟", "CODE ĐÃ NHẬP"),
    "mua":  ("🛒", "GIFTCODE ĐÃ MUA"),
    "gift": ("🎁", "GIFTCODE ĐÃ DÙNG"),
}
RP_PAGE_SIZE = 8
RP_DATE_RE = re.compile(r"\d{1,2}/\d{1,2}(?:/\d{2,4})?|\d{1,2}-\d{1,2}-\d{4}")

def _rp_money(n):
    try:
        return fmt_money(int(n or 0))
    except Exception:
        return "0"

def _rp_date(value):
    """Giá trị thời gian trong DB -> date theo giờ Việt Nam."""
    if isinstance(value, datetime):
        try:
            if value.tzinfo:
                value = value.astimezone(VIETNAM_TZ)
        except Exception:
            pass
        return value.date()
    return _parse_db_date(value)

def _rp_parse_date_text(s):
    s = (s or "").strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    m = re.fullmatch(r"(\d{1,2})/(\d{1,2})", s)
    if m:
        try:
            return datetime(get_vietnam_time().year, int(m.group(2)), int(m.group(1))).date()
        except ValueError:
            return None
    return None

def _rp_token_from_text(text):
    """'all' | '7' | '29/10/2026' | '01/10 - 29/10' -> token (all / nN / dYYYYMMDD / rYYYYMMDD-YYYYMMDD) hoặc None."""
    t = (text or "").strip().lower()
    if not t or t in ("all", "tatca", "tất cả", "tat ca", "tc", "full"):
        return "all"
    if t in ("homnay", "hôm nay", "hom nay", "today"):
        return "n1"
    if t.isdigit():
        n = int(t)
        return f"n{n}" if 1 <= n <= 3650 else None
    found = RP_DATE_RE.findall(t)
    dates = [_rp_parse_date_text(x) for x in found]
    if not dates or any(d is None for d in dates):
        return None
    if len(dates) == 1:
        return "d" + dates[0].strftime("%Y%m%d")
    if len(dates) == 2:
        a, b = sorted(dates)
        return f"r{a.strftime('%Y%m%d')}-{b.strftime('%Y%m%d')}"
    return None

def _rp_range(token):
    """token -> (start_date|None, end_date|None, nhãn hiển thị)."""
    today = get_vietnam_time().date()
    token = token or "all"
    try:
        if token == "all":
            return None, None, "Tất cả thời gian"
        if token.startswith("n"):
            n = max(1, int(token[1:]))
            start = today - timedelta(days=n - 1)
            if n == 1:
                return today, today, f"Hôm nay ({today.strftime('%d/%m/%Y')})"
            return start, today, f"{n} ngày gần đây ({start.strftime('%d/%m/%Y')} – {today.strftime('%d/%m/%Y')})"
        if token.startswith("d"):
            d = datetime.strptime(token[1:], "%Y%m%d").date()
            return d, d, f"Ngày {d.strftime('%d/%m/%Y')}"
        if token.startswith("r"):
            a_s, b_s = token[1:].split("-")
            a = datetime.strptime(a_s, "%Y%m%d").date()
            b = datetime.strptime(b_s, "%Y%m%d").date()
            return a, b, f"{a.strftime('%d/%m/%Y')} – {b.strftime('%d/%m/%Y')}"
    except Exception:
        pass
    return None, None, "Tất cả thời gian"

def _rp_tag(token):
    token = token or "all"
    if token == "all":
        return "all"
    if token.startswith("n"):
        return f"{token[1:]}ngay"
    return token[1:]

def _rp_in_range(value, start, end):
    if start is None and end is None:
        return True
    d = _rp_date(value)
    if not d:
        return False
    if start and d < start:
        return False
    if end and d > end:
        return False
    return True

def _rp_status(s):
    s = str(s or "").strip().lower()
    return {"success": "Thành công", "pending": "Chờ duyệt", "rejected": "Từ chối"}.get(s, (s or "—"))

def _rp_status_icon(label):
    return {"Thành công": "✅", "Chờ duyệt": "⌛", "Từ chối": "❌"}.get(label, "🔖")

def _rp_admin_label(admin_id):
    try:
        a = int(admin_id or 0)
    except Exception:
        a = 0
    return "Tự động / hệ thống" if a == 0 else f"Admin {a}"

def _rp_run(queries):
    """Chạy nhiều câu SQL trên MỘT kết nối (nhanh hơn, lỗi một câu không làm hỏng các câu khác)."""
    conn = get_db_connection()
    out = []
    try:
        cur = conn.cursor()
        for sql, args in queries:
            try:
                cur.execute(sql, args if args else None)
                out.append(cur.fetchall() if cur.description else [])
            except Exception as e:
                print(f"[report] SQL lỗi: {e}")
                conn.rollback()
                out.append([])
        conn.commit()
        cur.close()
    finally:
        conn.close()
    return out

def _rp_user_exists(uid):
    return bool(query("SELECT 1 FROM users WHERE user_id=%s", (uid,)))

# ------------------------------------------------------------
# THU THẬP DỮ LIỆU THEO LOẠI
# ------------------------------------------------------------
def _rp_collect(kind, uid, start, end):
    """Trả về dict: headers, rows (mới nhất trước), money_col, sum_cols, extra."""
    rows, extra = [], {}
    if kind == "his":
        raw = query("SELECT id, amount, note, time FROM history WHERE user_id=%s ORDER BY id DESC LIMIT 50000", (uid,)) or []
        inc = out = 0
        for r in raw:
            if not _rp_in_range(r[3], start, end):
                continue
            amt = int(r[1] or 0)
            rows.append((r[0], r[3] or "", amt, r[2] or ""))
            if amt >= 0:
                inc += amt
            else:
                out += -amt
        extra = {"in": inc, "out": out}
        return {"headers": ["#", "Thời gian", "Biến động (đ)", "Nội dung"], "rows": rows,
                "money_cols": [2], "sum_cols": [], "signed_col": 2, "extra": extra}
    if kind == "nap":
        raw = query("SELECT id, amount, status, time, ref_code, admin_id FROM deposit_history WHERE user_id=%s ORDER BY id DESC LIMIT 50000", (uid,)) or []
        ok = ok_n = pend = 0
        for r in raw:
            if not _rp_in_range(r[3], start, end):
                continue
            label = _rp_status(r[2]); amt = int(r[1] or 0)
            rows.append((r[0], r[3] or "", amt, label, r[4] or "", _rp_admin_label(r[5])))
            if label == "Thành công":
                ok += amt; ok_n += 1
            elif label == "Chờ duyệt":
                pend += amt
        extra = {"ok": ok, "ok_n": ok_n, "pending": pend}
        return {"headers": ["#", "Thời gian", "Số tiền (đ)", "Trạng thái", "Mã giao dịch", "Xử lý bởi"], "rows": rows,
                "money_cols": [2], "sum_cols": [], "extra": extra, "ok_sum_col": 2, "status_col": 3}
    if kind == "rut":
        raw = query("SELECT id, amount, status, time, admin_id, admin_note FROM withdraw_history WHERE user_id=%s ORDER BY id DESC LIMIT 50000", (uid,)) or []
        ok = ok_n = pend = 0
        for r in raw:
            if not _rp_in_range(r[3], start, end):
                continue
            label = _rp_status(r[2]); amt = int(r[1] or 0)
            rows.append((r[0], r[3] or "", amt, label, _rp_admin_label(r[4]) if r[4] else "—", r[5] or ""))
            if label == "Thành công":
                ok += amt; ok_n += 1
            elif label == "Chờ duyệt":
                pend += amt
        extra = {"ok": ok, "ok_n": ok_n, "pending": pend}
        return {"headers": ["#", "Thời gian", "Số tiền (đ)", "Trạng thái", "Admin xử lý", "Ghi chú"], "rows": rows,
                "money_cols": [2], "sum_cols": [], "extra": extra, "ok_sum_col": 2, "status_col": 3}
    if kind == "cuoc":
        win_sql = " OR ".join(["note LIKE %s"] * len(WIN_NOTE_PREFIXES))
        raw = query(
            "SELECT id, amount, note, time FROM history WHERE user_id=%s AND "
            "((amount<0 AND note ILIKE 'cược%%') OR (amount>0 AND (" + win_sql + "))) ORDER BY id DESC LIMIT 50000",
            (uid, *[p + "%" for p in WIN_NOTE_PREFIXES])
        ) or []
        bets = wins = nb = nw = 0
        for r in raw:
            if not _rp_in_range(r[3], start, end):
                continue
            amt = int(r[1] or 0)
            if amt < 0:
                rows.append((r[0], r[3] or "", "Cược", -amt, r[2] or "")); bets += -amt; nb += 1
            else:
                rows.append((r[0], r[3] or "", "Thắng / Hoàn", amt, r[2] or "")); wins += amt; nw += 1
        extra = {"bets": bets, "wins": wins, "net": wins - bets, "n_bet": nb, "n_win": nw}
        return {"headers": ["#", "Thời gian", "Loại", "Số tiền (đ)", "Nội dung"], "rows": rows,
                "money_cols": [3], "sum_cols": [], "extra": extra}
    if kind == "code":
        raw = query(
            "SELECT cu.code, cu.used_date, COALESCE(g.reward, c.reward), g.ctype "
            "FROM code_usage cu LEFT JOIN giftcodes g ON g.code=cu.code LEFT JOIN codes c ON c.code=cu.code "
            "WHERE cu.user_id=%s", (uid,)
        ) or []
        raw = sorted(raw, key=lambda r: (_rp_date(r[1]) or datetime(1970, 1, 1).date(), str(r[1] or "")), reverse=True)
        total = 0
        for r in raw:
            if not _rp_in_range(r[1], start, end):
                continue
            rw = int(r[2] or 0); total += rw
            rows.append((r[1] or "", r[0], rw, r[3] or "Code thường"))
        extra = {"sum": total}
        return {"headers": ["Thời gian nhập", "Mã code", "Giá trị (đ)", "Loại"], "rows": rows,
                "money_cols": [2], "sum_cols": [2], "extra": extra}
    if kind in ("mua", "gift"):
        if kind == "mua":
            sql = ("SELECT code, created_by, created_at, reward, wager, expiry, used, used_by, used_at, ctype, bound_user "
                   "FROM giftcodes WHERE created_by=%s ORDER BY created_at DESC LIMIT 50000")
        else:
            sql = ("SELECT code, created_by, created_at, reward, wager, expiry, used, used_by, used_at, ctype, bound_user "
                   "FROM giftcodes WHERE used_by=%s OR (bound_user=%s AND COALESCE(used,0)=0) ORDER BY created_at DESC LIMIT 50000")
        raw = query(sql, (uid,) if kind == "mua" else (uid, uid)) or []
        now = get_vietnam_time()
        total = used_n = 0
        for r in raw:
            when = r[2] if kind == "mua" else (r[8] or r[2])
            if not _rp_in_range(when, start, end):
                continue
            expired = False
            try:
                exp = r[5]
                if exp:
                    expired = (now > exp) if getattr(exp, "tzinfo", None) else (now.replace(tzinfo=None) > exp)
            except Exception:
                expired = False
            status = "Đã dùng" if r[6] else ("Hết hạn" if expired else "Chưa dùng")
            if r[6]:
                used_n += 1
            rw = int(r[3] or 0); total += rw
            rows.append((when or "", r[0], str(r[1] or ""), str(r[7] or ""), rw, f"x{r[4] or 0}", status,
                         str(r[5] or "")[:19], r[9] or ""))
        extra = {"sum": total, "used_n": used_n}
        return {"headers": ["Thời gian", "Mã code", "ID tạo/mua", "ID dùng", "Giá trị (đ)", "Vòng cược", "Trạng thái", "Hạn dùng", "Loại"],
                "rows": rows, "money_cols": [4], "sum_cols": [4], "extra": extra}
    return {"headers": [], "rows": [], "money_cols": [], "sum_cols": [], "extra": {}}

def _rp_profile_sync(uid):
    """Toàn bộ số liệu hồ sơ (toàn thời gian) — dùng 1 kết nối."""
    res = _rp_run([
        ("SELECT balance, refs, refed, bank, stk, name, last_checkin, last_withdraw, total_bet, bank_linked FROM users WHERE user_id=%s", (uid,)),
        ("SELECT COALESCE(SUM(amount),0), COUNT(*) FROM deposit_history WHERE user_id=%s AND status='success'", (uid,)),
        ("SELECT COALESCE(SUM(amount),0), COUNT(*) FROM withdraw_history WHERE user_id=%s AND status='success'", (uid,)),
        ("SELECT COALESCE(SUM(amount),0), COUNT(*) FROM withdraw_history WHERE user_id=%s AND status='pending'", (uid,)),
        ("SELECT bonus_amount, required_bet, current_bet FROM user_bonus WHERE user_id=%s", (uid,)),
        ("SELECT 1 FROM banned WHERE user_id=%s", (uid,)),
        ("SELECT game_id FROM banned_games WHERE user_id=%s ORDER BY game_id", (uid,)),
        ("SELECT feature FROM banned_features WHERE user_id=%s", (uid,)),
        ("SELECT amount, note, time FROM history WHERE user_id=%s ORDER BY id DESC LIMIT 5", (uid,)),
        ("SELECT COUNT(*) FROM giftcodes WHERE used_by=%s", (uid,)),
        ("SELECT COUNT(*) FROM code_usage WHERE user_id=%s", (uid,)),
        ("SELECT time FROM history WHERE user_id=%s ORDER BY id ASC LIMIT 1", (uid,)),
        ("SELECT COALESCE(SUM(amount),0) FROM history WHERE user_id=%s AND amount>0 AND (" + " OR ".join(["note LIKE %s"] * len(WIN_NOTE_PREFIXES)) + ")",
         (uid, *[p + "%" for p in WIN_NOTE_PREFIXES])),
    ])
    if not res[0]:
        return None
    u = res[0][0]
    gname = {v[1]: v[2] for v in ADMIN_GAMES.values()} if "ADMIN_GAMES" in globals() else {}
    return {
        "balance": int(u[0] or 0), "refs": u[1] or 0, "refed": u[2] or 0, "bank": u[3], "stk": u[4], "name": u[5],
        "last_checkin": u[6], "last_withdraw": u[7], "total_bet": int(u[8] or 0), "bank_linked": u[9],
        "dep": int(res[1][0][0] or 0) if res[1] else 0, "dep_n": int(res[1][0][1] or 0) if res[1] else 0,
        "wd": int(res[2][0][0] or 0) if res[2] else 0, "wd_n": int(res[2][0][1] or 0) if res[2] else 0,
        "wd_pend": int(res[3][0][0] or 0) if res[3] else 0, "wd_pend_n": int(res[3][0][1] or 0) if res[3] else 0,
        "bonus": res[4][0] if res[4] else None,
        "banned": bool(res[5]),
        "banned_games": [gname.get(r[0], f"Game {r[0]}") for r in res[6]],
        "banned_features": [str(r[0]).upper() for r in res[7]],
        "recent": res[8], "gifts_used": int(res[9][0][0] or 0) if res[9] else 0,
        "codes_used": int(res[10][0][0] or 0) if res[10] else 0,
        "first_time": res[11][0][0] if res[11] else None,
        "wins": int(res[12][0][0] or 0) if res[12] else 0,
    }

# ------------------------------------------------------------
# GIAO DIỆN: THẺ HỒ SƠ, CHỌN KỲ, XEM TRONG CHAT
# ------------------------------------------------------------
def _rp_bar(cur, total, width=10):
    try:
        ratio = 0 if not total else max(0.0, min(1.0, float(cur) / float(total)))
    except Exception:
        ratio = 0
    filled = int(round(ratio * width))
    return "█" * filled + "░" * (width - filled) + f" {int(ratio * 100)}%"

async def _rp_render_card(bot, uid):
    p = await asyncio.to_thread(_rp_profile_sync, uid)
    if not p:
        return None, None
    name = await _telegram_name(bot, uid, {})
    status = f'{ce("⛔️")} <b>BỊ KHÓA</b>' if p["banned"] else f'{ce("🟢")} <b>Hoạt động</b>'
    net = p["dep"] - p["wd"]
    pnl = p["wins"] - p["total_bet"]
    L = [
        f'{ce("📋")} <b>HỒ SƠ NGƯỜI DÙNG</b>',
        "━━━━━━━━━━━━━━━━━━━━",
        f'{ce("🆔")} ID: <code>{uid}</code>',
        f'{ce("👤")} Tên: <b>{html.escape(name or "Chưa lấy được")}</b>',
        f'{ce("🛡")} Trạng thái: {status}',
        f'{ce("💰")} Số dư: <b>{_rp_money(p["balance"])}đ</b>',
        "━━━━━━━━━━━━━━━━━━━━",
        f'{ce("📥")} Tổng nạp: <b>{_rp_money(p["dep"])}đ</b> · {p["dep_n"]} lần',
        f'{ce("📤")} Tổng rút: <b>{_rp_money(p["wd"])}đ</b> · {p["wd_n"]} lần',
    ]
    if p["wd_pend_n"]:
        L.append(f'{ce("⌛")} Rút đang chờ: <b>{_rp_money(p["wd_pend"])}đ</b> · {p["wd_pend_n"]} yêu cầu')
    L += [
        f'{ce("📈" if net >= 0 else "📉")} Nạp − Rút: <b>{"+" if net >= 0 else "−"}{_rp_money(abs(net))}đ</b>',
        f'{ce("🎲")} Tổng cược: <b>{_rp_money(p["total_bet"])}đ</b>',
        f'{ce("🏆")} Tổng thắng/hoàn: <b>{_rp_money(p["wins"])}đ</b>',
        f'{ce("📈" if pnl >= 0 else "📉")} Kết quả chơi: <b>{"+" if pnl >= 0 else "−"}{_rp_money(abs(pnl))}đ</b>',
    ]
    b = p["bonus"]
    if b and int(b[1] or 0) > 0:
        L.append(f'{ce("🎁")} Vòng cược KM: {_rp_money(b[2])}/{_rp_money(b[1])}đ · <code>{_rp_bar(b[2], b[1])}</code>')
    L += [
        "━━━━━━━━━━━━━━━━━━━━",
        f'{ce("🏦")} Ngân hàng: <code>{html.escape(str(p["bank"] or "Chưa liên kết"))}</code>',
        f'{ce("💳")} STK: <code>{html.escape(str(p["stk"] or "—"))}</code> · {html.escape(str(p["name"] or "—"))}',
        f'{ce("🔗")} Liên kết: {"Đã liên kết" if p["bank_linked"] else "Chưa liên kết"}',
        f'{ce("👥")} Đã mời: <b>{p["refs"]}</b> · {"Được mời bởi người khác" if p["refed"] else "Tự đăng ký"}',
        f'{ce("🎟")} Code đã nhập: <b>{p["codes_used"]}</b> · Giftcode đã dùng: <b>{p["gifts_used"]}</b>',
        f'{ce("🗓")} Check-in cuối: <code>{html.escape(str(p["last_checkin"] or "—"))}</code>',
        f'{ce("⏱")} Rút gần nhất: <code>{html.escape(str(p["last_withdraw"] or "—"))}</code>',
        f'{ce("⌛")} Hoạt động đầu tiên: <code>{html.escape(str(p["first_time"] or "—"))}</code>',
    ]
    if p["banned_games"] or p["banned_features"]:
        L.append(f'{ce("🚫")} Đang bị cấm: <b>{html.escape(", ".join(p["banned_games"] + p["banned_features"]))}</b>')
    if p["recent"]:
        L += ["━━━━━━━━━━━━━━━━━━━━", f'{ce("🔔")} <b>5 GIAO DỊCH GẦN NHẤT</b>']
        for amt, note, t in p["recent"]:
            a = int(amt or 0)
            L.append(f'{ce("📈" if a >= 0 else "📉")} <b>{"+" if a >= 0 else "−"}{_rp_money(abs(a))}đ</b> · {html.escape(str(note or ""))[:60]} · <i>{html.escape(str(t or ""))}</i>')
    L += ["━━━━━━━━━━━━━━━━━━━━", f'{ce("💡")} <i>Chọn mục bên dưới để xem trong chat hoặc xuất file Excel.</i>']
    kb = InlineKeyboardMarkup([
        [btn("XUẤT FULL HỒ SƠ (EXCEL)", "📊", callback_data=f"ar:{uid}:pick:all:-:x")],
        [btn("Lịch sử nạp", "📥", callback_data=f"ar:{uid}:pick:nap:-:x"),
         btn("Lịch sử rút", "📤", callback_data=f"ar:{uid}:pick:rut:-:x")],
        [btn("Cược & thắng", "🎲", callback_data=f"ar:{uid}:pick:cuoc:-:x"),
         btn("Biến động số dư", "💳", callback_data=f"ar:{uid}:pick:his:-:x")],
        [btn("Code đã nhập", "🎟", callback_data=f"ar:{uid}:pick:code:-:x"),
         btn("Gift đã dùng", "🎁", callback_data=f"ar:{uid}:pick:gift:-:x")],
        [btn("Gift đã mua", "🛒", callback_data=f"ar:{uid}:pick:mua:-:x"),
         btn("Làm mới", "🔄", callback_data=f"ar:{uid}:home:-:-:-")],
        [btn("Mở khóa tài khoản", "🔓", callback_data=f"ar:{uid}:unban:-:-:-") if p["banned"]
         else btn("Khóa tài khoản", "🔒", callback_data=f"ar:{uid}:ban:-:-:-")],
    ])
    return "\n".join(L), kb

def _rp_picker(uid, kind, mode):
    icon, label = RP_KINDS.get(kind, ("📊", kind.upper()))
    today = get_vietnam_time().date()
    yest = today - timedelta(days=1)
    act = "xls" if mode == "x" else "view"
    def cb(token):
        return f"ar:{uid}:{act}:{kind}:{token}:0"
    rows = [
        [btn(("● " if mode == "x" else "○ ") + "File Excel", "📥", callback_data=f"ar:{uid}:pick:{kind}:-:x"),
         btn(("● " if mode == "v" else "○ ") + ("Xem trong chat" if kind != "all" else "Xem tổng kết"), "👀", callback_data=f"ar:{uid}:pick:{kind}:-:v")],
        [btn("Hôm nay", "📅", callback_data=cb("n1")),
         btn("Hôm qua", "📅", callback_data=cb("d" + yest.strftime("%Y%m%d")))],
        [btn("3 ngày", "📅", callback_data=cb("n3")),
         btn("7 ngày", "📅", callback_data=cb("n7")),
         btn("30 ngày", "📅", callback_data=cb("n30"))],
        [btn("TẤT CẢ THỜI GIAN", "🗓", callback_data=cb("all"))],
    ]
    day_btns = [btn((today - timedelta(days=i)).strftime("%d/%m"), "📅",
                    callback_data=cb("d" + (today - timedelta(days=i)).strftime("%Y%m%d"))) for i in range(7)]
    rows.append(day_btns[:4])
    rows.append(day_btns[4:])
    rows.append([btn("Nhập ngày / khoảng ngày", "✍️", callback_data=f"ar:{uid}:ask:{kind}:-:{mode}")])
    rows.append([btn("Quay lại hồ sơ", "⬅️", callback_data=f"ar:{uid}:home:-:-:-")])
    text = (f'{ce("🗓")} <b>CHỌN KỲ BÁO CÁO</b>\n━━━━━━━━━━━━━━━━━━━━\n'
            f'{ce("🆔")} ID: <code>{uid}</code>\n'
            f'{ce(icon)} Mục: <b>{html.escape(label)}</b>\n'
            f'{ce("📎")} Hình thức: <b>{"File Excel" if mode == "x" else ("Xem trong chat" if kind != "all" else "Tổng kết trong chat")}</b>\n\n'
            f'{ce("💡")} <i>Bấm một nút ngày bên dưới — bot sẽ gửi ngay, không cần gõ gì thêm.</i>')
    return text, InlineKeyboardMarkup(rows)

def _rp_line(kind, row):
    e = html.escape
    if kind == "his":
        _id, t, amt, note = row
        return (f'{ce("📈" if amt >= 0 else "📉")} <b>{"+" if amt >= 0 else "−"}{_rp_money(abs(amt))}đ</b> · {e(str(note))[:70]}\n'
                f'    {ce("⏱")} <i>{e(str(t))}</i>')
    if kind == "nap":
        _id, t, amt, label, ref, adm = row
        return (f'{ce(_rp_status_icon(label))} <b>{_rp_money(amt)}đ</b> · {e(label)} · {e(adm)}\n'
                f'    {ce("⏱")} <i>{e(str(t))}</i>' + (f' · <code>{e(str(ref))[:24]}</code>' if ref else ""))
    if kind == "rut":
        _id, t, amt, label, adm, note = row
        return (f'{ce(_rp_status_icon(label))} <b>{_rp_money(amt)}đ</b> · {e(label)} · {e(str(adm))}\n'
                f'    {ce("⏱")} <i>{e(str(t))}</i>' + (f' · {e(str(note))[:40]}' if note else ""))
    if kind == "cuoc":
        _id, t, loai, amt, note = row
        return (f'{ce("🎲" if loai == "Cược" else "🏆")} <b>{_rp_money(amt)}đ</b> · {e(loai)} · {e(str(note))[:60]}\n'
                f'    {ce("⏱")} <i>{e(str(t))}</i>')
    if kind == "code":
        t, code, rw, loai = row
        return (f'{ce("🎟")} <code>{e(str(code))}</code> · <b>{_rp_money(rw)}đ</b> · {e(str(loai))}\n'
                f'    {ce("⏱")} <i>{e(str(t))}</i>')
    # mua / gift
    t, code, creator, used_by, rw, wager, status, exp, ctype = row
    icon = {"Đã dùng": "✅", "Hết hạn": "⌛", "Chưa dùng": "🎁"}.get(status, "🎁")
    return (f'{ce(icon)} <code>{e(str(code))}</code> · <b>{_rp_money(rw)}đ</b> · {e(wager)} · {e(status)}\n'
            f'    {ce("⏱")} <i>{e(str(t))}</i> · {e(str(ctype))}')

def _rp_summary_line(kind, data):
    x = data["extra"]
    if kind == "his":
        return f'{ce("📈")} Vào: <b>+{_rp_money(x["in"])}đ</b> · {ce("📉")} Ra: <b>−{_rp_money(x["out"])}đ</b>'
    if kind in ("nap", "rut"):
        s = f'{ce("✅")} Thành công: <b>{_rp_money(x["ok"])}đ</b> ({x["ok_n"]} lần)'
        if x["pending"]:
            s += f' · {ce("⌛")} Chờ: <b>{_rp_money(x["pending"])}đ</b>'
        return s
    if kind == "cuoc":
        return (f'{ce("🎲")} Cược: <b>{_rp_money(x["bets"])}đ</b> ({x["n_bet"]}) · {ce("🏆")} Thắng/hoàn: <b>{_rp_money(x["wins"])}đ</b> ({x["n_win"]})\n'
                f'{ce("📈" if x["net"] >= 0 else "📉")} Kết quả: <b>{"+" if x["net"] >= 0 else "−"}{_rp_money(abs(x["net"]))}đ</b>')
    if kind == "code":
        return f'{ce("💰")} Tổng giá trị: <b>{_rp_money(x["sum"])}đ</b>'
    return f'{ce("💰")} Tổng giá trị: <b>{_rp_money(x["sum"])}đ</b> · {ce("✅")} Đã dùng: <b>{x["used_n"]}</b>'

async def _rp_render_view(bot, uid, kind, token, page):
    start, end, label = _rp_range(token)
    data = await asyncio.to_thread(_rp_collect, kind, uid, start, end)
    rows = data["rows"]
    total = len(rows)
    pages = max(1, -(-total // RP_PAGE_SIZE))
    page = max(0, min(int(page or 0), pages - 1))
    icon, title = RP_KINDS.get(kind, ("📊", kind.upper()))
    name = await _telegram_name(bot, uid, {})
    L = [
        f'{ce(icon)} <b>{html.escape(title)}</b>',
        "━━━━━━━━━━━━━━━━━━━━",
        f'{ce("🆔")} <code>{uid}</code> · {ce("👤")} {html.escape(name or "Chưa lấy được")}',
        f'{ce("🗓")} {html.escape(label)}',
        f'{ce("📄")} Tổng: <b>{total}</b> dòng',
        _rp_summary_line(kind, data),
        "━━━━━━━━━━━━━━━━━━━━",
    ]
    chunk = rows[page * RP_PAGE_SIZE:(page + 1) * RP_PAGE_SIZE]
    if not chunk:
        L.append("Không có dữ liệu trong kỳ này.")
    for r in chunk:
        L.append(_rp_line(kind, r))
    L += ["━━━━━━━━━━━━━━━━━━━━", f'{ce("📎")} Trang <b>{page + 1}/{pages}</b>']
    nav = []
    if page > 0:
        nav.append(btn("Trước", "⬅️", callback_data=f"ar:{uid}:view:{kind}:{token}:{page - 1}"))
    nav.append(InlineKeyboardButton(f"{page + 1}/{pages}", callback_data="ar:0:noop:-:-:-"))
    if page < pages - 1:
        nav.append(btn("Sau", "➡️", callback_data=f"ar:{uid}:view:{kind}:{token}:{page + 1}"))
    kb = InlineKeyboardMarkup([
        nav,
        [btn("Xuất Excel kỳ này", "📥", callback_data=f"ar:{uid}:xls:{kind}:{token}:0"),
         btn("Đổi kỳ", "🗓", callback_data=f"ar:{uid}:pick:{kind}:-:v")],
        [btn("Hồ sơ", "🏠", callback_data=f"ar:{uid}:home:-:-:-")],
    ])
    return "\n".join(L), kb

async def _rp_render_summary(bot, uid, token):
    start, end, label = _rp_range(token)
    kinds = ["nap", "rut", "cuoc", "his", "code", "gift"]
    res = await asyncio.gather(*[asyncio.to_thread(_rp_collect, k, uid, start, end) for k in kinds])
    d = dict(zip(kinds, res))
    p = await asyncio.to_thread(_rp_profile_sync, uid)
    name = await _telegram_name(bot, uid, {})
    net = d["nap"]["extra"]["ok"] - d["rut"]["extra"]["ok"]
    cx = d["cuoc"]["extra"]
    L = [
        f'{ce("📊")} <b>TỔNG KẾT NGƯỜI DÙNG</b>',
        "━━━━━━━━━━━━━━━━━━━━",
        f'{ce("🆔")} <code>{uid}</code> · {ce("👤")} {html.escape(name or "Chưa lấy được")}',
        f'{ce("🗓")} {html.escape(label)}',
        f'{ce("💰")} Số dư hiện tại: <b>{_rp_money(p["balance"]) if p else "—"}đ</b>',
        "━━━━━━━━━━━━━━━━━━━━",
        f'{ce("📥")} Nạp thành công: <b>{_rp_money(d["nap"]["extra"]["ok"])}đ</b> ({d["nap"]["extra"]["ok_n"]} lần)',
        f'{ce("📤")} Rút thành công: <b>{_rp_money(d["rut"]["extra"]["ok"])}đ</b> ({d["rut"]["extra"]["ok_n"]} lần)',
        f'{ce("📈" if net >= 0 else "📉")} Nạp − Rút: <b>{"+" if net >= 0 else "−"}{_rp_money(abs(net))}đ</b>',
        "━━━━━━━━━━━━━━━━━━━━",
        f'{ce("🎲")} Tổng cược: <b>{_rp_money(cx["bets"])}đ</b> ({cx["n_bet"]} lượt)',
        f'{ce("🏆")} Thắng/hoàn: <b>{_rp_money(cx["wins"])}đ</b> ({cx["n_win"]} lượt)',
        f'{ce("📈" if cx["net"] >= 0 else "📉")} Kết quả chơi: <b>{"+" if cx["net"] >= 0 else "−"}{_rp_money(abs(cx["net"]))}đ</b>',
        "━━━━━━━━━━━━━━━━━━━━",
        f'{ce("🎟")} Code nhập: <b>{len(d["code"]["rows"])}</b> ({_rp_money(d["code"]["extra"]["sum"])}đ)',
        f'{ce("🎁")} Giftcode dùng: <b>{d["gift"]["extra"]["used_n"]}</b> ({_rp_money(d["gift"]["extra"]["sum"])}đ)',
        f'{ce("💳")} Biến động số dư: <b>{len(d["his"]["rows"])}</b> dòng · +{_rp_money(d["his"]["extra"]["in"])}đ / −{_rp_money(d["his"]["extra"]["out"])}đ',
    ]
    kb = InlineKeyboardMarkup([
        [btn("Xuất FULL Excel kỳ này", "📊", callback_data=f"ar:{uid}:xls:all:{token}:0"),
         btn("Đổi kỳ", "🗓", callback_data=f"ar:{uid}:pick:all:-:v")],
        [btn("Hồ sơ", "🏠", callback_data=f"ar:{uid}:home:-:-:-")],
    ])
    return "\n".join(L), kb

# ------------------------------------------------------------
# XUẤT FILE (XLSX nhiều sheet, tự fallback CSV nếu thiếu openpyxl)
# ------------------------------------------------------------
def _rp_build_xlsx(title, subtitle, sheets):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    TAB = {"Tổng quan": "183153", "Biến động số dư": "246B8E", "Nạp": "2E8B57", "Rút": "C0392B",
           "Cược & Thắng": "8E44AD", "Code đã nhập": "D68910", "Gift đã mua": "117A8B", "Gift đã dùng": "117A8B"}
    wb = Workbook()
    wb.remove(wb.active)
    used = set()
    thin = Side(style="hair", color="C9D6E8")
    for sh in sheets:
        name = re.sub(r"[\\/*?:\[\]]", "", sh["name"])[:31] or "Sheet"
        base, i = name, 2
        while name in used:
            name = f"{base[:28]}_{i}"; i += 1
        used.add(name)
        ws = wb.create_sheet(name)
        ws.sheet_properties.tabColor = TAB.get(sh["name"], "246B8E")
        headers, rows = sh["headers"], sh["rows"]
        ncol = max(1, len(headers))
        money = set(sh.get("money_cols", []))
        signed = sh.get("signed_col")
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncol)
        c = ws.cell(1, 1, title)
        c.font = Font(name="Arial", size=15, bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="183153")
        c.alignment = Alignment(horizontal="center", vertical="center")
        ws.row_dimensions[1].height = 32
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncol)
        c2 = ws.cell(2, 1, f"{subtitle}  |  Xuất lúc: {get_vietnam_datetime_db()}  |  Số dòng: {len(rows)}")
        c2.font = Font(name="Arial", italic=True, size=9, color="555555")
        c2.alignment = Alignment(horizontal="center")
        for ci, h in enumerate(headers, 1):
            hc = ws.cell(4, ci, str(h))
            hc.font = Font(name="Arial", bold=True, color="FFFFFF", size=10)
            hc.fill = PatternFill("solid", fgColor="246B8E")
            hc.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.row_dimensions[4].height = 24
        for ri, row in enumerate(rows, 5):
            zebra = PatternFill("solid", fgColor="F3F7FB") if ri % 2 == 0 else None
            for ci, v in enumerate(row, 1):
                cell = ws.cell(ri, ci)
                if isinstance(v, (int, float)) and not isinstance(v, bool) and (ci - 1) in money:
                    cell.value = v
                    cell.number_format = "#,##0"
                    cell.alignment = Alignment(horizontal="right", vertical="top")
                    if signed is not None and (ci - 1) == signed:
                        cell.font = Font(name="Arial", size=10, bold=True, color="1E8449" if v >= 0 else "C0392B")
                    else:
                        cell.font = Font(name="Arial", size=10)
                else:
                    s = "" if v is None else str(v)
                    cell.value = s
                    cell.data_type = "s"          # luôn là chuỗi -> không bị hiểu thành công thức Excel
                    cell.font = Font(name="Arial", size=10)
                    cell.alignment = Alignment(vertical="top", wrap_text=len(s) > 40)
                cell.border = Border(bottom=thin)
                if zebra:
                    cell.fill = zebra
        last = 4 + len(rows)
        if sh.get("sum_cols") and rows:
            tr = last + 1
            ws.cell(tr, 1, "TỔNG").font = Font(name="Arial", bold=True)
            for ci in sh["sum_cols"]:
                total = sum(int(r[ci] or 0) for r in rows if isinstance(r[ci], (int, float)))
                tc = ws.cell(tr, ci + 1, total)
                tc.number_format = "#,##0"
                tc.font = Font(name="Arial", bold=True)
                tc.fill = PatternFill("solid", fgColor="FFF2CC")
        ws.freeze_panes = "A5"
        if rows:
            ws.auto_filter.ref = f"A4:{get_column_letter(ncol)}{last}"
        for ci, h in enumerate(headers, 1):
            vals = [len(str(h))] + [len(str(r[ci - 1])) for r in rows[:300] if r[ci - 1] is not None]
            ws.column_dimensions[get_column_letter(ci)].width = min(48, max(12, max(vals) + 3))
        ws.page_setup.orientation = "landscape"
        ws.print_title_rows = "4:4"
    wb.properties.title = title
    out = BytesIO()
    wb.save(out)
    out.seek(0)
    return out

def _rp_build_csv(title, subtitle, sheets):
    import io as _io
    def safe(v):
        s = "" if v is None else v
        if isinstance(s, str) and s[:1] in ("=", "+", "@"):
            return "'" + s
        return s
    sio = _io.StringIO()
    w = csv.writer(sio)
    w.writerow([title]); w.writerow([subtitle])
    for sh in sheets:
        w.writerow([]); w.writerow([f"== {sh['name']} =="]); w.writerow(sh["headers"])
        for r in sh["rows"]:
            w.writerow([safe(v) for v in r])
    return BytesIO(("\ufeff" + sio.getvalue()).encode("utf-8"))

async def _rp_export(message, bot, uid, kind, token):
    start, end, label = _rp_range(token)
    icon, title = RP_KINDS.get(kind, ("📊", kind.upper()))
    status = await message.reply_text("⏳ Đang tạo file báo cáo, vui lòng chờ…")
    try:
        name = await _telegram_name(bot, uid, {})
        if kind == "all":
            order = ["his", "nap", "rut", "cuoc", "code", "mua", "gift"]
            res = await asyncio.gather(*[asyncio.to_thread(_rp_collect, k, uid, start, end) for k in order])
            data = dict(zip(order, res))
            p = await asyncio.to_thread(_rp_profile_sync, uid)
            cx = data["cuoc"]["extra"]
            kv = [
                ("ID người dùng", str(uid)), ("Tên / @username", name or "Chưa lấy được"),
                ("Trạng thái", "BỊ KHÓA" if (p and p["banned"]) else "Hoạt động"),
                ("Số dư hiện tại (đ)", p["balance"] if p else ""),
                ("Ngân hàng", (p or {}).get("bank") or "Chưa liên kết"), ("Số tài khoản", (p or {}).get("stk") or ""),
                ("Chủ tài khoản", (p or {}).get("name") or ""),
                ("Đã liên kết ngân hàng", "Có" if (p and p["bank_linked"]) else "Không"),
                ("Số người đã mời", (p or {}).get("refs", 0)),
                ("Check-in cuối", (p or {}).get("last_checkin") or ""), ("Rút gần nhất", (p or {}).get("last_withdraw") or ""),
                ("Hoạt động đầu tiên", (p or {}).get("first_time") or ""),
                ("— TOÀN THỜI GIAN —", ""),
                ("Tổng nạp thành công (đ)", p["dep"] if p else ""), ("Số lần nạp thành công", p["dep_n"] if p else ""),
                ("Tổng rút thành công (đ)", p["wd"] if p else ""), ("Số lần rút thành công", p["wd_n"] if p else ""),
                ("Rút đang chờ (đ)", p["wd_pend"] if p else ""), ("Tổng cược (đ)", p["total_bet"] if p else ""),
                (f"— KỲ: {label} —", ""),
                ("Nạp thành công trong kỳ (đ)", data["nap"]["extra"]["ok"]), ("Rút thành công trong kỳ (đ)", data["rut"]["extra"]["ok"]),
                ("Tổng cược trong kỳ (đ)", cx["bets"]), ("Thắng / hoàn trong kỳ (đ)", cx["wins"]),
                ("Kết quả chơi trong kỳ (đ)", cx["net"]),
                ("Số code đã nhập trong kỳ", len(data["code"]["rows"])),
                ("Số giftcode đã dùng trong kỳ", data["gift"]["extra"]["used_n"]),
            ]
            kv_rows = [(k, v) for k, v in kv]
            sheets = [
                {"name": "Tổng quan", "headers": ["Chỉ tiêu", "Giá trị"], "rows": kv_rows, "money_cols": [1], "sum_cols": []},
                {"name": "Biến động số dư", **data["his"]},
                {"name": "Nạp", **data["nap"]}, {"name": "Rút", **data["rut"]},
                {"name": "Cược & Thắng", **data["cuoc"]}, {"name": "Code đã nhập", **data["code"]},
                {"name": "Gift đã mua", **data["mua"]}, {"name": "Gift đã dùng", **data["gift"]},
            ]
            total_rows = sum(len(s["rows"]) for s in sheets[1:])
        else:
            data = await asyncio.to_thread(_rp_collect, kind, uid, start, end)
            sheets = [{"name": {"his": "Biến động số dư", "nap": "Nạp", "rut": "Rút", "cuoc": "Cược & Thắng",
                                "code": "Code đã nhập", "mua": "Gift đã mua", "gift": "Gift đã dùng"}.get(kind, "Báo cáo"), **data}]
            total_rows = len(data["rows"])
        head = f"{title} — ID {uid} — {label}"
        sub = f"Tài khoản: {name or 'Chưa lấy được'}"
        tag = _rp_tag(token)
        try:
            bio = await asyncio.to_thread(_rp_build_xlsx, head, sub, sheets)
            fname, note = f"{'fulluser' if kind == 'all' else kind}_{uid}_{tag}.xlsx", ""
        except ImportError:
            bio = await asyncio.to_thread(_rp_build_csv, head, sub, sheets)
            fname, note = f"{'fulluser' if kind == 'all' else kind}_{uid}_{tag}.csv", "\n⚠️ Máy chủ chưa cài <code>openpyxl</code> nên bot xuất CSV (mở được bằng Excel)."
        bio.seek(0)
        await message.reply_document(
            document=bio, filename=fname,
            caption=(f'{ce(icon)} <b>{html.escape(title)}</b>\n'
                     f'{ce("🆔")} ID: <code>{uid}</code> · {ce("👤")} {html.escape(name or "Chưa lấy được")}\n'
                     f'{ce("🗓")} {html.escape(label)}\n'
                     f'{ce("📄")} Tổng: <b>{total_rows}</b> dòng' + note),
            parse_mode=ParseMode.HTML)
        try:
            await status.delete()
        except Exception:
            pass
    except Exception as e:
        traceback.print_exc()
        try:
            await status.edit_text(f"❌ Không xuất được file: {html.escape(str(e))[:300]}", parse_mode=ParseMode.HTML)
        except Exception:
            pass

# ------------------------------------------------------------
# LỆNH ADMIN
# ------------------------------------------------------------
def _rp_parse_cmd_args(update, ctx):
    args = list(ctx.args or [])
    msg = update.effective_message
    uid = None
    if args and args[0].lstrip("-").isdigit():
        uid = int(args.pop(0))
    elif msg and msg.reply_to_message and msg.reply_to_message.from_user:
        uid = msg.reply_to_message.from_user.id
    if uid is None:
        return None, None
    token = _rp_token_from_text(" ".join(args)) if args else "all"
    return uid, token

async def _rp_cmd_guard(update, ctx, usage):
    uid, token = _rp_parse_cmd_args(update, ctx)
    msg = update.effective_message
    if uid is None:
        await msg.reply_text(usage, parse_mode=ParseMode.HTML); return None, None
    if token is None:
        await msg.reply_text("❌ Kỳ không hợp lệ. Dùng: <code>all</code>, <code>7</code> (số ngày), <code>29/10/2026</code> hoặc <code>01/10/2026 - 29/10/2026</code>.", parse_mode=ParseMode.HTML)
        return None, None
    if not await asyncio.to_thread(_rp_user_exists, uid):
        await msg.reply_text("❌ Không tìm thấy người dùng này trong hệ thống."); return None, None
    return uid, token

RP_USAGE_TAIL = "\n<i>[kỳ] = all | số ngày | DD/MM/YYYY | DD/MM/YYYY - DD/MM/YYYY. Có thể reply tin nhắn của user thay cho ID.</i>"

@admin_only
async def fulluser_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    uid = None
    if ctx.args and ctx.args[0].lstrip("-").isdigit():
        uid = int(ctx.args[0])
    elif msg.reply_to_message and msg.reply_to_message.from_user:
        uid = msg.reply_to_message.from_user.id
    if uid is None:
        return await msg.reply_text("Cú pháp: <code>/fulluser ID</code> (hoặc reply tin nhắn của user)", parse_mode=ParseMode.HTML)
    text, kb = await _rp_render_card(ctx.bot, uid)
    if not text:
        return await msg.reply_text("❌ Không tìm thấy người dùng này.")
    await msg.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

def _rp_make_view_cmd(kind, cmd, desc):
    @admin_only
    async def _cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
        uid, token = await _rp_cmd_guard(update, ctx, f"Cú pháp: <code>/{cmd} ID [kỳ]</code> — {desc}" + RP_USAGE_TAIL)
        if uid is None:
            return
        text, kb = await _rp_render_view(ctx.bot, uid, kind, token, 0)
        await update.effective_message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    return _cmd

lsuser_cmd = _rp_make_view_cmd("his", "lsuser", "biến động số dư đầy đủ")
lsnap_cmd = _rp_make_view_cmd("nap", "lsnap", "lịch sử nạp")
lsrut_cmd = _rp_make_view_cmd("rut", "lsrut", "lịch sử rút")
lscuoc_cmd = _rp_make_view_cmd("cuoc", "lscuoc", "lịch sử cược & thắng")
lscode_cmd = _rp_make_view_cmd("code", "lscode", "code đã nhập")
lsgift_cmd = _rp_make_view_cmd("gift", "lsgift", "giftcode đã dùng / được cấp")
lsmua_cmd = _rp_make_view_cmd("mua", "lsmua", "giftcode đã mua")

@admin_only
async def tongket_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid, token = await _rp_cmd_guard(update, ctx, "Cú pháp: <code>/tongket ID [kỳ]</code> — tổng kết nạp/rút/cược theo kỳ" + RP_USAGE_TAIL)
    if uid is None:
        return
    text, kb = await _rp_render_summary(ctx.bot, uid, token)
    await update.effective_message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

@admin_only
async def xuatls_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid, token = await _rp_cmd_guard(update, ctx, "Cú pháp: <code>/xuatls ID [kỳ]</code> — xuất FULL Excel nhiều sheet" + RP_USAGE_TAIL)
    if uid is None:
        return
    await _rp_export(update.effective_message, ctx.bot, uid, "all", token)

@admin_only
async def resetbank_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        uid = int(ctx.args[0])
    except (IndexError, ValueError):
        return await update.effective_message.reply_text("Cú pháp: /resetbank ID\nLệnh này gỡ thông tin ngân hàng đã liên kết, không xóa số dư.")
    if not (query("SELECT 1 FROM users WHERE user_id=%s", (uid,)) or []):
        return await update.effective_message.reply_text("Không tìm thấy người dùng.")
    query("UPDATE users SET bank=NULL, stk=NULL, name=NULL, bank_linked=0 WHERE user_id=%s", (uid,))
    await update.effective_message.reply_text(f"✅ Đã gỡ liên kết ngân hàng của ID {uid}. Số dư và lịch sử giao dịch được giữ nguyên. Người dùng có thể liên kết lại bằng /lienket.")
    try:
        await ctx.bot.send_message(uid, "🔄 Admin đã đặt lại liên kết ngân hàng của bạn. Bạn có thể liên kết lại bằng /lienket [Ngân_hàng] [STK] [Chủ_TK].")
    except Exception:
        pass

async def _telegram_name(bot, uid, cache=None):
    if not uid:
        return ""
    if cache is not None and uid in cache:
        return cache[uid]
    result = ""
    try:
        chat = await bot.get_chat(int(uid))
        username = getattr(chat, "username", None)
        full_name = getattr(chat, "full_name", None) or getattr(chat, "first_name", None)
        result = ("@" + username) if username else (full_name or "")
    except Exception:
        result = ""
    if cache is not None:
        cache[uid] = result
    return result

# ------------------------------------------------------------
# CALLBACK NÚT BẤM + NHẬP NGÀY
# ------------------------------------------------------------
async def _rp_edit(q, text, kb):
    try:
        await q.message.edit_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception as e:
        if "not modified" in str(e).lower():
            return
        raise

async def admin_report_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id not in ADMIN_IDS or is_admin_banned(q.from_user.id):
        return await q.answer("Bạn không có quyền.", show_alert=True)
    parts = (q.data or "").split(":")
    if len(parts) < 6:
        return await q.answer()
    _, uid_s, act, kind, token, extra = parts[:6]
    try:
        uid = int(uid_s)
    except ValueError:
        return await q.answer()
    try:
        if act == "noop":
            return await q.answer()
        if act == "home":
            text, kb = await _rp_render_card(ctx.bot, uid)
            if not text:
                return await q.answer("Không tìm thấy người dùng.", show_alert=True)
            await q.answer()
            return await _rp_edit(q, text, kb)
        if act == "pick":
            await q.answer()
            text, kb = _rp_picker(uid, kind, extra if extra in ("x", "v") else "x")
            return await _rp_edit(q, text, kb)
        if act == "view":
            await q.answer()
            if kind == "all":
                text, kb = await _rp_render_summary(ctx.bot, uid, token)
            else:
                text, kb = await _rp_render_view(ctx.bot, uid, kind, token, int(extra or 0))
            return await _rp_edit(q, text, kb)
        if act == "xls":
            await q.answer("⏳ Đang tạo file…")
            return await _rp_export(q.message, ctx.bot, uid, kind, token)
        if act == "ask":
            await q.answer()
            sent = await q.message.reply_text(
                f'<a href="tg://user?id={q.from_user.id}">Admin</a> ✍️ Nhập <b>ngày hoặc khoảng ngày</b> cần xem cho ID <code>{uid}</code>:\n'
                f'• <code>29/10/2026</code> — một ngày\n• <code>01/10/2026 - 29/10/2026</code> — khoảng ngày\n'
                f'• <code>10</code> — 10 ngày gần nhất · <code>all</code> — tất cả\n'
                f'<i>Reply tin nhắn này (hoặc gửi /huy để hủy).</i>',
                parse_mode=ParseMode.HTML,
                reply_markup=ForceReply(selective=True, input_field_placeholder="DD/MM/YYYY hoặc DD/MM - DD/MM"))
            ctx.user_data["rp_wait"] = {"uid": uid, "kind": kind, "mode": extra if extra in ("x", "v") else "x",
                                        "ts": get_vietnam_time().timestamp(), "prompt_id": sent.message_id}
            return
        if act in ("ban", "unban"):
            if act == "ban":
                if uid in ADMIN_IDS:
                    return await q.answer("Không thể khóa admin.", show_alert=True)
                query("INSERT INTO banned(user_id) VALUES(%s) ON CONFLICT DO NOTHING", (uid,))
                await q.answer("Đã khóa tài khoản.", show_alert=True)
            else:
                query("DELETE FROM banned WHERE user_id=%s", (uid,))
                await q.answer("Đã mở khóa tài khoản.", show_alert=True)
            text, kb = await _rp_render_card(ctx.bot, uid)
            if text:
                await _rp_edit(q, text, kb)
            return
        await q.answer()
    except Exception as e:
        traceback.print_exc()
        try:
            await q.answer()
        except Exception:
            pass
        try:
            await q.message.reply_text(f"❌ Lỗi khi xử lý nút: {html.escape(str(e))[:300]}", parse_mode=ParseMode.HTML)
        except Exception:
            pass

async def legacy_report_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("Menu cũ đã hết hạn. Hãy gõ lại /fulluser ID để dùng giao diện mới.", show_alert=True)

async def huy_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if ctx.user_data.pop("rp_wait", None):
        await update.effective_message.reply_text("✅ Đã hủy chọn ngày.")

async def report_date_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    wait = ctx.user_data.get("rp_wait")
    msg = update.effective_message
    user = update.effective_user
    if not wait or not msg or not msg.text or not user or user.id not in ADMIN_IDS:
        return
    if get_vietnam_time().timestamp() - wait.get("ts", 0) > 600:
        ctx.user_data.pop("rp_wait", None)
        return
    is_private = update.effective_chat and update.effective_chat.type == "private"
    is_reply = bool(msg.reply_to_message and msg.reply_to_message.message_id == wait.get("prompt_id"))
    if not (is_private or is_reply):
        return
    text = msg.text.strip()
    if text.lower() in ("huy", "hủy", "cancel"):
        ctx.user_data.pop("rp_wait", None)
        await msg.reply_text("✅ Đã hủy chọn ngày.")
        raise ApplicationHandlerStop
    token = _rp_token_from_text(text)
    if token is None:
        await msg.reply_text("❌ Không hiểu định dạng. Ví dụ: <code>29/10/2026</code>, <code>01/10 - 29/10</code>, <code>7</code> hoặc <code>all</code>.", parse_mode=ParseMode.HTML)
        raise ApplicationHandlerStop
    ctx.user_data.pop("rp_wait", None)
    uid, kind, mode = int(wait["uid"]), wait["kind"], wait.get("mode", "x")
    try:
        if mode == "x":
            await _rp_export(msg, ctx.bot, uid, kind, token)
        elif kind == "all":
            t, kb = await _rp_render_summary(ctx.bot, uid, token)
            await msg.reply_text(t, reply_markup=kb, parse_mode=ParseMode.HTML)
        else:
            t, kb = await _rp_render_view(ctx.bot, uid, kind, token, 0)
            await msg.reply_text(t, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception as e:
        traceback.print_exc()
        await msg.reply_text(f"❌ Lỗi: {html.escape(str(e))[:300]}", parse_mode=ParseMode.HTML)
    raise ApplicationHandlerStop

async def _on_error(update, context):
    """Không để lỗi bị nuốt im lặng: in log và báo cho admin nếu lỗi đến từ thao tác của admin."""
    print(f"❌ Lỗi handler: {context.error}")
    try:
        traceback.print_exception(type(context.error), context.error, context.error.__traceback__)
    except Exception:
        pass
    try:
        if isinstance(update, Update) and update.effective_user and update.effective_user.id in ADMIN_IDS and update.effective_message:
            await update.effective_message.reply_text(f"⚠️ Lỗi nội bộ: {html.escape(str(context.error))[:300]}", parse_mode=ParseMode.HTML)
    except Exception:
        pass


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
application.add_handler(CommandHandler("kmgio", kmgio_cmd))
application.add_handler(CommandHandler("homnay", homnay_cmd))
application.add_handler(CommandHandler("dskm", dskm_cmd))
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

application.add_handler(CommandHandler("admin", admin_help_cmd))
application.add_handler(CommandHandler("fulluser", fulluser_cmd))
application.add_handler(CommandHandler("lsuser", lsuser_cmd))
application.add_handler(CommandHandler("lsnap", lsnap_cmd))
application.add_handler(CommandHandler("lsrut", lsrut_cmd))
application.add_handler(CommandHandler("lscuoc", lscuoc_cmd))
application.add_handler(CommandHandler("lscode", lscode_cmd))
application.add_handler(CommandHandler("lsgift", lsgift_cmd))
application.add_handler(CommandHandler("lsmua", lsmua_cmd))
application.add_handler(CommandHandler("tongket", tongket_cmd))
application.add_handler(CommandHandler("xuatls", xuatls_cmd))
application.add_handler(CommandHandler("huy", huy_cmd))
application.add_handler(CommandHandler("resetbank", resetbank_cmd))
application.add_handler(CallbackQueryHandler(admin_report_callback, pattern=r"^ar:"))
application.add_handler(CallbackQueryHandler(legacy_report_callback, pattern=r"^(admreport_|admperiod_)"))
application.add_error_handler(_on_error)
application.add_handler(CommandHandler("baotrigame", baotrigame_cmd))
application.add_handler(CommandHandler("trangthai", trangthai_cmd))
application.add_handler(CommandHandler("user", user_cmd))
application.add_handler(CommandHandler("timuser", timuser_cmd))
application.add_handler(CommandHandler("camgame", camgame_cmd))
application.add_handler(CommandHandler("mogame", mogame_cmd))
application.add_handler(CommandHandler("camtn", camtn_cmd))
application.add_handler(CommandHandler("motn", motn_cmd))
application.add_handler(CommandHandler("dsban", dsban_cmd))
application.add_handler(CommandHandler("dsrut", dsrut_cmd))
application.add_handler(CommandHandler("dsnap", dsnap_cmd))
application.add_handler(CommandHandler("setsd", setsd_cmd))
application.add_handler(CommandHandler("top", top_cmd))
application.add_handler(CommandHandler("topnap", topnap_cmd))
application.add_handler(CommandHandler("topsodu", topsodu_cmd))
application.add_handler(CommandHandler("checktt", checktt_cmd))
application.add_handler(CommandHandler("help", interaction_help_cmd))
application.add_handler(CommandHandler("topcuoc", topcuoc_cmd))
application.add_handler(CallbackQueryHandler(admin_user_callback, pattern=r"^admuser_"))

application.add_handler(CallbackQueryHandler(handle_callback))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, report_date_input), group=-1)
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_group_message))

_bg_tasks = []

async def auto_settle_tich_luy_loop(bot):
    while True:
        try:
            # Chạy liên tục mỗi 60s để check và gửi code tích lũy ngay khi đạt mốc
            await auto_gen_tich_luy_codes()
        except Exception as e:
            print(f"Lỗi auto_settle_tich_luy_loop: {e}")
        await asyncio.sleep(60)

async def main():
    global _bot_instance
    await application.initialize()
    # Gợi ý lệnh khi người dùng gõ "/" trong nhóm; chỉ đưa các lệnh dùng cho thành viên.
    group_commands = [
        BotCommand("nap", "Nạp tiền"),
        BotCommand("rut", "Rút tiền"),
        BotCommand("top", "Top người chơi"),
        BotCommand("topnap", "Top nạp tiền"),
        BotCommand("topsodu", "Top số dư"),
        BotCommand("topcuoc", "Top cược"),
        BotCommand("checktt", "Kiểm tra tương tác hôm nay"),
        BotCommand("help", "Hướng dẫn sử dụng"),
        BotCommand("sd", "Xem số dư"),
        BotCommand("his", "Lịch sử giao dịch"),
    ]
    try:
        await application.bot.set_my_commands(group_commands, scope=BotCommandScopeAllGroupChats())
        await application.bot.set_my_commands(
            [BotCommand("start", "Mở menu bot"), *group_commands],
            scope=BotCommandScopeAllPrivateChats()
        )
    except Exception as e:
        print(f"Không thể cập nhật gợi ý lệnh Telegram: {e}")
    await application.start()
    _bot_instance = application.bot
    
    _bg_tasks.append(asyncio.create_task(reward_settle_loop(application.bot)))
    _bg_tasks.append(asyncio.create_task(auto_settle_tich_luy_loop(application.bot)))
    _bg_tasks.append(asyncio.create_task(settle_interaction_top_loop(application.bot)))
    _bg_tasks.append(asyncio.create_task(promo_golden_loop(application.bot)))
    
    # Khởi động webhook server
    await start_webhook_server()
    
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
