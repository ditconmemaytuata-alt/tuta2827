# ADMIN_PANEL_V3
import os
import re
import random
import asyncio
import collections
import hashlib
import csv
import traceback
import html
import json
import hmac
import time
from urllib.parse import urlencode, parse_qsl, urlparse
from datetime import datetime, timedelta
from io import BytesIO

import psycopg2
from psycopg2 import extras
import pytz
from telegram import (Bot, Update, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, InputMediaPhoto, WebAppInfo, ChatPermissions, BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats, ForceReply)
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters, CallbackQueryHandler, ApplicationHandlerStop
from telegram.constants import ParseMode
from telegram.error import RetryAfter
import aiohttp
from aiohttp import web

# ============================================================
# CẤU HÌNH CHUNG
# ============================================================
TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
SEPAY_API_KEY = os.getenv("SEPAY_API_KEY", "")  # Bắt buộc cấu hình bằng biến môi trường; không hardcode khóa bí mật

ADMIN_IDS = [5633649201, 7884394252]
BOT_USERNAME = "xoclo88dtbot"
SESSION_HISTORY_GROUP_ID = -1004464587619
SESSION_HISTORY_URL = "https://t.me/lsphienxoclo88"
ROOM_LINK = "https://t.me/hocviencbm"
MIN_WITHDRAW = 50000
MIN_DEPOSIT_FEATURES = 200000   # tổng nạp phải TRÊN mức này mới được mua giftcode / chuyển tiền
LOG_GROUP_ID = -1003663678808

# THÔNG TIN NGÂN HÀNG MỚI
BANK_ID = "970452"
ACCOUNT_NO = "101499100004641579"
ACCOUNT_NAME = "BAN TIEN PHONG"

_bot_instance = None
GROUP_IDS = [-1003663678808]

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
    "💵": "5409048419211682843", "🥰": "6318677150534734288", "🐺": "6309898817202295364", "💳": "5445353829304387411", "💰": "5278467510604160626", "🏦": "5332455502917949981", "🏆": "5188344996356448758",
    "⭐": "6114085614590629784", "🛍": "6201912473113596548", "📱": "6212898076038797235", "😍": "6221893124831057477", "🇻🇳": "6190651897792174993", "🆘": "6273945156341209192", "👍": "6282565984632970119", "🔔": "5440910346334255336", "🤭": "5440833702642857683", "🎁": "5253821918812862724", "🚗": "5442939099906325301", "🫐": "5420353563408741206", "🍭": "5442872991769707734", "🧤": "5255858639549251782", "🧦": "5422369251690298040", "🥛": "5255850496291259327", "🔴": "5255748374853863125", "💡": "5456145097844340698",
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

def btn_id(text, custom_emoji_id, callback_data=None, url=None):
    """Nút inline dùng custom emoji ID được cung cấp trực tiếp."""
    return InlineKeyboardButton(
        text, callback_data=callback_data, url=url,
        api_kwargs={"icon_custom_emoji_id": str(custom_emoji_id)}
    )

def kbtn_id(text, custom_emoji_id):
    """Nút bàn phím trả lời với icon emoji premium theo ID cụ thể."""
    return KeyboardButton(text, api_kwargs={"icon_custom_emoji_id": str(custom_emoji_id)})

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
    "🏀": "🏅", "⚽": "🏆", "🎳": "🔮",
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


def _top_medal(rank: int) -> str:
    return {1: "🥇", 2: "🥈", 3: "🥉"}.get(rank, "🏅")

def fmt_money(amount: int) -> str:
    return f"{amount:,}".replace(",", ".")

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

# ---- Connection pool: tái sử dụng kết nối, không bắt tay SSL mỗi truy vấn ----
from psycopg2 import pool as _pgpool
import threading as _threading
_DB_POOL = None
_DB_POOL_LOCK = _threading.Lock()
_DB_POOL_MAX = int(os.getenv("DB_POOL_MAX", "20"))

def _get_pool():
    global _DB_POOL
    if _DB_POOL is None:
        with _DB_POOL_LOCK:
            if _DB_POOL is None:
                _DB_POOL = _pgpool.ThreadedConnectionPool(
                    2, _DB_POOL_MAX, DATABASE_URL, sslmode='require',
                    keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=5)
    return _DB_POOL

def _pool_conn():
    """Lấy kết nối từ pool; nếu kết nối cũ đã chết thì bỏ và lấy cái khác."""
    pl = _get_pool()
    for _ in range(3):
        conn = pl.getconn()
        try:
            if conn.closed:
                raise psycopg2.OperationalError("closed")
            return conn
        except Exception:
            try:
                pl.putconn(conn, close=True)
            except Exception:
                pass
    return psycopg2.connect(DATABASE_URL, sslmode='require')

def _pool_release(conn):
    try:
        pl = _get_pool()
        if conn.closed:
            pl.putconn(conn, close=True)
        else:
            pl.putconn(conn)
    except Exception:
        try:
            conn.close()
        except Exception:
            pass

def query(q, args=()):
    res = None
    for attempt in (1, 2):
        conn = _pool_conn()
        cur = None
        try:
            cur = conn.cursor()
            cur.execute(q, args if args else None)
            if cur.description:
                res = cur.fetchall()
            conn.commit()
            break
        except (psycopg2.OperationalError, psycopg2.InterfaceError) as e:
            # kết nối chết giữa chừng -> bỏ kết nối, thử lại 1 lần với kết nối mới
            print(f"Database Error (conn): {e}")
            try:
                if cur: cur.close()
            except Exception:
                pass
            try:
                _get_pool().putconn(conn, close=True)
            except Exception:
                pass
            conn = None
            res = None
            if attempt == 2:
                break
            continue
        except Exception as e:
            print(f"Database Error: {e}")
            try:
                conn.rollback()
            except Exception:
                pass
            break
        finally:
            if conn is not None:
                try:
                    if cur: cur.close()
                except Exception:
                    pass
                _pool_release(conn)
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
query("""CREATE TABLE IF NOT EXISTS spam_permanent_bans (user_id BIGINT PRIMARY KEY, reason TEXT NOT NULL, banned_at TIMESTAMPTZ NOT NULL DEFAULT NOW())""")
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
    admin_note TEXT,
    request_code TEXT
)
""")
query("ALTER TABLE withdraw_history ADD COLUMN IF NOT EXISTS request_code TEXT")
query("ALTER TABLE withdraw_history ALTER COLUMN request_code TYPE TEXT USING request_code::TEXT")
for _c in ("method", "bank", "stk", "acc_name", "qr_file_id", "memo"):
    query(f"ALTER TABLE withdraw_history ADD COLUMN IF NOT EXISTS {_c} TEXT")
query("DROP INDEX IF EXISTS idx_withdraw_pending_request_code")
query("""
CREATE TABLE IF NOT EXISTS user_payout_accounts (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    method TEXT NOT NULL CHECK (method IN ('BANKING', 'MOMO', 'ZALOPAY')),
    bank_code TEXT,
    account_number TEXT NOT NULL,
    account_name TEXT NOT NULL,
    qr_file_id TEXT NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
""")
query("CREATE INDEX IF NOT EXISTS idx_user_payout_accounts_user ON user_payout_accounts(user_id)")

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
CREATE TABLE IF NOT EXISTS user_game_streaks (
    user_id BIGINT NOT NULL,
    group_id BIGINT NOT NULL,
    current_type TEXT NOT NULL DEFAULT '',
    current_count INTEGER NOT NULL DEFAULT 0,
    max_win INTEGER NOT NULL DEFAULT 0,
    max_loss INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT,
    PRIMARY KEY (user_id, group_id)
)
""")

query("""
CREATE TABLE IF NOT EXISTS daily_streaks (
    user_id BIGINT NOT NULL,
    group_id BIGINT NOT NULL,
    day TEXT NOT NULL,
    current_type TEXT NOT NULL DEFAULT '',
    current_count INTEGER NOT NULL DEFAULT 0,
    max_win INTEGER NOT NULL DEFAULT 0,
    max_loss INTEGER NOT NULL DEFAULT 0,
    win_at TEXT,
    loss_at TEXT,
    PRIMARY KEY (user_id, group_id, day)
)
""")
query("""
CREATE TABLE IF NOT EXISTS daily_streak_rewards (
    user_id BIGINT NOT NULL,
    group_id BIGINT NOT NULL,
    day TEXT NOT NULL,
    kind TEXT NOT NULL,
    rank INTEGER NOT NULL,
    streak INTEGER NOT NULL DEFAULT 0,
    reward_amount BIGINT NOT NULL DEFAULT 0,
    code TEXT,
    sent INTEGER NOT NULL DEFAULT 0,
    tries INTEGER NOT NULL DEFAULT 0,
    created_at TEXT,
    PRIMARY KEY (user_id, group_id, day, kind)
)
""")
query("""
CREATE TABLE IF NOT EXISTS daily_streak_settlements (
    group_id BIGINT NOT NULL,
    day TEXT NOT NULL,
    kind TEXT NOT NULL,
    settled_at TEXT,
    PRIMARY KEY (group_id, day, kind)
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

# Chương trình Fan +30K: điểm danh 7 ngày liên tiếp và chờ Admin duyệt
query("""
CREATE TABLE IF NOT EXISTS fan_checkins (
    user_id BIGINT NOT NULL,
    checkin_date DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY(user_id, checkin_date)
)
""")
query("""
CREATE TABLE IF NOT EXISTS fan_enrollments (
    user_id BIGINT PRIMARY KEY,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)
""")
query("""
CREATE TABLE IF NOT EXISTS fan_requests (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    streak_days INTEGER NOT NULL DEFAULT 7,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    reviewed_by TEXT,
    gift_code TEXT
)
""")
query("ALTER TABLE users ADD COLUMN IF NOT EXISTS total_bet BIGINT DEFAULT 0")
query("ALTER TABLE users ADD COLUMN IF NOT EXISTS rate_bonus INTEGER DEFAULT NULL")
query("ALTER TABLE users ADD COLUMN IF NOT EXISTS bank_linked INTEGER DEFAULT 0")
query("ALTER TABLE users ADD COLUMN IF NOT EXISTS tg_username TEXT")
query("ALTER TABLE users ADD COLUMN IF NOT EXISTS tg_full_name TEXT")
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
CREATE TABLE IF NOT EXISTS vip_level_reward_claims (
    user_id BIGINT NOT NULL,
    vip_level INTEGER NOT NULL,
    reward_amount BIGINT NOT NULL,
    claimed_at TEXT,
    PRIMARY KEY (user_id, vip_level)
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
query("ALTER TABLE giftcodes ADD COLUMN IF NOT EXISTS require_total_dep BIGINT DEFAULT 0")
query("CREATE UNIQUE INDEX IF NOT EXISTS uq_tichluy_user_milestone_day ON giftcodes(bound_user, milestone, claim_date) WHERE ctype='TICHLUY' AND bound_user IS NOT NULL AND milestone IS NOT NULL AND claim_date IS NOT NULL")
query("""CREATE TABLE IF NOT EXISTS tanthu_claims (user_id BIGINT PRIMARY KEY, code TEXT, claimed_at TEXT)""")

query("CREATE TABLE IF NOT EXISTS history (user_id BIGINT, amount BIGINT, note TEXT, time TEXT)")
query("ALTER TABLE history ADD COLUMN IF NOT EXISTS id SERIAL")
query("ALTER TABLE history ADD COLUMN IF NOT EXISTS bal_before BIGINT")
query("ALTER TABLE history ADD COLUMN IF NOT EXISTS bal_after BIGINT")
query("CREATE TABLE IF NOT EXISTS banned (user_id BIGINT PRIMARY KEY)")
query("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)")

def get_setting(key, default=None):
    res = query("SELECT value FROM settings WHERE key=%s", (key,))
    return res[0][0] if res else default

def set_setting(key, value):
    query("INSERT INTO settings(key, value) VALUES(%s, %s) "
          "ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value", (key, str(value)))

try:
    _session_counter_row = query("SELECT value FROM settings WHERE key='dice_session_counter'")
    if not _session_counter_row:
        query("INSERT INTO settings(key, value) VALUES('dice_session_counter', '0') ON CONFLICT (key) DO NOTHING")
except Exception as _counter_init_error:
    print(f"[session-counter] chưa khởi tạo được bộ đếm: {_counter_init_error}")

query("CREATE TABLE IF NOT EXISTS welcome_bonus_log (user_id BIGINT PRIMARY KEY, amount BIGINT DEFAULT 0, created_at TEXT)")
query("CREATE TABLE IF NOT EXISTS stats_bet_base (user_id BIGINT, day DATE, bet BIGINT DEFAULT 0, win BIGINT DEFAULT 0, PRIMARY KEY (user_id, day))")
# Mốc reset hoàn trả theo từng người (scope: ngay | tuan). Doanh số hoàn trả = bet_daily - mốc này.
query("CREATE TABLE IF NOT EXISTS reward_base (user_id BIGINT, day DATE, scope TEXT, bet BIGINT DEFAULT 0, win BIGINT DEFAULT 0, PRIMARY KEY (user_id, day, scope))")

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

def has_bank_linked(uid):
    """True nếu người dùng đã liên kết tài khoản nhận tiền (bank/ví). Admin luôn được qua."""
    if uid in ADMIN_IDS:
        return True
    try:
        r = query("SELECT 1 FROM user_payout_accounts WHERE user_id=%s LIMIT 1", (uid,))
        if r:
            return True
        r = query("SELECT bank, stk, bank_linked FROM users WHERE user_id=%s", (uid,))
        if r and r[0][0] and r[0][1] and (r[0][2] or 0):
            return True
    except Exception as e:
        print(f"has_bank_linked lỗi: {e}")
    return False

BANK_LINK_REQUIRED_MSG = (
    '🏦 <b>CHƯA LIÊN KẾT TÀI KHOẢN NGÂN HÀNG</b>\n\n'
    'Bạn cần liên kết tài khoản ngân hàng trước khi <b>chơi game</b> hoặc <b>nhập giftcode</b>.\n'
    '👉 Dùng lệnh <code>/lienket</code> để liên kết ngay.'
)

def is_banned(uid):
    res = query("SELECT 1 FROM banned WHERE user_id=%s", (uid,))
    return len(res) > 0 if res else False

_BAL_TRACE = {}   # uid -> (số dư TRƯỚC, số dư SAU) của lần cộng/trừ tiền gần nhất

def _bal_note(uid, before, after):
    if len(_BAL_TRACE) > 20000:
        _BAL_TRACE.clear()
    _BAL_TRACE[uid] = (int(before), int(after))

def add_money(uid, amt, note):
    get_user(uid)
    now_str = get_vietnam_datetime_db()
    _r = query("UPDATE users SET balance=balance+%s WHERE user_id=%s RETURNING balance", (amt, uid))
    if _r:
        _bal_note(uid, int(_r[0][0]) - int(amt), int(_r[0][0]))
    _t = _BAL_TRACE.get(uid) if _r else None
    query("INSERT INTO history(user_id, amount, note, time, bal_before, bal_after) VALUES(%s,%s,%s,%s,%s,%s)",
          (uid, amt, note, now_str, _t[0] if _t else None, _t[1] if _t else None))
    if amt > 0 and note.startswith(WIN_NOTE_PREFIXES):
        record_daily(uid, win=amt)

def sub_money(uid, amt, note="withdraw"):
    get_user(uid)
    bal = get_balance(uid)
    if bal < amt:
        return False
    now_str = get_vietnam_datetime_db()
    _r = query("UPDATE users SET balance=balance-%s WHERE user_id=%s RETURNING balance", (amt, uid))
    if _r:
        _bal_note(uid, int(_r[0][0]) + int(amt), int(_r[0][0]))
    _t = _BAL_TRACE.get(uid) if _r else None
    query("INSERT INTO history(user_id, amount, note, time, bal_before, bal_after) VALUES(%s,%s,%s,%s,%s,%s)",
          (uid, -amt, note, now_str, _t[0] if _t else None, _t[1] if _t else None))
    if (note != "Rút tiền" and note != "withdraw" and "Admin" not in note
            and "Chuyển tiền" not in note and not note.startswith("Mua giftcode")):
        query("UPDATE users SET total_bet=total_bet+%s WHERE user_id=%s", (amt, uid))
        record_daily(uid, bet=amt)
        update_bet_progress(uid, amt)
    return True

def bal_pre(uid):
    """Số dư TRƯỚC lần cộng/trừ gần nhất của uid (None nếu chưa có)."""
    t = _BAL_TRACE.get(uid)
    return t[0] if t else None

def bal_pair(before, uid):
    """Hai dòng 'Số dư trước / Số dư sau' (sau = số dư hiện tại)."""
    after = get_balance(uid)
    out = ""
    if before is not None:
        out += f'{ce("💳")} Số dư trước: <code>{fmt_money(before)}đ</code>\n'
    return out + f'{ce("💰")} Số dư sau: <code>{fmt_money(after)}đ</code>'

def bal_block(uid):
    """Hai dòng 'Số dư trước / Số dư sau' của lần cộng/trừ tiền gần nhất."""
    t = _BAL_TRACE.get(uid)
    if t:
        return (f'{ce("💳")} Số dư trước: <code>{fmt_money(t[0])}đ</code>\n'
                f'{ce("💰")} Số dư sau: <code>{fmt_money(t[1])}đ</code>')
    return f'{ce("💰")} Số dư hiện tại: <code>{fmt_money(get_balance(uid))}đ</code>'

def add_bonus_with_requirement(user_id, bonus_amount, required_multiplier=None):
    if required_multiplier is None:
        required_multiplier = PROMO_WAGER_MULT
    required_bet = int(round((get_balance(user_id) + bonus_amount) * required_multiplier))   # toàn bộ số dư + khuyến mãi
    now_str = get_vietnam_datetime_db()
    query("DELETE FROM user_bonus WHERE user_id=%s", (user_id,))
    query("INSERT INTO user_bonus (user_id, bonus_amount, required_bet, current_bet, created_at) VALUES (%s, %s, %s, %s, %s)",
          (user_id, bonus_amount, required_bet, 0, now_str))
    add_money(user_id, bonus_amount, f"Khuyến mãi nạp +{bonus_amount:,}đ (yêu cầu cược x{required_multiplier})")
    return required_bet

# ============================================================
# KHUYẾN MÃI NẠP
#  • 10% mỗi lần nạp, MỖI NGÀY CHỈ NHẬN 1 LẦN (đang có vòng cược khác vẫn nhận, cược được cộng dồn)
#  • +3% thưởng thêm cho MỖI lệnh nạp (không giới hạn số lần)
#  • GIỜ VÀNG tự động bật/tắt hằng ngày: 10:00-11:00 và 20:00-21:00 (giờ Việt Nam)
#  • Admin có thể ép bật/tắt bằng /kmgio on|off|auto
# ============================================================
PROMO_PCT = 10                              # % khuyến mãi nạp (1 lần/ngày)
try:
    PROMO_PCT = max(0, min(100, int(get_setting("promo_pct", PROMO_PCT) or PROMO_PCT)))
except (TypeError, ValueError):
    PROMO_PCT = 10
PROMO_ORDER_PCT = 3                         # % thưởng thêm cho mỗi lệnh nạp
PROMO_WAGER_MULT = 2.8                      # khuyến mãi (10%, admin tặng...) phải cược x2.8 vòng
PROMO_ORDER_WAGER_MULT = 1                  # thưởng 3% mỗi lệnh nạp chỉ cần cược x1 vòng
PROMO_GOLDEN_WINDOWS = ((10, 11), (20, 21)) # [giờ bắt đầu, giờ kết thúc) -> 10:00-11:00 và 20:00-21:00
PROMO_ALWAYS_ON = False                     # True = khuyến mãi 10% luôn mở cả ngày (không phụ thuộc giờ vàng)

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
    """Đánh dấu đã nhận 10% hôm nay. Trả về True nếu lần đầu trong ngày."""
    r = query("INSERT INTO promo_daily_claims (user_id, claim_date, amount) VALUES (%s,%s,%s) "
              "ON CONFLICT DO NOTHING RETURNING user_id", (uid, promo_today_key(), amount))
    return bool(r)

# --- Khuyến mãi sau nạp: chưa nhận mà đã phát sinh cược => coi như TỪ BỎ, không nhận lại được ---
query("""CREATE TABLE IF NOT EXISTS promo_offers (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    amount BIGINT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)""")
query("CREATE INDEX IF NOT EXISTS idx_promo_offers_user ON promo_offers(user_id, status)")

def promo_offer_create(uid, amount):
    """Ghi lời mời khuyến mãi (trạng thái pending). Trả về id, hoặc None nếu lỗi."""
    try:
        r = query("INSERT INTO promo_offers(user_id, amount) VALUES(%s,%s) RETURNING id", (uid, int(amount)))
        return int(r[0][0]) if r else None
    except Exception as e:
        print(f"[promo] không tạo được offer: {e}")
        return None

def promo_forfeit_pending(uid):
    """Gọi mỗi khi user phát sinh cược: mọi khuyến mãi nạp chưa nhận bị hủy vĩnh viễn."""
    try:
        query("UPDATE promo_offers SET status='forfeited' WHERE user_id=%s AND status='pending'", (uid,))
    except Exception as e:
        print(f"[promo] không hủy được offer của {uid}: {e}")

def promo_required(base_balance, bonus_main, bonus_order=0):
    """Yêu cầu cược = (TOÀN BỘ số dư + khuyến mãi) × số vòng. Hai loại thưởng (10% x2.8 / 3% x1) gộp theo tỉ lệ."""
    total = int(bonus_main) + int(bonus_order)
    if total <= 0:
        return 0
    mult = (bonus_main * PROMO_WAGER_MULT + bonus_order * PROMO_ORDER_WAGER_MULT) / total
    return int(round((max(0, int(base_balance or 0)) + total) * mult))

def add_promo_bonus(uid, bonus_main, bonus_order=0, note="Khuyến mãi nạp"):
    """Cộng thưởng + CỘNG DỒN yêu cầu cược vào vòng cược hiện có (nếu đang có).
    bonus_main: phần khuyến mãi phải cược x2.8; bonus_order: phần thưởng 3%/lệnh chỉ cược x1."""
    total = bonus_main + bonus_order
    _prev = get_balance(uid)
    required = promo_required(_prev, bonus_main, bonus_order)
    add_wager_requirement(uid, total, required, prev_balance=_prev)
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
    _bal_now = get_balance(uid)
    required = promo_required(_bal_now, p15, p3)
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
        lines.append(f'{ce("🎯")} <b>Cược {PROMO_PCT}%:</b> x{PROMO_WAGER_MULT} vòng')
    lines.append(f'{ce("🎯")} <b>Cược {PROMO_ORDER_PCT}%:</b> x{PROMO_ORDER_WAGER_MULT} vòng')
    lines.append(f'{ce("💳")} <b>Tính trên toàn bộ số dư + khuyến mãi:</b> <code>{fmt_money(_bal_now + total)}đ</code>')
    lines.append(f'{ce("📊")} <b>Tổng yêu cầu cược:</b> <code>{fmt_money(required)}đ</code>')
    lines.append(f'{ce("⚠️")} <b>Lưu ý:</b> Cược đủ yêu cầu mới được rút. '
                 f'Nếu đang có vòng cược khuyến mãi khác, yêu cầu cược sẽ được cộng dồn.')
    lines.append(f'{ce("❗️")} <b>Phải bấm nhận TRƯỚC khi chơi:</b> nếu bạn đã cược (chơi game) mà chưa nhận, '
                 f'khuyến mãi này coi như từ bỏ và <b>không được nhận lại</b>.')
    if not eligible15:
        if promo_claimed_today(uid):
            lines.append(f'{ce("📌")} <i>Hôm nay bạn đã nhận khuyến mãi {PROMO_PCT}% rồi (mỗi ngày 1 lần).</i>')
        else:
            lines.append(f'{ce("📌")} <i>Khuyến mãi {PROMO_PCT}% mở trong giờ vàng {promo_windows_text()} mỗi ngày.</i>')
    lines.append('━━━━━━━━━━━━━━━━━━━━━\n\nVui lòng chọn bên dưới:')
    _offer_id = promo_offer_create(uid, amount)
    _oid_suffix = f"_{_offer_id}" if _offer_id else ""
    kb = InlineKeyboardMarkup([[
        btn("NHẬN KHUYẾN MÃI", "🎁", callback_data=f"accept_promo_{uid}_{amount}_{1 if eligible15 else 0}{_oid_suffix}"),
        btn("TỪ CHỐI", "❌", callback_data=f"reject_bonus_{uid}{_oid_suffix}")
    ]])
    return "\n".join(lines), kb

def get_remaining_bet_required(user_id):
    bonus_data = query("SELECT required_bet, current_bet FROM user_bonus WHERE user_id=%s", (user_id,))
    if not bonus_data or bonus_data[0][0] == 0:
        return 0
    required_bet, current_bet = bonus_data[0]
    return max(0, required_bet - current_bet)

# ============================================================
# ADMIN_PANEL_V3 — TÂN THỦ +3.000đ & TỰ ĐỘNG XOÁ CƯỢC CŨ KHI NẠP/NHẬP CODE MỚI
# ============================================================
WELCOME_BONUS = 3000          # tiền tặng cho người dùng MỚI bấm /start lần đầu
WELCOME_WAGER_MULT = 3        # yêu cầu cược x3 (đặt 0 nếu muốn tặng KHÔNG cần cược)
WAGER_CLEAR_BALANCE = 5000    # số dư < mức này mà nạp đơn mới / nhập code mới => tự xoá vòng cược cũ

def grant_welcome_bonus(uid):
    """Tặng quà tân thủ đúng 1 lần cho mỗi tài khoản. Trả về số tiền đã tặng (0 nếu không tặng)."""
    try:
        ok = query(
            "INSERT INTO welcome_bonus_log (user_id, amount, created_at) VALUES (%s,%s,%s) "
            "ON CONFLICT DO NOTHING RETURNING user_id",
            (uid, WELCOME_BONUS, get_vietnam_datetime_db()))
    except Exception as e:
        print(f"grant_welcome_bonus lỗi: {e}")
        return 0
    if not ok:
        return 0
    add_money(uid, WELCOME_BONUS, f"Quà tân thủ +{WELCOME_BONUS:,}đ")
    if WELCOME_WAGER_MULT > 0:
        add_wager_requirement(uid, WELCOME_BONUS, int(get_balance(uid) * WELCOME_WAGER_MULT))   # số dư + quà tân thủ
    return WELCOME_BONUS

def auto_clear_old_wager(uid, prev_balance):
    """Nếu số dư TRƯỚC khi nạp/nhận code < 5.000đ mà còn vòng cược cũ -> xoá toàn bộ vòng cược cũ.
    Trả về số tiền cược còn thiếu đã bị xoá (0 nếu không xoá gì)."""
    try:
        if int(prev_balance or 0) >= WAGER_CLEAR_BALANCE:
            return 0
        remaining = get_remaining_bet_required(uid)
        if remaining <= 0:
            return 0
        query("DELETE FROM user_bonus WHERE user_id=%s", (uid,))
        return remaining
    except Exception as e:
        print(f"auto_clear_old_wager lỗi: {e}")
        return 0

DEPOSIT_DIRTY_WAGER_MULT = 5   # còn cược khuyến mãi cũ + số dư >= 5.000đ mà nạp mới => cược x5 tiền nạp mới được rút

DEPOSIT_BASE_WAGER_MULT = 1    # MỌI lệnh nạp thành công đều phải cược x1 tiền nạp mới được rút (kể cả không nhận khuyến mãi)

query("CREATE TABLE IF NOT EXISTS deposit_base_wager (user_id BIGINT PRIMARY KEY, amount BIGINT DEFAULT 0, base BIGINT DEFAULT 0)")

def _deposit_base_set(uid, amount, base):
    """Ghi nhớ phần cược x1 của lệnh nạp gần nhất (để khi nhận khuyến mãi không bị tính trùng tiền nạp)."""
    try:
        query("INSERT INTO deposit_base_wager (user_id, amount, base) VALUES (%s,%s,%s) "
              "ON CONFLICT (user_id) DO UPDATE SET amount=EXCLUDED.amount, base=EXCLUDED.base",
              (uid, int(amount), int(base)))
    except Exception as e:
        print(f"_deposit_base_set lỗi: {e}")

def deposit_base_release(uid, amount):
    """Gọi khi user nhận khuyến mãi của lệnh nạp `amount`: khuyến mãi đã tính cược trên TOÀN BỘ số dư
    (đã gồm tiền nạp) nên bỏ phần cược x1 tiền nạp đã cộng trước đó để không bị tính trùng."""
    try:
        r = query("DELETE FROM deposit_base_wager WHERE user_id=%s AND amount=%s RETURNING base", (uid, int(amount)))
        if r and int(r[0][0] or 0) > 0:
            query("UPDATE user_bonus SET required_bet=GREATEST(required_bet-%s,0) WHERE user_id=%s",
                  (int(r[0][0]), uid))
    except Exception as e:
        print(f"deposit_base_release lỗi: {e}")

def deposit_wager_line(uid):
    """Dòng thông báo yêu cầu cược còn lại để rút (rỗng nếu không còn yêu cầu)."""
    rem = get_remaining_bet_required(uid)
    if rem <= 0:
        return ""
    return (f'\n{ce("🎯")} Yêu cầu cược để rút: <code>{fmt_money(int(rem))}đ</code> '
            f'(x{DEPOSIT_BASE_WAGER_MULT} tiền nạp)')

def apply_deposit_wager_rule(uid, prev_balance, amount):
    # Gọi TRƯỚC khi cộng tiền nạp. Trả về (số_cược_cũ_đã_xoá, số_cược_x5_được_thêm).
    # Mọi lệnh nạp đều bị yêu cầu cược x1 tiền nạp (kể cả không nhận khuyến mãi).
    try:
        amount = int(amount)
        base = amount * DEPOSIT_BASE_WAGER_MULT
        remaining = get_remaining_bet_required(uid)
        if remaining <= 0:
            query("DELETE FROM user_bonus WHERE user_id=%s", (uid,))
            add_wager_requirement(uid, 0, base)
            _deposit_base_set(uid, amount, base)
            return 0, 0
        if int(prev_balance or 0) < WAGER_CLEAR_BALANCE:
            cleared = auto_clear_old_wager(uid, prev_balance)
            add_wager_requirement(uid, 0, base)
            _deposit_base_set(uid, amount, base)
            return cleared, 0
        extra = amount * DEPOSIT_DIRTY_WAGER_MULT
        add_wager_requirement(uid, 0, extra)
        return 0, extra
    except Exception as e:
        print(f"apply_deposit_wager_rule lỗi: {e}")
        return 0, 0

async def notify_deposit_wager(bot, uid, cleared, extra):
    if cleared:
        return await notify_wager_cleared(bot, uid, cleared)
    if not bot or not extra:
        return
    try:
        await bot.send_message(
            uid,
            f'{ce("⚠️")} <b>ĐƠN NẠP DÍNH CƯỢC KHUYẾN MÃI CŨ!</b>\n'
            f'━━━━━━━━━━━━━━━━━━━━━\n'
            f'{ce("💰")} Bạn nạp khi còn vòng cược khuyến mãi cũ và số dư từ <code>{fmt_money(WAGER_CLEAR_BALANCE)}đ</code> trở lên.\n'
            f'{ce("🎯")} Cần cược thêm <code>x{DEPOSIT_DIRTY_WAGER_MULT}</code> tiền nạp: <code>+{fmt_money(int(extra))}đ</code>\n'
            f'{ce("📊")} Tổng cược còn thiếu: <code>{fmt_money(get_remaining_bet_required(uid))}đ</code>\n'
            f'{ce("🔓")} Cược đủ mới được rút tiền.',
            parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"Không gửi được thông báo cược x5 cho {uid}: {e}")

async def notify_wager_cleared(bot, uid, remaining):
    if not bot or not remaining or remaining <= 0:
        return
    try:
        await bot.send_message(
            uid,
            f'{ce("🔓")} <b>ĐÃ XOÁ VÒNG CƯỢC CŨ!</b>\n'
            f'━━━━━━━━━━━━━━━━━━━━━\n'
            f'{ce("💰")} Số dư trước khi nạp dưới <code>{fmt_money(WAGER_CLEAR_BALANCE)}đ</code> '
            f'nên yêu cầu cược cũ (còn thiếu <code>{fmt_money(int(remaining))}đ</code>) đã được xoá tự động.\n'
            f'{ce("✅")} Đơn nạp mới của bạn được tính từ đầu, không bị dính cược cũ.',
            parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"Không gửi được thông báo xoá cược cho {uid}: {e}")


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
        f'{ce("🏦")} Ngân hàng: <b>BIDV</b>\n'
        f'{ce("👤")} CTK: <b>{ACCOUNT_NAME}</b>\n'
        f'{ce("💰")} STK: <code>{ACCOUNT_NO}</code>\n'
        f'{ce("✍️")} Nội dung: <code>{content}</code>\n'
        f'{ce("💰")} Số tiền: <code>{fmt_money(amount)}đ</code>\n'
        f'{ce("⏰")} Hiệu lực lệnh nạp: <b>{NAP_ORDER_TTL_MINUTES} phút</b>\n\n'
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
             "TPB": "970423", "STB": "970403", "VIB": "970441", "OCB": "970448",
             "MSB": "970426", "SHB": "970443", "LPB": "970449", "HDB": "970437",
             "AGRIBANK": "970405", "SCB": "970429", "EIB": "970431", "SEAB": "970440",
             "NAB": "970428", "BAB": "970409", "VAB": "970427", "ABB": "970425",
             "PVCB": "970412", "OCEANBANK": "970414", "CAKE": "546034", "TIMO": "963388"}

def _crc16_ccitt(text: str) -> str:
    crc = 0xFFFF
    for b in text.encode("ascii"):
        crc ^= b << 8
        for _ in range(8):
            crc = ((crc << 1) ^ 0x1021) & 0xFFFF if crc & 0x8000 else (crc << 1) & 0xFFFF
    return f"{crc:04X}"

def _tlv(tag: str, value: str) -> str:
    return f"{tag}{len(value):02d}{value}"

def build_vietqr_payload(amount: int, content: str, bank_id=None, account_no=None) -> str:
    b = str(bank_id or BANK_ID).upper()
    bin_ = b if b.isdigit() else _BANK_BIN.get(b)
    if not bin_:
        raise ValueError(f"Không có mã BIN cho ngân hàng {b}")
    content = re.sub(r"[^\x20-\x7E]", "", str(content or ""))
    acc = _tlv("00", bin_) + _tlv("01", str(account_no or ACCOUNT_NO))
    merchant = _tlv("00", "A000000727") + _tlv("01", acc) + _tlv("02", "QRIBFTTA")
    info = _tlv("08", content)
    body = (
        _tlv("00", "01") + _tlv("01", "12") + _tlv("38", merchant) +
        _tlv("53", "704") + _tlv("54", str(int(amount))) + _tlv("58", "VN") +
        _tlv("62", info) + "6304"
    )
    return body + _crc16_ccitt(body)

def make_local_qr(amount: int, content: str, bank_id=None, account_no=None) -> BytesIO:
    import qrcode
    qr = qrcode.QRCode(box_size=10, border=4)
    qr.add_data(build_vietqr_payload(amount, content, bank_id, account_no))
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

async def send_deposit_qr(bot, chat_id, qr_url, caption, kb, amount=0, content="", bank_id=None, account_no=None):
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
        return await bot.send_photo(photo=make_local_qr(amount, content, bank_id, account_no), **kw)
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
        [btn("10.000đ", "💵", "dep_10000"), btn("20.000đ", "💵", "dep_20000"), btn("30.000đ", "💵", "dep_30000")],
        [btn("50.000đ · NẠP NHANH", "👑", "dep_50000"), btn("100.000đ", "💵", "dep_100000"), btn("200.000đ", "💵", "dep_200000")],
        [btn("500.000đ", "💵", "dep_500000"), btn("1.000.000đ", "💰", "dep_1000000"), btn("2.000.000đ", "💰", "dep_2000000")],
        [btn("5.000.000đ", "💰", "dep_5000000"), btn("10.000.000đ", "💎", "dep_10000000"), btn("20.000.000đ", "💎", "dep_20000000")],
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
WIN_NOTE_PREFIXES = ("Thắng", "Nổ hũ", "Hoàn tiền Long Hổ", "Hoàn tiền Baccarat", "Hoàn tiền Game Telegram")

def record_daily(uid, bet=0, win=0):
    if bet and bet > 0:
        promo_forfeit_pending(uid)   # phát sinh cược => khuyến mãi nạp chưa nhận bị hủy
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
                     OR note LIKE 'Hoàn tiền Long Hổ%' OR note LIKE 'Hoàn tiền Baccarat%' OR note LIKE 'Hoàn tiền Game Telegram%')
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

def reward_stats(uid, d1, d2, scope):
    """Doanh số / tiền thắng dùng để tính hoàn trả = bet_daily trừ mốc admin đã reset (reward_base)."""
    res = query(
        "SELECT COALESCE(SUM(GREATEST(b.bet - COALESCE(r.bet,0),0)),0), "
        "COALESCE(SUM(GREATEST(b.win - COALESCE(r.win,0),0)),0) "
        "FROM bet_daily b LEFT JOIN reward_base r "
        "ON r.user_id=b.user_id AND r.day=b.day AND r.scope=%s "
        "WHERE b.user_id=%s AND b.day BETWEEN %s AND %s", (scope, uid, d1, d2))
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

VIP_LEVEL_REWARDS = {
    1: 10000, 2: 30000, 3: 100000, 4: 500000, 5: 1000000,
    6: 3000000, 7: 5000000, 8: 10000000, 9: 30000000,
}

def vip_reward_screen(uid):
    """Màn hình VIP gọn, đồng nhất trạng thái từng mốc và dễ đọc trên Telegram."""
    info = vip_info(uid)
    points, lvl = info["points"], info["lvl"]
    icon, name = VIP_LEVELS[lvl][1], VIP_LEVELS[lvl][2]

    lines = [
        f'{ce("👑")} <b>NHẬN THƯỞNG VIP</b>',
        '━━━━━━━━━━━━━━━━━━━━',
        f'{ce("🏅")} <b>Cấp hiện tại:</b> {ce(icon)} <b>{html.escape(name)}</b> · VIP {lvl}',
        f'{ce("💎")} <b>Điểm VIP:</b> <code>{fmt_money(points)}</code>',
        '',
        f'{ce("🎁")} <b>DANH SÁCH PHẦN THƯỞNG</b>',
        '━━━━━━━━━━━━━━━━━━━━',
    ]

    claimable = []
    for level in range(1, 10):
        threshold = VIP_LEVELS[level][3]
        reward = VIP_LEVEL_REWARDS[level]
        claimed = bool(query(
            "SELECT 1 FROM vip_level_reward_claims WHERE user_id=%s AND vip_level=%s",
            (uid, level)
        ))

        if points >= threshold and claimed:
            status = f'{ce("✅")} <b>ĐÃ NHẬN</b>'
        elif points >= threshold:
            status = f'{ce("🎉")} <b>CÓ THỂ NHẬN</b>'
            claimable.append(level)
        else:
            status = f'{ce("🔒")} Còn <b>{fmt_money(threshold - points)}</b> điểm'

        lines.append(
            f'{ce("🏅")} <b>VIP {level}</b>  ·  Thưởng: <b>{fmt_money(reward)}đ</b>\n'
            f'    {status}'
        )

    lines.extend([
        '━━━━━━━━━━━━━━━━━━━━',
        f'{ce("💡")} Đạt mốc VIP mới để mở khóa phần thưởng tương ứng.',
    ])

    kb = (
        InlineKeyboardMarkup([[
            btn("NHẬN TẤT CẢ THƯỞNG VIP", "🎁", callback_data="ev_vip_claim_all")
        ]])
        if claimable else None
    )
    return "\n".join(lines), kb

async def claim_vip_level_rewards(update, ctx):
    q = update.callback_query
    uid = q.from_user.id
    info = vip_info(uid)
    claimed_now, total_reward = [], 0
    for level in range(1, info["lvl"] + 1):
        reward = VIP_LEVEL_REWARDS[level]
        inserted = query(
            "INSERT INTO vip_level_reward_claims (user_id, vip_level, reward_amount, claimed_at) "
            "VALUES (%s,%s,%s,%s) ON CONFLICT (user_id, vip_level) DO NOTHING RETURNING vip_level",
            (uid, level, reward, get_vietnam_datetime_db())
        )
        if inserted:
            add_money(uid, reward, f"Nhận thưởng lên VIP {level} +{reward:,}đ")
            claimed_now.append((level, reward))
            total_reward += reward
    if not claimed_now:
        return await q.answer("Bạn chưa có mốc VIP mới để nhận thưởng!", show_alert=True)
    await q.answer("Nhận thưởng VIP thành công!")
    details = "\\n".join(
        f'{ce("🏅")} VIP {level}: <code>+{fmt_money(amount)}đ</code>'
        for level, amount in claimed_now
    )
    await q.message.reply_text(
        f'{ce("🎉")} <b>NHẬN THƯỞNG VIP THÀNH CÔNG!</b>\\n'
        f'━━━━━━━━━━━━━━━━━━━━━\\n{details}\\n'
        f'━━━━━━━━━━━━━━━━━━━━━\\n'
        f'{ce("💰")} Tổng nhận: <code>+{fmt_money(total_reward)}đ</code>\\n'
        f'{bal_block(uid)}',
        parse_mode=ParseMode.HTML
    )
    screen, kb = vip_reward_screen(uid)
    await q.message.reply_text(screen, reply_markup=kb, parse_mode=ParseMode.HTML)

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
        f'{bal_block(uid)}'
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
LOSS_TIERS_DAY = [(1_000_000_000, 11.8), (100_000_000, 7.8), (10_000_000, 5.8), (1_000_000, 3.8), (100_000, 1.8)]
LOSS_TIERS_WEEK = [(1_000_000_000, 4.8), (100_000_000, 2.8), (10_000_000, 2.3), (1_000_000, 1.8), (100_000, 0.8)]

RTYPE_LABEL = {
    "cuoc_ngay": ("HOÀN CƯỢC NGÀY", "🔥"),
    "cuoc_tuan": ("HOÀN CƯỢC TUẦN", "🚀"),
    "thua_ngay": ("HOÀN THUA NGÀY", "📉"),
    "thua_tuan": ("HOÀN THUA TUẦN", "🗓"),
}

def get_rebate_pct(kind):
    try:
        return float(get_setting(f"rebate_{kind}_pct", "1.8"))
    except (TypeError, ValueError):
        return 1.8

def _migrate_rebate_minus_02():
    # Chạy 1 lần: nếu admin từng đặt % bằng /sethoancuoc thì trừ thêm 0,2%.
    if get_setting("rebate_minus_02_done") == "1":
        return
    for _k in ("ngay", "tuan"):
        _v = get_setting(f"rebate_{_k}_pct")
        if _v is not None:
            try:
                set_setting(f"rebate_{_k}_pct", round(max(0.0, float(_v) - 0.2), 2))
            except ValueError:
                pass
    set_setting("rebate_minus_02_done", "1")

_migrate_rebate_minus_02()

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

# Cache trạng thái khóa nhận hoàn trả trong thời gian ngắn để hạn chế truy vấn DB
# khi người dùng liên tục bấm nút nhận thưởng đã bị khóa.
_REWARD_BAN_CACHE = {}
_REWARD_BAN_CACHE_TTL = 2.0

def reward_ban_status(uid):
    now_mono = time.monotonic()
    cached = _REWARD_BAN_CACHE.get(uid)
    if cached and now_mono - cached[0] < _REWARD_BAN_CACHE_TTL:
        return cached[1]
    rows = query(
        "SELECT feature FROM banned_features WHERE user_id=%s AND feature IN ('hoan_ngay','hoan_tuan')",
        (uid,)
    ) or []
    status = {str(row[0]) for row in rows}
    _REWARD_BAN_CACHE[uid] = (now_mono, status)
    return status

def reward_center(uid):
    now = get_vietnam_time()
    today = now.date()
    ws = week_start(today)
    we = ws + timedelta(days=6)
    d_bet, d_win = reward_stats(uid, today, today, "ngay")
    w_bet, w_win = reward_stats(uid, ws, we, "tuan")
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
    reward_bans = reward_ban_status(uid)
    if "hoan_ngay" in reward_bans:
        pending = [p for p in pending if not str(p[0]).endswith("_ngay")]
    if "hoan_tuan" in reward_bans:
        pending = [p for p in pending if not str(p[0]).endswith("_tuan")]
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

    # Kiểm tra khóa trước mọi thao tác nhận thưởng.
    bans = reward_ban_status(uid)
    fully_banned = {"hoan_ngay", "hoan_tuan"}.issubset(bans)
    if fully_banned:
        await safe_answer(q, f'{ce("🚫")} Bạn đã bị khóa nhận hoàn trả!', True)
        # Gỡ nút ở tin nhắn cũ để tránh tiếp tục bấm spam.
        try:
            await q.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        return

    blocked_types = []
    if "hoan_ngay" in bans:
        blocked_types.extend(["cuoc_ngay", "thua_ngay"])
    if "hoan_tuan" in bans:
        blocked_types.extend(["cuoc_tuan", "thua_tuan"])

    if blocked_types:
        rows = query(
            "UPDATE rewards SET claimed=1, claimed_at=%s WHERE user_id=%s AND claimed=0 AND amount>0 "
            "AND rtype <> ALL(%s) RETURNING rtype, period, amount",
            (get_vietnam_datetime_db(), uid, blocked_types))
    else:
        rows = query(
            "UPDATE rewards SET claimed=1, claimed_at=%s WHERE user_id=%s AND claimed=0 AND amount>0 "
            "RETURNING rtype, period, amount", (get_vietnam_datetime_db(), uid))

    if not rows:
        await safe_answer(q, "Hiện chưa có khoản thưởng nào được phép nhận hoặc đang chờ nhận!", True)
        try:
            await q.edit_message_reply_markup(reply_markup=None)
        except Exception:
            pass
        return

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
        f'{bal_block(uid)}'
    )
    try:
        await q.message.edit_text(text, parse_mode=ParseMode.HTML)
    except Exception:
        await q.message.reply_text(text, parse_mode=ParseMode.HTML)

def event_screen(uid, kind):
    today = get_vietnam_time().date()
    ws = week_start(today)
    is_day = kind.endswith("ngay")
    bet, win = reward_stats(uid, today, today, "ngay") if is_day else reward_stats(uid, ws, ws + timedelta(days=6), "tuan")
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

    rows = query("SELECT b.user_id, GREATEST(b.bet - COALESCE(r.bet,0),0), GREATEST(b.win - COALESCE(r.win,0),0) "
                 "FROM bet_daily b LEFT JOIN reward_base r ON r.user_id=b.user_id AND r.day=b.day AND r.scope='ngay' "
                 "WHERE b.day=%s", (day,)) or []
    for uid_, bet, win in rows:
        for rtype in ("cuoc_ngay", "thua_ngay"):
            base, amount = reward_calc(rtype, int(bet or 0), int(win or 0))
            _add(uid_, rtype, day.isoformat(), base, amount)

    if day.weekday() == 6:
        ws = week_start(day)
        wrows = query("SELECT b.user_id, SUM(GREATEST(b.bet - COALESCE(r.bet,0),0)), SUM(GREATEST(b.win - COALESCE(r.win,0),0)) "
                      "FROM bet_daily b LEFT JOIN reward_base r ON r.user_id=b.user_id AND r.day=b.day AND r.scope='tuan' "
                      "WHERE b.day BETWEEN %s AND %s GROUP BY b.user_id",
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
    "TANTHU":  {"name": "Code Tân Thủ",  "icon": "🎁", "fmt": "XOCLO88-TANTHU-xxxxxxx"},
    "CODEMUA": {"name": "Code Mua",      "icon": "🛒", "fmt": "XOCLO88-CODEMUA-xxxxxxx"},
    "GIOVANG": {"name": "Code Giờ Vàng", "icon": "⏰", "fmt": "XOCLO88-GIOVANG-xxxxxxx"},
    "NAP":     {"name": "Code Nạp",      "icon": "💳", "fmt": "XOCLO88-1234567-ABCDEFG"},
    "TRIAN":   {"name": "Code Tri Ân",   "icon": "🎉", "fmt": "XOCLO88-TRIAN-xxxxxxx"},
    "TICHLUY": {"name": "Code Tích Lũy", "icon": "🏆", "fmt": "XOCLO88-TICHLUY-xxxxxxx"},
    "INTERACT": {"name": "Code Tương Tác / CHECKTT", "icon": "💬", "fmt": "XOCLO88-INTERACT-xxxxxxx"},
    "TICHLUY": {"name": "Code TOP / Tích Lũy", "icon": "🏆", "fmt": "XOCLO88-TICHLUY-xxxxxxx"},
    "DAYTHANG": {"name": "Code Top Dây Thắng", "icon": "🔥", "fmt": "XOCLO88-DAYTHANG-xxxxxxx", "hidden": True},
    "DAYTHUA":  {"name": "Code Top Dây Thua",  "icon": "🥶", "fmt": "XOCLO88-DAYTHUA-xxxxxxx",  "hidden": True},
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
            code = f"XOCLO88-{_rand(_DIGITS, 7)}-{_rand(_LETTERS, 7)}"
        else:
            code = f"XOCLO88-{ctype}-{_rand(_ALNUM, 7)}"
        if not query("SELECT 1 FROM giftcodes WHERE code=%s", (code,)):
            return code

def add_wager_requirement(uid, bonus_amount, required_bet, prev_balance=None):
    cleared = 0
    if prev_balance is not None:
        cleared = auto_clear_old_wager(uid, prev_balance)
    ex = query("SELECT required_bet FROM user_bonus WHERE user_id=%s", (uid,))
    if ex and (ex[0][0] or 0) > 0:
        query("UPDATE user_bonus SET bonus_amount=bonus_amount+%s, required_bet=required_bet+%s WHERE user_id=%s",
              (bonus_amount, required_bet, uid))
    else:
        query("DELETE FROM user_bonus WHERE user_id=%s", (uid,))
        query("INSERT INTO user_bonus (user_id, bonus_amount, required_bet, current_bet, created_at) VALUES (%s,%s,%s,0,%s)",
              (uid, bonus_amount, required_bet, get_vietnam_datetime_db()))
    return cleared

async def redeem_giftcode(update: Update, uid: int, code_str: str) -> bool:
    msg = update.effective_message
    if query("SELECT 1 FROM admin_code_bans WHERE user_id=%s", (uid,)):
        await msg.reply_text("🚫 Tài khoản của bạn hiện không được phép nhập giftcode. Vui lòng liên hệ hỗ trợ.")
        return True
    if not has_bank_linked(uid):
        await msg.reply_text(BANK_LINK_REQUIRED_MSG, parse_mode=ParseMode.HTML)
        return True
    row = query("SELECT ctype, reward, wager, expiry, require_deposit, required_amount, bound_user, used, "
                "COALESCE(require_total_dep,0) FROM giftcodes WHERE code=%s", (code_str,))
    if not row:
        return False
    ctype, reward, wager, expiry, require_deposit, required_amount, bound_user, used, req_total_dep = row[0]
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

    if ctype == "TANTHU":
        _claimed_before = query("SELECT 1 FROM tanthu_claims WHERE user_id=%s", (uid,))
        _hist = query(
            "SELECT (SELECT COUNT(*) FROM deposit_history WHERE user_id=%s) + "
            "(SELECT COUNT(*) FROM withdraw_history WHERE user_id=%s)", (uid, uid))
        if _claimed_before:
            await msg.reply_text(
                f'{ce("🚫")} <b>Mỗi tài khoản chỉ được nhập Code Tân Thủ đúng 1 lần duy nhất.</b>',
                parse_mode=ParseMode.HTML)
            return True
        if _hist and int(_hist[0][0] or 0) > 0:
            await msg.reply_text(
                f'{ce("🚫")} <b>Code Tân Thủ</b> chỉ dành cho tài khoản <b>chưa có lịch sử nạp / rút</b>.',
                parse_mode=ParseMode.HTML)
            return True

    if req_total_dep and total_deposited(uid) < int(req_total_dep):
        _td = total_deposited(uid)
        await msg.reply_text(
            f'{ce("⚠️")} <b>CHƯA ĐỦ ĐIỀU KIỆN NHẬP CODE!</b>\n'
            f'━━━━━━━━━━━━━━━━━━━━━\n'
            f'{ce("🔑")} Mã: <code>{code_str}</code>\n'
            f'{ce("📈")} Cần tổng nạp từ: <code>{fmt_money(int(req_total_dep))}đ</code>\n'
            f'{ce("📥")} Tổng nạp của bạn: <code>{fmt_money(_td)}đ</code>\n'
            f'{ce("📌")} Còn thiếu: <code>{fmt_money(int(req_total_dep) - _td)}đ</code>',
            parse_mode=ParseMode.HTML)
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

    if ctype == "TANTHU":
        _tanthu_lock = query(
            "INSERT INTO tanthu_claims (user_id, code, claimed_at) VALUES (%s,%s,%s) "
            "ON CONFLICT (user_id) DO NOTHING RETURNING user_id",
            (uid, code_str, get_vietnam_datetime_db())
        )
        if not _tanthu_lock:
            await msg.reply_text(
                f'{ce("🚫")} <b>Mỗi tài khoản chỉ được nhập Code Tân Thủ đúng 1 lần duy nhất.</b>',
                parse_mode=ParseMode.HTML)
            return True

    claimed = query("UPDATE giftcodes SET used=1, used_by=%s, used_at=%s WHERE code=%s AND used=0 RETURNING code",
                    (uid, get_vietnam_datetime_db(), code_str))
    if not claimed:
        if ctype == "TANTHU":
            query("DELETE FROM tanthu_claims WHERE user_id=%s AND code=%s", (uid, code_str))
        await msg.reply_text(f'{ce("❌")} Mã này đã được sử dụng!', parse_mode=ParseMode.HTML)
        return True

    reward = int(reward)
    wager = int(wager or 0)
    prev_bal = get_balance(uid)
    add_money(uid, reward, f"Giftcode {gname}: {code_str}")
    required_bet = get_balance(uid) * wager      # toàn bộ số dư (đã gồm code) × vòng cược
    cleared_old = 0
    if required_bet > 0:
        cleared_old = add_wager_requirement(uid, reward, required_bet, prev_balance=prev_bal)
    success_text = (
        f'{ce("🎉")} <b>NHẬN CODE THÀNH CÔNG!</b> {ce("🎉")}\n'
        f'┏━━━━━━━━━━━━━━━━━━━━━━━━━\n'
        f'┃ {ce("🔑")} <b>Loại:</b> {gname}\n'
        f'┃ {ce("🔑")} <b>Mã code:</b> <code>{code_str}</code>\n'
        f'┃ {ce("💰")} <b>Đã nhận:</b> <code>+{fmt_money(reward)}đ</code>\n'
        f'┃ {ce("🎯")} <b>Vòng cược yêu cầu:</b> <code>x{wager}</code>\n'
        f'┃ {ce("📊")} <b>Tổng cược cần:</b> <code>{fmt_money(required_bet)}đ</code>\n'
        f'┗━━━━━━━━━━━━━━━━━━━━━━━━━\n\n'
        f'{bal_block(uid)}'
    )
    if cleared_old:
        success_text += (
            f'\n\n{ce("🔓")} <i>Số dư trước đó dưới {fmt_money(WAGER_CLEAR_BALANCE)}đ nên vòng cược cũ '
            f'(còn thiếu {fmt_money(int(cleared_old))}đ) đã được xoá tự động.</i>')
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
        f'{ce("⚠️")} Phí 5%. Mệnh giá mỗi code tối thiểu 1.000đ. Cần tổng nạp >200k.\n'
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
    if total_deposited(uid) <= MIN_DEPOSIT_FEATURES:
        return await msg_obj.reply_text(
            f'{ce("⚠️")} Bạn cần có tổng nạp trên <b>{fmt_money(MIN_DEPOSIT_FEATURES)}đ</b> mới được mua giftcode!\n'
            f'{ce("💳")} Tổng nạp hiện tại: <code>{fmt_money(total_deposited(uid))}đ</code>',
            parse_mode=ParseMode.HTML)

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
        f'{bal_block(uid)}',
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
        if t.get("hidden"):
            continue
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
    (50, 3333),
    (100, 6666),
    (200, 11111),
    (500, 15555),
    (1000, 22222),
    (2000, 25555),
    (3000, 33333),
    (4000, 37777),
    (5000, 55556),
    (6000, 88888),
]
TOP_INTERACTION_PRIZES = {1: 22222, 2: 18888, 3: 15000, 4: 13333,
                          5: 10000, 6: 10000, 7: 10000, 8: 10000, 9: 10000, 10: 10000}
# Chống spam: mỗi người, mỗi nhóm, trong 10 giây chỉ tính TỐI ĐA 1 tin hợp lệ.
# (gửi 2-4 tin liên tiếp trong 10 giây vẫn chỉ được cộng 1 tin)
INTERACTION_WINDOW_SECONDS = 10
# Cùng một nội dung gửi lặp lại trong khoảng này không được tính.
INTERACTION_DUP_SECONDS = 30
_interaction_seen = {}  # (user_id, chat_id) -> {"counted_at": datetime, "text": str}

def mask_user_id(user_id):
    """Chỉ hiển thị 5 chữ số cuối; mọi chữ số phía trước được thay bằng *."""
    raw = str(user_id or "")
    if len(raw) <= 5:
        return raw
    return ("*" * (len(raw) - 5)) + raw[-5:]

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

# Cột delivered: NULL = code cũ (coi như đã gửi), 0 = chưa gửi được, 1 = đã gửi riêng thành công.
query("ALTER TABLE interaction_reward_claims ADD COLUMN IF NOT EXISTS delivered INTEGER")

async def _deliver_interaction_code(bot, uid, milestone, reward, code):
    """Gửi code vào tin nhắn riêng. Trả về True nếu gửi được."""
    try:
        await bot.send_message(
            uid,
            f"🎁 <b>QUÀ TƯƠNG TÁC NHÓM</b>\n"
            f"Bạn đã đạt mốc <b>{milestone:,}</b> tin nhắn hợp lệ.\n"
            f"Mã giftcode: <code>{code}</code>\n"
            f"Giá trị: <b>{fmt_money(reward)}đ</b> · Vòng cược: <b>x7</b>\n"
            f"Nhập bằng lệnh <code>/code {code}</code> hoặc gửi thẳng mã cho bot.",
            parse_mode=ParseMode.HTML
        )
        return True
    except Exception as e:
        print(f"Không gửi được giftcode tương tác cho {uid}: {e}")
        return False

async def _send_interaction_code(bot, uid, group_id, milestone, reward, date_text, notify_group=True):
    """Tạo + gửi code cho 1 mốc. Trả về True nếu đã gửi riêng thành công."""
    code = gen_gift_code("TT")
    expiry = get_vietnam_time() + timedelta(hours=24)
    inserted = query(
        "INSERT INTO giftcodes (code, ctype, reward, wager, expiry, require_deposit, required_amount, "
        "bound_user, used, created_by, created_at) "
        "VALUES (%s,'INTERACT',%s,7,%s,0,0,%s,0,0,%s) ON CONFLICT DO NOTHING RETURNING code",
        (code, reward, expiry, uid, get_vietnam_datetime_db())
    )
    if not inserted:
        return False
    claim = query(
        "INSERT INTO interaction_reward_claims (user_id,group_id,date,milestone,code,reward_amount,created_at,delivered) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,0) ON CONFLICT DO NOTHING RETURNING milestone",
        (uid, group_id, date_text, milestone, code, reward, get_vietnam_datetime_db())
    )
    if not claim:
        query("DELETE FROM giftcodes WHERE code=%s AND used=0", (code,))
        return False
    ok = await _deliver_interaction_code(bot, uid, milestone, reward, code)
    if ok:
        query("UPDATE interaction_reward_claims SET delivered=1 WHERE user_id=%s AND group_id=%s AND date=%s AND milestone=%s",
              (uid, group_id, date_text, milestone))
    elif notify_group:
        try:
            await bot.send_message(
                group_id,
                f"🎁 Thành viên ID {mask_user_id(uid)} đã đạt mốc tương tác {milestone:,} tin. "
                f"Hãy mở bot riêng, nhắn /start rồi gõ /checktt để nhận giftcode (code không đăng trong nhóm)."
            )
        except Exception:
            pass
    return ok

async def _issue_interaction_rewards(bot, uid, group_id, count, date_text, notify_group=True):
    """Phát tất cả mốc đã đạt mà chưa nhận. Trả về list (mốc, tiền, đã_gửi_được)."""
    out = []
    for milestone, reward in INTERACTION_MILESTONES:
        if count < milestone:
            continue
        already = query(
            "SELECT 1 FROM interaction_reward_claims WHERE user_id=%s AND group_id=%s AND date=%s AND milestone=%s",
            (uid, group_id, date_text, milestone)
        )
        if already:
            continue
        ok = await _send_interaction_code(bot, uid, group_id, milestone, reward, date_text, notify_group)
        out.append((milestone, reward, ok))
    return out

async def _resend_undelivered(bot, uid, group_id, date_text):
    """Gửi lại các code đã tạo nhưng lần trước chưa nhắn riêng được. Trả về (gửi_được, vẫn_lỗi)."""
    rows = query(
        "SELECT c.milestone, c.code, c.reward_amount FROM interaction_reward_claims c "
        "JOIN giftcodes g ON g.code=c.code "
        "WHERE c.user_id=%s AND c.group_id=%s AND c.date=%s AND c.delivered=0 "
        "AND g.used=0 AND (g.expiry IS NULL OR g.expiry > NOW()) ORDER BY c.milestone",
        (uid, group_id, date_text)
    ) or []
    ok_n = fail_n = 0
    for milestone, code, reward in rows:
        if await _deliver_interaction_code(bot, uid, int(milestone), int(reward or 0), code):
            query("UPDATE interaction_reward_claims SET delivered=1 WHERE user_id=%s AND group_id=%s AND date=%s AND milestone=%s",
                  (uid, group_id, date_text, milestone))
            ok_n += 1
        else:
            fail_n += 1
    return ok_n, fail_n

async def track_interaction(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not msg or not user or not chat or chat.type == "private" or user.is_bot:
        return
    if GROUP_IDS and chat.id not in GROUP_IDS:
        return
    # Chỉ đếm tin nhắn văn bản tự nhiên; bỏ command, media-only, nội dung quá ngắn.
    # Room đang bị admin tắt (/tatroom) vẫn được tính tương tác bình thường.
    text_value = (msg.text or msg.caption or "").strip()
    if not text_value or text_value.startswith("/") or len(text_value) < 2:
        return
    normalized = re.sub(r"\s+", " ", text_value).casefold()
    now = get_vietnam_time()
    key = (user.id, chat.id)
    previous = _interaction_seen.get(key)
    if previous:
        gap = (now - previous["counted_at"]).total_seconds()
        # Trong 10 giây kể từ tin ĐÃ ĐƯỢC TÍNH gần nhất: bỏ qua mọi tin còn lại
        # (2, 3, 4... tin liên tiếp chỉ tính đúng 1 tin).
        if gap < INTERACTION_WINDOW_SECONDS:
            return
        # Lặp lại đúng nội dung của tin vừa được tính -> không tính.
        if normalized == previous["text"] and gap < INTERACTION_DUP_SECONDS:
            return
    _interaction_seen[key] = {"counted_at": now, "text": normalized}
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
    # Bộ đếm dài hạn của /checktt tự bắt đầu chu kỳ mới khi đủ 6.000 tin.
    cycle_row = query("SELECT interaction_count FROM group_interactions WHERE user_id=%s AND group_id=%s",
                      (uid, gid))
    cycle_count = int(cycle_row[0][0] or 0) if cycle_row else 0
    if cycle_count >= 6000:
        query("UPDATE group_interactions SET interaction_count=0 WHERE user_id=%s AND group_id=%s",
              (uid, gid))
    total = query(
        "SELECT interaction_count FROM daily_top_interactions WHERE user_id=%s AND group_id=%s AND date=%s",
        (uid, gid, today)
    )
    count = int(total[0][0] or 0) if total else 0
    await _issue_interaction_rewards(ctx.bot, uid, gid, count, today)


JACKPOT_RATE = 0.018   # 1,8% tiền thua của phiên được trích cộng vào hũ jackpot

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

async def _refund_round(bot, group_id, game_state, session_id):
    # Room bị tắt giữa phiên: hoàn toàn bộ tiền cược của phiên đang mở, không để mất tiền người chơi.
    for bet in list(game_state.get("bets", {}).values()):
        uid_, amt = bet["user_id"], int(bet["amount"])
        add_money(uid_, amt, f"Hoàn cược phiên #{session_id} (room tắt)")
        query("UPDATE users SET total_bet=GREATEST(total_bet-%s,0) WHERE user_id=%s", (amt, uid_))
        record_daily(uid_, bet=-amt)
        query("UPDATE user_bonus SET current_bet=GREATEST(current_bet-%s,0) WHERE user_id=%s", (amt, uid_))
        try:
            await bot.send_message(
                uid_,
                f'{ce("🚫")} <b>ROOM ĐÃ TẮT</b> — phiên #{session_id} bị hủy.\n'
                f'{ce("💰")} Đã hoàn lại <code>{fmt_money(amt)}đ</code> tiền cược vào số dư của bạn.\n'
                f'{bal_block(uid_)}',
                parse_mode=ParseMode.HTML)
        except Exception:
            pass
    game_state.get("bets", {}).clear()
    group_games.pop(group_id, None)


async def run_dice_game_cycle(bot, group_id: int, chat_id: int):
    while True:
        try:
            if not room_betting_enabled.get(group_id, True) or _is_room_muted(group_id):
                await asyncio.sleep(10)
                continue

            # Bộ đếm phiên lưu trong PostgreSQL để không quay về #1 khi sửa/redeploy bot.
            try:
                saved_counter = int(get_setting("dice_session_counter", "0") or 0)
            except (TypeError, ValueError):
                saved_counter = 0
            SESSION_COUNTER["value"] = max(int(SESSION_COUNTER.get("value", 0)), saved_counter) + 1
            session_id = SESSION_COUNTER["value"]
            set_setting("dice_session_counter", session_id)

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
                f'{ce("🔥")} T/X/C/L trả x1.97: thua tổng khi 3 XX 9/10/11/12 điểm\n'
                f'{ce("👅")} Tất tay: VD T MAX hoặc T ALL <i>(Lưu ý: MAX là tất tay)</i>\n'
                f'{ce("🎰")} D1 [mặt] x5: đoán viên đầu, VD D1 4 20k\n'
                f'{ce("🎰")} D2 [2 mặt] x10: đoán viên 1 và 2 đúng thứ tự, VD D2 46 20k\n'
                f'{ce("🎰")} D3 [tổng]: 9/10/11/12 x7; 8/13 x9; 7/14 x12; 6/15 x15; 5/16 x18; 4/17 x25; 3/18 x30, VD: D3 13 20000 hoặc D3 13 max\n'
                f'{ce("💎")} Xiên TC/TL/XC/XL trả x3, VD: TC 50000, XC 50000,\n\n'
                f'{ce("✅")} <b>VD tổng hợp:</b> T 50000, X 50000, XX MAX, TT MAX hoặc TC max\n\n'
                f'{ce("🎁")} Hũ jackpot: <code>{fmt_money(jackpot_now)}đ</code>'
            )

            try:
                await bot.send_message(
                    chat_id, start_text, parse_mode=ParseMode.HTML,
                    reply_markup=InlineKeyboardMarkup([[
                        btn("LỊCH SỬ PHIÊN", "📊", url=SESSION_HISTORY_URL)
                    ]])
                )
            except Exception as e:
                print(f"Lỗi gửi tin nhắn bắt đầu phiên: {e}")
                await asyncio.sleep(5)
                continue

            current_second = 60
            stats_msg_id = None
            aborted = False

            while current_second > 0:
                await asyncio.sleep(10)
                current_second -= 10
                if current_second < 0:
                    current_second = 0
                if _is_room_muted(group_id):
                    aborted = True
                    break

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
                        [
                            btn('NẠP TIỀN TẠI ĐÂY', '💰', url=f'https://t.me/{BOT_USERNAME}?start=nap'),
                            btn('BOT CHƠI GAME', '🎮', url=f'https://t.me/{BOT_USERNAME}')
                        ],
                        [
                            btn('CHƠI TÀI XỈU 3D NGAY', '🎮', url=f'https://t.me/{BOT_USERNAME}?start=tx3d'),
                            btn('LỊCH SỬ PHIÊN', '📊', url=SESSION_HISTORY_URL)
                        ]
                    ]))
                    stats_msg_id = new_stats_msg.message_id
                except Exception as e:
                    print(f"Lỗi gửi thống kê: {e}")

            if aborted or _is_room_muted(group_id):
                game_state["status"] = "closed"
                await _refund_round(bot, group_id, game_state, session_id)
                if stats_msg_id:
                    try:
                        await bot.delete_message(chat_id, stats_msg_id)
                    except Exception:
                        pass
                await asyncio.sleep(5)
                continue

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
            await asyncio.sleep(1)
            d2 = await bot.send_dice(chat_id, emoji="🎲")
            await asyncio.sleep(1)
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
            user_round_results = {}

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
                elif choice == "tai" and res_tx == "tai": is_win = True; multiplier = 1.97
                elif choice == "xiu" and res_tx == "xiu": is_win = True; multiplier = 1.97
                elif choice == "chan" and res_cl == "chan": is_win = True; multiplier = 1.97
                elif choice == "le" and res_cl == "le": is_win = True; multiplier = 1.97
                elif choice == "tl" and res_tx == "tai" and res_cl == "le": is_win = True; multiplier = 3
                elif choice == "tc" and res_tx == "tai" and res_cl == "chan": is_win = True; multiplier = 3
                elif choice == "xl" and res_tx == "xiu" and res_cl == "le": is_win = True; multiplier = 3
                elif choice == "xc" and res_tx == "xiu" and res_cl == "chan": is_win = True; multiplier = 3
                elif choice.startswith("a"):
                    target_triple = int(choice[1])
                    if dice_values == [target_triple, target_triple, target_triple]:
                        is_win = True; multiplier = 150

                user_round_results.setdefault(uid, []).append(bool(is_win))
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
                            f'{bal_block(uid)}\n'
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

            # Cập nhật chuỗi thắng/thua theo từng người chơi sau mỗi phiên.
            for streak_uid, outcomes in user_round_results.items():
                # Có ít nhất một cửa thắng trong phiên được tính là phiên thắng.
                round_type = "win" if any(outcomes) else "loss"
                try:
                    query(
                        """INSERT INTO user_game_streaks
                           (user_id, group_id, current_type, current_count, max_win, max_loss, updated_at)
                           VALUES (%s,%s,%s,1,%s,%s,%s)
                           ON CONFLICT (user_id, group_id) DO UPDATE SET
                             current_count = CASE
                               WHEN user_game_streaks.current_type = EXCLUDED.current_type
                               THEN user_game_streaks.current_count + 1 ELSE 1 END,
                             current_type = EXCLUDED.current_type,
                             max_win = GREATEST(user_game_streaks.max_win,
                               CASE WHEN EXCLUDED.current_type='win' THEN
                                 CASE WHEN user_game_streaks.current_type='win'
                                   THEN user_game_streaks.current_count + 1 ELSE 1 END
                               ELSE 0 END),
                             max_loss = GREATEST(user_game_streaks.max_loss,
                               CASE WHEN EXCLUDED.current_type='loss' THEN
                                 CASE WHEN user_game_streaks.current_type='loss'
                                   THEN user_game_streaks.current_count + 1 ELSE 1 END
                               ELSE 0 END),
                             updated_at = EXCLUDED.updated_at""",
                        (streak_uid, group_id, round_type,
                         1 if round_type == "win" else 0,
                         1 if round_type == "loss" else 0,
                         get_vietnam_datetime_db())
                    )
                except Exception as streak_error:
                    print(f"[streak] lỗi cập nhật user {streak_uid}: {streak_error}")
                try:
                    _record_daily_streak(streak_uid, group_id, round_type)
                except Exception as streak_error:
                    print(f"[daily_streak] lỗi cập nhật user {streak_uid}: {streak_error}")

            jackpot_amount = get_jackpot()
            jackpot_contribution = 0

            if total_lose > total_win:
                jackpot_contribution = int(total_lose * JACKPOT_RATE)   # trích 1,8% tiền thua vào hũ
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
                        _winner_rows = query("SELECT name FROM users WHERE user_id=%s", (w["user_id"],)) or []
                        _winner_name = html.escape(str(_winner_rows[0][0] or f'ID {w["user_id"]}')) if _winner_rows else f'ID {w["user_id"]}'
                        _masked_winner_id = ("*" * max(0, len(str(w["user_id"])) - 5)) + str(w["user_id"])[-5:]
                        jackpot_winners.append(
                            f'{ce("👤")} {_winner_name} · ID <code>{_masked_winner_id}</code>: '
                            f'<code>+{fmt_money(share)}đ</code>'
                        )
                    update_jackpot(100000)
                    jackpot_amount = 100000
            elif count_1 >= 3:
                winners = [b for b in game_state["bets"].values() if b["choice"] == "xiu"]
                if winners and jackpot_amount > 0:
                    total_bet_xiu = sum(w["amount"] for w in winners)
                    for w in winners:
                        share = int(jackpot_amount * (w["amount"] / total_bet_xiu))
                        add_money(w["user_id"], share, f"Nổ hũ Jackpot (3 con 1) +{share:,}đ")
                        _winner_rows = query("SELECT name FROM users WHERE user_id=%s", (w["user_id"],)) or []
                        _winner_name = html.escape(str(_winner_rows[0][0] or f'ID {w["user_id"]}')) if _winner_rows else f'ID {w["user_id"]}'
                        _masked_winner_id = ("*" * max(0, len(str(w["user_id"])) - 5)) + str(w["user_id"])[-5:]
                        jackpot_winners.append(
                            f'{ce("👤")} {_winner_name} · ID <code>{_masked_winner_id}</code>: '
                            f'<code>+{fmt_money(share)}đ</code>'
                        )
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
                f'┃ {ce("🎁")} Hũ hiện tại: {fmt_money(jackpot_amount)}đ'
                + (f' <b>(+{fmt_money(jackpot_contribution)}đ vào hũ)</b>' if jackpot_contribution > 0 and not jackpot_winners else '') +
                f'\n┗━━━━━━━━━━━━━\n'
                f'<b>Cầu gần đây:</b>\n'
                f'{cau_tx if cau_tx else "Chưa có"}\n'
                f'      🔵  Tài             🔴  XỈU\n'
                f'{cau_cl if cau_cl else "Chưa có"}\n'
                f'      ⚪️  Chẵn        ⚫️  Lẻ.'
            )

            try:
                await bot.set_chat_permissions(chat_id, FULL_PERMS)
            except Exception as e:
                print(f"Lỗi mở khóa chat: {e}")

            _result_post = await bot.send_message(
                chat_id, final_msg, parse_mode=ParseMode.HTML,
                reply_markup=InlineKeyboardMarkup([[
                    btn("LỊCH SỬ PHIÊN", "📊", url=SESSION_HISTORY_URL)
                ]])
            )
            if jackpot_winners:
                jackpot_notice = (
                    f'{ce("🎉")} <b>NỔ HŨ JACKPOT!</b> {ce("🎉")}\n'
                    f'┏━━━━━━━━━━━━━\n'
                    f'┃ {ce("💰")} Danh sách người trúng và tiền được chia:\n'
                    + "\n".join([f'┃ {w}' for w in jackpot_winners]) +
                    f'\n┗━━━━━━━━━━━━━\n'
                    f'{ce("🔄")} Hũ đã reset về 100.000đ'
                )
                try:
                    jackpot_post = await bot.send_message(chat_id, jackpot_notice, parse_mode=ParseMode.HTML)
                    await bot.pin_chat_message(chat_id=chat_id, message_id=jackpot_post.message_id,
                                               disable_notification=True)
                except Exception as _pin_error:
                    print(f"[jackpot] Không gửi/ghim được tin nổ hũ ở nhóm {chat_id}: {_pin_error}")
            # Gửi kết quả từng phiên sang nhóm lưu lịch sử.
            try:
                # Định dạng lịch sử gọn giống mẫu kênh: một dòng số phiên,
                # một dòng ba mặt xúc xắc + Tài/Xỉu, Chẵn/Lẻ và màu tương ứng.
                history_post = (
                    f'{ce("🎲")} <b>Kết quả phiên {session_id}</b> {ce("🎲")}\n'
                    f'<b>{dice_str}</b> 👉 <b>{html.escape(result_text)}</b> '
                    f'{result_icons}\n'
                    f'{ce("💯")} Tổng điểm: <b>{total}</b>'
                )
                # Nhóm lịch sử chỉ đăng nội dung kết quả, không gắn nút lịch sử phiên.
                await bot.send_message(
                    SESSION_HISTORY_GROUP_ID, history_post,
                    parse_mode=ParseMode.HTML
                )
            except Exception as history_error:
                print(f"[session-history] không gửi được phiên #{session_id}: {history_error}")
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
    if not has_bank_linked(user_id):
        return False, BANK_LINK_REQUIRED_MSG
    if not room_betting_enabled.get(group_id, True) or _is_room_muted(group_id):
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
    multiplier = 1.97
    if choice in ["tl", "tc", "xl", "xc"]: multiplier = 3
    elif choice.startswith("a"): multiplier = 150
    elif choice.startswith("d1"): multiplier = 5
    elif choice.startswith("d2"): multiplier = 10
    elif choice.startswith("d3"): multiplier = "7-30"

    msg = (
        f'{ce("✅")} Đặt thành công — Phiên #{session_id}\n\n'
        f'{ce("🥷")} Công khai\n'
        f'{ce("🎯")} {choice_display_map} · {fmt_money(game["bets"][bet_key]["amount"])}\n'
        f'{ce("💵")} Tỷ lệ x{multiplier}'
    )
    return True, msg

async def place_anonymous_bet(bot, user_id, group_id, choice, amount):
    if check_mt('mt_taixiu_room') and user_id not in ADMIN_IDS:
        return False, f'{ce("⚙️")} Game Tài Xỉu Room đang bảo trì!'
    if is_game_banned(user_id, 1):
        return False, f'{ce("🚫")} Bạn đã bị cấm chơi trò chơi này!'
    if not has_bank_linked(user_id):
        return False, BANK_LINK_REQUIRED_MSG
    if not room_betting_enabled.get(group_id, True) or _is_room_muted(group_id):
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
        f'{bal_block(user_id)}'
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
    _dm_bal = bal_block(user_id) if success else ""   # số dư chỉ gửi riêng, KHÔNG hiện công khai trong nhóm
    await reply_bet_notice(update.effective_message, message, success, private=(update.effective_chat.type == "private"))
    # Báo riêng về bot để người chơi nhận xác nhận kể cả khi nhóm bị trôi tin.
    if success:
        try:
            await send_bet_notice(ctx.bot, user_id, message + "\n" + _dm_bal)
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
    if not has_bank_linked(uid):
        return await update.effective_message.reply_text(BANK_LINK_REQUIRED_MSG, parse_mode=ParseMode.HTML)
    if check_mt('mt_xucxac_don') and uid not in ADMIN_IDS:
        return await update.effective_message.reply_text(f'{ce("⚙️")} Game Xúc Xắc Đơn đang bảo trì!', parse_mode=ParseMode.HTML)
    if amount < 1000:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền cược tối thiểu là 1.000đ!', parse_mode=ParseMode.HTML)
    if not sub_money(uid, amount, f"Cược Xúc Xắc Đơn {choice_code}"):
        return await update.effective_message.reply_text(f'{ce("❌")} Bạn không đủ số dư.', parse_mode=ParseMode.HTML)
    _bal0 = bal_pre(uid)

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
        f'{bal_pair(_bal0, uid)}',
        parse_mode=ParseMode.HTML)

async def play_longho(update, ctx, choice, amount):
    # Chuẩn hóa lựa chọn để tương thích callback/menu cũ và lệnh /lh.
    choice = str(choice or "").strip().lower()
    choice = {"dragon": "long", "rong": "long", "rồng": "long",
              "tiger": "ho", "ho": "ho", "hổ": "ho"}.get(choice, choice)
    uid = update.effective_user.id
    if is_game_banned(uid, 3):
        return await update.effective_message.reply_text(f'{ce("🚫")} Bạn đã bị cấm chơi trò chơi này!', parse_mode=ParseMode.HTML)
    if not has_bank_linked(uid):
        return await update.effective_message.reply_text(BANK_LINK_REQUIRED_MSG, parse_mode=ParseMode.HTML)
    if check_mt('mt_longho') and uid not in ADMIN_IDS:
        return await update.effective_message.reply_text(f'{ce("⚙️")} Game Long Hổ đang bảo trì!', parse_mode=ParseMode.HTML)
    if amount < 1000:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền cược tối thiểu là 1.000đ!', parse_mode=ParseMode.HTML)
    if not sub_money(uid, amount, f"Cược Long Hổ {choice.upper()}"):
        return await update.effective_message.reply_text(f'{ce("❌")} Bạn không đủ số dư.', parse_mode=ParseMode.HTML)
    _bal0 = bal_pre(uid)

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
                f'{bal_pair(_bal0, uid)}',
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
            f'{bal_pair(_bal0, uid)}',
            parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"Lỗi play_longho: {e}")
        try:
            await msg_status.edit_text(
                f'{ce("⚠️")} Có lỗi xảy ra, vui lòng thử lại!\n{bal_pair(_bal0, uid)}',
                parse_mode=ParseMode.HTML)
        except:
            pass

async def lh_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if len(ctx.args) < 2:
        return await update.effective_message.reply_text(
            f'{ce("❌")} Cú pháp: <code>/lh [long/ho] [số_tiền]</code>',
            parse_mode=ParseMode.HTML)
    choice = ctx.args[0].lower().strip()
    choice = {"dragon": "long", "rong": "long", "rồng": "long",
              "tiger": "ho", "hổ": "ho"}.get(choice, choice)
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
    if not has_bank_linked(uid):
        return await update.effective_message.reply_text(BANK_LINK_REQUIRED_MSG, parse_mode=ParseMode.HTML)
    if check_mt('mt_minipoker') and uid not in ADMIN_IDS:
        return await update.effective_message.reply_text(f'{ce("⚙️")} Game Mini Poker đang bảo trì!', parse_mode=ParseMode.HTML)
    if amount < 1000:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền cược tối thiểu là 1.000đ!', parse_mode=ParseMode.HTML)
    if not sub_money(uid, amount, f"Cược Mini Poker"):
        return await update.effective_message.reply_text(f'{ce("❌")} Bạn không đủ số dư.', parse_mode=ParseMode.HTML)
    _bal0 = bal_pre(uid)

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
        f'{bal_pair(_bal0, uid)}',
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
    if not has_bank_linked(uid):
        return await update.effective_message.reply_text(BANK_LINK_REQUIRED_MSG, parse_mode=ParseMode.HTML)
    if check_mt('mt_baccarat') and uid not in ADMIN_IDS:
        return await update.effective_message.reply_text(f'{ce("⚙️")} Game Baccarat đang bảo trì!', parse_mode=ParseMode.HTML)
    if amount < 1000:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền cược tối thiểu là 1.000đ!', parse_mode=ParseMode.HTML)
    if not sub_money(uid, amount, f"Cược Baccarat {choice.upper()}"):
        return await update.effective_message.reply_text(f'{ce("❌")} Bạn không đủ số dư.', parse_mode=ParseMode.HTML)
    _bal0 = bal_pre(uid)

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
        f'{bal_pair(_bal0, uid)}',
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
    if not has_bank_linked(uid):
        return await update.effective_message.reply_text(BANK_LINK_REQUIRED_MSG, parse_mode=ParseMode.HTML)
    if check_mt('mt_xocdia4') and uid not in ADMIN_IDS:
        return await update.effective_message.reply_text(f'{ce("⚙️")} Game Xóc Đĩa 4 Vị đang bảo trì!', parse_mode=ParseMode.HTML)
    if amount < 1000:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền cược tối thiểu là 1.000đ!', parse_mode=ParseMode.HTML)
    if not sub_money(uid, amount, f"Cược Xóc Đĩa 4 Vị {choice.upper()}"):
        return await update.effective_message.reply_text(f'{ce("❌")} Bạn không đủ số dư.', parse_mode=ParseMode.HTML)
    _bal0 = bal_pre(uid)

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
        f'{bal_pair(_bal0, uid)}',
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
    if not has_bank_linked(uid):
        return await update.effective_message.reply_text(BANK_LINK_REQUIRED_MSG, parse_mode=ParseMode.HTML)
    if check_mt('mt_taixiumd5') and uid not in ADMIN_IDS:
        return await update.effective_message.reply_text(f'{ce("⚙️")} Game Tài Xỉu MD5 đang bảo trì!', parse_mode=ParseMode.HTML)
    if amount < 1000:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền cược tối thiểu là 1.000đ!', parse_mode=ParseMode.HTML)
    if not sub_money(uid, amount, f"Cược Tài Xỉu MD5 {choice.upper()}"):
        return await update.effective_message.reply_text(f'{ce("❌")} Bạn không đủ số dư.', parse_mode=ParseMode.HTML)
    _bal0 = bal_pre(uid)

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
        f'{bal_pair(_bal0, uid)}',
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
    if not has_bank_linked(uid):
        return await update.effective_message.reply_text(BANK_LINK_REQUIRED_MSG, parse_mode=ParseMode.HTML)
    if check_mt('mt_baucua') and uid not in ADMIN_IDS:
        return await update.effective_message.reply_text(f'{ce("⚙️")} Game Bầu Cua đang bảo trì!', parse_mode=ParseMode.HTML)
    if amount < 1000:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền cược tối thiểu là 1.000đ!', parse_mode=ParseMode.HTML)
    if not sub_money(uid, amount, f"Cược Bầu Cua {choice.upper()}"):
        return await update.effective_message.reply_text(f'{ce("❌")} Bạn không đủ số dư.', parse_mode=ParseMode.HTML)
    _bal0 = bal_pre(uid)

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
        f'{bal_pair(_bal0, uid)}',
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
    if not has_bank_linked(uid):
        return await update.effective_message.reply_text(BANK_LINK_REQUIRED_MSG, parse_mode=ParseMode.HTML)
    if check_mt('mt_xocdia6') and uid not in ADMIN_IDS:
        return await update.effective_message.reply_text(f'{ce("⚙️")} Game Xóc Đĩa 6 Vị đang bảo trì!', parse_mode=ParseMode.HTML)
    if amount < 1000:
        return await update.effective_message.reply_text(f'{ce("❌")} Số tiền cược tối thiểu là 1.000đ!', parse_mode=ParseMode.HTML)
    if not sub_money(uid, amount, f"Cược Xóc Đĩa 6 Vị {choice.upper()}"):
        return await update.effective_message.reply_text(f'{ce("❌")} Bạn không đủ số dư.', parse_mode=ParseMode.HTML)
    _bal0 = bal_pre(uid)

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
        f'{bal_pair(_bal0, uid)}',
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
    if total_deposited(uid) <= MIN_DEPOSIT_FEATURES:
        return await msg_obj.reply_text(
            f'{ce("⚠️")} Bạn cần có tổng nạp trên <b>{fmt_money(MIN_DEPOSIT_FEATURES)}đ</b> mới được chuyển tiền!\n'
            f'{ce("💳")} Tổng nạp hiện tại: <code>{fmt_money(total_deposited(uid))}đ</code>',
            parse_mode=ParseMode.HTML)
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
                f'{bal_block(uid)}',
                parse_mode=ParseMode.HTML
            )
            try:
                await ctx.bot.send_message(target_id, f'{ce("💰")} Bạn vừa nhận được <code>{fmt_money(amount)}đ</code> từ ID <code>{uid}</code>.\n{bal_block(target_id)}', parse_mode=ParseMode.HTML)
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

FAN_PROMO_IMAGE = os.getenv("FAN_PROMO_IMAGE", "fan_xoclo88.jpg")
FAN_REF_URL = f"https://t.me/{BOT_USERNAME}?start={{uid}}"

def _fan_streak(uid):
    rows = query("SELECT checkin_date FROM fan_checkins WHERE user_id=%s ORDER BY checkin_date DESC LIMIT 7", (uid,)) or []
    if not rows:
        return 0
    dates = [r[0] for r in rows]
    today = get_vietnam_time().date()
    if dates[0] not in (today, today - timedelta(days=1)):
        return 0
    streak = 0
    expected = dates[0]
    for d in dates:
        if d == expected:
            streak += 1
            expected = expected - timedelta(days=1)
        else:
            break
    return streak

def _fan_profile_check(chat, has_photo, uid):
    display_name = " ".join(x for x in [getattr(chat, "first_name", ""), getattr(chat, "last_name", "")] if x).strip()
    bio = getattr(chat, "bio", "") or ""
    need_link = FAN_REF_URL.format(uid=uid)
    name_ok = "fan xoclo88" in display_name.casefold()
    bio_ok = need_link.casefold() in bio.casefold()
    return display_name, name_ok, bool(has_photo), bio_ok, need_link

def _fan_guide_text(uid, chat, has_photo):
    display, name_ok, photo_ok, bio_ok, ref_link = _fan_profile_check(chat, has_photo, uid)
    base_name = (display or "Tên của bạn").replace("Fan Xoclo88", "").strip() or "Tên của bạn"
    ok_all = name_ok and photo_ok and bio_ok
    head = ("✅ <b>BẠN ĐÃ ĐỦ ĐIỀU KIỆN, GỬI /baodanh ĐỂ ĐIỂM DANH!</b>" if ok_all
            else "❌ <b>BẠN CHƯA ĐẶT TÊN / ẢNH / TIỂU SỬ ĐÚNG YÊU CẦU ĐỂ NHẬN 30.000</b>")
    return (
        f"{head}\n\n"
        f"👤 Tên hiện tại: <b>{html.escape(display or '(chưa đặt)')}</b>\n"
        f"{'✅' if name_ok else '❌'} Tên {'đã' if name_ok else 'không'} chứa Fan Xoclo88\n"
        f"{'✅' if photo_ok else '❌'} Ảnh đại diện {'đã đúng yêu cầu' if photo_ok else 'chưa được đặt'}\n"
        f"{'✅' if bio_ok else '❌'} Tiểu sử {'đã' if bio_ok else 'không'} chứa link giới thiệu của XOCLO88\n\n"
        "✏️ Yêu cầu tên phải chứa cụm:\n<b>Fan Xoclo88</b>\n\n"
        f"✏️ Ví dụ tên hợp lệ:\n<code>{html.escape(base_name)} Fan Xoclo88</code>\n\n"
        "✏️ Set tiểu sử Telegram chứa link giới thiệu:\n"
        f"⭐ <code>{html.escape(ref_link)}</code>\n\n"
        "📅 Cần điểm danh đủ 7 ngày liên tiếp để nhận 30.000đ.\n"
        "📝 Sau khi đổi xong → gửi lại /baodanh để điểm danh!"
    )

async def _fan_send_guide(ctx, uid, msg):
    try:
        chat = await ctx.bot.get_chat(uid)
        photos = await ctx.bot.get_user_profile_photos(uid, limit=1)
        has_photo = bool(photos and photos.total_count > 0)
    except Exception:
        return await msg.reply_text("Bot chưa kiểm tra được hồ sơ Telegram. Bạn hãy thử lại sau.")
    text = _fan_guide_text(uid, chat, has_photo)
    path = FAN_PROMO_IMAGE if os.path.isabs(FAN_PROMO_IMAGE) else os.path.join(os.path.dirname(os.path.abspath(__file__)), FAN_PROMO_IMAGE)
    if os.path.exists(path):
        try:
            with open(path, "rb") as f:
                return await msg.reply_photo(photo=f, caption=text[:1024], parse_mode=ParseMode.HTML)
        except Exception as e:
            print("fan guide photo error:", e)
    return await msg.reply_text(text, parse_mode=ParseMode.HTML)

async def fan_baodanh(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    msg = update.effective_message
    if update.effective_chat.type != "private":
        return await msg.reply_text("Vui lòng điểm danh trong chat riêng với bot bằng /baodanh.")
    enrolled = query("SELECT 1 FROM fan_enrollments WHERE user_id=%s", (uid,))
    if not enrolled:
        return await msg.reply_text(
            "🌸 Bạn chưa tham gia chương trình Fan +30K.\n"
            "Hãy vào Tài khoản → Fan cứng +30k và bấm tham gia trước, "
            "sau đó gửi /baodanh mỗi ngày nhé."
        )
    _today0 = get_vietnam_time().date()
    if query("SELECT 1 FROM fan_checkins WHERE user_id=%s AND checkin_date=%s", (uid, _today0)):
        _st = _fan_streak(uid)
        return await msg.reply_text(f"✅ Bạn đã báo danh hôm nay rồi.\n📅 Chuỗi điểm danh: {_st}/7 ngày. Hãy quay lại vào ngày mai nhé!")
    try:
        chat = await ctx.bot.get_chat(uid)
        photos = await ctx.bot.get_user_profile_photos(uid, limit=1)
        has_photo = bool(photos and photos.total_count > 0)
    except Exception as e:
        return await msg.reply_text("Bot chưa kiểm tra được hồ sơ Telegram. Bạn hãy thử lại sau.")
    display, name_ok, photo_ok, bio_ok, ref_link = _fan_profile_check(chat, has_photo, uid)
    report = (
        "🌸 <b>FAN +30.000Đ · XOCLO88</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{'✅' if name_ok else '❌'} Tên hiển thị phải chứa: <b>Fan Xoclo88</b>\n"
        f"{'✅' if photo_ok else '❌'} Ảnh đại diện đã được đặt\n"
        f"{'✅' if bio_ok else '❌'} Tiểu sử có link giới thiệu cá nhân\n\n"
        f"👤 Tên hiện tại: <code>{html.escape(display or '(chưa đặt)')}</code>\n"
        f"🔗 Link cần thêm vào tiểu sử:\n<code>{html.escape(ref_link)}</code>\n\n"
    )
    if not (name_ok and photo_ok and bio_ok):
        return await msg.reply_text(report + "Hãy chỉnh đủ 3 điều kiện trên rồi gửi lại /baodanh.", parse_mode=ParseMode.HTML)
    today = get_vietnam_time().date()
    already = query("SELECT 1 FROM fan_checkins WHERE user_id=%s AND checkin_date=%s", (uid, today))
    reset_notice = ""
    if not already:
        latest = query("SELECT MAX(checkin_date) FROM fan_checkins WHERE user_id=%s", (uid,))
        last_date = latest[0][0] if latest else None
        # Bỏ lỡ ít nhất một ngày: xóa chuỗi cũ để lần báo danh hôm nay bắt đầu lại ngày 1.
        if last_date and last_date < today - timedelta(days=1):
            query("DELETE FROM fan_checkins WHERE user_id=%s", (uid,))
            reset_notice = "⚠️ Bạn đã bỏ lỡ ít nhất 1 ngày, chuỗi điểm danh đã được reset về ngày 1.\n"
        query("INSERT INTO fan_checkins(user_id,checkin_date) VALUES(%s,%s) ON CONFLICT DO NOTHING", (uid,today))
    streak = _fan_streak(uid)
    req = query("SELECT status,gift_code FROM fan_requests WHERE user_id=%s", (uid,))
    if req:
        status, gift = req[0]
        status_text = "đang chờ Admin duyệt" if status == "pending" else ("đã được duyệt" if status == "approved" else "đã bị từ chối")
        return await msg.reply_text(report + reset_notice + f"📅 Chuỗi điểm danh: <b>{streak}/7 ngày</b>\n📨 Yêu cầu Fan của bạn {status_text}." + (f"\n🎁 Giftcode: <code>{html.escape(gift)}</code>" if gift else ""), parse_mode=ParseMode.HTML)
    report += reset_notice + f"📅 Chuỗi điểm danh liên tiếp: <b>{streak}/7 ngày</b>\n"
    if streak >= 7:
        ins = query("INSERT INTO fan_requests(user_id,streak_days,status) VALUES(%s,7,'pending') ON CONFLICT(user_id) DO NOTHING RETURNING id", (uid,))
        if ins:
            for admin_id in ADMIN_IDS:
                try:
                    await ctx.bot.send_message(admin_id, f"🌸 <b>YÊU CẦU DUYỆT FAN +30K</b>\n👤 User ID: <code>{uid}</code>\n📅 Đã điểm danh đủ 7 ngày liên tiếp.\nVào Web Admin → Duyệt Fan để xử lý.", parse_mode=ParseMode.HTML)
                except Exception:
                    pass
        report += "🎉 Đã đủ 7 ngày! Yêu cầu của bạn đã được gửi Admin duyệt. Sau khi duyệt, bot sẽ gửi giftcode x3 vòng cược, hạn dùng 3 ngày."
    else:
        report += "➡️ Hãy quay lại gửi /baodanh mỗi ngày để đủ 7 ngày liên tiếp."
    return await msg.reply_text(report, parse_mode=ParseMode.HTML)

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
    _chk = query("SELECT 1 FROM users WHERE user_id=%s", (uid,))
    is_new_user = (_chk is not None and len(_chk) == 0)
    get_user(uid)
    if is_new_user:
        _given = grant_welcome_bonus(uid)
        if _given:
            _wg = (f'{ce("🎯")} Yêu cầu cược: <code>x{WELCOME_WAGER_MULT}</code> vòng (<code>{fmt_money(int(get_balance(uid) * WELCOME_WAGER_MULT))}đ</code>) mới được rút.\n'
                   if WELCOME_WAGER_MULT > 0 else '')
            await update.effective_message.reply_text(
                f'{ce("🎁")} <b>QUÀ TÂN THỦ DÀNH CHO BẠN!</b>\n'
                f'━━━━━━━━━━━━━━━━━━━━━\n'
                f'{ce("💰")} Bạn được tặng: <code>+{fmt_money(_given)}đ</code>\n'
                + _wg +
                f'{bal_block(uid)}\n'
                f'{ce("🎉")} Chúc bạn chơi vui vẻ và may mắn!',
                parse_mode=ParseMode.HTML)
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
    if ctx.args and ctx.args[0].lower() == "tx3d":
        _t, _k = tx3d_entry_view(uid, private=True, back=False)
        return await update.effective_message.reply_text(_t, reply_markup=_k, parse_mode=ParseMode.HTML)
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

    _menu_rows = [
        [kbtn_id("DANH SÁCH GAME", "5231005931550030290"), kbtn_id("TÀI KHOẢN", "6269196846657182682")],
        [kbtn_id("NẠP TIỀN", "5440833702642857683"), kbtn_id("RÚT TIỀN", "5472250091332993630")],
        [kbtn_id("GIỚI THIỆU", "5433758796289685818"), kbtn_id("ĐUA TOP", "5469744063815102906")],
        [kbtn_id("EVENT", "5375203677487248777")]
    ]
    if uid in ADMIN_IDS:
        _menu_rows.append([kbtn("ADMIN", "🛠")])   # nút chỉ hiện với admin
    menu = ReplyKeyboardMarkup(_menu_rows, resize_keyboard=True)

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

async def show_withdraw_methods(message):
    kb = InlineKeyboardMarkup([
        [btn_id("BANKING", "5332455502917949981", callback_data="payout:withdraw:BANKING")],
        [btn_id("MOMO", "5197161121106123533", callback_data="payout:withdraw:MOMO"),
         btn_id("ZALOPAY", "5445353829304387411", callback_data="payout:withdraw:ZALOPAY")]
    ])
    return await message.reply_text(
        f'{ce("💸")} <b>CHỌN PHƯƠNG THỨC RÚT TIỀN</b>\n\n'
        'Chọn nơi bạn muốn nhận tiền. Bạn có thể chọn phương thức khác với tài khoản đã liên kết trước đó.',
        reply_markup=kb, parse_mode=ParseMode.HTML
    )


async def lien_ket(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if is_banned(uid):
        return
    if is_total_maintenance() and uid not in ADMIN_IDS:
        return await update.effective_message.reply_text(
            f'{ce("⚡")} <b>HỆ THỐNG ĐANG BẢO TRÌ TOÀN BỘ</b>',
            parse_mode=ParseMode.HTML
        )
    ctx.user_data["payout_link"] = {"stage": "method"}
    kb = InlineKeyboardMarkup([
        [btn_id("BANKING", "5332455502917949981", callback_data="payout:method:BANKING")],
        [btn_id("MOMO", "5197161121106123533", callback_data="payout:method:MOMO"),
         btn_id("ZALOPAY", "5445353829304387411", callback_data="payout:method:ZALOPAY")],
        [btn("Hủy", "❌", callback_data="payout:cancel")]
    ])
    return await update.effective_message.reply_text(
        f'{ce("💳")} <b>LIÊN KẾT TÀI KHOẢN NHẬN TIỀN</b>\n\n'
        'Chọn phương thức nhận tiền. Ở bước cuối, bạn cần gửi ảnh QR tương ứng để Admin quét khi xử lý lệnh rút.',
        reply_markup=kb, parse_mode=ParseMode.HTML
    )


async def lien_ket_from_callback(q, ctx):
    kb = InlineKeyboardMarkup([
        [btn_id("BANKING", "5332455502917949981", callback_data="payout:method:BANKING")],
        [btn_id("MOMO", "5197161121106123533", callback_data="payout:method:MOMO"),
         btn_id("ZALOPAY", "5445353829304387411", callback_data="payout:method:ZALOPAY")],
        [btn("Hủy", "❌", callback_data="payout:cancel")]
    ])
    return await q.message.reply_text(
        "Bạn chưa có tài khoản cho phương thức này. Hãy liên kết tài khoản trước:",
        reply_markup=kb)


async def payout_link_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    uid = update.effective_user.id
    data = q.data or ""
    if data.startswith("payout:withdraw:"):
        method = data.rsplit(":", 1)[1]
        if method not in ("BANKING", "MOMO", "ZALOPAY"):
            return await q.answer("Phương thức không hợp lệ.", show_alert=True)
        channel_key = {"MOMO": "mt_rut_momo", "ZALOPAY": "mt_rut_zalopay", "BANKING": "mt_rut_banking"}[method]
        if check_mt(channel_key) and uid not in ADMIN_IDS:
            return await q.answer(f"Phương thức {method} đang bảo trì; các cổng khác vẫn hoạt động.", show_alert=True)
        rows = query(
            """SELECT id, bank_code, account_number, account_name
               FROM user_payout_accounts WHERE user_id=%s AND method=%s
               ORDER BY is_default DESC, id DESC""", (uid, method)
        ) or []
        if not rows:
            await q.answer("Bạn chưa liên kết phương thức này.", show_alert=True)
            ctx.user_data["payout_link"] = {"stage": "method"}
            return await lien_ket_from_callback(q, ctx)
        buttons = [[btn(f"{r[2]} • {r[3]}", "💳", callback_data=f"payout:use:{r[0]}")] for r in rows]
        await q.answer()
        return await q.message.reply_text(
            f"Chọn tài khoản {method} để nhận tiền:",
            reply_markup=InlineKeyboardMarkup(buttons))
    if data.startswith("payout:use:"):
        try:
            account_id = int(data.rsplit(":", 1)[1])
        except ValueError:
            return await q.answer("Tài khoản không hợp lệ.", show_alert=True)
        row = query("""SELECT id, method, bank_code, account_number, account_name
                       FROM user_payout_accounts WHERE id=%s AND user_id=%s""", (account_id, uid))
        if not row:
            return await q.answer("Không tìm thấy tài khoản.", show_alert=True)
        ctx.user_data["withdraw_payout_id"] = account_id
        await q.answer("Đã chọn tài khoản.")
        return await q.message.reply_text(
            f'{ce("✅")} Đã chọn {row[0][1]}: <code>{html.escape(str(row[0][3]))}</code>\\n'
            'Bây giờ nhập số tiền bằng lệnh <code>/rut 50000</code> hoặc <code>/rut all</code>.',
            parse_mode=ParseMode.HTML)
    if data == "payout:cancel":
        ctx.user_data.pop("payout_link", None)
        await q.answer("Đã hủy.")
        return await q.edit_message_text(f'{ce("❌")} Đã hủy liên kết tài khoản.', parse_mode=ParseMode.HTML)
    if data == "payout:close":
        await q.answer()
        return await q.edit_message_reply_markup(reply_markup=None)
    if data.startswith("payout:default:"):
        try:
            account_id = int(data.rsplit(":", 1)[1])
        except ValueError:
            return await q.answer("Tài khoản không hợp lệ.", show_alert=True)
        owned = query("SELECT id FROM user_payout_accounts WHERE id=%s AND user_id=%s", (account_id, uid))
        if not owned:
            return await q.answer("Không tìm thấy tài khoản.", show_alert=True)
        query("UPDATE user_payout_accounts SET is_default=FALSE WHERE user_id=%s", (uid,))
        query("UPDATE user_payout_accounts SET is_default=TRUE WHERE id=%s AND user_id=%s", (account_id, uid))
        await q.answer("Đã đặt tài khoản mặc định.")
        return await q.edit_message_text(f'{ce("✅")} Đã cập nhật tài khoản mặc định. Dùng /taikhoan để xem danh sách.', parse_mode=ParseMode.HTML)
    if not data.startswith("payout:method:"):
        return
    method = data.split(":")[-1]
    if method not in ("BANKING", "MOMO", "ZALOPAY"):
        return await q.answer("Phương thức không hợp lệ.", show_alert=True)
    ctx.user_data["payout_link"] = {"stage": "bank" if method == "BANKING" else "number", "method": method}
    await q.answer()
    prompt = "Nhập tên ngân hàng (VD: MB, BIDV, VCB):" if method == "BANKING" else f"Nhập số điện thoại {method}:"
    return await q.message.reply_text(f'{ce("📝")} {prompt}\n\nGửi /huy để hủy.', parse_mode=ParseMode.HTML)


async def payout_link_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    state = ctx.user_data.get("payout_link")
    msg = update.effective_message
    if not state or not msg or not msg.text or update.effective_chat.type != "private":
        return
    value = msg.text.strip()
    if value.lower() in ("/huy", "huy", "hủy", "cancel"):
        ctx.user_data.pop("payout_link", None)
        await msg.reply_text(f'{ce("❌")} Đã hủy liên kết.', parse_mode=ParseMode.HTML)
        raise ApplicationHandlerStop
    stage = state.get("stage")
    if stage == "bank":
        if len(value) > 40:
            await msg.reply_text("Tên ngân hàng quá dài, vui lòng nhập lại.")
            raise ApplicationHandlerStop
        state["bank_code"] = value.upper()
        state["stage"] = "number"
        await msg.reply_text("Nhập số tài khoản ngân hàng:")
        raise ApplicationHandlerStop
    if stage == "number":
        compact = re.sub(r"\s+", "", value)
        if not re.fullmatch(r"[0-9A-Za-z]{5,30}", compact):
            await msg.reply_text("Số tài khoản/số điện thoại không hợp lệ. Vui lòng nhập lại.")
            raise ApplicationHandlerStop
        state["account_number"] = compact
        state["stage"] = "name"
        await msg.reply_text("Nhập chính xác tên chủ tài khoản/chủ ví:")
        raise ApplicationHandlerStop
    if stage == "name":
        if len(value) < 2 or len(value) > 80:
            await msg.reply_text("Tên không hợp lệ, vui lòng nhập lại.")
            raise ApplicationHandlerStop
        state["account_name"] = value.upper()
        state["stage"] = "qr"
        await msg.reply_text(
            f'{ce("🖼")} <b>BƯỚC CUỐI: GỬI ẢNH QR</b>\n\n'
            'Gửi ảnh QR nhận tiền của đúng tài khoản vừa nhập (gửi dạng ẢNH, không gửi đường link). '
            'Bot sẽ lưu ảnh và gửi cho Admin cùng yêu cầu rút tiền.',
            parse_mode=ParseMode.HTML
        )
        raise ApplicationHandlerStop


async def payout_link_photo(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    state = ctx.user_data.get("payout_link")
    msg = update.effective_message
    if not state or state.get("stage") != "qr" or not msg or not msg.photo:
        return
    uid = update.effective_user.id
    photo = msg.photo[-1]
    method = state["method"]
    bank = state.get("bank_code")
    number = state["account_number"]
    name = state["account_name"]
    query("UPDATE user_payout_accounts SET is_default=FALSE WHERE user_id=%s", (uid,))
    saved_account = query(
        """INSERT INTO user_payout_accounts
           (user_id, method, bank_code, account_number, account_name, qr_file_id, is_default)
           VALUES (%s,%s,%s,%s,%s,%s,TRUE) RETURNING id""",
        (uid, method, bank, number, name, photo.file_id)
    )
    if not saved_account:
        await msg.reply_text("❌ Chưa lưu được tài khoản. Vui lòng thử lại hoặc liên hệ Admin.")
        return
    if method == "BANKING":
        query("UPDATE users SET bank=%s, stk=%s, name=%s, bank_linked=1 WHERE user_id=%s",
              (bank, number, name, uid))
    ctx.user_data.pop("payout_link", None)
    await msg.reply_text(
        f'{ce("✅")} <b>LIÊN KẾT TÀI KHOẢN THÀNH CÔNG</b>\n\n'
        f'{ce("💳")} Phương thức: <b>{method}</b>\n'
        f'{ce("🔢")} Số tài khoản/số điện thoại: <code>{html.escape(number)}</code>\n'
        f'{ce("👤")} Chủ tài khoản: <b>{html.escape(name)}</b>\n'
        f'{ce("🖼")} Đã lưu ảnh QR. Tài khoản này được đặt làm mặc định khi rút tiền.',
        parse_mode=ParseMode.HTML
    )


async def taikhoan_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    rows = query(
        """SELECT id, method, bank_code, account_number, account_name, is_default
           FROM user_payout_accounts WHERE user_id=%s ORDER BY id DESC""", (uid,)
    )
    if not rows:
        return await update.effective_message.reply_text(
            "Bạn chưa có tài khoản đã lưu. Dùng /lienket để thêm tài khoản kèm QR."
        )
    lines = [f'{ce("💳")} <b>TÀI KHOẢN NHẬN TIỀN ĐÃ LƯU</b>\n']
    buttons = []
    for row in rows:
        aid, method, bank, number, name, is_default = row
        default_text = " ⭐ MẶC ĐỊNH" if is_default else ""
        lines.append(
            f'• <b>{html.escape(str(method))}</b> {html.escape(str(bank or ""))}\n'
            f'  <code>{html.escape(str(number))}</code> — {html.escape(str(name))}{default_text}'
        )
        if not is_default:
            buttons.append([btn(f"Đặt mặc định #{aid}", "⭐", callback_data=f"payout:default:{aid}")])
    if buttons:
        buttons.append([btn("Đóng", "❌", callback_data="payout:close")])
    return await update.effective_message.reply_text(
        "\n\n".join(lines),
        reply_markup=InlineKeyboardMarkup(buttons) if buttons else None,
        parse_mode=ParseMode.HTML
    )


async def rut(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    msg_obj = update.effective_message
    args = ctx.args or []
    # /rut chỉ dùng trong chat riêng với bot, không dùng trong nhóm.
    _chat = update.effective_chat
    if _chat is not None and _chat.type != "private":
        return await msg_obj.reply_text(
            f'{ce("🚫")} Lệnh <b>/rut</b> chỉ dùng trong chat riêng với bot, không dùng trong nhóm.\n'
            f'{ce("👉")} Nhắn riêng cho bot: https://t.me/{BOT_USERNAME}',
            parse_mode=ParseMode.HTML)
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
    if not args:
        return await show_withdraw_methods(msg_obj)
    selected_id = ctx.user_data.get("withdraw_payout_id")
    if selected_id:
        payout = query(
            """SELECT method, bank_code, account_number, account_name, qr_file_id
               FROM user_payout_accounts WHERE user_id=%s AND id=%s""", (uid, selected_id)
        )
    else:
        payout = query(
            """SELECT method, bank_code, account_number, account_name, qr_file_id
               FROM user_payout_accounts WHERE user_id=%s
               ORDER BY is_default DESC, id DESC LIMIT 1""", (uid,)
        )
    legacy = query("SELECT bank, stk, name, balance FROM users WHERE user_id=%s", (uid,))
    if payout:
        method, bank, stk, name, payout_qr_file_id = payout[0]
        balance_value = legacy[0][3] if legacy else get_balance(uid)
        u = (bank or method, stk, name, balance_value)
    elif legacy and legacy[0][0] and legacy[0][1]:
        bank, stk, name, balance_value = legacy[0]
        method, payout_qr_file_id = "BANKING", None
        u = legacy[0]
    else:
        return await msg_obj.reply_text(
            f'{ce("❌")} Bạn chưa liên kết tài khoản nhận tiền.\n'
            f'Hãy dùng lệnh <code>/lienket</code> và gửi ảnh QR theo hướng dẫn.',
            parse_mode=ParseMode.HTML)

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
        ctx.user_data.pop("withdraw_payout_id", None)
        now_str = get_vietnam_datetime_db()
        # Mã yêu cầu rút: SHIN + 5 số bất kỳ (VD: SHIN48215), không trùng với các yêu cầu đang chờ duyệt.
        used_codes = {
            str(row[0]) for row in
            (query("SELECT request_code FROM withdraw_history WHERE status='pending' AND request_code IS NOT NULL") or [])
        }
        request_code = f"SHIN{random.randint(0, 99999):05d}"
        while request_code in used_codes:
            request_code = f"SHIN{random.randint(0, 99999):05d}"
        ins = query(
            "INSERT INTO withdraw_history (user_id, amount, status, time, request_code, method, bank, stk, acc_name, qr_file_id) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (uid, amount, 'pending', now_str, request_code, str(method), str(bank or ''),
             re.sub(r"\s+", "", str(stk or "")), str(name or ''), payout_qr_file_id)
        )
        withdraw_id = int(ins[0][0]) if ins else 0
        # Tạo mã nội dung chuyển khoản gồm 3 từ ngẫu nhiên, gắn với QR của người nhận tiền.
        memo_words = random.sample(["MAY", "LOC", "PHAT", "AN", "TAM", "KIM", "SONG", "VUI", "SEN", "LONG", "MINH", "THINH"], 3)
        transfer_memo = " ".join(memo_words)
        if withdraw_id:
            query("UPDATE withdraw_history SET memo=%s WHERE id=%s", (transfer_memo, withdraw_id))
        keyboard = InlineKeyboardMarkup([[
            btn("Duyệt", "✅", callback_data=f"ok_{uid}_{amount}"),
            btn("Từ chối", "❌", callback_data=f"no_{uid}_{amount}")
        ]])
        # VietQR nhận mã ngân hàng; chuẩn hóa một số tên thường gặp.
        bank_raw = str(bank or "").strip()
        bank_key = re.sub(r"[^A-Z0-9]", "", bank_raw.upper())
        bank_codes = {
            "MB": "MB", "MBBANK": "MB", "VIETCOMBANK": "VCB", "VCB": "VCB",
            "TECHCOMBANK": "TCB", "TCB": "TCB", "BIDV": "BIDV",
            "VIETINBANK": "CTG", "CTG": "CTG", "ACB": "ACB", "SACOMBANK": "STB",
            "STB": "STB", "VPBANK": "VPB", "VPB": "VPB", "TPBANK": "TPB",
            "TPB": "TPB", "AGRIBANK": "AGRIBANK", "VIB": "VIB", "SHB": "SHB",
            "MSB": "MSB", "LPBANK": "LPB", "OCB": "OCB", "HDBANK": "HDB"
        }
        _code = bank_codes.get(bank_key, bank_key)
        qr_bank = _BANK_BIN.get(_code) or _code
        stk = re.sub(r"\s+", "", str(stk or ""))
        qr_url = "https://img.vietqr.io/image/" + str(qr_bank) + "-" + str(stk) + "-compact2.png?" + urlencode({
            "amount": int(amount), "addInfo": transfer_memo, "accountName": str(name or "")
        })
        _wd_bal = bal_block(uid)
        for admin_id in ADMIN_IDS:
            try:
                admin_text = (
                    f'{ce("🎁")} <b>YÊU CẦU RÚT TIỀN MỚI</b> {ce("🎁")}\n'
                    f'━━━━━━━━━━━━━━━━━━━━━\n'
                    f'{ce("🧾")} <b>Mã yêu cầu:</b> <code>{request_code}</code>\n'
                    f'{ce("👥")} <b>ID:</b> <code>{uid}</code>\n'
                    f'{ce("💰")} <b>Số tiền:</b> <code>{fmt_money(amount)}đ</code>\n'
                    f'{ce("💳")} <b>Phương thức:</b> <code>{html.escape(str(method))}</code>\n'
                    f'{ce("🏦")} <b>Ngân hàng:</b> <code>{html.escape(str(bank))}</code>\n'
                    f'{ce("🔢")} <b>STK/SĐT:</b> <code>{html.escape(str(stk))}</code>\n'
                    f'{ce("👤")} <b>Chủ TK:</b> <code>{html.escape(str(name))}</code>\n'
                    f'{ce("📝")} <b>Nội dung chuyển khoản:</b> <code>{html.escape(transfer_memo)}</code>\n'
                    f'{ce("⏰")} <b>Thời gian:</b> <code>{now_str}</code>\n'
                    f'{_wd_bal}\n'
                    f'━━━━━━━━━━━━━━━━━━━━━\n'
                    f'<i>QR là thông tin chuyển khoản để admin xử lý thủ công; vui lòng kiểm tra đúng người nhận trước khi chuyển.</i>'
                )
                # BANKING: luôn tạo QR VietQR động chứa đúng số tiền và nội dung.
                # MOMO/ZALOPAY: dùng QR ví do người dùng tải lên khi liên kết;
                # không tự nhúng số tiền/nội dung vào QR ví khi chưa có định dạng/API chính thức.
                if str(method).upper() == "BANKING":
                    try:
                        dynamic_qr = make_local_qr(
                            amount=amount,
                            content=transfer_memo,
                            bank_id=qr_bank,
                            account_no=stk,
                        )
                        await ctx.bot.send_photo(
                            chat_id=admin_id, photo=dynamic_qr,
                            caption=admin_text, reply_markup=keyboard,
                            parse_mode=ParseMode.HTML
                        )
                    except Exception as qr_error:
                        print(f"Không tạo được QR ngân hàng động: {qr_error}")
                        await send_deposit_qr(
                            ctx.bot, admin_id, qr_url, admin_text, keyboard,
                            amount, transfer_memo, bank_id=qr_bank, account_no=stk
                        )
                elif payout_qr_file_id:
                    await ctx.bot.send_photo(
                        chat_id=admin_id, photo=payout_qr_file_id,
                        caption=admin_text, reply_markup=keyboard,
                        parse_mode=ParseMode.HTML
                    )
                else:
                    # Không dùng QR ngân hàng cho ví điện tử vì có thể chuyển sai người nhận.
                    await ctx.bot.send_message(
                        chat_id=admin_id,
                        text=admin_text + "\n\n⚠️ Tài khoản ví chưa có ảnh QR đã lưu. Vui lòng kiểm tra thông tin ví trước khi chuyển.",
                        reply_markup=keyboard,
                        parse_mode=ParseMode.HTML
                    )
            except Exception as e:
                print(f"Không thể gửi QR/tin nhắn đến admin {admin_id}: {e}")
                try:
                    await ctx.bot.send_message(admin_id, admin_text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
                except Exception:
                    pass
        await msg_obj.reply_text(
            f'{ce("✅")} <b>GỬI YÊU CẦU RÚT THÀNH CÔNG!</b>\n\n'
            f'{ce("💰")} Số tiền rút: <code>{fmt_money(amount)}đ</code>\n'
            f'{bal_block(uid)}\n'
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

        # Chống spam lệnh nạp: mỗi lệnh sống 10 phút, đang có lệnh thì phải chờ; quá 5 mã chưa nạp => khóa ẩn.
        _gate, _info = nap_order_gate(uid)
        if _gate == "banned":
            return                                   # khóa ẩn: im lặng hoàn toàn, không báo gì
        if _gate == "wait":
            return await msg_obj.reply_text(nap_wait_text(_info), parse_mode=ParseMode.HTML)

        qr_url, caption, content = get_deposit_info(uid, amount)
        _order_id = nap_order_record(uid, amount, content)   # không có await giữa gate và record => không bị tạo trùng
        kb = InlineKeyboardMarkup([
            [btn("Hỗ Trợ", "🔔", callback_data="dep_support")]
        ])
        _sent = await send_deposit_qr(ctx.bot, msg_obj.chat_id, qr_url, caption, kb, amount, content)
        nap_order_schedule_expiry(ctx.bot, _sent, _order_id)
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
    if query("SELECT 1 FROM admin_code_bans WHERE user_id=%s", (uid,)):
        await update.effective_message.reply_text("🚫 Tài khoản của bạn hiện không được phép nhập code/giftcode. Vui lòng liên hệ hỗ trợ.")
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

        required_bet = get_balance(uid) * wager      # toàn bộ số dư (đã gồm code) × vòng cược
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
            f'{bal_block(uid)}'
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
        f'Mã đã nhập: <code>{code_str}</code>\n\n'
        f'{bal_block(uid)}'
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

    # Chặn ở đầu luồng xử lý tin nhắn để không thể đi vòng qua trạng thái
    # nhập liệu đang chờ (pending_inputs), lệnh /code hay gửi mã trực tiếp.
    if query("SELECT 1 FROM admin_code_bans WHERE user_id=%s", (uid,)):
        code_like = (
            txt.strip().upper().startswith("XOCLO88-")
            or re.match(r"^/code(?:@\\w+)?(?:\\s|$)", txt.strip(), re.I)
            or re.match(r"^/nhapcode(?:@\\w+)?(?:\\s|$)", txt.strip(), re.I)
        )
        if code_like:
            await update.effective_message.reply_text(
                "🚫 Tài khoản của bạn hiện không được phép nhập code/giftcode. Vui lòng liên hệ hỗ trợ."
            )
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

    if update.effective_chat.type == "private" and re.fullmatch(r'XOCLO88-[A-Z0-9]+(?:-[A-Z0-9]+)?', txt.strip().upper()):
        code_in = txt.strip().upper()
        if await redeem_giftcode(update, uid, code_in):
            return
        return await user_reply.reply_text(f'{ce("❌")} Mã quà tặng không tồn tại.', parse_mode=ParseMode.HTML)

    if key == "ADMIN" and uid in ADMIN_IDS:
        return await admin_panel_cmd(update, ctx)

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
            [btn("Tích lũy nạp", "💎", callback_data="acc_tich_luy")],
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
    if key == "LIÊN KẾT TÀI KHOẢN":
        return await lien_ket(update, ctx)

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
            [btn("TOP CƯỢC NGÀY", "🏆", callback_data="top_cuoc_ngay")],
            [btn("TOP DÂY THẮNG", "🔥", callback_data="top_streak_win")],
            [btn("TOP DÂY THUA", "🥶", callback_data="top_streak_loss")]
        ])
        return await user_reply.reply_text(
            f'{ce("🏆")} <b>ĐUA TOP</b>\nChọn bảng muốn xem:',
            reply_markup=kb, parse_mode=ParseMode.HTML)

    if key == "EVENT":
        kb = InlineKeyboardMarkup([
            [btn("Hoàn cược ngày", "📈", callback_data="ev_hc_ngay"), btn("Hoàn cược tuần", "📉", callback_data="ev_hc_tuan")],
            [btn("Hoàn thua ngày", "💸", callback_data="ev_ht_ngay"), btn("Hoàn thua tuần", "💸", callback_data="ev_ht_tuan")],
            [btn("Nhận thưởng VIP", "👑", callback_data="ev_nhan_vip")],
            [btn("Tương tác nhóm +50k", "🎁", callback_data="ev_tuong_tac")],
            [btn("Mời đệ tử", "🧑‍🤝‍🧑", callback_data="ev_moi_de_tu")]
        ])
        return await user_reply.reply_text(
            f'{ce("🎁")} <b>TRUNG TÂM EVENT XOCLO88</b>\nChọn chương trình bạn muốn xem hoặc nhận thưởng:',
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
            return await reply_bet_notice(update.effective_message, message, success, private=True)

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
                            await reply_bet_notice(update.effective_message, msg, success, private=True)
                            return
                    except: pass

                if cmd == "D1" and len(parts) == 3:
                    face = parts[1]
                    if face in "123456" and len(face) == 1:
                        try:
                            amount = get_balance(uid) if parts[2].lower() in ["max", "all"] else int(parts[2])
                            if amount >= 1000:
                                success, msg = await place_anonymous_bet(ctx.bot, uid, GROUP_IDS[0], f"d1_{face}", amount)
                                await reply_bet_notice(update.effective_message, msg, success, private=True)
                                return
                        except: pass
                if cmd == "D2" and len(parts) == 3:
                    faces = parts[1]
                    if len(faces) == 2 and all(c in "123456" for c in faces):
                        try:
                            amount = get_balance(uid) if parts[2].lower() in ["max", "all"] else int(parts[2])
                            if amount >= 1000:
                                success, msg = await place_anonymous_bet(ctx.bot, uid, GROUP_IDS[0], f"d2_{faces}", amount)
                                await reply_bet_notice(update.effective_message, msg, success, private=True)
                                return
                        except: pass
                if cmd == "D3" and len(parts) == 3:
                    try:
                        sum_val = int(parts[1])
                        if 3 <= sum_val <= 18:
                            amount = get_balance(uid) if parts[2].lower() in ["max", "all"] else int(parts[2])
                            if amount >= 1000:
                                success, msg = await place_anonymous_bet(ctx.bot, uid, GROUP_IDS[0], f"d3_{sum_val}", amount)
                                await reply_bet_notice(update.effective_message, msg, success, private=True)
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
        _cleared, _extra = apply_deposit_wager_rule(target_id, get_balance(target_id), amount)
        add_money(target_id, amount, f"Nạp tiền +{amount:,}đ")
        await notify_deposit_wager(ctx.bot, target_id, _cleared, _extra)
        
        # Chỉ hiển thị 5 số cuối của ID.
        masked_id = mask_user_id(target_id)
            
        try:
            await send_group_notice(ctx.bot, chat_id=LOG_GROUP_ID,
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
                    f'{bal_block(target_id)}{deposit_wager_line(target_id)}\n\n'
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
                    f'{bal_block(target_id)}{deposit_wager_line(target_id)}'
                )
                await ctx.bot.send_message(chat_id=target_id, text=bill, parse_mode=ParseMode.HTML)
            except Exception as e: pass
        await update.effective_message.reply_text(
            f'{ce("✅")} <b>NẠP TIỀN THÀNH CÔNG</b>\n\n'
            f'{ce("👥")} ID: <code>{target_id}</code>\n'
            f'{ce("💰")} Số tiền: <code>+{fmt_money(amount)}đ</code>\n'
            f'{bal_block(target_id)}',
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
        await update.effective_message.reply_text(f'{ce("✅")} Đã cộng <code>{fmt_money(amt)}đ</code> cho ID <code>{uid}</code>\n{bal_block(uid)}', parse_mode=ParseMode.HTML)
    except (IndexError, ValueError):
        await update.effective_message.reply_text(f'{ce("❌")} Cú pháp: <code>/add [ID] [số tiền]</code>', parse_mode=ParseMode.HTML)

@admin_only
async def sub(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        uid, amt = int(ctx.args[0]), int(ctx.args[1])
        if sub_money(uid, amt, "Admin trừ tiền"):
            await update.effective_message.reply_text(f'{ce("✅")} Đã trừ <code>{fmt_money(amt)}đ</code> của ID <code>{uid}</code>\n{bal_block(uid)}', parse_mode=ParseMode.HTML)
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

# Gửi thông báo hàng loạt có giới hạn tốc độ, dùng chung cho lệnh bot và web admin.
_BROADCAST_LOCK = asyncio.Lock()
_BROADCAST_DELAY = 0.10  # khoảng 10 tin/giây, chừa tài nguyên cho lệnh/game khác
_BROADCAST_BATCH = 20
_BROADCAST_BATCH_PAUSE = 0.50


async def _broadcast_send_one(bot, uid, message):
    """Gửi một tin; nếu Telegram giới hạn tốc độ thì tự chờ và thử lại."""
    for attempt in range(6):
        try:
            await bot.send_message(
                chat_id=int(uid), text=message, parse_mode=ParseMode.HTML,
                connect_timeout=10, read_timeout=20, write_timeout=20,
                pool_timeout=10
            )
            return True
        except RetryAfter as exc:
            wait_for = getattr(exc, "retry_after", 1)
            try:
                wait_for = float(wait_for.total_seconds() if hasattr(wait_for, "total_seconds") else wait_for)
            except (TypeError, ValueError):
                wait_for = 1
            await asyncio.sleep(max(1.0, wait_for) + 0.3)
        except Exception as exc:
            # Lỗi mạng tạm thời: thử lại tối đa 2 lần; user chặn bot thì bỏ qua.
            name = type(exc).__name__.lower()
            if attempt < 2 and any(x in name for x in ("timeout", "network", "connect")):
                await asyncio.sleep(1.0 + attempt)
                continue
            return False
    return False


async def _broadcast_all(bot, users, message, progress_callback=None):
    """Worker tuần tự, giới hạn tốc độ và nhường event loop giữa các lần gửi."""
    sent = failed = 0
    async with _BROADCAST_LOCK:
        total = len(users)
        for index, row in enumerate(users, 1):
            uid = row[0] if isinstance(row, (tuple, list)) else row
            if await _broadcast_send_one(bot, uid, message):
                sent += 1
            else:
                failed += 1

            if index % _BROADCAST_BATCH == 0:
                if progress_callback:
                    await progress_callback(sent, failed, total)
                await asyncio.sleep(_BROADCAST_BATCH_PAUSE)
            else:
                await asyncio.sleep(_BROADCAST_DELAY)

        if progress_callback:
            await progress_callback(sent, failed, total)
    return sent, failed


@admin_only
async def broadcast(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not ctx.args:
        return await update.effective_message.reply_text(
            f'{ce("❌")} Cú pháp: <code>/send [nội dung]</code>',
            parse_mode=ParseMode.HTML
        )

    msg_to_send = " ".join(ctx.args)
    users = await asyncio.to_thread(query, "SELECT user_id FROM users") or []
    status_msg = await update.effective_message.reply_text(
        f'{ce("🚀")} Đã xếp hàng gửi tới {len(users)} người. Bot vẫn tiếp tục xử lý lệnh bình thường…',
        parse_mode=ParseMode.HTML
    )
    if _BROADCAST_LOCK.locked():
        return await status_msg.edit_text(
            f'{ce("⏳")} Đang có đợt thông báo khác chạy. Vui lòng đợi đợt đó hoàn tất.',
            parse_mode=ParseMode.HTML
        )

    message = f'{ce("🔔")} <b>THÔNG BÁO MỚI</b>\\n\\n{html.escape(msg_to_send)}'
    last_update = 0

    async def update_progress(sent, failed, total):
        nonlocal last_update
        processed = sent + failed
        if processed == total or processed - last_update >= 100:
            last_update = processed
            try:
                await status_msg.edit_text(
                    f'{ce("📣")} <b>ĐANG GỬI THÔNG BÁO</b>\\n'
                    f'Đã xử lý: <code>{processed}/{total}</code>\\n'
                    f'Thành công: <code>{sent}</code> · Lỗi: <code>{failed}</code>',
                    parse_mode=ParseMode.HTML
                )
            except Exception:
                pass

    async def worker():
        try:
            sent, failed = await _broadcast_all(ctx.bot, users, message, update_progress)
            await status_msg.edit_text(
                f'{ce("✅")} <b>HOÀN THÀNH THÔNG BÁO</b>\\n\\n'
                f'{ce("👥")} Tổng: <code>{len(users)}</code>\\n'
                f'{ce("📊")} Thành công: <code>{sent}</code>\\n'
                f'{ce("❌")} Thất bại: <code>{failed}</code>',
                parse_mode=ParseMode.HTML
            )
        except Exception as exc:
            print(f"[broadcast] worker error: {exc}")

    task = asyncio.create_task(worker())
    # Lưu task để không bị thu hồi và dễ theo dõi khi bot đang chạy.
    if "_BROADCAST_TASKS" not in globals():
        globals()["_BROADCAST_TASKS"] = set()
    _BROADCAST_TASKS.add(task)
    task.add_done_callback(_BROADCAST_TASKS.discard)

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
        data = query("SELECT amount, note, time, id FROM history WHERE user_id=%s ORDER BY id DESC LIMIT 100", (uid,))
        if not data:
            await update.effective_message.reply_text(f'{ce("📥")} User <code>{uid}</code> chưa có giao dịch.', parse_mode=ParseMode.HTML)
        else:
            _bm = await asyncio.to_thread(_rp_bal_map, uid)
            msg = f'{ce("📜")} <b>LỊCH SỬ USER <code>{uid}</code>:</b>\n\n'
            for d in data:
                _b = _bm.get(d[3])
                _bt = f' | 💳 {fmt_money(_b[0])} → {fmt_money(_b[1])}' if _b else ''
                msg += f'{ce("💰")} <code>{fmt_money(d[0])}</code>{_bt} | {html.escape(d[1])} | <i>{d[2]}</i>\n'
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

# ---------- THỐNG KÊ HỆ THỐNG (đọc từ bảng nạp / rút / bet_daily; có hỗ trợ mốc reset) ----------
def _ep_int(key):
    try:
        return int(get_setting(key, "0") or 0)
    except (TypeError, ValueError):
        return 0

def _stat_epoch_note():
    at = get_setting("stats_epoch_at", "") or ""
    if not at:
        return ""
    return f'{ce("📌")} <i>Thống kê đang tính từ lúc reset: {html.escape(at)}</i>\n'

def stat_dep(like=None):
    sql = ("SELECT COUNT(*), COALESCE(SUM(amount),0), COUNT(DISTINCT user_id) "
           "FROM deposit_history WHERE status='success' AND id>%s")
    args = [_ep_int("stats_epoch_dep")]
    if like:
        sql += " AND time LIKE %s"
        args.append(like)
    rows = query(sql, tuple(args)) or []
    r = rows[0] if rows else (0, 0, 0)
    return int(r[0] or 0), int(r[1] or 0), int(r[2] or 0)

def stat_wd(like=None):
    sql = ("SELECT COUNT(*), COALESCE(SUM(amount),0) "
           "FROM withdraw_history WHERE status='success' AND id>%s")
    args = [_ep_int("stats_epoch_wd")]
    if like:
        sql += " AND time LIKE %s"
        args.append(like)
    rows = query(sql, tuple(args)) or []
    r = rows[0] if rows else (0, 0)
    return int(r[0] or 0), int(r[1] or 0)

def stat_bet_totals(d1, d2):
    ed = get_setting("stats_epoch_day", "1970-01-01") or "1970-01-01"
    sql = ("SELECT COALESCE(SUM(GREATEST(b.bet-COALESCE(s.bet,0),0)),0), "
           "COALESCE(SUM(GREATEST(b.win-COALESCE(s.win,0),0)),0), COUNT(DISTINCT b.user_id) "
           "FROM bet_daily b LEFT JOIN stats_bet_base s ON s.user_id=b.user_id AND s.day=b.day "
           "WHERE b.day>=%s AND b.day>=%s AND b.day<=%s")
    rows = query(sql, (ed, d1, d2)) or []
    r = rows[0] if rows else (0, 0, 0)
    return int(r[0] or 0), int(r[1] or 0), int(r[2] or 0)

def _signed_money(n):
    n = int(n or 0)
    return f'{"+" if n >= 0 else "−"}{fmt_money(abs(n))}đ'

@admin_only
async def dashboard_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    now = get_vietnam_time()
    today = get_vietnam_date()
    like_day = f"%{today}"
    like_month = f"%/{now.strftime('%m/%Y')}"
    d_date = now.date()
    m_start = d_date.replace(day=1)
    dn, ds, du = stat_dep(like_day)
    wn, wsum = stat_wd(like_day)
    mdn, mds, mdu = stat_dep(like_month)
    mwn, mws = stat_wd(like_month)
    adn, ads, adu = stat_dep()
    awn, aws = stat_wd()
    tb, tw, tp = stat_bet_totals(d_date, d_date)
    mb, mw, mpl = stat_bet_totals(m_start, d_date)
    ab, aw, apl = stat_bet_totals(datetime(2000, 1, 1).date(), d_date)
    msg = (
        f'{ce("📊")} <b>BẢNG THỐNG KÊ HỆ THỐNG</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("🗓")} <b>HÔM NAY</b> <code>{today}</code>\n'
        f'  {ce("📥")} Nạp: <code>+{fmt_money(ds)}đ</code> · {dn} lệnh · {du} người\n'
        f'  {ce("📤")} Rút: <code>{fmt_money(wsum)}đ</code> · {wn} lệnh\n'
        f'  {ce("🎯")} Cược: <code>{fmt_money(tb)}đ</code> · {tp} người\n'
        f'  {ce("🏆")} Trả thưởng: <code>{fmt_money(tw)}đ</code>\n'
        f'  {ce("💰")} Lãi/lỗ game: <code>{_signed_money(tb - tw)}</code>\n\n'
        f'{ce("🗓")} <b>THÁNG {now.strftime("%m/%Y")}</b>\n'
        f'  {ce("📥")} Nạp: <code>+{fmt_money(mds)}đ</code> · {mdn} lệnh\n'
        f'  {ce("📤")} Rút: <code>{fmt_money(mws)}đ</code> · {mwn} lệnh\n'
        f'  {ce("🎯")} Cược: <code>{fmt_money(mb)}đ</code> · Trả thưởng: <code>{fmt_money(mw)}đ</code>\n'
        f'  {ce("💰")} Lãi/lỗ game: <code>{_signed_money(mb - mw)}</code>\n\n'
        f'{ce("📈")} <b>TỔNG TOÀN THỜI GIAN</b>\n'
        f'  {ce("📥")} Nạp: <code>+{fmt_money(ads)}đ</code> · {adn} lệnh · {adu} người\n'
        f'  {ce("📤")} Rút: <code>{fmt_money(aws)}đ</code> · {awn} lệnh\n'
        f'  {ce("💵")} Nạp − Rút: <code>{_signed_money(ads - aws)}</code>\n'
        f'  {ce("💰")} Lãi/lỗ game: <code>{_signed_money(ab - aw)}</code>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{_stat_epoch_note()}'
        f'{ce("💡")} <i>Xoá 1 giao dịch bằng /xoanap hoặc /xoarut, thống kê tự cập nhật. Reset bằng /resetthongke.</i>'
    )
    kb = InlineKeyboardMarkup([
        [btn("Xuất file 30 ngày", "📊", callback_data="adm2:run:xuatthongke|30"),
         btn("Xuất file 7 ngày", "📥", callback_data="adm2:run:xuatthongke|7")],
        [btn("Xuất toàn bộ thời gian", "📎", callback_data="adm2:run:xuatthongke|all"),
         btn("Menu admin", "🏠", callback_data="adm2:home")],
    ])
    await update.effective_message.reply_text(msg, reply_markup=kb, parse_mode=ParseMode.HTML)

@admin_only
async def tong_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    adn, ads, adu = stat_dep()
    awn, aws = stat_wd()
    ab, aw, apl = stat_bet_totals(datetime(2000, 1, 1).date(), get_vietnam_time().date())
    pend = _sum("SELECT COALESCE(SUM(amount),0) FROM withdraw_history WHERE status='pending'")
    bal = _sum("SELECT COALESCE(SUM(balance),0) FROM users")
    msg = (
        f'{ce("📊")} <b>TỔNG QUAN TÀI CHÍNH HỆ THỐNG</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("📥")} <b>Tổng nạp:</b> <code>+{fmt_money(ads)}đ</code> ({adn} lệnh, {adu} người)\n'
        f'{ce("📤")} <b>Tổng rút:</b> <code>{fmt_money(aws)}đ</code> ({awn} lệnh)\n'
        f'{ce("⌛")} <b>Rút đang chờ:</b> <code>{fmt_money(int(pend))}đ</code>\n'
        f'{ce("💵")} <b>Nạp − Rút:</b> <code>{_signed_money(ads - aws)}</code>\n'
        f'{ce("🎯")} <b>Tổng cược:</b> <code>{fmt_money(ab)}đ</code>\n'
        f'{ce("🏆")} <b>Tổng trả thưởng:</b> <code>{fmt_money(aw)}đ</code>\n'
        f'{ce("💰")} <b>Lãi/lỗ game:</b> <code>{_signed_money(ab - aw)}</code>\n'
        f'{ce("💎")} <b>Tổng số dư người dùng:</b> <code>{fmt_money(int(bal))}đ</code>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{_stat_epoch_note()}'
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
            f'{ce("🎯")} <b>Yêu cầu cược:</b> <code>{fmt_money(required_bet)}đ</code>\n'
            f'{bal_block(target_id)}',
            parse_mode=ParseMode.HTML)
        try:
            await ctx.bot.send_message(target_id,
                f'{ce("🎁")} <b>THÔNG BÁO KHUYẾN MÃI</b>\n\n'
                f'Bạn vừa nhận được khuyến mãi nạp: <code>+{fmt_money(bonus_amount)}đ</code>\n'
                f'{bal_block(target_id)}\n\n'
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
    dep = stat_dep(like)
    wd = stat_wd(like)
    wd_pending = one("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM withdraw_history WHERE status='pending'") or (0, 0)
    bets = stat_bet_totals(now.date(), now.date())
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
                    custom = get_setting("promo_group_text", "") or ""
                    text = (custom.replace("{PERCENT}", str(PROMO_PCT))
                            .replace("{ORDER_PERCENT}", str(PROMO_ORDER_PCT))
                            .replace("{HOURS}", promo_windows_text())
                            if custom else
                            (f'{ce("⏰")} <b>GIỜ VÀNG NẠP ĐÃ MỞ!</b> {ce("🎉")}\n'
                             f'{ce("✨")} Nạp ngay nhận khuyến mãi <b>{PROMO_PCT}%</b> (mỗi ngày 1 lần){until}\n'
                             f'{ce("➕")} Mỗi lệnh nạp được thưởng thêm <b>{PROMO_ORDER_PCT}%</b>\n'
                             f'{ce("🗓")} Giờ vàng hằng ngày: <code>{promo_windows_text()}</code>'))
                else:
                    text = (f'{ce("⌛")} <b>Giờ vàng nạp đã kết thúc.</b>\n'
                            f'{ce("🗓")} Hẹn bạn khung giờ vàng tiếp theo: <code>{promo_windows_text()}</code>')
                for gid in GROUP_IDS:
                    try:
                        promo_post = await bot.send_message(gid, text, parse_mode=ParseMode.HTML)
                        try:
                            await bot.pin_chat_message(gid, promo_post.message_id, disable_notification=True)
                        except Exception as pin_error:
                            print(f"Không ghim được thông báo khuyến mãi ở nhóm {gid}: {pin_error}")
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
    'mt_tx3d': {'name': 'TÀI XỈU 3D', 'type': 'game', 'icon': '🎲'},
    'mt_nap': {'name': 'NẠP TIỀN', 'type': 'feature', 'icon': '💳'},
    'mt_rut': {'name': 'RÚT TIỀN (TẤT CẢ)', 'type': 'feature', 'icon': '💸'},
    'mt_rut_momo': {'name': 'RÚT MOMO', 'type': 'feature', 'icon': '❤️'},
    'mt_rut_zalopay': {'name': 'RÚT ZALOPAY', 'type': 'feature', 'icon': '💠'},
    'mt_rut_banking': {'name': 'RÚT BANKING', 'type': 'feature', 'icon': '💳'},
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
        *_tgdice_mt_rows(st, ic),
        [btn(f"Tài Xỉu 3D: {st('mt_tx3d')}", ic('mt_tx3d'), callback_data="tg_mt_tx3d")],
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

async def tatcuoc_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
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
            f'{ce("✍️")} Cú pháp:\n• Tắt: <code>/tatcuoc off</code>\n• Bật: <code>/tatcuoc on</code>',
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

# ============================================================
# MINIAPP TÀI XỈU 3D
#  • Giao diện: index.html (Telegram Web App) — phục vụ tại  GET /app
#  • API: GET /api/state , POST /api/bet  (xác thực bằng initData của Telegram)
#  • Số dư dùng CHUNG với bot chính (bảng users) → cược/thắng/hoàn đều ghi vào lịch sử, thống kê, vòng cược
#  • Phiên chạy chung cho mọi người chơi: đặt cược -> úp bát -> mở bát -> phiên mới
#  • /hu [số tiền]  : đặt tiền trong hũ của game 3D (admin)
#  • /ep ...        : ÉP kết quả (admin, chat riêng) — áp dụng cả khi có người chơi thật cược
#  • Bảo trì: /baotri (nút "Tài Xỉu 3D") hoặc /baotrigame tx3d on|off
# ============================================================
TX3D_NAME = "TÀI XỈU 3D"
TX3D_MT_KEY = "mt_tx3d"          # khoá bảo trì trong bảng settings
TX3D_POT_KEY = "tx3d_pot"        # khoá lưu tiền hũ trong bảng settings
TX3D_GAME_ID = 11                # id game dùng cho /camgame (banned_games)
TX3D_BET_SECONDS = 45            # thời gian đặt cược mỗi phiên
TX3D_COVER_SECONDS = 20          # thời gian úp bát / mở bát trước khi sang phiên mới
TX3D_MIN_BET = 1000
TX3D_MAX_BET = 10 ** 12
TX3D_PAYOUT = 1.97               # thắng Tài/Xỉu nhận x1.97 (giống Tài Xỉu Room)
TX3D_JP_MULT_MIN = 10            # nổ hũ: mỗi người nhận x10 đến x12 tiền cược (không ăn cả hũ)
TX3D_JP_MULT_MAX = 12
TX3D_POT_DEFAULT = 100000        # tiền hũ khi mới tạo / sau khi nổ
TX3D_POT_RATE = 0.018            # 1,8% tiền thua cộng vào hũ (khi nhà thắng phiên đó)
TX3D_BAO_REFUND = False          # True = Bão (3 mặt giống nhau, trừ 111 và 666) hoàn tiền cược; False = nhà ăn
TX3D_HIST_MAX = 180              # số phiên hiển thị trên cầu
TX3D_USER_TTL = 3.0              # giây cache số dư mỗi người chơi (giảm tải DB khi app gọi liên tục)
TX3D_INITDATA_MAX_AGE = 86400    # initData Telegram hợp lệ tối đa 24 giờ

query("""
CREATE TABLE IF NOT EXISTS tx3d_rounds (
    id BIGINT PRIMARY KEY,
    d1 INTEGER, d2 INTEGER, d3 INTEGER,
    created TEXT
)
""")
query("""
CREATE TABLE IF NOT EXISTS tx3d_bets (
    round_id BIGINT,
    user_id BIGINT,
    side TEXT,
    amount BIGINT,
    PRIMARY KEY (round_id, user_id)
)
""")
query("INSERT INTO settings (key, value) VALUES ('mt_tx3d', '0') ON CONFLICT (key) DO NOTHING")
query("INSERT INTO settings (key, value) VALUES (%s, %s) ON CONFLICT (key) DO NOTHING", (TX3D_POT_KEY, str(TX3D_POT_DEFAULT)))


class _TX3DState:
    def __init__(self):
        self.lock = None
        self.round_id = 0
        self.phase = "bet"          # bet | cover
        self.phase_end = time.time() + TX3D_BET_SECONDS
        self.bets = {}              # uid -> {"side","amt","name"}
        self.dice = None            # chỉ có từ lúc úp bát
        self.result = None          # kết quả đã tính (chưa trả tiền) trong lúc úp bát
        self.applied = False
        self.pot = TX3D_POT_DEFAULT
        self.hist = []              # mới nhất ở đầu: [[d1,d2,d3], ...]
        self.last = None            # kết quả phiên vừa xong (để người chưa kịp mở bát vẫn thấy)
        self.force = None           # {"dice": [..] | None, "kind": "tai"|"xiu"|None, "by": uid}
        self.users = {}             # uid -> (ts, balance, banned, game_banned)
        self.flags = {}
        self.flags_ts = 0.0
        self.ready = False

TX3D = _TX3DState()


def _tx3d_lock():
    if TX3D.lock is None:
        TX3D.lock = asyncio.Lock()
    return TX3D.lock


def _tx3d_norm_url(raw):
    """Chuẩn hoá link miniapp: thêm https://, thêm /app nếu thiếu đường dẫn, bỏ link GitHub."""
    u = (raw or "").strip().strip("\"'").strip()
    if not u:
        return None
    if u.lower().startswith("http://"):
        u = "https://" + u[7:]
    elif not u.lower().startswith("https://"):
        u = "https://" + u.lstrip("/")
    pr = urlparse(u)
    host = (pr.netloc or "").lower()
    if not host or "." not in host or host.endswith("github.com") or host.endswith("githubusercontent.com"):
        return None
    path = pr.path if pr.path not in ("", "/") else "/app"
    return f"https://{host}{path}"


def tx3d_url():
    """Địa chỉ HTTPS của miniapp: ưu tiên biến MINIAPP_URL, nếu sai/thiếu thì dùng domain Railway."""
    for raw in (os.getenv("MINIAPP_URL"), os.getenv("RAILWAY_PUBLIC_DOMAIN"), os.getenv("RAILWAY_STATIC_URL")):
        u = _tx3d_norm_url(raw)
        if u:
            return u
    return None


def tx3d_play_kb(private=True):
    """Nút 'CHƠI TÀI XỈU 3D NGAY' gắn dưới thông báo đặt cược (web_app trong chat riêng, link /start trong nhóm)."""
    url = tx3d_url()
    if not url:
        return None
    if private:
        return InlineKeyboardMarkup([[InlineKeyboardButton("🎮 CHƠI TÀI XỈU 3D NGAY", web_app=WebAppInfo(url=url))]])
    return InlineKeyboardMarkup([[InlineKeyboardButton("🎮 CHƠI TÀI XỈU 3D NGAY", url=f"https://t.me/{BOT_USERNAME}?start=tx3d")]])


async def reply_bet_notice(msg_obj, text, success=True, private=True):
    """Trả lời thông báo đặt cược, kèm nút vào miniapp (nếu lỗi nút vẫn gửi tin như cũ)."""
    kb = tx3d_play_kb(private) if success else None
    try:
        return await msg_obj.reply_text(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception as e:
        if kb is None:
            raise
        print(f"[tx3d] không gắn được nút vào thông báo cược: {e}")
        return await msg_obj.reply_text(text, parse_mode=ParseMode.HTML)


async def send_bet_notice(bot, chat_id, text):
    kb = tx3d_play_kb(True)
    try:
        return await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML, reply_markup=kb)
    except Exception as e:
        if kb is None:
            raise
        print(f"[tx3d] không gắn được nút vào xác nhận cược riêng: {e}")
        return await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML)


# ---------- xác thực Telegram Web App ----------
def tx3d_verify_init(init_data):
    """Trả về dict user của Telegram nếu initData hợp lệ, ngược lại None."""
    if not init_data or not TOKEN:
        return None
    try:
        pairs = dict(parse_qsl(init_data, keep_blank_values=True))
        got_hash = pairs.pop("hash", None)
        if not got_hash:
            return None
        check = "\n".join(f"{k}={pairs[k]}" for k in sorted(pairs))
        secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
        calc = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, got_hash):
            return None
        if TX3D_INITDATA_MAX_AGE and time.time() - int(pairs.get("auth_date", "0")) > TX3D_INITDATA_MAX_AGE:
            return None
        user = json.loads(pairs.get("user", "{}"))
        if not isinstance(user, dict) or not user.get("id"):
            return None
        return user
    except Exception:
        return None


def _tx3d_auth(request):
    u = tx3d_verify_init(request.headers.get("X-Init", ""))
    if not u:
        return None
    name = (u.get("first_name") or u.get("username") or str(u["id"])).strip() or str(u["id"])
    return int(u["id"]), name


def _tx3d_mask(name):
    name = (name or "").strip() or "Player"
    return name[:3] + "***"


# ---------- truy vấn DB (chạy trong thread để không chặn bot) ----------
def _tx3d_user_row(uid):
    sql = ("SELECT balance, EXISTS(SELECT 1 FROM banned b WHERE b.user_id=%s), "
           "EXISTS(SELECT 1 FROM banned_games g WHERE g.user_id=%s AND g.game_id=%s) "
           "FROM users WHERE user_id=%s")
    args = (uid, uid, TX3D_GAME_ID, uid)
    rows = query(sql, args)
    if not rows:
        get_user(uid)
        rows = query(sql, args)
    if not rows:
        return None
    bal, banned, gban = rows[0]
    return int(bal or 0), bool(banned), bool(gban)


async def _tx3d_user(uid, fresh=False):
    ent = TX3D.users.get(uid)
    now = time.time()
    if ent and not fresh and now - ent[0] < TX3D_USER_TTL:
        return ent[1], ent[2], ent[3]
    row = await asyncio.to_thread(_tx3d_user_row, uid)
    if row is None:
        return None
    if len(TX3D.users) > 5000:
        TX3D.users.clear()
    TX3D.users[uid] = (now, row[0], row[1], row[2])
    return row


def _tx3d_load_flags():
    rows = query("SELECT key, value FROM settings WHERE key IN (%s, 'mt_tongbao', 'system_maintenance')", (TX3D_MT_KEY,)) or []
    return {k: v for k, v in rows}


async def _tx3d_flags():
    if time.time() - TX3D.flags_ts > 2.0:
        try:
            TX3D.flags = await asyncio.to_thread(_tx3d_load_flags)
        except Exception as e:
            print(f"[tx3d] lỗi đọc cờ bảo trì: {e}")
        TX3D.flags_ts = time.time()
    return TX3D.flags


def _tx3d_sub_sync(uid, amt, note):
    """Trừ tiền cược nguyên tử (không bao giờ âm). Trả về số dư mới hoặc None nếu không đủ."""
    rows = query(
        "UPDATE users SET balance=balance-%s, total_bet=COALESCE(total_bet,0)+%s "
        "WHERE user_id=%s AND balance>=%s RETURNING balance", (amt, amt, uid, amt))
    if not rows:
        return None
    _after = int(rows[0][0])
    query("INSERT INTO history(user_id, amount, note, time, bal_before, bal_after) VALUES(%s,%s,%s,%s,%s,%s)",
          (uid, -amt, note, get_vietnam_datetime_db(), _after + int(amt), _after))
    _bal_note(uid, _after + int(amt), _after)
    record_daily(uid, bet=amt)
    return _after


def _tx3d_boot_sync():
    """Chạy 1 lần khi khởi động: nạp cầu, tiền hũ, hoàn tiền các cược dở dang do bot bị tắt giữa phiên."""
    rows = query("SELECT id, d1, d2, d3 FROM tx3d_rounds ORDER BY id DESC LIMIT %s", (TX3D_HIST_MAX,)) or []
    TX3D.hist = [[int(r[1]), int(r[2]), int(r[3])] for r in rows]
    TX3D.round_id = int(rows[0][0]) if rows else 0
    try:
        TX3D.pot = int(get_setting(TX3D_POT_KEY, str(TX3D_POT_DEFAULT)) or TX3D_POT_DEFAULT)
    except ValueError:
        TX3D.pot = TX3D_POT_DEFAULT
    left = query("SELECT round_id, user_id, amount FROM tx3d_bets") or []
    for rid, uid, amt in left:
        try:
            add_money(int(uid), int(amt), f"Hoàn cược Tài Xỉu 3D (phiên #{rid} bị gián đoạn)")
            query("DELETE FROM tx3d_bets WHERE round_id=%s AND user_id=%s", (rid, uid))
        except Exception as e:
            print(f"[tx3d] lỗi hoàn cược dở {uid}: {e}")
    if left:
        print(f"[tx3d] đã hoàn {len(left)} cược dở dang sau khi khởi động lại")


# ---------- logic phiên ----------
_TX3D_RNG = random.SystemRandom()


def _tx3d_dice_for(kind):
    for _ in range(500):
        d = [_TX3D_RNG.randint(1, 6) for _ in range(3)]
        if d[0] == d[1] == d[2]:
            continue
        if kind == "tai" and sum(d) >= 11:
            return d
        if kind == "xiu" and sum(d) <= 10:
            return d
    return [4, 5, 6] if kind == "tai" else [1, 2, 3]


def _tx3d_compute(dice, bets, rid, pot):
    """Tính kết quả phiên (CHƯA trả tiền). Trả về dict mô tả thắng/thua, hũ và lãi/lỗ từng người."""
    total = sum(dice)
    triple = dice[0] == dice[1] == dice[2]
    win, jp_side = None, None
    if triple:
        if dice[0] == 6:
            win = jp_side = "tai"
        elif dice[0] == 1:
            win = jp_side = "xiu"
    else:
        win = "tai" if total >= 11 else "xiu"
    pay, refund = {}, {}
    total_win = total_lose = 0
    for uid, b in bets.items():
        if win and b["side"] == win:
            pay[uid] = int(b["amt"] * TX3D_PAYOUT)
            total_win += pay[uid]
        elif triple and not win and TX3D_BAO_REFUND:
            refund[uid] = b["amt"]
        else:
            total_lose += b["amt"]
    contrib = int(total_lose * TX3D_POT_RATE) if total_lose > total_win else 0
    pot_total = pot + contrib
    pot_after = pot_total
    share, jp = {}, None
    if jp_side:
        winners = [(uid, b) for uid, b in bets.items() if b["side"] == jp_side]
        tb = sum(b["amt"] for _, b in winners)
        if winners and pot_total > 0 and tb > 0:
            for uid, b in winners:
                share[uid] = int(b["amt"] * _TX3D_RNG.randint(TX3D_JP_MULT_MIN, TX3D_JP_MULT_MAX))
            paid = sum(share.values())
            if paid > pot_total:                      # hũ không đủ: chia lại theo tỉ lệ, không vượt quá hũ
                for uid in share:
                    share[uid] = int(share[uid] * pot_total / paid)
                paid = sum(share.values())
            jp = {"id": rid, "total": paid, "n": len(winners),
                  "winners": sorted(((uid, _tx3d_mask(b["name"]), b["amt"], share[uid]) for uid, b in winners),
                                    key=lambda w: -w[3])[:5]}
            pot_after = max(pot_total - paid, TX3D_POT_DEFAULT)   # chỉ trừ phần đã trả, hũ không bị nổ sạch
    nets = {uid: pay.get(uid, 0) + refund.get(uid, 0) + share.get(uid, 0) - b["amt"] for uid, b in bets.items()}
    return {"win": win, "dice": list(dice), "pay": pay, "refund": refund, "share": share, "jp": jp,
            "nets": nets, "pot_after": pot_after, "pot_add": contrib}


def _tx3d_jp_view(jp, uid):
    if not jp:
        return None
    me = next((w[3] for w in jp["winners"] if w[0] == uid), 0)
    if not me:
        me = 0
    return {"id": jp["id"], "total": jp["total"], "n": jp["n"], "me": me,
            "top": [{"name": w[1], "bet": w[2], "amt": w[3], "me": w[0] == uid} for w in jp["winners"]]}


def _tx3d_apply_sync(rid, bets, res, test):
    """Trả tiền thắng / hoàn / nổ hũ, xoá cược dở, lưu lịch sử phiên."""
    for uid, b in bets.items():
        try:
            side = b["side"].upper()
            if res["pay"].get(uid):
                add_money(uid, res["pay"][uid], f"Thắng Tài Xỉu 3D {side}")
            if res["refund"].get(uid):
                add_money(uid, res["refund"][uid], f"Hoàn tiền Tài Xỉu 3D (Bão) {side}")
            if res["share"].get(uid):
                add_money(uid, res["share"][uid], f"Nổ hũ Tài Xỉu 3D +{res['share'][uid]:,}đ")
            query("DELETE FROM tx3d_bets WHERE round_id=%s AND user_id=%s", (rid, uid))
        except Exception as e:
            print(f"[tx3d] lỗi trả thưởng {uid}: {e}")
    set_setting(TX3D_POT_KEY, res["pot_after"])
    if not test:
        d = res["dice"]
        query("INSERT INTO tx3d_rounds(id,d1,d2,d3,created) VALUES(%s,%s,%s,%s,%s) ON CONFLICT (id) DO NOTHING",
              (rid, d[0], d[1], d[2], get_vietnam_datetime_db()))


def _tx3d_refund_sync(rid, bets):
    for uid, b in bets.items():
        try:
            add_money(uid, b["amt"], f"Hoàn cược Tài Xỉu 3D (lỗi phiên #{rid})")
            query("DELETE FROM tx3d_bets WHERE round_id=%s AND user_id=%s", (rid, uid))
        except Exception as e:
            print(f"[tx3d] lỗi hoàn cược {uid}: {e}")


def _tx3d_take_dice():
    """Chọn xúc xắc cho phiên. Admin dùng /ep để ÉP kết quả, áp dụng cả khi đã có người chơi thật đặt cược.
    Phiên bị ép vẫn trả thưởng và ghi vào cầu như phiên bình thường (trả về test=False)."""
    forced, TX3D.force = TX3D.force, None
    if forced:
        dice = forced["dice"] or _tx3d_dice_for(forced["kind"])
        return list(dice), False
    # Ngẫu nhiên tự nhiên: tỉ lệ nổ hũ = 0% (không bao giờ ra 1-1-1 / 6-6-6). Chỉ admin ép /ep 1 1 1 hoặc /ep 6 6 6 mới nổ.
    while True:
        d = [_TX3D_RNG.randint(1, 6) for _ in range(3)]
        if not (d[0] == d[1] == d[2] and d[0] in (1, 6)):
            return d, False


def _tx3d_notify_admin(uid, text):
    if not uid or _bot_instance is None:
        return
    try:
        asyncio.get_running_loop().create_task(_bot_instance.send_message(uid, text))
    except Exception as e:
        print(f"[tx3d] không gửi được thông báo admin: {e}")


async def tx3d_loop():
    G = TX3D
    await asyncio.to_thread(_tx3d_boot_sync)
    G.ready = True
    print(f"✅ Miniapp {TX3D_NAME}: sẵn sàng (hũ {G.pot:,}đ, phiên kế tiếp #{G.round_id + 1})")
    test = False
    while True:
        try:
            async with _tx3d_lock():
                G.round_id += 1
                G.phase, G.bets, G.dice, G.result, G.applied = "bet", {}, None, None, False
                G.phase_end = time.time() + TX3D_BET_SECONDS
            await asyncio.sleep(max(0.0, G.phase_end - time.time()))

            async with _tx3d_lock():
                dice, test = _tx3d_take_dice()
                G.dice = dice
                G.result = _tx3d_compute(dice, G.bets, G.round_id, G.pot)
                G.phase = "cover"
                G.phase_end = time.time() + TX3D_COVER_SECONDS
            await asyncio.sleep(max(0.0, G.phase_end - time.time()))

            async with _tx3d_lock():
                G.applied = True
                rid, res, bets = G.round_id, G.result, dict(G.bets)
                await asyncio.to_thread(_tx3d_apply_sync, rid, bets, res, test)
                G.pot = res["pot_after"]
                if not test:
                    G.hist.insert(0, list(res["dice"]))
                    del G.hist[TX3D_HIST_MAX:]
                G.last = {"id": rid, "dice": list(res["dice"]), "win": res["win"], "jp": res["jp"],
                          "bets": {u: {b["side"]: b["amt"]} for u, b in bets.items()},
                          "nets": dict(res["nets"]), "t": time.time()}
                for u in bets:
                    G.users.pop(u, None)      # buộc đọc lại số dư mới
        except asyncio.CancelledError:
            raise
        except Exception as e:
            print(f"[tx3d] lỗi vòng lặp: {e}")
            traceback.print_exc()
            try:
                if G.bets and not G.applied:
                    G.applied = True
                    await asyncio.to_thread(_tx3d_refund_sync, G.round_id, dict(G.bets))
                    G.bets = {}
            except Exception as e2:
                print(f"[tx3d] lỗi hoàn cược sau sự cố: {e2}")
            await asyncio.sleep(3)


# ---------- API ----------
def _tx3d_json(data, status=200):
    return web.json_response(data, status=status, headers={"Cache-Control": "no-store"})


def _tx3d_state(uid, bal, mt):
    G, now = TX3D, time.time()
    tot = {"tai": [0, 0], "xiu": [0, 0]}
    for b in G.bets.values():
        tot[b["side"]][0] += b["amt"]
        tot[b["side"]][1] += 1
    mine = G.bets.get(uid)
    st = {"id": G.round_id, "phase": G.phase, "left": round(max(0.0, G.phase_end - now), 2),
          "bal": bal, "pot": G.pot, "tot": tot,
          "my": {mine["side"]: mine["amt"]} if mine else {},
          "hist": G.hist, "mt": 1 if mt else 0}
    if G.phase == "cover" and G.result:
        st["dice"] = G.dice
        st["win"] = G.result["win"]
        st["net"] = G.result["nets"].get(uid, 0)
        st["jp"] = _tx3d_jp_view(G.result["jp"], uid)
        st["pot_add"] = int(G.result.get("pot_add", 0))   # tiền vừa cộng vào hũ phiên này (hiện "+X")
    L = G.last
    if L and now - L["t"] < 60:
        st["last"] = {"id": L["id"], "dice": L["dice"], "win": L["win"], "my": L["bets"].get(uid, {}),
                      "net": L["nets"].get(uid, 0), "jp": _tx3d_jp_view(L["jp"], uid), "ago": int(now - L["t"])}
    return st


async def tx3d_api_state(request):
    me = _tx3d_auth(request)
    if not me:
        return _tx3d_json({"err": 1, "msg": "Hãy mở từ nút trong bot Telegram"})
    uid, _name = me
    if not TX3D.ready:
        return _tx3d_json({"err": 1, "msg": "Game đang khởi động, thử lại sau vài giây"})
    flags, info = await _tx3d_flags(), await _tx3d_user(uid)
    if info is None:
        return _tx3d_json({"err": 1, "msg": "Không tìm thấy tài khoản, hãy gửi /start cho bot"})
    bal, banned, gban = info
    is_admin = uid in ADMIN_IDS
    if (banned or gban) and not is_admin:
        return _tx3d_json({"err": 1, "msg": "Tài khoản của bạn đã bị khóa"})
    if (flags.get("mt_tongbao") == "1" or flags.get("system_maintenance") == "1") and not is_admin:
        return _tx3d_json({"err": 1, "msg": "Hệ thống đang bảo trì, vui lòng quay lại sau"})
    mt = flags.get(TX3D_MT_KEY) == "1" and not is_admin
    return _tx3d_json(_tx3d_state(uid, bal, mt))


async def tx3d_api_bet(request):
    me = _tx3d_auth(request)
    if not me:
        return _tx3d_json({"err": "Hãy mở từ nút trong bot Telegram"})
    uid, name = me
    try:
        body = await request.json()
        side = str(body.get("side", "")).lower()
        amt = int(body.get("amt", 0))
    except Exception:
        return _tx3d_json({"err": "Dữ liệu cược không hợp lệ"})
    if side not in ("tai", "xiu"):
        return _tx3d_json({"err": "Cửa cược không hợp lệ"})
    if amt < TX3D_MIN_BET:
        return _tx3d_json({"err": f"Cược tối thiểu {fmt_money(TX3D_MIN_BET)}đ"})
    if amt > TX3D_MAX_BET:
        return _tx3d_json({"err": "Số tiền cược quá lớn"})
    if not TX3D.ready:
        return _tx3d_json({"err": "Game đang khởi động, thử lại sau vài giây"})
    flags = await _tx3d_flags()
    is_admin = uid in ADMIN_IDS
    if not is_admin:
        if flags.get(TX3D_MT_KEY) == "1":
            return _tx3d_json({"err": "Game Tài Xỉu 3D đang bảo trì"})
        if flags.get("mt_tongbao") == "1" or flags.get("system_maintenance") == "1":
            return _tx3d_json({"err": "Hệ thống đang bảo trì"})
    info = await _tx3d_user(uid, fresh=True)
    if info is None:
        return _tx3d_json({"err": "Không tìm thấy tài khoản"})
    if (info[1] or info[2]) and not is_admin:
        return _tx3d_json({"err": "Tài khoản của bạn đã bị khóa"})
    if not is_admin and not await asyncio.to_thread(has_bank_linked, uid):
        return _tx3d_json({"err": "Bạn cần liên kết ngân hàng (/lienket) trước khi chơi"})
    async with _tx3d_lock():
        G = TX3D
        if G.phase != "bet" or time.time() >= G.phase_end - 0.25:
            return _tx3d_json({"err": "Đã hết giờ đặt cược"})
        cur = G.bets.get(uid)
        if cur and cur["side"] != side:
            return _tx3d_json({"err": "Mỗi phiên chỉ cược một cửa"})
        rid = G.round_id
        new_bal = await asyncio.to_thread(_tx3d_sub_sync, uid, amt, f"Cược Tài Xỉu 3D {side.upper()}")
        if new_bal is None:
            return _tx3d_json({"err": "Số dư không đủ"})
        total = (cur["amt"] if cur else 0) + amt
        G.bets[uid] = {"side": side, "amt": total, "name": name}
        await asyncio.to_thread(
            query,
            "INSERT INTO tx3d_bets(round_id,user_id,side,amount) VALUES(%s,%s,%s,%s) "
            "ON CONFLICT (round_id,user_id) DO UPDATE SET amount=EXCLUDED.amount, side=EXCLUDED.side",
            (rid, uid, side, total))
        TX3D.users[uid] = (time.time(), new_bal, info[1], info[2])
    try:
        update_bet_progress(uid, amt)       # tiến độ vòng cược khuyến mãi (giống các game khác)
    except Exception as e:
        print(f"[tx3d] lỗi cập nhật vòng cược: {e}")
    return _tx3d_json({"ok": 1, "bal": new_bal})


TX3D_MUSIC_FILES = ["cuoi-luan-duoc-khong.mp3", "thuyen-hoa.mp3", "son-thuy-trung-may.mp3", "tuong-tu-nang-ca-si.mp3"]


async def tx3d_music_list(request):
    d = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music")
    have = [f for f in TX3D_MUSIC_FILES if os.path.isfile(os.path.join(d, f))]
    return _tx3d_json({"tracks": [f"/music/{f}" for f in have]})


async def tx3d_music_file(request):
    name = request.match_info.get("name", "")
    if name not in TX3D_MUSIC_FILES:
        return web.Response(status=404, text="Not found")
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "music", name)
    if not os.path.isfile(path):
        return web.Response(status=404, text="Chưa có file nhạc " + name)
    return web.FileResponse(path, headers={"Cache-Control": "public, max-age=86400"})


async def tx3d_page(request):
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
    if not os.path.exists(path):
        return web.Response(status=404, text="Không tìm thấy index.html (hãy đặt cùng thư mục với main_9.py)")
    return web.FileResponse(path, headers={"Cache-Control": "no-cache"})


def tx3d_register_routes(app):
    app.router.add_get("/app", tx3d_page)
    app.router.add_get("/app/", tx3d_page)
    app.router.add_get("/api/music", tx3d_music_list)
    app.router.add_get("/music/{name}", tx3d_music_file)
    app.router.add_get("/api/state", tx3d_api_state)
    app.router.add_post("/api/bet", tx3d_api_bet)


# ---------- lệnh admin ----------
def _tx3d_parse_money(raw):
    s = (raw or "").strip().lower().replace(" ", "")
    mult = 1
    for suf, m in (("tỷ", 10 ** 9), ("ty", 10 ** 9), ("tr", 10 ** 6), ("m", 10 ** 6), ("k", 10 ** 3)):
        if s.endswith(suf):
            s, mult = s[: -len(suf)], m
            break
    if mult == 1:
        s = s.replace(".", "").replace(",", "")
    else:
        s = s.replace(",", ".")
    return int(round(float(s) * mult))


@admin_only
async def hu_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not ctx.args:
        return await msg.reply_text(
            f'{ce("🎁")} <b>HŨ {TX3D_NAME}</b>\n\n'
            f'{ce("💰")} Hiện tại: <code>{fmt_money(TX3D.pot)}đ</code>\n\n'
            f'{ce("✍️")} <b>Cú pháp:</b> <code>/hu [số_tiền]</code>\n'
            f'VD: <code>/hu 50000000</code> · <code>/hu 50m</code> · <code>/hu 1.5tỷ</code>',
            parse_mode=ParseMode.HTML)
    try:
        amount = _tx3d_parse_money(ctx.args[0])
    except ValueError:
        return await msg.reply_text(f'{ce("❌")} Số tiền không hợp lệ! VD: <code>/hu 50m</code>', parse_mode=ParseMode.HTML)
    if amount < 0 or amount > 10 ** 13:
        return await msg.reply_text(f'{ce("❌")} Số tiền phải từ 0 đến 10 nghìn tỷ!', parse_mode=ParseMode.HTML)
    old = TX3D.pot
    TX3D.pot = amount
    set_setting(TX3D_POT_KEY, amount)
    await msg.reply_text(
        f'{ce("✅")} <b>ĐÃ CẬP NHẬT HŨ {TX3D_NAME}</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("📊")} <b>Số cũ:</b> <code>{fmt_money(old)}đ</code>\n'
        f'{ce("💰")} <b>Số mới:</b> <code>{fmt_money(amount)}đ</code>\n'
        f'━━━━━━━━━━━━━━━━━━━━━', parse_mode=ParseMode.HTML)


async def ep_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/ep 1 3 4 | /ep t | /ep x | /ep off  — admin ép kết quả phiên kế tiếp, kể cả khi có người chơi thật cược."""
    uid = update.effective_user.id
    msg = update.effective_message
    if uid not in ADMIN_IDS or is_admin_banned(uid):
        return
    if update.effective_chat.type != "private":     # không để lộ lệnh trong nhóm
        try:
            await msg.delete()
        except Exception:
            pass
        return
    args = [a.strip().lower() for a in (ctx.args or []) if a.strip()]
    nxt = TX3D.round_id if TX3D.phase == "bet" else TX3D.round_id + 1
    note = "\n\n<i>Áp dụng cho phiên kế tiếp kể cả khi đã có người chơi thật cược (vẫn trả thưởng và ghi vào cầu bình thường).</i>"
    if not args:
        cur = TX3D.force
        cur_txt = "không có"
        if cur:
            cur_txt = " ".join(map(str, cur["dice"])) if cur["dice"] else ("TÀI" if cur["kind"] == "tai" else "XỈU")
        return await msg.reply_text(
            f'{ce("🛠")} <b>ÉP KẾT QUẢ {TX3D_NAME}</b>\n'
            f'• <code>/ep 1 3 4</code> — ra 1-3-4\n'
            f'• <code>/ep t</code> — ra Tài · <code>/ep x</code> — ra Xỉu\n'
            f'• <code>/ep off</code> — huỷ\n\n'
            f'Đang chờ: <b>{cur_txt}</b>' + note, parse_mode=ParseMode.HTML)
    if args[0] in ("off", "huy", "hủy", "0"):
        TX3D.force = None
        return await msg.reply_text(f'{ce("✅")} Đã huỷ ép kết quả.', parse_mode=ParseMode.HTML)
    forced = None
    if args[0] in ("t", "tai", "tài"):
        forced = {"dice": None, "kind": "tai", "by": uid}
        label = "TÀI"
    elif args[0] in ("x", "xiu", "xỉu"):
        forced = {"dice": None, "kind": "xiu", "by": uid}
        label = "XỈU"
    else:
        digits = [c for a in args for c in a if not c.isspace()]
        if len(digits) == 3 and all(c in "123456" for c in digits):
            d = [int(c) for c in digits]
            forced = {"dice": d, "kind": None, "by": uid}
            label = " - ".join(map(str, d))
    if not forced:
        return await msg.reply_text(
            f'{ce("❌")} Cú pháp: <code>/ep 1 3 4</code> · <code>/ep t</code> · <code>/ep x</code> · <code>/ep off</code>',
            parse_mode=ParseMode.HTML)
    TX3D.force = forced
    await msg.reply_text(f'{ce("✅")} Đã ép kết quả <b>{label}</b> cho phiên <b>#{nxt}</b>.' + note,
                         parse_mode=ParseMode.HTML)


# ================= TẮT GAME CŨ (chỉ giữ Tài Xỉu Room + Tài Xỉu 3D + game hoạt ảnh Telegram mới) =================
def _legacy_off(_fn):
    async def _w(update, ctx, *a, **k):
        try:
            return await update.effective_message.reply_text(
                f'{ce("🚫")} Game này đã ngừng hoạt động.\nBấm <b>DANH SÁCH GAME</b> để chọn game mới nhé!',
                parse_mode=ParseMode.HTML)
        except Exception as _e:
            print(f"[legacy-game] {_e}")
    return _w

for _n in ("play_xucxac_don", "play_longho", "play_minipoker", "play_baccarat",
           "play_xocdia4", "play_taixiumd5", "play_baucua", "play_xocdia6"):
    if _n in globals():
        globals()[_n] = _legacy_off(globals()[_n])

# ================= GAME HOẠT ẢNH TELEGRAM (send_dice: 🎯 🏀 ⚽ 🎳 🎰 🎲) =================
# Kết quả do chính Telegram sinh ngẫu nhiên (dice.value) -> bot không can thiệp được.
# Mỗi bet: (nhãn, mã, icon, tỷ lệ thưởng, mô tả điều kiện, hàm kiểm tra danh sách điểm)
def _goals(v):
    return sum(1 for x in v if x >= 3)

SLOT_SYM = ["BAR", "NHO", "CHANH", "7️⃣"]

def _slot_reels(value):
    x = int(value) - 1
    return [x & 3, (x >> 2) & 3, (x >> 4) & 3]

def _slot_eval(value):
    r = _slot_reels(value)
    if r[0] == r[1] == r[2]:
        return (25.0, "JACKPOT 777") if r[0] == 3 else (7.0, f"BA {SLOT_SYM[r[0]]} GIỐNG NHAU")
    if r.count(3) == 2:
        return 1.5, "HAI SỐ 7"
    return 0, "KHÔNG TRÚNG"

TGDICE = {
    "pt": {
        "key": "mt_phitieu", "gid": 12, "name": "PHI TIÊU", "note": "Phi Tiêu", "icon": "🎯",
        "dice": "🎯", "n": 1, "wait": 3.8, "aliases": ("phitieu", "darts"),
        "intro": "Telegram phóng 1 phi tiêu vào bia: <b>điểm 6 = HỒNG TÂM</b>, <b>điểm 1 = trượt bia</b>.",
        "bets": [
            ("HỒNG TÂM", "hong", "🎯", 5.5, "điểm 6", lambda v: v[0] == 6),
            ("TRƯỢT BIA", "truot", "❌", 5.5, "điểm 1", lambda v: v[0] == 1),
            ("TRÚNG BIA", "bia", "✅", 1.45, "điểm 2–5", lambda v: 2 <= v[0] <= 5),
        ],
        "show": lambda v: f'{ce("🎯")} Điểm phi tiêu: <b>{v[0]}</b> · <b>' + ("HỒNG TÂM" if v[0] == 6 else "TRƯỢT BIA" if v[0] == 1 else "TRÚNG BIA") + '</b>',
    },
    "br": {
        "key": "mt_bongro", "gid": 13, "name": "BÓNG RỔ", "note": "Bóng Rổ", "icon": "🏀",
        "dice": "🏀", "n": 1, "wait": 4.2, "aliases": ("bongro", "basket"),
        "intro": "Telegram ném 1 quả bóng rổ: <b>điểm 4–5 = vào rổ</b>, điểm 3 = kẹt vành, điểm 1–2 = trượt.",
        "bets": [
            ("VÀO RỔ", "vao", "🔥", 2.35, "điểm 4–5", lambda v: v[0] in (4, 5)),
            ("TRƯỢT", "truot", "❌", 2.35, "điểm 1–2", lambda v: v[0] in (1, 2)),
            ("KẸT VÀNH", "ket", "🍀", 4.7, "điểm 3", lambda v: v[0] == 3),
        ],
        "show": lambda v: f'{ce("🏀")} Điểm bóng rổ: <b>{v[0]}</b> · <b>' + ("VÀO RỔ" if v[0] in (4, 5) else "KẸT VÀNH" if v[0] == 3 else "TRƯỢT") + '</b>',
    },
    "bd": {
        "key": "mt_bongda", "gid": 14, "name": "BÓNG ĐÁ", "note": "Bóng Đá", "icon": "⚽",
        "dice": "⚽", "n": 1, "wait": 4.2, "aliases": ("bongda", "football"),
        "intro": "Telegram sút 1 quả bóng: <b>điểm 3–5 = VÀO LƯỚI</b>, điểm 1–2 = trượt.",
        "bets": [
            ("VÀO LƯỚI", "vao", "🏆", 1.55, "điểm 3–5", lambda v: v[0] >= 3),
            ("TRƯỢT", "truot", "❌", 2.3, "điểm 1–2", lambda v: v[0] <= 2),
        ],
        "show": lambda v: f'{ce("⚽")} Điểm bóng đá: <b>{v[0]}</b> · <b>' + ("VÀO LƯỚI" if v[0] >= 3 else "TRƯỢT") + '</b>',
    },
    "bl": {
        "key": "mt_bowling", "gid": 15, "name": "BOWLING", "note": "Bowling", "icon": "🎳",
        "dice": "🎳", "n": 1, "wait": 4.2, "aliases": ("bowling", "bowl"),
        "intro": "Telegram lăn 1 quả bowling: <b>điểm 6 = STRIKE</b>, điểm 1 = trượt hết.",
        "bets": [
            ("STRIKE", "strike", "🔥", 5.5, "điểm 6", lambda v: v[0] == 6),
            ("TRƯỢT HẾT", "truot", "❌", 5.5, "điểm 1", lambda v: v[0] == 1),
            ("ĐỔ NHIỀU", "nhieu", "⬆️", 2.8, "điểm 4–5", lambda v: v[0] in (4, 5)),
            ("ĐỔ ÍT", "it", "⬇️", 2.8, "điểm 2–3", lambda v: v[0] in (2, 3)),
        ],
        "show": lambda v: f'{ce("🎳")} Điểm bowling: <b>{v[0]}</b> · <b>' + ("STRIKE" if v[0] == 6 else "TRƯỢT HẾT" if v[0] == 1 else "ĐỔ NHIỀU" if v[0] in (4, 5) else "ĐỔ ÍT") + '</b>',
    },
    "sl": {
        "key": "mt_slot", "gid": 16, "name": "QUAY HŨ", "note": "Quay Hũ", "icon": "🎰",
        "dice": "🎰", "n": 1, "wait": 3.4, "aliases": ("slot", "quayhu", "hu"),
        "intro": "Kéo máy quay hũ 3 cuộn của Telegram — chỉ cần bấm mức cược là quay!",
        "bets": None,
        "extra": [
            f'• {ce("💎")} <b>7️⃣ 7️⃣ 7️⃣ — JACKPOT</b> — <b>x25</b>',
            f'• {ce("🍀")} <b>3 hình giống nhau</b> (BAR / NHO / CHANH) — <b>x7</b>',
            f'• {ce("⭐")} <b>Hai số 7</b> — <b>x1.5</b>',
        ],
        "show": lambda v: f'{ce("🎰")} Cuộn: <b>' + " · ".join(SLOT_SYM[r] for r in _slot_reels(v[0])) + f'</b>\n{ce("🎯")} Kết quả: <b>{_slot_eval(v[0])[1]}</b>',
    },
    "xxd": {
        "key": "mt_xucxacdoi", "gid": 17, "name": "XÚC XẮC ĐÔI", "note": "Xúc Xắc Đôi", "icon": "🎲",
        "dice": "🎲", "n": 2, "wait": 3.8, "aliases": ("xucxacdoi", "2dice"),
        "intro": "Telegram tung <b>2 viên xúc xắc</b>, tính tổng điểm (2–12).",
        "bets": [
            ("TÀI", "tai", "⬆️", 2.3, "tổng 8–12", lambda v: sum(v) >= 8),
            ("XỈU", "xiu", "⬇️", 2.3, "tổng 2–6", lambda v: sum(v) <= 6),
            ("BẢY", "bay", "7️⃣", 5.5, "tổng đúng 7", lambda v: sum(v) == 7),
        ],
        "show": lambda v: f'{ce("🎲")} Xúc xắc: <b>{v[0]}</b> + <b>{v[1]}</b> = <b>{sum(v)}</b>',
    },
    "pk": {
        "key": "mt_dopk", "gid": 18, "name": "ĐỌ XÚC XẮC", "note": "Đọ Xúc Xắc", "icon": "⚔️",
        "dice": "🎲", "n": 2, "wait": 3.8, "aliases": ("dopk", "pk"),
        "intro": "Bạn và <b>NHÀ CÁI</b> mỗi bên tung 1 viên xúc xắc — <b>điểm cao hơn thắng</b>!",
        "bets": None,
        "extra": [
            f'• {ce("🏆")} <b>Bạn cao điểm hơn</b> — <b>x1.9</b>',
            f'• {ce("⚖️")} <b>Hòa điểm</b> — hoàn tiền cược',
            f'• {ce("🎲")} Viên xúc xắc <b>trên</b> là của bạn, viên <b>dưới</b> là của nhà cái.',
        ],
        "show": lambda v: f'{ce("🎲")} BẠN: <b>{v[0]}</b>  {ce("⚔️")}  NHÀ CÁI: <b>{v[1]}</b>',
    },
    "ll": {
        "key": "mt_luanluu", "gid": 19, "name": "LUÂN LƯU", "note": "Luân Lưu", "icon": "⚽",
        "dice": "⚽", "n": 3, "wait": 4.4, "aliases": ("luanluu", "penalty"),
        "intro": "Sút <b>3 quả luân lưu</b> liên tiếp — đoán xem bạn ghi được mấy bàn (mỗi quả điểm 3–5 là vào).",
        "bets": [
            ("3/3 VÀO", "hat", "🏆", 4.3, "ghi đủ 3 bàn", lambda v: _goals(v) == 3),
            ("TỪ 2 VÀO", "kha", "✅", 1.45, "ghi ≥ 2 bàn", lambda v: _goals(v) >= 2),
            ("TỪ 1 TRỞ XUỐNG", "kem", "❌", 2.6, "ghi ≤ 1 bàn", lambda v: _goals(v) <= 1),
        ],
        "show": lambda v: f'{ce("⚽")} Điểm 3 quả: <b>{v[0]}</b> · <b>{v[1]}</b> · <b>{v[2]}</b>\n{ce("🎯")} Ghi được: <b>{_goals(v)}/3</b> bàn',
    },
}

def _tg_rows(c):
    if not c.get("bets"):
        return None
    btns = [(f"{lb} (x{m:g})", cd, em) for lb, cd, em, m, _r, _p in c["bets"]]
    return [btns[i:i + 2] for i in range(0, len(btns), 2)]

def _tg_rules(g):
    c = TGDICE[g]
    lines = [f'{ce(c["icon"])} <b>{c["name"]}</b> {ce("✨")}',
             '━━━━━━━━━━━━━━━━━━━━',
             f'{ce("🎮")} {c["intro"]}', '']
    if c.get("bets"):
        lines.append(f'{ce("📊")} <b>CỬA CƯỢC &amp; TỶ LỆ THƯỞNG</b>')
        for lb, cd, em, m, rng, _p in c["bets"]:
            lines.append(f'• {ce(em)} <b>{lb}</b> <i>({rng})</i> — <b>x{m:g}</b>')
    else:
        lines.append(f'{ce("📊")} <b>BẢNG THƯỞNG</b>')
        lines.extend(c["extra"])
    lines.append('')
    lines.append(f'{ce("💡")} Hoạt ảnh &amp; kết quả do <b>Telegram</b> quyết định ngẫu nhiên, thắng là nhận tiền ngay.')
    return "\n".join(lines)

def _tg_bet(g, code):
    for b in TGDICE[g].get("bets") or []:
        if b[1] == code:
            return b
    return None

def _tg_eval(g, code, vals):
    """Trả về (kết_quả 'win'/'lose'/'push', hệ_số)."""
    if g == "sl":
        m, _t = _slot_eval(vals[0])
        return ("win", m) if m else ("lose", 0)
    if g == "pk":
        if vals[0] > vals[1]:
            return "win", 1.9
        return ("push", 1) if vals[0] == vals[1] else ("lose", 0)
    b = _tg_bet(g, code)
    if b and b[5](vals):
        return "win", b[3]
    return "lose", 0

async def play_tgdice(update, ctx, g, code, amount):
    c = TGDICE[g]
    msg = update.effective_message
    uid = update.effective_user.id
    if is_banned(uid):
        return await msg.reply_text(f'{ce("🚫")} Bạn đã bị khóa tài khoản!', parse_mode=ParseMode.HTML)
    if is_game_banned(uid, c["gid"]):
        return await msg.reply_text(f'{ce("🚫")} Bạn đã bị cấm chơi trò chơi này!', parse_mode=ParseMode.HTML)
    if not has_bank_linked(uid):
        return await msg.reply_text(BANK_LINK_REQUIRED_MSG, parse_mode=ParseMode.HTML)
    if check_mt(c["key"]) and uid not in ADMIN_IDS:
        return await msg.reply_text(f'{ce("⚙️")} Game {c["name"].title()} đang bảo trì!', parse_mode=ParseMode.HTML)
    bet = _tg_bet(g, code)
    if c.get("bets") and not bet:
        return await msg.reply_text(f'{ce("❌")} Cửa cược không hợp lệ!', parse_mode=ParseMode.HTML)
    if amount < 1000:
        return await msg.reply_text(f'{ce("❌")} Số tiền cược tối thiểu là 1.000đ!', parse_mode=ParseMode.HTML)
    note = f'{c["note"]} {bet[0]}' if bet else c["note"]
    if not sub_money(uid, amount, f"Cược {note}"):
        return await msg.reply_text(f'{ce("❌")} Bạn không đủ số dư.', parse_mode=ParseMode.HTML)
    _bal0 = bal_pre(uid)

    # ---- tung xúc xắc hoạt ảnh Telegram ----
    vals = []
    try:
        head = (f'{ce(c["icon"])} <b>{c["name"]}</b>\n'
                f'━━━━━━━━━━━━━━━━━━━━\n')
        if bet:
            head += f'{ce("🎟")} Cửa: <b>{bet[0]}</b> · <b>x{bet[3]:g}</b>\n'
        head += f'{ce("💵")} Cược: <code>{fmt_money(amount)}đ</code>'
        await msg.reply_text(head, parse_mode=ParseMode.HTML)
        for i in range(c["n"]):
            d = await msg.reply_dice(emoji=c["dice"])
            vals.append(int(d.dice.value))
            if i < c["n"] - 1:
                await asyncio.sleep(0.6)
        await asyncio.sleep(c["wait"])
    except Exception as e:
        print(f"Lỗi play_tgdice {g}: {e}")
        add_money(uid, amount, f"Hoàn tiền Game Telegram - lỗi {c['note']}")
        return await msg.reply_text(
            f'{ce("⚠️")} Có lỗi khi tung, đã hoàn lại tiền cược!\n{bal_pair(_bal0, uid)}', parse_mode=ParseMode.HTML)

    # ---- trả thưởng ----
    outcome, mult = _tg_eval(g, code, vals)
    if outcome == "win":
        win_amt = int(amount * mult)
        add_money(uid, win_amt, f"Thắng {note}")
        status = (f'{ce("🎉")} <b>THẮNG!</b> Nhận <code>+{fmt_money(win_amt)}đ</code>\n'
                  f'{ce("💎")} Lãi: <code>+{fmt_money(win_amt - amount)}đ</code> · <b>x{mult:g}</b>')
    elif outcome == "push":
        add_money(uid, amount, f"Hoàn tiền Game Telegram - Hòa {c['note']}")
        status = f'{ce("⚖️")} <b>HÒA!</b> Hoàn lại <code>{fmt_money(amount)}đ</code>'
    else:
        status = f'{ce("❌")} <b>THUA</b> · <code>-{fmt_money(amount)}đ</code>'

    res = (f'{ce(c["icon"])} <b>KẾT QUẢ {c["name"]}</b>\n'
           f'━━━━━━━━━━━━━━━━━━━━\n'
           f'{c["show"](vals)}\n')
    if bet:
        res += f'{ce("🎟")} Bạn chọn: <b>{bet[0]}</b>\n'
    res += (f'{ce("💵")} Tiền cược: <code>{fmt_money(amount)}đ</code>\n'
            f'━━━━━━━━━━━━━━━━━━━━\n'
            f'{status}\n\n'
            f'{bal_pair(_bal0, uid)}')
    kb = InlineKeyboardMarkup([
        [btn(f"CHƠI LẠI {fmt_money(amount)}đ", "🔄", callback_data=f"gb_{g}_{code}_{amount}")],
        [btn("ĐỔI CỬA", "🎮", callback_data=f"gm_{g}"), btn("DANH SÁCH", "🏆", callback_data="game_list")],
    ])
    try:
        await msg.reply_text(res, reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"Lỗi gửi kết quả {g}: {e}")

# ---- đăng ký bảo trì / khởi tạo cờ cho game mới ----
for _g, _c in TGDICE.items():
    MT_ITEMS[_c["key"]] = {'name': _c["name"], 'type': 'game', 'icon': _c["icon"]}
    if not query("SELECT 1 FROM settings WHERE key=%s", (_c["key"],)):
        query("INSERT INTO settings(key, value) VALUES(%s, '0') ON CONFLICT (key) DO NOTHING", (_c["key"],))

def _tgdice_mt_rows(st, ic):
    items = list(TGDICE.values())
    rows = []
    for i in range(0, len(items), 2):
        rows.append([btn(f"{x['name'].title()}: {st(x['key'])}", ic(x['key']), callback_data=f"tg_{x['key']}") for x in items[i:i + 2]])
    return rows



# ================= GAME MỞ RỘNG: XÚC XẮC TELE / BẦU CUA / SOLO =================
SOLO_ROOMS = {}
SOLO_ROOM_LOCK = asyncio.Lock()
SOLO_GROUP_IDS = list(GROUP_IDS)
TELE_DICE_CHOICES = {"xxc": {2, 4, 6}, "xxl": {1, 3, 5}, "xxt": {4, 5, 6}, "xxx": {1, 2, 3}}
BAUCUA_CHOICES = {
    "bau": ("BẦU", "🍐"), "tom": ("TÔM", "🦐"), "cua": ("CUA", "🦀"),
    "ca": ("CÁ", "🐟"), "ga": ("GÀ", "🐓"), "nai": ("NAI", "🦌")
}
BAUCUA_FACE = {1: "bau", 2: "tom", 3: "cua", 4: "ca", 5: "ga", 6: "nai"}
KBB_CHOICES = {"keo": "✂️ KÉO", "bua": "🪨 BÚA", "bao": "📄 BAO"}
KBB_BEATS = {"keo": "bao", "bua": "keo", "bao": "bua"}
SOLO_MIN, SOLO_MAX = 2000, 1000000


def _solo_mask_id(uid):
    value = str(int(uid))
    return "*" * min(5, len(value)) + value[5:]


def _solo_kb(room_id):
    return InlineKeyboardMarkup([
        [btn("VÀO PHÒNG SOLO", "🎮", callback_data=f"pvp:join:{room_id}")],
        [btn("HỦY PHÒNG", "❌", callback_data=f"pvp:cancel:{room_id}")]
    ])


async def _solo_create(update, ctx, game):
    msg, user = update.effective_message, update.effective_user
    args = ctx.args or []
    cmd = "/soloxd" if game == "dice" else "/solokbb"
    if not args:
        return await msg.reply_text(
            f'{ce("🎮")} Cú pháp: <code>{cmd} [số_tiền]</code>\n'
            f'Ví dụ: <code>{cmd} 20000</code>\n'
            f'Mức cược: 2.000đ - 1.000.000đ/người',
            parse_mode=ParseMode.HTML)
    try:
        amount = int(args[0].replace(",", "").replace(".", ""))
    except ValueError:
        return await msg.reply_text("Số tiền không hợp lệ.")
    if not SOLO_MIN <= amount <= SOLO_MAX:
        return await msg.reply_text("Mức cược từ 2.000đ đến 1.000.000đ/người.")
    if is_banned(user.id) and user.id not in ADMIN_IDS:
        return await msg.reply_text("Tài khoản của bạn đã bị khóa.")
    if not has_bank_linked(user.id):
        return await msg.reply_text(BANK_LINK_REQUIRED_MSG, parse_mode=ParseMode.HTML)
    if get_balance(user.id) < amount:
        return await msg.reply_text("Số dư không đủ để tạo phòng.")
    room_id = str(random.randint(100000, 999999))
    async with SOLO_ROOM_LOCK:
        while room_id in SOLO_ROOMS:
            room_id = str(random.randint(100000, 999999))
        SOLO_ROOMS[room_id] = {
            "game": game, "owner": user.id, "amount": amount, "status": "open",
            "owner_name": html.escape(user.full_name or str(user.id))
        }
    title = "SOLO XÚC XẮC" if game == "dice" else "SOLO KÉO BÚA BAO"
    text = (
        f'{ce("🎮")} <b>{title} - PHÒNG ĐANG MỞ</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("💰")} Tiền solo: <code>{fmt_money(amount)}đ/người</code>\n'
        f'{ce("👤")} Người tạo: <b>{html.escape(user.full_name or "Người chơi")}</b>\n'
        f'{ce("🆔")} ID: <code>{_solo_mask_id(user.id)}</code>\n'
        f'{ce("🏆")} Tỷ lệ trả thưởng: <b>x1.95</b>\n\n'
        f'{ce("👇")} Bấm nút bên dưới để vào thách đấu!'
    )
    targets = SOLO_GROUP_IDS or ([msg.chat_id] if msg.chat.type != "private" else [])
    posted = 0
    for gid in targets:
        try:
            notice = await ctx.bot.send_message(gid, text, parse_mode=ParseMode.HTML, reply_markup=_solo_kb(room_id))
            try:
                await ctx.bot.pin_chat_message(gid, notice.message_id, disable_notification=True)
            except Exception as e:
                print(f"[solo] Không ghim được tin nhóm {gid}: {e}")
            posted += 1
        except Exception as e:
            print(f"[solo] Không đăng được phòng vào nhóm {gid}: {e}")
    if not posted:
        SOLO_ROOMS.pop(room_id, None)
        return await msg.reply_text(
            'Không đăng được thông báo vào nhóm. Kiểm tra bot có quyền gửi và ghim tin nhắn.',
            parse_mode=ParseMode.HTML)
    await msg.reply_text(
        f'{ce("✅")} Đã tạo phòng <b>{title}</b>!\n'
        f'{ce("💰")} Tiền solo: <code>{fmt_money(amount)}đ/người</code>\n'
        f'{ce("🆔")} Mã phòng: <code>{room_id}</code>\n'
        f'{ce("📌")} Bot đã đăng thông báo và ghim tin trong nhóm.',
        parse_mode=ParseMode.HTML)


async def _solo_join_by_code(update, ctx, room_id, expected_game):
    msg, user = update.effective_message, update.effective_user
    room_id = str(room_id).strip()
    async with SOLO_ROOM_LOCK:
        room = SOLO_ROOMS.get(room_id)
        if not room or room.get("status") != "open":
            return await msg.reply_text("Phòng không tồn tại hoặc đã đóng.")
        if room.get("game") != expected_game:
            return await msg.reply_text("Mã phòng không thuộc trò chơi này.")
        if user.id == room["owner"]:
            return await msg.reply_text("Bạn không thể tự vào phòng của mình.")
        if is_banned(user.id) and user.id not in ADMIN_IDS:
            return await msg.reply_text("Tài khoản đã bị khóa.")
        if not has_bank_linked(user.id):
            return await msg.reply_text(BANK_LINK_REQUIRED_MSG, parse_mode=ParseMode.HTML)
        amount, owner = room["amount"], room["owner"]
        if get_balance(user.id) < amount or get_balance(owner) < amount:
            return await msg.reply_text("Một trong hai người không đủ số dư.")
        if not sub_money(owner, amount, f"Cược phòng Solo #{room_id}"):
            return await msg.reply_text("Người tạo không còn đủ số dư.")
        if not sub_money(user.id, amount, f"Cược phòng Solo #{room_id}"):
            add_money(owner, amount, f"Hoàn cược phòng Solo #{room_id}")
            return await msg.reply_text("Không thể trừ tiền cược của bạn; đã hoàn tiền người tạo.")
        room["opponent"] = user.id
        room["opponent_name"] = html.escape(user.full_name or str(user.id))
        room["status"] = "choosing" if expected_game == "kbb" else "playing"
        room_copy = dict(room)

    chat_id = msg.chat_id
    if expected_game == "kbb":
        pick_kb = InlineKeyboardMarkup([[
            btn("KÉO", "✂️", callback_data=f"pvp:pick:{room_id}:keo"),
            btn("BÚA", "🪨", callback_data=f"pvp:pick:{room_id}:bua"),
            btn("BAO", "📄", callback_data=f"pvp:pick:{room_id}:bao"),
        ]])
        return await ctx.bot.send_message(
            chat_id,
            f'{ce("✊")} <b>SOLO KÉO BÚA BAO - CHỌN NƯỚC ĐI</b>\\n'
            f'{room_copy["owner_name"]} đấu với <b>{room_copy["opponent_name"]}</b>\\n'
            f'Mỗi người: <code>{fmt_money(amount)}đ</code>\\n'
            'Mỗi người chơi bấm chọn một nút bên dưới. Lựa chọn được giữ kín đến khi cả hai đã chọn.',
            parse_mode=ParseMode.HTML, reply_markup=pick_kb)

    settled = False
    try:
        await ctx.bot.send_message(chat_id,
            f'{ce("🎲")} <b>SOLO XÚC XẮC BẮT ĐẦU</b>\\n'
            f'{room_copy["owner_name"]} đấu với <b>{room_copy["opponent_name"]}</b>\\n'
            f'Mỗi người: <code>{fmt_money(amount)}đ</code>', parse_mode=ParseMode.HTML)
        one = await ctx.bot.send_dice(chat_id=chat_id, emoji="🎲")
        await asyncio.sleep(1)
        two = await ctx.bot.send_dice(chat_id=chat_id, emoji="🎲")
        a, b = one.dice.value, two.dice.value
        if a == b:
            add_money(owner, amount, f"Hoàn cược hòa Solo Xúc Xắc #{room_id}")
            add_money(user.id, amount, f"Hoàn cược hòa Solo Xúc Xắc #{room_id}")
            settled = True
            result = f'{ce("🤝")} <b>HÒA</b> - đã hoàn cược cho cả hai.'
        else:
            winner = owner if a > b else user.id
            prize = int(amount * 1.95)
            add_money(winner, prize, f"Thắng Solo Xúc Xắc #{room_id}")
            settled = True
            result = f'{ce("🏆")} Người thắng: <b>{"Người tạo phòng" if winner == owner else "Người tham gia"}</b> · Nhận <code>{fmt_money(prize)}đ</code>'
        await ctx.bot.send_message(chat_id,
            f'{ce("🎲")} <b>KẾT QUẢ SOLO XÚC XẮC</b>\\nNgười tạo: <b>{a}</b>\\nNgười tham gia: <b>{b}</b>\\n{result}',
            parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"[solo-dice-command] Lỗi trận {room_id}: {e}")
        if not settled:
            add_money(owner, amount, f"Hoàn cược lỗi Solo Xúc Xắc #{room_id}")
            add_money(user.id, amount, f"Hoàn cược lỗi Solo Xúc Xắc #{room_id}")
        try:
            await msg.reply_text("Trận đấu gặp lỗi kỹ thuật. Hệ thống đã xử lý hoàn cược nếu chưa thanh toán.")
        except Exception:
            pass
    finally:
        SOLO_ROOMS.pop(room_id, None)


async def _solo_cancel_by_code(update, ctx, room_id, expected_game):
    msg, user = update.effective_message, update.effective_user
    async with SOLO_ROOM_LOCK:
        room = SOLO_ROOMS.get(str(room_id))
        if not room or room.get("status") != "open" or room.get("game") != expected_game:
            return await msg.reply_text("Phòng không tồn tại hoặc đã đóng.")
        if user.id != room["owner"] and user.id not in ADMIN_IDS:
            return await msg.reply_text("Chỉ người tạo phòng mới được hủy.")
        SOLO_ROOMS.pop(str(room_id), None)
    return await msg.reply_text(f'{ce("🚫")} Đã hủy phòng SOLO <code>{room_id}</code>.', parse_mode=ParseMode.HTML)


async def soloxd_cmd(update, ctx):
    args = ctx.args or []
    if len(args) == 1 and args[0].isdigit() and args[0] in SOLO_ROOMS:
        return await _solo_join_by_code(update, ctx, args[0], "dice")
    return await _solo_create(update, ctx, "dice")


async def solokbb_cmd(update, ctx):
    args = ctx.args or []
    if len(args) == 1 and args[0].isdigit() and args[0] in SOLO_ROOMS:
        return await _solo_join_by_code(update, ctx, args[0], "kbb")
    return await _solo_create(update, ctx, "kbb")


async def solo_cmd(update, ctx):
    args = ctx.args or []
    if len(args) == 1 and args[0].isdigit() and args[0] in SOLO_ROOMS:
        return await _solo_join_by_code(update, ctx, args[0], "dice")
    return await _solo_create(update, ctx, "dice")


async def solo_cancel_cmd(update, ctx):
    args = ctx.args or []
    if len(args) != 1:
        return await update.effective_message.reply_text("Cú pháp: /huy [mã phòng]")
    return await _solo_cancel_by_code(update, ctx, args[0], "dice")


async def solo_kbb_cancel_cmd(update, ctx):
    args = ctx.args or []
    if len(args) != 1:
        return await update.effective_message.reply_text("Cú pháp: /huykbb [mã phòng]")
    return await _solo_cancel_by_code(update, ctx, args[0], "kbb")


async def _solo_callback(update, ctx, data):
    q = update.callback_query
    parts = data.split(":")
    if len(parts) not in (3, 4):
        return await q.answer()
    action, room_id = parts[1], parts[2]
    uid = q.from_user.id

    if action == "pick":
        if len(parts) != 4 or parts[3] not in KBB_CHOICES:
            return await q.answer("Lựa chọn không hợp lệ.", show_alert=True)
        choice = parts[3]
        async with SOLO_ROOM_LOCK:
            room = SOLO_ROOMS.get(room_id)
            if not room or room.get("status") != "choosing":
                return await q.answer("Trận đấu không còn nhận lựa chọn.", show_alert=True)
            if uid not in (room["owner"], room["opponent"]):
                return await q.answer("Bạn không phải người chơi trong phòng này.", show_alert=True)
            if uid in room.setdefault("choices", {}):
                return await q.answer("Bạn đã chọn rồi.", show_alert=True)
            room["choices"][uid] = choice
            done = len(room["choices"]) == 2
            if done:
                room["status"] = "settling"
                room_copy = dict(room)
                room_copy["choices"] = dict(room["choices"])
        await q.answer("Đã ghi nhận lựa chọn.")
        if not done:
            return await q.message.reply_text(
                f'{ce("✅")} Đã ghi nhận lựa chọn của bạn. Đang chờ người chơi còn lại.',
                parse_mode=ParseMode.HTML)
        owner, opponent, amount = room_copy["owner"], room_copy["opponent"], room_copy["amount"]
        a, b = room_copy["choices"][owner], room_copy["choices"][opponent]
        settled = False
        try:
            if a == b:
                add_money(owner, amount, f"Hoàn cược hòa Solo KBB #{room_id}")
                add_money(opponent, amount, f"Hoàn cược hòa Solo KBB #{room_id}")
                settled = True
                result = f'{ce("🤝")} <b>HÒA</b> - đã hoàn cược cho cả hai.'
            else:
                winner = owner if KBB_BEATS[a] == b else opponent
                prize = int(amount * 1.95)
                add_money(winner, prize, f"Thắng Solo Kéo Búa Bao #{room_id}")
                settled = True
                result = f'{ce("🏆")} Người thắng: <b>{"Người tạo phòng" if winner == owner else "Người tham gia"}</b> · Nhận <code>{fmt_money(prize)}đ</code>'
            await ctx.bot.send_message(
                q.message.chat_id,
                f'{ce("✊")} <b>KẾT QUẢ SOLO KÉO BÚA BAO</b>\n'
                f'Người tạo: <b>{KBB_CHOICES[a]}</b>\n'
                f'Người tham gia: <b>{KBB_CHOICES[b]}</b>\n{result}',
                parse_mode=ParseMode.HTML)
        except Exception as e:
            print(f"[solo-kbb] Lỗi xử lý phòng {room_id}: {e}")
            if not settled:
                add_money(owner, amount, f"Hoàn cược lỗi Solo KBB #{room_id}")
                add_money(opponent, amount, f"Hoàn cược lỗi Solo KBB #{room_id}")
            try:
                await ctx.bot.send_message(q.message.chat_id, "Trận đấu gặp lỗi kỹ thuật. Hệ thống đã xử lý hoàn cược nếu chưa thanh toán.")
            except Exception:
                pass
        finally:
            SOLO_ROOMS.pop(room_id, None)
        return

    async with SOLO_ROOM_LOCK:
        room = SOLO_ROOMS.get(room_id)
        if not room or room.get("status") != "open":
            return await q.answer("Phòng không còn mở.", show_alert=True)
        if action == "cancel":
            if uid != room["owner"] and uid not in ADMIN_IDS:
                return await q.answer("Chỉ người tạo phòng mới được hủy.", show_alert=True)
            SOLO_ROOMS.pop(room_id, None)
            await q.answer("Đã hủy phòng.")
            try:
                return await q.edit_message_text(
                    f'{ce("🚫")} <b>PHÒNG SOLO ĐÃ HỦY</b>', parse_mode=ParseMode.HTML)
            except Exception:
                return
        if action != "join":
            return await q.answer()
        if uid == room["owner"]:
            return await q.answer("Bạn không thể tự vào phòng của mình.", show_alert=True)
        if is_banned(uid) and uid not in ADMIN_IDS:
            return await q.answer("Tài khoản đã bị khóa.", show_alert=True)
        if not has_bank_linked(uid):
            return await q.answer("Bạn cần liên kết ngân hàng trước khi chơi.", show_alert=True)
        amount, owner, game = room["amount"], room["owner"], room["game"]
        if get_balance(uid) < amount or get_balance(owner) < amount:
            return await q.answer("Một trong hai người không đủ số dư.", show_alert=True)
        if not sub_money(owner, amount, f"Cược phòng Solo #{room_id}"):
            return await q.answer("Người tạo không còn đủ số dư.", show_alert=True)
        if not sub_money(uid, amount, f"Cược phòng Solo #{room_id}"):
            add_money(owner, amount, f"Hoàn cược phòng Solo #{room_id}")
            return await q.answer("Không thể trừ tiền cược của bạn; đã hoàn tiền người tạo.", show_alert=True)
        room["opponent"] = uid
        room["opponent_name"] = html.escape(q.from_user.full_name or str(uid))
        room["status"] = "choosing" if game == "kbb" else "playing"
        room_copy = dict(room)

    await q.answer("Đã vào phòng!")
    try:
        await q.edit_message_reply_markup(reply_markup=None)
    except Exception:
        pass
    chat_id = q.message.chat_id if q.message else (SOLO_GROUP_IDS[0] if SOLO_GROUP_IDS else None)
    if chat_id is None:
        add_money(owner, amount, f"Hoàn cược Solo #{room_id}")
        add_money(uid, amount, f"Hoàn cược Solo #{room_id}")
        SOLO_ROOMS.pop(room_id, None)
        return

    if game == "kbb":
        pick_kb = InlineKeyboardMarkup([[
            btn("KÉO", "✂️", callback_data=f"pvp:pick:{room_id}:keo"),
            btn("BÚA", "🪨", callback_data=f"pvp:pick:{room_id}:bua"),
            btn("BAO", "📄", callback_data=f"pvp:pick:{room_id}:bao"),
        ]])
        await ctx.bot.send_message(
            chat_id,
            f'{ce("✊")} <b>SOLO KÉO BÚA BAO - CHỌN NƯỚC ĐI</b>\n'
            f'{room_copy["owner_name"]} đấu với <b>{room_copy["opponent_name"]}</b>\n'
            f'{ce("💰")} Mỗi người: <code>{fmt_money(amount)}đ</code>\n'
            f'Mỗi người chơi bấm chọn một nút bên dưới. Lựa chọn được giữ kín đến khi cả hai đã chọn.',
            parse_mode=ParseMode.HTML, reply_markup=pick_kb)
        return

    settled = False
    try:
        await ctx.bot.send_message(
            chat_id,
            f'{ce("🎲")} <b>SOLO XÚC XẮC BẮT ĐẦU</b>\n'
            f'{room_copy["owner_name"]} đấu với <b>{room_copy["opponent_name"]}</b>\n'
            f'Mỗi người: <code>{fmt_money(amount)}đ</code>',
            parse_mode=ParseMode.HTML)
        one = await ctx.bot.send_dice(chat_id=chat_id, emoji="🎲")
        await asyncio.sleep(1)
        two = await ctx.bot.send_dice(chat_id=chat_id, emoji="🎲")
        a, b = one.dice.value, two.dice.value
        if a == b:
            add_money(owner, amount, f"Hoàn cược hòa Solo Xúc Xắc #{room_id}")
            add_money(uid, amount, f"Hoàn cược hòa Solo Xúc Xắc #{room_id}")
            settled = True
            result = f'{ce("🤝")} <b>HÒA</b> - đã hoàn cược cho cả hai.'
        else:
            winner = owner if a > b else uid
            prize = int(amount * 1.95)
            add_money(winner, prize, f"Thắng Solo Xúc Xắc #{room_id}")
            settled = True
            result = f'{ce("🏆")} Người thắng: <b>{"Người tạo phòng" if winner == owner else "Người tham gia"}</b> · Nhận <code>{fmt_money(prize)}đ</code>'
        output = f'{ce("🎲")} <b>KẾT QUẢ SOLO XÚC XẮC</b>\nNgười tạo: <b>{a}</b>\nNgười tham gia: <b>{b}</b>\n{result}'
        await ctx.bot.send_message(chat_id, output, parse_mode=ParseMode.HTML)
    except Exception as e:
        print(f"[solo-dice] Lỗi trận {room_id}: {e}")
        if not settled:
            add_money(owner, amount, f"Hoàn cược lỗi Solo Xúc Xắc #{room_id}")
            add_money(uid, amount, f"Hoàn cược lỗi Solo Xúc Xắc #{room_id}")
        try:
            await ctx.bot.send_message(chat_id, "Trận đấu gặp lỗi kỹ thuật. Hệ thống đã xử lý hoàn cược nếu chưa thanh toán.")
        except Exception:
            pass
    finally:
        SOLO_ROOMS.pop(room_id, None)


async def xuctele_cmd(update, ctx):
    args = ctx.args or []
    if len(args) != 2 or args[0].lower() not in TELE_DICE_CHOICES:
        return await update.effective_message.reply_text(
            f'{ce("🎲")} <b>XÚC XẮC TELE</b>\n'
            'XXC: 2,4,6 · XXL: 1,3,5 · XXT: 4,5,6 · XXX: 1,2,3\n'
            'Tỷ lệ x1.95 · Min 5.000đ · Max 100.000đ\n'
            'Cú pháp: <code>/xuctele xxc 10000</code>',
            parse_mode=ParseMode.HTML)
    try:
        amount = int(args[1].replace(",", "").replace(".", ""))
    except ValueError:
        return await update.effective_message.reply_text("Số tiền không hợp lệ.")
    if not 5000 <= amount <= 100000:
        return await update.effective_message.reply_text("Mức cược từ 5.000đ đến 100.000đ.")
    uid = update.effective_user.id
    if not has_bank_linked(uid):
        return await update.effective_message.reply_text(BANK_LINK_REQUIRED_MSG, parse_mode=ParseMode.HTML)
    if not sub_money(uid, amount, f"Cược Xúc Xắc Tele {args[0].upper()}"):
        return await update.effective_message.reply_text("Số dư không đủ.")
    before = bal_pre(uid)
    status = await update.effective_message.reply_text(f'{ce("🎲")} Đang tung xúc xắc...', parse_mode=ParseMode.HTML)
    try:
        dice = await ctx.bot.send_dice(chat_id=update.effective_chat.id, emoji="🎲")
        face, choice = dice.dice.value, args[0].lower()
        if face in TELE_DICE_CHOICES[choice]:
            prize = int(amount * 1.95)
            add_money(uid, prize, f"Thắng Xúc Xắc Tele {choice.upper()}")
            result = f'{ce("🎉")} THẮNG · Nhận <code>+{fmt_money(prize)}đ</code>'
        else:
            result = f'{ce("❌")} THUA'
        await status.edit_text(
            f'{ce("🎲")} <b>XÚC XẮC TELE</b>\nKết quả: <b>{face}</b>\n'
            f'Cửa chọn: <b>{choice.upper()}</b>\n{result}\n{bal_pair(before, uid)}',
            parse_mode=ParseMode.HTML)
    except Exception:
        add_money(uid, amount, "Hoàn cược lỗi Xúc Xắc Tele")
        raise


async def baucua_cmd(update, ctx):
    args = [x.lower() for x in (ctx.args or [])]
    if len(args) < 2 or len(args) > 4:
        return await update.effective_message.reply_text(
            f'{ce("🦀")} <b>BẦU CUA</b>\n'
            'Bầu=1 · Tôm=2 · Cua=3 · Cá=4 · Gà=5 · Nai=6\n'
            'Chọn tối đa 3 cửa. 1 mặt x1.95 · 2 mặt x3 · 3 mặt x4\n'
            'Min 2.000đ · Max 300.000đ/cửa\n'
            'Cú pháp: <code>/baucua bau cua ca 5000</code>',
            parse_mode=ParseMode.HTML)
    try:
        amount = int(args[-1].replace(",", "").replace(".", ""))
    except ValueError:
        return await update.effective_message.reply_text("Số tiền không hợp lệ.")
    choices = args[:-1]
    if not 1 <= len(choices) <= 3 or len(set(choices)) != len(choices) or any(c not in BAUCUA_CHOICES for c in choices):
        return await update.effective_message.reply_text("Chọn tối đa 3 cửa khác nhau: bau, tom, cua, ca, ga, nai.")
    if not 2000 <= amount <= 300000:
        return await update.effective_message.reply_text("Mức cược mỗi cửa từ 2.000đ đến 300.000đ.")
    uid, total = update.effective_user.id, amount * len(choices)
    if not has_bank_linked(uid):
        return await update.effective_message.reply_text(BANK_LINK_REQUIRED_MSG, parse_mode=ParseMode.HTML)
    if not sub_money(uid, total, f"Cược Bầu Cua {','.join(choices)}"):
        return await update.effective_message.reply_text(f"Số dư không đủ. Tổng cược: {fmt_money(total)}đ.")
    before = bal_pre(uid)
    status = await update.effective_message.reply_text(f'{ce("🎲")} Đang lắc Bầu Cua...', parse_mode=ParseMode.HTML)
    try:
        faces = [random.randint(1, 6) for _ in range(3)]
        counts = collections.Counter(BAUCUA_FACE[n] for n in faces)
        icons = " ".join(BAUCUA_CHOICES[BAUCUA_FACE[n]][1] for n in faces)
        total_prize, details = 0, []
        for c in choices:
            count = counts.get(c, 0)
            if count:
                mult = {1: 1.95, 2: 3, 3: 4}[count]
                prize = int(amount * mult)
                total_prize += prize
                details.append(f'{BAUCUA_CHOICES[c][0]}: {count} mặt · x{mult:g} · +{fmt_money(prize)}đ')
            else:
                details.append(f'{BAUCUA_CHOICES[c][0]}: không xuất hiện')
        if total_prize:
            add_money(uid, total_prize, "Thắng Bầu Cua")
        result = f'{ce("🎉")} Tổng nhận: <code>+{fmt_money(total_prize)}đ</code>' if total_prize else f'{ce("❌")} Không trúng cửa nào.'
        await status.edit_text(
            f'{ce("🦀")} <b>BẦU CUA</b>\n{icons}\n'
            f'Kết quả: <b>{" · ".join(BAUCUA_CHOICES[BAUCUA_FACE[n]][0] for n in faces)}</b>\n\n'
            + "\n".join(details) + f'\n{result}\n{bal_pair(before, uid)}',
            parse_mode=ParseMode.HTML)
    except Exception:
        add_money(uid, total, "Hoàn cược lỗi Bầu Cua")
        raise


# ================= HỆ THỐNG DANH SÁCH GAME (DẠNG NÚT BẤM) =================
AMOUNT_BUTTONS = [("1k", 1000), ("5k", 5000), ("10k", 10000), ("20k", 20000), ("50k", 50000),
                  ("100k", 100000), ("200k", 200000), ("500k", 500000), ("1m", 1000000)]

GAMES = {
    "room": {"name": "TÀI XỈU ROOM", "icon": "👑", "rows": None},
    "tx3d": {"name": "TÀI XỈU 3D", "icon": "🎲", "rows": None},
    "xuctele": {"name": "XÚC XẮC TELE", "icon": "🎲", "rows": None},
    "baucua": {"name": "BẦU CUA", "icon": "🦀", "rows": None},
    "soloxd": {"name": "SOLO XÚC XẮC", "icon": "🎲", "rows": None},
    "solokbb": {"name": "SOLO KÉO BÚA BAO", "icon": "✊", "rows": None},
}
for _g, _c in TGDICE.items():
    GAMES[_g] = {"name": _c["name"], "icon": _c["icon"], "rows": _tg_rows(_c)}

# Bố cục 2 cột: Tài Xỉu Room + Tài Xỉu 3D ở hàng đầu, sau đó là các game hoạt ảnh Telegram.
GAME_ROWS = [["room", "tx3d"], ["xuctele", "baucua"], ["soloxd", "solokbb"], ["pt", "br"], ["bd", "bl"], ["sl", "xxd"], ["pk", "ll"]]

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
        f'  - Tài / Xỉu / Chẵn / Lẻ: x1.97\n'
        f'  - Cửa kết hợp: x3\n'
        f'  - Bộ ba đồng nhất: x150\n\n'
        f'{ce("💡")} <b>Cách chơi:</b> Bấm nút bên dưới để vào phòng, nhắn lệnh VD: <code>T 20000</code> hoặc cược ẩn danh nhắn riêng cho bot.'
    ),
}
for _g in TGDICE:
    GAME_RULES[_g] = _tg_rules(_g)

GAME_RULES.update({
    "xuctele": (
        f'{ce("🎲")} <b>XÚC XẮC TELEGRAM</b> {ce("🎲")}\n\n'
        '<b>Chế độ mặc định: BOT tung xúc xắc</b>\n\n'
        '<b>Nội dung | Kết quả 1 xúc xắc | Tỷ lệ ăn</b>\n'
        'XXC | 2,4,6 | x1.95\n'
        'XXL | 1,3,5 | x1.95\n'
        'XXT | 4,5,6 | x1.95\n'
        'XXX | 1,2,3 | x1.95\n\n'
        '🔹 Tối thiểu là 5.000 và tối đa là 100.000\n\n'
        '💡 Cách chơi: [Nội dung] [tiền cược]\n'
        'VD: <code>XXC 10000</code> hoặc <code>XXL 10000</code>'
    ),
    "baucua": (
        f'{ce("🦀")} <b>BẦU CUA</b>\n\n'
        '🍐 BẦU - Nếu xúc xắc ra số 1\n'
        '🦐 TÔM - Nếu xúc xắc ra số 2\n'
        '🦀 CUA - Nếu xúc xắc ra số 3\n'
        '🐟 CÁ - Nếu xúc xắc ra số 4\n'
        '🐓 GÀ - Nếu xúc xắc ra số 5\n'
        '🦌 NAI - Nếu xúc xắc ra số 6\n\n'
        'Tỷ lệ: ra 1 viên x1.95 | ra 2 viên x3 | ra 3 viên x4\n'
        'Đặt tối đa 3 cửa trong 1 lệnh.\n\n'
        '🔹 Tối thiểu là 2.000 và tối đa là 300.000 mỗi cửa\n\n'
        '💡 Cách chơi: [cửa 1] [cửa 2] [cửa 3] [tiền cược]\n'
        'VD: <code>bau cua ca 5000</code> hoặc <code>cua 10000</code>'
    ),
    "soloxd": (
        f'{ce("🎲")} <b>GAME SOLO XÚC XẮC</b> {ce("🎲")}\n'
        'Tạo phòng và mời người khác tham gia đấu xúc xắc.\n\n'
        '🏆 Min: 2.000\n🏆 Max: 1.000.000\n🏆 Tỉ lệ trả thưởng: 1.95\n\n'
        '💡 <b>Cách chơi</b>\n'
        '<code>/solo 5000</code> - tạo phòng\n'
        '<code>/solo [mã phòng]</code> - vào phòng\n'
        '<code>/huy [mã phòng]</code> - hủy phòng\n\n'
        'Phòng tạo sẽ được đăng vào nhóm để người khác tham gia.'
    ),
    "solokbb": (
        f'{ce("✊")} <b>SOLO KÉO BÚA BAO</b>\n'
        'Tạo phòng và mời người khác tham gia đấu kéo búa bao.\n\n'
        '🤖 Chế độ BOT: đấu với bot, tỉ lệ thắng x1.95 (hòa hoàn tiền).\n'
        '🔹 Gõ <code>/kbb [số tiền]</code> để hiện 3 nút Kéo / Búa / Bao.\n'
        'VD: <code>/kbb 20000</code>\n'
        '🔹 Hoặc chơi SOLO: <code>/solokbb [kéo|búa|bao] [số tiền]</code>\n'
        'VD: <code>/solokbb kéo 10000</code>\n\n'
        '🔹 Min: 2.000\n🔹 Max: 1.000.000\n🔹 Tỉ lệ trả thưởng SOLO: x1.95\n\n'
        '💡 <b>Cách chơi SOLO</b>\n'
        '<code>/solokbb 20000</code> - tạo phòng\n'
        '<code>/solokbb [mã phòng]</code> - vào phòng\n'
        '<code>/huykbb [mã phòng]</code> - hủy phòng'
    ),
})

GAME_RULES["tx3d"] = (
    f'{ce("🎲")} <b>TÀI XỈU 3D (MINIAPP)</b>\n\n'
    f'{ce("🎯")} <b>LUẬT CHƠI:</b>\n'
    f'━━━━━━━━━━━━━━━━━━━━━\n'
    f'• Mỗi phiên lắc 3 viên xúc xắc, kéo bát để mở kết quả.\n'
    f'• Tài: tổng 11-18 · Xỉu: tổng 3-10 · Thắng nhận x{TX3D_PAYOUT}.\n'
    f'• Mỗi phiên chỉ được cược một cửa (có thể cược thêm nhiều lần).\n'
    f'• Bão (3 mặt giống nhau): {"hoàn tiền cược" if TX3D_BAO_REFUND else "nhà cái ăn cả hai cửa"}.\n'
    f'• Nổ hũ: 3 con 6 → cửa Tài ăn hũ · 3 con 1 → cửa Xỉu ăn hũ (người thắng hũ nhận x10–x12 tiền cược).\n'
    f'• Số dư dùng chung với bot chính, cược/thắng tự cập nhật ngay.\n\n'
    f'{ce("💡")} <b>Bấm nút bên dưới để vào game.</b>'
)

def tx3d_entry_view(uid, private=True, back=True):
    """Nội dung + nút vào game Tài Xỉu 3D. Trả về (text, keyboard)."""
    rows_back = [[btn("Quay lại", "🔙", callback_data="game_list")]] if back else []
    if check_mt(TX3D_MT_KEY) and uid not in ADMIN_IDS:
        return f'{ce("⚙️")} Game Tài Xỉu 3D đang bảo trì!', InlineKeyboardMarkup(rows_back) if rows_back else None
    if is_game_banned(uid, TX3D_GAME_ID) and uid not in ADMIN_IDS:
        return f'{ce("🚫")} Bạn đã bị cấm chơi trò chơi này!', InlineKeyboardMarkup(rows_back) if rows_back else None
    if not has_bank_linked(uid):
        return BANK_LINK_REQUIRED_MSG, InlineKeyboardMarkup(rows_back) if rows_back else None
    kb = tx3d_play_kb(private)
    if kb is None:
        return (GAME_RULES["tx3d"] + f'\n\n{ce("⚠️")} Miniapp chưa cấu hình địa chỉ (biến MINIAPP_URL hoặc domain Railway).',
                InlineKeyboardMarkup(rows_back) if rows_back else None)
    if private:
        text = GAME_RULES["tx3d"]
    else:
        text = GAME_RULES["tx3d"] + f'\n\n{ce("⚠️")} Miniapp chỉ mở được trong chat riêng với bot.'
    rows = list(kb.inline_keyboard) + rows_back
    return text, InlineKeyboardMarkup(rows)

GAME_LIST_TEXT = (
    f'{ce("🎮")} <b>TRUNG TÂM TRÒ CHƠI</b> {ce("✨")}\n'
    f'━━━━━━━━━━━━━━━━━━━━\n'
    f'{ce("👑")} <b>PHÒNG VIP</b>\n'
    f'{ce("🎲")} Tài Xỉu Room · Tài Xỉu 3D\n\n'
    f'{ce("🔥")} <b>GAME HOẠT ẢNH TELEGRAM</b>\n'
    f'{ce("🎯")} Phi Tiêu · {ce("🏀")} Bóng Rổ · {ce("⚽")} Bóng Đá\n'
    f'{ce("🎳")} Bowling · {ce("🎰")} Quay Hũ · {ce("🎲")} Xúc Xắc Đôi\n'
    f'{ce("⚔️")} Đọ Xúc Xắc · {ce("⚽")} Luân Lưu\n'
    f'━━━━━━━━━━━━━━━━━━━━\n'
    f'{ce("💡")} Bấm vào game để xem luật và chọn cửa cược.\n'
    f'{ce("🍀")} Chúc bạn chơi vui, may mắn!'
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

async def _edit_text_or_caption(q, text, reply_markup=None):
    """Sửa tin nhắn dù nó là tin chữ hay ảnh/file có chú thích (tin yêu cầu rút có kèm ảnh QR)."""
    try:
        return await q.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
    except Exception as e:
        if "no text in the message" in str(e).lower():
            return await q.edit_message_caption(caption=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)
        raise

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
    if g in TGDICE:
        return await play_tgdice(update, ctx, g, choice, amount)


# ================= SOLO: MENU CHƠI VỚI BOT / TẠO PHÒNG =================
SOLO_BOT_PENDING = {}

def _solo_entry_keyboard(game):
    label = "Kéo Búa Bao" if game == "kbb" else "Xúc Xắc"
    return InlineKeyboardMarkup([
        [btn("🤖 CHƠI NHANH VỚI BOT", "🤖", callback_data=f"solo:bot:{game}")],
        [btn("🟩 TẠO PHÒNG SOLO", "🎮", callback_data=f"solo:room:{game}")],
        [btn("Quay lại", "🔙", callback_data="game_list")]
    ])

def _solo_entry_text(game, uid):
    if game == "kbb":
        return (
            f'{ce("✊")} <b>SOLO KÉO BÚA BAO</b>\\n\\n'
            f'{ce("🤖")} <b>CHƠI NHANH VỚI BOT</b>\\n'
            'Nhập <code>/kbb [số tiền]</code> từ 2.000 đến 1.000.000.\\n'
            'Bot sẽ hiện 3 nút để bạn chọn ✂️ Kéo, 🪨 Búa hoặc 📄 Bao.\\n\\n'
            f'{ce("🟩")} <b>TẠO PHÒNG SOLO</b>\\n'
            'Nhập <code>/solokbb [số tiền]</code> từ 2.000 đến 1.000.000.\\n'
            'Sau khi tạo, bot gửi mã phòng để mời người khác tham gia.'
        )
    return (
        f'{ce("🎲")} <b>SOLO XÚC XẮC</b>\\n\\n'
        f'{ce("🤖")} <b>CHƠI NHANH VỚI BOT</b>\\n'
        'Nhập <code>/xucxacbot [số tiền]</code> từ 2.000 đến 1.000.000.\\n'
        'Bot tung xúc xắc, so điểm với bạn; điểm cao hơn thắng. Hòa hoàn tiền.\\n\\n'
        f'{ce("🟩")} <b>TẠO PHÒNG SOLO</b>\\n'
        'Nhập <code>/solo [số tiền]</code> từ 2.000 đến 1.000.000.\\n'
        'Sau khi tạo, bot gửi mã phòng để mời người khác tham gia.'
    )

async def _solo_bot_kbb_cmd(update, ctx):
    msg, uid = update.effective_message, update.effective_user.id
    args = ctx.args or []
    if len(args) != 1:
        return await msg.reply_text("Cú pháp: /kbb [số tiền] (2.000–1.000.000đ)")
    try:
        amount = int(args[0].replace(",", "").replace(".", ""))
    except ValueError:
        return await msg.reply_text("Số tiền không hợp lệ.")
    if not SOLO_MIN <= amount <= SOLO_MAX:
        return await msg.reply_text("Mức cược từ 2.000đ đến 1.000.000đ.")
    if not has_bank_linked(uid):
        return await msg.reply_text(BANK_LINK_REQUIRED_MSG, parse_mode=ParseMode.HTML)
    if not sub_money(uid, amount, "Cược Kéo Búa Bao với BOT"):
        return await msg.reply_text("Số dư không đủ.")
    token = f"{uid}-{time.time_ns()}"
    SOLO_BOT_PENDING[token] = amount
    kb = InlineKeyboardMarkup([[
        btn("KÉO", "✂️", callback_data=f"kb_bot:{token}:keo"),
        btn("BÚA", "🪨", callback_data=f"kb_bot:{token}:bua"),
        btn("BAO", "📄", callback_data=f"kb_bot:{token}:bao"),
    ]])
    await msg.reply_text(
        f'{ce("🤖")} <b>CHƠI KÉO BÚA BAO VỚI BOT</b>\\n'
        f'Cược: <code>{fmt_money(amount)}đ</code> · Thắng x1.95 · Hòa hoàn tiền\\n'
        'Hãy chọn nước đi:', parse_mode=ParseMode.HTML, reply_markup=kb)

async def _solo_bot_dice_cmd(update, ctx):
    msg, uid = update.effective_message, update.effective_user.id
    args = ctx.args or []
    if len(args) != 1:
        return await msg.reply_text("Cú pháp: /xucxacbot [số tiền] (2.000–1.000.000đ)")
    try:
        amount = int(args[0].replace(",", "").replace(".", ""))
    except ValueError:
        return await msg.reply_text("Số tiền không hợp lệ.")
    if not SOLO_MIN <= amount <= SOLO_MAX:
        return await msg.reply_text("Mức cược từ 2.000đ đến 1.000.000đ.")
    if not has_bank_linked(uid):
        return await msg.reply_text(BANK_LINK_REQUIRED_MSG, parse_mode=ParseMode.HTML)
    if not sub_money(uid, amount, "Cược Solo Xúc Xắc với BOT"):
        return await msg.reply_text("Số dư không đủ.")
    try:
        await msg.reply_text(f'{ce("🤖")} <b>SOLO XÚC XẮC VỚI BOT</b> · Cược <code>{fmt_money(amount)}đ</code>', parse_mode=ParseMode.HTML)
        player = await ctx.bot.send_dice(chat_id=msg.chat_id, emoji="🎲")
        await asyncio.sleep(1)
        botdice = await ctx.bot.send_dice(chat_id=msg.chat_id, emoji="🎲")
        a, b = player.dice.value, botdice.dice.value
        if a == b:
            add_money(uid, amount, "Hoàn cược hòa Solo Xúc Xắc BOT")
            result = "🤝 HÒA — đã hoàn tiền cược."
        elif a > b:
            prize = int(amount * 1.95)
            add_money(uid, prize, "Thắng Solo Xúc Xắc BOT")
            result = f"🏆 BẠN THẮNG — nhận {fmt_money(prize)}đ."
        else:
            result = "❌ BOT THẮNG — bạn thua cược."
        await msg.reply_text(f'Kết quả của bạn: <b>{a}</b>\\nKết quả BOT: <b>{b}</b>\\n{result}', parse_mode=ParseMode.HTML)
    except Exception:
        add_money(uid, amount, "Hoàn cược lỗi Solo Xúc Xắc BOT")
        raise

async def _solo_bot_callback(update, ctx, data):
    q = update.callback_query
    parts = data.split(":")
    if len(parts) != 3:
        return await q.answer("Lựa chọn không hợp lệ.", show_alert=True)
    token, choice = parts[1], parts[2]
    amount = SOLO_BOT_PENDING.get(token)
    uid = q.from_user.id
    if amount is None or token.split("-", 1)[0] != str(uid):
        return await q.answer("Lượt chơi đã hết hạn hoặc không thuộc về bạn.", show_alert=True)
    if choice not in KBB_CHOICES:
        return await q.answer("Lựa chọn không hợp lệ.", show_alert=True)
    SOLO_BOT_PENDING.pop(token, None)
    bot_choice = random.choice(list(KBB_CHOICES))
    if choice == bot_choice:
        add_money(uid, amount, "Hoàn cược hòa Kéo Búa Bao BOT")
        result = "🤝 HÒA — đã hoàn tiền cược."
    elif KBB_BEATS[choice] == bot_choice:
        prize = int(amount * 1.95)
        add_money(uid, prize, "Thắng Kéo Búa Bao BOT")
        result = f"🏆 BẠN THẮNG — nhận {fmt_money(prize)}đ."
    else:
        result = "❌ BOT THẮNG — bạn thua cược."
    await q.answer("Đã ghi nhận lựa chọn.")
    return await q.edit_message_text(
        f'Bạn chọn: <b>{KBB_CHOICES[choice]}</b>\\nBOT chọn: <b>{KBB_CHOICES[bot_choice]}</b>\\n{result}',
        parse_mode=ParseMode.HTML)

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
            return await q.answer("Game này đã ngừng hoạt động, hãy chọn game khác trong danh sách!", show_alert=True)
        await q.answer()
        if g == "room":
            kb = InlineKeyboardMarkup([
                [btn("VÀO PHÒNG CHƠI", "🎮", url=ROOM_LINK)],
                [btn("Quay lại", "🔙", callback_data="game_list")]
            ])
            return await safe_edit(q, GAME_RULES["room"], kb)
        if g in ("soloxd", "solokbb"):
            solo_game = "dice" if g == "soloxd" else "kbb"
            return await safe_edit(q, _solo_entry_text(solo_game, uid), _solo_entry_keyboard(solo_game))
        if g in ("xuctele", "baucua"):
            return await safe_edit(
                q, GAME_RULES[g] + f'\n\n{ce("💰")} Số dư: <code>{fmt_money(get_balance(uid))}đ</code>',
                InlineKeyboardMarkup([[btn("Quay lại", "🔙", callback_data="game_list")]])
            )
        if g == "tx3d":
            in_private = (not q.message) or q.message.chat.type == "private"
            text, kb = tx3d_entry_view(uid, private=in_private, back=True)
            try:
                return await q.edit_message_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)
            except Exception as e:
                if "not modified" in str(e).lower():
                    return
                print(f"[tx3d] lỗi hiển thị nút miniapp (url={tx3d_url()}): {e}")
                detail = f"\n<code>{html.escape(str(e))[:200]}</code>\nLink đang dùng: <code>{html.escape(str(tx3d_url()))}</code>" if uid in ADMIN_IDS else ""
                return await safe_edit(q, f'{ce("⚠️")} Miniapp chưa sẵn sàng, vui lòng thử lại sau hoặc liên hệ admin.{detail}',
                                       InlineKeyboardMarkup([[btn("Quay lại", "🔙", callback_data="game_list")]]))
        if not game.get("rows"):
            text = GAME_RULES[g] + f'\n\n{ce("💰")} Số dư: <code>{fmt_money(get_balance(uid))}đ</code>\n{ce("⬇️")} <b>Chọn số tiền cược:</b>'
            return await safe_edit(q, text, game_amount_kb(g, "x"))
        rows = [[btn(label, em, callback_data=f"gc_{g}_{code}") for label, code, em in row] for row in game["rows"]]
        rows.append([btn("Quay lại", "🔙", callback_data="game_list")])
        text = GAME_RULES[g] + f'\n\n{ce("💰")} Số dư: <code>{fmt_money(get_balance(uid))}đ</code>\n{ce("⬇️")} <b>Chọn cửa để đặt cược:</b>'
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

    if d.startswith("pvp:"):
        return await _solo_callback(update, ctx, d)
    if d.startswith("solo:"):
        parts = d.split(":")
        if len(parts) == 3:
            _, mode, game = parts
            if mode == "bot":
                await q.answer()
                if game == "kbb":
                    return await q.message.reply_text(
                        "🤖 <b>CHƠI NHANH VỚI BOT</b>\nNhập <code>/kbb [số tiền]</code> để chơi.",
                        parse_mode=ParseMode.HTML)
                return await q.message.reply_text(
                    "🤖 <b>CHƠI NHANH VỚI BOT</b>\nNhập <code>/xucxacbot [số tiền]</code> để chơi.",
                    parse_mode=ParseMode.HTML)
            if mode == "room":
                await q.answer()
                command = "/solokbb" if game == "kbb" else "/solo"
                return await q.message.reply_text(
                    f'🟩 <b>TẠO PHÒNG SOLO</b>\nNhập <code>{command} [số tiền]</code> để tạo phòng. Bot sẽ gửi mã phòng để mời người khác.',
                    parse_mode=ParseMode.HTML)
        return await q.answer("Lựa chọn không hợp lệ.", show_alert=True)
    if d.startswith("kb_bot:"):
        return await _solo_bot_callback(update, ctx, d)

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
        await q.answer()
        if not query("SELECT 1 FROM fan_enrollments WHERE user_id=%s", (uid,)):
            query("INSERT INTO fan_enrollments(user_id) VALUES(%s) ON CONFLICT(user_id) DO NOTHING", (uid,))
            # Không cho lịch sử điểm danh trước khi tham gia được tính vào chương trình.
            query("DELETE FROM fan_checkins WHERE user_id=%s", (uid,))
        return await _fan_send_guide(ctx, uid, q.message)

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
        day = get_vietnam_time().date()
        date_text = day.strftime("%d/%m/%Y")
        rows = query(
            "SELECT user_id, COALESCE(bet,0) FROM bet_daily WHERE day=%s AND COALESCE(bet,0)>0 ORDER BY bet DESC, user_id ASC LIMIT 10",
            (day,)
        ) or []
        lines = [f'{ce("🔥")} <b>TOP CƯỢC NGÀY {date_text}</b>', ""]
        if rows:
            for rank, (player_id, bet_amount) in enumerate(rows, 1):
                masked_id = "**" + str(player_id)[-4:]
                medal = _top_medal(rank)
                lines.append(f'{medal} Top {rank}: <code>{masked_id}</code> | <b>{fmt_money(int(bet_amount or 0))}k</b>')
        else:
            lines.append("Chưa có dữ liệu cược hôm nay.")
        my_rank = next((i for i, row in enumerate(rows, 1) if int(row[0]) == int(uid)), None)
        lines.append("")
        lines.append(f"🎉 Thứ hạng của bạn: Top {my_rank}" if my_rank else "🎉 Thứ hạng của bạn: Chưa vào top")
        return await q.message.reply_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup([
                [btn("TOP DÂY THẮNG", "🔥", callback_data="top_streak_win"),
                 btn("TOP DÂY THUA", "🥶", callback_data="top_streak_loss")]
            ]),
            parse_mode=ParseMode.HTML)

    if d == "top_thang_thua":
        await q.answer()
        return await q.message.reply_text(
            f'{ce("🏆")} <b>ĐUA TOP</b>',
            reply_markup=InlineKeyboardMarkup([
                [btn("TOP CƯỢC NGÀY", "🏆", callback_data="top_cuoc_ngay")],
                [btn("TOP DÂY THẮNG", "🔥", callback_data="top_streak_win")],
                [btn("TOP DÂY THUA", "🥶", callback_data="top_streak_loss")]
            ]),
            parse_mode=ParseMode.HTML)

    if d in ("top_streak_win", "top_streak_loss"):
        await q.answer()
        streak_type = "win" if d.endswith("win") else "loss"
        column = "max_win" if streak_type == "win" else "max_loss"
        title = "DÂY THẮNG" if streak_type == "win" else "DÂY THUA"
        word = "thắng" if streak_type == "win" else "thua"
        icon = "🔥" if streak_type == "win" else "🥶"
        date_text = get_vietnam_time().strftime("%d/%m/%Y")
        rows = query(
            f"SELECT user_id, MAX({column}) FROM user_game_streaks "
            f"WHERE {column}>0 GROUP BY user_id ORDER BY MAX({column}) DESC,user_id ASC LIMIT 10"
        ) or []
        reward_list = [50000, 30000, 20000, 10000] + [5000] * 4
        lines = [f'{ce(icon)} <b>TOP {title} HÔM NAY {date_text}</b>', ""]
        if rows:
            for rank, (player_id, best) in enumerate(rows, 1):
                masked_id = "**" + str(player_id)[-4:]
                medal = _top_medal(rank)
                reward_text = f' | thưởng <b>{reward_list[rank-1] // 1000}K</b>' if rank <= len(reward_list) else ''
                lines.append(f'{medal} Top {rank}: <code>{masked_id}</code> | <b>{int(best or 0)} ván {word} liên tiếp</b>{reward_text}')
        else:
            lines.append("Chưa có dữ liệu dây thắng/thua.")
        my_rank = next((i for i, row in enumerate(rows, 1) if int(row[0]) == int(uid)), None)
        lines.append("")
        lines.append(f"🎉 Thứ hạng của bạn: Top {my_rank}" if my_rank else "🎉 Thứ hạng của bạn: Chưa vào top")
        return await q.message.reply_text(
            "\n".join(lines),
            reply_markup=InlineKeyboardMarkup([
                [btn("TOP CƯỢC NGÀY", "🏆", callback_data="top_cuoc_ngay")],
                [btn("TOP DÂY THẮNG", "🔥", callback_data="top_streak_win"),
                 btn("TOP DÂY THUA", "🥶", callback_data="top_streak_loss")]
            ]),
            parse_mode=ParseMode.HTML)

    if d.startswith("ev_"):
        if (not d.startswith("ev_nhan_") or d == "ev_nhan_vip") and d != "ev_vip_claim_all":
            await q.answer()
        if d in ("ev_hc_ngay", "ev_hc_tuan", "ev_ht_ngay", "ev_ht_tuan"):
            ev_text, ev_kb = event_screen(uid, d[3:])
            return await q.message.reply_text(ev_text, reply_markup=ev_kb, parse_mode=ParseMode.HTML)
        if d == "ev_nhan_vip":
            vip_text, vip_kb = vip_reward_screen(uid)
            return await q.message.reply_text(vip_text, reply_markup=vip_kb, parse_mode=ParseMode.HTML)
        if d == "ev_vip_claim_all":
            return await claim_vip_level_rewards(update, ctx)
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
            return await q.message.reply_text(f'{ce("🔔")} <b>HỖ TRỢ NẠP TIỀN</b>\n\nVui lòng liên hệ CSKH: @dgfrutil\nHoặc dùng lệnh <code>/nap [số_tiền]</code> để tạo QR.', parse_mode=ParseMode.HTML)
        try:
            await q.answer()
            amount = int(d.split("_")[1])
            if amount < 10000 or amount > 100000000:
                return await q.message.reply_text("Số tiền nạp phải từ 10.000đ đến 100.000.000đ.")
            # Chống spam lệnh nạp: đang có lệnh còn hiệu lực thì phải chờ; quá 5 mã chưa nạp => khóa ẩn.
            _gate, _info = nap_order_gate(uid)
            if _gate == "banned":
                return                               # khóa ẩn: im lặng hoàn toàn, không báo gì
            if _gate == "wait":
                return await q.message.reply_text(nap_wait_text(_info), parse_mode=ParseMode.HTML)

            qr_url, caption, content = get_deposit_info(uid, amount)
            _order_id = nap_order_record(uid, amount, content)
            kb = InlineKeyboardMarkup([[btn("Hỗ Trợ", "🔔", callback_data="dep_support")]])
            # Gửi QR mới trước; chỉ xóa menu cũ sau khi gửi thành công để không mất giao diện nếu API lỗi.
            sent = await send_deposit_qr(ctx.bot, uid, qr_url, caption, kb, amount, content)
            nap_order_schedule_expiry(ctx.bot, sent, _order_id)
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
        # Đã phát sinh cược sau khi nạp mà chưa nhận => coi như từ bỏ khuyến mãi, không nhận lại.
        offer_id = int(parts[5]) if len(parts) > 5 and parts[5].isdigit() else None
        if offer_id is not None:
            claimed = query("UPDATE promo_offers SET status='claimed' WHERE id=%s AND user_id=%s AND status='pending' RETURNING id",
                            (offer_id, target_id))
            if not claimed:
                await q.answer("❌ Khuyến mãi đã hết hiệu lực vì bạn đã cược trước khi nhận!", show_alert=True)
                try:
                    await q.message.edit_text(
                        f'{ce("❌")} <b>KHUYẾN MÃI ĐÃ HẾT HIỆU LỰC</b>\n'
                        f'Bạn đã phát sinh cược trước khi nhận nên khuyến mãi lần nạp này coi như từ bỏ và không được nhận lại.',
                        parse_mode=ParseMode.HTML)
                except Exception:
                    pass
                return
        p15 = 0
        if offered15 and promo_claim_daily(target_id, amount):
            p15 = int(amount * PROMO_PCT / 100)
        p3 = int(amount * PROMO_ORDER_PCT / 100)
        total = p15 + p3
        if total <= 0:
            return await q.answer("❌ Không có khuyến mãi để nhận!", show_alert=True)
        deposit_base_release(target_id, amount)   # đã tính cược trên toàn bộ số dư (gồm tiền nạp) nên bỏ phần x1 cộng trước đó
        add_promo_bonus(target_id, p15, p3)
        st = get_bet_progress_status(target_id)
        lines = [f'{ce("🎁")} <b>ĐÃ NHẬN KHUYẾN MÃI!</b>']
        if p15:
            lines.append(f'{ce("✨")} Thưởng {PROMO_PCT}%: <code>+{fmt_money(p15)}đ</code>')
        elif offered15:
            lines.append(f'{ce("📌")} <i>Hôm nay bạn đã nhận {PROMO_PCT}% rồi nên chỉ nhận phần {PROMO_ORDER_PCT}%.</i>')
        lines.append(f'{ce("➕")} Thưởng {PROMO_ORDER_PCT}% mỗi lệnh nạp: <code>+{fmt_money(p3)}đ</code>')
        lines.append(f'{ce("💰")} Tổng nhận: <code>+{fmt_money(total)}đ</code>')
        lines.append(bal_block(target_id))
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
            f'{bal_block(target_id)}\n'
            f'{ce("⚠️")} <b>Lưu ý:</b> Phải cược x{PROMO_WAGER_MULT} vòng',
            parse_mode=ParseMode.HTML)
        return

    if d.startswith("reject_bonus_"):
        _rp = d.split("_")
        target_id = int(_rp[2])
        if q.from_user.id != target_id: return await q.answer("❌ Không phải yêu cầu của bạn!", show_alert=True)
        if len(_rp) > 3 and _rp[3].isdigit():
            query("UPDATE promo_offers SET status='rejected' WHERE id=%s AND user_id=%s AND status='pending'", (int(_rp[3]), target_id))
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

    if d.startswith("ok_") or d.startswith("no_") or d.startswith("wdrf_") or d.startswith("wdnr_"):
        if uid not in ADMIN_IDS: return await q.answer()
        act, u_id, amt = d.split("_")
        u_id, amt = int(u_id), int(amt)
        pending = query("SELECT id FROM withdraw_history WHERE user_id=%s AND amount=%s AND status='pending' ORDER BY id DESC LIMIT 1", (u_id, amt))
        if not pending:
            await q.answer("⚠️ Yêu cầu này đã được xử lý rồi!", show_alert=True)
            try: await _edit_text_or_caption(q, f'{ce("⚠️")} Yêu cầu rút này đã được xử lý trước đó.')
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
            try: await send_group_notice(ctx.bot, chat_id=LOG_GROUP_ID, text=f'{ce("📤")} <b>RÚT TIỀN THÀNH CÔNG</b>\n👤 Người rút: {html.escape(target_name)}\n🆔 ID: <code>{mask_user_id(u_id)}</code>\n{ce("💰")} Số tiền: <code>{fmt_money(amt)}đ</code>\n{ce("✅")} Trạng thái: Thành công\n⏰ {get_vietnam_datetime_db()}', parse_mode=ParseMode.HTML)
            except Exception as e: pass
            try: await ctx.bot.send_message(u_id, f'{ce("✅")} Yêu cầu rút <code>{fmt_money(amt)}đ</code> đã được duyệt!\n{ce("💰")} Số dư hiện tại: <code>{fmt_money(get_balance(u_id))}đ</code>', parse_mode=ParseMode.HTML)
            except: pass
            await _edit_text_or_caption(q, f'{ce("✅")} ĐÃ DUYỆT ID <code>{u_id}</code> | <code>{fmt_money(amt)}đ</code>')
        else:
            query("UPDATE withdraw_history SET status='rejected', admin_id=%s, admin_note='Từ chối' WHERE id=%s", (uid, wid))
            add_money(u_id, amt, "Hoàn tiền rút")
            try:
                target_chat = await ctx.bot.get_chat(u_id)
                target_name = ("@" + target_chat.username) if getattr(target_chat, "username", None) else (getattr(target_chat, "full_name", None) or "Thành viên")
            except Exception:
                target_name = "Thành viên"
            # Không gửi thông báo rút tiền bị từ chối lên nhóm.
            # Người rút vẫn nhận thông báo riêng bên dưới và tiền được hoàn theo luồng hiện có.
            try: await ctx.bot.send_message(u_id, f'{ce("❌")} Yêu cầu rút <code>{fmt_money(amt)}đ</code> bị từ chối.\n{ce("🔄")} Tiền đã được hoàn về số dư của bạn.\n{bal_block(u_id)}', parse_mode=ParseMode.HTML)
            except: pass
            await _edit_text_or_caption(q, f'{ce("❌")} TỪ CHỐI ID <code>{u_id}</code> | <code>{fmt_money(amt)}đ</code>')
        return

    await q.answer()

# ============================================================
# WEBHOOK SEPAY
# ============================================================
async def sepay_webhook(request):
    # Xác thực API Key. SePay gửi header "Authorization: Apikey <KEY>" (cũng chấp nhận "Bearer <KEY>").
    import hmac
    auth_header = request.headers.get("Authorization", "").strip()
    parts = auth_header.split(None, 1)
    given_key = parts[1].strip() if len(parts) == 2 and parts[0].lower() in ("apikey", "bearer") else ""
    if not SEPAY_API_KEY:
        print("SePay Webhook: CHƯA đặt biến môi trường SEPAY_API_KEY trên server -> từ chối mọi webhook")
        return web.Response(status=401, text="SEPAY_API_KEY not configured")
    if not given_key or not hmac.compare_digest(given_key, SEPAY_API_KEY):
        print(f"SePay Webhook: Sai API key (header nhận được: {auth_header[:12]}...)")
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
        if str(data.get("transferType", "in")).lower() != "in":
            return web.Response(status=200, text="Not incoming")

        # Tìm user_id từ nội dung chuyển khoản.
        # Nội dung gốc: "doi tac 7884394252" nhưng ngân hàng hay chèn thêm mã phía sau
        # (vd "doi tac 7884394252 I2T82W15/054424") nên KHÔNG lấy số ở cuối chuỗi.
        # Chỉ xét các từ gồm toàn chữ số (>=5 số), ưu tiên ID đã tồn tại trong bảng users.
        candidates = [int(t) for t in re.findall(r'(?<![\w/])(\d{5,15})(?![\w/])', content)]
        if not candidates:
            print(f"SePay Webhook: Không tìm thấy ID trong nội dung: {content}")
            return web.Response(status=200, text="No ID found")
        user_id = next((c for c in candidates if query("SELECT 1 FROM users WHERE user_id=%s", (c,))), None)
        if user_id is None:
            print(f"SePay Webhook: ID {candidates} không có trong bảng users: {content}")
            return web.Response(status=200, text="User not found")
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
        try:
            nap_orders_mark_paid(user_id)   # đã thanh toán => hết chờ, không bị tính vào hạn mức 5 mã
        except Exception as _e:
            print(f"SePay Webhook: không cập nhật được trạng thái lệnh nạp: {_e}")
        _cleared, _extra = apply_deposit_wager_rule(user_id, get_balance(user_id), amount)
        add_money(user_id, amount, f"Nạp tiền tự động (SePay) +{amount:,}đ")
        await notify_deposit_wager(_bot_instance, user_id, _cleared, _extra)

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
                f'{bal_block(user_id)}{deposit_wager_line(user_id)}',
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"SePay Webhook: Lỗi gửi tin nhắn cho user {user_id}: {e}")

        # Thông báo cho Admin (Log Group)
        masked_id = mask_user_id(user_id)
        try:
            await send_group_notice(
                _bot_instance,
                LOG_GROUP_ID,
                f'{ce("✅")} <b>THÔNG BÁO NẠP TIỀN TỰ ĐỘNG</b>\n'
                f'{ce("👥")} ID: <code>{masked_id}</code>\n'
                f'{ce("💰")} Số tiền: <code>+{fmt_money(amount)}đ</code>',
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
            f'{bal_block(user_id)}\n'
            f'🧾 Mã giao dịch: <code>{html.escape(str(ref_code or "—"))}</code>\n'
            f'⏰ Thời gian: <code>{now_str}</code>'
        )
        for admin_id in ADMIN_IDS:
            try:
                await _bot_instance.send_message(admin_id, admin_notice, parse_mode=ParseMode.HTML)
            except Exception as e:
                print(f"Không gửi được thông báo nạp cho admin {admin_id}: {e}")

        # Khuyến mãi nạp: 10% (1 lần/ngày, giờ vàng) + 3% mỗi lệnh nạp
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

# ============================================================
# WEB ADMIN (đăng nhập bằng tên đăng nhập + mật khẩu do admin tạo qua bot)
#   Bot:  /taoadmin  /xoaadmin  /doimkadmin  /dsadminweb
#   Web:  https://<tên-miền>/admin
# ============================================================
import secrets as _secrets
import string as _string

query("""CREATE TABLE IF NOT EXISTS admin_web_users (
    username TEXT PRIMARY KEY,
    pw_hash TEXT NOT NULL,
    created_by BIGINT,
    created_at TEXT,
    active INTEGER DEFAULT 1,
    last_login TEXT
)""")
query("""CREATE TABLE IF NOT EXISTS admin_web_log (
    id SERIAL PRIMARY KEY,
    username TEXT,
    action TEXT,
    detail TEXT,
    ip TEXT,
    time TEXT
)""")
# Phan quyen admin phu; tai khoan cu mac dinh la chu so huu.
query("ALTER TABLE admin_web_users ADD COLUMN IF NOT EXISTS is_owner INTEGER DEFAULT 1")
query("ALTER TABLE admin_web_users ADD COLUMN IF NOT EXISTS permissions TEXT DEFAULT '{}'")
query("""CREATE TABLE IF NOT EXISTS admin_code_bans (
    user_id BIGINT PRIMARY KEY, created_by TEXT, created_at TEXT
)""")
query("""CREATE TABLE IF NOT EXISTS admin_user_stat_resets (
    user_id BIGINT PRIMARY KEY, dep_offset BIGINT DEFAULT 0, wd_offset BIGINT DEFAULT 0,
    reset_by TEXT, reset_at TEXT
)""")


ADMIN_WEB_SESSION_TTL = 8 * 3600      # tối đa 8 giờ
ADMIN_WEB_IDLE_TTL = 2 * 3600         # 2 giờ không thao tác thì hết phiên
_ADMIN_SESSIONS = {}                  # token -> {user, csrf, created, last, ip}
_ADMIN_LOGIN_FAILS = {}               # key (ip / user) -> [timestamps]
_USERNAME_RE = re.compile(r"^[a-z0-9_]{3,20}$")


def _aw_hash_password(password: str, salt: bytes = None, iters: int = 200_000) -> str:
    salt = salt or os.urandom(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iters)
    return f"pbkdf2_sha256${iters}${salt.hex()}${dk.hex()}"


# Tài khoản SUPER ADMIN mặc định do chủ bot yêu cầu.
# Tự đồng bộ mỗi lần khởi động để tránh mất quyền đăng nhập do /taoadmin trước đó.
def _aw_bootstrap_super_admin():
    try:
        _super_hash = _aw_hash_password("123123123")
        _super_perms = json.dumps({k: True for k in _AW_FEATURES})
        # Chuyển quyền owner duy nhất sang username admin.
        query("UPDATE admin_web_users SET is_owner=0 WHERE username<>%s", ("admin",))
        query("""INSERT INTO admin_web_users(username,pw_hash,created_by,created_at,active,is_owner,permissions)
                 VALUES(%s,%s,%s,%s,1,1,%s)
                 ON CONFLICT(username) DO UPDATE SET pw_hash=EXCLUDED.pw_hash, active=1,
                 is_owner=1, permissions=EXCLUDED.permissions""",
              ("admin", _super_hash, 0, get_vietnam_datetime_db(), _super_perms))
        print("✅ SUPER ADMIN Web đã đồng bộ: admin")
    except Exception as _e:
        print(f"⚠️ Không thể khởi tạo SUPER ADMIN Web: {_e}")


_aw_bootstrap_super_admin()


def _aw_verify_password(password: str, stored: str) -> bool:
    try:
        algo, iters, salt_hex, hash_hex = stored.split("$")
        if algo != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iters))
        return hmac.compare_digest(dk.hex(), hash_hex)
    except Exception:
        return False


def _aw_gen_password(n: int = 12) -> str:
    alphabet = _string.ascii_letters + _string.digits
    return "".join(_secrets.choice(alphabet) for _ in range(n))


def _aw_ip(request) -> str:
    fwd = request.headers.get("X-Forwarded-For", "")
    if fwd:
        return fwd.split(",")[0].strip()[:64]
    return (request.remote or "?")[:64]


def _aw_log(username, action, detail="", ip=""):
    try:
        query("INSERT INTO admin_web_log(username, action, detail, ip, time) VALUES(%s,%s,%s,%s,%s)",
              (username, action, str(detail)[:500], ip, get_vietnam_datetime_db()))
    except Exception as e:
        print(f"admin_web_log lỗi: {e}")


def _aw_rate_blocked(key: str, limit: int = 5, window: int = 600) -> bool:
    now = time.time()
    arr = [t for t in _ADMIN_LOGIN_FAILS.get(key, []) if now - t < window]
    _ADMIN_LOGIN_FAILS[key] = arr
    return len(arr) >= limit


def _aw_rate_fail(key: str):
    _ADMIN_LOGIN_FAILS.setdefault(key, []).append(time.time())


def _aw_kill_sessions(username: str):
    for tok in [t for t, s in _ADMIN_SESSIONS.items() if s["user"] == username]:
        _ADMIN_SESSIONS.pop(tok, None)


def _aw_session(request):
    tok = request.cookies.get("xl_adm", "")
    s = _ADMIN_SESSIONS.get(tok)
    if not s:
        return None, None
    now = time.time()
    if now - s["created"] > ADMIN_WEB_SESSION_TTL or now - s["last"] > ADMIN_WEB_IDLE_TTL:
        _ADMIN_SESSIONS.pop(tok, None)
        return None, None
    # tài khoản bị xoá/khoá thì phiên mất hiệu lực ngay
    row = query("SELECT active, COALESCE(is_owner,1), COALESCE(permissions,'{}') FROM admin_web_users WHERE username=%s", (s["user"],))
    if not row or not row[0][0]:
        _ADMIN_SESSIONS.pop(tok, None)
        return None, None
    s["owner"] = bool(row[0][1])
    try:
        s["permissions"] = json.loads(row[0][2] or "{}")
    except Exception:
        s["permissions"] = {}
    s["last"] = now
    return tok, s


_AW_SEC_HEADERS = {
    "Content-Security-Policy": "default-src 'none'; img-src 'self' data:; style-src 'unsafe-inline'; "
                               "script-src 'self'; connect-src 'self'; form-action 'self'; "
                               "frame-ancestors 'none'; base-uri 'none'",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Cache-Control": "no-store",
    "X-Robots-Tag": "noindex, nofollow",
}


def _aw_html(body: str, status: int = 200):
    return web.Response(text=body, status=status, content_type="text/html", charset="utf-8", headers=_AW_SEC_HEADERS)


def _aw_json(data, status: int = 200):
    return web.json_response(data, status=status, headers=_AW_SEC_HEADERS)


_AW_CSS = """
:root{--bg:#0f1117;--card:#181b24;--line:#272b38;--tx:#e8eaf0;--mut:#8b91a3;--pri:#4f8cff;--ok:#27c281;--bad:#ff5d6c;--warn:#f5b942}
*{box-sizing:border-box}html,body{margin:0;background:var(--bg);color:var(--tx);font:15px/1.45 system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
a{color:var(--pri)}
.wrap{max-width:1100px;margin:0 auto;padding:14px 16px 60px}
header{display:flex;align-items:center;justify-content:space-between;gap:10px;padding:12px 16px;border-bottom:1px solid var(--line);position:sticky;top:0;background:var(--bg);z-index:5}
header b{font-size:17px}.mut{color:var(--mut)}
nav{display:flex;gap:6px;overflow:auto;padding:12px 0}
nav button{background:var(--card);color:var(--mut);border:1px solid var(--line);padding:8px 14px;border-radius:10px;white-space:nowrap;cursor:pointer;font-size:14px}
nav button.on{color:#fff;background:var(--pri);border-color:var(--pri)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:10px}
.card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}
.card .k{color:var(--mut);font-size:12.5px}.card .v{font-size:21px;font-weight:650;margin-top:4px}
.item{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px;margin:10px 0}
.row{display:flex;flex-wrap:wrap;gap:6px 18px;font-size:14px}.row span b{font-weight:600}
.btn{border:0;border-radius:9px;padding:9px 14px;font-size:14px;cursor:pointer;color:#fff;background:var(--pri)}
.btn.ok{background:var(--ok)}.btn.bad{background:var(--bad)}.btn.gray{background:#2c3142}
.btn:disabled{opacity:.5}
input,select{background:#0f1117;border:1px solid var(--line);color:var(--tx);border-radius:9px;padding:10px 12px;font-size:15px;width:100%}
.inl{display:flex;gap:8px;flex-wrap:wrap}.inl input{flex:1;min-width:140px;width:auto}
.tag{display:inline-block;padding:2px 9px;border-radius:99px;font-size:12px;border:1px solid var(--line)}
.tag.pending{color:var(--warn);border-color:var(--warn)}.tag.success{color:var(--ok);border-color:var(--ok)}.tag.rejected{color:var(--bad);border-color:var(--bad)}
.qr{width:170px;height:170px;background:#fff;border-radius:10px;object-fit:contain}
.acts{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}
table{width:100%;border-collapse:collapse;font-size:13.5px}td,th{padding:8px 6px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}th{color:var(--mut);font-weight:500}
.tw{overflow:auto}
#toast{position:fixed;left:50%;bottom:22px;transform:translateX(-50%);background:#222838;border:1px solid var(--line);padding:10px 16px;border-radius:10px;display:none;z-index:9;max-width:90vw}
.login{max-width:360px;margin:12vh auto;padding:0 16px}.login .card{padding:22px}.login h2{margin:0 0 16px}
.login label{display:block;margin:12px 0 5px;color:var(--mut);font-size:13px}.err{color:var(--bad);margin-top:12px;font-size:14px}
"""

_AW_LOGIN_PAGE = """<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>Đăng nhập quản trị</title><style>__CSS__</style></head><body>
<div class="login"><div class="card"><h2>🔐 Đăng nhập quản trị</h2>
<form method="post" action="/admin/login" autocomplete="off">
<label>Tên đăng nhập</label><input name="username" autocomplete="username" autocapitalize="none" required>
<label>Mật khẩu</label><input name="password" type="password" autocomplete="current-password" required>
<div style="margin-top:18px"><button class="btn" style="width:100%" type="submit">Đăng nhập</button></div>
__ERR__
</form></div></div></body></html>"""

_AW_APP_PAGE = """<!doctype html><html lang="vi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex">
<title>Quản trị</title><style>__CSS__</style></head><body>
<header><b>⚙️ Quản trị</b><span class="mut"><span id="who"></span> · <a href="#" id="out">Đăng xuất</a></span></header>
<div class="wrap">
<nav id="nav"></nav>
<div id="view"></div>
</div><div id="toast"></div>
<script src="/admin/app.js"></script></body></html>"""

_AW_JS = r"""
(function(){
'use strict';
var csrf = '';
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c];});}
function money(n){return Number(n||0).toLocaleString('vi-VN')+'đ';}
function toast(t){var e=document.getElementById('toast');e.textContent=t;e.style.display='block';clearTimeout(toast._t);toast._t=setTimeout(function(){e.style.display='none';},3200);}
async function api(path,opt){
  opt=opt||{};opt.headers=Object.assign({'X-CSRF':csrf},opt.headers||{});opt.credentials='same-origin';
  var r=await fetch('/admin/api/'+path,opt);
  if(r.status===401){location.href='/admin/login';throw new Error('unauth');}
  var j;try{j=await r.json();}catch(e){throw new Error('Máy chủ lỗi ('+r.status+'), xem log Railway');}if(j.err){throw new Error(j.err);}return j;
}
function post(path,body){return api(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body||{})});}
var tabs=[['stats','Tổng quan'],['wd','Rút tiền'],['dep','Nạp tiền'],['user','Người dùng'],['dupe','Trùng tên rút tiền'],['gift','Giftcode'],['tx3d','Ép TX3D'],['ctl','Điều khiển'],['bc','Thông báo'],['exp','Xuất file'],['reset','Reset'],['log','Nhật ký'],['admins','Tạo admin'],['fan','Duyệt Fan']];
var cur='stats',view=document.getElementById('view'),isOwner=false,allowed={};
function nav(){var n=document.getElementById('nav');n.innerHTML='';tabs.filter(function(t){return t[0]==='admins'?isOwner:(isOwner||allowed[t[0]]);}).forEach(function(t){var b=document.createElement('button');b.textContent=t[1];if(t[0]===cur)b.className='on';b.onclick=function(){cur=t[0];nav();load();};n.appendChild(b);});}
function load(){view.innerHTML='<p class="mut">Đang tải…</p>';var pages={stats:vStats2,wd:vWd,dep:vDep2,user:vUser,dupe:vPayoutDuplicates,gift:vGift2,tx3d:vTx3d,ctl:vCtl,bc:vBc,exp:vExp,reset:vReset,log:vLog,admins:vAdmins,fan:vFan};var fn=pages[cur];if(!fn){view.innerHTML='<p class="err">Mục này chưa được cấu hình.</p>';return;}fn().catch(function(e){view.innerHTML='<p class="err">'+esc(e.message)+'</p>';});}


async function vFan(){
  var d=await api('fan');
  var rows=d.rows||[];
  var h='<h2>🌸 Duyệt Fan +30K</h2><p class="mut">Người dùng điểm danh đủ 7 ngày liên tiếp. Duyệt sẽ tạo giftcode thưởng 30.000đ, x3 vòng cược, hạn 3 ngày.</p>';
  if(!rows.length){view.innerHTML=h+'<p class="mut">Chưa có yêu cầu nào.</p>';return;}
  h+=rows.map(function(r){
    var status=r.status==='pending'?'⏳ Chờ duyệt':(r.status==='approved'?'✅ Đã duyệt':'❌ Từ chối');
    return '<div class="item"><div class="row"><b>#'+esc(r.id)+' · User '+esc(r.user_id)+'</b><span>'+status+'</span></div>'+
      '<div class="mut" style="margin:6px 0">Tên: '+esc(r.full_name||'-')+' · @'+esc(r.username||'-')+' · '+esc(r.created_at)+'</div>'+
      (r.gift_code?'<div>Giftcode: <code>'+esc(r.gift_code)+'</code></div>':'')+
      (r.status==='pending'?'<div class="acts"><button class="btn ok" data-fan="approve" data-id="'+esc(r.id)+'">✅ Duyệt & gửi code</button><button class="btn bad" data-fan="reject" data-id="'+esc(r.id)+'">❌ Từ chối</button></div>':'')+'</div>';
  }).join('');
  view.innerHTML=h;
  view.querySelectorAll('[data-fan]').forEach(function(b){b.onclick=async function(){
    if(!confirm(b.dataset.fan==='approve'?'Tạo giftcode 30.000đ x3, hạn 3 ngày và gửi cho người dùng?':'Từ chối yêu cầu Fan này?'))return;
    try{var x=await post('fan',{id:Number(b.dataset.id),action:b.dataset.fan});toast(x.msg||'Đã xử lý');vFan();}
    catch(e){toast(e.message);}
  };});
}

async function vStats(){
  var d=await api('stats');var c=[
   ['Người dùng',d.users],['Tổng số dư',money(d.balance)],['Nạp hôm nay',money(d.dep_today)],['Rút hôm nay',money(d.wd_today)],
   ['Tổng nạp',money(d.dep_total)],['Tổng rút',money(d.wd_total)],['Rút chờ duyệt',d.wd_pending_n+' đơn · '+money(d.wd_pending_sum)],['Cược hôm nay',money(d.bet_today)]];
  view.innerHTML='<div class="grid">'+c.map(function(x){return '<div class="card"><div class="k">'+esc(x[0])+'</div><div class="v">'+esc(x[1])+'</div></div>';}).join('')+'</div>';
}

function wdCard(w){
  var h='<div class="item"><div class="row"><span><b>#'+esc(w.id)+'</b> · <span class="tag '+esc(w.status)+'">'+esc({pending:'Chờ duyệt',success:'Đã duyệt',rejected:'Từ chối'}[w.status]||w.status)+'</span></span><span>'+esc(w.time)+'</span></div>'
  +'<div class="row" style="margin-top:8px"><span>Mã: <b>'+esc(w.code||'-')+'</b></span><span>ID: <b>'+esc(w.user_id)+'</b></span><span>Số tiền: <b>'+money(w.amount)+'</b></span></div>'
  +'<div class="row" style="margin-top:6px"><span>'+esc(w.method)+'</span><span>Ngân hàng: <b>'+esc(w.bank||'-')+'</b></span><span>STK: <b>'+esc(w.stk||'-')+'</b></span><span>Chủ TK: <b>'+esc(w.acc_name||'-')+'</b></span></div>';
  if(w.memo)h+='<div class="row" style="margin-top:6px"><span>Nội dung CK: <b>'+esc(w.memo)+'</b></span></div>';
  if(w.note)h+='<div class="row mut" style="margin-top:6px"><span>'+esc(w.note)+'</span></div>';
  if(w.legacy)h+='<div class="mut" style="margin-top:6px;font-size:12.5px">Bản ghi cũ: thông tin lấy từ tài khoản liên kết hiện tại.</div>';
  h+='<div style="margin-top:10px"><img class="qr" alt="QR" loading="lazy" src="/admin/api/wqr/'+encodeURIComponent(w.id)+'"></div>';
  if(w.status==='pending')h+='<div class="acts"><button class="btn ok" data-a="approve" data-id="'+esc(w.id)+'">✅ Duyệt</button><button class="btn bad" data-a="reject" data-id="'+esc(w.id)+'">❌ Từ chối (hoàn tiền)</button><button class="btn bad" data-a="reject_no_refund" data-id="'+esc(w.id)+'">🚫 Từ chối (không hoàn tiền)</button></div>';
  return h+'</div>';
}
async function vWd(){
  var d=await api('withdraws?status='+(vWd.f||'pending'));
  var f='<div class="inl" style="margin-bottom:8px"><select id="wf"><option value="pending">Chờ duyệt</option><option value="all">Tất cả (50 gần nhất)</option></select><input id="wu" placeholder="Lọc theo ID người dùng"><button class="btn gray" id="wg">Lọc</button></div>';
  var list=function(rows){return rows.length?rows.map(wdCard).join(''):'<p class="mut">Không có yêu cầu.</p>';};
  view.innerHTML=f+'<div id="wl">'+list(d.rows)+'</div>';
  var s=document.getElementById('wf');s.value=vWd.f||'pending';document.getElementById('wu').value=vWd.u||'';
  document.getElementById('wg').onclick=async function(){vWd.f=s.value;vWd.u=document.getElementById('wu').value.trim();
    var r=await api('withdraws?status='+vWd.f+(vWd.u?'&uid='+encodeURIComponent(vWd.u):''));
    document.getElementById('wl').innerHTML=list(r.rows);};
}
view.addEventListener('click',async function(ev){
  var b=ev.target.closest('button[data-a]');if(!b)return;
  var act=b.getAttribute('data-a'),id=b.getAttribute('data-id');
  var reason='';
  if(act==='reject_no_refund'){
    reason=prompt('Nhập lý do từ chối KHÔNG hoàn tiền cho đơn #'+id+':');
    if(reason===null)return;
    reason=reason.trim();
    if(!reason){toast('Bạn phải nhập lý do từ chối.');return;}
    if(!confirm('Xác nhận từ chối đơn #'+id+' và KHÔNG hoàn lại tiền cho người dùng?'))return;
  }else if(!confirm((act==='approve'?'Xác nhận ĐÃ CHUYỂN KHOẢN và duyệt':'Từ chối và hoàn tiền')+' đơn #'+id+'?'))return;
  b.disabled=true;
  try{await post('withdraw/'+encodeURIComponent(id)+'/'+act,{reason:reason});toast('Đã xử lý đơn #'+id);load();}catch(e){toast(e.message);b.disabled=false;}
});


async function vPayoutDuplicates(){
  var q=vPayoutDuplicates.q||'';
  var d=await api('payout-duplicates?q='+encodeURIComponent(q));
  var methodLabel={BANKING:'Ngân hàng',MOMO:'MoMo',ZALOPAY:'ZaloPay'};
  var cards=d.groups.map(function(g){
    var h='<div class="item"><div class="row"><b>👥 '+esc(g.name)+'</b><span class="tag pending">'+esc(g.user_count)+' tài khoản người dùng</span></div>';
    h+='<div class="mut" style="margin:6px 0 10px">Trùng '+esc(g.account_count)+' bản ghi liên kết · '+Object.keys(g.method_counts).map(function(k){return esc(methodLabel[k]||k)+': '+esc(g.method_counts[k]);}).join(' · ')+'</div>';
    h+='<div style="overflow:auto"><table><tr><th>User ID</th><th>Phương thức</th><th>Ngân hàng</th><th>Số TK / SĐT</th><th>Tên chủ TK</th><th>Mặc định</th></tr>';
    h+=g.accounts.map(function(a){return '<tr><td><a href="#" data-open="'+esc(a.user_id)+'">'+esc(a.user_id)+'</a></td><td>'+esc(methodLabel[a.method]||a.method)+'</td><td>'+esc(a.bank_code||'-')+'</td><td>'+esc(a.account_number||'-')+'</td><td>'+esc(a.account_name||'-')+'</td><td>'+(a.is_default?'Có':'Không')+'</td></tr>';}).join('');
    return h+'</table></div></div>';
  }).join('');
  view.innerHTML='<div class="item"><b>🔎 Tìm tài khoản trùng</b><div class="inl" style="margin-top:8px"><input id="dup-q" value="'+esc(q)+'" placeholder="Nhập ID, tên chủ TK, STK hoặc SĐT"><button class="btn" id="dup-search">Tìm kiếm</button></div></div><div class="grid">'+
    '<div class="card"><div class="k">Nhóm tên trùng</div><div class="v">'+esc(d.group_count)+'</div></div>'+
    '<div class="card"><div class="k">Người dùng liên quan</div><div class="v">'+esc(d.matched_users)+'</div></div>'+
    '<div class="card"><div class="k">Bản ghi liên kết</div><div class="v">'+esc(d.matched_accounts)+'</div></div></div>'+
    '<div class="row" style="margin:12px 0"><span class="mut">Chỉ hiển thị tên chủ tài khoản xuất hiện ở từ 2 User ID khác nhau. Tên được chuẩn hoá dấu và khoảng trắng khi so sánh.</span><button class="btn gray" id="dup-refresh">Làm mới</button></div>'+
    (cards||'<div class="item mut">Chưa phát hiện tên chủ tài khoản rút tiền nào trùng giữa các người dùng.</div>');
  document.getElementById('dup-refresh').onclick=function(){vPayoutDuplicates().catch(function(e){toast(e.message);});};
  document.getElementById('dup-search').onclick=function(){vPayoutDuplicates.q=document.getElementById('dup-q').value.trim();vPayoutDuplicates().catch(function(e){toast(e.message);});};
  document.getElementById('dup-q').onkeydown=function(e){if(e.key==='Enter')document.getElementById('dup-search').click();};
}

async function vDep(){
  var d=await api('deposits');
  view.innerHTML='<div class="item tw"><table><tr><th>#</th><th>ID</th><th>Số tiền</th><th>Trạng thái</th><th>Thời gian</th></tr>'+
   d.rows.map(function(r){return '<tr><td>'+esc(r.id)+'</td><td>'+esc(r.user_id)+'</td><td>'+money(r.amount)+'</td><td><span class="tag '+esc(r.status)+'">'+esc(r.status)+'</span></td><td>'+esc(r.time)+'</td></tr>';}).join('')+'</table></div>';
}

var curUser=null;
function tagc(s){return {'Thành công':'success','Đã dùng':'success','Chờ duyệt':'pending','Chưa dùng':'pending','Từ chối':'rejected','Hết hạn':'rejected'}[s]||'';}
function tbl(d,idCols){
  var mc=d.money_cols||[],ic=idCols||[];
  var h='<div class="item tw"><table><tr>'+d.headers.map(function(x){return '<th>'+esc(x)+'</th>';}).join('')+'</tr>';
  h+=d.rows.map(function(r){return '<tr>'+r.map(function(c,i){
    if(mc.indexOf(i)>=0&&c!==''&&c!=null&&!isNaN(c))return '<td>'+money(c)+'</td>';
    if(i===d.status_col)return '<td><span class="tag '+tagc(c)+'">'+esc(c)+'</span></td>';
    if(ic.indexOf(i)>=0&&/^[0-9]+$/.test(String(c)))return '<td><a href="#" data-open="'+esc(c)+'">'+esc(c)+'</a></td>';
    return '<td>'+esc(c)+'</td>';}).join('')+'</tr>';}).join('');
  return h+'</table></div>'+(d.rows.length===0?'<p class="mut">Không có dữ liệu.</p>':'');
}
function card(k,v){return '<div class="card"><div class="k">'+esc(k)+'</div><div class="v" style="font-size:18px">'+esc(v)+'</div></div>';}

async function vUser(){
  if(curUser){return openUser(curUser);}
  view.innerHTML='<div class="inl"><input id="uq" placeholder="ID / @username / tên Telegram / STK / SĐT / tên chủ TK rút"><button class="btn" id="ug">Tìm</button></div><div id="ur"></div>';
  var run=async function(){var q=document.getElementById('uq').value.trim();var d=await api('users?q='+encodeURIComponent(q));
    var out=document.getElementById('ur');
    out.innerHTML=d.rows.length?d.rows.map(function(u){return '<div class="item"><div class="row"><span>ID: <b>'+esc(u.user_id)+'</b></span><span>Số dư: <b>'+money(u.balance)+'</b></span><span>Cược: <b>'+money(u.total_bet)+'</b></span><span>Nạp: <b>'+money(u.dep)+'</b></span><span>Rút: <b>'+money(u.wd)+'</b></span>'+(u.banned?'<span class="tag rejected">ĐÃ KHÓA</span>':'')+'</div>'
      +'<div class="row" style="margin-top:6px"><span>Ngân hàng: <b>'+esc(u.bank||'Chưa liên kết')+'</b></span><span>STK: <b>'+esc(u.stk||'-')+'</b></span><span>Chủ TK: <b>'+esc(u.name||'-')+'</b></span></div>'
      +(u.payouts&&u.payouts.length?'<div class="mut" style="margin-top:6px">Tài khoản rút liên kết: '+u.payouts.map(function(a){return esc(a.method)+' · '+esc(a.number||'-')+' · '+esc(a.name||'-');}).join(' | ')+'</div>':'')
      +'<div class="acts"><button class="btn" data-d="'+esc(u.user_id)+'">Xem đầy đủ thông tin</button></div></div>';}).join(''):'<p class="mut">Không tìm thấy.</p>';};
  document.getElementById('ug').onclick=run;document.getElementById('uq').onkeydown=function(e){if(e.key==='Enter')run();};
  run();
}

var secs=[['his','Lịch sử số dư'],['nap','Nạp tiền'],['rut','Rút tiền'],['cuoc','Cược / thắng'],['code','Code đã nhập'],['mua','Giftcode đã mua'],['gift','Giftcode nhận / dùng']];
async function openUser(id){
  curUser=id;view.innerHTML='<p class="mut">Đang tải…</p>';
  var d=await api('user/'+encodeURIComponent(id)+'/full');var p=d.p;
  var pnl=p.wins-p.total_bet,net=p.dep-p.wd;
  var cards=[
    ['Số dư',money(p.balance)],['Tổng nạp',money(p.dep)+' · '+p.dep_n+' lần'],['Tổng rút',money(p.wd)+' · '+p.wd_n+' lần'],
    ['Nạp − Rút',(net<0?'−':'+')+money(Math.abs(net))],['Rút đang chờ',money(p.wd_pend)+' · '+p.wd_pend_n+' đơn'],['Nạp hôm nay',money(p.dep_today)],
    ['Tổng cược',money(p.total_bet)],['Tổng thắng/hoàn',money(p.wins)],['Kết quả chơi',(pnl<0?'−':'+')+money(Math.abs(pnl))],
    ['Vòng cược còn lại',money(p.wager_remaining)],['VIP',p.vip||'—'],['Đã mời',p.refs+' người'],
    ['Code đã nhập',p.codes_used+' code'],['Giftcode đã dùng',p.gifts_used+' · '+money(p.received_sum)],['Giftcode đã mua',p.bought_n+' · '+money(p.bought_sum)+' (đã dùng '+p.bought_used+')'],
    ['Code chưa sử dụng',((p.pending_giftcodes||[]).length)+' code']];
  var h='<div class="acts" style="margin:0 0 10px"><button class="btn gray" id="bk">← Quay lại danh sách</button></div>'
   +'<div class="item"><div class="row"><span>ID: <b>'+esc(d.user_id)+'</b></span><span>Telegram: <b>'+esc(p.tg_name||'—')+'</b></span>'+(p.banned?'<span class="tag rejected">ĐÃ KHÓA</span>':'<span class="tag success">Hoạt động</span>')+'</div>'
   +'<div class="row" style="margin-top:8px"><span>Ngân hàng: <b>'+esc(p.bank||'Chưa liên kết')+'</b></span><span>STK: <b>'+esc(p.stk||'—')+'</b></span><span>Chủ TK: <b>'+esc(p.name||'—')+'</b></span><span>Liên kết: <b>'+(p.bank_linked?'Đã liên kết':'Chưa')+'</b></span></div>'
   +'<div class="row" style="margin-top:8px"><span>Hoạt động đầu: <b>'+esc(p.first_time||'—')+'</b></span><span>Check-in cuối: <b>'+esc(p.last_checkin||'—')+'</b></span><span>Rút gần nhất: <b>'+esc(p.last_withdraw||'—')+'</b></span><span>'+(p.refed?'Được người khác mời':'Tự đăng ký')+'</span></div>'
   +((p.banned_games.length||p.banned_features.length)?'<div class="row" style="margin-top:8px"><span>Bị cấm game: <b>'+esc(p.banned_games.join(', ')||'—')+'</b></span><span>Bị cấm tính năng: <b>'+esc(p.banned_features.join(', ')||'—')+'</b></span></div>':'')
   +(p.bonus?'<div class="row" style="margin-top:8px"><span>Khuyến mãi: <b>'+money(p.bonus.amount)+'</b></span><span>Vòng cược: <b>'+money(p.bonus.current)+' / '+money(p.bonus.required)+'</b></span></div>':'')
   +(p.payouts.length?'<div style="margin-top:8px" class="mut">Tài khoản nhận tiền đã liên kết:</div>'+p.payouts.map(function(a){return '<div class="row" style="margin-top:4px"><span>'+esc(a.method)+(a.default?' (mặc định)':'')+'</span><span>'+esc(a.bank||'')+'</span><span><b>'+esc(a.number)+'</b></span><span>'+esc(a.name)+'</span></div>';}).join(''):'')
   +'</div><div class="grid">'+cards.map(function(c){return card(c[0],c[1]);}).join('')+'</div>'
   +'<div class="item"><div class="row"><b>🎁 Danh sách code chưa sử dụng</b><span class="tag '+(p.pending_giftcodes&&p.pending_giftcodes.length?'pending':'success')+'">'+((p.pending_giftcodes||[]).length)+' mã</span></div>'
   +((p.pending_giftcodes||[]).length?'<div style="display:grid;gap:8px;margin-top:10px">'+p.pending_giftcodes.map(function(g){return '<div style="padding:10px;border:1px solid var(--line);border-radius:10px"><div class="row"><b>'+esc(g.type)+'</b><span class="tag '+(g.expired?'rejected':'pending')+'">'+(g.expired?'Đã hết hạn · chưa nhập':'Chưa nhập')+'</span></div><div style="margin-top:5px"><code>'+esc(g.code)+'</code></div><div class="mut" style="margin-top:4px">Giá trị: <b>'+money(g.reward)+'</b> · Hạn: '+esc(g.expiry||'Không giới hạn')+'</div></div>';}).join('')+'</div>':'<p class="mut" style="margin:8px 0 0">Tài khoản hiện không còn giftcode được cấp riêng nào chưa sử dụng.</p>')+'</div>'
   +'<div class="item"><b>💰 Điều chỉnh số dư</b><div class="inl" style="margin-top:8px"><input data-amt="'+esc(id)+'" placeholder="Số tiền (vd 50000)" inputmode="numeric"><button class="btn ok" data-u="add" data-id="'+esc(id)+'">＋ Cộng tiền</button><button class="btn bad" data-u="sub" data-id="'+esc(id)+'">－ Trừ tiền</button></div>'
   +'<div style="margin-top:14px"><b>🛡️ Quyền tài khoản</b><div class="grid" style="grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:8px">'
   +'<button class="btn gray" data-u="'+(p.banned?'unban':'ban')+'" data-id="'+esc(id)+'">'+(p.banned?'🔓 Mở khóa tài khoản':'🔒 Khóa tài khoản')+'</button>'
   +'<button class="btn gray" data-u="resetbank" data-id="'+esc(id)+'">🏦 Gỡ liên kết ngân hàng</button>'
   +'<button class="btn '+(p.code_blocked?'ok':'bad')+'" data-u="codeban" data-id="'+esc(id)+'">'+(p.code_blocked?'✅ Cho phép nhập code':'🚫 Cấm nhập code')+'</button>'
   +'</div></div><div style="margin-top:14px"><b>📊 Điều chỉnh thống kê</b><div class="grid" style="grid-template-columns:repeat(2,minmax(0,1fr));gap:8px;margin-top:8px">'
   +'<button class="btn gray" data-u="resetdep" data-id="'+esc(id)+'">↺ Đặt tổng nạp về 0</button><button class="btn gray" data-u="resetwd" data-id="'+esc(id)+'">↺ Đặt tổng rút về 0</button>'
   +'</div></div></div>'
   +'<nav id="snav"></nav><div id="sbody"></div>';
  view.innerHTML=h;
  document.getElementById('bk').onclick=function(){curUser=null;vUser();};
  var sn=document.getElementById('snav');
  secs.forEach(function(s,i){var b=document.createElement('button');b.textContent=s[1];b.onclick=function(){sn.querySelectorAll('button').forEach(function(x){x.className='';});b.className='on';loadSec(id,s[0]);};sn.appendChild(b);});
  sn.firstChild.click();
}
async function loadSec(id,kind){
  var body=document.getElementById('sbody');body.innerHTML='<p class="mut">Đang tải…</p>';
  var d=await api('user/'+encodeURIComponent(id)+'/sec/'+kind);var x=d.extra||{},sum='';
  if(kind==='nap'||kind==='rut')sum='Thành công: '+money(x.ok)+' ('+(x.ok_n||0)+' lần) · Đang chờ: '+money(x.pending);
  if(kind==='his')sum='Tổng tiền vào: '+money(x.in)+' · Tổng tiền ra: '+money(x.out);
  if(kind==='cuoc')sum='Tổng cược: '+money(x.bets)+' ('+(x.n_bet||0)+' lượt) · Thắng/hoàn: '+money(x.wins)+' · Kết quả: '+((x.net||0)<0?'−':'+')+money(Math.abs(x.net||0));
  if(kind==='code')sum='Tổng giá trị code đã nhập: '+money(x.sum);
  if(kind==='mua'||kind==='gift')sum='Tổng giá trị: '+money(x.sum)+' · Đã dùng: '+(x.used_n||0)+' code';
  body.innerHTML='<p class="mut" style="margin:8px 0">'+esc(sum)+(d.total>d.rows.length?' · hiển thị '+d.rows.length+'/'+d.total+' dòng mới nhất':' · '+d.total+' dòng')+'</p>'+tbl(d,(kind==='mua'||kind==='gift')?[2,3]:[]);
}
view.addEventListener('click',async function(ev){
  var o=ev.target.closest('a[data-open]');if(o){ev.preventDefault();cur='user';nav();openUser(o.getAttribute('data-open')).catch(function(e){toast(e.message);});return;}
  var d=ev.target.closest('button[data-d]');if(d){openUser(d.getAttribute('data-d')).catch(function(e){toast(e.message);});return;}
  var b=ev.target.closest('button[data-u]');if(!b)return;
  var act=b.getAttribute('data-u'),id=b.getAttribute('data-id'),body={};
  if(act==='add'||act==='sub'){var inp=view.querySelector('input[data-amt="'+id+'"]');var amt=parseInt((inp.value||'').replace(/[^0-9]/g,''),10);
    if(!amt||amt<=0){toast('Số tiền không hợp lệ');return;}body.amount=amt;
    if(!confirm((act==='add'?'CỘNG ':'TRỪ ')+money(amt)+' cho ID '+id+'?'))return;}
  else if(act==='codeban'){
    body.blocked=b.textContent.indexOf('Cấm nhập')>=0;
    if(!confirm((body.blocked?'Cấm':'Mở quyền')+' nhập giftcode cho ID '+id+'?'))return;
  } else if(act==='resetdep'||act==='resetwd'){
    body.kinds=[act==='resetdep'?'dep':'wd'];
    if(!confirm('Đặt tổng '+(act==='resetdep'?'nạp':'rút')+' hiển thị của ID '+id+' về 0? Lịch sử giao dịch vẫn được giữ.'))return;
  } else if(!confirm('Xác nhận thao tác "'+act+'" cho ID '+id+'?'))return;
  b.disabled=true;
  try{
    var endpoint=act==='codeban'?'user/'+encodeURIComponent(id)+'/codeban':
                 (act==='resetdep'||act==='resetwd')?'user/'+encodeURIComponent(id)+'/reset-stats':
                 'user/'+encodeURIComponent(id)+'/'+act;
    var r=await post(endpoint,body);toast(r.msg||'Xong');if(curUser){openUser(curUser);}else{var g=document.getElementById('ug');if(g)g.click();}}catch(e){toast(e.message);b.disabled=false;}
});

var gf={type:'',status:'all',q:'',page:1};
async function vGift(){
  var s=await api('gifts/summary');var t=s.total;
  var cards=[['Tổng code (giftcode)',t.count],['Đã dùng',t.used],['Chưa dùng',t.unused],['Hết hạn',t.expired],['Tổng giá trị',money(t.value)],['Giá trị đã dùng',money(t.used_value)],
             ['Code thường (số mã)',s.regular.codes],['Code thường đã nhập',s.regular.entered+' lượt']];
  var types=tbl({headers:['Loại','Tổng','Đã dùng','Chưa dùng','Hết hạn','Tổng giá trị','Giá trị đã dùng'],money_cols:[5,6],rows:s.types.map(function(x){return [x.name,x.total,x.used,x.unused,x.expired,x.value,x.used_value];})});
  var buyers=tbl({headers:['ID người mua','Số code đã mua','Tổng giá trị','Đã dùng'],money_cols:[2],rows:s.buyers.map(function(x){return [x.user_id,x.count,x.value,x.used];})},[0]);
  var opts='<option value="">Tất cả loại</option>'+s.types.map(function(x){return '<option value="'+esc(x.type)+'">'+esc(x.name)+'</option>';}).join('');
  view.innerHTML='<div class="grid">'+cards.map(function(c){return card(c[0],c[1]);}).join('')+'</div><h3 style="margin:18px 0 4px">Theo loại code</h3>'+types
   +'<h3 style="margin:18px 0 4px">Người mua code nhiều nhất (Code Mua)</h3>'+buyers
   +'<h3 style="margin:18px 0 8px">Danh sách code</h3><div class="inl"><select id="gt" style="max-width:190px">'+opts+'</select><select id="gs" style="max-width:150px"><option value="all">Mọi trạng thái</option><option value="used">Đã dùng</option><option value="unused">Chưa dùng</option><option value="expired">Hết hạn</option></select><input id="gq" placeholder="Mã code / ID tạo / ID dùng"><button class="btn" id="gg">Lọc</button></div><div id="gl"></div>';
  document.getElementById('gt').value=gf.type;document.getElementById('gs').value=gf.status;document.getElementById('gq').value=gf.q;
  var go=async function(pg){gf.type=document.getElementById('gt').value;gf.status=document.getElementById('gs').value;gf.q=document.getElementById('gq').value.trim();gf.page=pg||1;
    var d=await api('gifts?type='+encodeURIComponent(gf.type)+'&status='+gf.status+'&q='+encodeURIComponent(gf.q)+'&page='+gf.page);
    var rows=d.rows.map(function(r){return [r.code,r.type,r.reward,'x'+(r.wager||0),r.status,r.created_by||'',r.created_at||'',r.used_by||'',r.used_at||'',r.expiry,r.bound_user||'',r.need_dep];});
    var pager='<div class="acts"><button class="btn gray" class="btn gray gp"'+(d.page<=1?' disabled':'')+'>← Trước</button><span class="mut" style="align-self:center">Trang '+d.page+'/'+d.pages+' · '+d.total+' code</span><button class="btn gray" class="btn gray gn"'+(d.page>=d.pages?' disabled':'')+'>Sau →</button></div>';
    document.getElementById('gl').innerHTML=pager+tbl({headers:['Mã','Loại','Giá trị','Vòng cược','Trạng thái','ID tạo/mua','Thời gian tạo','ID dùng','Thời gian dùng','Hạn dùng','ID gắn','Yêu cầu tổng nạp'],money_cols:[2,11],status_col:4,rows:rows},[5,7,10])+pager;
    document.querySelectorAll('.gp').forEach(function(e){e.onclick=function(){go(d.page-1);};});document.querySelectorAll('.gn').forEach(function(e){e.onclick=function(){go(d.page+1);};});};
  document.getElementById('gg').onclick=function(){go(1);};go(gf.page);
}


async function vAdmins(){
  var d=await api('admins'),keys=Object.keys(d.features),labels=d.features;
  var h='<div class="item"><h3>Tạo admin phụ</h3><p class="mut">Chọn riêng từng mục được phép sử dụng.</p><div class="inl"><input id="an" placeholder="Tên đăng nhập"><input id="ap" placeholder="Mật khẩu (tối thiểu 8 ký tự)"></div><div class="grid" style="margin-top:10px">'+keys.map(function(k){return '<label class="card"><input type="checkbox" data-newperm="'+k+'" style="width:auto"> '+esc(labels[k])+'</label>';}).join('')+'</div><div class="acts"><button class="btn" id="acreate">Tạo tài khoản phụ</button></div></div><h3>Danh sách tài khoản</h3>';
  h+=d.rows.map(function(a){var perms=keys.map(function(k){return '<label class="card"><input type="checkbox" data-perm="'+esc(a.username)+'" data-key="'+k+'" '+(a.permissions&&a.permissions[k]?'checked':'')+' style="width:auto"> '+esc(labels[k])+'</label>';}).join('');
    return '<div class="item"><div class="row"><b>'+esc(a.username)+'</b><span class="tag '+(a.active?'success':'rejected')+'">'+(a.owner?'Chủ sở hữu':a.active?'Hoạt động':'Đã khóa')+'</span><span class="mut">Đăng nhập: '+esc(a.last_login||'Chưa đăng nhập')+'</span></div>'+(a.owner?'':'<div class="grid" style="margin-top:10px">'+perms+'</div><div class="acts"><button class="btn" data-saveperm="'+esc(a.username)+'">Lưu quyền</button><button class="btn gray" data-adminact="'+(a.active?'disable':'enable')+'" data-name="'+esc(a.username)+'">'+(a.active?'Khóa':'Mở khóa')+'</button><button class="btn bad" data-adminact="delete" data-name="'+esc(a.username)+'">Xóa</button></div>')+'</div>';
  }).join('');
  view.innerHTML=h;
  document.getElementById('acreate').onclick=async function(){var permissions={};keys.forEach(function(k){permissions[k]=!!view.querySelector('[data-newperm="'+k+'"]').checked;});
    try{await post('admins',{action:'create',username:document.getElementById('an').value.trim(),password:document.getElementById('ap').value,permissions:permissions});toast('Đã tạo admin phụ');vAdmins();}catch(e){toast(e.message);}};
  view.querySelectorAll('[data-saveperm]').forEach(function(b){b.onclick=async function(){var username=b.getAttribute('data-saveperm'),permissions={};keys.forEach(function(k){var el=view.querySelector('[data-perm="'+username+'"][data-key="'+k+'"]');permissions[k]=!!(el&&el.checked);});try{await post('admins',{action:'permissions',username:username,permissions:permissions});toast('Đã lưu quyền');vAdmins();}catch(e){toast(e.message);}};});
  view.querySelectorAll('[data-adminact]').forEach(function(b){b.onclick=async function(){var username=b.getAttribute('data-name'),action=b.getAttribute('data-adminact');if(!confirm('Xác nhận '+action+' tài khoản '+username+'?'))return;try{await post('admins',{action:action,username:username});toast('Đã cập nhật');vAdmins();}catch(e){toast(e.message);}};});
}
async function vLog(){
  var d=await api('log');
  view.innerHTML='<div class="item tw"><table><tr><th>Thời gian</th><th>Tài khoản</th><th>Thao tác</th><th>Chi tiết</th><th>IP</th></tr>'+
   d.rows.map(function(r){return '<tr><td>'+esc(r.time)+'</td><td>'+esc(r.username)+'</td><td>'+esc(r.action)+'</td><td>'+esc(r.detail)+'</td><td>'+esc(r.ip)+'</td></tr>';}).join('')+'</table></div>';
}

document.getElementById('out').onclick=async function(e){e.preventDefault();try{await post('logout');}catch(x){}location.href='/admin/login';};
(async function(){var m=await api('me');csrf=m.csrf;isOwner=!!m.owner;allowed=m.permissions||{};document.getElementById('who').textContent=m.user;nav();if(!isOwner&&!allowed.stats){var first=tabs.find(function(t){return allowed[t[0]];});cur=first?first[0]:'user';}nav();load();})().catch(function(){});
})();
"""


async def aw_login_page(request):
    tok, s = _aw_session(request)
    if s:
        raise web.HTTPFound("/admin")
    return _aw_html(_AW_LOGIN_PAGE.replace("__CSS__", _AW_CSS).replace("__ERR__", ""))


async def aw_login_post(request):
    ip = _aw_ip(request)
    try:
        form = await request.post()
        username = str(form.get("username", "")).strip().lower()[:40]
        password = str(form.get("password", ""))[:200]
    except Exception:
        return _aw_html(_AW_LOGIN_PAGE.replace("__CSS__", _AW_CSS).replace("__ERR__", '<div class="err">Yêu cầu không hợp lệ.</div>'), 400)

    def _fail(msg):
        return _aw_html(_AW_LOGIN_PAGE.replace("__CSS__", _AW_CSS).replace("__ERR__", f'<div class="err">{msg}</div>'), 401)

    if _aw_rate_blocked("ip:" + ip) or _aw_rate_blocked("u:" + username):
        return _aw_html(_AW_LOGIN_PAGE.replace("__CSS__", _AW_CSS).replace(
            "__ERR__", '<div class="err">Sai quá nhiều lần. Vui lòng thử lại sau 10 phút.</div>'), 429)

    row = await asyncio.to_thread(query, "SELECT pw_hash, active, COALESCE(is_owner,1), COALESCE(permissions,'{}') FROM admin_web_users WHERE username=%s", (username,))
    # luôn chạy 1 lần băm để thời gian phản hồi không lộ việc tài khoản có tồn tại hay không
    stored = row[0][0] if row else _aw_hash_password("dummy", b"\x00" * 16)
    ok = await asyncio.to_thread(_aw_verify_password, password, stored)
    if not (row and row[0][1] and ok):
        _aw_rate_fail("ip:" + ip)
        _aw_rate_fail("u:" + username)
        await asyncio.to_thread(_aw_log, username or "?", "LOGIN_FAIL", "", ip)
        return _fail("Sai tên đăng nhập hoặc mật khẩu.")

    token = _secrets.token_urlsafe(32)
    now = time.time()
    try:
        _perms = json.loads(row[0][3] or "{}") if row else {}
    except Exception:
        _perms = {}
    _ADMIN_SESSIONS[token] = {"user": username, "owner": bool(row[0][2]), "permissions": _perms,
                              "csrf": _secrets.token_urlsafe(24), "created": now, "last": now, "ip": ip}
    await asyncio.to_thread(query, "UPDATE admin_web_users SET last_login=%s WHERE username=%s",
                            (get_vietnam_datetime_db(), username))
    await asyncio.to_thread(_aw_log, username, "LOGIN", "", ip)
    resp = web.HTTPFound("/admin")
    secure = request.headers.get("X-Forwarded-Proto", request.scheme) == "https"
    resp.set_cookie("xl_adm", token, httponly=True, secure=secure, samesite="Strict",
                    max_age=ADMIN_WEB_SESSION_TTL, path="/admin")
    raise resp


async def aw_home(request):
    tok, s = _aw_session(request)
    if not s:
        raise web.HTTPFound("/admin/login")
    return _aw_html(_AW_APP_PAGE.replace("__CSS__", _AW_CSS))


async def aw_js(request):
    return web.Response(text=_AW_JS, content_type="application/javascript", charset="utf-8", headers=_AW_SEC_HEADERS)


def _aw_auth(request, need_csrf=False):
    tok, s = _aw_session(request)
    if not s:
        raise web.HTTPUnauthorized(text='{"err":"unauth"}', content_type="application/json")
    if need_csrf and not hmac.compare_digest(request.headers.get("X-CSRF", ""), s["csrf"]):
        raise web.HTTPForbidden(text='{"err":"CSRF không hợp lệ"}', content_type="application/json")
    if not s.get("owner"):
        path = request.path
        feature = ("stats" if "/stats" in path or "/chart" in path else
                   "wd" if "/withdraw" in path or "/wqr/" in path else
                   "dep" if "/deposits" in path or "/deposit/" in path or "/naptien" in path else
                   "user" if "/users" in path or "/user/" in path or "/u2/" in path else
                   "dupe" if "/payout-duplicates" in path else
                   "gift" if "/gifts" in path or "/gift/" in path else
                   "tx3d" if "/tx3d/" in path else
                   "ctl" if "/control" in path else
                   "bc" if "/broadcast" in path or "/vcall" in path else
                   "exp" if "/export/" in path else
                   "reset" if "/reset/" in path else
                   "log" if "/log" in path else
                   "admins" if "/admins" in path else None)
        if feature and not s.get("permissions", {}).get(feature, False):
            raise web.HTTPForbidden(text='{"err":"Tài khoản này không được cấp quyền sử dụng mục này"}', content_type="application/json")
    return tok, s


async def aw_api_me(request):
    tok, s = await asyncio.to_thread(_aw_auth, request)
    return _aw_json({"user": s["user"], "csrf": s["csrf"], "owner": bool(s.get("owner")), "permissions": s.get("permissions", {})})


async def aw_api_logout(request):
    tok, s = await asyncio.to_thread(_aw_auth, request, True)
    _ADMIN_SESSIONS.pop(tok, None)
    await asyncio.to_thread(_aw_log, s["user"], "LOGOUT", "", _aw_ip(request))
    return _aw_json({"ok": True})


def _aw_stats_sync():
    today = "% - " + get_vietnam_date()
    def one(q, a=()):
        r = query(q, a)
        return r[0] if r else (0,)
    users = one("SELECT COUNT(*) FROM users")[0]
    bal = one("SELECT COALESCE(SUM(balance),0) FROM users")[0]
    dep_t = one("SELECT COALESCE(SUM(amount),0) FROM deposit_history WHERE status='success'")[0]
    wd_t = one("SELECT COALESCE(SUM(amount),0) FROM withdraw_history WHERE status='success'")[0]
    dep_d = one("SELECT COALESCE(SUM(amount),0) FROM deposit_history WHERE status='success' AND time LIKE %s", (today,))[0]
    wd_d = one("SELECT COALESCE(SUM(amount),0) FROM withdraw_history WHERE status='success' AND time LIKE %s", (today,))[0]
    pend = one("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM withdraw_history WHERE status='pending'")
    bet_d = 0
    try:
        bet_d = one("SELECT COALESCE(SUM(bet),0) FROM bet_daily WHERE day=%s", (datetime.now(VIETNAM_TZ).date(),))[0]
    except Exception:
        bet_d = 0
    reset_totals = one("SELECT COALESCE(SUM(dep_offset),0), COALESCE(SUM(wd_offset),0) FROM admin_user_stat_resets")
    dep_t = max(0, int(dep_t or 0) - int(reset_totals[0] or 0))
    wd_t = max(0, int(wd_t or 0) - int(reset_totals[1] or 0))
    return {"users": int(users), "balance": int(bal), "dep_total": int(dep_t), "wd_total": int(wd_t),
            "dep_today": int(dep_d), "wd_today": int(wd_d), "wd_pending_n": int(pend[0]), "wd_pending_sum": int(pend[1]),
            "bet_today": int(bet_d or 0)}


async def aw_api_stats(request):
    await asyncio.to_thread(_aw_auth, request)
    return _aw_json(await asyncio.to_thread(_aw_stats_sync))


_AW_WD_SQL = ("SELECT w.id, w.user_id, w.amount, w.status, w.time, w.request_code, w.admin_note, "
              "COALESCE(w.method,''), COALESCE(w.bank,''), COALESCE(w.stk,''), COALESCE(w.acc_name,''), w.memo, "
              "u.bank, u.stk, u.name FROM withdraw_history w LEFT JOIN users u ON u.user_id=w.user_id ")


def _aw_wd_row(r):
    (wid, uid_, amount, status, time_, code, note, method, bank, stk, acc_name, memo, u_bank, u_stk, u_name) = r
    legacy = not (stk or bank)
    if legacy:
        bank, stk, acc_name, method = (u_bank or ""), (u_stk or ""), (u_name or ""), (method or "BANKING")
    return {"id": wid, "user_id": uid_, "amount": int(amount or 0), "status": status, "time": time_, "code": code,
            "note": note, "method": (method or "BANKING").upper(), "bank": bank, "stk": stk, "acc_name": acc_name,
            "memo": memo, "legacy": legacy}


def _aw_withdraws_sync(status, uid):
    cond, args = [], []
    if status == "pending":
        cond.append("w.status='pending'")
    if uid:
        cond.append("w.user_id=%s")
        args.append(uid)
    where = ("WHERE " + " AND ".join(cond) + " ") if cond else ""
    rows = query(_AW_WD_SQL + where + "ORDER BY w.id DESC LIMIT 50", tuple(args)) or []
    return [_aw_wd_row(r) for r in rows]


async def aw_api_withdraws(request):
    await asyncio.to_thread(_aw_auth, request)
    status = "pending" if request.query.get("status") != "all" else "all"
    uid_s = request.query.get("uid", "").strip()
    uid = int(uid_s) if uid_s.isdigit() else None
    return _aw_json({"rows": await asyncio.to_thread(_aw_withdraws_sync, status, uid)})


async def aw_api_wqr(request):
    await asyncio.to_thread(_aw_auth, request)
    wid = request.match_info.get("wid", "")
    if not wid.isdigit():
        raise web.HTTPNotFound()
    rows = await asyncio.to_thread(query, _AW_WD_SQL + "WHERE w.id=%s", (int(wid),))
    if not rows:
        raise web.HTTPNotFound()
    w = _aw_wd_row(rows[0])
    qr_fid = (await asyncio.to_thread(query, "SELECT qr_file_id FROM withdraw_history WHERE id=%s", (int(wid),)) or [[None]])[0][0]
    try:
        if w["method"] == "BANKING" and w["stk"]:
            key = re.sub(r"[^A-Z0-9]", "", str(w["bank"]).upper())
            code_b = _BANK_CODE_ALIASES.get(key, key)
            qr_bank = _BANK_BIN.get(code_b) or code_b
            buf = await asyncio.to_thread(make_local_qr, w["amount"], w["memo"] or str(w["code"] or ""), qr_bank, w["stk"])
            return web.Response(body=buf.getvalue(), content_type="image/png", headers=_AW_SEC_HEADERS)
        if qr_fid:
            f = await application.bot.get_file(qr_fid)
            data = bytes(await f.download_as_bytearray())
            return web.Response(body=data, content_type="image/jpeg", headers=_AW_SEC_HEADERS)
    except Exception as e:
        print(f"aw_api_wqr lỗi #{wid}: {e}")
    raise web.HTTPNotFound()


async def aw_api_withdraw_act(request):
    tok, s = await asyncio.to_thread(_aw_auth, request, True)
    wid_s, act = request.match_info.get("wid", ""), request.match_info.get("act", "")
    if not wid_s.isdigit() or act not in ("approve", "reject", "reject_no_refund"):
        return _aw_json({"err": "Yêu cầu không hợp lệ"}, 400)
    wid = int(wid_s)
    try:
        payload = await request.json()
    except Exception:
        payload = {}
    reason = str((payload or {}).get("reason", "")).strip()[:500]
    if act == "reject_no_refund" and not reason:
        return _aw_json({"err": "Vui lòng nhập lý do từ chối không hoàn tiền"}, 400)
    note = f"Web: {s['user']}"
    if act == "approve":
        r = await asyncio.to_thread(
            query, "UPDATE withdraw_history SET status='success', admin_id=0, admin_note=%s WHERE id=%s AND status='pending' RETURNING user_id, amount",
            (note, wid))
    elif act == "reject":
        r = await asyncio.to_thread(
            query, "UPDATE withdraw_history SET status='rejected', admin_id=0, admin_note=%s WHERE id=%s AND status='pending' RETURNING user_id, amount",
            (note + " - Từ chối (hoàn tiền)", wid))
    else:
        r = await asyncio.to_thread(
            query, "UPDATE withdraw_history SET status='rejected', admin_id=0, admin_note=%s WHERE id=%s AND status='pending' RETURNING user_id, amount",
            (note + " - Từ chối KHÔNG hoàn tiền: " + reason, wid))
    if not r:
        return _aw_json({"err": "Đơn này đã được xử lý rồi hoặc không tồn tại"}, 409)
    u_id, amt = int(r[0][0]), int(r[0][1])
    bot = application.bot
    if act == "approve":
        try:
            await send_group_notice(bot, chat_id=LOG_GROUP_ID, text=(
                f'{ce("📤")} <b>RÚT TIỀN THÀNH CÔNG</b>\n🆔 ID: <code>{mask_user_id(u_id)}</code>\n'
                f'{ce("💰")} Số tiền: <code>{fmt_money(amt)}đ</code>\n{ce("✅")} Trạng thái: Thành công\n⏰ {get_vietnam_datetime_db()}'),
                parse_mode=ParseMode.HTML)
        except Exception:
            pass
        try:
            await bot.send_message(u_id, f'{ce("✅")} Yêu cầu rút <code>{fmt_money(amt)}đ</code> đã được duyệt!\n'
                                         f'{ce("💰")} Số dư hiện tại: <code>{fmt_money(await asyncio.to_thread(get_balance, u_id))}đ</code>',
                                   parse_mode=ParseMode.HTML)
        except Exception:
            pass
    elif act == "reject":
        await asyncio.to_thread(add_money, u_id, amt, "Hoàn tiền rút")
        try:
            await bot.send_message(u_id, f'{ce("❌")} Yêu cầu rút <code>{fmt_money(amt)}đ</code> bị từ chối.\\n'
                                         f'{ce("🔄")} Tiền đã được hoàn về số dư của bạn.\\n{bal_block(u_id)}',
                                   parse_mode=ParseMode.HTML)
        except Exception:
            pass
    else:
        safe_reason = html.escape(reason)
        try:
            await bot.send_message(
                u_id,
                f'{ce("❌")} Yêu cầu rút <code>{fmt_money(amt)}đ</code> đã bị từ chối.\\n'
                f'{ce("📝")} Lý do: {safe_reason}\\n'
                f'{ce("⚠️")} Số tiền của yêu cầu này không được hoàn lại vào số dư.',
                parse_mode=ParseMode.HTML)
        except Exception:
            pass
    await asyncio.to_thread(_aw_log, s["user"], "WITHDRAW_" + act.upper(), f"#{wid} ID {u_id} {amt}đ" + (f" | Lý do: {reason}" if act == "reject_no_refund" else ""), _aw_ip(request))
    return _aw_json({"ok": True})


async def aw_api_deposits(request):
    await asyncio.to_thread(_aw_auth, request)
    rows = await asyncio.to_thread(query, "SELECT id,user_id,amount,status,time FROM deposit_history ORDER BY id DESC LIMIT 50") or []
    return _aw_json({"rows": [{"id": r[0], "user_id": r[1], "amount": int(r[2] or 0), "status": r[3], "time": r[4]} for r in rows]})


async def aw_api_user_act(request):
    tok, s = await asyncio.to_thread(_aw_auth, request, True)
    uid_s, act = request.match_info.get("uid", ""), request.match_info.get("act", "")
    if not uid_s.isdigit() or act not in ("add", "sub", "ban", "unban", "resetbank"):
        return _aw_json({"err": "Yêu cầu không hợp lệ"}, 400)
    uid = int(uid_s)
    ip = _aw_ip(request)
    exists = await asyncio.to_thread(query, "SELECT 1 FROM users WHERE user_id=%s", (uid,))
    if not exists:
        return _aw_json({"err": "Không tìm thấy người dùng"}, 404)
    if act in ("add", "sub"):
        try:
            body = await request.json()
            amt = int(body.get("amount", 0))
        except Exception:
            return _aw_json({"err": "Số tiền không hợp lệ"}, 400)
        if amt <= 0 or amt > 10_000_000_000:
            return _aw_json({"err": "Số tiền không hợp lệ"}, 400)
        if act == "add":
            await asyncio.to_thread(add_money, uid, amt, f"Admin cộng tiền (web {s['user']})")
            msg = f"Đã cộng {fmt_money(amt)}đ"
        else:
            ok = await asyncio.to_thread(sub_money, uid, amt, f"Admin trừ tiền (web {s['user']})")
            if not ok:
                return _aw_json({"err": "Số dư không đủ để trừ"}, 400)
            msg = f"Đã trừ {fmt_money(amt)}đ"
        await asyncio.to_thread(_aw_log, s["user"], "BALANCE_" + act.upper(), f"ID {uid} {amt}đ", ip)
        return _aw_json({"ok": True, "msg": msg})
    if act == "ban":
        await asyncio.to_thread(query, "INSERT INTO banned(user_id) VALUES(%s) ON CONFLICT (user_id) DO NOTHING", (uid,))
        msg = "Đã khóa tài khoản"
    elif act == "unban":
        await asyncio.to_thread(query, "DELETE FROM banned WHERE user_id=%s", (uid,))
        msg = "Đã mở khóa"
    else:
        await asyncio.to_thread(query, "UPDATE users SET bank=NULL, stk=NULL, name=NULL, bank_linked=0 WHERE user_id=%s", (uid,))
        await asyncio.to_thread(query, "DELETE FROM user_payout_accounts WHERE user_id=%s", (uid,))
        msg = "Đã gỡ liên kết ngân hàng"
    await asyncio.to_thread(_aw_log, s["user"], act.upper(), f"ID {uid}", ip)
    return _aw_json({"ok": True, "msg": msg})


async def aw_api_log(request):
    await asyncio.to_thread(_aw_auth, request)
    rows = await asyncio.to_thread(query, "SELECT time, username, action, detail, ip FROM admin_web_log ORDER BY id DESC LIMIT 100") or []
    return _aw_json({"rows": [{"time": r[0], "username": r[1], "action": r[2], "detail": r[3], "ip": r[4]} for r in rows]})


def _aw_jsafe(v):
    if v is None or isinstance(v, (int, float, str, bool)):
        return v
    return str(v)


def _aw_users_sync(q):
    """Tìm user theo ID, tên tài khoản Telegram (nếu có), STK/SĐT hoặc tên chủ TK rút."""
    q = (q or "").strip()[:80]
    q_plain = q[1:] if q.startswith("@") else q
    like = f"%{q_plain}%"
    base = ("SELECT u.user_id, u.balance, COALESCE(u.total_bet,0), u.bank, u.stk, u.name, "
            "GREATEST(0,(SELECT COALESCE(SUM(amount),0) FROM deposit_history d WHERE d.user_id=u.user_id AND d.status='success')-"
            "COALESCE((SELECT dep_offset FROM admin_user_stat_resets z WHERE z.user_id=u.user_id),0)), "
            "GREATEST(0,(SELECT COALESCE(SUM(amount),0) FROM withdraw_history w WHERE w.user_id=u.user_id AND w.status='success')-"
            "COALESCE((SELECT wd_offset FROM admin_user_stat_resets z WHERE z.user_id=u.user_id),0)), "
            "EXISTS(SELECT 1 FROM banned b WHERE b.user_id=u.user_id) FROM users u ")
    if q:
        where = ("WHERE CAST(u.user_id AS TEXT)=%s "
                 "OR COALESCE(u.stk,'') ILIKE %s OR COALESCE(u.name,'') ILIKE %s "
                 "OR COALESCE(u.tg_username,'') ILIKE %s OR COALESCE(u.tg_full_name,'') ILIKE %s "
                 "OR EXISTS (SELECT 1 FROM user_payout_accounts p WHERE p.user_id=u.user_id AND "
                 "(COALESCE(p.account_name,'') ILIKE %s OR COALESCE(p.account_number,'') ILIKE %s "
                 "OR COALESCE(p.bank_code,'') ILIKE %s OR COALESCE(p.method,'') ILIKE %s)) "
                 "ORDER BY u.balance DESC LIMIT 50")
        rows = query(base + where, (q_plain, like, like, like, like, like, like, like, like)) or []
    else:
        rows = query(base + "ORDER BY u.balance DESC LIMIT 20") or []
    out = []
    for r in rows:
        uid = int(r[0])
        linked = query("SELECT method,bank_code,account_number,account_name FROM user_payout_accounts WHERE user_id=%s ORDER BY is_default DESC,id DESC", (uid,)) or []
        out.append({"user_id": uid, "balance": int(r[1] or 0), "total_bet": int(r[2] or 0),
                    "bank": r[3], "stk": r[4], "name": r[5], "dep": int(r[6] or 0),
                    "wd": int(r[7] or 0), "banned": bool(r[8]),
                    "payouts": [{"method": a[0], "bank": a[1], "number": a[2], "name": a[3]} for a in linked]})
    return out



def _aw_payout_duplicates_sync(search=""):
    import unicodedata
    """Nhóm các tài khoản rút tiền có cùng tên chủ tài khoản, chuẩn hoá dấu/khoảng trắng."""
    rows = query(
        """SELECT p.user_id, p.method, p.bank_code, p.account_number,
                  p.account_name, p.is_default, p.created_at
           FROM user_payout_accounts p
           WHERE COALESCE(TRIM(p.account_name),'') <> ''
           ORDER BY UPPER(TRIM(p.account_name)), p.user_id, p.method"""
    ) or []
    groups = {}
    def norm_name(value):
        value = unicodedata.normalize("NFD", str(value or "").strip().upper())
        value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
        return " ".join(value.split())
    for uid, method, bank, number, name, is_default, created in rows:
        key = norm_name(name)
        if not key:
            continue
        item = groups.setdefault(key, {"name": " ".join(str(name).strip().upper().split()), "accounts": [], "users": set(), "methods": {}})
        item["users"].add(int(uid))
        method = str(method or "").upper()
        item["methods"][method] = item["methods"].get(method, 0) + 1
        item["accounts"].append({
            "user_id": int(uid), "method": method, "bank_code": bank or "",
            "account_number": number or "", "account_name": str(name or ""),
            "is_default": bool(is_default), "created_at": str(created or "")
        })
    search = str(search or "").strip().lstrip("@").casefold()
    result = []
    for item in groups.values():
        if len(item["users"]) < 2:
            continue
        if search:
            haystack = [item["name"].casefold()] + [str(uid) for uid in item["users"]]
            for acc in item["accounts"]:
                haystack.extend([str(acc.get("account_number") or "").casefold(),
                                 str(acc.get("bank_code") or "").casefold(),
                                 str(acc.get("method") or "").casefold(),
                                 str(acc.get("account_name") or "").casefold()])
            if not any(search in v for v in haystack):
                continue
        methods = item["methods"]
        result.append({
            "name": item["name"],
            "user_count": len(item["users"]),
            "account_count": len(item["accounts"]),
            "method_counts": methods,
            "users": sorted(item["users"]),
            "accounts": item["accounts"]
        })
    result.sort(key=lambda x: (-x["user_count"], -x["account_count"], x["name"]))
    return {
        "groups": result,
        "group_count": len(result),
        "matched_users": len({uid for g in result for uid in g["users"]}),
        "matched_accounts": sum(g["account_count"] for g in result)
    }


async def aw_api_payout_duplicates(request):
    await asyncio.to_thread(_aw_auth, request)
    data = await asyncio.to_thread(_aw_payout_duplicates_sync, request.query.get("q", ""))
    return _aw_json(data)


async def _aw_capture_telegram_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lưu username/tên Telegram khi user tương tác để web admin tìm được bằng @username."""
    try:
        user = update.effective_user
        if not user:
            return
        get_user(int(user.id))
        full_name = (user.full_name or "").strip()[:160]
        username = (user.username or "").strip().lstrip("@")[:64]
        await asyncio.to_thread(query,
            "UPDATE users SET tg_username=%s,tg_full_name=%s WHERE user_id=%s",
            (username, full_name, int(user.id)))
    except Exception as exc:
        print(f"[web-admin] Không lưu được hồ sơ Telegram: {exc}")


async def aw_api_users(request):
    await asyncio.to_thread(_aw_auth, request)
    try:
        rows = await asyncio.to_thread(_aw_users_sync, request.query.get("q", ""))
        return _aw_json({"rows": rows})
    except Exception as exc:
        print(f"[web-admin] Lỗi tìm người dùng: {exc}")
        return _aw_json({"err": "Không thể tải danh sách người dùng. Kiểm tra cấu trúc database và log máy chủ."}, 500)


def _aw_user_full_sync(uid):
    p = _rp_profile_sync(uid)
    if not p:
        return None
    bonus = p.get("bonus")
    one = lambda q, a=(): (query(q, a) or [(0,)])[0]
    bought = one("SELECT COUNT(*), COALESCE(SUM(reward),0), COALESCE(SUM(CASE WHEN COALESCE(used,0)=1 THEN 1 ELSE 0 END),0) "
                 "FROM giftcodes WHERE created_by=%s", (uid,))
    received = one("SELECT COUNT(*), COALESCE(SUM(reward),0) FROM giftcodes WHERE used_by=%s", (uid,))
    payouts = query("SELECT method, bank_code, account_number, account_name, created_at, is_default "
                    "FROM user_payout_accounts WHERE user_id=%s ORDER BY id DESC", (uid,)) or []
    try:
        remaining = int(get_remaining_bet_required(uid) or 0)
    except Exception:
        remaining = 0
    try:
        dep_today = int(deposited_today(uid) or 0)
    except Exception:
        dep_today = 0
    try:
        vip = str(get_vip_info(p["total_bet"])[0])
    except Exception:
        vip = ""
    # query() trả về danh sách các hàng; mỗi hàng chứa đủ dep_offset và wd_offset.
    # Dùng query thay vì one() để tránh tuple (0,) bị thiếu phần tử thứ hai.
    reset = query("SELECT dep_offset,wd_offset FROM admin_user_stat_resets WHERE user_id=%s", (uid,))
    code_blocked = bool(query("SELECT 1 FROM admin_code_bans WHERE user_id=%s", (uid,)))
    # Chỉ liệt kê code đã cấp riêng cho user; không đưa code dùng chung của
    # người khác vào hồ sơ. Bao gồm CHECKTT/INTERACT và TOP/TICHLUY.
    pending_gifts_raw = query(
        "SELECT code, ctype, reward, expiry FROM giftcodes "
        "WHERE bound_user=%s AND COALESCE(used,0)=0 "
        "ORDER BY created_at DESC, code DESC",
        (uid,)
    ) or []
    _now = get_vietnam_time()
    pending_gifts = []
    for _g in pending_gifts_raw:
        _exp = _g[3]
        _expired = False
        if _exp:
            try:
                _expired = (_now > _exp) if getattr(_exp, "tzinfo", None) else (_now.replace(tzinfo=None) > _exp)
            except Exception:
                _expired = False
        pending_gifts.append({
            "code": str(_g[0]),
            "type": GIFT_TYPES.get(_g[1], {}).get("name", str(_g[1] or "Giftcode")),
            "reward": int(_g[2] or 0),
            "expiry": _aw_jsafe(_exp),
            "expired": bool(_expired),
        })
    dep_offset = int(reset[0][0] or 0) if reset else 0
    wd_offset = int(reset[0][1] or 0) if reset else 0
    return {
        "code_blocked": code_blocked,
        "pending_giftcodes": pending_gifts,
        "balance": p["balance"], "refs": int(p["refs"] or 0), "refed": int(p["refed"] or 0),
        "bank": p["bank"], "stk": p["stk"], "name": p["name"], "bank_linked": bool(p["bank_linked"]),
        "last_checkin": p["last_checkin"], "last_withdraw": p["last_withdraw"], "first_time": p["first_time"],
        "total_bet": p["total_bet"], "wins": p["wins"], "dep": max(0,int(p["dep"] or 0)-dep_offset), "dep_n": p["dep_n"], "wd": max(0,int(p["wd"] or 0)-wd_offset), "wd_n": p["wd_n"],
        "wd_pend": p["wd_pend"], "wd_pend_n": p["wd_pend_n"], "banned": p["banned"],
        "banned_games": p["banned_games"], "banned_features": p["banned_features"],
        "codes_used": p["codes_used"], "gifts_used": p["gifts_used"],
        "bonus": ({"amount": int(bonus[0] or 0), "required": int(bonus[1] or 0), "current": int(bonus[2] or 0)} if bonus else None),
        "wager_remaining": remaining, "dep_today": dep_today, "vip": vip,
        "bought_n": int(bought[0] or 0), "bought_sum": int(bought[1] or 0), "bought_used": int(bought[2] or 0),
        "received_n": int(received[0] or 0), "received_sum": int(received[1] or 0),
        "payouts": [{"method": r[0], "bank": r[1], "number": r[2], "name": r[3], "at": _aw_jsafe(r[4]), "default": bool(r[5])} for r in payouts],
    }


async def aw_api_user_full(request):
    await asyncio.to_thread(_aw_auth, request)
    uid_s = request.match_info.get("uid", "")
    if not uid_s.isdigit():
        return _aw_json({"err": "ID không hợp lệ"}, 400)
    uid = int(uid_s)
    try:
        p = await asyncio.to_thread(_aw_user_full_sync, uid)
    except Exception as e:
        traceback.print_exc()
        return _aw_json({"err": f"Lỗi tải hồ sơ: {e}"}, 500)
    if p is None:
        return _aw_json({"err": "Không tìm thấy người dùng"}, 404)
    tg = ""
    try:
        chat = await asyncio.wait_for(application.bot.get_chat(uid), timeout=4)
        tg = (("@" + chat.username) if getattr(chat, "username", None) else "") or (getattr(chat, "full_name", None) or "")
    except Exception:
        tg = ""
    p["tg_name"] = tg
    return _aw_json({"user_id": uid, "p": p})


_AW_SECTIONS = {"his", "nap", "rut", "cuoc", "code", "mua", "gift"}


def _aw_user_section_sync(uid, kind):
    d = _rp_collect(kind, uid, None, None)
    rows = d.get("rows", [])
    total = len(rows)
    return {
        "headers": d.get("headers", []), "money_cols": d.get("money_cols", []), "status_col": d.get("status_col"),
        "total": total, "rows": [[_aw_jsafe(c) for c in r] for r in rows[:300]],
        "extra": {k: _aw_jsafe(v) for k, v in (d.get("extra") or {}).items()},
    }


async def aw_api_user_section(request):
    await asyncio.to_thread(_aw_auth, request)
    uid_s, kind = request.match_info.get("uid", ""), request.match_info.get("kind", "")
    if not uid_s.isdigit() or kind not in _AW_SECTIONS:
        return _aw_json({"err": "Yêu cầu không hợp lệ"}, 400)
    return _aw_json(await asyncio.to_thread(_aw_user_section_sync, int(uid_s), kind))


def _aw_gift_summary_sync():
    expired_sql = "COALESCE(used,0)=0 AND expiry IS NOT NULL AND expiry < NOW()"
    rows = query(
        "SELECT ctype, COUNT(*), "
        "COALESCE(SUM(CASE WHEN COALESCE(used,0)=1 THEN 1 ELSE 0 END),0), "
        f"COALESCE(SUM(CASE WHEN {expired_sql} THEN 1 ELSE 0 END),0), "
        "COALESCE(SUM(reward),0), COALESCE(SUM(CASE WHEN COALESCE(used,0)=1 THEN reward ELSE 0 END),0) "
        "FROM giftcodes GROUP BY ctype ORDER BY COUNT(*) DESC") or []
    types = []
    tot = [0, 0, 0, 0, 0]
    for r in rows:
        total, used, exp, val, uval = int(r[1] or 0), int(r[2] or 0), int(r[3] or 0), int(r[4] or 0), int(r[5] or 0)
        types.append({"type": r[0] or "?", "name": GIFT_TYPES.get(r[0], {}).get("name", r[0] or "Khác"),
                      "total": total, "used": used, "expired": exp, "unused": total - used - exp, "value": val, "used_value": uval})
        for i, v in enumerate((total, used, exp, val, uval)):
            tot[i] += v
    buyers = query(
        "SELECT created_by, COUNT(*), COALESCE(SUM(reward),0), "
        "COALESCE(SUM(CASE WHEN COALESCE(used,0)=1 THEN 1 ELSE 0 END),0) FROM giftcodes "
        "WHERE ctype='CODEMUA' GROUP BY created_by ORDER BY SUM(reward) DESC LIMIT 15") or []
    reg = (query("SELECT COUNT(*), COALESCE(SUM(uses),0) FROM codes") or [(0, 0)])[0]
    reg_used = (query("SELECT COUNT(*) FROM code_usage") or [(0,)])[0][0]
    return {
        "types": types,
        "total": {"count": tot[0], "used": tot[1], "expired": tot[2], "unused": tot[0] - tot[1] - tot[2], "value": tot[3], "used_value": tot[4]},
        "buyers": [{"user_id": r[0], "count": int(r[1] or 0), "value": int(r[2] or 0), "used": int(r[3] or 0)} for r in buyers],
        "regular": {"codes": int(reg[0] or 0), "uses_left": int(reg[1] or 0), "entered": int(reg_used or 0)},
    }


async def aw_api_gift_summary(request):
    await asyncio.to_thread(_aw_auth, request)
    return _aw_json(await asyncio.to_thread(_aw_gift_summary_sync))


def _aw_gifts_sync(ctype, status, q, page):
    cond, args = [], []
    if ctype and ctype in GIFT_TYPES:
        cond.append("ctype=%s"); args.append(ctype)
    if status == "used":
        cond.append("COALESCE(used,0)=1")
    elif status == "unused":
        cond.append("COALESCE(used,0)=0 AND (expiry IS NULL OR expiry >= NOW())")
    elif status == "expired":
        cond.append("COALESCE(used,0)=0 AND expiry IS NOT NULL AND expiry < NOW()")
    q = (q or "").strip()[:60]
    if q:
        cond.append("(code ILIKE %s OR CAST(created_by AS TEXT)=%s OR CAST(used_by AS TEXT)=%s OR CAST(bound_user AS TEXT)=%s)")
        args += [f"%{q}%", q, q, q]
    where = ("WHERE " + " AND ".join(cond) + " ") if cond else ""
    cnt = (query("SELECT COUNT(*) FROM giftcodes " + where, tuple(args)) or [(0,)])[0][0]
    raw = query("SELECT code, ctype, reward, wager, expiry, COALESCE(used,0), used_by, used_at, created_by, created_at, bound_user, "
                "COALESCE(require_total_dep,0), CASE WHEN COALESCE(used,0)=0 AND expiry IS NOT NULL AND expiry < NOW() THEN 1 ELSE 0 END "
                "FROM giftcodes " + where + "LIMIT 5000", tuple(args)) or []
    epoch = datetime(1970, 1, 1).date()
    key_idx = 7 if status == "used" else 9
    raw = sorted(raw, key=lambda r: (_rp_date(r[key_idx]) or epoch, str(r[key_idx] or "")), reverse=True)
    size = 50
    page = max(1, page)
    part = raw[(page - 1) * size: page * size]
    out = []
    for r in part:
        st = "Đã dùng" if r[5] else ("Hết hạn" if r[12] else "Chưa dùng")
        out.append({"code": r[0], "type": GIFT_TYPES.get(r[1], {}).get("name", r[1] or ""), "reward": int(r[2] or 0),
                    "wager": r[3], "expiry": str(r[4] or "")[:19], "status": st, "used_by": r[6], "used_at": r[7],
                    "created_by": r[8], "created_at": r[9], "bound_user": r[10], "need_dep": int(r[11] or 0)})
    return {"rows": out, "total": int(cnt or 0), "page": page, "pages": max(1, (min(int(cnt or 0), 5000) + size - 1) // size)}


async def aw_api_gifts(request):
    await asyncio.to_thread(_aw_auth, request)
    page_s = request.query.get("page", "1")
    return _aw_json(await asyncio.to_thread(
        _aw_gifts_sync, request.query.get("type", ""), request.query.get("status", "all"),
        request.query.get("q", ""), int(page_s) if page_s.isdigit() else 1))



_AW_FEATURES = {"stats":"Tổng quan","wd":"Rút tiền","dep":"Nạp tiền","user":"Người dùng","dupe":"Trùng tên rút tiền","gift":"Giftcode","tx3d":"Ép TX3D","ctl":"Điều khiển","bc":"Thông báo","exp":"Xuất file","reset":"Reset","log":"Nhật ký","fan":"Duyệt Fan"}

async def aw_api_admins(request):
    tok, sess = await asyncio.to_thread(_aw_auth, request, True)
    if not sess.get("owner"):
        return _aw_json({"err":"Chỉ chủ sở hữu mới được quản lý admin phụ"},403)
    if request.method == "GET":
        rows = await asyncio.to_thread(query, "SELECT username,created_at,last_login,active,is_owner,permissions FROM admin_web_users ORDER BY is_owner DESC,username")
        out=[]
        for r in rows or []:
            try: perms=json.loads(r[5] or "{}")
            except Exception: perms={}
            out.append({"username":r[0],"created_at":r[1],"last_login":r[2],"active":bool(r[3]),"owner":bool(r[4]),"permissions":perms})
        return _aw_json({"rows":out,"features":_AW_FEATURES})
    try: body=await request.json()
    except Exception: return _aw_json({"err":"Dữ liệu không hợp lệ"},400)
    action=str(body.get("action",""))
    username=str(body.get("username","")).strip().lower()
    if not _USERNAME_RE.fullmatch(username): return _aw_json({"err":"Tên đăng nhập 3-20 ký tự: chữ thường, số, gạch dưới"},400)
    if action=="create":
        password=str(body.get("password",""))
        if len(password)<8: return _aw_json({"err":"Mật khẩu tối thiểu 8 ký tự"},400)
        if await asyncio.to_thread(query,"SELECT 1 FROM admin_web_users WHERE username=%s",(username,)):
            return _aw_json({"err":"Tên đăng nhập đã tồn tại"},409)
        perms={k:bool((body.get("permissions") or {}).get(k)) for k in _AW_FEATURES}
        pw=await asyncio.to_thread(_aw_hash_password,password)
        await asyncio.to_thread(query,"INSERT INTO admin_web_users(username,pw_hash,created_by,created_at,active,is_owner,permissions) VALUES(%s,%s,%s,%s,1,0,%s)",
            (username,pw,sess["user"],get_vietnam_datetime_db(),json.dumps(perms)))
        await asyncio.to_thread(_aw_log,sess["user"],"CREATE_SUBADMIN",username,_aw_ip(request))
        return _aw_json({"ok":True,"msg":"Đã tạo admin phụ"})
    if action=="permissions":
        target=await asyncio.to_thread(query,"SELECT is_owner FROM admin_web_users WHERE username=%s",(username,))
        if not target: return _aw_json({"err":"Không tìm thấy admin"},404)
        if target[0][0]: return _aw_json({"err":"Không thay đổi quyền chủ sở hữu"},400)
        perms={k:bool((body.get("permissions") or {}).get(k)) for k in _AW_FEATURES}
        await asyncio.to_thread(query,"UPDATE admin_web_users SET permissions=%s WHERE username=%s",(json.dumps(perms),username))
        await asyncio.to_thread(_aw_kill_sessions,username)
        await asyncio.to_thread(_aw_log,sess["user"],"SET_ADMIN_PERMISSIONS",username+" "+json.dumps(perms),_aw_ip(request))
        return _aw_json({"ok":True,"msg":"Đã lưu quyền. Admin phụ cần đăng nhập lại."})
    if action in ("disable","enable","delete"):
        target=await asyncio.to_thread(query,"SELECT is_owner FROM admin_web_users WHERE username=%s",(username,))
        if not target: return _aw_json({"err":"Không tìm thấy admin"},404)
        if target[0][0]: return _aw_json({"err":"Không thể khóa/xóa chủ sở hữu"},400)
        if action=="delete": await asyncio.to_thread(query,"DELETE FROM admin_web_users WHERE username=%s",(username,))
        else: await asyncio.to_thread(query,"UPDATE admin_web_users SET active=%s WHERE username=%s",(1 if action=="enable" else 0,username))
        await asyncio.to_thread(_aw_kill_sessions,username)
        await asyncio.to_thread(_aw_log,sess["user"],action.upper()+"_ADMIN",username,_aw_ip(request))
        return _aw_json({"ok":True,"msg":"Đã cập nhật tài khoản"})
    return _aw_json({"err":"Thao tác không hợp lệ"},400)

async def aw_api_user_codeban(request):
    tok,sess=await asyncio.to_thread(_aw_auth,request,True)
    uid_s=request.match_info.get("uid","")
    if not uid_s.isdigit(): return _aw_json({"err":"ID không hợp lệ"},400)
    uid=int(uid_s)
    try: body=await request.json()
    except Exception: body={}
    if body.get("blocked"):
        await asyncio.to_thread(query,"INSERT INTO admin_code_bans(user_id,created_by,created_at) VALUES(%s,%s,%s) ON CONFLICT(user_id) DO UPDATE SET created_by=EXCLUDED.created_by,created_at=EXCLUDED.created_at",(uid,sess["user"],get_vietnam_datetime_db()))
        msg="Đã cấm nhập giftcode"
    else:
        await asyncio.to_thread(query,"DELETE FROM admin_code_bans WHERE user_id=%s",(uid,))
        msg="Đã mở quyền nhập giftcode"
    await asyncio.to_thread(_aw_log,sess["user"],"CODE_BAN" if body.get("blocked") else "CODE_UNBAN",f"ID {uid}",_aw_ip(request))
    return _aw_json({"ok":True,"msg":msg})

async def aw_api_user_reset_stats(request):
    tok,sess=await asyncio.to_thread(_aw_auth,request,True)
    uid_s=request.match_info.get("uid","")
    if not uid_s.isdigit(): return _aw_json({"err":"ID không hợp lệ"},400)
    uid=int(uid_s)
    try: body=await request.json()
    except Exception: body={}
    kinds=[k for k in body.get("kinds",[]) if k in ("dep","wd")]
    if not kinds: return _aw_json({"err":"Chọn tổng nạp hoặc tổng rút cần đặt lại"},400)
    row=await asyncio.to_thread(query,"SELECT COALESCE(SUM(amount),0) FROM deposit_history WHERE user_id=%s AND status='success'",(uid,))
    dep=int(row[0][0] or 0)
    row=await asyncio.to_thread(query,"SELECT COALESCE(SUM(amount),0) FROM withdraw_history WHERE user_id=%s AND status='success'",(uid,))
    wd=int(row[0][0] or 0)
    old=await asyncio.to_thread(query,"SELECT dep_offset,wd_offset FROM admin_user_stat_resets WHERE user_id=%s",(uid,))
    od,ow=(int(old[0][0] or 0),int(old[0][1] or 0)) if old else (0,0)
    if "dep" in kinds: od=dep
    if "wd" in kinds: ow=wd
    await asyncio.to_thread(query,"INSERT INTO admin_user_stat_resets(user_id,dep_offset,wd_offset,reset_by,reset_at) VALUES(%s,%s,%s,%s,%s) ON CONFLICT(user_id) DO UPDATE SET dep_offset=EXCLUDED.dep_offset,wd_offset=EXCLUDED.wd_offset,reset_by=EXCLUDED.reset_by,reset_at=EXCLUDED.reset_at",(uid,od,ow,sess["user"],get_vietnam_datetime_db()))
    await asyncio.to_thread(_aw_log,sess["user"],"RESET_USER_STATS",f"ID {uid}: {','.join(kinds)}",_aw_ip(request))
    return _aw_json({"ok":True,"msg":"Đã đặt lại số tổng hiển thị; lịch sử giao dịch gốc vẫn được giữ nguyên."})


async def aw_api_fan(request):
    tok, sess = await asyncio.to_thread(_aw_auth, request, True)
    if request.method == "GET":
        rows = await asyncio.to_thread(query,
            """SELECT r.id,r.user_id,r.streak_days,r.status,r.created_at,r.gift_code,
                      u.tg_username,u.tg_full_name
               FROM fan_requests r LEFT JOIN users u ON u.user_id=r.user_id
               ORDER BY CASE WHEN r.status='pending' THEN 0 ELSE 1 END,r.id DESC LIMIT 300""")
        return _aw_json({"rows":[{"id":int(x[0]),"user_id":int(x[1]),"streak_days":int(x[2] or 0),
            "status":x[3],"created_at":str(x[4] or ""),"gift_code":x[5],
            "username":x[6] or "","full_name":x[7] or ""} for x in (rows or [])]})
    try: body=await request.json()
    except Exception: return _aw_json({"err":"Dữ liệu không hợp lệ"},400)
    rid=body.get("id")
    act=str(body.get("action",""))
    if not str(rid).isdigit() or act not in ("approve","reject"):
        return _aw_json({"err":"Yêu cầu không hợp lệ"},400)
    row=await asyncio.to_thread(query,"SELECT user_id,status FROM fan_requests WHERE id=%s",(int(rid),))
    if not row or row[0][1]!="pending":
        return _aw_json({"err":"Yêu cầu không tồn tại hoặc đã được xử lý"},409)
    uid=int(row[0][0])
    if act=="reject":
        await asyncio.to_thread(query,"UPDATE fan_requests SET status='rejected',reviewed_at=NOW(),reviewed_by=%s WHERE id=%s AND status='pending'",(sess["user"],int(rid)))
        try: await application.bot.send_message(uid,"Yêu cầu Fan +30K của bạn chưa được duyệt. Vui lòng liên hệ Admin để biết thêm chi tiết.")
        except Exception: pass
        await asyncio.to_thread(_aw_log,sess["user"],"FAN_REJECT",f"ID {uid}",_aw_ip(request))
        return _aw_json({"ok":True,"msg":"Đã từ chối yêu cầu"})
    code="FAN"+''.join(random.choices("ABCDEFGHJKLMNPQRSTUVWXYZ23456789",k=8))
    # Thưởng 30.000đ, yêu cầu cược x3; giftcode hết hạn sau 3 ngày.
    created=await asyncio.to_thread(query,
        """INSERT INTO giftcodes(code,ctype,reward,wager,expiry,require_deposit,required_amount,
                  bound_user,used,created_by,created_at)
           VALUES(%s,'FAN',30000,3,NOW()+INTERVAL '3 days',0,0,%s,0,0,%s)
           ON CONFLICT(code) DO NOTHING RETURNING code""",
        (code,uid,get_vietnam_datetime_db()))
    if not created:
        return _aw_json({"err":"Không tạo được giftcode, vui lòng thử lại"},500)
    updated=await asyncio.to_thread(query,
        "UPDATE fan_requests SET status='approved',reviewed_at=NOW(),reviewed_by=%s,gift_code=%s WHERE id=%s AND status='pending' RETURNING id",
        (sess["user"],code,int(rid)))
    if not updated:
        await asyncio.to_thread(query,"DELETE FROM giftcodes WHERE code=%s AND used=0",(code,))
        return _aw_json({"err":"Yêu cầu đã được xử lý đồng thời"},409)
    try:
        await application.bot.send_message(uid,
            f"🎉 <b>FAN +30.000Đ ĐÃ ĐƯỢC DUYỆT!</b>\n\n🔑 Giftcode: <code>{code}</code>\n💰 Thưởng: <b>30.000đ</b>\n🎯 Vòng cược: <b>x3</b>\n⏳ Hạn sử dụng: <b>3 ngày</b>\n\nNhập mã bằng lệnh <code>/code {code}</code>.",
            parse_mode=ParseMode.HTML)
    except Exception:
        pass
    await asyncio.to_thread(_aw_log,sess["user"],"FAN_APPROVE",f"ID {uid} code {code}",_aw_ip(request))
    return _aw_json({"ok":True,"msg":"Đã duyệt và gửi giftcode cho người dùng","code":code})

def admin_web_register_routes(app):
    app.router.add_get("/admin/login", aw_login_page)
    app.router.add_post("/admin/login", aw_login_post)
    app.router.add_get("/admin", aw_home)
    app.router.add_get("/admin/", aw_home)
    app.router.add_get("/admin/app.js", aw_js)
    app.router.add_get("/admin/api/me", aw_api_me)
    app.router.add_post("/admin/api/logout", aw_api_logout)
    app.router.add_get("/admin/api/stats", aw_api_stats)
    app.router.add_route("*", "/admin/api/fan", aw_api_fan)
    app.router.add_get("/admin/api/withdraws", aw_api_withdraws)
    app.router.add_get("/admin/api/wqr/{wid}", aw_api_wqr)
    app.router.add_post("/admin/api/withdraw/{wid}/{act}", aw_api_withdraw_act)
    app.router.add_get("/admin/api/deposits", aw_api_deposits)
    app.router.add_get("/admin/api/users", aw_api_users)
    app.router.add_get("/admin/api/payout-duplicates", aw_api_payout_duplicates)
    app.router.add_get("/admin/api/user/{uid}/full", aw_api_user_full)
    app.router.add_get("/admin/api/user/{uid}/sec/{kind}", aw_api_user_section)
    app.router.add_get("/admin/api/gifts/summary", aw_api_gift_summary)
    app.router.add_get("/admin/api/gifts", aw_api_gifts)
    app.router.add_post("/admin/api/user/{uid}/{act}", aw_api_user_act)
    app.router.add_get("/admin/api/log", aw_api_log)
    app.router.add_route("*", "/admin/api/admins", aw_api_admins)
    app.router.add_post("/admin/api/user/{uid}/codeban", aw_api_user_codeban)
    app.router.add_post("/admin/api/user/{uid}/reset-stats", aw_api_user_reset_stats)


# ---------- Lệnh bot quản lý tài khoản web admin (chỉ admin, chỉ chat riêng) ----------
async def _aw_private_only(update):
    chat = update.effective_chat
    if chat is not None and chat.type != "private":
        await update.effective_message.reply_text("🚫 Lệnh này chứa mật khẩu nên chỉ dùng trong chat riêng với bot.")
        return False
    return True


def _aw_web_url():
    base = os.getenv("ADMIN_WEB_URL", "").rstrip("/")
    return (base + "/admin") if base else "https://<tên-miền-của-bạn>/admin"


@admin_only
async def taoadmin_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/taoadmin <tên_đăng_nhập> [mật_khẩu] - tạo tài khoản web admin (bỏ trống mật khẩu = tự tạo ngẫu nhiên)."""
    msg = update.effective_message
    if not await _aw_private_only(update):
        return
    args = ctx.args or []
    if not args:
        return await msg.reply_text(
            "Cú pháp: <code>/taoadmin [tên_đăng_nhập] [mật_khẩu]</code>\n"
            "Tên: 3-20 ký tự gồm chữ thường, số, gạch dưới. Mật khẩu tối thiểu 8 ký tự; bỏ trống để bot tự tạo.",
            parse_mode=ParseMode.HTML)
    username = args[0].strip().lower()
    if not _USERNAME_RE.fullmatch(username):
        return await msg.reply_text("❌ Tên đăng nhập chỉ gồm chữ thường, số, gạch dưới (3-20 ký tự).")
    password = args[1] if len(args) > 1 else _aw_gen_password()
    if len(password) < 8:
        return await msg.reply_text("❌ Mật khẩu tối thiểu 8 ký tự.")
    if query("SELECT 1 FROM admin_web_users WHERE username=%s", (username,)):
        return await msg.reply_text("❌ Tên đăng nhập này đã tồn tại. Dùng /doimkadmin để đổi mật khẩu.")
    pw_hash = await asyncio.to_thread(_aw_hash_password, password)
    # /taoadmin đầu tiên tạo tài khoản CHỦ SỞ HỮU Web Admin; các lần sau là admin phụ.
    owner_exists = bool(query("SELECT 1 FROM admin_web_users WHERE is_owner=1 LIMIT 1"))
    is_owner = 0 if owner_exists else 1
    permissions = json.dumps({k: True for k in _AW_FEATURES}) if is_owner else json.dumps({k: False for k in _AW_FEATURES})
    query("INSERT INTO admin_web_users(username,pw_hash,created_by,created_at,active,is_owner,permissions) "
          "VALUES(%s,%s,%s,%s,1,%s,%s)",
          (username, pw_hash, update.effective_user.id, get_vietnam_datetime_db(), is_owner, permissions))
    _aw_log(f"bot:{update.effective_user.id}", "CREATE_ADMIN", username)
    try:
        await msg.delete()   # xoá tin nhắn lệnh có chứa mật khẩu
    except Exception:
        pass
    await ctx.bot.send_message(
        update.effective_chat.id,
        f'✅ <b>ĐÃ TẠO TÀI KHOẢN WEB ADMIN</b>\n\n👤 Tên đăng nhập: <code>{html.escape(username)}</code>\n'
        f'🔑 Mật khẩu: <code>{html.escape(password)}</code>\n🌐 Link: {html.escape(_aw_web_url())}\n\n'
        f'⚠️ Lưu mật khẩu ở nơi an toàn rồi xoá tin nhắn này. Mật khẩu không xem lại được.',
        parse_mode=ParseMode.HTML)


@admin_only
async def doimkadmin_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/doimkadmin <tên> [mật_khẩu_mới]"""
    msg = update.effective_message
    if not await _aw_private_only(update):
        return
    args = ctx.args or []
    if not args:
        return await msg.reply_text("Cú pháp: <code>/doimkadmin [tên_đăng_nhập] [mật_khẩu_mới]</code>", parse_mode=ParseMode.HTML)
    username = args[0].strip().lower()
    password = args[1] if len(args) > 1 else _aw_gen_password()
    if len(password) < 8:
        return await msg.reply_text("❌ Mật khẩu tối thiểu 8 ký tự.")
    if not query("SELECT 1 FROM admin_web_users WHERE username=%s", (username,)):
        return await msg.reply_text("❌ Không có tài khoản này.")
    pw_hash = await asyncio.to_thread(_aw_hash_password, password)
    query("UPDATE admin_web_users SET pw_hash=%s, active=1 WHERE username=%s", (pw_hash, username))
    _aw_kill_sessions(username)
    _aw_log(f"bot:{update.effective_user.id}", "RESET_PASSWORD", username)
    try:
        await msg.delete()
    except Exception:
        pass
    await ctx.bot.send_message(
        update.effective_chat.id,
        f'✅ Đã đổi mật khẩu cho <code>{html.escape(username)}</code>\n🔑 Mật khẩu mới: <code>{html.escape(password)}</code>\n'
        f'(Các phiên đăng nhập cũ đã bị đăng xuất.)', parse_mode=ParseMode.HTML)


@admin_only
async def xoaadmin_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/xoaadmin <tên> - xoá tài khoản web admin và đăng xuất ngay."""
    msg = update.effective_message
    args = ctx.args or []
    if not args:
        return await msg.reply_text("Cú pháp: <code>/xoaadmin [tên_đăng_nhập]</code>", parse_mode=ParseMode.HTML)
    username = args[0].strip().lower()
    r = query("DELETE FROM admin_web_users WHERE username=%s RETURNING username", (username,))
    if not r:
        return await msg.reply_text("❌ Không có tài khoản này.")
    _aw_kill_sessions(username)
    _aw_log(f"bot:{update.effective_user.id}", "DELETE_ADMIN", username)
    await msg.reply_text(f"✅ Đã xoá tài khoản web admin <code>{html.escape(username)}</code>.", parse_mode=ParseMode.HTML)


@admin_only
async def dsadminweb_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/dsadminweb - danh sách tài khoản web admin."""
    rows = query("SELECT username, created_at, last_login FROM admin_web_users ORDER BY created_at") or []
    if not rows:
        return await update.effective_message.reply_text("Chưa có tài khoản web admin. Tạo bằng /taoadmin [tên] [mật_khẩu].")
    text = "🌐 <b>TÀI KHOẢN WEB ADMIN</b>\n\n" + "\n".join(
        f"• <code>{html.escape(r[0])}</code> · tạo: {html.escape(str(r[1] or '-'))} · đăng nhập gần nhất: {html.escape(str(r[2] or 'chưa')) }"
        for r in rows) + f"\n\n🌐 {html.escape(_aw_web_url())}"
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


# ============================================================
# WEB ADMIN PLUS  —  DÁN NGUYÊN KHỐI NÀY NGAY TRƯỚC DÒNG:
#     async def start_webhook_server():
# rồi thêm 1 dòng  admin_web_plus_register(app)  vào trong start_webhook_server()
# (ngay sau dòng admin_web_register_routes(app)).
#
# Thêm vào web /admin:
#   • Tổng quan + biểu đồ 14 ngày        • Duyệt / từ chối NẠP, nạp thủ công
#   • Điều khiển: bảo trì từng game/nạp/rút/hệ thống, tắt-mở room, khoá cược nhóm,
#     chỉnh giờ vàng, % hoàn cược, hũ jackpot, tên bot
#   • Trang người dùng: đặt/reset số dư, cấm/gỡ cấm game, khoá nạp/rút, khoá/reset hoàn trả,
#     xoá/thêm vòng cược, tặng khuyến mãi, nhắn riêng, xuất Excel của user
#   • Giftcode: tạo nhiều loại, xoá       • Thông báo toàn bộ user, thêm vòng cược hàng loạt
#   • Xuất file Excel: thống kê / nạp / rút
# Mọi thao tác đều ghi vào Nhật ký web admin và bắt buộc đăng nhập + CSRF như cũ.
# ============================================================
_AWP_TASKS = set()
_AWP_BC = {"running": False, "sent": 0, "failed": 0, "total": 0}
_AWP_PERIODS = ("ngay", "tuan", "all")


def _awp_int(v, lo=None, hi=None):
    n = int(v) if isinstance(v, (int, float)) and not isinstance(v, bool) else int(parse_money_text(str(v)))
    if (lo is not None and n < lo) or (hi is not None and n > hi):
        raise ValueError("out of range")
    return n


async def _awp_body(request):
    try:
        b = await request.json()
        return b if isinstance(b, dict) else {}
    except Exception:
        return {}


async def _awp_send(uid, text, **kw):
    try:
        await application.bot.send_message(uid, text, parse_mode=ParseMode.HTML, **kw)
        return True
    except Exception as e:
        print(f"[web-plus] không nhắn được {uid}: {e}")
        return False


# ---------- Biểu đồ ----------
def _awp_chart_sync(days):
    today = get_vietnam_time().date()
    start = today - timedelta(days=days - 1)
    sheets, _ = _stat_collect_sync(start, today, False)
    rows = sheets[1]["rows"]
    return [{"day": r[0], "dep": int(r[2]), "wd": int(r[4]), "bet": int(r[6]), "pnl": int(r[8])} for r in rows]


async def awp_api_chart(request):
    await asyncio.to_thread(_aw_auth, request)
    d = request.query.get("days", "14")
    days = max(3, min(60, int(d))) if d.isdigit() else 14
    return _aw_json({"rows": await asyncio.to_thread(_awp_chart_sync, days)})


# ---------- Điều khiển: bảo trì / room / cài đặt ----------
def _awp_control_sync():
    games = [{"alias": a, "key": v[0], "gid": v[1], "name": v[2], "mt": check_mt(v[0])} for a, v in ADMIN_GAMES.items()]
    feats = [{"alias": a, "key": v[0], "name": v[1], "mt": check_mt(v[0])} for a, v in ADMIN_FEATURES.items()]
    rooms = [{"id": g, "muted": _is_room_muted(g), "bet": bool(room_betting_enabled.get(g, True))} for g in GROUP_IDS]
    return {
        "games": games, "features": feats, "rooms": rooms,
        "system": is_system_maintenance(), "total": is_total_maintenance(),
        "promo_mode": promo_mode(), "promo_active": promo_is_active(), "promo_windows": promo_windows_text(),
        "rebate_ngay": get_rebate_pct("ngay"), "rebate_tuan": get_rebate_pct("tuan"),
        "jackpot": int(get_jackpot()), "tx3d_pot": int(TX3D.pot), "bot_name": get_bot_name(),
        "promo_pct": int(get_setting("promo_pct", PROMO_PCT) or PROMO_PCT),
        "promo_text": get_setting("promo_group_text", "") or "",
        "payout_channels": [
            {"key": "mt_rut_momo", "name": "MOMO", "mt": check_mt("mt_rut_momo")},
            {"key": "mt_rut_zalopay", "name": "ZALOPAY", "mt": check_mt("mt_rut_zalopay")},
            {"key": "mt_rut_banking", "name": "BANKING", "mt": check_mt("mt_rut_banking")},
        ],
    }


async def awp_api_control(request):
    await asyncio.to_thread(_aw_auth, request)
    return _aw_json(await asyncio.to_thread(_awp_control_sync))


def _awp_mt_keys():
    keys = {v[0] for v in ADMIN_GAMES.values()} | {v[0] for v in ADMIN_FEATURES.values()}
    return keys | {"system_maintenance", "mt_tongbao", "mt_rut_momo", "mt_rut_zalopay", "mt_rut_banking"}


async def awp_api_mt(request):
    tok, s = await asyncio.to_thread(_aw_auth, request, True)
    b = await _awp_body(request)
    key, val = str(b.get("key", "")), "1" if str(b.get("value", "0")) in ("1", "True", "true") else "0"
    if key not in _awp_mt_keys():
        return _aw_json({"err": "Khoá bảo trì không hợp lệ"}, 400)
    await asyncio.to_thread(set_setting, key, val)
    await asyncio.to_thread(_aw_log, s["user"], "MAINTENANCE", f"{key}={val}", _aw_ip(request))
    return _aw_json({"ok": True})


async def awp_api_mtall(request):
    tok, s = await asyncio.to_thread(_aw_auth, request, True)
    b = await _awp_body(request)
    val = "1" if str(b.get("value", "0")) in ("1", "True", "true") else "0"
    scope = str(b.get("scope", "games"))
    keys = []
    if scope in ("games", "all"):
        keys += [v[0] for v in ADMIN_GAMES.values()]
    if scope in ("features", "all"):
        keys += [v[0] for v in ADMIN_FEATURES.values()]
    if not keys:
        return _aw_json({"err": "Phạm vi không hợp lệ"}, 400)
    for k in keys:
        await asyncio.to_thread(set_setting, k, val)
    await asyncio.to_thread(_aw_log, s["user"], "MAINTENANCE_ALL", f"{scope}={val}", _aw_ip(request))
    return _aw_json({"ok": True})


async def awp_api_room(request):
    tok, s = await asyncio.to_thread(_aw_auth, request, True)
    b = await _awp_body(request)
    act = str(b.get("act", ""))
    gid = b.get("id")
    try:
        ids = [int(gid)] if gid not in (None, "", "all") else list(GROUP_IDS)
        if any(g not in GROUP_IDS for g in ids) or act not in ("mute", "unmute", "betoff", "beton"):
            raise ValueError
    except (ValueError, TypeError):
        return _aw_json({"err": "Yêu cầu không hợp lệ"}, 400)
    for g in ids:
        if act == "mute":
            await asyncio.to_thread(_set_room_muted, g, True)
        elif act == "unmute":
            await asyncio.to_thread(_set_room_muted, g, False)
        else:
            room_betting_enabled[g] = (act == "beton")
    await asyncio.to_thread(_aw_log, s["user"], "ROOM_" + act.upper(), str(ids), _aw_ip(request))
    return _aw_json({"ok": True})


def _awp_setting_sync(name, value):
    if name == "promo_pct":
        n = _awp_int(value, 0, 100)
        globals()["PROMO_PCT"] = n
        set_setting("promo_pct", n)
        return f"Khuyến mãi nạp: {n}%"
    if name == "promo_group_text":
        v = str(value or "").strip()[:3000]
        set_setting("promo_group_text", v)
        return "Đã lưu nội dung thông báo khuyến mãi"
    if name == "promo_mode":
        v = str(value).lower()
        if v not in ("auto", "on", "off"):
            raise ValueError
        set_setting("promo_mode", v)
        return f"Giờ vàng: {v}"
    if name in ("rebate_ngay", "rebate_tuan"):
        f = float(str(value).replace(",", "."))
        if not 0 <= f <= 100:
            raise ValueError
        set_setting(f"rebate_{name[7:]}_pct", f)
        return f"Hoàn cược {name[7:]}: {f:g}%"
    if name == "jackpot":
        n = _awp_int(value, 0, 10 ** 13)
        update_jackpot(n)
        return f"Hũ jackpot: {fmt_money(n)}đ"
    if name == "tx3d_pot":
        n = _awp_int(value, 0, 10 ** 13)
        TX3D.pot = n
        set_setting(TX3D_POT_KEY, n)
        return f"Hũ Tài Xỉu 3D: {fmt_money(n)}đ"
    if name == "bot_name":
        v = str(value).strip()[:60]
        if not v:
            raise ValueError
        set_setting("bot_display_name", v)
        return "Đã đổi tên bot"
    raise ValueError


async def awp_api_setting(request):
    tok, s = await asyncio.to_thread(_aw_auth, request, True)
    b = await _awp_body(request)
    try:
        msg = await asyncio.to_thread(_awp_setting_sync, str(b.get("name", "")), b.get("value"))
    except (ValueError, TypeError):
        return _aw_json({"err": "Giá trị không hợp lệ"}, 400)
    await asyncio.to_thread(_aw_log, s["user"], "SETTING", f"{b.get('name')}={b.get('value')}", _aw_ip(request))
    return _aw_json({"ok": True, "msg": msg})


# ---------- Nạp tiền ----------
def _awp_deposits_sync(status):
    sql = "SELECT id,user_id,amount,status,time,ref_code FROM deposit_history "
    if status == "pending":
        sql += "WHERE status='pending' "
    rows = query(sql + "ORDER BY id DESC LIMIT 100") or []
    return [{"id": r[0], "user_id": r[1], "amount": int(r[2] or 0), "status": r[3], "time": r[4], "ref": r[5] or ""} for r in rows]


async def awp_api_deposits2(request):
    await asyncio.to_thread(_aw_auth, request)
    st = "pending" if request.query.get("status") != "all" else "all"
    return _aw_json({"rows": await asyncio.to_thread(_awp_deposits_sync, st)})


def _awp_credit_deposit_sync(uid, amount, note):
    prev = get_balance(uid)
    cleared, extra = apply_deposit_wager_rule(uid, prev, amount)
    add_money(uid, amount, note)
    try:
        nap_orders_mark_paid(uid)
    except Exception:
        pass
    return cleared, extra


async def _awp_after_deposit(uid, amount, cleared, extra):
    bot = application.bot
    try:
        await notify_deposit_wager(bot, uid, cleared, extra)
    except Exception:
        pass
    masked = mask_user_id(uid)
    try:
        await send_group_notice(bot, chat_id=LOG_GROUP_ID, parse_mode=ParseMode.HTML,
                                text=f'{ce("✅")} <b>THÔNG BÁO NẠP TIỀN</b>\n{ce("👥")} ID: <code>{masked}</code>\n'
                                     f'{ce("💰")} Số tiền: <code>+{fmt_money(amount)}đ</code>')
    except Exception:
        pass
    offer = await asyncio.to_thread(promo_build_offer, uid, amount)
    head = (f'{ce("✅")} <b>NẠP TIỀN THÀNH CÔNG!</b>\n\n{ce("💰")} Số tiền nạp: <code>+{fmt_money(amount)}đ</code>\n'
            f'{bal_block(uid)}{deposit_wager_line(uid)}')
    if offer:
        await _awp_send(uid, head + "\n\n" + offer[0], reply_markup=offer[1])
    else:
        await _awp_send(uid, head)


async def awp_api_deposit_act(request):
    tok, s = await asyncio.to_thread(_aw_auth, request, True)
    did, act = request.match_info.get("did", ""), request.match_info.get("act", "")
    if not did.isdigit() or act not in ("approve", "reject"):
        return _aw_json({"err": "Yêu cầu không hợp lệ"}, 400)
    new_status = "success" if act == "approve" else "rejected"
    r = await asyncio.to_thread(
        query, "UPDATE deposit_history SET status=%s, admin_id=0 WHERE id=%s AND status='pending' RETURNING user_id, amount",
        (new_status, int(did)))
    if not r:
        return _aw_json({"err": "Đơn nạp đã được xử lý hoặc không tồn tại"}, 409)
    uid, amount = int(r[0][0]), int(r[0][1])
    if act == "approve":
        cleared, extra = await asyncio.to_thread(
            _awp_credit_deposit_sync, uid, amount, f"Nạp tiền (duyệt web {s['user']}) +{amount:,}đ")
        await _awp_after_deposit(uid, amount, cleared, extra)
    else:
        await _awp_send(uid, f'{ce("❌")} Yêu cầu nạp <code>{fmt_money(amount)}đ</code> của bạn đã bị từ chối.')
    await asyncio.to_thread(_aw_log, s["user"], "DEPOSIT_" + act.upper(), f"#{did} ID {uid} {amount}đ", _aw_ip(request))
    return _aw_json({"ok": True})


async def awp_api_naptien(request):
    tok, s = await asyncio.to_thread(_aw_auth, request, True)
    b = await _awp_body(request)
    try:
        uid = int(str(b.get("uid", "")).strip())
        amount = _awp_int(b.get("amount"), 10000, 10 ** 10)
    except (ValueError, TypeError):
        return _aw_json({"err": "ID hoặc số tiền không hợp lệ (tối thiểu 10.000đ)"}, 400)
    if not await asyncio.to_thread(query, "SELECT 1 FROM users WHERE user_id=%s", (uid,)):
        return _aw_json({"err": "Không tìm thấy người dùng"}, 404)
    await asyncio.to_thread(
        query, "INSERT INTO deposit_history (user_id, amount, admin_id, status, time) VALUES (%s,%s,0,'success',%s)",
        (uid, amount, get_vietnam_datetime_db()))
    cleared, extra = await asyncio.to_thread(
        _awp_credit_deposit_sync, uid, amount, f"Nạp tiền +{amount:,}đ (web {s['user']})")
    await _awp_after_deposit(uid, amount, cleared, extra)
    await asyncio.to_thread(_aw_log, s["user"], "NAPTIEN", f"ID {uid} {amount}đ", _aw_ip(request))
    return _aw_json({"ok": True, "msg": f"Đã nạp {fmt_money(amount)}đ cho {uid}"})


# ---------- Quản lý người dùng nâng cao ----------
def _awp_user_state_sync(uid):
    gb = [int(r[0]) for r in (query("SELECT game_id FROM banned_games WHERE user_id=%s", (uid,)) or [])]
    fb = [str(r[0]) for r in (query("SELECT feature FROM banned_features WHERE user_id=%s", (uid,)) or [])]
    st = get_bet_progress_status(uid)
    try:
        items, pend, live = _rh_preview_sync(uid, "all")
    except Exception:
        items = pend = live = 0
    return {
        "games": [{"alias": a, "gid": v[1], "name": v[2]} for a, v in ADMIN_GAMES.items()],
        "banned_game_ids": gb, "features": fb, "banned": bool(is_banned(uid)),
        "wager": ({k: (float(v) if isinstance(v, float) else v) for k, v in st.items()} if st else None),
        "rewards": {"items": items, "pending": pend, "live": live}, "balance": get_balance(uid),
    }


async def awp_api_user_state(request):
    await asyncio.to_thread(_aw_auth, request)
    uid = request.match_info.get("uid", "")
    if not uid.isdigit():
        return _aw_json({"err": "ID không hợp lệ"}, 400)
    return _aw_json(await asyncio.to_thread(_awp_user_state_sync, int(uid)))


def _awp_user_act_sync(uid, act, b, who):
    tag = f"(web {who})"
    if act in ("credit", "debit"):
        if uid in ADMIN_IDS:
            return False, "Không thể điều chỉnh số dư tài khoản admin", None
        amt = _awp_int(b.get("amount"), 1, 10 ** 13)
        if act == "credit":
            add_money(uid, amt, f"Admin cộng tiền {tag}")
            return True, f"Đã cộng {fmt_money(amt)}đ; số dư mới {fmt_money(get_balance(uid))}đ", None
        if get_balance(uid) < amt:
            return False, "Số dư người dùng không đủ để trừ", None
        if not sub_money(uid, amt, f"Admin trừ tiền {tag}"):
            return False, "Không trừ được số dư", None
        return True, f"Đã trừ {fmt_money(amt)}đ; số dư mới {fmt_money(get_balance(uid))}đ", None
    if act in ("banuser", "unbanuser"):
        if uid in ADMIN_IDS:
            return False, "Không thể khoá tài khoản admin", None
        if act == "banuser":
            query("INSERT INTO banned(user_id) VALUES(%s) ON CONFLICT DO NOTHING", (uid,))
        else:
            query("DELETE FROM banned WHERE user_id=%s", (uid,))
        return True, ("Đã khoá tài khoản" if act == "banuser" else "Đã mở khoá tài khoản"), None
    if act in ("setbal", "resetbal"):
        if uid in ADMIN_IDS:
            return False, "Không thể đổi số dư tài khoản admin", None
        new = 0 if act == "resetbal" else _awp_int(b.get("amount"), 0, 10 ** 13)
        old = get_balance(uid)
        if new - old:
            add_money(uid, new - old, f"Admin điều chỉnh số dư {tag}")
        return True, f"Số dư: {fmt_money(old)}đ → {fmt_money(new)}đ", None
    if act in ("camgame", "mogame"):
        g = str(b.get("game", "")).lower()
        if act == "mogame" and g == "all":
            query("DELETE FROM banned_games WHERE user_id=%s", (uid,))
            return True, "Đã gỡ cấm tất cả game", None
        if g not in ADMIN_GAMES:
            return False, "Game không hợp lệ", None
        gid = ADMIN_GAMES[g][1]
        if act == "camgame":
            query("INSERT INTO banned_games(user_id,game_id) VALUES(%s,%s) ON CONFLICT DO NOTHING", (uid, gid))
        else:
            query("DELETE FROM banned_games WHERE user_id=%s AND game_id=%s", (uid, gid))
        return True, f'{"Đã cấm" if act == "camgame" else "Đã gỡ cấm"} {ADMIN_GAMES[g][2]}', None
    if act in ("camtn", "motn"):
        w = str(b.get("what", "")).lower()
        if w not in ("nap", "rut", "all") or (act == "camtn" and w == "all"):
            return False, "Loại không hợp lệ", None
        if act == "camtn":
            query("INSERT INTO banned_features(user_id,feature) VALUES(%s,%s) ON CONFLICT DO NOTHING", (uid, w))
        elif w == "all":
            query("DELETE FROM banned_features WHERE user_id=%s AND feature IN ('nap','rut')", (uid,))
        else:
            query("DELETE FROM banned_features WHERE user_id=%s AND feature=%s", (uid, w))
        return True, f'{"Đã khoá" if act == "camtn" else "Đã mở"} {w.upper()}', None
    if act in ("camhoan", "mohoan"):
        p = str(b.get("period", "")).lower()
        if p not in _AWP_PERIODS:
            return False, "Loại không hợp lệ", None
        feats = ["hoan_ngay", "hoan_tuan"] if p == "all" else [f"hoan_{p}"]
        for f in feats:
            if act == "camhoan":
                query("INSERT INTO banned_features(user_id,feature) VALUES(%s,%s) ON CONFLICT DO NOTHING", (uid, f))
            else:
                query("DELETE FROM banned_features WHERE user_id=%s AND feature=%s", (uid, f))
        _REWARD_BAN_CACHE.pop(uid, None)
        return True, f'{"Đã khoá" if act == "camhoan" else "Đã mở"} nhận hoàn trả ({p})', None
    if act == "resethoan":
        p = str(b.get("period", "all")).lower()
        if p not in _AWP_PERIODS:
            return False, "Loại không hợp lệ", None
        res = _rh_apply_sync(uid, p)
        if res is None:
            return False, "Lỗi cơ sở dữ liệu, chưa reset được", None
        return True, f"Đã reset hoàn trả: xoá {res[0]} khoản = {fmt_money(res[1])}đ", None
    if act == "xoacuoc":
        row = query("DELETE FROM user_bonus WHERE user_id=%s RETURNING required_bet", (uid,))
        return True, ("Đã xoá vòng cược" if row else "User không có vòng cược"), \
            ({"text": f'{ce("🔓")} Admin đã xoá yêu cầu vòng cược của bạn. Bạn có thể rút tiền bình thường.'} if row else None)
    if act == "themcuoc":
        amt = _awp_int(b.get("amount"), -10 ** 13, 10 ** 13)
        row = query("SELECT required_bet, current_bet FROM user_bonus WHERE user_id=%s", (uid,)) or []
        if not row or int(row[0][0] or 0) <= 0:
            return False, "User không có vòng cược để cộng", None
        req, cur = int(row[0][0]), int(row[0][1] or 0)
        new = max(0, cur + amt)
        query("UPDATE user_bonus SET current_bet=%s WHERE user_id=%s", (new, uid))
        return True, f"Tiến độ cược: {fmt_money(new)}đ / {fmt_money(req)}đ", ({"done": (uid, new, req)} if new >= req else None)
    if act == "themvong":
        amt = _awp_int(b.get("amount"), 1, 10 ** 13)
        add_wager_requirement(uid, 0, amt)
        return True, f"Đã thêm yêu cầu cược {fmt_money(amt)}đ", \
            {"text": f'{ce("🎯")} <b>THÔNG BÁO VÒNG CƯỢC</b>\nBạn được yêu cầu cược thêm <code>{fmt_money(amt)}đ</code> trước khi rút tiền.'}
    if act == "kmnap":
        amt = _awp_int(b.get("amount"), 1, 10 ** 12)
        req = add_bonus_with_requirement(uid, amt)
        return True, f"Đã tặng {fmt_money(amt)}đ (cược {fmt_money(req)}đ)", \
            {"text": f'{ce("🎁")} <b>KHUYẾN MÃI</b>\nBạn nhận <code>+{fmt_money(amt)}đ</code>. Cần cược <code>{fmt_money(req)}đ</code> trước khi rút.'}
    return False, "Thao tác không hợp lệ", None


async def awp_api_user_act(request):
    tok, s = await asyncio.to_thread(_aw_auth, request, True)
    us, act = request.match_info.get("uid", ""), request.match_info.get("act", "")
    if not us.isdigit():
        return _aw_json({"err": "ID không hợp lệ"}, 400)
    uid = int(us)
    if not await asyncio.to_thread(query, "SELECT 1 FROM users WHERE user_id=%s", (uid,)):
        return _aw_json({"err": "Không tìm thấy người dùng"}, 404)
    b = await _awp_body(request)
    if act == "message":
        text = str(b.get("text", "")).strip()[:3500]
        if not text:
            return _aw_json({"err": "Nội dung trống"}, 400)
        ok = await _awp_send(uid, f'{ce("✍️")} <b>PHẢN HỒI TỪ ADMIN:</b>\n\n{html.escape(text)}')
        await asyncio.to_thread(_aw_log, s["user"], "MESSAGE", f"ID {uid}", _aw_ip(request))
        return _aw_json({"ok": ok, "msg": "Đã gửi" if ok else "Không gửi được (user chưa /start bot?)"})
    try:
        ok, msg, notify = await asyncio.to_thread(_awp_user_act_sync, uid, act, b, s["user"])
    except (ValueError, TypeError):
        return _aw_json({"err": "Dữ liệu không hợp lệ"}, 400)
    if not ok:
        return _aw_json({"err": msg}, 400)
    if notify:
        if notify.get("text"):
            await _awp_send(uid, notify["text"])
        if notify.get("done"):
            await check_and_notify_bet_completion(*notify["done"])
    await asyncio.to_thread(_aw_log, s["user"], "USER_" + act.upper(), f"ID {uid} {msg}", _aw_ip(request))
    return _aw_json({"ok": True, "msg": msg})


# ---------- Giftcode ----------
async def awp_api_gift_types(request):
    await asyncio.to_thread(_aw_auth, request)
    return _aw_json({"types": [{"type": k, "name": v["name"]} for k, v in GIFT_TYPES.items()]})


async def awp_api_gift_create(request):
    tok, s = await asyncio.to_thread(_aw_auth, request, True)
    b = await _awp_body(request)
    ctype = str(b.get("ctype", ""))
    if ctype not in GIFT_TYPES:
        return _aw_json({"err": "Loại code không hợp lệ"}, 400)

    def num(key, lo, hi, label, default=None):
        try:
            return _awp_int(b.get(key, default), lo, hi)
        except (ValueError, TypeError):
            raise ValueError(label)

    try:
        st = {"ctype": ctype,
              "reward": num("reward", 1000, 10 ** 8, "Giá trị mỗi code phải từ 1.000đ đến 100.000.000đ"),
              "wager": num("wager", 0, 100, "Vòng cược phải từ 0 đến 100", 0),
              "duration": num("minutes", 1, 525600, "Hạn dùng phải từ 1 phút đến 365 ngày"),
              "qty": num("qty", 1, 100, "Số lượng code phải từ 1 đến 100", 1),
              "require_deposit": 0, "required_amount": 0, "bound_user": None}
        if str(b.get("req_dep", "")).strip():
            st["required_amount"] = num("req_dep", 1000, 10 ** 10, "Yêu cầu nạp phải từ 1.000đ trở lên")
            st["require_deposit"] = 1
        if str(b.get("bound", "")).strip():
            try:
                st["bound_user"] = int(str(b.get("bound")).strip())
            except ValueError:
                raise ValueError("ID người dùng không hợp lệ")
    except ValueError as e:
        return _aw_json({"err": str(e) or "Thông tin code không hợp lệ"}, 400)
    codes, expiry = await asyncio.to_thread(_create_gift_codes, st, 0)
    await asyncio.to_thread(_aw_log, s["user"], "GIFT_CREATE",
                            f"{ctype} x{len(codes)} {st['reward']}đ vòng cược x{st['wager']}", _aw_ip(request))
    return _aw_json({"ok": True, "codes": codes, "expiry": expiry.strftime("%d/%m/%Y %H:%M"),
                     "reward": st["reward"], "wager": st["wager"]})


async def awp_api_gift_delete(request):
    tok, s = await asyncio.to_thread(_aw_auth, request, True)
    b = await _awp_body(request)
    code = str(b.get("code", "")).strip().upper()[:60]
    r = await asyncio.to_thread(query, "DELETE FROM giftcodes WHERE code=%s RETURNING reward", (code,))
    if not r:
        return _aw_json({"err": "Không tìm thấy code"}, 404)
    await asyncio.to_thread(_aw_log, s["user"], "GIFT_DELETE", code, _aw_ip(request))
    return _aw_json({"ok": True, "msg": f"Đã xoá {code}"})


# ---------- Code chưa sử dụng (toàn bộ loại code) ----------
_AWP_CODE_LABEL = {
    "TANTHU": "CODETANTHU", "CODEMUA": "CODEMUA", "INTERACT": "CODETT", "GIOVANG": "CODEGIOVANG",
    "NAP": "CODENAP", "TRIAN": "CODETRIAN", "TICHLUY": "CODETICHLUY",
    "DAYTHANG": "CODEDAYTHANG", "DAYTHUA": "CODEDAYTHUA",
}


def _awp_unused_groups_sync():
    """Tóm tắt toàn bộ code CHƯA SỬ DỤNG, chia theo từng loại."""
    stat = {}
    for r in query(
            "SELECT ctype, COUNT(*), COALESCE(SUM(reward),0), "
            "COALESCE(SUM(CASE WHEN expiry IS NOT NULL AND expiry < NOW() THEN 1 ELSE 0 END),0) "
            "FROM giftcodes WHERE COALESCE(used,0)=0 GROUP BY ctype") or []:
        stat[r[0]] = (int(r[1] or 0), int(r[2] or 0), int(r[3] or 0))
    ctypes = list(GIFT_TYPES.keys()) + [k for k in stat if k not in GIFT_TYPES]
    groups = []
    for ct in ctypes:
        cnt, val, exp = stat.get(ct, (0, 0, 0))
        meta = GIFT_TYPES.get(ct, {})
        groups.append({"key": "gift:" + str(ct), "src": "gift", "ctype": ct,
                       "label": _AWP_CODE_LABEL.get(ct, "CODE" + str(ct or "KHAC")),
                       "name": meta.get("name", str(ct or "Khác")), "icon": meta.get("icon", "🎁"),
                       "count": cnt, "value": val, "expired": exp})
    # Code thường (/taocode): còn lượt dùng
    r = (query("SELECT COUNT(*), COALESCE(SUM(reward),0) FROM codes WHERE COALESCE(uses,0)>0") or [(0, 0)])[0]
    groups.append({"key": "codes", "src": "codes", "ctype": "", "label": "CODETHUONG",
                   "name": "Code thường (/taocode)", "icon": "🔑",
                   "count": int(r[0] or 0), "value": int(r[1] or 0), "expired": 0})
    # Bảng cũ: chỉ hiện khi còn dữ liệu
    r = (query("SELECT COUNT(*), COALESCE(SUM(reward),0) FROM codenap WHERE COALESCE(used,0)=0") or [(0, 0)])[0]
    if int(r[0] or 0) > 0:
        groups.append({"key": "codenap", "src": "codenap", "ctype": "", "label": "CODENAP_CU",
                       "name": "Code nạp (bảng cũ)", "icon": "💳",
                       "count": int(r[0] or 0), "value": int(r[1] or 0), "expired": 0})
    r = (query("SELECT COUNT(*) FROM tanthu_code WHERE COALESCE(used,0)=0") or [(0,)])[0]
    if int(r[0] or 0) > 0:
        groups.append({"key": "tanthu_code", "src": "tanthu_code", "ctype": "", "label": "CODETANTHU_CU",
                       "name": "Code tân thủ (bảng cũ)", "icon": "🎁",
                       "count": int(r[0] or 0), "value": 0, "expired": 0})
    return {"groups": groups}


def _awp_user_infos(ids):
    """Thông tin đầy đủ của danh sách ID người dùng: {id: {...}}."""
    ids = sorted({int(i) for i in ids if i})
    if not ids:
        return {}
    info = {}
    for r in query("SELECT user_id, name, balance, bank, stk, total_bet FROM users WHERE user_id = ANY(%s)", (ids,)) or []:
        info[int(r[0])] = {"name": r[1], "balance": int(r[2] or 0), "bank": r[3], "stk": r[4],
                           "total_bet": int(r[5] or 0), "dep": 0, "wd": 0, "banned": False, "code_blocked": False}
    for r in query("SELECT user_id, COALESCE(SUM(amount),0) FROM deposit_history "
                   "WHERE status='success' AND user_id = ANY(%s) GROUP BY user_id", (ids,)) or []:
        if int(r[0]) in info:
            info[int(r[0])]["dep"] = int(r[1] or 0)
    for r in query("SELECT user_id, COALESCE(SUM(amount),0) FROM withdraw_history "
                   "WHERE status='success' AND user_id = ANY(%s) GROUP BY user_id", (ids,)) or []:
        if int(r[0]) in info:
            info[int(r[0])]["wd"] = int(r[1] or 0)
    for r in query("SELECT user_id FROM admin_code_bans WHERE user_id = ANY(%s)", (ids,)) or []:
        if int(r[0]) in info:
            info[int(r[0])]["code_blocked"] = True
    for r in query("SELECT user_id FROM spam_permanent_bans WHERE user_id = ANY(%s)", (ids,)) or []:
        if int(r[0]) in info:
            info[int(r[0])]["banned"] = True
    return info


def _awp_unused_rows_sync(key, status, q, page):
    key = str(key or "")
    status = status if status in ("all", "valid", "expired") else "all"
    q = (q or "").strip()[:60]
    size = 30
    page = max(1, page)
    off = (page - 1) * size
    rows = []   # mỗi phần tử: dict đã có owner_id / owner_role
    cnt = 0
    if key.startswith("gift:"):
        ct = key[5:]
        cond, args = ["COALESCE(used,0)=0", "ctype=%s"], [ct]
        if status == "valid":
            cond.append("(expiry IS NULL OR expiry >= NOW())")
        elif status == "expired":
            cond.append("(expiry IS NOT NULL AND expiry < NOW())")
        if q:
            cond.append("(code ILIKE %s OR CAST(bound_user AS TEXT)=%s OR CAST(created_by AS TEXT)=%s)")
            args += [f"%{q}%", q, q]
        where = " WHERE " + " AND ".join(cond)
        cnt = (query("SELECT COUNT(*) FROM giftcodes" + where, tuple(args)) or [(0,)])[0][0]
        raw = query("SELECT code, reward, wager, expiry, bound_user, created_by, created_at, "
                    "COALESCE(require_total_dep,0), COALESCE(required_amount,0), "
                    "CASE WHEN expiry IS NOT NULL AND expiry < NOW() THEN 1 ELSE 0 END "
                    "FROM giftcodes" + where + " ORDER BY expiry DESC NULLS LAST, code LIMIT %s OFFSET %s",
                    tuple(args) + (size, off)) or []
        for r in raw:
            owner, role = None, ""
            if r[4]:
                owner, role = int(r[4]), "Chủ code (được cấp riêng)"
            elif ct == "CODEMUA" and r[5]:
                owner, role = int(r[5]), "Chủ code (người mua)"
            creator = int(r[5]) if r[5] and int(r[5]) != owner else None
            rows.append({"code": r[0], "reward": int(r[1] or 0), "wager": r[2], "expiry": str(r[3] or "")[:19],
                         "expired": bool(r[9]), "created_at": r[6], "owner_id": owner, "owner_role": role,
                         "creator": creator, "need_dep": int(r[7] or 0), "need_today": int(r[8] or 0)})
    elif key == "codes":
        cond, args = ["COALESCE(uses,0)>0"], []
        if q:
            cond.append("code ILIKE %s"); args.append(f"%{q}%")
        where = " WHERE " + " AND ".join(cond)
        cnt = (query("SELECT COUNT(*) FROM codes" + where, tuple(args)) or [(0,)])[0][0]
        for r in query("SELECT code, reward, uses FROM codes" + where + " ORDER BY code LIMIT %s OFFSET %s",
                       tuple(args) + (size, off)) or []:
            rows.append({"code": r[0], "reward": int(r[1] or 0), "uses": int(r[2] or 0), "expiry": "", "expired": False,
                         "owner_id": None, "owner_role": ""})
    elif key == "codenap":
        cond, args = ["COALESCE(used,0)=0"], []
        if q:
            cond.append("(code ILIKE %s OR CAST(created_by AS TEXT)=%s)"); args += [f"%{q}%", q]
        where = " WHERE " + " AND ".join(cond)
        cnt = (query("SELECT COUNT(*) FROM codenap" + where, tuple(args)) or [(0,)])[0][0]
        for r in query("SELECT code, reward, wager, expiry, created_by, required_amount FROM codenap" + where +
                       " ORDER BY code LIMIT %s OFFSET %s", tuple(args) + (size, off)) or []:
            rows.append({"code": r[0], "reward": int(r[1] or 0), "wager": r[2], "expiry": str(r[3] or ""), "expired": False,
                         "owner_id": None, "owner_role": "", "creator": int(r[4]) if r[4] else None,
                         "need_today": int(r[5] or 0)})
    elif key == "tanthu_code":
        cond, args = ["COALESCE(used,0)=0"], []
        if q:
            cond.append("(code ILIKE %s OR CAST(user_id AS TEXT)=%s)"); args += [f"%{q}%", q]
        where = " WHERE " + " AND ".join(cond)
        cnt = (query("SELECT COUNT(*) FROM tanthu_code" + where, tuple(args)) or [(0,)])[0][0]
        for r in query("SELECT code, user_id, received_at FROM tanthu_code" + where +
                       " ORDER BY received_at DESC NULLS LAST LIMIT %s OFFSET %s", tuple(args) + (size, off)) or []:
            rows.append({"code": r[0], "reward": 0, "expiry": "", "expired": False, "created_at": r[2],
                         "owner_id": int(r[1]) if r[1] else None, "owner_role": "Chủ code (đã nhận)"})
    else:
        return {"err": "Loại code không hợp lệ"}
    infos = _awp_user_infos([x.get("owner_id") for x in rows])
    for x in rows:
        oid = x.pop("owner_id", None)
        role = x.pop("owner_role", "")
        x["owner"] = ({"id": oid, "role": role, "info": infos.get(oid)} if oid else None)
    cnt = int(cnt or 0)
    return {"rows": rows, "total": cnt, "page": page, "pages": max(1, (cnt + size - 1) // size)}


async def awp_api_unused(request):
    await asyncio.to_thread(_aw_auth, request)
    key = request.query.get("key", "")
    if not key:
        return _aw_json(await asyncio.to_thread(_awp_unused_groups_sync))
    page_s = request.query.get("page", "1")
    res = await asyncio.to_thread(_awp_unused_rows_sync, key, request.query.get("status", "all"),
                                  request.query.get("q", ""), int(page_s) if page_s.isdigit() else 1)
    if res.get("err"):
        return _aw_json(res, 400)
    return _aw_json(res)


async def awp_api_unused_delete(request):
    """Xoá 1 code chưa sử dụng."""
    tok, s = await asyncio.to_thread(_aw_auth, request, True)
    b = await _awp_body(request)
    src = str(b.get("src", ""))
    code = str(b.get("code", "")).strip().upper()[:80]
    if not code:
        return _aw_json({"err": "Thiếu mã code"}, 400)
    sql = {
        "gift": "DELETE FROM giftcodes WHERE code=%s AND COALESCE(used,0)=0 RETURNING code",
        "codes": "DELETE FROM codes WHERE code=%s RETURNING code",
        "codenap": "DELETE FROM codenap WHERE code=%s AND COALESCE(used,0)=0 RETURNING code",
        "tanthu_code": "DELETE FROM tanthu_code WHERE code=%s AND COALESCE(used,0)=0 RETURNING code",
    }.get(src)
    if not sql:
        return _aw_json({"err": "Nguồn code không hợp lệ"}, 400)
    r = await asyncio.to_thread(query, sql, (code,))
    if not r:
        return _aw_json({"err": "Không tìm thấy code (có thể đã được dùng hoặc đã xoá)"}, 404)
    await asyncio.to_thread(_aw_log, s["user"], "UNUSED_CODE_DELETE", f"{src} {code}", _aw_ip(request))
    return _aw_json({"ok": True, "msg": f"Đã xoá {code}"})


async def awp_api_unused_delete_all(request):
    """Xoá toàn bộ code chưa sử dụng của 1 loại (scope=all) hoặc chỉ code đã hết hạn (scope=expired)."""
    tok, s = await asyncio.to_thread(_aw_auth, request, True)
    b = await _awp_body(request)
    src = str(b.get("src", ""))
    ctype = str(b.get("ctype", ""))[:40]
    scope = "expired" if str(b.get("scope", "all")) == "expired" else "all"
    if src == "gift":
        if not ctype:
            return _aw_json({"err": "Thiếu loại code"}, 400)
        extra = " AND expiry IS NOT NULL AND expiry < NOW()" if scope == "expired" else ""
        r = await asyncio.to_thread(
            query, "DELETE FROM giftcodes WHERE ctype=%s AND COALESCE(used,0)=0" + extra + " RETURNING code", (ctype,))
        label = _AWP_CODE_LABEL.get(ctype, ctype)
    elif src == "codes" and scope == "all":
        r = await asyncio.to_thread(query, "DELETE FROM codes WHERE COALESCE(uses,0)>0 RETURNING code")
        label = "CODETHUONG"
    elif src == "codenap" and scope == "all":
        r = await asyncio.to_thread(query, "DELETE FROM codenap WHERE COALESCE(used,0)=0 RETURNING code")
        label = "CODENAP_CU"
    elif src == "tanthu_code" and scope == "all":
        r = await asyncio.to_thread(query, "DELETE FROM tanthu_code WHERE COALESCE(used,0)=0 RETURNING code")
        label = "CODETANTHU_CU"
    else:
        return _aw_json({"err": "Yêu cầu không hợp lệ"}, 400)
    n = len(r or [])
    await asyncio.to_thread(_aw_log, s["user"], "UNUSED_CODE_DELETE_ALL", f"{label} {scope} x{n}", _aw_ip(request))
    return _aw_json({"ok": True, "deleted": n,
                     "msg": f"Đã xoá {n} code {label} " + ("hết hạn" if scope == "expired" else "chưa sử dụng")})


# ---------- Thông báo / vòng cược hàng loạt ----------
async def _awp_broadcast_task(users, text):
    _AWP_BC.update(running=True, sent=0, failed=0, total=len(users))
    try:
        message = f'{ce("🔔")} <b>THÔNG BÁO MỚI</b>\\n\\n{html.escape(text)}'

        async def update_progress(sent, failed, total):
            _AWP_BC.update(sent=sent, failed=failed, total=total)

        await _broadcast_all(application.bot, users, message, update_progress)
    except Exception as exc:
        print(f"[web-plus] broadcast worker error: {exc}")
    finally:
        _AWP_BC["running"] = False


async def awp_api_broadcast(request):
    tok, s = await asyncio.to_thread(_aw_auth, request, True)
    b = await _awp_body(request)
    text = str(b.get("text", "")).strip()[:3500]
    if not text:
        return _aw_json({"err": "Nội dung trống"}, 400)
    if _AWP_BC["running"] or _BROADCAST_LOCK.locked():
        return _aw_json({"err": "Đang có đợt gửi khác chạy, vui lòng chờ"}, 409)
    users = await asyncio.to_thread(query, "SELECT user_id FROM users") or []
    t = asyncio.create_task(_awp_broadcast_task(users, text))
    _AWP_TASKS.add(t)
    t.add_done_callback(_AWP_TASKS.discard)
    await asyncio.to_thread(_aw_log, s["user"], "BROADCAST", f"{len(users)} người", _aw_ip(request))
    return _aw_json({"ok": True, "total": len(users)})


async def awp_api_broadcast_status(request):
    await asyncio.to_thread(_aw_auth, request)
    return _aw_json(dict(_AWP_BC))


async def awp_api_vcall_preview(request):
    await asyncio.to_thread(_aw_auth, request)
    try:
        mult = _vc_parse_mult(request.query.get("mult", ""))
    except (ValueError, TypeError):
        return _aw_json({"err": "Số vòng không hợp lệ"}, 400)
    rows = await asyncio.to_thread(query, "SELECT user_id, balance FROM users WHERE balance>0") or []
    rows = [(int(u), int(bl)) for u, bl in rows if int(u) not in ADMIN_IDS]
    return _aw_json({"users": len(rows), "total": sum(int(bl * mult) for _u, bl in rows)})


async def awp_api_vcall(request):
    tok, s = await asyncio.to_thread(_aw_auth, request, True)
    b = await _awp_body(request)
    try:
        mult = _vc_parse_mult(b.get("mult", ""))
    except (ValueError, TypeError):
        return _aw_json({"err": "Số vòng không hợp lệ"}, 400)
    done, total, targets = await asyncio.to_thread(_vcall_apply_sync, mult)
    t = asyncio.create_task(_vcall_notify(application.bot, mult, targets))
    _AWP_TASKS.add(t)
    t.add_done_callback(_AWP_TASKS.discard)
    await asyncio.to_thread(_aw_log, s["user"], "VCALL", f"x{mult:g} {done} người", _aw_ip(request))
    return _aw_json({"ok": True, "msg": f"Đã thêm vòng cược x{mult:g} cho {done} người (tổng {fmt_money(total)}đ)"})


# ---------- Xuất file ----------
_AWP_XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_AWP_USER_SHEETS = {"his": "Biến động số dư", "nap": "Nạp", "rut": "Rút", "cuoc": "Cược & Thắng",
                    "code": "Code đã nhập", "mua": "Gift đã mua", "gift": "Gift đã dùng"}


def _awp_export_sync(kind, token, uid):
    start, end, label = _rp_range(token)
    tag = _rp_tag(token)
    stamp = get_vietnam_time().strftime("%Y%m%d_%H%M")
    if kind == "stats":
        sheets, _sm = _stat_collect_sync(start, end, False)
        head, sub, base = "BÁO CÁO THỐNG KÊ HỆ THỐNG", f"Kỳ báo cáo: {label}", f"thongke_{tag}_{stamp}"
    elif kind == "nap":
        raw = [r for r in (query("SELECT id,user_id,amount,status,time,ref_code,admin_id FROM deposit_history ORDER BY id ASC") or [])
               if _rp_in_range(r[4], start, end)]
        sheets, head, sub, base = [_xs_dep_sheet(raw)], "LỊCH SỬ NẠP", f"Kỳ: {label}", f"nap_{tag}_{stamp}"
    elif kind == "rut":
        raw = [r for r in (query("SELECT id,user_id,amount,status,time,admin_id,admin_note FROM withdraw_history ORDER BY id ASC") or [])
               if _rp_in_range(r[4], start, end)]
        sheets, head, sub, base = [_xs_wd_sheet(raw)], "LỊCH SỬ RÚT", f"Kỳ: {label}", f"rut_{tag}_{stamp}"
    elif kind == "user":
        sheets = []
        for k, name in _AWP_USER_SHEETS.items():
            data = _rp_collect(k, uid, start, end)
            sheets.append({"name": name, **data, "kpis": _rp_kpis(k, data)})
        head, sub, base = f"HỒ SƠ NGƯỜI DÙNG {uid}", f"Kỳ: {label}", f"user_{uid}_{tag}_{stamp}"
    else:
        raise ValueError("kind")
    try:
        return _rp_build_xlsx(head, sub, sheets).getvalue(), base + ".xlsx", _AWP_XLSX
    except ImportError:
        return _rp_build_csv(head, sub, sheets).getvalue(), base + ".csv", "text/csv"


async def awp_api_export(request):
    tok, s = await asyncio.to_thread(_aw_auth, request)
    kind = request.match_info.get("kind", "")
    token = _rp_token_from_text(request.query.get("period", "30")) or "n30"
    us = request.query.get("uid", "")
    if kind not in ("stats", "nap", "rut", "user") or (kind == "user" and not us.isdigit()):
        return _aw_json({"err": "Yêu cầu không hợp lệ"}, 400)
    try:
        data, fname, ctype = await asyncio.to_thread(_awp_export_sync, kind, token, int(us) if us.isdigit() else 0)
    except Exception as e:
        traceback.print_exc()
        return _aw_json({"err": f"Không xuất được file: {e}"}, 500)
    await asyncio.to_thread(_aw_log, s["user"], "EXPORT", f"{kind} {token} {us}", _aw_ip(request))
    return web.Response(body=data, content_type=ctype,
                        headers={"Content-Disposition": f'attachment; filename="{fname}"', **_AW_SEC_HEADERS})




# ---------- Ép kết quả Tài Xỉu 3D từ Web Admin ----------
async def awp_api_tx3d_force_state(request):
    await asyncio.to_thread(_aw_auth, request)
    forced = TX3D.force
    current = "Không có"
    if forced:
        current = (" ".join(map(str, forced["dice"])) if forced.get("dice")
                   else ("TÀI" if forced.get("kind") == "tai" else "XỈU"))
    next_round = TX3D.round_id if TX3D.phase == "bet" else TX3D.round_id + 1
    tot = {"tai": [0, 0], "xiu": [0, 0]}
    for b in list(TX3D.bets.values()):
        tot[b["side"]][0] += int(b["amt"])
        tot[b["side"]][1] += 1
    players = []
    for _uid, _b in list(TX3D.bets.items()):
        players.append({"uid": int(_uid), "name": str(_b.get("name") or ""), "side": _b.get("side"), "amt": int(_b.get("amt") or 0)})
    players.sort(key=lambda x: -x["amt"])
    cover = TX3D.phase == "cover" and TX3D.dice and TX3D.result
    return _aw_json({
        "round": int(next_round),
        "round_now": int(TX3D.round_id),
        "phase": TX3D.phase,
        "left": int(round(max(0.0, TX3D.phase_end - time.time()))),
        "bets": len(TX3D.bets),
        "tot": tot,
        "players": players,
        "pot": int(TX3D.pot),
        "dice": list(TX3D.dice) if cover else None,
        "jp": bool(TX3D.result.get("jp")) if cover else False,
        "hist": [list(h) for h in TX3D.hist[:12]],
        "current": current,
        "pending": bool(forced),
    })


async def awp_api_tx3d_force(request):
    tok, session = await asyncio.to_thread(_aw_auth, request, True)
    body = await _awp_body(request)
    mode = str(body.get("mode", "")).strip().lower()

    if mode in ("off", "cancel", "huy"):
        TX3D.force = None
        detail = "Huỷ ép kết quả Tài Xỉu 3D"
        message = "Đã huỷ ép kết quả Tài Xỉu 3D."
    elif mode in ("tai", "t"):
        TX3D.force = {"dice": None, "kind": "tai", "by": session["user"]}
        detail = "Ép kết quả Tài Xỉu 3D: TÀI"
        message = "Đã đặt ép TÀI cho phiên kế tiếp."
    elif mode in ("xiu", "x"):
        TX3D.force = {"dice": None, "kind": "xiu", "by": session["user"]}
        detail = "Ép kết quả Tài Xỉu 3D: XỈU"
        message = "Đã đặt ép XỈU cho phiên kế tiếp."
    elif mode in ("dice", "exact"):
        raw = body.get("dice", "")
        if isinstance(raw, (list, tuple)):
            digits = [str(x).strip() for x in raw]
        else:
            digits = re.findall(r"[1-6]", str(raw))
            # Không chấp nhận ký tự số ngoài 1..6 hoặc dữ liệu nhập thừa.
            compact = re.sub(r"[\s,;.-]", "", str(raw))
            if not re.fullmatch(r"[1-6]{3}", compact):
                digits = []
        if len(digits) != 3 or any(x not in ("1", "2", "3", "4", "5", "6") for x in digits):
            return _aw_json({"err": "Nhập đúng 3 mặt xúc xắc từ 1 đến 6, ví dụ 1 3 4."}, 400)
        dice = [int(x) for x in digits]
        TX3D.force = {"dice": dice, "kind": None, "by": session["user"]}
        detail = "Ép kết quả Tài Xỉu 3D: " + "-".join(map(str, dice))
        message = "Đã đặt ép kết quả " + "-".join(map(str, dice)) + " cho phiên kế tiếp."
    else:
        return _aw_json({"err": "Thao tác không hợp lệ."}, 400)

    next_round = TX3D.round_id if TX3D.phase == "bet" else TX3D.round_id + 1
    await asyncio.to_thread(_aw_log, session["user"], "TX3D_FORCE", detail + f" · phiên #{next_round}", _aw_ip(request))
    return _aw_json({"ok": True, "msg": message, "round": int(next_round)})



async def awp_api_reset_stats(request):
    tok, session = await asyncio.to_thread(_aw_auth, request, True)
    dep_rows = await asyncio.to_thread(query, "SELECT COALESCE(MAX(id),0) FROM deposit_history")
    wd_rows = await asyncio.to_thread(query, "SELECT COALESCE(MAX(id),0) FROM withdraw_history")
    dep_max = int((dep_rows or [(0,)])[0][0] or 0)
    wd_max = int((wd_rows or [(0,)])[0][0] or 0)
    today = get_vietnam_time().date()
    await asyncio.to_thread(set_setting, "stats_epoch_dep", dep_max)
    await asyncio.to_thread(set_setting, "stats_epoch_wd", wd_max)
    await asyncio.to_thread(query, "DELETE FROM stats_bet_base")
    await asyncio.to_thread(
        query,
        "INSERT INTO stats_bet_base (user_id, day, bet, win) SELECT user_id, day, bet, win FROM bet_daily WHERE day=%s",
        (today,),
    )
    await asyncio.to_thread(set_setting, "stats_epoch_day", today.isoformat())
    await asyncio.to_thread(set_setting, "stats_epoch_at", get_vietnam_datetime_db())
    await asyncio.to_thread(
        _aw_log, session["user"], "RESET_STATS",
        "reset counters deposits/withdrawals", _aw_ip(request)
    )
    return _aw_json({"ok": True, "msg": "Đã reset mốc thống kê"})

def _awp_reset_system_sync():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname='public' AND tablename <> 'settings'
              AND tablename NOT LIKE 'schema_migrations%'
            ORDER BY tablename
        """)
        tables = [r[0] for r in cur.fetchall()]
        if tables:
            quoted = ", ".join('"' + name.replace('"', '""') + '"' for name in tables)
            cur.execute("TRUNCATE TABLE " + quoted + " RESTART IDENTITY CASCADE")
        conn.commit()
        try:
            _interaction_seen.clear()
        except Exception:
            pass
        return len(tables)
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()


async def awp_api_reset_system(request):
    tok, session = await asyncio.to_thread(_aw_auth, request, True)
    body = await _awp_body(request)
    if str(body.get("confirm", "")).strip() != "RESET TOAN BO":
        return _aw_json({"err": "Nhập chính xác RESET TOAN BO để xác nhận"}, 400)
    try:
        count = await asyncio.to_thread(_awp_reset_system_sync)
    except Exception as exc:
        print(f"[web-admin] Lỗi reset hệ thống: {exc}")
        return _aw_json({"err": "Reset thất bại; dữ liệu đã rollback. Kiểm tra log máy chủ."}, 500)
    # Ghi log sau thao tác không thể ghi được vì bảng nhật ký đã bị truncate.
    return _aw_json({"ok": True, "msg": f"Đã reset {count} bảng. Cấu hình settings được giữ lại."})


def admin_web_plus_register(app):
    r = app.router
    r.add_get("/admin/api/chart", awp_api_chart)
    r.add_get("/admin/api/tx3d/force", awp_api_tx3d_force_state)
    r.add_post("/admin/api/tx3d/force", awp_api_tx3d_force)
    r.add_get("/admin/api/control", awp_api_control)
    r.add_post("/admin/api/control/mt", awp_api_mt)
    r.add_post("/admin/api/control/mtall", awp_api_mtall)
    r.add_post("/admin/api/control/room", awp_api_room)
    r.add_post("/admin/api/control/setting", awp_api_setting)
    r.add_post("/admin/api/reset/stats", awp_api_reset_stats)
    r.add_post("/admin/api/reset/system", awp_api_reset_system)
    r.add_get("/admin/api/deposits2", awp_api_deposits2)
    r.add_post("/admin/api/deposit/{did}/{act}", awp_api_deposit_act)
    r.add_post("/admin/api/naptien", awp_api_naptien)
    r.add_get("/admin/api/u2/{uid}/state", awp_api_user_state)
    r.add_post("/admin/api/u2/{uid}/{act}", awp_api_user_act)
    r.add_get("/admin/api/gift/types", awp_api_gift_types)
    r.add_post("/admin/api/gift/create", awp_api_gift_create)
    r.add_post("/admin/api/gift/delete", awp_api_gift_delete)
    r.add_get("/admin/api/gifts/unused", awp_api_unused)
    r.add_post("/admin/api/gifts/unused/delete", awp_api_unused_delete)
    r.add_post("/admin/api/gifts/unused/delete-all", awp_api_unused_delete_all)
    r.add_post("/admin/api/broadcast", awp_api_broadcast)
    r.add_get("/admin/api/broadcast/status", awp_api_broadcast_status)
    r.add_get("/admin/api/vcall/preview", awp_api_vcall_preview)
    r.add_post("/admin/api/vcall", awp_api_vcall)
    r.add_get("/admin/api/export/{kind}", awp_api_export)


# ---------- Giao diện: JS bổ sung (được ghép vào _AW_JS lúc khởi động) ----------
_AWP_JS = r'''
function sw(label,key,on){return '<button class="btn '+(on?'bad':'ok')+'" data-x="mt" data-key="'+esc(key)+'" data-v="'+(on?0:1)+'">'+(on?'🔴 ':'🟢 ')+esc(label)+(on?' — ĐANG BẢO TRÌ':' — hoạt động')+'</button>';}
function vals(b){var o={};b.parentNode.querySelectorAll('[data-k]').forEach(function(e){o[e.getAttribute('data-k')]=e.value;});return o;}
function ub(id,label,act,cls,body,cf){return '<button class="btn '+(cls||'gray')+'" data-x="u" data-id="'+esc(id)+'" data-act="'+act+'"'+(body?' data-body="'+esc(JSON.stringify(body))+'"':'')+(cf?' data-cf="'+esc(cf)+'"':'')+'>'+esc(label)+'</button>';}
var TA='style="background:#0f1117;border:1px solid #272b38;color:#e8eaf0;border-radius:9px;padding:10px 12px;font-size:15px;width:100%;min-height:90px"';

async function vStats2(){
  await vStats();
  var c=await api('chart?days=14');var mx=1;
  c.rows.forEach(function(r){mx=Math.max(mx,r.dep,r.wd);});
  var h='<div class="item"><b>📈 14 ngày gần nhất</b><div class="tw"><table><tr><th>Ngày</th><th>Nạp</th><th>Rút</th><th></th><th>Cược</th><th>Lãi/lỗ game</th></tr>'+c.rows.slice().reverse().map(function(r){
    return '<tr><td>'+esc(r.day)+'</td><td>'+money(r.dep)+'</td><td>'+money(r.wd)+'</td><td style="min-width:110px"><div style="height:5px;background:#27c281;width:'+Math.round(r.dep*100/mx)+'%"></div><div style="height:5px;margin-top:2px;background:#ff5d6c;width:'+Math.round(r.wd*100/mx)+'%"></div></td><td>'+money(r.bet)+'</td><td style="color:'+(r.pnl>=0?'#27c281':'#ff5d6c')+'">'+(r.pnl<0?'−':'+')+money(Math.abs(r.pnl))+'</td></tr>';}).join('')+'</table></div><p class="mut" style="font-size:12.5px;margin:6px 0 0">Thanh xanh: nạp · thanh đỏ: rút</p></div>';
  view.insertAdjacentHTML('beforeend',h);
}

async function vDep2(){
  var f=vDep2.f||'pending';var d=await api('deposits2?status='+f);
  var h='<div class="item"><b>➕ Nạp tiền thủ công</b><div class="inl" style="margin-top:8px"><input data-k="uid" placeholder="ID người dùng" inputmode="numeric"><input data-k="amount" placeholder="Số tiền (vd 100k)"><button class="btn ok" data-x="naptien">Nạp</button></div></div>';
  h+='<div class="inl" style="margin:8px 0"><select id="df"><option value="pending">Chờ duyệt</option><option value="all">100 giao dịch gần nhất</option></select></div>';
  h+='<div class="item tw"><table><tr><th>#</th><th>ID</th><th>Số tiền</th><th>Trạng thái</th><th>Thời gian</th><th>Mã GD</th><th></th></tr>'+d.rows.map(function(r){
    return '<tr><td>'+esc(r.id)+'</td><td><a href="#" data-open="'+esc(r.user_id)+'">'+esc(r.user_id)+'</a></td><td>'+money(r.amount)+'</td><td><span class="tag '+esc(r.status)+'">'+esc(r.status)+'</span></td><td>'+esc(r.time)+'</td><td>'+esc(r.ref)+'</td><td>'+(r.status==='pending'?'<button class="btn ok" data-x="dep" data-id="'+esc(r.id)+'" data-act="approve">Duyệt</button> <button class="btn bad" data-x="dep" data-id="'+esc(r.id)+'" data-act="reject">Từ chối</button>':'')+'</td></tr>';}).join('')+'</table></div>'+(d.rows.length?'':'<p class="mut">Không có giao dịch.</p>');
  view.innerHTML=h;var s=document.getElementById('df');s.value=f;s.onchange=function(){vDep2.f=s.value;load();};
}

function gform(){var o={};document.querySelectorAll('#gform [data-k]').forEach(function(e){o[e.getAttribute('data-k')]=e.value;});return o;}
function pmoney(s){s=String(s==null?'':s).toLowerCase().replace(/[.,đ\s]/g,'');var m=1;if(s.slice(-1)==='k'){m=1000;s=s.slice(0,-1);}else if(s.slice(-1)==='m'){m=1000000;s=s.slice(0,-1);}return Math.round((parseFloat(s)||0)*m);}
function fmin(m){m=Math.round(m||0);if(m<=0)return '—';var d=Math.floor(m/1440),h=Math.floor(m%1440/60),p=m%60,o=[];if(d)o.push(d+' ngày');if(h)o.push(h+' giờ');if(p)o.push(p+' phút');return o.join(' ');}
function gsum(){
  var e=document.getElementById('gsum');if(!e)return;
  var v=gform(),q=parseInt(v.qty,10)||0,r=pmoney(v.reward),w=parseInt(v.wager,10)||0,m=(parseFloat(v.mins)||0)*parseInt(v.unit,10);
  var t='Tạo <b>'+q+'</b> code × <b>'+money(r)+'</b> = tổng <b>'+money(q*r)+'</b><br>';
  t+=w>0?'Vòng cược <b>x'+w+'</b>: người nhập cần cược (số dư sau khi nhận code × '+w+') mới được rút.':'Không yêu cầu vòng cược.';
  t+='<br>Hạn dùng: <b>'+fmin(m)+'</b>';
  if(v.bound&&v.bound.trim())t+=' · chỉ ID <b>'+esc(v.bound.trim())+'</b>';
  if(v.req_dep&&v.req_dep.trim())t+=' · yêu cầu nạp trong ngày <b>'+money(pmoney(v.req_dep))+'</b>';
  e.innerHTML=t;
}
async function vGift2(){
  await vGift();
  var t=await api('gift/types');
  if(!document.getElementById('gfs')){var sy=document.createElement('style');sy.id='gfs';
    sy.textContent='.gfl{display:grid;grid-template-columns:210px 1fr;gap:6px 14px;align-items:center;margin-top:12px}.gfl label{font-weight:600}.gfl label small{display:block;font-weight:400;color:var(--mut);font-size:12px}.gsum{margin-top:14px;padding:10px 12px;border-radius:10px;background:#0f1117;border:1px dashed var(--line);font-size:13.5px;line-height:1.7}@media(max-width:620px){.gfl{grid-template-columns:1fr}}';
    document.head.appendChild(sy);}
  function line(label,hint,ctl){return '<div class="gfl"><label>'+label+(hint?'<small>'+hint+'</small>':'')+'</label><div>'+ctl+'</div></div>';}
  var h='<div class="item" id="gform"><b style="font-size:17px">🎁 Tạo giftcode</b>'
   +line('Loại code','Chọn nhóm code cần tạo','<select data-k="ctype">'+t.types.map(function(x){return '<option value="'+esc(x.type)+'">'+esc(x.name)+'</option>';}).join('')+'</select>')
   +line('Số lượng code','Từ 1 đến 100 code mỗi lần','<input data-k="qty" value="1" inputmode="numeric" placeholder="1">')
   +line('Giá trị mỗi code (đ)','Ví dụ 20000 hoặc 20k (tối thiểu 1.000đ)','<input data-k="reward" placeholder="20k">')
   +line('Vòng cược (x)','Số vòng phải cược trước khi rút. Nhập 0 = không yêu cầu','<input data-k="wager" value="1" inputmode="numeric" placeholder="1">')
   +line('Hạn dùng','Tính từ lúc tạo code','<div class="inl"><input data-k="mins" value="1" inputmode="numeric" placeholder="1"><select data-k="unit" style="max-width:140px"><option value="1440">ngày</option><option value="60">giờ</option><option value="1">phút</option></select></div>')
   +line('Chỉ ID này được dùng','Để trống = ai cũng nhập được','<input data-k="bound" placeholder="Tuỳ chọn" inputmode="numeric">')
   +line('Yêu cầu nạp trong ngày (đ)','Để trống = không yêu cầu nạp','<input data-k="req_dep" placeholder="Tuỳ chọn, ví dụ 50k">')
   +'<div class="gsum" id="gsum"></div>'
   +'<div class="acts"><button class="btn ok" data-x="gcreate">Tạo code</button></div>'
   +'<pre id="gout" class="mut" style="white-space:pre-wrap;user-select:all;margin:10px 0 0"></pre>'
   +'<div class="acts" id="gcp" style="display:none"><button class="btn gray" data-x="gcopy">Sao chép tất cả code</button></div></div>'
   +'<div class="item"><b>🗑 Xoá giftcode</b><div class="inl" style="margin-top:8px"><input data-k="code" placeholder="Mã code"><button class="btn bad" data-x="gdel">Xoá</button></div></div>';
  view.insertAdjacentHTML('afterbegin',h);
  var gf=document.getElementById('gform');gf.addEventListener('input',gsum);gf.addEventListener('change',gsum);gsum();
}

var UF={key:'',status:'all',q:'',page:1};
function uown(o){
  if(!o)return '<div class="mut" style="margin-top:8px">👤 Chủ code: <b>Không gắn ID</b> (ai nhập cũng được)</div>';
  var x=o.info;
  var h='<div style="margin-top:8px;padding:9px 11px;border:1px solid var(--line);border-radius:10px;background:#0f1117;line-height:1.7;font-size:13.5px">'
   +'<div><b>👤 '+esc(o.role)+'</b> · ID <a href="#" data-open="'+esc(o.id)+'"><code>'+esc(o.id)+'</code></a>'
   +(x&&x.banned?' <span class="tag rejected">Bị cấm</span>':'')+(x&&x.code_blocked?' <span class="tag rejected">Cấm nhập code</span>':'')+'</div>';
  if(x){h+='<div>Tên: <b>'+esc(x.name||'—')+'</b> · Số dư: <b>'+money(x.balance)+'</b></div>'
   +'<div>Ngân hàng: '+esc(x.bank||'—')+' · STK: <code>'+esc(x.stk||'—')+'</code></div>'
   +'<div>Tổng nạp: '+money(x.dep)+' · Tổng rút: '+money(x.wd)+' · Tổng cược: '+money(x.total_bet)+'</div>';}
  else{h+='<div class="mut">ID này chưa có trong bảng người dùng.</div>';}
  return h+'</div>';
}
async function vUnused(){
  var d=await api('gifts/unused');
  if(!UF.key||!d.groups.some(function(g){return g.key===UF.key;})){var first=d.groups.filter(function(g){return g.count>0;})[0]||d.groups[0];UF.key=first?first.key:'';}
  var tot=0,val=0;d.groups.forEach(function(g){tot+=g.count;val+=g.value;});
  view.innerHTML='<div class="grid">'+card('Tổng code chưa sử dụng',tot)+card('Tổng giá trị',money(val))+card('Số loại code',d.groups.length)+'</div>'
   +'<div class="acts" style="margin:12px 0">'+d.groups.map(function(g){return '<button class="btn '+(g.key===UF.key?'':'gray')+'" data-ukey="'+esc(g.key)+'">'+esc(g.icon+' '+g.label)+' · '+g.count+'</button>';}).join('')+'</div><div id="ud"></div>';
  view.querySelectorAll('[data-ukey]').forEach(function(b){b.onclick=function(){UF.key=b.getAttribute('data-ukey');UF.page=1;UF.q='';UF.status='all';vUnused().catch(function(e){toast(e.message);});};});
  await udetail(d.groups.filter(function(g){return g.key===UF.key;})[0]);
}
async function udetail(g){
  var box=document.getElementById('ud');
  if(!g){box.innerHTML='<p class="mut">Chưa có loại code nào.</p>';return;}
  var d=await api('gifts/unused?key='+encodeURIComponent(g.key)+'&status='+UF.status+'&q='+encodeURIComponent(UF.q)+'&page='+UF.page);
  UF.page=d.page;
  var h='<div class="item"><div class="row"><b style="font-size:17px">'+esc(g.icon+' '+g.label)+'</b><span class="mut">'+esc(g.name)+'</span></div>'
   +'<p class="mut" style="margin:6px 0">Chưa sử dụng: <b>'+g.count+'</b> code · Tổng giá trị <b>'+money(g.value)+'</b>'+(g.expired?' · Đã hết hạn chưa nhập: <b>'+g.expired+'</b>':'')+'</p>'
   +'<div class="acts"><button class="btn bad" id="uxall"'+(g.count?'':' disabled')+'>🗑 Xoá toàn bộ '+esc(g.label)+' ('+g.count+')</button>'
   +(g.expired?'<button class="btn gray" id="uxexp">Xoá code hết hạn ('+g.expired+')</button>':'')+'</div>'
   +'<div class="inl" style="margin-top:10px"><select id="uxs" style="max-width:170px"><option value="all">Tất cả</option><option value="valid">Còn hạn</option><option value="expired">Hết hạn</option></select>'
   +'<input id="uxq" placeholder="Mã code / ID chủ code"><button class="btn" id="uxg">Lọc</button></div></div>';
  var pager='<div class="acts"><button class="btn gray uxp"'+(d.page<=1?' disabled':'')+'>← Trước</button><span class="mut" style="align-self:center">Trang '+d.page+'/'+d.pages+' · '+d.total+' code</span><button class="btn gray uxn"'+(d.page>=d.pages?' disabled':'')+'>Sau →</button></div>';
  h+=pager+(d.rows.length?d.rows.map(function(r){
    var meta='Giá trị <b>'+money(r.reward)+'</b>'+(r.wager!=null?' · Vòng cược x'+esc(r.wager):'')+(r.uses!=null?' · Còn <b>'+esc(r.uses)+'</b> lượt':'')+(r.expiry?' · Hạn: '+esc(r.expiry):'')
      +(r.need_dep?' · Yêu cầu tổng nạp '+money(r.need_dep):'')+(r.need_today?' · Yêu cầu nạp '+money(r.need_today):'')+(r.creator?' · ID tạo/mua: <a href="#" data-open="'+esc(r.creator)+'">'+esc(r.creator)+'</a>':'');
    return '<div class="item"><div class="row"><code style="font-size:14px;user-select:all">'+esc(r.code)+'</code><span class="tag '+(r.expired?'rejected':'pending')+'">'+(r.expired?'Hết hạn · chưa nhập':'Chưa sử dụng')+'</span></div>'
      +'<div class="mut" style="margin-top:5px">'+meta+'</div>'+uown(r.owner)
      +'<div class="acts"><button class="btn bad" data-udel="'+esc(r.code)+'">Xoá code này</button></div></div>';
  }).join(''):'<p class="mut">Không có code nào.</p>')+pager;
  box.innerHTML=h;
  document.getElementById('uxs').value=UF.status;document.getElementById('uxq').value=UF.q;
  var redo=function(pg){UF.status=document.getElementById('uxs').value;UF.q=document.getElementById('uxq').value.trim();UF.page=pg||1;udetail(g).catch(function(e){toast(e.message);});};
  document.getElementById('uxg').onclick=function(){redo(1);};
  box.querySelectorAll('.uxp').forEach(function(e){e.onclick=function(){redo(d.page-1);};});
  box.querySelectorAll('.uxn').forEach(function(e){e.onclick=function(){redo(d.page+1);};});
  box.querySelectorAll('[data-udel]').forEach(function(b){b.onclick=async function(){
    var c=b.getAttribute('data-udel');if(!confirm('Xoá code '+c+'?'))return;b.disabled=true;
    try{var r=await post('gifts/unused/delete',{src:g.src,code:c});toast(r.msg||'Đã xoá');vUnused();}catch(e){toast(e.message);b.disabled=false;}};});
  var delAll=async function(btn,scope,n){
    if(!confirm((scope==='expired'?'XOÁ '+n+' code HẾT HẠN của ':'XOÁ TOÀN BỘ '+n+' code chưa sử dụng của ')+g.label+'? Không thể hoàn tác.'))return;
    btn.disabled=true;
    try{var r=await post('gifts/unused/delete-all',{src:g.src,ctype:g.ctype,scope:scope});toast(r.msg||'Đã xoá');UF.page=1;vUnused();}catch(e){toast(e.message);btn.disabled=false;}};
  var ba=document.getElementById('uxall');if(ba)ba.onclick=function(){delAll(ba,'all',g.count);};
  var be=document.getElementById('uxexp');if(be)be.onclick=function(){delAll(be,'expired',g.expired);};
}

async function vCtl(){
  var d=await api('control');
  var h='<div class="item"><b>🛠 Bảo trì</b><p class="mut" style="margin:4px 0 8px">Xanh = hoạt động · đỏ = đang bảo trì (admin vẫn chơi được). Bấm để đổi.</p><div class="acts">'+sw('Toàn hệ thống','system_maintenance',d.system)+sw('Toàn bộ (kể cả menu)','mt_tongbao',d.total)+'</div></div>';
  h+='<div class="item"><b>🎮 Game</b><div class="acts">'+d.games.map(function(g){return sw(g.name,g.key,g.mt);}).join('')+'</div><div class="acts"><button class="btn bad" data-x="mtall" data-v="1" data-scope="games" data-cf="Bảo trì TẤT CẢ game?">Bảo trì tất cả game</button><button class="btn ok" data-x="mtall" data-v="0" data-scope="games">Mở tất cả game</button></div></div>';
  h+='<div class="item"><b>💳 Nạp / Rút tổng</b><div class="acts">'+d.features.filter(function(g){return g.key==='mt_nap'||g.key==='mt_rut';}).map(function(g){return sw(g.name,g.key,g.mt);}).join('')+'</div></div>';
  h+='<div class="item"><b>🏧 Bảo trì riêng từng cổng rút</b><p class="mut">Tắt một cổng không ảnh hưởng các cổng còn lại.</p><div class="acts">'+d.payout_channels.map(function(g){return sw(g.name,g.key,g.mt);}).join('')+'</div></div>';
  h+='<div class="item"><b>🏠 Room nhóm</b>'+d.rooms.map(function(r){return '<div class="row" style="margin-top:8px"><span>Nhóm <b>'+esc(r.id)+'</b></span><span>Bot: <b>'+(r.muted?'ĐÃ TẮT':'đang bật')+'</b></span><span>Cược: <b>'+(r.bet?'mở':'khoá')+'</b></span></div><div class="acts">'+
    (r.muted?'<button class="btn ok" data-x="room" data-id="'+esc(r.id)+'" data-act="unmute">Bật lại room</button>':'<button class="btn bad" data-x="room" data-id="'+esc(r.id)+'" data-act="mute" data-cf="Tắt room? Bot ngừng gửi tin và hoàn cược phiên đang mở.">Tắt room</button>')+
    (r.bet?'<button class="btn gray" data-x="room" data-id="'+esc(r.id)+'" data-act="betoff">Khoá cược</button>':'<button class="btn ok" data-x="room" data-id="'+esc(r.id)+'" data-act="beton">Mở cược</button>')+'</div>';}).join('')+'</div>';
  function srow(label,name,val,sel){return '<div class="inl" style="margin-top:8px"><span style="min-width:200px;align-self:center">'+label+'</span>'+(sel?'<select data-k="value">'+sel.map(function(o){return '<option value="'+o+'"'+(o===val?' selected':'')+'>'+o+'</option>';}).join('')+'</select>':'<input data-k="value" value="'+esc(val)+'">')+'<button class="btn" data-x="set" data-name="'+name+'">Lưu</button></div>';}
  h+='<div class="item"><b>🎁 Khuyến mãi nạp</b>'+srow('Chế độ giờ vàng ('+esc(d.promo_windows)+')','promo_mode',d.promo_mode,['auto','on','off'])+srow('Phần trăm khuyến mãi (%)','promo_pct',d.promo_pct)+'<label class="mut" style="display:block;margin-top:10px">Nội dung gửi nhóm (HTML Telegram; biến: {PERCENT}, {ORDER_PERCENT}, {HOURS})</label><textarea id="promotext" rows="5" style="width:100%;margin-top:6px" placeholder="Để trống dùng nội dung mặc định">'+esc(d.promo_text||'')+'</textarea><div class="acts"><button class="btn ok" data-x="promoSave">Lưu nội dung khuyến mãi</button></div><p class="mut">Khi khuyến mãi chuyển sang trạng thái bật, bot sẽ gửi tin và tự ghim trong nhóm.</p></div>';
  h+='<div class="item"><b>⚙️ Cài đặt khác</b>'+srow('Hoàn cược ngày (%)','rebate_ngay',d.rebate_ngay)+srow('Hoàn cược tuần (%)','rebate_tuan',d.rebate_tuan)+srow('Hũ jackpot Tài Xỉu Room (đ)','jackpot',d.jackpot)+srow('Hũ Tài Xỉu 3D (đ)','tx3d_pot',d.tx3d_pot)+srow('Tên hiển thị của bot','bot_name',d.bot_name)+'</div>';
  view.innerHTML=h;
}


async function vTx3d(){
  var my=(vTx3d.run=(vTx3d.run||0)+1);
  var d=await api('tx3d/force');
  var h='<div class="item"><b>🎲 TÀI XỈU 3D — TRỰC TIẾP</b><div id="txlive" style="margin-top:8px"></div></div>'
    +'<div class="item"><b>👥 NGƯỜI ĐẶT CƯỢC TRONG PHIÊN</b><div id="txpl" style="margin-top:8px"></div></div>'
    +'<div class="item"><b>🛠 ÉP KẾT QUẢ</b>'
    +'<p class="mut" style="margin:6px 0">Áp dụng cho phiên <b id="txnext">#'+esc(d.round)+'</b> · Đang chờ ép: <b id="txcur">'+esc(d.current)+'</b></p>'
    +'<div class="acts" style="margin-top:10px">'
    +'<button class="btn" data-x="tx3d" data-mode="tai" data-cf="Xác nhận đặt ép TÀI cho phiên kế tiếp?">🔵 Ép TÀI</button>'
    +'<button class="btn bad" data-x="tx3d" data-mode="xiu" data-cf="Xác nhận đặt ép XỈU cho phiên kế tiếp?">🔴 Ép XỈU</button></div>'
    +'<div class="inl" style="margin-top:10px"><input data-k="dice" placeholder="3 mặt xúc xắc, ví dụ 1 3 4" inputmode="numeric">'
    +'<button class="btn" data-x="tx3d" data-mode="dice" data-cf="Xác nhận ép đúng 3 mặt xúc xắc đã nhập?">Ép 3 mặt</button></div>'
    +'<div class="acts" style="margin-top:10px"><button class="btn gray" data-x="tx3d" data-mode="off" data-cf="Huỷ kết quả đang chờ?">🚫 Huỷ ép</button>'
    +'<button class="btn gray" data-x="tx3d-refresh">🔄 Làm mới</button></div>'
    +'<p class="mut" style="margin-top:10px">Giống lệnh <b>/ep</b> trong bot: ép Tài/Xỉu không bao giờ ra Bão; ép 1-1-1 hoặc 6-6-6 sẽ nổ hũ. Phiên bị ép vẫn trả thưởng và ghi vào cầu như bình thường. Mọi thao tác ghi vào Nhật ký.</p></div>';
  view.innerHTML=h;
  var F=['⚀','⚁','⚂','⚃','⚄','⚅'];
  function faces(a){return a.map(function(x){return F[x-1]||'?';}).join(' ');}
  function nm(a){var s=a[0]+a[1]+a[2];return (a[0]==a[1]&&a[1]==a[2]&&a[0]>1&&a[0]<6)?'BÃO':(s>=11?'TÀI':'XỈU');}
  function col(a){var n=nm(a);return n==='TÀI'?'#f5b942':n==='XỈU'?'#ff8da0':'#6fd3ff';}
  function paint(s){
    var e=document.getElementById('txlive');if(!e)return;
    var ph=s.phase==='bet'?'Đang nhận cược':'Đang úp bát / mở kết quả';
    var x='<div class="row"><span>Phiên <b>#'+esc(s.round_now)+'</b></span><span>'+ph+'</span><span>Còn <b>'+esc(s.left)+'s</b></span><span>Hũ <b>'+money(s.pot)+'</b></span></div>';
    x+='<div class="grid" style="margin-top:10px"><div class="card"><div class="k">TÀI · '+esc(s.tot.tai[1])+' người</div><div class="v" style="color:#f5b942">'+money(s.tot.tai[0])+'</div></div>'
      +'<div class="card"><div class="k">XỈU · '+esc(s.tot.xiu[1])+' người</div><div class="v" style="color:#ff8da0">'+money(s.tot.xiu[0])+'</div></div></div>';
    if(s.dice){x+='<p style="margin:12px 0 0;font-size:15px">Kết quả phiên này: <span style="font-size:30px;vertical-align:middle">'+faces(s.dice)+'</span> <b>'+(s.dice[0]+s.dice[1]+s.dice[2])+'</b> · <b style="color:'+col(s.dice)+'">'+nm(s.dice)+'</b>'+(s.jp?' · <b style="color:#ffd05a">NỔ HŨ</b>':'')+'</p>';}
    else{x+='<p class="mut" style="margin:12px 0 0">Kết quả sẽ được chọn khi hết giờ đặt cược.</p>';}
    if(s.hist&&s.hist.length){x+='<div style="margin-top:12px;display:flex;gap:6px;flex-wrap:wrap">'+s.hist.map(function(a){return '<span title="'+a.join('-')+'" style="display:inline-block;min-width:34px;text-align:center;padding:3px 6px;border-radius:8px;border:1px solid '+col(a)+';color:'+col(a)+';font-size:12px">'+(a[0]+a[1]+a[2])+'</span>';}).join('')+'</div><p class="mut" style="margin:4px 0 0;font-size:12px">Cầu 12 phiên gần nhất (mới nhất bên trái)</p>';}
    e.innerHTML=x;
    var pl=document.getElementById('txpl');
    if(pl){var P=s.players||[];
      if(!P.length){pl.innerHTML='<p class="mut" style="margin:0">Chưa có ai đặt cược trong phiên này.</p>';}
      else{pl.innerHTML='<p class="mut" style="margin:0 0 6px">'+P.length+' người · sắp xếp theo tiền cược</p>'+P.map(function(u,i){var tai=u.side==='tai';
        return '<div class="row" style="padding:6px 0;border-top:1px solid #ffffff14;align-items:center"><span style="flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+(i+1)+'. <b>'+esc(u.name||'?')+'</b> <span class="mut">('+esc(u.uid)+')</span></span>'
          +'<b style="color:'+(tai?'#f5b942':'#ff8da0')+';margin:0 10px">'+(tai?'TÀI':'XỈU')+'</b><b>'+money(u.amt)+'</b></div>';}).join('');}}
    var n=document.getElementById('txnext'),c=document.getElementById('txcur');if(n)n.textContent='#'+s.round;if(c)c.textContent=s.current;
  }
  paint(d);
  (function loop(){
    setTimeout(async function(){
      if(my!==vTx3d.run||cur!=='tx3d'||!document.getElementById('txlive'))return;
      try{paint(await api('tx3d/force'));}catch(e){}
      loop();
    },2000);
  })();
}

async function vBc(){
  var h='<div class="item"><b>📣 Gửi thông báo tới TẤT CẢ người dùng</b><div style="margin-top:8px"><textarea id="bct" '+TA+' placeholder="Nội dung thông báo"></textarea></div><div class="acts"><button class="btn" data-x="bc">Gửi</button><span id="bcs" class="mut" style="align-self:center"></span></div></div>'
   +'<div class="item"><b>🎯 Thêm vòng cược cho TẤT CẢ người có số dư</b><p class="mut" style="margin:4px 0 8px">Yêu cầu cược thêm = số dư × số vòng (cộng dồn). Không áp dụng cho admin.</p><div class="inl"><input data-k="mult" placeholder="Số vòng, vd 7" value="7"><button class="btn gray" data-x="vcprev">Xem trước</button><button class="btn bad" data-x="vcall">Áp dụng</button></div><p id="vcs" class="mut"></p></div>';
  view.innerHTML=h;
}

async function vReset(){
   view.innerHTML='<div class="item"><b>📊 Reset tổng nạp / tổng rút</b><p class="mut">Chỉ đặt lại mốc thống kê. Không xoá số dư, giao dịch hay lịch sử cá nhân.</p><button class="btn bad" data-x="resetStats" data-cf="Reset tổng thống kê nạp/rút về 0? Dữ liệu giao dịch gốc vẫn được giữ.">Reset thống kê nạp/rút</button></div>'
    +'<div class="item"><b>⚠️ Reset toàn bộ hệ thống</b><p class="mut">Xoá dữ liệu người dùng, số dư, lịch sử giao dịch, cược, giftcode và nhật ký. Cấu hình trong settings được giữ lại. Không thể hoàn tác; hãy sao lưu cơ sở dữ liệu trước.</p><div class="inl"><input data-k="confirm" placeholder="Nhập RESET TOAN BO để xác nhận"><button class="btn bad" data-x="resetSystem" data-cf="Bạn đã sao lưu dữ liệu và chắc chắn muốn xoá toàn bộ?">RESET HỆ THỐNG</button></div></div>';
}
async function vExp(){
  function row(title,kind){return '<div class="item"><b>'+title+'</b><div class="inl" style="margin-top:8px"><input data-k="period" value="30" placeholder="all | 7 | 29/10/2026 | 01/10/2026 - 29/10/2026"><button class="btn" data-x="dl" data-kind="'+kind+'">Tải file Excel</button></div></div>';}
  view.innerHTML='<p class="mut">Kỳ: <b>all</b> (tất cả), số ngày gần nhất (vd <b>7</b>), một ngày hoặc khoảng ngày DD/MM/YYYY.</p>'+row('📊 Thống kê hệ thống (nhiều sheet + biểu đồ)','stats')+row('📥 Lịch sử nạp','nap')+row('📤 Lịch sử rút','rut');
}

async function uPlus(id,p){
  var box=document.getElementById('uplus');if(!box)return;
  var s;try{s=await api('u2/'+encodeURIComponent(id)+'/state');}catch(e){return;}
  var gname={};s.games.forEach(function(g){gname[g.gid]=g.name;});
  var bg=s.banned_game_ids.map(function(i){return esc(gname[i]||('Game '+i));}).join(', ')||'—';
  var f=s.features;function has(x){return f.indexOf(x)>=0;}
  var w=s.wager;
  var h='<div class="item"><b>🧰 Quản lý nâng cao</b><p class="mut">Tài khoản: <b>'+(s.banned?'ĐANG KHOÁ':'ĐANG HOẠT ĐỘNG')+'</b></p>';
  h+='<div class="inl" style="margin-top:10px"><input data-k="amount" placeholder="Số tiền, vd 50k"><button class="btn ok" data-x="u" data-id="'+esc(id)+'" data-act="credit">Cộng tiền</button><button class="btn bad" data-x="u" data-id="'+esc(id)+'" data-act="debit" data-cf="Xác nhận trừ tiền người dùng?">Trừ tiền</button></div>';
  h+='<div class="inl" style="margin-top:10px"><button class="btn bad" data-x="u" data-id="'+esc(id)+'" data-act="banuser" data-cf="Khoá tài khoản người dùng này?">Khoá tài khoản</button><button class="btn ok" data-x="u" data-id="'+esc(id)+'" data-act="unbanuser">Mở khoá tài khoản</button></div>';
  h+='<div class="inl" style="margin-top:10px"><input data-k="amount" placeholder="Số dư mới (vd 500k)"><button class="btn" data-x="u" data-id="'+esc(id)+'" data-act="setbal" data-cf="Đặt lại số dư?">Đặt số dư</button>'+ub(id,'Reset số dư về 0','resetbal','bad',null,'Đặt số dư về 0?')+'</div>';
  h+='<div class="inl" style="margin-top:10px"><input data-k="amount" placeholder="Tặng khuyến mãi (có vòng cược), vd 20k"><button class="btn" data-x="u" data-id="'+esc(id)+'" data-act="kmnap">Tặng KM</button></div>';
  h+='<div class="mut" style="margin-top:12px">Game đang bị cấm: <b>'+bg+'</b></div><div class="inl" style="margin-top:6px"><select data-k="game">'+s.games.map(function(g){return '<option value="'+esc(g.alias)+'">'+esc(g.name)+'</option>';}).join('')+'</select>'+ub(id,'Cấm game','camgame','bad')+ub(id,'Gỡ cấm','mogame','ok')+ub(id,'Gỡ tất cả','mogame','gray',{game:'all'})+'</div>';
  h+='<div class="mut" style="margin-top:12px">Nạp: <b>'+(has('nap')?'ĐÃ KHOÁ':'mở')+'</b> · Rút: <b>'+(has('rut')?'ĐÃ KHOÁ':'mở')+'</b></div><div class="acts">'+ub(id,'Khoá nạp','camtn','bad',{what:'nap'})+ub(id,'Khoá rút','camtn','bad',{what:'rut'})+ub(id,'Mở nạp','motn','ok',{what:'nap'})+ub(id,'Mở rút','motn','ok',{what:'rut'})+'</div>';
  h+='<div class="mut" style="margin-top:12px">Hoàn trả: ngày <b>'+(has('hoan_ngay')?'ĐÃ KHOÁ':'mở')+'</b> · tuần <b>'+(has('hoan_tuan')?'ĐÃ KHOÁ':'mở')+'</b> · chờ nhận <b>'+money(s.rewards.pending)+'</b> · đang tích luỹ <b>'+money(s.rewards.live)+'</b></div><div class="acts">'+ub(id,'Khoá hoàn ngày','camhoan','bad',{period:'ngay'})+ub(id,'Khoá hoàn tuần','camhoan','bad',{period:'tuan'})+ub(id,'Mở tất cả hoàn','mohoan','ok',{period:'all'})+ub(id,'RESET toàn bộ hoàn trả','resethoan','bad',{period:'all'},'Reset toàn bộ tiền hoàn trả của người này về 0?')+'</div>';
  h+='<div class="mut" style="margin-top:12px">Vòng cược: '+(w?'đã cược <b>'+money(w.current_bet)+'</b> / yêu cầu <b>'+money(w.required_bet)+'</b> · còn thiếu <b>'+money(Math.max(0,w.remaining))+'</b>':'<b>không có</b>')+'</div><div class="inl" style="margin-top:6px"><input data-k="amount" placeholder="Số tiền, vd 500k (âm để trừ tiến độ)">'+ub(id,'Thêm yêu cầu cược','themvong','')+ub(id,'Cộng tiến độ cược','themcuoc','')+ub(id,'Xoá vòng cược','xoacuoc','bad',null,'Xoá toàn bộ vòng cược?')+'</div>';
  h+='<div class="inl" style="margin-top:12px"><input data-k="text" placeholder="Nhắn riêng cho người này qua bot">'+ub(id,'Gửi','message','')+'</div>';
  h+='<div class="inl" style="margin-top:12px"><input data-k="period" value="all" placeholder="Kỳ: all | 7 | 29/10/2026"><button class="btn gray" data-x="dl" data-kind="user" data-uid="'+esc(id)+'">Tải Excel của user này</button></div></div>';
  box.innerHTML=h;
}

view.addEventListener('click',async function(ev){
  var b=ev.target.closest('button[data-x]');if(!b)return;
  var x=b.getAttribute('data-x');function g(k){return b.getAttribute('data-'+k);}
  if(g('cf')&&!confirm(g('cf')))return;
  var v=vals(b);b.disabled=true;
  try{
    if(x==='tx3d-refresh'){return load();}
    if(x==='tx3d'){
      var mode=g('mode'), payload={mode:mode};
      if(mode==='dice'){
        payload.dice=v.dice||'';
        if(!String(payload.dice).trim()){throw new Error('Bạn chưa nhập 3 mặt xúc xắc.');}
      }
      var result=await post('tx3d/force',payload);
      toast(result.msg||'Đã cập nhật');
      return load();
    }
    if(x==='promoSave'){var pt=document.getElementById('promotext').value;var pr=await post('control/setting',{name:'promo_group_text',value:pt});toast(pr.msg||'Đã lưu');return load();}
    if(x==='resetStats'){await post('reset/stats',{});toast('Đã reset thống kê nạp/rút');return load();}
    if(x==='resetSystem'){if(v.confirm!=='RESET TOAN BO'){throw new Error('Bạn phải nhập chính xác RESET TOAN BO.');}var rs=await post('reset/system',{confirm:v.confirm});toast(rs.msg||'Đã reset');return load();}
    if(x==='mt'){await post('control/mt',{key:g('key'),value:+g('v')});toast('Đã cập nhật');return load();}
    if(x==='mtall'){await post('control/mtall',{value:+g('v'),scope:g('scope')});toast('Đã cập nhật');return load();}
    if(x==='room'){await post('control/room',{id:g('id'),act:g('act')});toast('Đã cập nhật');return load();}
    if(x==='set'){var r=await post('control/setting',{name:g('name'),value:v.value});toast(r.msg||'Đã lưu');return load();}
    if(x==='dep'){if(!confirm((g('act')==='approve'?'DUYỆT':'TỪ CHỐI')+' đơn nạp #'+g('id')+'?')){b.disabled=false;return;}await post('deposit/'+g('id')+'/'+g('act'));toast('Đã xử lý');return load();}
    if(x==='naptien'){if(!confirm('Nạp '+v.amount+' cho ID '+v.uid+'?')){b.disabled=false;return;}var r2=await post('naptien',{uid:v.uid,amount:v.amount});toast(r2.msg);return load();}
    if(x==='u'){var body=Object.assign({},v,g('body')?JSON.parse(g('body')):{});var r3=await post('u2/'+encodeURIComponent(g('id'))+'/'+g('act'),body);toast(r3.msg||'Xong');return openUser(g('id'));}
    if(x==='gcreate'){var gv=gform();if(!String(gv.reward||'').trim())throw new Error('Nhập giá trị mỗi code.');
      var r4=await post('gift/create',{ctype:gv.ctype,qty:gv.qty,reward:gv.reward,wager:gv.wager,minutes:(parseFloat(gv.mins)||0)*parseInt(gv.unit,10),bound:gv.bound,req_dep:gv.req_dep});
      var go=document.getElementById('gout');go.setAttribute('data-codes',r4.codes.join('\n'));
      go.textContent='Đã tạo '+r4.codes.length+' code · '+money(r4.reward)+' · vòng cược x'+r4.wager+'\nHạn đến '+r4.expiry+'\n\n'+r4.codes.join('\n');
      document.getElementById('gcp').style.display='flex';toast('Đã tạo '+r4.codes.length+' code');b.disabled=false;return;}
    if(x==='gcopy'){var cd=(document.getElementById('gout').getAttribute('data-codes')||'');try{await navigator.clipboard.writeText(cd);toast('Đã sao chép '+cd.split('\n').length+' code');}catch(e2){toast('Trình duyệt không cho sao chép, hãy bôi đen và copy tay');}b.disabled=false;return;}
    if(x==='gdel'){var r5=await post('gift/delete',{code:v.code});toast(r5.msg);b.disabled=false;return;}
    if(x==='bc'){var t=document.getElementById('bct').value;if(!t.trim()||!confirm('Gửi thông báo cho TẤT CẢ người dùng?')){b.disabled=false;return;}
      var r6=await post('broadcast',{text:t});var st=document.getElementById('bcs');st.textContent='Đang gửi tới '+r6.total+' người…';
      var tm=setInterval(async function(){try{var s=await api('broadcast/status');st.textContent='Đã gửi '+s.sent+' · lỗi '+s.failed+' / '+s.total;if(!s.running){clearInterval(tm);b.disabled=false;toast('Gửi xong');}}catch(e){clearInterval(tm);b.disabled=false;}},2000);return;}
    if(x==='vcprev'){var p2=await api('vcall/preview?mult='+encodeURIComponent(v.mult));document.getElementById('vcs').textContent=p2.users+' người · tổng yêu cầu cược thêm '+money(p2.total);b.disabled=false;return;}
    if(x==='vcall'){if(!confirm('Thêm vòng cược x'+v.mult+' cho TẤT CẢ người có số dư? Không hoàn tác được.')){b.disabled=false;return;}var r7=await post('vcall',{mult:v.mult});toast(r7.msg);document.getElementById('vcs').textContent=r7.msg;b.disabled=false;return;}
    if(x==='dl'){var url='/admin/api/export/'+g('kind')+'?period='+encodeURIComponent(v.period||'30')+(g('uid')?'&uid='+encodeURIComponent(g('uid')):'');b.disabled=false;location.href=url;return;}
  }catch(e){toast(e.message);b.disabled=false;}
});
'''


def _awp_patch_js(js):
    reps = [
        ("var tabs=[['stats','Tổng quan'],['wd','Rút tiền'],['dep','Nạp tiền'],['user','Người dùng'],['dupe','Trùng tên rút tiền'],['gift','Giftcode'],['tx3d','Ép TX3D'],['ctl','Điều khiển'],['bc','Thông báo'],['exp','Xuất file'],['reset','Reset'],['log','Nhật ký'],['admins','Tạo admin']];",
         "var tabs=[['stats','Tổng quan'],['wd','Rút tiền'],['dep','Nạp tiền'],['user','Người dùng'],['dupe','Trùng tên rút tiền'],['gift','Giftcode'],['tx3d','Ép TX3D'],['ctl','Điều khiển'],['bc','Thông báo'],['exp','Xuất file'],['reset','Reset'],['log','Nhật ký'],['admins','Tạo admin']];"),
        ("({stats:vStats,wd:vWd,dep:vDep,user:vUser,gift:vGift,log:vLog})[cur]()",
         "({stats:vStats2,wd:vWd,dep:vDep2,user:vUser,dupe:vPayoutDuplicates,gift:vGift2,tx3d:vTx3d,ctl:vCtl,bc:vBc,exp:vExp,reset:vReset,log:vLog})[cur]()"),
        ("['gift','Giftcode'],", "['gift','Giftcode'],['unused','Code chưa dùng'],"),
        ("allowed[t[0]]", "allowed[t[0]==='unused'?'gift':t[0]]"),
        ("gift:vGift2,", "gift:vGift2,unused:vUnused,"),
        ("""'<nav id="snav"></nav><div id="sbody"></div>'""",
         """'<div id="uplus"></div><nav id="snav"></nav><div id="sbody"></div>'"""),
        ("document.getElementById('bk').onclick=", "uPlus(id,p);document.getElementById('bk').onclick="),
        ("document.getElementById('out').onclick=", _AWP_JS + "\ndocument.getElementById('out').onclick="),
    ]
    for old, new in reps:
        if old not in js:
            print(f"[web-plus] CẢNH BÁO: không tìm thấy đoạn cần vá trong _AW_JS: {old[:60]}…")
            continue
        js = js.replace(old, new, 1)
    return js


_AW_JS = _awp_patch_js(_AW_JS)


async def start_webhook_server():
    app = web.Application()
    # Nhận webhook ở cả gốc "/" lẫn /sepay_webhook (SePay đang gọi thẳng tên miền, không kèm đường dẫn).
    for path in ('/', '/sepay_webhook', '/webhook', '/sepay'):
        app.router.add_post(path, sepay_webhook)
    async def _health(request):
        return web.Response(text="OK")
    app.router.add_get('/', _health)
    app.router.add_get('/health', _health)
    tx3d_register_routes(app)      # miniapp Tài Xỉu 3D: /app , /api/state , /api/bet
    admin_web_register_routes(app)  # web admin: /admin (đăng nhập bằng tài khoản tạo qua /taoadmin)
    admin_web_plus_register(app)  # mở rộng giao diện và API admin
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.getenv("PORT", "8080"))   # Railway cấp cổng qua biến PORT
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"✅ Webhook server started on port {port} (SEPAY_API_KEY {'đã đặt' if SEPAY_API_KEY else 'CHƯA ĐẶT'})")

# ============================================================
# ADMIN TOOLS: help, per-game maintenance, bot status and user tools
# ============================================================
ADMIN_GAMES = {
    "room": ("mt_taixiu_room", 1, "Tài Xỉu Room"),
    "tx3d": (TX3D_MT_KEY, TX3D_GAME_ID, "Tài Xỉu 3D"),
}
for _a, _c in TGDICE.items():
    ADMIN_GAMES[_a] = (_c["key"], _c["gid"], _c["name"].title())
ADMIN_FEATURES = {"nap": ("mt_nap", "Nạp tiền"), "rut": ("mt_rut", "Rút tiền")}
GAME_ALIAS = {"tx": "room", "taixiu": "room", "3d": "tx3d", "taixiu3d": "tx3d", "tx3d": "tx3d",
              "naptien": "nap", "ruttien": "rut"}
for _a, _c in TGDICE.items():
    for _al in _c["aliases"]:
        GAME_ALIAS[_al] = _a

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
        "<code>/baotrigame pt br on</code> — bảo trì nhiều game\n"
        "<code>/baotrigame all on|off</code> — bảo trì/mở tất cả game + nạp/rút\n"
        "<code>/baotrigame games on|off</code> — tất cả game\n"
        "<code>/baotrigame nap rut on|off</code> — nạp/rút\n"
        "<code>/baotriht</code>, <code>/baotriall on|off</code>, <code>/baotritc on|off</code> — bảo trì hệ thống hiện có\n"
        "<code>/trangthai</code> — tổng quan bot\n"
        "<code>/hu số_tiền</code> — đặt hũ Tài Xỉu 3D; <code>/ep 1 3 4</code> | <code>/ep t</code> | <code>/ep x</code> | <code>/ep off</code> — ép kết quả 3D (chat riêng, áp dụng cả khi có người chơi thật cược)\n\n"
        "<b>👥 Người dùng</b>\n<code>/user ID</code> — hồ sơ; <code>/timuser từ_khóa</code> — tìm user\n"
        "<code>/ban ID</code> / <code>/unban ID</code> — khóa/mở tài khoản\n"
        "<code>/camgame ID game</code> / <code>/mogame ID game|all</code> — khóa/mở game\n"
        "<code>/camtn ID nap|rut</code> / <code>/motn ID nap|rut|all</code> — khóa/mở nạp/rút\n"
        "<code>/dsban</code> — danh sách tài khoản bị khóa\n\n"
        "<b>💰 Số dư & giao dịch</b>\n<code>/add ID số_tiền</code>, <code>/sub ID số_tiền</code>, <code>/setsd ID số_tiền</code>\n"
        "<code>/naptien ID số_tiền</code> — nạp tay; <code>/dsnap</code> / <code>/dsrut</code> — danh sách chờ\n\n"
        "<b>📊 Thống kê / code</b>\n<code>/stats</code>, <code>/all</code>, <code>/thongke</code>, <code>/tong</code>, <code>/check ID</code>, <code>/hisall</code>\n"
        "<code>/top</code> — Top tương tác hôm nay; <code>/topsodu [n]</code> — Top số dư; <code>/topcuoc [n]</code>, <code>/taocode</code>, <code>/taocodeall</code>, <code>/xoacode</code>, <code>/taogift</code>, <code>/dsgift</code>, <code>/xoagift</code>\n"
        "<code>/dsnaphomnay</code> — người đã nạp thành công hôm nay; <code>/tangcodenap giá_trị vòng hạn [homnay|all|id,id] [nạp_tối_thiểu]</code> — tặng code thủ công cho người đã nạp; <code>/yccode mã nap|tongnap số_tiền|off</code> — thêm/gỡ yêu cầu nhập code\n"
        "<code>/resethoanall</code> — reset TOÀN BỘ hoàn trả của <b>1 người</b>: bot hỏi ID rồi hỏi loại (ngày/tuần/cả hai), có xác nhận; gõ nhanh: <code>/resethoanall ID ngay|tuan|all</code> (<code>/resethoan</code> là lệnh cũ, cùng chức năng)\n"
        "<b>🎁 Khuyến mãi & báo cáo</b>\n"
        "<code>/kmgio</code> — xem/điều khiển giờ vàng nạp 10% (<code>on</code> / <code>off</code> / <code>auto</code>)\n"
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
        "<code>/send nội_dung</code>, <code>/rep ID nội_dung</code> — thông báo/liên hệ user\n"
        "<b>🔇 Tắt / bật room</b>\n"
        "<code>/tatroom</code> — bot ngừng gửi mọi tin nhắn vào nhóm (dùng trong nhóm, hoặc chat riêng: <code>/tatroom ID_nhóm</code>)\n"
        "<code>/moroom</code> — bật lại; <code>/trangthairoom</code> — xem trạng thái; <code>/tatcuoc on|off</code> — chỉ khóa/mở cược\n\n"
        "<b>🆕 Mới</b>\n"
        "<code>/admin</code> — menu admin dạng nút bấm (hoặc nút ADMIN trong menu bot); <code>/adminhelp</code> — bảng chữ này\n"
        "<code>/xoacuoc ID</code> — xoá vòng cược; <code>/themcuoc ID số_tiền</code> — cộng tiến độ cược\n"
        "<code>/themvongcuoc ID số_tiền</code> — thêm yêu cầu cược; <code>/ktvc ID</code> — kiểm tra vòng cược; <code>/vcall x7</code> — thêm vòng cược toàn bộ số dư của mọi user\n"
        "<code>/xuatthongke [kỳ]</code> — xuất file thống kê hệ thống (Excel nhiều sheet + biểu đồ)\n"
        "<code>/resetthongke</code> — reset thống kê từ đầu (<code>/resetthongke khoiphuc</code> để quay lại)\n"
        "<code>/xoanap mã_GD</code>, <code>/xoarut mã_GD</code> — xoá giao dịch, thống kê tự trừ\n"
        "<code>/tatroom all</code>, <code>/moroom all</code> — tắt/bật hoàn toàn mọi room\n\n"
        "<b>Trạng thái bảo trì</b> (🔴 bảo trì, 🟢 hoạt động):\n" + _admin_mt_lines()
    )
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

@admin_only
async def baotrigame_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    args = ctx.args or []
    msg = update.effective_message
    if len(args) < 2 or args[-1].lower() not in ("on", "off"):
        return await msg.reply_text("Cú pháp: <code>/baotrigame [game...] on|off</code>\nGame: room tx3d pt br bd bl sl xxd pk ll; tính năng: nap rut; nhóm: games all\n\n" + _admin_mt_lines(), parse_mode=ParseMode.HTML)
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
        return await update.effective_message.reply_text("Cú pháp: <code>/camgame ID room|tx3d|pt|br|bd|bl|sl|xxd|pk|ll</code>", parse_mode=ParseMode.HTML)
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
    await update.effective_message.reply_text(f"Đã cập nhật <code>{target}</code>:\n💳 Số dư trước: <code>{fmt_money(old)}đ</code>\n💰 Số dư sau: <code>{fmt_money(amount)}đ</code>", parse_mode=ParseMode.HTML)

async def _interaction_top_text(bot, group_id, date_text, limit=10):
    rows = query(
        "SELECT user_id, interaction_count FROM daily_top_interactions "
        "WHERE group_id=%s AND date=%s AND interaction_count>=200 ORDER BY interaction_count DESC, user_id ASC LIMIT %s",
        (group_id, date_text, limit)
    ) or []
    if not rows:
        return "🏆 <b>TOP 10 TƯƠNG TÁC HÔM NAY</b>\n\nChưa có tin nhắn hợp lệ nào được ghi nhận trong nhóm."
    lines = [
        "🏆 <b>TOP 10 TƯƠNG TÁC HÔM NAY</b>",
        "📌 Chỉ xếp hạng thành viên đạt từ 200 tin hợp lệ/ngày.",
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
        f"⚠️ Mỗi {INTERACTION_WINDOW_SECONDS} giây chỉ tính tối đa 1 tin. Không spam, flood, gửi lặp ký tự hoặc dùng bot/farm tương tác; nội dung quảng cáo/spam không được tính.",
        "💡 Gõ /checktt để xem tiến trình của bạn."
    ]
    return "\n".join(lines)

@admin_only
async def reset_system_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Yêu cầu xác nhận trước khi xóa dữ liệu hệ thống."""
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("⚠️ XÁC NHẬN XÓA TOÀN BỘ", callback_data="sysreset_yes"),
        InlineKeyboardButton("Hủy", callback_data="sysreset_no"),
    ]])
    await update.effective_message.reply_text(
        "⚠️ <b>XÁC NHẬN RESET TOÀN BỘ HỆ THỐNG</b>\\n\\n"
        "Thao tác này sẽ xóa dữ liệu người dùng, số dư, lịch sử giao dịch, cược, giftcode, "
        "thống kê và dữ liệu vận hành trong cơ sở dữ liệu. Không thể hoàn tác.\\n"
        "Các cấu hình trong bảng settings được giữ lại để bot tiếp tục khởi động.\\n\\n"
        "Chỉ nhấn xác nhận nếu bạn đã sao lưu dữ liệu.",
        reply_markup=kb, parse_mode=ParseMode.HTML
    )

async def reset_system_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not q:
        return
    if q.from_user.id not in ADMIN_IDS:
        return await q.answer("Bạn không có quyền thực hiện.", show_alert=True)
    if q.data == "sysreset_no":
        await q.answer("Đã hủy.")
        return await q.edit_message_text("Đã hủy reset hệ thống.")
    if q.data != "sysreset_yes":
        return
    await q.answer("Đang thực hiện reset…")
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT tablename FROM pg_tables
            WHERE schemaname='public' AND tablename <> 'settings'
              AND tablename NOT LIKE 'schema_migrations%'
            ORDER BY tablename
        """)
        tables = [r[0] for r in cur.fetchall()]
        if tables:
            quoted = ", ".join('"' + name.replace('"', '""') + '"' for name in tables)
            cur.execute("TRUNCATE TABLE " + quoted + " RESTART IDENTITY CASCADE")
        conn.commit()
        _interaction_seen.clear()
        await q.edit_message_text(
            "✅ <b>ĐÃ RESET DỮ LIỆU HỆ THỐNG</b>\\n"
            f"Đã làm sạch {len(tables)} bảng dữ liệu. Cấu hình settings được giữ lại.",
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        conn.rollback()
        print(f"Lỗi reset toàn hệ thống: {e}")
        await q.edit_message_text("❌ Reset thất bại; cơ sở dữ liệu đã rollback. Kiểm tra log máy chủ.")
    finally:
        cur.close()
        conn.close()

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

def _interaction_reward_table(count, claimed):
    """Bảng mốc thưởng tin nhắn: ✅ đã đạt, 🔒 chưa đạt."""
    rows = []
    for m, reward in INTERACTION_MILESTONES:
        if count >= m:
            if count < 200:
                tag = "đạt mốc; cần đủ 200 tin/ngày mới nhận code"
            else:
                tag = "đã nhận code" if m in claimed else "đạt mốc, gõ /checktt để nhận"
            rows.append(f"✅ <b>{fmt_money(m)}</b> tin → <b>{fmt_money(reward)}đ</b> · <i>{tag}</i>")
        else:
            rows.append(f"🔒 <b>{fmt_money(m)}</b> tin → <b>{fmt_money(reward)}đ</b> · <i>còn {fmt_money(m-count)} tin</i>")
    return "\n".join(rows)

def _interaction_top_prize_table():
    medals = {1: "🥇", 2: "🥈", 3: "🥉"}
    lines = []
    for rank in (1, 2, 3, 4):
        lines.append(f"{medals.get(rank, '🔝')} Top {rank} → <b>{fmt_money(TOP_INTERACTION_PRIZES[rank])}đ</b>")
    lines.append(f"⭐️ Top 5 - 10 → <b>{fmt_money(TOP_INTERACTION_PRIZES[5])}đ</b> / người")
    return "\n".join(lines)

async def checktt_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    if not user:
        return
    if is_banned(user.id):
        return
    group_id = chat.id if chat and chat.type != "private" else (GROUP_IDS[0] if GROUP_IDS else None)
    if not group_id:
        return await update.effective_message.reply_text("Chưa cấu hình nhóm tương tác.")
    today = get_vietnam_date()

    # Số tin HÔM NAY: đây là số dùng để xét mốc thưởng (khớp với lúc phát code).
    daily_row = query("SELECT interaction_count FROM daily_top_interactions WHERE user_id=%s AND group_id=%s AND date=%s",
                      (user.id, group_id, today))
    count = int(daily_row[0][0] or 0) if daily_row else 0
    cycle_row = query("SELECT interaction_count FROM group_interactions WHERE user_id=%s AND group_id=%s",
                      (user.id, group_id))
    cycle_count = int(cycle_row[0][0] or 0) if cycle_row else 0

    # Phát code trực tiếp qua bot: gửi lại code lỗi cũ trước, rồi phát các mốc mới đủ điều kiện.
    resent_ok = resent_fail = 0
    new_items = []
    try:
        resent_ok, resent_fail = await _resend_undelivered(ctx.bot, user.id, group_id, today)
        if count >= 200:
            new_items = await _issue_interaction_rewards(ctx.bot, user.id, group_id, count, today, notify_group=False)
    except Exception as e:
        print(f"Lỗi phát code /checktt cho {user.id}: {e}")
        traceback.print_exc()
    sent_ok = sum(1 for _m, _r, ok in new_items if ok) + resent_ok
    sent_fail = sum(1 for _m, _r, ok in new_items if not ok) + resent_fail

    rank_rows = query(
        "SELECT COUNT(*) + 1 FROM daily_top_interactions WHERE group_id=%s AND date=%s AND interaction_count > %s",
        (group_id, today, count)
    ) or []
    rank = int(rank_rows[0][0] or 1) if rank_rows else 1
    claimed_rows = query("SELECT milestone FROM interaction_reward_claims WHERE user_id=%s AND group_id=%s AND date=%s ORDER BY milestone",
                         (user.id, group_id, today)) or []
    claimed = {int(r[0]) for r in claimed_rows}
    next_milestone = next(((m, reward) for m, reward in INTERACTION_MILESTONES if count < m), None)
    if count < 200:
        progress = f"🔒 Cần tối thiểu 200 tin hợp lệ/ngày để nhận giftcode. Bạn còn <b>{200-count}</b> tin."
    elif next_milestone:
        m, reward = next_milestone
        progress = f"🎯 Mốc tiếp theo: <b>{fmt_money(m)}</b> tin — còn <b>{fmt_money(m-count)}</b> tin để nhận <b>{fmt_money(reward)}đ</b>."
    else:
        progress = "👑 Bạn đã đạt toàn bộ mốc tương tác trong ngày!"
    total_reward = sum(r for _, r in INTERACTION_MILESTONES)
    earned_total = sum(r for m, r in INTERACTION_MILESTONES if count >= m)

    notice = ""
    if sent_ok:
        notice += f"✅ <b>Bot vừa gửi {sent_ok} giftcode vào tin nhắn riêng của bạn.</b> Hãy kiểm tra chat với bot!\n"
    if sent_fail:
        notice += (f"⚠️ Có {sent_fail} giftcode chưa gửi được vì bot không nhắn riêng cho bạn được. "
                   f"Hãy mở @{BOT_USERNAME}, bấm <b>/start</b> rồi gõ lại <b>/checktt</b> để nhận.\n")
    if notice:
        notice += "\n"

    await update.effective_message.reply_text(
        f"📊 <b>THỐNG KÊ TƯƠNG TÁC HÔM NAY</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👤 {html.escape(user.full_name or 'Thành viên')} · ID {mask_user_id(user.id)}\n"
        f"💬 Tin hợp lệ hôm nay: <b>{fmt_money(count)}</b>\n"
        f"🔁 Tích lũy chu kỳ: <b>{fmt_money(cycle_count)}</b>/6.000\n"
        f"🏆 Thứ hạng hiện tại: <b>{('#' + str(rank)) if count else 'Chưa có hạng'}</b>\n"
        f"💰 Đã đạt: <b>{fmt_money(earned_total)}đ</b> / {fmt_money(total_reward)}đ\n\n"
        f"{notice}"
        f"{progress}\n\n"
        f"🎁 <b>BẢNG MỐC THƯỞNG TIN NHẮN</b>\n"
        f"{_interaction_reward_table(count, claimed)}\n\n"
        f"👑 <b>THƯỞNG TOP 10 TƯƠNG TÁC NGÀY</b> <i>(chốt 00:00)</i>\n"
        f"{_interaction_top_prize_table()}\n\n"
        f"💡 Dùng /top để xem bảng xếp hạng nhóm.",
        parse_mode=ParseMode.HTML
    )

async def interaction_help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(
        "🎁 <b>HỆ THỐNG TƯƠNG TÁC NHÓM</b>\n\n"
        "• /checktt — xem tiến trình, bảng mốc và tiền thưởng hôm nay\n"
        "• /top — Top 10 tương tác hôm nay\n"
        "• /topnap — Top 10 nạp tiền\n"
        "• /topcuoc — Top 10 tổng cược\n"
        "• /code MÃ_CODE — nhập giftcode\n\n"
        "🎯 <b>Mốc thưởng tin nhắn</b>\n"
        + "\n".join(f"• {fmt_money(m)} tin → {fmt_money(r)}đ" for m, r in INTERACTION_MILESTONES) +
        "\n\n👑 <b>Thưởng Top ngày</b>\n"
        + _interaction_top_prize_table() +
        f"\n\nChỉ tính tin nhắn văn bản tự nhiên. Mỗi {INTERACTION_WINDOW_SECONDS} giây tối đa 1 tin (gửi 2-4 tin liên tiếp chỉ tính 1); "
        "lệnh bot, tin lặp và flood không được tính.\n"
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
                    "WHERE group_id=%s AND date=%s AND interaction_count>=200 ORDER BY interaction_count DESC, user_id ASC LIMIT 10",
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



def _tbl_name(name, width=14):
    """Làm sạch tên để vào bảng: bỏ ký tự điều khiển, cắt gọn theo độ rộng."""
    name = str(name or "Thành viên")
    # Bỏ emoji/ký hiệu: trong khối <pre> không chèn được emoji premium, và chúng làm lệch cột.
    name = re.sub(r"[\U0001F000-\U0001FFFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F\u200D]", "", name)
    name = re.sub(r"[\r\n\t]+", " ", name).strip() or "Thành viên"
    return name if len(name) <= width else name[:width - 1] + "…"

def _tbl_render(headers, rows, aligns):
    """Dựng bảng monospace có hàng/cột thẳng hàng, bọc trong <pre> để Telegram giữ nguyên khoảng trắng.
    aligns: chuỗi 'l'/'r' cho từng cột (trái/phải)."""
    cols = len(headers)
    widths = [len(str(h)) for h in headers]
    for r in rows:
        for c in range(cols):
            widths[c] = max(widths[c], len(str(r[c])))
    def line(cells):
        out = []
        for c in range(cols):
            t = str(cells[c])
            out.append(t.rjust(widths[c]) if aligns[c] == "r" else t.ljust(widths[c]))
        return " │ ".join(out)
    sep = "─┼─".join("─" * w for w in widths)
    body = [line(headers), sep] + [line(r) for r in rows]
    return "<pre>" + html.escape("\n".join(body)) + "</pre>"

# ============================================================
# ===== /daythang  /daythua : TOP ĐU DÂY TRONG NGÀY (top 3 + thưởng giftcode tự động) =====
# ============================================================
DAY_STREAK_MIN = 3                         # dây tối thiểu (số phiên liên tiếp) mới tính là "dây hợp lệ"
DAY_STREAK_PRIZES = {1: 50000, 2: 30000, 3: 20000}   # thưởng Top 1/2/3 (đ) - chỉnh tại đây
DAY_STREAK_WAGER = 3                       # yêu cầu vòng cược x3
DAY_STREAK_EXPIRE_HOURS = 24               # hạn dùng giftcode: 1 ngày
DAY_STREAK_KIND = {
    "win":  {"ctype": "DAYTHANG", "label": "THẮNG", "col": "max_win",  "at": "win_at",  "icon": "🔥"},
    "loss": {"ctype": "DAYTHUA",  "label": "THUA",   "col": "max_loss", "at": "loss_at", "icon": "🥶"},
}

def _today_key():
    return get_vietnam_time().strftime("%Y-%m-%d")

def _record_daily_streak(user_id, group_id, round_type):
    """Cập nhật dây thắng/thua liên tiếp TRONG NGÀY (reset theo ngày Việt Nam)."""
    day = _today_key()
    now_txt = get_vietnam_time().strftime("%Y-%m-%d %H:%M:%S")
    row = query("SELECT current_type,current_count,max_win,max_loss FROM daily_streaks "
                "WHERE user_id=%s AND group_id=%s AND day=%s", (user_id, group_id, day))
    if row:
        ctype, ccount, mwin, mloss = row[0][0], int(row[0][1] or 0), int(row[0][2] or 0), int(row[0][3] or 0)
    else:
        ctype, ccount, mwin, mloss = "", 0, 0, 0
    new_count = ccount + 1 if ctype == round_type else 1
    win_at = loss_at = None
    if round_type == "win" and new_count > mwin:
        mwin, win_at = new_count, now_txt
    if round_type == "loss" and new_count > mloss:
        mloss, loss_at = new_count, now_txt
    query(
        "INSERT INTO daily_streaks (user_id,group_id,day,current_type,current_count,max_win,max_loss,win_at,loss_at) "
        "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) "
        "ON CONFLICT (user_id,group_id,day) DO UPDATE SET "
        "current_type=EXCLUDED.current_type, current_count=EXCLUDED.current_count, "
        "max_win=EXCLUDED.max_win, max_loss=EXCLUDED.max_loss, "
        "win_at=COALESCE(EXCLUDED.win_at, daily_streaks.win_at), "
        "loss_at=COALESCE(EXCLUDED.loss_at, daily_streaks.loss_at)",
        (user_id, group_id, day, round_type, new_count, mwin, mloss, win_at, loss_at))

def _day_streak_top(group_id, day, kind, limit=3):
    """Top dây trong ngày: dây dài nhất trước, bằng nhau thì ai đạt mốc đó trước xếp trên."""
    k = DAY_STREAK_KIND[kind]
    return query(
        f"SELECT user_id, {k['col']} FROM daily_streaks "
        f"WHERE group_id=%s AND day=%s AND {k['col']}>=%s "
        f"ORDER BY {k['col']} DESC, {k['at']} ASC, user_id ASC LIMIT {int(limit)}",
        (group_id, day, DAY_STREAK_MIN)) or []

def _day_streak_prize_text(rank):
    return fmt_money(DAY_STREAK_PRIZES.get(rank, 0))

async def _streak_top_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE, streak_type: str):
    group = update.effective_chat
    gid = group.id if group and group.type != "private" else (GROUP_IDS[0] if GROUP_IDS else None)
    if not gid:
        return await update.effective_message.reply_text("Chưa xác định được nhóm thống kê.")
    k = DAY_STREAK_KIND[streak_type]
    day = _today_key()
    rows = _day_streak_top(gid, day, streak_type, 3)
    lines = [f"🏆 <b>Top đu dây {k['label']} hôm nay</b> (tính tới hiện tại)", ""]
    for rank in (1, 2, 3):
        if rank <= len(rows):
            uid, best = rows[rank - 1]
            lines.append(f"Top {rank}: <code>{mask_user_id(uid)}</code> | {int(best)} trận | thưởng {_day_streak_prize_text(rank)}")
        else:
            lines.append(f"Top {rank}: — | thưởng {_day_streak_prize_text(rank)}")
    lines.append("")
    me = update.effective_user.id
    own = query(f"SELECT {k['col']}, current_type, current_count FROM daily_streaks "
                f"WHERE user_id=%s AND group_id=%s AND day=%s", (me, gid, day)) or []
    my_best = int(own[0][0] or 0) if own else 0
    if my_best >= DAY_STREAK_MIN:
        rank = next((i for i, r in enumerate(rows, 1) if int(r[0]) == me), None)
        now_cnt = int(own[0][2] or 0) if own[0][1] == streak_type else 0
        lines.append(f"Dây {k['label'].lower()} dài nhất của bạn hôm nay: <b>{my_best} trận</b>"
                     + (f" · đang đứng <b>Top {rank}</b>" if rank else " · chưa lọt Top 3"))
        if now_cnt:
            lines.append(f"Đang có: {now_cnt} trận liên tiếp")
    else:
        lines.append("Bạn chưa có dây hợp lệ hôm nay.")
    lines.append(f"<i>Dây hợp lệ từ {DAY_STREAK_MIN} trận liên tiếp · chốt thưởng 00:00 · giftcode gửi riêng qua bot "
                 f"(x{DAY_STREAK_WAGER} vòng cược, hạn 1 ngày)</i>")
    await update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

async def daythang_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        await _streak_top_cmd(update, ctx, "win")
    except Exception as e:
        print(f"Lỗi /daythang: {e}")
        await update.effective_message.reply_text("Không tải được bảng dây thắng. Vui lòng thử lại.")

async def daythua_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        await _streak_top_cmd(update, ctx, "loss")
    except Exception as e:
        print(f"Lỗi /daythua: {e}")
        await update.effective_message.reply_text("Không tải được bảng dây thua. Vui lòng thử lại.")

async def _send_day_streak_code(bot, user_id, kind, rank, streak, reward, code, day_text):
    k = DAY_STREAK_KIND[kind]
    await bot.send_message(
        user_id,
        f"🏆 <b>BẠN ĐẠT TOP {rank} DÂY {k['label']} NGÀY {day_text}!</b>\n"
        f"{k['icon']} Dây dài nhất: <b>{int(streak)} trận</b>\n"
        f"🎁 Giftcode: <code>{code}</code>\n"
        f"💰 Giá trị: <b>{fmt_money(reward)}đ</b> · Vòng cược x{DAY_STREAK_WAGER}\n"
        f"⏰ Hạn dùng 1 ngày. Nhập bằng <code>/code {code}</code>.",
        parse_mode=ParseMode.HTML)

async def settle_day_streak_loop(bot):
    """00:00 mỗi ngày: chốt Top 3 dây thắng/thua của hôm qua, tự tạo giftcode và gửi riêng cho từng người."""
    while True:
        try:
            y = get_vietnam_time().date() - timedelta(days=1)
            day = y.strftime("%Y-%m-%d")
            day_text = y.strftime("%d/%m/%Y")
            for group_id in GROUP_IDS:
                for kind, k in DAY_STREAK_KIND.items():
                    done = query("SELECT 1 FROM daily_streak_settlements WHERE group_id=%s AND day=%s AND kind=%s",
                                 (group_id, day, kind))
                    if done:
                        continue
                    rows = _day_streak_top(group_id, day, kind, 3)
                    public = [f"🏆 <b>CHỐT TOP ĐU DÂY {k['label']} NGÀY {day_text}</b>"]
                    for rank, (uid, best) in enumerate(rows, 1):
                        reward = DAY_STREAK_PRIZES.get(rank, 0)
                        if reward <= 0:
                            continue
                        code = gen_gift_code(k["ctype"])
                        expiry = get_vietnam_time() + timedelta(hours=DAY_STREAK_EXPIRE_HOURS)
                        created = query(
                            "INSERT INTO giftcodes (code,ctype,reward,wager,expiry,require_deposit,required_amount,"
                            "bound_user,used,created_by,created_at) "
                            "VALUES (%s,%s,%s,%s,%s,0,0,%s,0,0,%s) ON CONFLICT DO NOTHING RETURNING code",
                            (code, k["ctype"], reward, DAY_STREAK_WAGER, expiry, uid, get_vietnam_datetime_db()))
                        if created:
                            ins = query(
                                "INSERT INTO daily_streak_rewards (user_id,group_id,day,kind,rank,streak,reward_amount,code,created_at) "
                                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING RETURNING user_id",
                                (uid, group_id, day, kind, rank, int(best), reward, code, get_vietnam_datetime_db()))
                            if ins:
                                try:
                                    await _send_day_streak_code(bot, uid, kind, rank, best, reward, code, day_text)
                                    query("UPDATE daily_streak_rewards SET sent=1,tries=tries+1 WHERE user_id=%s AND group_id=%s AND day=%s AND kind=%s",
                                          (uid, group_id, day, kind))
                                except Exception:
                                    query("UPDATE daily_streak_rewards SET tries=tries+1 WHERE user_id=%s AND group_id=%s AND day=%s AND kind=%s",
                                          (uid, group_id, day, kind))
                        public.append(f"{'🥇' if rank==1 else '🥈' if rank==2 else '🥉'} Top {rank}: "
                                      f"<code>{mask_user_id(uid)}</code> | {int(best)} trận | thưởng {fmt_money(reward)}")
                    if rows:
                        public.append("\n🎁 Giftcode đã gửi riêng qua bot (x%d vòng cược, hạn 1 ngày). "
                                      "Ai chưa nhận được hãy mở bot bấm /start." % DAY_STREAK_WAGER)
                        try:
                            await bot.send_message(group_id, "\n".join(public), parse_mode=ParseMode.HTML)
                        except Exception as e:
                            print(f"Không gửi được bảng chốt dây {kind} nhóm {group_id}: {e}")
                    query("INSERT INTO daily_streak_settlements (group_id,day,kind,settled_at) VALUES (%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                          (group_id, day, kind, get_vietnam_datetime_db()))
            # Gửi lại giftcode chưa tới được người nhận (chưa /start bot), tối đa 10 lần, chỉ khi code còn hạn.
            pend = query(
                "SELECT r.user_id,r.group_id,r.day,r.kind,r.rank,r.streak,r.reward_amount,r.code "
                "FROM daily_streak_rewards r JOIN giftcodes g ON g.code=r.code "
                "WHERE r.sent=0 AND r.tries<10 AND g.used=0 AND g.expiry>NOW() LIMIT 20") or []
            for uid, gid_, day_, kind_, rank_, streak_, reward_, code_ in pend:
                try:
                    dt = datetime.strptime(day_, "%Y-%m-%d").strftime("%d/%m/%Y")
                    await _send_day_streak_code(bot, uid, kind_, rank_, streak_, reward_, code_, dt)
                    query("UPDATE daily_streak_rewards SET sent=1,tries=tries+1 WHERE user_id=%s AND group_id=%s AND day=%s AND kind=%s",
                          (uid, gid_, day_, kind_))
                except Exception:
                    query("UPDATE daily_streak_rewards SET tries=tries+1 WHERE user_id=%s AND group_id=%s AND day=%s AND kind=%s",
                          (uid, gid_, day_, kind_))
        except Exception as e:
            print(f"Lỗi settle dây thắng/thua: {e}")
        await asyncio.sleep(30)

async def topnap_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Top 10 người nạp thành công."""
    rows = query(
        "SELECT user_id, SUM(amount) AS total FROM deposit_history "
        "WHERE LOWER(COALESCE(status,'')) IN ('success','successful','completed','approved','done') "
        "GROUP BY user_id ORDER BY total DESC LIMIT 10"
    ) or []
    lines = ["💎 <b>TOP NẠP TIỀN</b>", "<i>10 thành viên nạp nhiều nhất</i>"]
    if rows:
        table_rows = []
        for i, row in enumerate(rows, 1):
            uid, total = row[0], int(row[1] or 0)
            display = await _telegram_name(ctx.bot, uid, {})
            table_rows.append((f"{i:02d}", _tbl_name(display), f"{fmt_money(total)}đ"))
        lines.append(_tbl_render(("Hạng", "Người chơi", "Tổng nạp"), table_rows, "llr"))
    else:
        lines.append("Chưa có dữ liệu nạp thành công.")
    await update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

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



# ============================================================
# TẮT/BẬT TIN NHẮN BOT TRONG ROOM
# /tatroom — chặn bot gửi tin nhắn vào nhóm đã cấu hình
# /moroom  — bật lại tin nhắn bot trong nhóm
# Trạng thái được lưu trong bảng settings nên tồn tại sau khi restart.
# ============================================================
def _room_mute_key(chat_id):
    return f"room_muted_{int(chat_id)}"

# Cache trạng thái tắt room để không phải truy vấn DB cho mỗi tin nhắn gửi đi.
_ROOM_MUTE_CACHE = {}          # chat_id -> (muted: bool, checked_at: float)
_ROOM_MUTE_CACHE_TTL = 20      # giây
# Tin xác nhận bật/tắt room (bắt đầu bằng 🔇/🔊) vẫn được gửi vào nhóm.
_ROOM_MUTE_ALLOW_PREFIX = ("🔇", "🔊")
# Thông báo NẠP / RÚT thành công vẫn gửi lên nhóm kể cả khi room đã tắt (gửi qua send_group_notice).
import contextvars as _contextvars
_ROOM_MUTE_BYPASS = _contextvars.ContextVar("room_mute_bypass", default=False)

async def send_group_notice(bot, *args, **kwargs):
    """bot.send_message nhưng KHÔNG bị chặn bởi chế độ tắt room (dùng cho thông báo nạp/rút thành công)."""
    tok = _ROOM_MUTE_BYPASS.set(True)
    try:
        return await bot.send_message(*args, **kwargs)
    finally:
        _ROOM_MUTE_BYPASS.reset(tok)

def _is_room_muted(chat_id):
    try:
        cid = int(chat_id)
    except (TypeError, ValueError):
        return False
    import time as _time
    cached = _ROOM_MUTE_CACHE.get(cid)
    if cached and _time.time() - cached[1] < _ROOM_MUTE_CACHE_TTL:
        return cached[0]
    try:
        rows = query("SELECT value FROM settings WHERE key=%s", (_room_mute_key(cid),))
        muted = bool(rows and str(rows[0][0]) == "1")
    except Exception:
        return cached[0] if cached else False
    _ROOM_MUTE_CACHE[cid] = (muted, _time.time())
    return muted

def _set_room_muted(chat_id, muted: bool):
    import time as _time
    query(
        "INSERT INTO settings (key, value) VALUES (%s, %s) "
        "ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value",
        (_room_mute_key(chat_id), "1" if muted else "0")
    )
    _ROOM_MUTE_CACHE[int(chat_id)] = (muted, _time.time())

async def _room_mute_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE, muted: bool):
    user = update.effective_user
    msg = update.effective_message
    if not user or user.id not in ADMIN_IDS:
        if msg:
            await msg.reply_text("⛔ Bạn không có quyền dùng lệnh này.")
        return
    if ctx.args and str(ctx.args[0]).lower() in ("all", "tatca"):
        for _g in GROUP_IDS:
            _set_room_muted(_g, muted)
        _t = (f"🔇 <b>ĐÃ TẮT TẤT CẢ ROOM</b> ({len(GROUP_IDS)} nhóm). Bot ngừng gửi tin và ngừng chạy game; cược phiên đang mở được hoàn lại. Bật lại: <code>/moroom all</code>."
              if muted else f"🔊 <b>ĐÃ BẬT LẠI TẤT CẢ ROOM</b> ({len(GROUP_IDS)} nhóm).")
        return await msg.reply_text(_t, parse_mode=ParseMode.HTML)
    chat = update.effective_chat
    # Trong nhóm: áp dụng cho nhóm đang chat. Trong chat riêng: /tatroom [ID_nhóm] (mặc định nhóm đầu tiên).
    if chat and chat.type != "private":
        target_group = chat.id
    else:
        target_group = None
        if ctx.args:
            try:
                target_group = int(ctx.args[0])
            except ValueError:
                return await msg.reply_text("❌ ID nhóm không hợp lệ. Ví dụ: /tatroom -1001234567890")
        elif GROUP_IDS:
            target_group = GROUP_IDS[0]
    if target_group is None:
        return await msg.reply_text("❌ Chưa cấu hình nhóm trong GROUP_IDS.")
    _set_room_muted(target_group, muted)
    if muted:
        text = (f"🔇 <b>ĐÃ TẮT ROOM</b> <code>{target_group}</code>\n"
                f"Bot sẽ không gửi bất kỳ tin nhắn nào vào nhóm này, và tạm dừng ván game mới.\n"
                f"Bật lại bằng <code>/moroom</code>.")
    else:
        text = (f"🔊 <b>ĐÃ BẬT LẠI ROOM</b> <code>{target_group}</code>\n"
                f"Bot gửi tin nhắn và chạy game trong nhóm bình thường.")
    await msg.reply_text(text, parse_mode=ParseMode.HTML)

@admin_only
async def tatroom_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await _room_mute_command(update, ctx, True)

@admin_only
async def moroom_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await _room_mute_command(update, ctx, False)

@admin_only
async def trangthairoom_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    lines = ["🏠 <b>TRẠNG THÁI ROOM</b>"]
    for gid in GROUP_IDS:
        lines.append(f"{'🔇 ĐÃ TẮT' if _is_room_muted(gid) else '🔊 ĐANG BẬT'} · <code>{gid}</code>")
    await update.effective_message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

# Chặn MỌI kiểu gửi/sửa tin của bot vào room đang tắt (tin nhắn, ảnh, gif, video, file, sticker,
# poll, copy, sửa tin...) — kể cả tin tự động từ các vòng lặp nền.
def _guard_room_mute(method_name, text_kw=None, allow_prefix=False):
    orig = getattr(Bot, method_name, None)
    if orig is None or getattr(orig, "_room_mute_guarded", False):
        return
    @functools.wraps(orig)
    async def guarded(self, *args, **kwargs):
        chat_id = kwargs.get("chat_id", args[0] if args else None)
        try:
            numeric = int(chat_id)
        except (TypeError, ValueError):
            numeric = None
        if numeric is not None and numeric < 0 and _is_room_muted(numeric) and not _ROOM_MUTE_BYPASS.get():
            if allow_prefix:
                text = kwargs.get(text_kw, args[1] if len(args) > 1 else "")
                if str(text or "").startswith(_ROOM_MUTE_ALLOW_PREFIX):
                    return await orig(self, *args, **kwargs)
            return None
        return await orig(self, *args, **kwargs)
    guarded._room_mute_guarded = True
    setattr(Bot, method_name, guarded)

_guard_room_mute("send_message", "text", allow_prefix=True)
for _m in ("send_photo", "send_animation", "send_video", "send_document", "send_audio",
           "send_voice", "send_sticker", "send_media_group", "send_poll", "copy_message",
           "pin_chat_message", "send_dice", "send_video_note"):
    _guard_room_mute(_m)

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
def _rp_bal_map(uid):
    """{id dòng lịch sử: (số dư trước, số dư sau)}. Dòng mới lấy giá trị đã lưu; dòng cũ suy ngược từ số dư hiện tại."""
    cur = query("SELECT balance FROM users WHERE user_id=%s", (uid,))
    run = int(cur[0][0] or 0) if cur else 0
    raw = query("SELECT id, amount, bal_before, bal_after FROM history WHERE user_id=%s ORDER BY id DESC LIMIT 200000", (uid,)) or []
    m = {}
    for hid, amt, bb, ba in raw:
        amt = int(amt or 0)
        if bb is not None and ba is not None:
            before, after = int(bb), int(ba)
        else:
            after, before = run, run - amt
        m[hid] = (before, after)
        run = before
    return m

def _rp_collect(kind, uid, start, end):
    """Trả về dict: headers, rows (mới nhất trước), money_col, sum_cols, extra."""
    rows, extra = [], {}
    if kind == "his":
        raw = query("SELECT id, amount, note, time FROM history WHERE user_id=%s ORDER BY id DESC LIMIT 50000", (uid,)) or []
        _bm = _rp_bal_map(uid)
        inc = out = 0
        for r in raw:
            if not _rp_in_range(r[3], start, end):
                continue
            amt = int(r[1] or 0)
            _b = _bm.get(r[0], ("", ""))
            rows.append((r[0], r[3] or "", amt, _b[0], _b[1], r[2] or ""))
            if amt >= 0:
                inc += amt
            else:
                out += -amt
        extra = {"in": inc, "out": out}
        return {"headers": ["#", "Thời gian", "Biến động (đ)", "Số dư trước (đ)", "Số dư sau (đ)", "Nội dung"], "rows": rows,
                "money_cols": [2, 3, 4], "sum_cols": [], "signed_col": 2, "extra": extra}
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
        _bm = _rp_bal_map(uid)
        bets = wins = nb = nw = 0
        for r in raw:
            if not _rp_in_range(r[3], start, end):
                continue
            amt = int(r[1] or 0)
            _b = _bm.get(r[0], ("", ""))
            if amt < 0:
                rows.append((r[0], r[3] or "", "Cược", -amt, _b[0], _b[1], r[2] or "")); bets += -amt; nb += 1
            else:
                rows.append((r[0], r[3] or "", "Thắng / Hoàn", amt, _b[0], _b[1], r[2] or "")); wins += amt; nw += 1
        extra = {"bets": bets, "wins": wins, "net": wins - bets, "n_bet": nb, "n_win": nw}
        return {"headers": ["#", "Thời gian", "Loại", "Số tiền (đ)", "Số dư trước (đ)", "Số dư sau (đ)", "Nội dung"], "rows": rows,
                "money_cols": [3, 4, 5], "sum_cols": [], "extra": extra, "status_col": 2}
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
                "rows": rows, "money_cols": [4], "sum_cols": [4], "extra": extra, "status_col": 6}
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
        _id, t, amt, bb, ba, note = row
        _bal = f'\n    {ce("💳")} Số dư: <code>{_rp_money(bb)}đ</code> → <code>{_rp_money(ba)}đ</code>' if bb != "" else ""
        return (f'{ce("📈" if amt >= 0 else "📉")} <b>{"+" if amt >= 0 else "−"}{_rp_money(abs(amt))}đ</b> · {e(str(note))[:70]}'
                f'{_bal}\n'
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
        _id, t, loai, amt, bb, ba, note = row
        _bal = f'\n    {ce("💳")} Số dư: <code>{_rp_money(bb)}đ</code> → <code>{_rp_money(ba)}đ</code>' if bb != "" else ""
        return (f'{ce("🎲" if loai == "Cược" else "🏆")} <b>{_rp_money(amt)}đ</b> · {e(loai)} · {e(str(note))[:60]}'
                f'{_bal}\n'
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
_XL_THEME = {
    "Tổng quan": ("183153", "1F4E79"), "Theo ngày": ("1F618D", "2874A6"),
    "Biến động số dư": ("1F618D", "2874A6"), "Danh sách user": ("1F618D", "2874A6"),
    "Nạp": ("1E8449", "239B56"), "Lịch sử nạp": ("1E8449", "239B56"), "Top nạp": ("1E8449", "239B56"),
    "Rút": ("B03A2E", "CB4335"), "Lịch sử rút": ("B03A2E", "CB4335"),
    "Cược & Thắng": ("6C3483", "7D3C98"), "Top cược": ("6C3483", "7D3C98"),
    "Code đã nhập": ("B9770E", "D68910"), "Top số dư": ("B9770E", "D68910"),
    "Gift đã mua": ("117A8B", "148F77"), "Gift đã dùng": ("117A8B", "148F77"),
}
_XL_STATUS = {
    "Thành công": ("D5F5E3", "1E8449"), "Đã dùng": ("D5F5E3", "1E8449"), "Thắng / Hoàn": ("D5F5E3", "1E8449"),
    "Chờ duyệt": ("FCF3CF", "9A7D0A"), "Chưa dùng": ("FCF3CF", "9A7D0A"),
    "Từ chối": ("FADBD8", "B03A2E"), "Hết hạn": ("FADBD8", "B03A2E"), "Cược": ("FADBD8", "B03A2E"),
}

def _rp_build_xlsx(title, subtitle, sheets):
    # File Excel nhiều sheet: banner tiêu đề, thẻ KPI, bảng có zebra, màu trạng thái, dòng tổng, biểu đồ.
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    from openpyxl.chart import BarChart, LineChart, Reference
    from openpyxl.worksheet.properties import PageSetupProperties

    def fill(color):
        return PatternFill("solid", fgColor=color)

    hair = Side(style="hair", color="BFC9D9")
    wb = Workbook()
    wb.remove(wb.active)
    used = set()
    for sh in sheets:
        name = re.sub(r"[\\/*?:\[\]]", "", sh["name"])[:31] or "Sheet"
        base, i = name, 2
        while name in used:
            name = f"{base[:28]}_{i}"
            i += 1
        used.add(name)
        dark, mid = _XL_THEME.get(sh["name"], ("183153", "246B8E"))
        ws = wb.create_sheet(name)
        ws.sheet_properties.tabColor = dark
        ws.sheet_view.showGridLines = False
        headers = [str(h) for h in sh["headers"]]
        rows = sh["rows"]
        ncol = max(2, len(headers))
        money = set(sh.get("money_cols", []))
        signed = set(sh.get("signed_cols", []))
        if sh.get("signed_col") is not None:
            signed.add(sh["signed_col"])
        right = set(sh.get("right_cols", []))
        status_col = sh.get("status_col")

        # --- banner ---
        ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=ncol)
        c = ws.cell(1, 1, title)
        c.font = Font(name="Calibri", size=17, bold=True, color="FFFFFF")
        c.alignment = Alignment(horizontal="center", vertical="center")
        for ci in range(1, ncol + 1):
            ws.cell(1, ci).fill = fill(dark)
        ws.row_dimensions[1].height = 38
        ws.merge_cells(start_row=2, start_column=1, end_row=2, end_column=ncol)
        c2 = ws.cell(2, 1, f"{subtitle}   |   Xuất lúc: {get_vietnam_datetime_db()}   |   Số dòng: {len(rows)}")
        c2.font = Font(name="Calibri", italic=True, size=10, color="FFFFFF")
        c2.alignment = Alignment(horizontal="center", vertical="center")
        for ci in range(1, ncol + 1):
            ws.cell(2, ci).fill = fill(mid)
        ws.row_dimensions[2].height = 20
        ws.row_dimensions[3].height = 8

        # --- thẻ KPI ---
        r = 4
        kpis = sh.get("kpis") or []
        if kpis:
            per_row = max(1, min(len(kpis), 4 if ncol >= 4 else ncol))
            span = max(1, ncol // per_row)
            for g in range(0, len(kpis), per_row):
                group = kpis[g:g + per_row]
                for j, (label, val, kind) in enumerate(group):
                    c1 = 1 + j * span
                    c2_ = ncol if j == per_row - 1 else c1 + span - 1
                    if c2_ > c1:
                        ws.merge_cells(start_row=r, start_column=c1, end_row=r, end_column=c2_)
                        ws.merge_cells(start_row=r + 1, start_column=c1, end_row=r + 1, end_column=c2_)
                    lab = ws.cell(r, c1, str(label))
                    lab.font = Font(name="Calibri", size=10, bold=True, color="5D6D7E")
                    lab.alignment = Alignment(horizontal="center", vertical="center")
                    vc = ws.cell(r + 1, c1)
                    numeric = isinstance(val, (int, float)) and not isinstance(val, bool)
                    color = dark
                    if kind == "signed" and numeric:
                        color = "1E8449" if val >= 0 else "C0392B"
                    if numeric:
                        vc.value = val
                        vc.number_format = {"money": '#,##0" đ"', "signed": '+#,##0" đ";-#,##0" đ";0" đ"'}.get(kind, "#,##0")
                    else:
                        vc.value = str(val)
                        vc.data_type = "s"
                    vc.font = Font(name="Calibri", size=17, bold=True, color=color)
                    vc.alignment = Alignment(horizontal="center", vertical="center")
                    for ci in range(c1, c2_ + 1):
                        ws.cell(r, ci).fill = fill("EAF2F8")
                        ws.cell(r + 1, ci).fill = fill("F7FBFE")
                        ws.cell(r, ci).border = Border(top=Side(style="thick", color=mid))
                        ws.cell(r + 1, ci).border = Border(bottom=hair)
                ws.row_dimensions[r].height = 20
                ws.row_dimensions[r + 1].height = 32
                ws.row_dimensions[r + 2].height = 8
                r += 3
        hr = r

        # --- header ---
        for ci, h in enumerate(headers, 1):
            hc = ws.cell(hr, ci, h)
            hc.font = Font(name="Calibri", bold=True, color="FFFFFF", size=11)
            hc.fill = fill(mid)
            hc.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
            hc.border = Border(bottom=Side(style="medium", color=dark))
        ws.row_dimensions[hr].height = 26

        # --- dữ liệu ---
        for ri, row in enumerate(rows, hr + 1):
            first = row[0] if row else None
            if isinstance(first, str) and first.startswith("—") and (len(row) < 2 or row[1] in ("", None)):
                ws.merge_cells(start_row=ri, start_column=1, end_row=ri, end_column=ncol)
                sc = ws.cell(ri, 1, first.strip("— ").strip())
                sc.font = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
                sc.alignment = Alignment(horizontal="left", vertical="center", indent=1)
                for ci in range(1, ncol + 1):
                    ws.cell(ri, ci).fill = fill(dark)
                ws.row_dimensions[ri].height = 22
                continue
            zebra = fill("F4F8FC") if (ri - hr) % 2 == 0 else None
            for ci, v in enumerate(row, 1):
                idx = ci - 1
                cell = ws.cell(ri, ci)
                numeric = isinstance(v, (int, float)) and not isinstance(v, bool)
                if numeric and idx in money:
                    cell.value = v
                    cell.number_format = "#,##0"
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                    if idx in signed:
                        cell.font = Font(name="Calibri", size=11, bold=True, color="1E8449" if v >= 0 else "C0392B")
                    else:
                        cell.font = Font(name="Calibri", size=11)
                elif numeric:
                    cell.value = v
                    cell.number_format = "0"
                    cell.font = Font(name="Calibri", size=11)
                    cell.alignment = Alignment(horizontal="center", vertical="center")
                else:
                    s = "" if v is None else str(v)
                    cell.value = s
                    cell.data_type = "s"          # luôn là chuỗi -> không bị Excel hiểu thành công thức
                    cell.font = Font(name="Calibri", size=11)
                    cell.alignment = Alignment(vertical="center", wrap_text=len(s) > 42)
                    if status_col is not None and idx == status_col and s in _XL_STATUS:
                        bg, fg = _XL_STATUS[s]
                        cell.fill = fill(bg)
                        cell.font = Font(name="Calibri", size=11, bold=True, color=fg)
                        cell.alignment = Alignment(horizontal="center", vertical="center")
                if idx in right:
                    cell.alignment = Alignment(horizontal="right", vertical="center", wrap_text=True)
                if zebra is not None and cell.fill.fgColor.rgb in (None, "00000000"):
                    cell.fill = zebra
                cell.border = Border(bottom=hair)
        last = hr + len(rows)

        # --- dòng tổng ---
        if sh.get("sum_cols") and rows:
            tr = last + 1
            tl = ws.cell(tr, 1, "TỔNG")
            tl.font = Font(name="Calibri", bold=True, size=11)
            for ci in range(1, ncol + 1):
                ws.cell(tr, ci).fill = fill("FFF2CC")
                ws.cell(tr, ci).border = Border(top=Side(style="thin", color=dark))
            for ci in sh["sum_cols"]:
                total = sum(int(rw[ci] or 0) for rw in rows if isinstance(rw[ci], (int, float)))
                tc = ws.cell(tr, ci + 1, total)
                tc.number_format = "#,##0"
                tc.font = Font(name="Calibri", bold=True, size=11)
                tc.alignment = Alignment(horizontal="right")

        ws.freeze_panes = f"A{hr + 1}"
        if rows and not sh.get("no_filter") and ncol >= 3:
            ws.auto_filter.ref = f"A{hr}:{get_column_letter(ncol)}{last}"

        for ci, h in enumerate(headers, 1):
            vals = [len(str(h))] + [len(str(rw[ci - 1])) for rw in rows[:300] if ci - 1 < len(rw) and rw[ci - 1] is not None]
            ws.column_dimensions[get_column_letter(ci)].width = min(46, max(13, max(vals) + 3))

        # --- biểu đồ ---
        for ch in sh.get("charts", []):
            if not rows or len(rows) > 400:
                continue
            is_bar = ch.get("kind", "bar") == "bar"
            chart = BarChart() if is_bar else LineChart()
            if is_bar:
                chart.type = "col"
                chart.grouping = "clustered"
            chart.title = ch["title"]
            chart.height = ch.get("h", 8.5)
            chart.width = ch.get("w", 21)
            for vc in ch["vals"]:
                chart.add_data(Reference(ws, min_col=vc + 1, min_row=hr, max_row=last), titles_from_data=True)
            chart.set_categories(Reference(ws, min_col=ch.get("cat", 0) + 1, min_row=hr + 1, max_row=last))
            ws.add_chart(chart, f"{get_column_letter(ncol + 2)}{hr + ch.get('row_offset', 0)}")

        ws.page_setup.orientation = "landscape"
        ws.page_setup.fitToWidth = 1
        ws.page_setup.fitToHeight = 0
        ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
        ws.print_title_rows = f"{hr}:{hr}"
        ws.oddFooter.center.text = "Trang &P / &N"
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
                {"name": "Tổng quan", "headers": ["Chỉ tiêu", "Giá trị"], "rows": kv_rows, "money_cols": [1], "sum_cols": [],
                 "right_cols": [1], "no_filter": True,
                 "kpis": [("Số dư hiện tại", p["balance"] if p else 0, "money"), ("Tổng nạp (kỳ)", data["nap"]["extra"]["ok"], "money"),
                          ("Tổng rút (kỳ)", data["rut"]["extra"]["ok"], "money"), ("Tổng cược (kỳ)", cx["bets"], "money"),
                          ("Thắng / hoàn (kỳ)", cx["wins"], "money"), ("Kết quả chơi (kỳ)", cx["net"], "signed")]},
                {"name": "Biến động số dư", **data["his"]},
                {"name": "Nạp", **data["nap"]}, {"name": "Rút", **data["rut"]},
                {"name": "Cược & Thắng", **data["cuoc"]}, {"name": "Code đã nhập", **data["code"]},
                {"name": "Gift đã mua", **data["mua"]}, {"name": "Gift đã dùng", **data["gift"]},
            ]
            total_rows = sum(len(s["rows"]) for s in sheets[1:])
        else:
            data = await asyncio.to_thread(_rp_collect, kind, uid, start, end)
            sheets = [{"name": {"his": "Biến động số dư", "nap": "Nạp", "rut": "Rút", "cuoc": "Cược & Thắng",
                                "code": "Code đã nhập", "mua": "Gift đã mua", "gift": "Gift đã dùng"}.get(kind, "Báo cáo"), **data,
                       "kpis": _rp_kpis(kind, data)}]
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
lsrut_report_cmd = _rp_make_view_cmd("rut", "lsrutky", "lịch sử rút theo kỳ")
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
    if ctx.user_data.pop("adm_flow", None):
        await update.effective_message.reply_text("✅ Đã huỷ thao tác admin đang nhập dở.")

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



# ============================================================
# BỔ SUNG QUẢN TRỊ: KHÓA HOÀN NGÀY/TUẦN, RESET SỐ DƯ, XUẤT FULL HỆ THỐNG
# ============================================================
@admin_only
async def camhoan_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        target = int(ctx.args[0])
        period = (ctx.args[1] if len(ctx.args) > 1 else "").lower()
        if period not in ("ngay", "tuan", "all"):
            raise ValueError
    except (IndexError, ValueError):
        return await update.effective_message.reply_text(
            "Cú pháp: <code>/camhoan ID ngay|tuan|all</code>\n"
            "Ví dụ: <code>/camhoan 123456 ngay</code>",
            parse_mode=ParseMode.HTML)
    if not (query("SELECT 1 FROM users WHERE user_id=%s", (target,)) or []):
        return await update.effective_message.reply_text("Không tìm thấy người dùng.")
    features = ["hoan_ngay", "hoan_tuan"] if period == "all" else [f"hoan_{period}"]
    for feature in features:
        query("INSERT INTO banned_features(user_id,feature) VALUES(%s,%s) ON CONFLICT DO NOTHING",
              (target, feature))
    _REWARD_BAN_CACHE.pop(target, None)
    await update.effective_message.reply_text(
        f'🚫 Đã khóa nhận hoàn trả <b>{html.escape(period.upper())}</b> cho ID <code>{target}</code>.\n'
        'Các khoản bị khóa sẽ không được nhận qua nút nhận thưởng.',
        parse_mode=ParseMode.HTML)

@admin_only
async def mohoan_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        target = int(ctx.args[0])
        period = (ctx.args[1] if len(ctx.args) > 1 else "all").lower()
        if period not in ("ngay", "tuan", "all"):
            raise ValueError
    except (IndexError, ValueError):
        return await update.effective_message.reply_text(
            "Cú pháp: <code>/mohoan ID ngay|tuan|all</code>",
            parse_mode=ParseMode.HTML)
    if period == "all":
        query("DELETE FROM banned_features WHERE user_id=%s AND feature IN ('hoan_ngay','hoan_tuan')", (target,))
    else:
        query("DELETE FROM banned_features WHERE user_id=%s AND feature=%s", (target, f"hoan_{period}"))
    _REWARD_BAN_CACHE.pop(target, None)
    await update.effective_message.reply_text(
        f'✅ Đã mở quyền nhận hoàn trả <b>{html.escape(period.upper())}</b> cho ID <code>{target}</code>.',
        parse_mode=ParseMode.HTML)

@admin_only
async def resethoan_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        target = int(ctx.args[0])
        period = (ctx.args[1] if len(ctx.args) > 1 else "all").lower()
        if period not in ("ngay", "tuan", "all"):
            raise ValueError
    except (IndexError, ValueError):
        return await update.effective_message.reply_text(
            "Cú pháp: <code>/resethoan ID ngay|tuan|all</code> — xóa số thưởng hoàn trả đang chờ nhận về 0.",
            parse_mode=ParseMode.HTML)
    if not (query("SELECT 1 FROM users WHERE user_id=%s", (target,)) or []):
        return await update.effective_message.reply_text("Không tìm thấy người dùng.")
    if period == "all":
        old_rows = query("SELECT amount FROM rewards WHERE user_id=%s AND claimed=0 AND amount>0",
                         (target,)) or []
        query("UPDATE rewards SET amount=0, claimed=1, claimed_at=%s "
              "WHERE user_id=%s AND claimed=0 AND amount>0",
              (get_vietnam_datetime_db(), target))
    else:
        types = ["cuoc_ngay", "thua_ngay"] if period == "ngay" else ["cuoc_tuan", "thua_tuan"]
        old_rows = query("SELECT amount FROM rewards WHERE user_id=%s AND claimed=0 AND amount>0 AND rtype = ANY(%s)",
                         (target, types)) or []
        query("UPDATE rewards SET amount=0, claimed=1, claimed_at=%s "
              "WHERE user_id=%s AND claimed=0 AND amount>0 AND rtype = ANY(%s)",
              (get_vietnam_datetime_db(), target, types))
    total = sum(int(r[0] or 0) for r in old_rows)
    await update.effective_message.reply_text(
        f"✅ Đã reset thưởng hoàn trả <b>{html.escape(period.upper())}</b> của ID <code>{target}</code> về 0.\n"
        f"Số thưởng chờ nhận đã xóa: <code>{fmt_money(total)}đ</code>. Lịch sử nạp/rút không bị ảnh hưởng.",
        parse_mode=ParseMode.HTML)

@admin_only
async def resetuser_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        target = int(ctx.args[0])
    except (IndexError, ValueError):
        return await update.effective_message.reply_text(
            "Cú pháp: <code>/resetuser ID</code> — đặt số dư user về 0 (cần xác nhận).",
            parse_mode=ParseMode.HTML)
    if target in ADMIN_IDS:
        return await update.effective_message.reply_text("Không thể reset số dư tài khoản admin.")
    row = query("SELECT balance FROM users WHERE user_id=%s", (target,)) or []
    if not row:
        return await update.effective_message.reply_text("Không tìm thấy người dùng.")
    old_balance = int(row[0][0] or 0)
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("⚠️ Xác nhận đặt về 0", callback_data=f"resetbal_yes_{target}"),
        InlineKeyboardButton("Hủy", callback_data=f"resetbal_no_{target}")
    ]])
    await update.effective_message.reply_text(
        f"⚠️ <b>XÁC NHẬN RESET SỐ DƯ</b>\nID: <code>{target}</code>\n"
        f"Số dư hiện tại: <code>{fmt_money(old_balance)}đ</code>\n"
        "Lịch sử giao dịch sẽ được giữ nguyên. Hành động này không thể tự hoàn tác.",
        reply_markup=kb, parse_mode=ParseMode.HTML)

async def reset_balance_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id not in ADMIN_IDS or is_admin_banned(q.from_user.id):
        return await q.answer("Bạn không có quyền.", show_alert=True)
    parts = (q.data or "").split("_")
    if len(parts) != 3:
        return await q.answer()
    action, target_s = parts[1], parts[2]
    try:
        target = int(target_s)
    except ValueError:
        return await q.answer("ID không hợp lệ.", show_alert=True)
    if action == "no":
        await q.answer("Đã hủy.")
        return await q.edit_message_text("❎ Đã hủy reset số dư.")
    if action != "yes" or target in ADMIN_IDS:
        return await q.answer("Thao tác không hợp lệ.", show_alert=True)
    row = query("SELECT balance FROM users WHERE user_id=%s", (target,)) or []
    if not row:
        return await q.answer("Không tìm thấy user.", show_alert=True)
    old_balance = int(row[0][0] or 0)
    if old_balance > 0:
        add_money(target, -old_balance, "Admin reset số dư về 0")
    elif old_balance < 0:
        add_money(target, -old_balance, "Admin reset số dư về 0")
    await q.answer("Đã reset số dư.")
    await q.edit_message_text(
        f"✅ Đã đặt số dư ID <code>{target}</code> về <code>0đ</code>.\n"
        f"💳 Số dư trước: <code>{fmt_money(old_balance)}đ</code>\n"
        f"💰 Số dư sau: <code>{fmt_money(0)}đ</code>\n"
        f"Lịch sử vẫn được giữ nguyên.",
        parse_mode=ParseMode.HTML)

@admin_only
async def xuatnapall_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await _system_export(update, "nap")

@admin_only
async def xuatrutall_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await _system_export(update, "rut")

@admin_only
async def xuathethong_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await _system_export(update, "all")

@admin_only
async def lsnaptatca_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    rows = query("SELECT id,user_id,amount,status,time FROM deposit_history ORDER BY id DESC LIMIT 50") or []
    if not rows:
        return await update.effective_message.reply_text("Chưa có lịch sử nạp.")
    text = "📥 <b>50 LỊCH SỬ NẠP MỚI NHẤT</b>\n\n" + "\n".join(
        f"#{r[0]} · ID <code>{r[1]}</code> · <code>{fmt_money(int(r[2] or 0))}đ</code> · {html.escape(str(r[3] or ''))} · {html.escape(str(r[4] or ''))}"
        for r in rows)
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)

_BANK_CODE_ALIASES = {
    "MB": "MB", "MBBANK": "MB", "VIETCOMBANK": "VCB", "VCB": "VCB",
    "TECHCOMBANK": "TCB", "TCB": "TCB", "BIDV": "BIDV",
    "VIETINBANK": "CTG", "CTG": "CTG", "ACB": "ACB", "SACOMBANK": "STB",
    "STB": "STB", "VPBANK": "VPB", "VPB": "VPB", "TPBANK": "TPB",
    "TPB": "TPB", "AGRIBANK": "AGRIBANK", "VIB": "VIB", "SHB": "SHB",
    "MSB": "MSB", "LPBANK": "LPB", "OCB": "OCB", "HDBANK": "HDB"
}

@admin_only
async def lsrut_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """/lsrut [ID] [số_lượng] - lịch sử rút kèm đầy đủ thông tin người rút và mã QR."""
    msg = update.effective_message
    target, limit = None, 10
    for a in (ctx.args or []):
        a = a.strip()
        if not a.isdigit():
            continue
        if len(a) <= 3 and int(a) <= 50:
            limit = max(1, int(a))
        else:
            target = int(a)
    sql = ("SELECT w.id, w.user_id, w.amount, w.status, w.time, w.request_code, w.admin_id, w.admin_note, "
           "COALESCE(w.method,''), COALESCE(w.bank,''), COALESCE(w.stk,''), COALESCE(w.acc_name,''), w.qr_file_id, w.memo, "
           "u.bank, u.stk, u.name FROM withdraw_history w LEFT JOIN users u ON u.user_id=w.user_id ")
    if target:
        rows = query(sql + "WHERE w.user_id=%s ORDER BY w.id DESC LIMIT %s", (target, limit)) or []
    else:
        rows = query(sql + "ORDER BY w.id DESC LIMIT %s", (limit,)) or []
    if not rows:
        return await msg.reply_text("Chưa có lịch sử rút.")
    status_txt = {"pending": "⏳ Chờ duyệt", "success": "✅ Đã duyệt", "rejected": "❌ Từ chối"}
    for (wid, uid_, amount, status, time_, code, admin_id, admin_note, method, bank, stk, acc_name,
         qr_fid, memo, u_bank, u_stk, u_name) in rows:
        # Bản ghi cũ chưa lưu snapshot -> dùng thông tin hiện tại của user.
        legacy = not (stk or bank)
        if legacy:
            bank, stk, acc_name, method = (u_bank or ''), (u_stk or ''), (u_name or ''), (method or 'BANKING')
        method = (method or 'BANKING').upper()
        amount = int(amount or 0)
        lines = [
            f'{ce("🧾")} <b>LỊCH SỬ RÚT #{wid}</b>',
            '━━━━━━━━━━━━━━━━━━━━━',
            f'{ce("🔖")} <b>Mã yêu cầu:</b> <code>{html.escape(str(code or "-"))}</code>',
            f'{ce("👥")} <b>ID người rút:</b> <code>{uid_}</code>',
            f'{ce("💰")} <b>Số tiền:</b> <code>{fmt_money(amount)}đ</code>',
            f'{ce("💳")} <b>Phương thức:</b> <code>{html.escape(method)}</code>',
            f'{ce("🏦")} <b>Ngân hàng:</b> <code>{html.escape(bank or "-")}</code>',
            f'{ce("🔢")} <b>STK/SĐT:</b> <code>{html.escape(stk or "-")}</code>',
            f'{ce("👤")} <b>Chủ TK:</b> <code>{html.escape(acc_name or "-")}</code>',
        ]
        if memo:
            lines.append(f'{ce("📝")} <b>Nội dung CK:</b> <code>{html.escape(memo)}</code>')
        lines += [
            f'{ce("📌")} <b>Trạng thái:</b> {status_txt.get(status, html.escape(str(status)))}',
            f'{ce("⏰")} <b>Thời gian:</b> <code>{html.escape(str(time_ or "-"))}</code>',
        ]
        if admin_id:
            lines.append(f'{ce("🛡")} <b>Admin xử lý:</b> <code>{admin_id}</code>')
        if admin_note:
            lines.append(f'{ce("🗒")} <b>Ghi chú:</b> {html.escape(str(admin_note))}')
        if legacy:
            lines.append('<i>(Bản ghi cũ: thông tin lấy từ tài khoản liên kết hiện tại)</i>')
        text = "\n".join(lines)
        kb = None
        if status == "pending":
            kb = InlineKeyboardMarkup([[
                btn("Duyệt", "✅", callback_data=f"ok_{uid_}_{amount}"),
                btn("Từ chối", "❌", callback_data=f"no_{uid_}_{amount}")]])
        sent = False
        try:
            if method == "BANKING" and stk:
                key = re.sub(r"[^A-Z0-9]", "", str(bank).upper())
                code_b = _BANK_CODE_ALIASES.get(key, key)
                qr_bank = _BANK_BIN.get(code_b) or code_b
                qr = make_local_qr(amount=amount, content=memo or str(code or ""), bank_id=qr_bank, account_no=stk)
                await msg.reply_photo(photo=qr, caption=text, reply_markup=kb, parse_mode=ParseMode.HTML)
                sent = True
            elif qr_fid:
                await msg.reply_photo(photo=qr_fid, caption=text, reply_markup=kb, parse_mode=ParseMode.HTML)
                sent = True
        except Exception as e:
            print(f"lsrut gửi QR lỗi (#{wid}): {e}")
        if not sent:
            await msg.reply_text(text + "\n\n⚠️ Không có QR cho giao dịch này.", reply_markup=kb, parse_mode=ParseMode.HTML)

@admin_only
async def lsruttatca_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    rows = query("SELECT id,user_id,amount,status,time FROM withdraw_history ORDER BY id DESC LIMIT 50") or []
    if not rows:
        return await update.effective_message.reply_text("Chưa có lịch sử rút.")
    text = "📤 <b>50 LỊCH SỬ RÚT MỚI NHẤT</b>\n\n" + "\n".join(
        f"#{r[0]} · ID <code>{r[1]}</code> · <code>{fmt_money(int(r[2] or 0))}đ</code> · {html.escape(str(r[3] or ''))} · {html.escape(str(r[4] or ''))}"
        for r in rows)
    await update.effective_message.reply_text(text, parse_mode=ParseMode.HTML)


def _rp_kpis(kind, data):
    x = data.get("extra", {}) or {}
    n = len(data.get("rows", []))
    if kind == "his":
        return [("Tổng tiền vào", x.get("in", 0), "money"), ("Tổng tiền ra", x.get("out", 0), "money"),
                ("Chênh lệch", x.get("in", 0) - x.get("out", 0), "signed"), ("Số dòng", n, "int")]
    if kind in ("nap", "rut"):
        return [("Thành công", x.get("ok", 0), "money"), ("Số lần thành công", x.get("ok_n", 0), "int"),
                ("Đang chờ duyệt", x.get("pending", 0), "money"), ("Tổng số dòng", n, "int")]
    if kind == "cuoc":
        return [("Tổng cược", x.get("bets", 0), "money"), ("Thắng / hoàn", x.get("wins", 0), "money"),
                ("Kết quả chơi", x.get("net", 0), "signed"), ("Số lượt", x.get("n_bet", 0) + x.get("n_win", 0), "int")]
    if kind == "code":
        return [("Tổng giá trị", x.get("sum", 0), "money"), ("Số code", n, "int")]
    return [("Tổng giá trị", x.get("sum", 0), "money"), ("Đã dùng", x.get("used_n", 0), "int"), ("Số code", n, "int")]

# ---------- XUẤT THỐNG KÊ TOÀN HỆ THỐNG ----------
def _stat_bet_rows(start=None, end=None, ignore_epoch=False):
    ed = "1970-01-01" if ignore_epoch else (get_setting("stats_epoch_day", "1970-01-01") or "1970-01-01")
    if ignore_epoch:
        sql = "SELECT b.user_id, b.day, b.bet, b.win FROM bet_daily b WHERE b.day>=%s"
    else:
        sql = ("SELECT b.user_id, b.day, GREATEST(b.bet-COALESCE(s.bet,0),0), GREATEST(b.win-COALESCE(s.win,0),0) "
               "FROM bet_daily b LEFT JOIN stats_bet_base s ON s.user_id=b.user_id AND s.day=b.day WHERE b.day>=%s")
    args = [ed]
    if start:
        sql += " AND b.day>=%s"
        args.append(start)
    if end:
        sql += " AND b.day<=%s"
        args.append(end)
    return query(sql, tuple(args)) or []

def _xs_dep_sheet(raw):
    rows = []
    ok = ok_n = pend = 0
    for r in raw:
        label = _rp_status(r[3])
        amt = int(r[2] or 0)
        rows.append((r[0], r[1], amt, label, r[4] or "", r[5] or "", _rp_admin_label(r[6])))
        if label == "Thành công":
            ok += amt
            ok_n += 1
        elif label == "Chờ duyệt":
            pend += amt
    rows.reverse()
    return {"name": "Lịch sử nạp", "headers": ["Mã GD", "User ID", "Số tiền (đ)", "Trạng thái", "Thời gian", "Mã giao dịch", "Xử lý bởi"],
            "rows": rows, "money_cols": [2], "status_col": 3,
            "kpis": [("Tổng nạp thành công", ok, "money"), ("Số lệnh thành công", ok_n, "int"),
                     ("Đang chờ duyệt", pend, "money"), ("Tổng số lệnh", len(rows), "int")]}

def _xs_wd_sheet(raw):
    rows = []
    ok = ok_n = pend = 0
    for r in raw:
        label = _rp_status(r[3])
        amt = int(r[2] or 0)
        rows.append((r[0], r[1], amt, label, r[4] or "", _rp_admin_label(r[5]) if r[5] else "—", r[6] or ""))
        if label == "Thành công":
            ok += amt
            ok_n += 1
        elif label == "Chờ duyệt":
            pend += amt
    rows.reverse()
    return {"name": "Lịch sử rút", "headers": ["Mã GD", "User ID", "Số tiền (đ)", "Trạng thái", "Thời gian", "Admin xử lý", "Ghi chú"],
            "rows": rows, "money_cols": [2], "status_col": 3,
            "kpis": [("Tổng rút thành công", ok, "money"), ("Số lệnh thành công", ok_n, "int"),
                     ("Đang chờ duyệt", pend, "money"), ("Tổng số lệnh", len(rows), "int")]}

def _stat_collect_sync(start, end, ignore_epoch=False):
    ep_dep = 0 if ignore_epoch else _ep_int("stats_epoch_dep")
    ep_wd = 0 if ignore_epoch else _ep_int("stats_epoch_wd")
    deps = [r for r in (query("SELECT id,user_id,amount,status,time,ref_code,admin_id FROM deposit_history "
                              "WHERE id>%s ORDER BY id ASC LIMIT 200000", (ep_dep,)) or [])
            if _rp_in_range(r[4], start, end)]
    wds = [r for r in (query("SELECT id,user_id,amount,status,time,admin_id,admin_note FROM withdraw_history "
                             "WHERE id>%s ORDER BY id ASC LIMIT 200000", (ep_wd,)) or [])
           if _rp_in_range(r[4], start, end)]
    bet_rows = _stat_bet_rows(start, end, ignore_epoch)

    per_day = {}
    def slot(d):
        return per_day.setdefault(d, [0, 0, 0, 0, 0, 0])   # nạp_n, nạp, rút_n, rút, cược, thắng

    dep_ok = dep_n = dep_pend = wd_ok = wd_n = wd_pend = 0
    dep_users, wd_users = {}, set()
    for r in deps:
        label, amt = _rp_status(r[3]), int(r[2] or 0)
        if label == "Thành công":
            dep_ok += amt
            dep_n += 1
            u = dep_users.setdefault(r[1], [0, 0, ""])
            u[0] += amt
            u[1] += 1
            u[2] = r[4] or ""
            d = _rp_date(r[4])
            if d:
                s = slot(d)
                s[0] += 1
                s[1] += amt
        elif label == "Chờ duyệt":
            dep_pend += amt
    for r in wds:
        label, amt = _rp_status(r[3]), int(r[2] or 0)
        if label == "Thành công":
            wd_ok += amt
            wd_n += 1
            wd_users.add(r[1])
            d = _rp_date(r[4])
            if d:
                s = slot(d)
                s[2] += 1
                s[3] += amt
        elif label == "Chờ duyệt":
            wd_pend += amt
    bet_total = win_total = 0
    bet_users = {}
    for uid_, day, b, w in bet_rows:
        b, w = int(b or 0), int(w or 0)
        d = day.date() if isinstance(day, datetime) else day
        s = slot(d)
        s[4] += b
        s[5] += w
        bu = bet_users.setdefault(uid_, [0, 0])
        bu[0] += b
        bu[1] += w
        bet_total += b
        win_total += w

    # --- Theo ngày ---
    days = sorted(per_day)
    if start and end and (end - start).days <= 92:
        days = [start + timedelta(days=i) for i in range((end - start).days + 1)]
    day_rows = []
    for d in days:
        s = per_day.get(d, [0, 0, 0, 0, 0, 0])
        day_rows.append((d.strftime("%d/%m/%Y"), s[0], s[1], s[2], s[3], s[1] - s[3], s[4], s[5], s[4] - s[5]))
    day_sheet = {
        "name": "Theo ngày",
        "headers": ["Ngày", "Số lệnh nạp", "Nạp (đ)", "Số lệnh rút", "Rút (đ)", "Nạp − Rút (đ)", "Tổng cược (đ)", "Trả thưởng (đ)", "Lãi/lỗ game (đ)"],
        "rows": day_rows, "money_cols": [2, 4, 5, 6, 7, 8], "signed_cols": [5, 8], "sum_cols": [1, 2, 3, 4, 5, 6, 7, 8],
        "charts": [{"title": "Nạp / Rút theo ngày", "kind": "bar", "cat": 0, "vals": [2, 4]},
                   {"title": "Lãi / lỗ game theo ngày", "kind": "line", "cat": 0, "vals": [8], "row_offset": 19}],
    }

    # --- Top ---
    all_ids = set(dep_users) | set(bet_users)
    top_dep = sorted(dep_users.items(), key=lambda kv: kv[1][0], reverse=True)[:20]
    top_bet = sorted(bet_users.items(), key=lambda kv: kv[1][0], reverse=True)[:20]
    uinfo = {}
    ids = list({i for i, _ in top_dep} | {i for i, _ in top_bet})
    if ids:
        for r in query("SELECT user_id, name, bank, stk FROM users WHERE user_id = ANY(%s)", (ids,)) or []:
            uinfo[r[0]] = r
    def owner(i):
        r = uinfo.get(i)
        return (r[1] or "—") if r else "—"
    top_dep_sheet = {
        "name": "Top nạp", "headers": ["Hạng", "User ID", "Chủ TK", "Tổng nạp (đ)", "Số lần nạp", "Lần nạp gần nhất"],
        "rows": [(i + 1, uid_, owner(uid_), v[0], v[1], v[2]) for i, (uid_, v) in enumerate(top_dep)],
        "money_cols": [3]}
    top_bet_sheet = {
        "name": "Top cược", "headers": ["Hạng", "User ID", "Chủ TK", "Tổng cược (đ)", "Tiền thắng (đ)", "Kết quả người chơi (đ)"],
        "rows": [(i + 1, uid_, owner(uid_), v[0], v[1], v[1] - v[0]) for i, (uid_, v) in enumerate(top_bet)],
        "money_cols": [3, 4, 5], "signed_cols": [5]}
    bal_rows = query("SELECT user_id, balance, COALESCE(total_bet,0), name, bank FROM users ORDER BY balance DESC LIMIT 20") or []
    top_bal_sheet = {
        "name": "Top số dư", "headers": ["Hạng", "User ID", "Số dư (đ)", "Tổng cược (đ)", "Chủ TK", "Ngân hàng"],
        "rows": [(i + 1, r[0], int(r[1] or 0), int(r[2] or 0), r[3] or "—", r[4] or "—") for i, r in enumerate(bal_rows)],
        "money_cols": [2, 3]}

    tot = query("SELECT COUNT(*), COALESCE(SUM(balance),0), COUNT(*) FILTER (WHERE balance>0) FROM users") or [(0, 0, 0)]
    pend_w = query("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM withdraw_history WHERE status='pending'") or [(0, 0)]
    rtp = (win_total * 100.0 / bet_total) if bet_total else 0
    net_dw = dep_ok - wd_ok
    def m(n):
        return f"{fmt_money(int(n))} đ"
    ov_rows = [
        ("— KẾT QUẢ KỲ BÁO CÁO —", ""),
        ("Tổng nạp thành công", m(dep_ok)), ("Số lệnh nạp thành công", str(dep_n)), ("Số người đã nạp", str(len(dep_users))),
        ("Nạp trung bình / lệnh", m(dep_ok / dep_n) if dep_n else "0 đ"),
        ("Tổng rút thành công", m(wd_ok)), ("Số lệnh rút thành công", str(wd_n)), ("Số người đã rút", str(len(wd_users))),
        ("Chênh lệch nạp − rút", ("+" if net_dw >= 0 else "−") + m(abs(net_dw))),
        ("— TRÒ CHƠI —", ""),
        ("Tổng tiền cược", m(bet_total)), ("Tổng tiền trả thưởng", m(win_total)),
        ("Lãi / lỗ game (nhà cái)", ("+" if bet_total - win_total >= 0 else "−") + m(abs(bet_total - win_total))),
        ("Tỉ lệ hoàn trả (RTP)", f"{rtp:.2f}%".replace(".", ",")),
        ("Số người chơi", str(len(bet_users))),
        ("Cược trung bình / người", m(bet_total / len(bet_users)) if bet_users else "0 đ"),
        ("— HIỆN TẠI —", ""),
        ("Tổng số người dùng", str(int(tot[0][0] or 0))), ("Người dùng còn số dư", str(int(tot[0][2] or 0))),
        ("Tổng số dư người dùng", m(tot[0][1] or 0)),
        ("Rút đang chờ duyệt", f"{int(pend_w[0][0] or 0)} lệnh · {m(pend_w[0][1] or 0)}"),
        ("Nạp đang chờ duyệt", m(dep_pend)),
        ("Hũ Jackpot hiện tại", m(get_jackpot())),
    ]
    if not ignore_epoch and (get_setting("stats_epoch_at", "") or ""):
        ov_rows.append(("Thống kê tính từ lúc reset", get_setting("stats_epoch_at", "")))
    overview = {
        "name": "Tổng quan", "headers": ["Chỉ tiêu", "Giá trị"], "rows": ov_rows, "right_cols": [1], "no_filter": True,
        "kpis": [("Tổng nạp", dep_ok, "money"), ("Tổng rút", wd_ok, "money"), ("Nạp − Rút", net_dw, "signed"),
                 ("Tổng cược", bet_total, "money"), ("Trả thưởng", win_total, "money"),
                 ("Lãi / lỗ game", bet_total - win_total, "signed")],
    }
    sheets = [overview, day_sheet, top_dep_sheet, top_bet_sheet, top_bal_sheet, _xs_dep_sheet(deps), _xs_wd_sheet(wds)]
    summary = {"dep": dep_ok, "dep_n": dep_n, "wd": wd_ok, "wd_n": wd_n, "bet": bet_total, "win": win_total,
               "days": len(day_rows), "rows": len(deps) + len(wds)}
    return sheets, summary

@admin_only
async def xuatthongke_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    raw = " ".join(ctx.args or []).strip()
    token = _rp_token_from_text(raw) if raw else "n30"
    if token is None:
        return await msg.reply_text(
            f'{ce("❌")} Kỳ không hợp lệ.\n'
            f'Cú pháp: <code>/xuatthongke [kỳ]</code>\n'
            f'Ví dụ: <code>/xuatthongke 7</code> · <code>/xuatthongke all</code> · '
            f'<code>/xuatthongke 01/10/2026 - 29/10/2026</code>',
            parse_mode=ParseMode.HTML)
    start, end, label = _rp_range(token)
    status = await msg.reply_text(f'{ce("⌛")} Đang tổng hợp thống kê hệ thống, vui lòng chờ…', parse_mode=ParseMode.HTML)
    try:
        sheets, sm = await asyncio.to_thread(_stat_collect_sync, start, end, False)
        head, sub = "BÁO CÁO THỐNG KÊ HỆ THỐNG", f"Kỳ báo cáo: {label}"
        tag = _rp_tag(token)
        stamp = get_vietnam_time().strftime("%Y%m%d_%H%M")
        try:
            bio = await asyncio.to_thread(_rp_build_xlsx, head, sub, sheets)
            fname, note = f"thongke_{tag}_{stamp}.xlsx", ""
        except ImportError:
            bio = await asyncio.to_thread(_rp_build_csv, head, sub, sheets)
            fname, note = f"thongke_{tag}_{stamp}.csv", "\n⚠️ Server chưa cài <code>openpyxl</code> nên xuất CSV."
        bio.seek(0)
        await msg.reply_document(
            document=bio, filename=fname,
            caption=(f'{ce("📊")} <b>BÁO CÁO THỐNG KÊ HỆ THỐNG</b>\n'
                     f'{ce("🗓")} {html.escape(label)}\n'
                     f'{ce("📥")} Nạp: <b>{fmt_money(sm["dep"])}đ</b> ({sm["dep_n"]} lệnh)\n'
                     f'{ce("📤")} Rút: <b>{fmt_money(sm["wd"])}đ</b> ({sm["wd_n"]} lệnh)\n'
                     f'{ce("🎯")} Cược: <b>{fmt_money(sm["bet"])}đ</b> · Trả thưởng: <b>{fmt_money(sm["win"])}đ</b>\n'
                     f'{ce("💰")} Lãi/lỗ game: <b>{_signed_money(sm["bet"] - sm["win"])}</b>' + note),
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

async def _system_export(update: Update, kind: str):
    msg = update.effective_message
    nowtag = get_vietnam_time().strftime("%Y%m%d_%H%M%S")
    status = await msg.reply_text("⏳ Đang tổng hợp toàn bộ lịch sử, vui lòng chờ…")
    try:
        sheets = []
        if kind == "nap":
            raw = query("SELECT id,user_id,amount,status,time,ref_code,admin_id FROM deposit_history ORDER BY id ASC") or []
            sheets.append(_xs_dep_sheet(raw))
            title = "TOÀN BỘ LỊCH SỬ NẠP HỆ THỐNG"
        elif kind == "rut":
            raw = query("SELECT id,user_id,amount,status,time,admin_id,admin_note FROM withdraw_history ORDER BY id ASC") or []
            sheets.append(_xs_wd_sheet(raw))
            title = "TOÀN BỘ LỊCH SỬ RÚT HỆ THỐNG"
        else:
            sheets, _ = await asyncio.to_thread(_stat_collect_sync, None, None, True)
            raw = query("SELECT user_id,balance,bank,stk,name,refs,COALESCE(total_bet,0) FROM users ORDER BY user_id ASC") or []
            rows = [(r[0], int(r[1] or 0), r[2] or "", r[3] or "", r[4] or "", int(r[5] or 0), int(r[6] or 0)) for r in raw]
            sheets.append({"name": "Danh sách user", "headers": ["User ID", "Số dư (đ)", "Ngân hàng", "Số tài khoản", "Chủ tài khoản", "Số người mời", "Tổng cược (đ)"],
                           "rows": rows, "money_cols": [1, 6],
                           "kpis": [("Tổng người dùng", len(rows), "int"), ("Tổng số dư", sum(r[1] for r in rows), "money"),
                                    ("Tổng cược", sum(r[6] for r in rows), "money")]})
            raw = query("SELECT id,user_id,amount,note,time,bal_before,bal_after FROM history ORDER BY id DESC LIMIT 300000") or []
            _run = {int(r[0]): int(r[1] or 0) for r in (query("SELECT user_id, balance FROM users") or [])}
            rows = []
            for r in raw:
                _amt = int(r[2] or 0)
                if r[5] is not None and r[6] is not None:
                    _bb, _ba = int(r[5]), int(r[6])
                else:
                    _ba = _run.get(int(r[1]), 0); _bb = _ba - _amt
                _run[int(r[1])] = _bb
                rows.append((r[0], r[1], _amt, _bb, _ba, r[3] or "", r[4] or ""))
            sheets.append({"name": "Biến động số dư", "headers": ["Mã", "User ID", "Biến động (đ)", "Số dư trước (đ)", "Số dư sau (đ)", "Nội dung", "Thời gian"],
                           "rows": rows, "money_cols": [2, 3, 4], "signed_col": 2})
            title = "BÁO CÁO TOÀN HỆ THỐNG (TOÀN BỘ THỜI GIAN)"
        total = sum(len(sh["rows"]) for sh in sheets)
        try:
            bio = await asyncio.to_thread(_rp_build_xlsx, title, "Báo cáo admin — dữ liệu toàn hệ thống", sheets)
            fname = f"{kind}_toan_he_thong_{nowtag}.xlsx"
        except ImportError:
            bio = await asyncio.to_thread(_rp_build_csv, title, "Báo cáo admin — dữ liệu toàn hệ thống", sheets)
            fname = f"{kind}_toan_he_thong_{nowtag}.csv"
        bio.seek(0)
        await msg.reply_document(document=bio, filename=fname,
                                 caption=f"📊 <b>{title}</b>\n📄 Tổng số dòng: <b>{total}</b>\n🕒 {get_vietnam_datetime_db()}",
                                 parse_mode=ParseMode.HTML)
        try:
            await status.delete()
        except Exception:
            pass
    except Exception as e:
        traceback.print_exc()
        await msg.reply_text(f"❌ Không thể xuất báo cáo: {html.escape(str(e))[:300]}",
                             parse_mode=ParseMode.HTML)


# ============================================================
# ADMIN_PANEL_V3 — MENU ADMIN NÚT BẤM, XOÁ/THÊM CƯỢC, RESET THỐNG KÊ, XOÁ GIAO DỊCH
# ============================================================
class _ProxyUpdate:
    # Giả lập update không có callback_query để các lệnh gửi tin mới thay vì sửa tin của menu.
    def __init__(self, upd):
        self._u = upd
        self.callback_query = None

    def __getattr__(self, name):
        return getattr(self._u, name)

# ---------- XOÁ / THÊM CƯỢC ----------
@admin_only
async def xoacuoc_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    try:
        target = int(ctx.args[0])
    except (IndexError, ValueError, TypeError):
        return await msg.reply_text(
            f'{ce("❌")} Cú pháp: <code>/xoacuoc [ID]</code> — xoá toàn bộ yêu cầu vòng cược của user.',
            parse_mode=ParseMode.HTML)
    row = query("SELECT bonus_amount, required_bet, current_bet FROM user_bonus WHERE user_id=%s", (target,)) or []
    if not row:
        return await msg.reply_text(f'{ce("📊")} ID <code>{target}</code> hiện không có vòng cược nào.', parse_mode=ParseMode.HTML)
    bonus, req, cur = row[0]
    query("DELETE FROM user_bonus WHERE user_id=%s", (target,))
    await msg.reply_text(
        f'{ce("✅")} <b>ĐÃ XOÁ VÒNG CƯỢC</b>\n━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("🆔")} ID: <code>{target}</code>\n'
        f'{ce("🎁")} Tiền khuyến mãi: <code>{fmt_money(int(bonus or 0))}đ</code>\n'
        f'{ce("🎯")} Yêu cầu cược: <code>{fmt_money(int(req or 0))}đ</code>\n'
        f'{ce("📈")} Đã cược: <code>{fmt_money(int(cur or 0))}đ</code>\n'
        f'{ce("🔓")} User có thể rút tiền bình thường.',
        parse_mode=ParseMode.HTML)
    try:
        await ctx.bot.send_message(target, f'{ce("🔓")} Admin đã xoá yêu cầu vòng cược của bạn. Bạn có thể rút tiền bình thường.', parse_mode=ParseMode.HTML)
    except Exception:
        pass

@admin_only
async def themcuoc_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    try:
        target = int(ctx.args[0])
        amount = parse_money_text(ctx.args[1])
    except (IndexError, ValueError, TypeError):
        return await msg.reply_text(
            f'{ce("❌")} Cú pháp: <code>/themcuoc [ID] [số tiền]</code>\n'
            f'Ví dụ: <code>/themcuoc 123456 500k</code> (số âm để trừ bớt: <code>-100k</code>)',
            parse_mode=ParseMode.HTML)
    row = query("SELECT required_bet, current_bet FROM user_bonus WHERE user_id=%s", (target,)) or []
    if not row or int(row[0][0] or 0) <= 0:
        return await msg.reply_text(
            f'{ce("❌")} ID <code>{target}</code> không có vòng cược để cộng. Dùng <code>/kmnap</code> để tạo khuyến mãi có vòng cược.',
            parse_mode=ParseMode.HTML)
    req, cur = int(row[0][0]), int(row[0][1] or 0)
    new_bet = max(0, cur + amount)
    query("UPDATE user_bonus SET current_bet=%s WHERE user_id=%s", (new_bet, target))
    left = req - new_bet
    await msg.reply_text(
        f'{ce("✅")} <b>ĐÃ CẬP NHẬT TIẾN ĐỘ CƯỢC</b>\n━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("🆔")} ID: <code>{target}</code>\n'
        f'{ce("➕")} Thêm: <code>{_signed_money(amount)}</code>\n'
        f'{ce("📈")} Đã cược: <code>{fmt_money(new_bet)}đ</code> / <code>{fmt_money(req)}đ</code>\n'
        f'{ce("📌")} Trạng thái: ' + (f'còn thiếu <code>{fmt_money(left)}đ</code>' if left > 0 else 'ĐÃ ĐỦ CƯỢC'),
        parse_mode=ParseMode.HTML)
    if new_bet >= req:
        await check_and_notify_bet_completion(target, new_bet, req)

# ---------- /themvongcuoc /ktvc /vcall ----------
_VCALL_DONE = set()

def _vc_bar(cur, req, width=20):
    pct = 0 if req <= 0 else max(0.0, min(100.0, cur * 100.0 / req))
    f = int(width * pct / 100)
    return "█" * f + "░" * (width - f), pct

def _vc_parse_mult(raw):
    t = str(raw).strip().lower().lstrip("x*").replace(",", ".")
    v = float(t)
    if v <= 0 or v > 1000:
        raise ValueError
    return v

@admin_only
async def themvongcuoc_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    try:
        target = int(ctx.args[0])
        amount = parse_money_text(ctx.args[1])
        if amount <= 0:
            raise ValueError
    except (IndexError, ValueError, TypeError):
        return await msg.reply_text(
            f'{ce("❌")} Cú pháp: <code>/themvongcuoc [ID] [số tiền yêu cầu cược]</code>\\n'
            f'Ví dụ: <code>/themvongcuoc 123456789 1000000</code> — người đó phải cược thêm 1.000.000đ mới được rút.',
            parse_mode=ParseMode.HTML)
    if not query("SELECT 1 FROM users WHERE user_id=%s", (target,)):
        return await msg.reply_text(f'{ce("❌")} Không tìm thấy ID <code>{target}</code>.', parse_mode=ParseMode.HTML)
    add_wager_requirement(target, 0, amount)
    st = get_bet_progress_status(target) or {"required_bet": amount, "current_bet": 0, "remaining": amount}
    await msg.reply_text(
        f'{ce("✅")} <b>ĐÃ THÊM VÒNG CƯỢC</b>\\n━━━━━━━━━━━━━━━━━━━━━\\n'
        f'{ce("🆔")} ID: <code>{target}</code>\\n'
        f'{ce("➕")} Yêu cầu cược thêm: <code>{fmt_money(amount)}đ</code>\\n'
        f'{ce("🎯")} Tổng yêu cầu: <code>{fmt_money(st["required_bet"])}đ</code>\\n'
        f'{ce("📈")} Đã cược: <code>{fmt_money(st["current_bet"])}đ</code>\\n'
        f'{ce("⚠️")} Còn phải cược: <code>{fmt_money(max(0, st["remaining"]))}đ</code>',
        parse_mode=ParseMode.HTML)
    try:
        await ctx.bot.send_message(
            target,
            f'{ce("🎯")} <b>THÔNG BÁO VÒNG CƯỢC</b>\\n'
            f'Bạn được yêu cầu cược thêm <code>{fmt_money(amount)}đ</code> trước khi rút tiền.\\n'
            f'{ce("⚠️")} Còn phải cược: <code>{fmt_money(max(0, st["remaining"]))}đ</code>',
            parse_mode=ParseMode.HTML)
    except Exception:
        pass

@admin_only
async def ktvc_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    try:
        target = int(ctx.args[0])
    except (IndexError, ValueError, TypeError):
        return await msg.reply_text(f'{ce("❌")} Cú pháp: <code>/ktvc [ID]</code>', parse_mode=ParseMode.HTML)
    if not query("SELECT 1 FROM users WHERE user_id=%s", (target,)):
        return await msg.reply_text(f'{ce("❌")} Không tìm thấy ID <code>{target}</code>.', parse_mode=ParseMode.HTML)
    bal = get_balance(target)
    st = get_bet_progress_status(target)
    if not st:
        return await msg.reply_text(
            f'{ce("📊")} <b>VÒNG CƯỢC</b> <code>{target}</code>\\n━━━━━━━━━━━━━━━━━━━━━\\n'
            f'{ce("💰")} Số dư: <code>{fmt_money(bal)}đ</code>\\n'
            f'{ce("🔓")} Không có yêu cầu cược — được rút bình thường.',
            parse_mode=ParseMode.HTML)
    bar, pct = _vc_bar(st["current_bet"], st["required_bet"])
    await msg.reply_text(
        f'{ce("📊")} <b>VÒNG CƯỢC</b> <code>{target}</code>\\n━━━━━━━━━━━━━━━━━━━━━\\n'
        f'{ce("💰")} Số dư: <code>{fmt_money(bal)}đ</code>\\n'
        f'{ce("🎁")} Tiền thưởng tích luỹ: <code>{fmt_money(int(st["bonus_amount"] or 0))}đ</code>\\n'
        f'{ce("🎯")} Yêu cầu cược: <code>{fmt_money(st["required_bet"])}đ</code>\\n'
        f'{ce("✅")} Đã hoàn thành: <code>{fmt_money(st["current_bet"])}đ</code>\\n'
        f'{ce("⚠️")} Còn thiếu: <code>{fmt_money(max(0, st["remaining"]))}đ</code>\\n'
        f'{ce("📈")} <code>{bar}</code> <code>{pct:.1f}%</code>',
        parse_mode=ParseMode.HTML)

@admin_only
async def vcall_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    try:
        mult = _vc_parse_mult(ctx.args[0])
    except (IndexError, ValueError, TypeError):
        return await msg.reply_text(
            f'{ce("❌")} Cú pháp: <code>/vcall x7</code>\\n'
            f'Thêm yêu cầu cược = số dư hiện tại × 7 vòng cho TẤT CẢ người dùng đang có số dư.',
            parse_mode=ParseMode.HTML)
    rows = query("SELECT user_id, balance FROM users WHERE balance>0") or []
    rows = [(int(u), int(b)) for u, b in rows if int(u) not in ADMIN_IDS]
    total_req = sum(int(b * mult) for _u, b in rows)
    mtxt = f"{mult:g}"
    kb = InlineKeyboardMarkup([[btn("XÁC NHẬN", "✅", callback_data=f"vcall:ok:{mtxt}"),
                                btn("HUỶ", "❌", callback_data="vcall:no")]])
    await msg.reply_text(
        f'{ce("⚠️")} <b>XÁC NHẬN THÊM VÒNG CƯỢC TOÀN BỘ</b>\\n━━━━━━━━━━━━━━━━━━━━━\\n'
        f'{ce("👥")} Số người có số dư: <b>{len(rows)}</b>\\n'
        f'{ce("🎯")} Mỗi người: số dư × <b>x{mtxt}</b> vòng cược\\n'
        f'{ce("📊")} Tổng yêu cầu cược sẽ thêm: <b>{fmt_money(total_req)}đ</b>\\n\\n'
        f'<i>Yêu cầu được cộng dồn vào vòng cược hiện có (nếu có). Bấm XÁC NHẬN để thực hiện.</i>',
        reply_markup=kb, parse_mode=ParseMode.HTML)

def _vcall_apply_sync(mult):
    rows = query("SELECT user_id, balance FROM users WHERE balance>0") or []
    done, total, targets = 0, 0, []
    for u, b in rows:
        u, b = int(u), int(b)
        if u in ADMIN_IDS:
            continue
        req = int(b * mult)
        if req <= 0:
            continue
        add_wager_requirement(u, 0, req)
        done += 1
        total += req
        targets.append((u, b, req))
    return done, total, targets

async def _vcall_notify(bot, mult, targets):
    for u, b, req in targets:
        try:
            await bot.send_message(
                u,
                f'{ce("🎯")} <b>THÔNG BÁO VÒNG CƯỢC</b>\\n'
                f'Tài khoản của bạn được yêu cầu cược <b>x{mult:g}</b> vòng trên số dư <code>{fmt_money(b)}đ</code>.\\n'
                f'{ce("⚠️")} Yêu cầu cược thêm: <code>{fmt_money(req)}đ</code> trước khi rút tiền.',
                parse_mode=ParseMode.HTML)
        except Exception:
            pass
        await asyncio.sleep(0.06)

async def vcall_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id not in ADMIN_IDS or is_admin_banned(q.from_user.id):
        return await q.answer("Bạn không có quyền.", show_alert=True)
    parts = (q.data or "").split(":")
    if len(parts) > 1 and parts[1] == "no":
        await q.answer("Đã huỷ.")
        return await q.edit_message_text(f'{ce("❎")} Đã huỷ thêm vòng cược toàn bộ.', parse_mode=ParseMode.HTML)
    if len(parts) < 3 or parts[1] != "ok":
        return await q.answer()
    key = (q.message.chat_id, q.message.message_id)
    if key in _VCALL_DONE:
        return await q.answer("Đã xử lý rồi!", show_alert=True)
    _VCALL_DONE.add(key)
    try:
        mult = float(parts[2])
    except ValueError:
        return await q.answer("Lỗi số vòng.", show_alert=True)
    await q.answer("Đang thực hiện…")
    done, total, targets = await asyncio.to_thread(_vcall_apply_sync, mult)
    await q.edit_message_text(
        f'{ce("✅")} <b>ĐÃ THÊM VÒNG CƯỢC TOÀN BỘ</b>\\n━━━━━━━━━━━━━━━━━━━━━\\n'
        f'{ce("🎯")} Hệ số: <b>x{mult:g}</b> vòng trên toàn bộ số dư\\n'
        f'{ce("👥")} Số người áp dụng: <b>{done}</b>\\n'
        f'{ce("📊")} Tổng yêu cầu cược đã thêm: <b>{fmt_money(total)}đ</b>\\n'
        f'<i>Đang gửi thông báo cho người dùng…</i>',
        parse_mode=ParseMode.HTML)
    asyncio.create_task(_vcall_notify(ctx.bot, mult, targets))

# ---------- RESET THỐNG KÊ ----------
@admin_only
async def resetthongke_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    args = [a.lower() for a in (ctx.args or [])]
    if args and args[0] in ("khoiphuc", "undo", "huy"):
        for k in ("stats_epoch_dep", "stats_epoch_wd"):
            set_setting(k, "0")
        set_setting("stats_epoch_day", "1970-01-01")
        set_setting("stats_epoch_at", "")
        query("DELETE FROM stats_bet_base")
        return await msg.reply_text(f'{ce("✅")} Đã khôi phục thống kê đầy đủ (bỏ mốc reset).', parse_mode=ParseMode.HTML)
    kb = InlineKeyboardMarkup([[btn("XÁC NHẬN RESET", "⚠️", callback_data="resetstat_yes"),
                                btn("Hủy", "❌", callback_data="resetstat_no")]])
    await msg.reply_text(
        f'{ce("⚠️")} <b>RESET THỐNG KÊ HỆ THỐNG</b>\n━━━━━━━━━━━━━━━━━━━━━\n'
        f'Sau khi xác nhận, các bảng thống kê (/thongke, /tong, /homnay, file xuất thống kê) sẽ đếm lại <b>từ 0</b>.\n\n'
        f'{ce("✅")} <b>KHÔNG bị xoá:</b> số dư, lịch sử cá nhân của user, điều kiện rút tiền, VIP, hoàn thưởng.\n'
        f'{ce("🔄")} Muốn quay lại thống kê đầy đủ: <code>/resetthongke khoiphuc</code>\n\n'
        f'{_stat_epoch_note()}Bạn chắc chắn muốn reset?',
        reply_markup=kb, parse_mode=ParseMode.HTML)

async def reset_stats_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id not in ADMIN_IDS or is_admin_banned(q.from_user.id):
        return await q.answer("Bạn không có quyền.", show_alert=True)
    if q.data == "resetstat_no":
        await q.answer("Đã hủy.")
        return await q.edit_message_text("❎ Đã hủy reset thống kê.")
    dep_max = int(((query("SELECT COALESCE(MAX(id),0) FROM deposit_history") or [(0,)])[0][0]) or 0)
    wd_max = int(((query("SELECT COALESCE(MAX(id),0) FROM withdraw_history") or [(0,)])[0][0]) or 0)
    today = get_vietnam_time().date()
    set_setting("stats_epoch_dep", dep_max)
    set_setting("stats_epoch_wd", wd_max)
    query("DELETE FROM stats_bet_base")
    query("INSERT INTO stats_bet_base (user_id, day, bet, win) SELECT user_id, day, bet, win FROM bet_daily WHERE day=%s", (today,))
    set_setting("stats_epoch_day", today.isoformat())
    set_setting("stats_epoch_at", get_vietnam_datetime_db())
    await q.answer("Đã reset thống kê.")
    await q.edit_message_text(
        f'{ce("✅")} <b>ĐÃ RESET THỐNG KÊ TỪ ĐẦU</b>\n'
        f'{ce("⏰")} Mốc reset: <code>{get_vietnam_datetime_db()}</code>\n'
        f'{ce("💡")} Xem lại bằng /thongke. Khôi phục: <code>/resetthongke khoiphuc</code>',
        parse_mode=ParseMode.HTML)

# ---------- XOÁ THỦ CÔNG GIAO DỊCH NẠP / RÚT ----------
async def _txdel_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE, kind: str):
    msg = update.effective_message
    cmd = "xoanap" if kind == "dep" else "xoarut"
    ids = []
    for a in (ctx.args or [])[:10]:
        if a.isdigit():
            ids.append(int(a))
    if not ids:
        return await msg.reply_text(
            f'{ce("❌")} Cú pháp: <code>/{cmd} [mã GD] [mã GD...]</code>\n'
            f'Xem mã GD ở <code>/{"lsnaptatca" if kind == "dep" else "lsruttatca"}</code> (số sau dấu #).\n'
            f'Xoá xong, thống kê tự động trừ giao dịch đó.',
            parse_mode=ParseMode.HTML)
    table = "deposit_history" if kind == "dep" else "withdraw_history"
    rows = query(f"SELECT id, user_id, amount, status, time FROM {table} WHERE id = ANY(%s) ORDER BY id", (ids,)) or []
    if not rows:
        return await msg.reply_text(f'{ce("❌")} Không tìm thấy giao dịch nào với mã đã nhập.', parse_mode=ParseMode.HTML)
    ok_ids, lines = [], []
    for r in rows:
        label = _rp_status(r[3])
        blocked = (kind == "rut" and label == "Chờ duyệt")
        lines.append(f'{ce("🚫") if blocked else ce("🧾")} #{r[0]} · ID <code>{r[1]}</code> · <code>{fmt_money(int(r[2] or 0))}đ</code> · {html.escape(label)} · {html.escape(str(r[4] or ""))}'
                     + (' <i>(đang chờ duyệt — hãy duyệt/từ chối trước)</i>' if blocked else ''))
        if not blocked:
            ok_ids.append(r[0])
    if not ok_ids:
        return await msg.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)
    kb = InlineKeyboardMarkup([[btn("XÁC NHẬN XOÁ", "🗑", callback_data=f"txdel_yes_{kind}_{'-'.join(map(str, ok_ids))}"),
                                btn("Hủy", "❌", callback_data="txdel_no")]])
    await msg.reply_text(
        f'{ce("🗑")} <b>XÁC NHẬN XOÁ GIAO DỊCH {"NẠP" if kind == "dep" else "RÚT"}</b>\n━━━━━━━━━━━━━━━━━━━━━\n'
        + "\n".join(lines) +
        f'\n━━━━━━━━━━━━━━━━━━━━━\n{ce("📌")} Chỉ xoá bản ghi giao dịch (thống kê tự cập nhật). <b>Số dư của user KHÔNG bị thay đổi</b> — nếu cần hãy dùng /sub hoặc /add.'
        + (f'\n{ce("⚠️")} Giao dịch nạp tự động có mã SePay: xoá bản ghi sẽ mất cơ chế chống nạp trùng cho mã đó.' if kind == "dep" else ''),
        reply_markup=kb, parse_mode=ParseMode.HTML)

@admin_only
async def xoanap_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await _txdel_cmd(update, ctx, "dep")

@admin_only
async def xoarut_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await _txdel_cmd(update, ctx, "rut")

async def txdel_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id not in ADMIN_IDS or is_admin_banned(q.from_user.id):
        return await q.answer("Bạn không có quyền.", show_alert=True)
    if q.data == "txdel_no":
        await q.answer("Đã hủy.")
        return await q.edit_message_text("❎ Đã hủy xoá giao dịch.")
    parts = q.data.split("_", 3)
    if len(parts) < 4:
        return await q.answer()
    kind, ids = parts[2], [int(x) for x in parts[3].split("-") if x.isdigit()]
    table = "deposit_history" if kind == "dep" else "withdraw_history"
    if kind == "dep":
        rows = query(f"DELETE FROM {table} WHERE id = ANY(%s) RETURNING id, user_id, amount", (ids,)) or []
    else:
        rows = query(f"DELETE FROM {table} WHERE id = ANY(%s) AND status <> 'pending' RETURNING id, user_id, amount", (ids,)) or []
    await q.answer("Đã xoá.")
    total = sum(int(r[2] or 0) for r in rows)
    await q.edit_message_text(
        f'{ce("✅")} <b>ĐÃ XOÁ {len(rows)} GIAO DỊCH {"NẠP" if kind == "dep" else "RÚT"}</b>\n'
        f'{ce("💰")} Tổng tiền: <code>{fmt_money(total)}đ</code>\n'
        f'{ce("📊")} Thống kê đã tự động cập nhật (xem /thongke).',
        parse_mode=ParseMode.HTML)

# ---------- MENU ADMIN DẠNG NÚT BẤM ----------
# item = (loại, lệnh hiển thị, mô tả, khoá chạy / khoá usage, cú pháp, ví dụ)
_ADM_CATS = [
    ("bt", "🛠", "BẢO TRÌ & ROOM", "Bật/tắt bảo trì game, nạp, rút và tắt/bật room hoàn toàn.", [
        ("run", "baotri", "Bảng bảo trì từng game", "baotri", None, None),
        ("run", "baotriht", "Bảng bảo trì hệ thống", "baotriht", None, None),
        ("run", "trangthai", "Trạng thái tổng quan bot", "trangthai", None, None),
        ("run", "tatroom", "Tắt room nhóm chính (bot ngừng gửi tin + hoàn cược phiên đang mở)", "tatroom", None, None),
        ("run", "moroom", "Bật lại room nhóm chính", "moroom", None, None),
        ("run", "tatroom all", "Tắt TẤT CẢ room", "tatroom|all", None, None),
        ("run", "moroom all", "Bật TẤT CẢ room", "moroom|all", None, None),
        ("run", "trangthairoom", "Xem trạng thái các room", "trangthairoom", None, None),
        ("use", "baotrigame", "Bảo trì nhiều game / nạp / rút", "x", "/baotrigame [game...] on|off", "/baotrigame pt br on  ·  /baotrigame all off"),
        ("use", "baotriall", "Bảo trì toàn hệ thống", "x", "/baotriall on|off", "/baotriall on"),
        ("use", "baotritc", "Bảo trì toàn bộ (kể cả menu)", "x", "/baotritc on|off", "/baotritc off"),
        ("use", "tatcuoc", "Chỉ khóa/mở cược trong nhóm", "x", "/tatcuoc on|off", "/tatcuoc off"),
    ]),
    ("us", "👥", "NGƯỜI DÙNG", "Tra cứu hồ sơ, khóa/mở tài khoản, cấm game, nạp/rút, hoàn trả.", [
        ("run", "all", "Danh sách người dùng (phân trang)", "all", None, None),
        ("run", "dsban", "Danh sách tài khoản bị khóa", "dsban", None, None),
        ("run", "topsodu", "Top 10 số dư", "topsodu", None, None),
        ("run", "topcuoc", "Top 10 tổng cược", "topcuoc", None, None),
        ("use", "fulluser", "Hồ sơ đầy đủ + nút xuất Excel", "x", "/fulluser [ID]", "/fulluser 123456789 (hoặc reply tin nhắn của user)"),
        ("use", "user", "Hồ sơ nhanh + khóa/mở", "x", "/user [ID]", "/user 123456789"),
        ("use", "timuser", "Tìm user theo ID/STK/tên", "x", "/timuser [từ khóa]", "/timuser NGUYEN VAN A"),
        ("use", "ban", "Khóa tài khoản", "x", "/ban [ID]", "/ban 123456789"),
        ("use", "unban", "Mở khóa tài khoản", "x", "/unban [ID]", "/unban 123456789"),
        ("use", "camgame", "Cấm user chơi 1 game", "x", "/camgame [ID] [game]", "/camgame 123456789 pt"),
        ("use", "mogame", "Gỡ cấm game", "x", "/mogame [ID] [game|all]", "/mogame 123456789 all"),
        ("use", "camtn", "Khóa nạp/rút của user", "x", "/camtn [ID] nap|rut", "/camtn 123456789 rut"),
        ("use", "motn", "Mở khóa nạp/rút", "x", "/motn [ID] nap|rut|all", "/motn 123456789 all"),
        ("use", "camhoan", "Khóa nhận hoàn trả", "x", "/camhoan [ID] ngay|tuan|all", "/camhoan 123456789 all"),
        ("use", "mohoan", "Mở nhận hoàn trả", "x", "/mohoan [ID] ngay|tuan|all", "/mohoan 123456789 all"),
        ("use", "resetbank", "Gỡ liên kết ngân hàng", "x", "/resetbank [ID]", "/resetbank 123456789"),
    ]),
    ("mn", "💰", "TIỀN & GIAO DỊCH", "Cộng/trừ tiền, nạp tay, duyệt nạp/rút, xoá giao dịch.", [
        ("run", "dsnap", "Nạp đang chờ duyệt", "dsnap", None, None),
        ("run", "dsrut", "Rút đang chờ duyệt", "dsrut", None, None),
        ("run", "lsnaptatca", "50 lịch sử nạp mới nhất", "lsnaptatca", None, None),
        ("run", "lsruttatca", "50 lịch sử rút mới nhất", "lsruttatca", None, None),
        ("run", "soduall", "Số dư của tất cả user", "soduall", None, None),
        ("run", "hisall", "50 giao dịch gần nhất toàn hệ thống", "hisall", None, None),
        ("use", "naptien", "Nạp tiền tay cho user", "x", "/naptien [ID] [số tiền]", "/naptien 123456789 100000"),
        ("use", "add", "Cộng tiền", "x", "/add [ID] [số tiền]", "/add 123456789 50000"),
        ("use", "sub", "Trừ tiền", "x", "/sub [ID] [số tiền]", "/sub 123456789 50000"),
        ("use", "setsd", "Đặt số dư bằng giá trị cụ thể", "x", "/setsd [ID] [số tiền]", "/setsd 123456789 500k"),
        ("use", "resetuser", "Reset số dư 1 user về 0 (có xác nhận)", "x", "/resetuser [ID]", "/resetuser 123456789"),
        ("use", "xoanap", "Xoá giao dịch NẠP (thống kê tự cập nhật)", "x", "/xoanap [mã GD] [mã GD...]", "/xoanap 15 16"),
        ("use", "xoarut", "Xoá giao dịch RÚT (thống kê tự cập nhật)", "x", "/xoarut [mã GD] [mã GD...]", "/xoarut 8"),
    ]),
    ("bet", "🎯", "CƯỢC & KHUYẾN MÃI", "Quản lý vòng cược, khuyến mãi nạp, hoàn trả, hũ jackpot.", [
        ("run", "dskm", "Danh sách đang có vòng cược khuyến mãi", "dskm", None, None),
        ("run", "kmgio", "Xem/điều khiển giờ vàng nạp 10%", "kmgio", None, None),
        ("run", "homnay", "Báo cáo nhanh hôm nay", "homnay", None, None),
        ("use", "xoacuoc", "XOÁ toàn bộ vòng cược của user", "x", "/xoacuoc [ID]", "/xoacuoc 123456789"),
        ("use", "themcuoc", "THÊM tiền cược đã hoàn thành (âm để trừ)", "x", "/themcuoc [ID] [số tiền]", "/themcuoc 123456789 500k"),
        ("use", "themvongcuoc", "THÊM yêu cầu vòng cược cho user (phải cược thêm mới được rút)", "x", "/themvongcuoc [ID] [số tiền]", "/themvongcuoc 123456789 1000000"),
        ("use", "ktvc", "Kiểm tra vòng cược: yêu cầu / đã cược / còn thiếu", "x", "/ktvc [ID]", "/ktvc 123456789"),
        ("use", "vcall", "THÊM vòng cược cho TẤT CẢ user có số dư (số dư × vòng)", "x", "/vcall x7", "/vcall x7"),
        ("use", "kmnap", "Tặng khuyến mãi có vòng cược", "x", "/kmnap [ID] [số tiền]", "/kmnap 123456789 20000"),
        ("use", "checkprogressadmin", "Xem tiến độ cược của user", "x", "/checkprogressadmin [ID]", "/checkprogressadmin 123456789"),
        ("use", "resetprogress", "Reset tiến độ cược", "x", "/resetprogress [ID]", "/resetprogress 123456789"),
        ("use", "resethoanall", "RESET TOÀN BỘ tiền hoàn trả của 1 người (đã chốt + đang tích luỹ, có xác nhận)", "x", "/resethoanall [ID] [ngay|tuan|all]", "/resethoanall 123456789 all"),
        ("use", "sethoancuoc", "Đặt % hoàn cược", "x", "/sethoancuoc ngay|tuan [%]", "/sethoancuoc ngay 2"),
        ("use", "sethu", "Đặt hũ Jackpot", "x", "/sethu [số tiền]", "/sethu 50m"),
        ("use", "hu", "Đặt hũ Tài Xỉu 3D (miniapp)", "x", "/hu [số tiền]", "/hu 50m"),
        ("use", "ep", "Ép kết quả Tài Xỉu 3D (áp dụng cả khi có người chơi thật cược)", "x", "/ep [1 3 4 | t | x | off]", "/ep 1 3 4"),
    ]),
    ("cd", "🎁", "GIFTCODE", "Tạo, xem và xoá các loại code.", [
        ("run", "taogift", "Tạo giftcode nhiều loại (từng bước)", "taogift", None, None),
        ("run", "dsgift", "30 giftcode gần nhất", "dsgift", None, None),
        ("use", "taocode", "Tạo code thường", "x", "/taocode [số tiền] [lượt dùng]", "/taocode 10000 50"),
        ("use", "taocodeall", "Tạo nhiều code 1 lượt", "x", "/taocodeall [số tiền] [số lượng]", "/taocodeall 5000 20"),
        ("use", "xoacode", "Xoá code thường", "x", "/xoacode [mã]", "/xoacode ABC12345"),
        ("use", "xoagift", "Xoá giftcode", "x", "/xoagift [mã]", "/xoagift XOCLO88-TANTHU-XXXXXXX"),
        ("run", "dsnaphomnay", "Danh sách người đã nạp thành công hôm nay", "dsnaphomnay", None, None),
        ("use", "tangcodenap", "Tặng code thủ công cho người đã nạp", "x", "/tangcodenap [giá trị] [vòng cược] [hạn] [homnay|all|id1,id2] [nạp tối thiểu]", "/tangcodenap 20k 1 1n homnay"),
        ("use", "yccode", "Thêm / gỡ yêu cầu nhập code (nạp trong ngày, tổng nạp)", "x", "/yccode [mã] nap|tongnap [số tiền] | off", "/yccode XOCLO88-TRIAN-ABC1234 nap 100k"),
    ]),
    ("tk", "📊", "THỐNG KÊ & XUẤT FILE", "Thống kê hệ thống và xuất file Excel đẹp nhiều sheet.", [
        ("run", "thongke", "Bảng thống kê hôm nay / tháng / tổng", "thongke", None, None),
        ("run", "tong", "Tổng quan tài chính", "tong", None, None),
        ("run", "xuatthongke 7", "Xuất file thống kê 7 ngày", "xuatthongke|7", None, None),
        ("run", "xuatthongke 30", "Xuất file thống kê 30 ngày", "xuatthongke|30", None, None),
        ("run", "xuatthongke all", "Xuất file thống kê toàn bộ", "xuatthongke|all", None, None),
        ("run", "xuatnapall", "Xuất toàn bộ lịch sử NẠP", "xuatnapall", None, None),
        ("run", "xuatrutall", "Xuất toàn bộ lịch sử RÚT", "xuatrutall", None, None),
        ("run", "xuathethong", "Xuất báo cáo toàn hệ thống", "xuathethong", None, None),
        ("run", "resetthongke", "Reset thống kê từ đầu (có xác nhận)", "resetthongke", None, None),
        ("use", "xuatthongke", "Xuất thống kê theo kỳ tuỳ chọn", "x", "/xuatthongke [kỳ]", "/xuatthongke 01/10/2026 - 29/10/2026"),
        ("use", "xuatls", "Xuất FULL Excel của 1 user", "x", "/xuatls [ID] [kỳ]", "/xuatls 123456789 30"),
        ("use", "tongket", "Tổng kết 1 user theo kỳ", "x", "/tongket [ID] [kỳ]", "/tongket 123456789 7"),
        ("use", "lsuser", "Biến động số dư của user", "x", "/lsuser [ID] [kỳ]", "/lsuser 123456789 all"),
    ]),
    ("cm", "📣", "THÔNG BÁO", "Gửi thông báo và nhắn riêng cho user.", [
        ("use", "send", "Gửi thông báo cho tất cả user", "x", "/send [nội dung]", "/send Bot bảo trì 10 phút"),
        ("use", "rep", "Nhắn riêng cho 1 user", "x", "/rep [ID] [nội dung]", "/rep 123456789 Đã duyệt rút của bạn"),
    ]),
]
# Các lệnh quản trị bổ sung trước đây chỉ có thể gọi bằng cách gõ lệnh.
_ADM_CATS.append((
    "more", "🧩", "CÔNG CỤ QUẢN TRỊ KHÁC",
    "Các công cụ tra cứu, thống kê, lịch sử và thiết lập bổ sung.",
    [
        ("use", "stats", "Thống kê nhanh", "x", "/stats", "/stats"),
        ("use", "info", "Thông tin nhanh user", "x", "/info [ID]", "/info 123456789"),
        ("use", "check", "Kiểm tra lịch sử user", "x", "/check [ID]", "/check 123456789"),
        ("use", "resetsdall", "Reset số dư toàn bộ user", "x", "/resetsdall", "/resetsdall"),
        ("use", "resetall", "Lệnh reset toàn bộ số dư (bí danh)", "x", "/resetall", "/resetall"),
        ("use", "xoalsall", "Xoá toàn bộ lịch sử", "x", "/xoalsall", "/xoalsall"),
        ("use", "xoals", "Xoá lịch sử một user", "x", "/xoals [ID]", "/xoals 123456789"),
        ("use", "setname", "Đổi tên bot", "x", "/setname [tên mới]", "/setname XOCLO88"),
        ("use", "kmnapvc", "Tặng khuyến mãi theo vòng cược", "x", "/kmnapvc [ID] [số tiền]", "/kmnapvc 123456789 20000"),
        ("use", "lsnap", "Lịch sử nạp của user", "x", "/lsnap [ID]", "/lsnap 123456789"),
        ("use", "lsrut", "Lịch sử rút kèm thông tin + QR", "x", "/lsrut [ID]", "/lsrut 123456789"),
        ("use", "lsrutky", "Báo cáo rút của user theo kỳ", "x", "/lsrutky [ID]", "/lsrutky 123456789"),
        ("use", "taoadmin", "Tạo tài khoản đăng nhập web admin", "x", "/taoadmin [tên] [mật khẩu]", "/taoadmin quanly1 MatKhau123"),
        ("use", "doimkadmin", "Đổi mật khẩu web admin", "x", "/doimkadmin [tên] [mật khẩu mới]", "/doimkadmin quanly1"),
        ("use", "xoaadmin", "Xoá tài khoản web admin", "x", "/xoaadmin [tên]", "/xoaadmin quanly1"),
        ("run", "dsadminweb", "Danh sách tài khoản web admin", "dsadminweb", None, None),
        ("use", "lscuoc", "Lịch sử cược và thắng của user", "x", "/lscuoc [ID]", "/lscuoc 123456789"),
        ("use", "lscode", "Lịch sử nhập code của user", "x", "/lscode [ID]", "/lscode 123456789"),
        ("use", "lsgift", "Lịch sử dùng giftcode", "x", "/lsgift [ID]", "/lsgift 123456789"),
        ("use", "lsmua", "Lịch sử mua giftcode", "x", "/lsmua [ID]", "/lsmua 123456789"),
        ("use", "top", "Top tương tác hôm nay", "x", "/top", "/top"),
        ("use", "checktt", "Kiểm tra tương tác user", "x", "/checktt [ID]", "/checktt 123456789"),
        ("use", "topnap", "Top 10 người nạp thành công", "x", "/topnap", "/topnap"),
        ("use", "resetsystem", "Yêu cầu xác nhận reset dữ liệu hệ thống", "x", "/resetsystem", "/resetsystem"),
        ("use", "codenap", "Tạo giftcode nạp (bí danh taogift)", "x", "/codenap", "/codenap"),
    ],
))
_ADM_CAT_MAP = {c[0]: c for c in _ADM_CATS}
_ADM_USAGE = {it[1]: (it[4] or "") for c in _ADM_CATS for it in c[4]}

# ============================================================
# ADMIN_FLOW — BẤM LỆNH TRONG MENU -> BOT HỎI TỪNG THÔNG TIN -> ADMIN NHẬP / BẤM NÚT -> TỰ CHẠY LỆNH
#  • Không cần gõ lệnh thủ công: bấm lệnh trong menu, bot hỏi ID / số tiền / lựa chọn...
#  • Mỗi bước có nút bấm nhanh (ID gần nhất, mức tiền hay dùng, on/off, ngày/tuần...), Quay lại, Bỏ qua, Huỷ.
#  • Trong chat riêng: gõ thẳng câu trả lời. Trong nhóm: reply vào tin nhắn của bot.
#  • Lệnh gõ tay (/add 123 50k ...) vẫn hoạt động như cũ.
# ============================================================
_FLOW_TTL = 600     # giây; quá hạn thì tự bỏ phiên nhập

def _S(kind, name, prompt, choices=None, optional=False, free=False, when=None, norm=None,
       quick=None, neg=False, lo=None, hi=None):
    return {"kind": kind, "name": name, "prompt": prompt, "choices": choices or [], "optional": optional,
            "free": free, "when": when, "norm": norm, "quick": quick or [], "neg": neg, "lo": lo, "hi": hi}

_Q_MONEY = ["10k", "50k", "100k", "500k", "1m"]
_CH_MT = [("🔴 BẬT bảo trì", "on"), ("🟢 TẮT bảo trì", "off")]
_CH_PERIOD = [("📅 Hoàn ngày", "ngay"), ("🗓 Hoàn tuần", "tuan"), ("♻️ Cả hai", "all")]
_CH_RANGE = [("7 ngày", "7"), ("30 ngày", "30"), ("Tất cả", "all")]
_CH_GAMES = [(v[2], k) for k, v in ADMIN_GAMES.items()]

def _ID(prompt="Nhập <b>ID người dùng</b> (dãy số):"):
    return _S("id", "ID", prompt)

def _MONEY(prompt="Nhập <b>số tiền</b> (vd: <code>50000</code>, <code>50k</code>, <code>1m</code>):", name="Số tiền", **kw):
    return _S("money", name, prompt, quick=_Q_MONEY, **kw)

def _TEXT(name, prompt, **kw):
    return _S("text", name, prompt, **kw)

def _RANGE():
    return _S("choice", "Kỳ", "Chọn <b>kỳ</b> (hoặc gõ ngày: <code>29/10/2026</code>, "
              "<code>01/10/2026 - 29/10/2026</code>, hay số ngày gần nhất):", choices=_CH_RANGE, free=True)

def _CONFIRM(prompt):
    return [_S("confirm", "Xác nhận", prompt)]

def _upper(v):
    return v.strip().upper()

_ADM_FLOW = {
    # ---- Bảo trì & room ----
    "baotrigame": [
        _S("choice", "Game", "Chọn <b>game / tính năng</b> cần đổi trạng thái bảo trì "
           "(hoặc gõ nhiều mục cách nhau bằng dấu cách, vd: <code>pt br nap</code>):",
           choices=_CH_GAMES + [("Nạp tiền", "nap"), ("Rút tiền", "rut"), ("TẤT CẢ", "all")], free=True),
        _S("choice", "Trạng thái", "Chọn trạng thái:", choices=_CH_MT)],
    "baotriall": [_S("choice", "Trạng thái", "Bảo trì <b>toàn hệ thống</b>:", choices=_CH_MT)],
    "baotritc": [_S("choice", "Trạng thái", "Bảo trì <b>toàn bộ</b> (kể cả menu):", choices=_CH_MT)],
    "tatcuoc": [_S("choice", "Cược", "Khoá / mở cược trong nhóm (lệnh này chỉ dùng được trong <b>NHÓM</b>):",
                   choices=[("🔒 TẮT cược", "off"), ("🔓 BẬT cược", "on")])],
    # ---- Người dùng ----
    "fulluser": [_ID()], "user": [_ID()],
    "timuser": [_TEXT("Từ khoá", "Nhập <b>từ khoá</b> cần tìm (ID, STK hoặc tên):")],
    "ban": [_ID("Nhập <b>ID</b> cần <b>KHOÁ</b> tài khoản:")],
    "unban": [_ID("Nhập <b>ID</b> cần <b>MỞ KHOÁ</b> tài khoản:")],
    "camgame": [_ID(), _S("choice", "Game", "Chọn <b>game</b> cấm user này chơi:", choices=_CH_GAMES)],
    "mogame": [_ID(), _S("choice", "Game", "Chọn <b>game</b> gỡ cấm:", choices=_CH_GAMES + [("Tất cả game", "all")])],
    "camtn": [_ID(), _S("choice", "Loại", "Khoá <b>nạp</b> hay <b>rút</b>?", choices=[("📥 Nạp", "nap"), ("📤 Rút", "rut")])],
    "motn": [_ID(), _S("choice", "Loại", "Mở khoá <b>nạp</b> hay <b>rút</b>?",
                       choices=[("📥 Nạp", "nap"), ("📤 Rút", "rut"), ("♻️ Cả hai", "all")])],
    "camhoan": [_ID(), _S("choice", "Loại", "<b>Khoá nhận</b> hoàn trả loại nào?", choices=_CH_PERIOD)],
    "mohoan": [_ID(), _S("choice", "Loại", "<b>Mở nhận</b> hoàn trả loại nào?", choices=_CH_PERIOD)],
    "resetbank": [_ID("Nhập <b>ID</b> cần gỡ liên kết ngân hàng:")],
    # ---- Tiền & giao dịch ----
    "naptien": [_ID(), _MONEY("Nhập <b>số tiền nạp tay</b>:")],
    "add": [_ID("Nhập <b>ID</b> cần <b>CỘNG</b> tiền:"), _MONEY("Nhập <b>số tiền cộng</b>:")],
    "sub": [_ID("Nhập <b>ID</b> cần <b>TRỪ</b> tiền:"), _MONEY("Nhập <b>số tiền trừ</b>:")],
    "setsd": [_ID(), _MONEY("Nhập <b>số dư mới</b> muốn đặt:")],
    "resetuser": [_ID("Nhập <b>ID</b> cần reset số dư về 0 (sau đó còn bước xác nhận):")],
    "xoanap": [_TEXT("Mã GD", "Nhập <b>mã giao dịch NẠP</b> cần xoá (nhiều mã cách nhau bằng dấu cách, vd: <code>15 16</code>):")],
    "xoarut": [_TEXT("Mã GD", "Nhập <b>mã giao dịch RÚT</b> cần xoá (nhiều mã cách nhau bằng dấu cách, vd: <code>8</code>):")],
    # ---- Cược & khuyến mãi ----
    "xoacuoc": [_ID("Nhập <b>ID</b> cần xoá toàn bộ vòng cược:")],
    "themcuoc": [_ID(), _MONEY("Nhập <b>số tiền cược cộng thêm</b> (số âm để trừ, vd: <code>-100k</code>):", neg=True)],
    "themvongcuoc": [_ID(), _MONEY("Nhập <b>số tiền yêu cầu cược thêm</b> (user phải cược đủ mới được rút):")],
    "ktvc": [_ID()],
    "vcall": [_S("choice", "Số vòng", "Chọn <b>số vòng cược</b> thêm cho TẤT CẢ user có số dư (số dư × vòng; sau đó còn bước xác nhận):",
                 choices=[("x3", "x3"), ("x5", "x5"), ("x7", "x7"), ("x10", "x10")], free=True)],
    "kmnap": [_ID(), _MONEY("Nhập <b>số tiền khuyến mãi</b> tặng:")],
    "checkprogressadmin": [_ID()],
    "resetprogress": [_ID("Nhập <b>ID</b> cần reset tiến độ cược:")],
    "resethoanall": [
        _ID("Nhập <b>ID</b> người cần <b>reset tiền hoàn trả</b> (chỉ reset riêng người này):"),
        _S("choice", "Loại", "Reset loại hoàn trả nào? (sau đó còn bước xác nhận)", choices=_CH_PERIOD)],
    "sethoancuoc": [
        _S("choice", "Loại", "Đặt % hoàn cược cho loại nào?", choices=[("📅 Hoàn ngày", "ngay"), ("🗓 Hoàn tuần", "tuan")]),
        _S("num", "Tỉ lệ %", "Nhập <b>tỉ lệ %</b> hoàn cược (vd: <code>1.8</code>):",
           quick=["1", "1.5", "1.8", "2", "3"], lo=0, hi=100)],
    "sethu": [_MONEY("Nhập <b>số tiền hũ Jackpot</b>:")],
    "hu": [_MONEY("Nhập <b>số tiền hũ Tài Xỉu 3D</b>:")],
    "ep": [_S("choice", "Kết quả", "Chọn kết quả <b>ép</b> cho phiên kế tiếp (hoặc gõ 3 số xúc xắc, vd: <code>1 3 4</code>). "
              "Lệnh này chỉ dùng được trong <b>chat riêng</b>:",
              choices=[("🔵 Tài", "t"), ("🔴 Xỉu", "x"), ("🚫 Huỷ ép", "off")], free=True)],
    # ---- Giftcode ----
    "taocode": [_MONEY("Nhập <b>giá trị code</b>:"),
                _S("num", "Lượt dùng", "Nhập <b>số lượt dùng</b>:", quick=["1", "10", "50", "100"], lo=1)],
    "taocodeall": [_MONEY("Nhập <b>giá trị mỗi code</b>:"),
                   _S("num", "Số lượng", "Nhập <b>số lượng code</b> (mỗi code 1 lượt):", quick=["5", "10", "20", "50"], lo=1)],
    "xoacode": [_TEXT("Mã", "Nhập <b>mã code</b> cần xoá:", norm=_upper)],
    "xoagift": [_TEXT("Mã", "Nhập <b>mã giftcode</b> cần xoá:", norm=_upper)],
    "tangcodenap": [
        _MONEY("Nhập <b>giá trị mỗi code</b> tặng:", name="Giá trị"),
        _S("num", "Vòng cược", "Nhập <b>số vòng cược</b> (0 = không cần cược):", quick=["0", "1", "2", "3"], lo=0, hi=100),
        _S("choice", "Hạn", "Nhập <b>hạn dùng</b>: <code>30p</code> (phút) · <code>2h</code> (giờ) · <code>1n</code> (ngày):",
           choices=[("30 phút", "30p"), ("2 giờ", "2h"), ("1 ngày", "1n"), ("3 ngày", "3n")], free=True),
        _S("choice", "Phạm vi", "Tặng cho ai? Chọn nút hoặc gõ danh sách ID cách nhau dấu phẩy (vd: <code>123456,789012</code>):",
           choices=[("Đã nạp hôm nay", "homnay"), ("Từng nạp", "all")], free=True,
           norm=lambda v: re.sub(r"[\s;,]+", ",", v.strip())),
        _MONEY("Nhập <b>tổng nạp tối thiểu</b> (không bắt buộc, bấm Bỏ qua nếu không cần):", name="Nạp tối thiểu", optional=True)],
    "yccode": [
        _TEXT("Mã", "Nhập <b>mã giftcode</b> cần thêm/gỡ yêu cầu:", norm=_upper),
        _S("choice", "Yêu cầu", "Chọn kiểu yêu cầu:",
           choices=[("💳 Nạp trong ngày", "nap"), ("📈 Tổng nạp", "tongnap"), ("🚫 Gỡ yêu cầu", "off")]),
        _MONEY("Nhập <b>số tiền yêu cầu</b> (tối thiểu 1.000đ):", when=lambda v: v.get(1) != "off")],
    # ---- Thống kê & xuất file ----
    "xuatthongke": [_RANGE()],
    "xuatls": [_ID(), _RANGE()],
    "tongket": [_ID(), _RANGE()],
    "lsuser": [_ID(), _RANGE()],
    # ---- Thông báo ----
    "send": [_TEXT("Nội dung", "Nhập <b>nội dung thông báo</b> gửi cho <b>TẤT CẢ</b> người dùng:"),
             _S("confirm", "Xác nhận", lambda v: f'Sẽ gửi cho <b>tất cả user</b>:\n<blockquote>{html.escape(v.get(0) or "")}</blockquote>')],
    "rep": [_ID("Nhập <b>ID</b> người cần nhắn riêng:"), _TEXT("Nội dung", "Nhập <b>nội dung</b> gửi cho người này:")],
    # ---- Công cụ khác ----
    "info": [_ID()], "check": [_ID()],
    "resetsdall": _CONFIRM('Reset <b>số dư của TẤT CẢ người dùng về 0</b>. Không thể hoàn tác!'),
    "resetall": _CONFIRM('Reset <b>số dư của TẤT CẢ người dùng về 0</b>. Không thể hoàn tác!'),
    "xoalsall": _CONFIRM('Xoá <b>TOÀN BỘ lịch sử cược, nạp, rút</b> của hệ thống. Không thể hoàn tác!'),
    "xoals": [_ID("Nhập <b>ID</b> cần xoá sạch lịch sử:"),
              _S("confirm", "Xác nhận", lambda v: f'Xoá <b>toàn bộ lịch sử</b> của ID <code>{html.escape(v.get(0) or "")}</code>. Không thể hoàn tác!')],
    "setname": [_TEXT("Tên", "Nhập <b>tên mới</b> hiển thị của bot:")],
    "kmnapvc": [_ID(), _MONEY("Nhập <b>số tiền khuyến mãi</b> (theo vòng cược):")],
    "lsnap": [_ID()], "lsrut": [_ID()], "lsrutky": [_ID()], "lscuoc": [_ID()], "lscode": [_ID()], "lsgift": [_ID()], "lsmua": [_ID()],
    "checktt": [_ID()],
}
# Lệnh dùng trong menu mà không cần nhập thông tin gì: bấm là chạy ngay.
_ADM_NOARG = {"stats", "top", "topnap", "resetsystem", "codenap"}

_ADM_LABEL = {it[1]: it[2] for c in _ADM_CATS for it in c[4]}

def _adm_cmd_fn(cmd):
    """Tìm hàm xử lý của lệnh đã đăng ký với CommandHandler (không cần liệt kê tay)."""
    for hs in application.handlers.values():
        for h in hs:
            if isinstance(h, CommandHandler) and cmd in h.commands:
                return h.callback
    return None

def _flow_next(flow, start):
    for j in range(start, len(flow["steps"])):
        w = flow["steps"][j]["when"]
        if w is None or w(flow["vals"]):
            return j
    return None

def _flow_args(flow):
    args = []
    for j in sorted(flow["vals"]):
        v = flow["vals"][j]
        st = flow["steps"][j]
        if v is None or st["kind"] == "confirm":
            continue
        if st["kind"] in ("text", "choice"):
            args += [t for t in v.split(" ") if t]       # giữ nguyên xuống dòng trong nội dung
        else:
            args.append(v)
    return args

def _flow_parse(step, raw):
    """Trả về (giá trị chuẩn hoá, None) hoặc (None, thông báo lỗi)."""
    raw = (raw or "").strip()
    k = step["kind"]
    if not raw:
        return None, "Bạn chưa nhập gì."
    if k == "id":
        if not re.fullmatch(r"\d{4,15}", raw):
            return None, "ID phải là dãy số (4–15 chữ số)."
        v = raw
    elif k == "money":
        try:
            n = parse_money_text(raw)
        except (ValueError, TypeError):
            return None, "Số tiền không hợp lệ. Ví dụ: 50000, 50k, 1m."
        if n == 0 or (n < 0 and not step["neg"]):
            return None, "Số tiền phải lớn hơn 0."
        v = str(n)
    elif k == "num":
        if not re.fullmatch(r"\d+(?:[.,]\d+)?", raw):
            return None, "Hãy nhập một con số."
        v = raw.replace(",", ".")
        f = float(v)
        if (step["lo"] is not None and f < step["lo"]) or (step["hi"] is not None and f > step["hi"]):
            return None, f'Giá trị phải từ {step["lo"] if step["lo"] is not None else "…"} đến {step["hi"] if step["hi"] is not None else "…"}.'
    elif k == "confirm":
        low = raw.lower()
        if low in ("yes", "y", "ok", "xacnhan", "xác nhận", "đồng ý", "dong y"):
            return "yes", None
        if low in ("no", "n", "huy", "hủy", "cancel"):
            return "no", None
        return None, "Bấm nút XÁC NHẬN hoặc Huỷ."
    else:       # text / choice
        v = raw
        if k == "choice":
            low = raw.lower()
            hit = next((val for lab, val in step["choices"] if low == val.lower() or low == lab.lower()), None)
            if hit is not None:
                v = hit
            elif not step["free"]:
                return None, "Hãy bấm một nút hoặc gõ: " + ", ".join(val for _l, val in step["choices"]) + "."
    if step["norm"]:
        v = step["norm"](v)
    return v, None

def _flow_view(ctx, flow):
    steps, i = flow["steps"], flow["i"]
    step = steps[i]
    has_when = any(s["when"] for s in steps)
    head = f'{ce("✏️")} <b>/{flow["cmd"]}</b> — {html.escape(flow["label"])}\n━━━━━━━━━━━━━━━━━━━━━\n'
    done = []
    for j in range(i):
        v = flow["vals"].get(j)
        if v is None or steps[j]["kind"] == "confirm":
            continue
        done.append(f'{ce("✅")} {steps[j]["name"]}: <code>{html.escape(v if len(v) < 80 else v[:77] + "…")}</code>')
    if done:
        head += "\n".join(done) + "\n\n"
    p = step["prompt"](flow["vals"]) if callable(step["prompt"]) else step["prompt"]
    prog = "" if has_when else f' <i>(bước {i + 1}/{len(steps)})</i>'
    body = f'{ce("❓")} {p}{prog}\n\n'
    if step["kind"] == "confirm":
        body += f'{ce("⚠️")} <b>Bấm XÁC NHẬN để thực hiện.</b>'
    elif flow["private"]:
        body += f'{ce("✍️")} <i>Gõ câu trả lời gửi cho bot, hoặc bấm nút bên dưới.</i>'
    else:
        body += f'{ce("✍️")} <i><b>Reply</b> tin nhắn này để nhập, hoặc bấm nút bên dưới.</i>'
    if i == 0 and flow.get("usage"):
        body += f'\n{ce("💡")} <i>Gõ tay cũng được: <code>{html.escape(flow["usage"])}</code></i>'
    # ---- nút ----
    opts, rows, cur = [], [], []

    def add(label, value, per_row=2):
        opts.append(value)
        cur.append(btn(label, None, callback_data=f"adm2:fv:{len(opts) - 1}"))
        if len(cur) >= per_row:
            rows.append(list(cur))
            cur.clear()

    def flush():
        if cur:
            rows.append(list(cur))
            cur.clear()

    if step["kind"] == "confirm":
        rows.append([btn("XÁC NHẬN", "✅", callback_data="adm2:fv:0")])
        opts.append("yes")
    else:
        if step["kind"] == "id" and ctx.user_data.get("adm_last_id"):
            add(f'ID gần nhất: {ctx.user_data["adm_last_id"]}', str(ctx.user_data["adm_last_id"]), 1)
        for lab, val in step["choices"]:
            add(lab, val, 3 if len(step["choices"]) > 4 else 2)
        flush()
        for q_ in step["quick"]:
            add(str(q_) if step["kind"] == "num" else q_.upper(), str(q_), 5)
        flush()
    nav = []
    if step["optional"]:
        nav.append(btn("Bỏ qua", "⏭", callback_data="adm2:fs"))
    if flow["hist"]:
        nav.append(btn("Quay lại", "🔙", callback_data="adm2:fb"))
    nav.append(btn("Huỷ", "❌", callback_data="adm2:fc"))
    rows.append(nav)
    rows.append([btn("Menu admin", "🏠", callback_data="adm2:home")])
    flow["opts"] = opts
    return head + body, InlineKeyboardMarkup(rows)

async def _flow_put(ctx, flow, text, kb=None):
    """Sửa tin nhắn của luồng; nếu không sửa được thì gửi tin mới và nhớ id mới."""
    try:
        await ctx.bot.edit_message_text(chat_id=flow["chat"], message_id=flow["mid"], text=text,
                                        reply_markup=kb, parse_mode=ParseMode.HTML)
    except Exception as e:
        if "not modified" in str(e).lower():
            return
        sent = await ctx.bot.send_message(chat_id=flow["chat"], text=text, reply_markup=kb, parse_mode=ParseMode.HTML)
        flow["mid"] = sent.message_id

async def _flow_show(ctx, flow):
    text, kb = _flow_view(ctx, flow)
    await _flow_put(ctx, flow, text, kb)

async def _adm_flow_start(update, ctx, cmd, via_cb=False):
    """Bắt đầu luồng nhập thông tin cho lệnh `cmd`. Lệnh không cần thông tin thì chạy ngay."""
    fn = _adm_cmd_fn(cmd)
    if not fn:
        return await update.effective_message.reply_text(f'{ce("❌")} Lệnh /{cmd} không tồn tại.', parse_mode=ParseMode.HTML)
    steps = _ADM_FLOW.get(cmd)
    ctx.user_data.pop("adm_flow", None)
    if not steps:
        ctx.args = []
        return await fn(_ProxyUpdate(update) if via_cb else update, ctx)
    chat = update.effective_chat
    if via_cb:
        mid = update.callback_query.message.message_id
    else:
        mid = (await update.effective_message.reply_text("⏳", parse_mode=ParseMode.HTML)).message_id
    flow = {"cmd": cmd, "label": _ADM_LABEL.get(cmd, cmd), "steps": steps, "i": 0, "vals": {}, "hist": [],
            "opts": [], "ts": time.time(), "chat": chat.id, "mid": mid, "private": chat.type == "private",
            "usage": _ADM_USAGE.get(cmd, "")}
    flow["i"] = _flow_next(flow, 0)
    ctx.user_data["adm_flow"] = flow
    await _flow_show(ctx, flow)

async def _flow_cancel(update, ctx, flow, toast=None):
    ctx.user_data.pop("adm_flow", None)
    text, kb = _adm_home(flow["private"])
    await _flow_put(ctx, flow, text, kb)

async def _flow_advance(update, ctx, flow, val, via_cb):
    """Lưu giá trị của bước hiện tại rồi sang bước kế / chạy lệnh."""
    i = flow["i"]
    step = flow["steps"][i]
    flow["vals"][i] = val
    flow["ts"] = time.time()
    if step["kind"] == "id" and val:
        ctx.user_data["adm_last_id"] = val
    flow["hist"].append(i)
    nxt = _flow_next(flow, i + 1)
    if nxt is not None:
        flow["i"] = nxt
        return await _flow_show(ctx, flow)
    # ---- đủ thông tin: chạy lệnh ----
    ctx.user_data.pop("adm_flow", None)
    args = _flow_args(flow)
    shown = " ".join(args)
    shown = shown if len(shown) < 120 else shown[:117] + "…"
    await _flow_put(ctx, flow,
                    f'{ce("⚙️")} Đang chạy <code>/{flow["cmd"]}{" " + html.escape(shown) if shown else ""}</code> …',
                    InlineKeyboardMarkup([[btn("Làm lại lệnh này", "🔁", callback_data=f'adm2:q:{flow["cmd"]}'),
                                           btn("Menu admin", "🏠", callback_data="adm2:home")]]))
    fn = _adm_cmd_fn(flow["cmd"])
    ctx.args = args
    try:
        await fn(_ProxyUpdate(update) if via_cb else update, ctx)
    except ApplicationHandlerStop:
        raise
    except Exception as e:
        traceback.print_exc()
        try:
            await ctx.bot.send_message(flow["chat"], f"❌ Lỗi khi chạy lệnh: {html.escape(str(e))[:300]}", parse_mode=ParseMode.HTML)
        except Exception:
            pass

async def adm_flow_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Nhận câu trả lời gõ tay của admin cho bước đang chờ."""
    flow = ctx.user_data.get("adm_flow")
    msg, user, chat = update.effective_message, update.effective_user, update.effective_chat
    if not flow or not msg or not msg.text or not user or user.id not in ADMIN_IDS or not chat:
        return
    if time.time() - flow["ts"] > _FLOW_TTL:
        ctx.user_data.pop("adm_flow", None)
        return
    if chat.id != flow["chat"]:
        return
    is_reply = bool(msg.reply_to_message and msg.reply_to_message.message_id == flow["mid"])
    if not (flow["private"] or is_reply):
        return
    text = msg.text.strip()
    if re.sub(r'^[^\w]+', '', text).strip().upper() == "ADMIN":      # bấm nút ADMIN: bỏ phiên nhập, mở lại menu
        ctx.user_data.pop("adm_flow", None)
        return
    if text.lower() in ("huy", "hủy", "cancel"):
        ctx.user_data.pop("adm_flow", None)
        await msg.reply_text(f'{ce("✅")} Đã huỷ thao tác.', parse_mode=ParseMode.HTML)
        raise ApplicationHandlerStop
    step = flow["steps"][flow["i"]]
    val, err = _flow_parse(step, text)
    if err:
        await msg.reply_text(f'{ce("❌")} {html.escape(err)}', parse_mode=ParseMode.HTML)
        raise ApplicationHandlerStop
    if step["kind"] == "confirm" and val == "no":
        ctx.user_data.pop("adm_flow", None)
        await msg.reply_text(f'{ce("🚫")} Đã huỷ thao tác.', parse_mode=ParseMode.HTML)
        raise ApplicationHandlerStop
    await _flow_advance(update, ctx, flow, val, False)
    raise ApplicationHandlerStop

async def _adm_flow_callback(update, ctx, act, parts):
    """Xử lý các nút của luồng: fv (chọn giá trị), fs (bỏ qua), fb (quay lại), fc (huỷ)."""
    q = update.callback_query
    flow = ctx.user_data.get("adm_flow")
    if (not flow or q.message.message_id != flow["mid"] or q.message.chat_id != flow["chat"]
            or time.time() - flow["ts"] > _FLOW_TTL):
        ctx.user_data.pop("adm_flow", None)
        return await q.answer("Phiên nhập đã hết hạn. Hãy mở lại lệnh từ menu admin.", show_alert=True)
    if act == "fc":
        await q.answer("Đã huỷ.")
        return await _flow_cancel(update, ctx, flow)
    if act == "fb":
        await q.answer()
        if flow["hist"]:
            back = flow["hist"].pop()
            for j in [k for k in flow["vals"] if k >= back]:
                flow["vals"].pop(j, None)
            flow["i"] = back
        return await _flow_show(ctx, flow)
    step = flow["steps"][flow["i"]]
    if act == "fs":
        if not step["optional"]:
            return await q.answer()
        await q.answer()
        return await _flow_advance(update, ctx, flow, None, True)
    # fv
    try:
        raw = flow["opts"][int(parts[2])]
    except (IndexError, ValueError):
        return await q.answer("Nút đã cũ, hãy bấm lại.", show_alert=True)
    val, err = _flow_parse(step, raw)
    if err:
        return await q.answer(err, show_alert=True)
    if step["kind"] == "confirm" and val == "no":
        await q.answer("Đã huỷ.")
        return await _flow_cancel(update, ctx, flow)
    await q.answer("⚡ Đang chạy…" if flow["i"] == len(flow["steps"]) - 1 else None)
    return await _flow_advance(update, ctx, flow, val, True)

def _adm_ok(uid):
    return uid in ADMIN_IDS and not is_admin_banned(uid)

def _adm_runner(key):
    return {
        "baotri": baotri_cmd, "baotriht": baotri_he_thong_cmd, "trangthai": trangthai_cmd,
        "tatroom": tatroom_cmd, "moroom": moroom_cmd, "trangthairoom": trangthairoom_cmd,
        "all": all_user, "dsban": dsban_cmd, "topsodu": topsodu_cmd, "topcuoc": topcuoc_cmd,
        "dsnap": dsnap_cmd, "dsrut": dsrut_cmd, "lsnaptatca": lsnaptatca_cmd, "lsruttatca": lsruttatca_cmd, "lsrut": lsrut_cmd, "dsadminweb": dsadminweb_cmd, "lsrutky": lsrut_report_cmd,
        "soduall": soduall_cmd, "hisall": history_all_admin, "dskm": dskm_cmd, "kmgio": kmgio_cmd,
        "homnay": homnay_cmd, "taogift": gift_flow_start, "dsgift": dsgift_cmd, "thongke": dashboard_cmd,
        "tong": tong_cmd, "xuatthongke": xuatthongke_cmd, "xuatnapall": xuatnapall_cmd,
        "xuatrutall": xuatrutall_cmd, "xuathethong": xuathethong_cmd, "resetthongke": resetthongke_cmd,
        "adminhelp": admin_help_cmd, "dsnaphomnay": dsnaphomnay_cmd,
    }.get(key)

def _adm_ep_state():
    """Mô tả lệnh ép Tài Xỉu 3D đang chờ + phiên sẽ áp dụng."""
    nxt = TX3D.round_id if TX3D.phase == "bet" else TX3D.round_id + 1
    f = TX3D.force
    if not f:
        return nxt, "không có"
    return nxt, (" ".join(map(str, f["dice"])) if f["dice"] else ("TÀI" if f["kind"] == "tai" else "XỈU"))

def _adm_ep_rows():
    return [[btn("Ép TÀI", "🔵", callback_data="adm2:ep:t"), btn("Ép XỈU", "🔴", callback_data="adm2:ep:x")],
            [btn("Huỷ ép", "🚫", callback_data="adm2:ep:off")]]

def _adm_home(private=False):
    def sc(sql):
        return int(_sum(sql) or 0)
    pend_w = sc("SELECT COUNT(*) FROM withdraw_history WHERE status='pending'")
    pend_d = sc("SELECT COUNT(*) FROM deposit_history WHERE status='pending'")
    mt_games = sum(1 for v in ADMIN_GAMES.values() if check_mt(v[0]))
    room_off = bool(GROUP_IDS) and all(_is_room_muted(g) for g in GROUP_IDS)
    text = (
        f'{ce("🛠")} <b>TRUNG TÂM QUẢN TRỊ</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("👋")} Bảng điều khiển dành riêng cho <b>Admin</b>. Chọn một danh mục bên dưới để xem toàn bộ lệnh.\n\n'
        f'{ce("📌")} <b>CÁCH DÙNG</b>\n'
        f'• {ce("⚡")} <b>Nút ⚡</b>: bấm là chạy ngay, không cần nhập gì thêm.\n'
        f'• {ce("✏️")} <b>Nút ✏️</b>: bấm vào lệnh, bot sẽ hỏi từng thông tin (ID, số tiền, lựa chọn…). Bạn chỉ cần nhập hoặc bấm nút, bot tự chạy lệnh — <b>không cần gõ lệnh thủ công</b>.\n'
        f'• Các lệnh dùng được cả trong chat riêng lẫn trong nhóm (trong nhóm: reply tin nhắn của bot để nhập).\n\n'
        f'{ce("📊")} <b>TÌNH TRẠNG NHANH</b>\n'
        f'• {ce("📤")} Rút chờ duyệt: <b>{pend_w}</b>   {ce("📥")} Nạp chờ: <b>{pend_d}</b>\n'
        f'• {ce("🎮")} Game đang bảo trì: <b>{mt_games}/{len(ADMIN_GAMES)}</b>\n'
        f'• {ce("🏠")} Room: <b>{"ĐANG TẮT" if room_off else "ĐANG BẬT"}</b>\n'
        f'• {ce("🛡")} Bảo trì hệ thống: <b>{"BẬT" if is_system_maintenance() else "TẮT"}</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━'
    )
    if private:
        _n, _cur = _adm_ep_state()
        text += (f'\n{ce("🎲")} <b>ÉP KẾT QUẢ TÀI XỈU 3D</b> — phiên <b>#{_n}</b>: <b>{_cur}</b>\n'
                 f'<i>Bấm Ép TÀI / Ép XỈU: kết quả phiên đó chắc chắn về bên đã chọn (kể cả khi có người chơi thật cược).</i>')
    rows, cur = [], []
    for key, em, title, _d, _items in _ADM_CATS:
        cur.append(btn(title.title(), em, callback_data=f"adm2:cat:{key}"))
        if len(cur) == 2:
            rows.append(cur)
            cur = []
    if cur:
        rows.append(cur)
    # Thao tác nhanh: các việc admin làm nhiều nhất, bấm là bot hỏi thông tin luôn.
    rows.append([btn("— THAO TÁC NHANH —", None, callback_data="adm2:noop")])
    for pair in (
        (("Hồ sơ user", "👤", "q:fulluser"), ("Cộng tiền", "➕", "q:add")),
        (("Trừ tiền", "➖", "q:sub"), ("Khoá tài khoản", "🔒", "q:ban")),
        (("Mở khoá", "🔓", "q:unban"), ("Reset hoàn trả", "🎁", "q:resethoanall")),
        (("Nạp chờ duyệt", "📥", "run:dsnap"), ("Rút chờ duyệt", "📤", "run:dsrut")),
    ):
        rows.append([btn(t, e, callback_data=f"adm2:{cb}") for t, e, cb in pair])
    if private:
        rows += _adm_ep_rows()
    rows.append([btn("Hướng dẫn dạng chữ", "📜", callback_data="adm2:help"), btn("Làm mới", "🔄", callback_data="adm2:home")])
    rows.append([btn("Đóng", "❌", callback_data="adm2:close")])
    return text, InlineKeyboardMarkup(rows)

def _adm_cat(key):
    _k, em, title, desc, items = _ADM_CAT_MAP[key]
    lines = [f'{ce(em)} <b>{title}</b>', '━━━━━━━━━━━━━━━━━━━━━', f'<i>{desc}</i>', '']
    run_btns, use_btns = [], []
    for idx, (kind, cmd, label, rkey, _usage, _ex) in enumerate(items):
        steps = _ADM_FLOW.get(cmd) if kind == "use" else None
        if kind == "run" or not steps:
            lines.append(f'{ce("⚡")} <code>/{cmd}</code> — {label}')
            if kind == "run":
                run_btns.append(btn(f"/{cmd}", "⚡", callback_data=f"adm2:run:{rkey}"))
            else:
                run_btns.append(btn(f"/{cmd}", "⚡", callback_data=f"adm2:use:{key}:{idx}"))
        else:
            ico = "⚠️" if all(s_["kind"] == "confirm" for s_ in steps) else "✏️"
            lines.append(f'{ce(ico)} <code>/{cmd}</code> — {label}')
            use_btns.append(btn(f"/{cmd}", ico, callback_data=f"adm2:use:{key}:{idx}"))
    lines += ['', f'{ce("💡")} <i>⚡ chạy ngay · ✏️ bấm để bot hỏi thông tin rồi tự chạy · ⚠️ có bước xác nhận</i>']
    rows = []
    for group in (run_btns, use_btns):
        for i in range(0, len(group), 2):
            rows.append(group[i:i + 2])
    rows.append([btn("Menu admin", "🏠", callback_data="adm2:home")])
    return "\n".join(lines), InlineKeyboardMarkup(rows)

@admin_only
async def admin_panel_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.pop("adm_flow", None)
    text, kb = _adm_home(update.effective_chat.type == "private")
    await update.effective_message.reply_text(text, reply_markup=kb, parse_mode=ParseMode.HTML)

async def admin_panel_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not _adm_ok(q.from_user.id):
        return await q.answer("Bạn không có quyền.", show_alert=True)
    parts = (q.data or "").split(":")
    act = parts[1] if len(parts) > 1 else ""
    try:
        if act == "ep" and len(parts) > 2:
            if q.message.chat.type != "private":      # không để lộ thao tác ép trong nhóm
                return await q.answer("Chỉ dùng được trong chat riêng với bot.", show_alert=True)
            mode = parts[2]
            if mode == "off":
                TX3D.force = None
                toast = "Đã huỷ ép kết quả."
            elif mode in ("t", "x"):
                TX3D.force = {"dice": None, "kind": "tai" if mode == "t" else "xiu", "by": q.from_user.id}
                toast = f"Đã ép {'TÀI' if mode == 't' else 'XỈU'} cho phiên #{_adm_ep_state()[0]}."
            else:
                return await q.answer()
            await q.answer(toast, show_alert=True)
            text, kb = _adm_home(True)
            return await safe_edit(q, text, kb)
        if act == "home":
            await q.answer()
            text, kb = _adm_home(q.message.chat.type == "private")
            return await safe_edit(q, text, kb)
        if act == "cat" and len(parts) > 2 and parts[2] in _ADM_CAT_MAP:
            await q.answer()
            text, kb = _adm_cat(parts[2])
            return await safe_edit(q, text, kb)
        if act == "noop":
            return await q.answer()
        if act in ("fv", "fs", "fb", "fc"):
            return await _adm_flow_callback(update, ctx, act, parts)
        if act in ("use", "q"):
            if act == "use" and len(parts) > 3 and parts[2] in _ADM_CAT_MAP:
                cmd = _ADM_CAT_MAP[parts[2]][4][int(parts[3])][1]
            elif act == "q" and len(parts) > 2:
                cmd = parts[2]
            else:
                return await q.answer()
            if cmd not in _ADM_LABEL:
                return await q.answer("Lệnh không tồn tại.", show_alert=True)
            await q.answer()
            return await _adm_flow_start(update, ctx, cmd, via_cb=True)
        if act == "help":
            await q.answer()
            return await admin_help_cmd(_ProxyUpdate(update), ctx)
        if act == "close":
            await q.answer()
            return await q.message.delete()
        if act == "run" and len(parts) > 2:
            key, _, arg = parts[2].partition("|")
            fn = _adm_runner(key) or _adm_cmd_fn(key)
            if not fn:
                return await q.answer("Lệnh không tồn tại.", show_alert=True)
            await q.answer("⚡ Đang chạy…")
            ctx.args = [arg] if arg else []
            return await fn(_ProxyUpdate(update), ctx)
        await q.answer()
    except Exception as e:
        traceback.print_exc()
        try:
            await q.message.reply_text(f"❌ Lỗi khi chạy lệnh: {html.escape(str(e))[:300]}", parse_mode=ParseMode.HTML)
        except Exception:
            pass


# ============================================================
# ADMIN: NGƯỜI NẠP HÔM NAY / TẶNG CODE THỦ CÔNG / YÊU CẦU NHẬP CODE
#  /dsnaphomnay                         — danh sách người đã nạp thành công hôm nay
#  /tangcodenap [giá trị] [vòng cược] [hạn] [homnay|all|id1,id2] [nạp tối thiểu]
#  /yccode [mã] nap|tongnap [số tiền] | off   — thêm / gỡ yêu cầu nhập code
# ============================================================
_TGN_PENDING = {}   # token -> thông tin đợt tặng đang chờ admin xác nhận

def _depositors_today_sync():
    rows = query(
        "SELECT d.user_id, COUNT(*), COALESCE(SUM(d.amount),0), MAX(d.time), MAX(u.name) "
        "FROM deposit_history d LEFT JOIN users u ON u.user_id=d.user_id "
        "WHERE d.status='success' AND right(d.\"time\",10)=%s "
        "GROUP BY d.user_id ORDER BY SUM(d.amount) DESC", (get_vietnam_date(),)) or []
    return [(int(r[0]), int(r[1]), int(r[2]), str(r[3] or ""), str(r[4] or "")) for r in rows]

def _depositors_all_sync(min_amount):
    rows = query(
        "SELECT user_id, COALESCE(SUM(amount),0) FROM deposit_history WHERE status='success' "
        "GROUP BY user_id HAVING COALESCE(SUM(amount),0) >= %s ORDER BY SUM(amount) DESC", (int(min_amount),)) or []
    return [(int(r[0]), int(r[1])) for r in rows]

@admin_only
async def dsnaphomnay_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    rows = await asyncio.to_thread(_depositors_today_sync)
    today = get_vietnam_date()
    if not rows:
        return await msg.reply_text(
            f'{ce("📥")} Hôm nay <code>{today}</code> chưa có ai nạp tiền thành công.',
            parse_mode=ParseMode.HTML)
    total = sum(r[2] for r in rows)
    orders = sum(r[1] for r in rows)
    head = (
        f'{ce("📥")} <b>NGƯỜI NẠP THÀNH CÔNG HÔM NAY</b> <code>{today}</code>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("👥")} Số người: <b>{len(rows)}</b> · {ce("🧾")} Số lệnh: <b>{orders}</b>\n'
        f'{ce("💰")} Tổng nạp: <b>{fmt_money(total)}đ</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n')
    cache, lines = {}, []
    for i, (uid, n, amt, last, bank_name) in enumerate(rows, 1):
        name = await _telegram_name(ctx.bot, uid, cache) if i <= 40 else ""
        name = name or bank_name or "—"
        lines.append(
            f'{ce("🥇") if i == 1 else ce("🥈") if i == 2 else ce("🥉") if i == 3 else ce("👤")} '
            f'<b>{i}.</b> <code>{uid}</code> · {html.escape(name)}\n'
            f'    {ce("💵")} <b>{fmt_money(amt)}đ</b> · {n} lệnh · {ce("⏰")} <i>{html.escape(last)}</i>')
    foot = (f'\n━━━━━━━━━━━━━━━━━━━━━\n{ce("🎁")} Tặng code cho nhóm này: '
            f'<code>/tangcodenap 20k 1 1n homnay</code>')
    chunks, cur = [], head
    for ln in lines:
        if len(cur) + len(ln) + 2 > 3800:
            chunks.append(cur)
            cur = ""
        cur += ln + "\n"
    chunks.append(cur + foot)
    for c in chunks:
        await msg.reply_text(c, parse_mode=ParseMode.HTML)

def _tgn_usage():
    return (
        f'{ce("🎁")} <b>TẶNG CODE THỦ CÔNG CHO NGƯỜI ĐÃ NẠP</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("✍️")} <code>/tangcodenap [giá trị] [vòng cược] [hạn] [phạm vi] [nạp tối thiểu]</code>\n\n'
        f'{ce("💰")} <b>giá trị</b>: <code>20000</code> hoặc <code>20k</code>\n'
        f'{ce("🎯")} <b>vòng cược</b>: <code>1</code> = x1 (0 = không cần cược)\n'
        f'{ce("⏰")} <b>hạn</b>: <code>1n</code> (ngày) · <code>2h</code> (giờ) · <code>30p</code> (phút)\n'
        f'{ce("👥")} <b>phạm vi</b>: <code>homnay</code> (đã nạp hôm nay, mặc định) · <code>all</code> (từng nạp) · '
        f'<code>id1,id2,id3</code> (chỉ định)\n'
        f'{ce("💳")} <b>nạp tối thiểu</b> (tuỳ chọn): chỉ tặng người có tổng nạp từ mức này\n\n'
        f'{ce("💡")} <b>VD:</b>\n'
        f'<code>/tangcodenap 20k 1 1n homnay</code>\n'
        f'<code>/tangcodenap 50k 2 3n homnay 500k</code>\n'
        f'<code>/tangcodenap 10k 1 1n 123456,789012</code>\n\n'
        f'{ce("📌")} Mỗi người nhận 1 code riêng (chỉ họ dùng được), bot gửi riêng cho từng người. '
        f'Có bước xác nhận trước khi gửi.')

@admin_only
async def tangcodenap_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    args = ctx.args or []
    if len(args) < 3:
        return await msg.reply_text(_tgn_usage(), parse_mode=ParseMode.HTML)
    try:
        reward = parse_money_text(args[0])
        wager = int(args[1].lower().replace("x", "").strip())
        minutes = parse_duration(args[2])
        scope = (args[3].lower() if len(args) > 3 else "homnay")
        min_amt = parse_money_text(args[4]) if len(args) > 4 else 0
    except (ValueError, TypeError):
        return await msg.reply_text(f'{ce("❌")} Tham số không hợp lệ.\n\n' + _tgn_usage(), parse_mode=ParseMode.HTML)
    if reward < 1000 or reward > 100_000_000:
        return await msg.reply_text(f'{ce("❌")} Giá trị code từ 1.000đ đến 100.000.000đ.', parse_mode=ParseMode.HTML)
    if wager < 0 or wager > 100:
        return await msg.reply_text(f'{ce("❌")} Số vòng cược từ 0 đến 100.', parse_mode=ParseMode.HTML)
    if not minutes or minutes <= 0:
        return await msg.reply_text(f'{ce("❌")} Hạn dùng không hợp lệ (VD: <code>1n</code>, <code>2h</code>, <code>30p</code>).', parse_mode=ParseMode.HTML)

    banned = {int(r[0]) for r in (query("SELECT user_id FROM banned") or [])}
    if scope in ("homnay", "today", "hn"):
        scope_txt = "đã nạp thành công HÔM NAY"
        rows = await asyncio.to_thread(_depositors_today_sync)
        if min_amt:
            # mức tối thiểu tính theo TỔNG nạp từ trước đến nay
            targets = [r[0] for r in rows if total_deposited(r[0]) >= min_amt]
        else:
            targets = [r[0] for r in rows]
    elif scope in ("all", "tatca"):
        scope_txt = "từng nạp thành công"
        rows = await asyncio.to_thread(_depositors_all_sync, max(min_amt, 1))
        targets = [r[0] for r in rows]
    else:
        scope_txt = "do admin chỉ định"
        ids = [int(x) for x in re.split(r"[,\s;]+", scope) if x.strip().isdigit()]
        if not ids:
            return await msg.reply_text(f'{ce("❌")} Phạm vi không hợp lệ.\n\n' + _tgn_usage(), parse_mode=ParseMode.HTML)
        exist = {int(r[0]) for r in (query("SELECT user_id FROM users WHERE user_id = ANY(%s)", (ids,)) or [])}
        targets = [i for i in dict.fromkeys(ids) if i in exist]
    targets = [t for t in targets if t not in banned]
    if not targets:
        return await msg.reply_text(f'{ce("📭")} Không có người nhận phù hợp với phạm vi này.', parse_mode=ParseMode.HTML)
    if len(targets) > 500:
        return await msg.reply_text(f'{ce("❌")} Tối đa 500 người mỗi đợt (đang chọn {len(targets)}). Hãy lọc thêm bằng mức nạp tối thiểu.', parse_mode=ParseMode.HTML)

    if len(_TGN_PENDING) > 50:
        _TGN_PENDING.clear()
    token = gen_code()
    _TGN_PENDING[token] = {"admin": update.effective_user.id, "targets": targets, "reward": reward,
                           "wager": wager, "minutes": minutes, "ts": time.time()}
    kb = InlineKeyboardMarkup([[btn("XÁC NHẬN GỬI", "✅", callback_data=f"tgn:ok:{token}"),
                                btn("HUỶ", "❌", callback_data=f"tgn:no:{token}")]])
    await msg.reply_text(
        f'{ce("⚠️")} <b>XÁC NHẬN TẶNG CODE</b>\n━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("👥")} Người nhận: <b>{len(targets)}</b> ({scope_txt})\n'
        f'{ce("💰")} Mỗi code: <b>{fmt_money(reward)}đ</b>\n'
        f'{ce("🎯")} Vòng cược: <b>x{wager}</b>\n'
        f'{ce("⏰")} Hạn dùng: <b>{fmt_duration(minutes)}</b>\n'
        + (f'{ce("💳")} Tổng nạp tối thiểu: <b>{fmt_money(min_amt)}đ</b>\n' if min_amt else '')
        + f'{ce("📊")} Tổng giá trị tặng: <b>{fmt_money(reward * len(targets))}đ</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'<i>Mỗi người nhận 1 code riêng, bot gửi tin nhắn riêng cho từng người.</i>',
        reply_markup=kb, parse_mode=ParseMode.HTML)

def _tgn_create_sync(info, admin_id):
    expiry = get_vietnam_time() + timedelta(minutes=info["minutes"])
    out = []
    for uid in info["targets"]:
        try:
            code = gen_gift_code("NAP")
            query("INSERT INTO giftcodes (code, ctype, reward, wager, expiry, require_deposit, required_amount, "
                  "bound_user, used, created_by, created_at) VALUES (%s,'NAP',%s,%s,%s,0,0,%s,0,%s,%s)",
                  (code, info["reward"], info["wager"], expiry, uid, admin_id, get_vietnam_datetime_db()))
            out.append((uid, code))
        except Exception as e:
            print(f"[tangcodenap] lỗi tạo code cho {uid}: {e}")
    return out, expiry

async def tangnap_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id not in ADMIN_IDS or is_admin_banned(q.from_user.id):
        return await q.answer("Bạn không có quyền.", show_alert=True)
    parts = (q.data or "").split(":")
    if len(parts) < 3:
        return await q.answer()
    act, token = parts[1], parts[2]
    info = _TGN_PENDING.pop(token, None)
    if not info:
        return await q.answer("Đợt tặng này đã xử lý hoặc hết hạn.", show_alert=True)
    if act == "no":
        await q.answer("Đã huỷ.")
        return await q.edit_message_text(f'{ce("🚫")} Đã huỷ đợt tặng code.', parse_mode=ParseMode.HTML)
    if time.time() - info["ts"] > 900:
        return await q.answer("Đợt tặng đã quá 15 phút, hãy tạo lại.", show_alert=True)
    await q.answer("Đang tạo và gửi code…")
    await q.edit_message_text(f'{ce("⌛")} Đang tạo code và gửi cho <b>{len(info["targets"])}</b> người…', parse_mode=ParseMode.HTML)
    created, expiry = await asyncio.to_thread(_tgn_create_sync, info, q.from_user.id)
    sent, failed = 0, []
    for uid, code in created:
        try:
            await ctx.bot.send_message(
                uid,
                f'{ce("🎁")} <b>QUÀ TẶNG TỪ ADMIN</b> {ce("🎉")}\n'
                f'━━━━━━━━━━━━━━━━━━━━━\n'
                f'Cảm ơn bạn đã nạp tiền và đồng hành cùng hệ thống!\n\n'
                f'{ce("🔑")} <b>Mã code:</b> <code>{code}</code>\n'
                f'{ce("💰")} <b>Giá trị:</b> <code>{fmt_money(info["reward"])}đ</code>\n'
                f'{ce("🎯")} <b>Vòng cược:</b> <code>x{info["wager"]}</code>\n'
                f'{ce("⏰")} <b>Hạn dùng:</b> <code>{expiry.strftime("%d/%m/%Y %H:%M")}</code>\n'
                f'━━━━━━━━━━━━━━━━━━━━━\n'
                f'{ce("📌")} Nhập bằng <code>/code {code}</code> hoặc gửi thẳng mã cho bot. Code chỉ dùng được cho tài khoản của bạn.',
                parse_mode=ParseMode.HTML)
            sent += 1
        except Exception:
            failed.append(uid)
            query("DELETE FROM giftcodes WHERE code=%s AND used=0", (code,))   # không để code mồ côi
        await asyncio.sleep(0.06)
    miss = len(info["targets"]) - len(created)
    text = (f'{ce("✅")} <b>ĐÃ TẶNG CODE XONG</b>\n━━━━━━━━━━━━━━━━━━━━━\n'
            f'{ce("📤")} Gửi thành công: <b>{sent}</b>/{len(info["targets"])}\n'
            f'{ce("💰")} Giá trị mỗi code: <b>{fmt_money(info["reward"])}đ</b> · x{info["wager"]} · {fmt_duration(info["minutes"])}\n')
    if failed:
        text += (f'{ce("⚠️")} Không nhắn được ({len(failed)}, đã thu hồi code): '
                 f'<code>{", ".join(map(str, failed[:30]))}</code>{" …" if len(failed) > 30 else ""}\n')
    if miss > 0:
        text += f'{ce("❌")} Lỗi tạo code: {miss} người.\n'
    await q.message.reply_text(text, parse_mode=ParseMode.HTML)

@admin_only
async def yccode_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    args = ctx.args or []
    usage = (
        f'{ce("🔑")} <b>THÊM YÊU CẦU NHẬP CODE</b>\n━━━━━━━━━━━━━━━━━━━━━\n'
        f'<code>/yccode [mã] nap [số tiền]</code> — phải nạp đủ số tiền <b>trong ngày</b> mới nhập được\n'
        f'<code>/yccode [mã] tongnap [số tiền]</code> — phải có <b>tổng nạp</b> đủ mức này\n'
        f'<code>/yccode [mã] off</code> — gỡ toàn bộ yêu cầu\n'
        f'<code>/yccode [mã]</code> — xem yêu cầu hiện tại\n\n'
        f'{ce("💡")} VD: <code>/yccode XOCLO88-TRIAN-ABC1234 nap 100k</code>')
    if not args:
        return await msg.reply_text(usage, parse_mode=ParseMode.HTML)
    code = args[0].strip().upper()
    row = query("SELECT ctype, reward, used, require_deposit, required_amount, COALESCE(require_total_dep,0) "
                "FROM giftcodes WHERE code=%s", (code,)) or []
    if not row:
        return await msg.reply_text(f'{ce("❌")} Không tìm thấy giftcode <code>{html.escape(code)}</code>.', parse_mode=ParseMode.HTML)
    if row[0][2]:
        return await msg.reply_text(f'{ce("❌")} Code này đã được sử dụng, không thể đổi yêu cầu.', parse_mode=ParseMode.HTML)
    if len(args) >= 2:
        mode = args[1].lower()
        if mode == "off":
            query("UPDATE giftcodes SET require_deposit=0, required_amount=0, require_total_dep=0 WHERE code=%s", (code,))
        elif mode in ("nap", "tongnap"):
            try:
                amount = parse_money_text(args[2])
                if amount < 1000:
                    raise ValueError
            except (IndexError, ValueError, TypeError):
                return await msg.reply_text(f'{ce("❌")} Thiếu hoặc sai số tiền (tối thiểu 1.000đ).\n\n' + usage, parse_mode=ParseMode.HTML)
            if mode == "nap":
                query("UPDATE giftcodes SET require_deposit=1, required_amount=%s WHERE code=%s", (amount, code))
            else:
                query("UPDATE giftcodes SET require_total_dep=%s WHERE code=%s", (amount, code))
        else:
            return await msg.reply_text(usage, parse_mode=ParseMode.HTML)
        row = query("SELECT ctype, reward, used, require_deposit, required_amount, COALESCE(require_total_dep,0) "
                    "FROM giftcodes WHERE code=%s", (code,)) or row
    ctype, reward, _used, req_dep, req_amt, req_total = row[0]
    await msg.reply_text(
        f'{ce("🔑")} <b>YÊU CẦU NHẬP CODE</b>\n━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("🎟")} Mã: <code>{html.escape(code)}</code> · {html.escape(GIFT_TYPES.get(ctype, {}).get("name", str(ctype)))}\n'
        f'{ce("💰")} Giá trị: <code>{fmt_money(int(reward or 0))}đ</code>\n'
        f'{ce("💳")} Nạp trong ngày: <b>{fmt_money(int(req_amt or 0)) + "đ" if req_dep else "Không yêu cầu"}</b>\n'
        f'{ce("📈")} Tổng nạp tối thiểu: <b>{fmt_money(int(req_total or 0)) + "đ" if req_total else "Không yêu cầu"}</b>' +
        (f'\n{ce("🚫")} Code Tân Thủ: chỉ tài khoản chưa có lịch sử nạp/rút' if ctype == "TANTHU" else ''),
        parse_mode=ParseMode.HTML)


# ============================================================
# ADMIN: RESET TOÀN BỘ TIỀN HOÀN TRẢ CỦA 1 NGƯỜI DÙNG (KHÔNG ĐỤNG TỚI NGƯỜI KHÁC)
#  /resethoanall            — bot hỏi ID, rồi hỏi loại (ngày / tuần / cả hai), rồi xác nhận
#  /resethoanall [ID] [ngay|tuan|all]  — gõ thẳng cũng được (mặc định all)
#  Xoá về 0: (1) khoản hoàn ĐÃ CHỐT đang chờ nhận; (2) phần ĐANG TÍCH LUỸ chưa chốt (hôm nay / tuần này).
#  Số dư, lịch sử, thống kê cược và khoản đã nhận trước đó KHÔNG đổi.
# ============================================================
_RHALL_DONE = set()
_RH_LABEL = {"all": "HOÀN NGÀY + HOÀN TUẦN", "ngay": "HOÀN NGÀY", "tuan": "HOÀN TUẦN"}

def _rh_types(period):
    if period == "ngay":
        return ["cuoc_ngay", "thua_ngay"]
    if period == "tuan":
        return ["cuoc_tuan", "thua_tuan"]
    return ["cuoc_ngay", "thua_ngay", "cuoc_tuan", "thua_tuan"]

def _rh_preview_sync(uid, period):
    """(số khoản đã chốt chờ nhận, tổng tiền đã chốt, tổng tiền đang tích luỹ chưa chốt)"""
    pr = query("SELECT COUNT(*), COALESCE(SUM(amount),0) FROM rewards "
               "WHERE user_id=%s AND claimed=0 AND amount>0 AND rtype = ANY(%s)",
               (uid, _rh_types(period))) or [(0, 0)]
    today = get_vietnam_time().date()
    ws = week_start(today)
    we = ws + timedelta(days=6)
    live = 0
    if period in ("ngay", "all"):
        b, w = reward_stats(uid, today, today, "ngay")
        live += reward_calc("cuoc_ngay", b, w)[1] + reward_calc("thua_ngay", b, w)[1]
    if period in ("tuan", "all"):
        b, w = reward_stats(uid, ws, we, "tuan")
        live += reward_calc("cuoc_tuan", b, w)[1] + reward_calc("thua_tuan", b, w)[1]
    return int(pr[0][0] or 0), int(pr[0][1] or 0), int(live)

def _rh_apply_sync(uid, period):
    """Trả về (số khoản đã xoá, tổng tiền đã xoá) hoặc None nếu lỗi DB."""
    rows = query(
        "WITH old AS (SELECT id, amount FROM rewards WHERE user_id=%s AND claimed=0 AND amount>0 "
        "AND rtype = ANY(%s) FOR UPDATE) "
        "UPDATE rewards r SET amount=0, claimed=1, claimed_at=%s FROM old WHERE r.id=old.id "
        "RETURNING old.amount",
        (uid, _rh_types(period), get_vietnam_datetime_db()))
    if rows is None:
        return None
    # Chốt mốc cho phần đang tích luỹ: từ giờ doanh số hoàn trả của người này tính lại từ 0.
    since = get_vietnam_time().date() - timedelta(days=8)
    for scope in (["ngay", "tuan"] if period == "all" else [period]):
        ok = query(
            "INSERT INTO reward_base(user_id, day, scope, bet, win) "
            "SELECT user_id, day, %s, bet, win FROM bet_daily WHERE user_id=%s AND day>=%s "
            "ON CONFLICT (user_id, day, scope) DO UPDATE SET bet=EXCLUDED.bet, win=EXCLUDED.win "
            "RETURNING 1", (scope, uid, since))
        if ok is None:
            return None
    return len(rows), sum(int(r[0] or 0) for r in rows)

@admin_only
async def resethoanall_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    args = ctx.args or []
    if not args:                         # gõ lệnh trống -> bot hỏi ID rồi hỏi loại
        return await _adm_flow_start(update, ctx, "resethoanall")
    try:
        target = int(args[0])
    except ValueError:
        return await msg.reply_text(
            f'{ce("❌")} ID không hợp lệ. Gõ <code>/resethoanall</code> rồi nhập ID, '
            f'hoặc <code>/resethoanall [ID] [ngay|tuan|all]</code>.', parse_mode=ParseMode.HTML)
    period = (args[1].lower() if len(args) > 1 else "all")
    if period not in _RH_LABEL:
        return await msg.reply_text(
            f'{ce("❌")} Loại phải là <code>ngay</code>, <code>tuan</code> hoặc <code>all</code>.',
            parse_mode=ParseMode.HTML)
    if not (query("SELECT 1 FROM users WHERE user_id=%s", (target,)) or []):
        return await msg.reply_text(f'{ce("❌")} Không tìm thấy ID <code>{target}</code>.', parse_mode=ParseMode.HTML)
    items, pend_total, live = await asyncio.to_thread(_rh_preview_sync, target, period)
    if items == 0 and live == 0:
        return await msg.reply_text(
            f'{ce("📭")} ID <code>{target}</code> hiện không có khoản <b>{_RH_LABEL[period]}</b> nào '
            f'(không có khoản chờ nhận và chưa tích luỹ thêm).', parse_mode=ParseMode.HTML)
    name = await _telegram_name(ctx.bot, target, {}) or "—"
    kb = InlineKeyboardMarkup([[btn("XÁC NHẬN RESET", "⚠️", callback_data=f"rhall:ok:{target}:{period}"),
                                btn("HUỶ", "❌", callback_data="rhall:no")]])
    await msg.reply_text(
        f'{ce("⚠️")} <b>XÁC NHẬN RESET TIỀN HOÀN TRẢ</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("🆔")} ID: <code>{target}</code> · {html.escape(name)}\n'
        f'{ce("🎁")} Loại: <b>{_RH_LABEL[period]}</b>\n'
        f'{ce("🧾")} Đã chốt, chờ nhận: <b>{items}</b> khoản = <code>{fmt_money(pend_total)}đ</code>\n'
        f'{ce("⏳")} Đang tích luỹ (chưa chốt): <code>{fmt_money(live)}đ</code>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("📌")} Chỉ reset <b>riêng người này</b>. Cả hai phần trên về <b>0</b>; số dư, lịch sử, '
        f'thống kê cược và khoản đã nhận trước đó <b>không đổi</b>. Không thể hoàn tác.',
        reply_markup=kb, parse_mode=ParseMode.HTML)

async def resethoanall_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.from_user.id not in ADMIN_IDS or is_admin_banned(q.from_user.id):
        return await q.answer("Bạn không có quyền.", show_alert=True)
    parts = (q.data or "").split(":")
    act = parts[1] if len(parts) > 1 else ""
    if act == "no":
        await q.answer("Đã huỷ.")
        return await q.edit_message_text(f'{ce("🚫")} Đã huỷ reset tiền hoàn trả.', parse_mode=ParseMode.HTML)
    if act != "ok" or len(parts) < 4 or not parts[2].isdigit() or parts[3] not in _RH_LABEL:
        return await q.answer()
    target, period = int(parts[2]), parts[3]
    key = (q.message.chat_id, q.message.message_id)
    if key in _RHALL_DONE:
        return await q.answer("Đã xử lý rồi!", show_alert=True)
    _RHALL_DONE.add(key)
    await q.answer("Đang reset…")
    result = await asyncio.to_thread(_rh_apply_sync, target, period)
    if result is None:
        _RHALL_DONE.discard(key)
        return await q.edit_message_text(
            f'{ce("❌")} Lỗi cơ sở dữ liệu, chưa reset được. Hãy thử lại.', parse_mode=ParseMode.HTML)
    done, total = result
    await q.edit_message_text(
        f'{ce("✅")} <b>ĐÃ RESET TIỀN HOÀN TRẢ</b>\n'
        f'━━━━━━━━━━━━━━━━━━━━━\n'
        f'{ce("🆔")} ID: <code>{target}</code>\n'
        f'{ce("🎁")} Loại: <b>{_RH_LABEL[period]}</b>\n'
        f'{ce("🧾")} Khoản chờ nhận đã xoá: <b>{done}</b> = <code>{fmt_money(total)}đ</code>\n'
        f'{ce("⏳")} Phần đang tích luỹ: <b>đã về 0</b>, tính lại từ bây giờ.',
        parse_mode=ParseMode.HTML)


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



# ============================================================
# CHỐNG SPAM: 5 thao tác (tin nhắn / bấm nút) trong 2 giây => khóa vĩnh viễn
# Bị khóa thì bot im lặng hoàn toàn, không trả lời gì nữa.
# Danh sách khóa lưu PostgreSQL (không mất khi restart) và được nạp vào RAM,
# nên kiểm tra mỗi tin không còn chạm DB -> không làm đơ bot khi bị spam.
# ============================================================
_SPAM_ACTIVITY = collections.defaultdict(collections.deque)
_SPAM_WINDOW_SECONDS = 2.0
_SPAM_MAX_EVENTS = 4          # tin thứ 5 trong 2 giây là bị khóa
_SPAM_LAST_ALBUM = {}         # uid -> media_group_id (album ảnh tính là 1 thao tác)

def _load_spam_banned():
    rows = query("SELECT user_id FROM spam_permanent_bans") or []
    return {int(r[0]) for r in rows}

_SPAM_BANNED = _load_spam_banned()
print(f"[spam-guard] loaded {len(_SPAM_BANNED)} banned users")

def _is_spam_permanently_banned(user_id: int) -> bool:
    return user_id in _SPAM_BANNED

def _spam_ban_db(uid: int):
    query(
        "INSERT INTO spam_permanent_bans(user_id, reason) VALUES(%s,%s) "
        "ON CONFLICT(user_id) DO NOTHING",
        (uid, "Spam: 5 thao tác trong 2 giây")
    )

# ============================================================
# CHỐNG SPAM LỆNH NẠP
#  - Mỗi lệnh nạp (QR) có hiệu lực 10 phút.
#  - Đang có lệnh còn hiệu lực => phải chờ hết hạn (hoặc thanh toán xong) mới tạo được lệnh mới.
#  - Tạo quá 5 mã mà chưa thanh toán thành công lần nào => KHÓA VĨNH VIỄN ẨN:
#    bot im lặng hoàn toàn (cả chat riêng lẫn nhóm), không báo lý do cho người dùng.
#  - Admin gỡ khóa bằng /unbanspam USER_ID (đồng thời xóa lịch sử lệnh nạp của user đó).
# ============================================================
NAP_ORDER_TTL_MINUTES = 10
NAP_MAX_UNPAID_ORDERS = 5
NAP_BAN_REASON = "Nạp: tạo quá 5 mã nạp mà chưa thanh toán"

query("""CREATE TABLE IF NOT EXISTS nap_orders (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    amount BIGINT,
    content TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL
)""")
query("CREATE INDEX IF NOT EXISTS idx_nap_orders_user ON nap_orders(user_id, id DESC)")

def _load_nap_banned():
    rows = query("SELECT user_id FROM spam_permanent_bans WHERE reason LIKE %s", ("Nạp%",)) or []
    return {int(r[0]) for r in rows}

_NAP_BANNED = _load_nap_banned()
_NAP_TASKS = set()   # giữ tham chiếu task hết hạn để không bị thu gom bộ nhớ
print(f"[nap-guard] loaded {len(_NAP_BANNED)} hidden-banned users")

def nap_hidden_ban(uid: int):
    """Khóa vĩnh viễn ẨN: ghi DB + nạp vào RAM, người dùng không nhận bất kỳ thông báo nào."""
    _NAP_BANNED.add(uid)
    _SPAM_BANNED.add(uid)
    _SPAM_ACTIVITY.pop(uid, None)
    try:
        query(
            "INSERT INTO spam_permanent_bans(user_id, reason) VALUES(%s,%s) "
            "ON CONFLICT(user_id) DO NOTHING",
            (uid, NAP_BAN_REASON)
        )
    except Exception as e:
        print(f"[nap-guard] db error khi khóa ẩn {uid}: {e}")
    print(f"[nap-guard] hidden permanent ban user_id={uid}")

def nap_order_gate(uid):
    """Kiểm tra trước khi tạo lệnh nạp. Hàm ĐỒNG BỘ (không await) nên kiểm tra + ghi lệnh là nguyên tử.
    Trả về:
      ("ok", None)                          -> được tạo lệnh mới
      ("wait", (amount, content, giây_còn)) -> đang có lệnh còn hạn, phải chờ
      ("banned", None)                      -> bị khóa ẩn, bot im lặng
    """
    if uid in ADMIN_IDS:
        return "ok", None
    if uid in _NAP_BANNED:
        return "banned", None

    rows = query(
        "SELECT amount, content, GREATEST(EXTRACT(EPOCH FROM (expires_at - NOW())), 0) "
        "FROM nap_orders WHERE user_id=%s AND status='pending' AND expires_at > NOW() "
        "ORDER BY id DESC LIMIT 1", (uid,))
    if rows:
        amount, content, secs = rows[0]
        return "wait", (int(amount or 0), content or "", int(secs or 0))

    # Hết cooldown: nếu đã tạo >= 5 mã mà chưa từng nạp thành công => khóa ẩn ngay lần tạo thứ 6.
    paid = query("SELECT 1 FROM deposit_history WHERE user_id=%s AND status='success' LIMIT 1", (uid,))
    if not paid:
        cnt = query("SELECT COUNT(*) FROM nap_orders WHERE user_id=%s", (uid,))
        if cnt and int(cnt[0][0] or 0) >= NAP_MAX_UNPAID_ORDERS:
            nap_hidden_ban(uid)
            return "banned", None
    return "ok", None

def nap_order_record(uid, amount, content):
    """Ghi lệnh nạp mới, hiệu lực NAP_ORDER_TTL_MINUTES phút. Admin không bị ghi."""
    if uid in ADMIN_IDS:
        return None
    rows = query(
        "INSERT INTO nap_orders(user_id, amount, content, status, expires_at) "
        "VALUES(%s,%s,%s,'pending', NOW() + make_interval(mins => %s)) RETURNING id",
        (uid, int(amount), content, NAP_ORDER_TTL_MINUTES))
    return int(rows[0][0]) if rows else None

def nap_orders_mark_paid(uid):
    """Gọi khi nạp thành công: lệnh đang chờ coi như đã thanh toán, user được tạo lệnh mới ngay."""
    query("UPDATE nap_orders SET status='paid' WHERE user_id=%s AND status='pending'", (uid,))

def nap_wait_text(info):
    amount, content, secs = info
    m, s = divmod(max(int(secs), 0), 60)
    text = (
        f'{ce("⏰")} <b>BẠN ĐANG CÓ LỆNH NẠP CHƯA HẾT HẠN</b>\n\n'
        f'Vui lòng chờ <b>{m} phút {s:02d} giây</b> để tạo lệnh nạp mới '
        f'(hoặc thanh toán lệnh hiện tại).'
    )
    if amount and content:
        text += (
            f'\n\n{ce("💰")} Số tiền: <code>{fmt_money(amount)}đ</code>\n'
            f'{ce("✍️")} Nội dung: <code>{html.escape(str(content))}</code>'
        )
    return text

async def _nap_order_expire(bot, sent, order_id, amount_hint=None):
    await asyncio.sleep(NAP_ORDER_TTL_MINUTES * 60)
    try:
        rows = await asyncio.to_thread(
            query, "UPDATE nap_orders SET status='expired' WHERE id=%s AND status='pending' RETURNING amount", (order_id,))
    except Exception as e:
        print(f"[nap-guard] không đánh dấu hết hạn được lệnh {order_id}: {e}")
        return
    if not rows or sent is None:
        return   # đã thanh toán hoặc không còn tin nhắn để sửa
    text = (
        f'{ce("⏰")} <b>LỆNH NẠP ĐÃ HẾT HẠN</b>\n\n'
        f'Lệnh nạp <code>{fmt_money(int(rows[0][0] or 0))}đ</code> đã quá {NAP_ORDER_TTL_MINUTES} phút.\n'
        f'{ce("❌")} Vui lòng <b>không chuyển khoản</b> theo thông tin cũ. Gõ <code>/nap số_tiền</code> để tạo lệnh mới.'
    )
    try:
        await bot.edit_message_caption(chat_id=sent.chat_id, message_id=sent.message_id,
                                       caption=text, parse_mode=ParseMode.HTML)
    except Exception:
        try:
            await bot.edit_message_text(chat_id=sent.chat_id, message_id=sent.message_id,
                                        text=text, parse_mode=ParseMode.HTML)
        except Exception as e:
            print(f"[nap-guard] không sửa được tin nhắn QR hết hạn: {e}")

def nap_order_schedule_expiry(bot, sent, order_id):
    """Sau 10 phút: nếu chưa thanh toán thì đánh dấu hết hạn và thay QR bằng thông báo hết hạn."""
    if not order_id:
        return
    try:
        task = asyncio.create_task(_nap_order_expire(bot, sent, order_id))
        _NAP_TASKS.add(task)
        task.add_done_callback(_NAP_TASKS.discard)
    except Exception as e:
        print(f"[nap-guard] không hẹn giờ hết hạn được: {e}")

async def spam_guard(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    uid = user.id

    # Không áp dụng cho quản trị viên để tránh khóa nhầm người vận hành.
    if uid in ADMIN_IDS:
        return

    # Khóa ẩn do spam lệnh nạp: im lặng hoàn toàn ở MỌI nơi (chat riêng và nhóm).
    if uid in _NAP_BANNED:
        if update.callback_query:
            try:
                await update.callback_query.answer()
            except Exception:
                pass
        raise ApplicationHandlerStop

    # Chỉ kiểm soát chat riêng với bot, không phạt hoạt động bình thường ở nhóm.
    chat = update.effective_chat
    if not chat or chat.type != "private":
        return

    # Đã bị khóa: nuốt mọi update, không trả lời gì.
    if uid in _SPAM_BANNED:
        if update.callback_query:
            try:
                await update.callback_query.answer()
            except Exception:
                pass
        raise ApplicationHandlerStop

    # Album nhiều ảnh gửi cùng lúc chỉ tính 1 thao tác.
    msg = update.effective_message
    gid = getattr(msg, "media_group_id", None) if msg else None
    if gid:
        if _SPAM_LAST_ALBUM.get(uid) == gid:
            return
        _SPAM_LAST_ALBUM[uid] = gid

    now = time.monotonic()
    events = _SPAM_ACTIVITY[uid]
    while events and now - events[0] > _SPAM_WINDOW_SECONDS:
        events.popleft()
    events.append(now)

    if len(events) > _SPAM_MAX_EVENTS:
        _SPAM_BANNED.add(uid)             # khóa ngay trong RAM
        _SPAM_ACTIVITY.pop(uid, None)
        _SPAM_LAST_ALBUM.pop(uid, None)
        print(f"[spam-guard] permanently blocked user_id={uid}")
        try:
            await asyncio.to_thread(_spam_ban_db, uid)   # ghi DB, không chặn event loop
        except Exception as e:
            print(f"[spam-guard] db error: {e}")
        if update.callback_query:
            try:
                await update.callback_query.answer()
            except Exception:
                pass
        raise ApplicationHandlerStop

async def unban_spam_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user or update.effective_user.id not in ADMIN_IDS:
        return
    if not ctx.args or not ctx.args[0].isdigit():
        await update.effective_message.reply_text("Cú pháp: /unbanspam USER_ID")
        return
    uid = int(ctx.args[0])
    await asyncio.to_thread(query, "DELETE FROM spam_permanent_bans WHERE user_id=%s", (uid,))
    # Xóa lịch sử lệnh nạp để user không bị khóa ẩn lại ngay ở lần /nap kế tiếp.
    await asyncio.to_thread(query, "DELETE FROM nap_orders WHERE user_id=%s", (uid,))
    _SPAM_BANNED.discard(uid)
    _NAP_BANNED.discard(uid)
    _SPAM_ACTIVITY.pop(uid, None)
    await update.effective_message.reply_text(f"Đã gỡ khóa chống spam cho user {uid}.")

application.add_handler(MessageHandler(filters.ALL, spam_guard), group=-100)
application.add_handler(CallbackQueryHandler(spam_guard), group=-100)
application.add_handler(CommandHandler("unbanspam", unban_spam_cmd), group=-99)
async def fan_menu_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if msg and msg.text and msg.text.strip().upper() == "FAN +30K":
        await fan_baodanh(update, ctx)
        raise ApplicationHandlerStop

application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fan_menu_text), group=1)
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("baodanh", fan_baodanh))
application.add_handler(CommandHandler("lienket", lien_ket))
application.add_handler(CommandHandler("taikhoan", taikhoan_cmd))
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

application.add_handler(MessageHandler(filters.ALL, _aw_capture_telegram_profile), group=-100)
application.add_handler(CallbackQueryHandler(_aw_capture_telegram_profile), group=-100)
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
application.add_handler(CommandHandler("hu", hu_cmd))
application.add_handler(CommandHandler("ep", ep_cmd))
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
application.add_handler(CommandHandler("dsnaphomnay", dsnaphomnay_cmd))
application.add_handler(CommandHandler("tangcodenap", tangcodenap_cmd))
application.add_handler(CommandHandler("yccode", yccode_cmd))
application.add_handler(CallbackQueryHandler(tangnap_callback, pattern=r"^tgn:"))
application.add_handler(CommandHandler("sethoancuoc", sethoancuoc_cmd))
application.add_handler(CommandHandler("baotri", baotri_cmd))
application.add_handler(CommandHandler("baotriht", baotri_he_thong_cmd))
application.add_handler(CommandHandler("baotriall", baotri_hethong_cmd))
application.add_handler(CommandHandler("baotritc", baotri_tong_cong_cmd))
application.add_handler(CommandHandler("tatcuoc", tatcuoc_cmd))

application.add_handler(CommandHandler("admin", admin_panel_cmd))
application.add_handler(CommandHandler("adminhelp", admin_help_cmd))
application.add_handler(CommandHandler("xoacuoc", xoacuoc_cmd))
application.add_handler(CommandHandler("themcuoc", themcuoc_cmd))
application.add_handler(CommandHandler("themvongcuoc", themvongcuoc_cmd))
application.add_handler(CommandHandler("ktvc", ktvc_cmd))
application.add_handler(CommandHandler("vcall", vcall_cmd))
application.add_handler(CallbackQueryHandler(vcall_callback, pattern=r"^vcall:"))
application.add_handler(CommandHandler("resetthongke", resetthongke_cmd))
application.add_handler(CommandHandler("xoanap", xoanap_cmd))
application.add_handler(CommandHandler("xoarut", xoarut_cmd))
application.add_handler(CommandHandler("xuatthongke", xuatthongke_cmd))
application.add_handler(CallbackQueryHandler(admin_panel_callback, pattern=r"^adm2:"))
application.add_handler(CallbackQueryHandler(reset_stats_callback, pattern=r"^resetstat_(yes|no)$"))
application.add_handler(CallbackQueryHandler(txdel_callback, pattern=r"^txdel_"))
application.add_handler(CommandHandler("fulluser", fulluser_cmd))
application.add_handler(CommandHandler("lsuser", lsuser_cmd))
application.add_handler(CommandHandler("lsnap", lsnap_cmd))
application.add_handler(CommandHandler("lsrut", lsrut_cmd))
application.add_handler(CommandHandler("lsrutky", lsrut_report_cmd))
application.add_handler(CommandHandler("lscuoc", lscuoc_cmd))
application.add_handler(CommandHandler("lscode", lscode_cmd))
application.add_handler(CommandHandler("lsgift", lsgift_cmd))
application.add_handler(CommandHandler("lsmua", lsmua_cmd))
application.add_handler(CommandHandler("tongket", tongket_cmd))
application.add_handler(CommandHandler("xuatls", xuatls_cmd))
application.add_handler(CommandHandler("huy", huy_cmd))
application.add_handler(CommandHandler("resetbank", resetbank_cmd))
application.add_handler(CommandHandler("camhoan", camhoan_cmd))
application.add_handler(CommandHandler("resethoan", resethoanall_cmd))
application.add_handler(CommandHandler("resethoanall", resethoanall_cmd))
application.add_handler(CallbackQueryHandler(resethoanall_callback, pattern=r"^rhall:"))
application.add_handler(CommandHandler("mohoan", mohoan_cmd))
application.add_handler(CommandHandler("resetuser", resetuser_cmd))
application.add_handler(CommandHandler("xuatnapall", xuatnapall_cmd))
application.add_handler(CommandHandler("xuatrutall", xuatrutall_cmd))
application.add_handler(CommandHandler("xuathethong", xuathethong_cmd))
application.add_handler(CommandHandler("lsnaptatca", lsnaptatca_cmd))
application.add_handler(CommandHandler("lsruttatca", lsruttatca_cmd))
application.add_handler(CallbackQueryHandler(reset_balance_callback, pattern=r"^resetbal_(yes|no)_\d+$"))
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
application.add_handler(CommandHandler("taoadmin", taoadmin_cmd))
application.add_handler(CommandHandler("doimkadmin", doimkadmin_cmd))
application.add_handler(CommandHandler("xoaadmin", xoaadmin_cmd))
application.add_handler(CommandHandler("dsadminweb", dsadminweb_cmd))
application.add_handler(CommandHandler("dsnap", dsnap_cmd))
application.add_handler(CommandHandler("setsd", setsd_cmd))
async def _early_top_cmd(update, ctx):
    try:
        await top_cmd(update, ctx)
    except Exception as e:
        print(f"Lỗi /top: {e}")
        await update.effective_message.reply_text("Không tải được bảng Top. Vui lòng thử lại.")
    raise ApplicationHandlerStop

async def _early_checktt_cmd(update, ctx):
    try:
        await checktt_cmd(update, ctx)
    except Exception as e:
        print(f"Lỗi /checktt: {e}")
        await update.effective_message.reply_text("Không tải được thống kê tương tác. Vui lòng thử lại.")
    raise ApplicationHandlerStop

application.add_handler(CommandHandler("daythang", daythang_cmd), group=-3)
application.add_handler(CommandHandler("daythua", daythua_cmd), group=-3)
application.add_handler(CommandHandler("top", _early_top_cmd), group=-3)
application.add_handler(CommandHandler("checktt", _early_checktt_cmd), group=-3)
# /top và /checktt đã được đăng ký ở group=-3 qua wrapper bên dưới
# để chỉ xử lý một lần trên bot @xoclo88dtbot.
application.add_handler(CommandHandler("topnap", topnap_cmd))
application.add_handler(CommandHandler("topsodu", topsodu_cmd))
application.add_handler(CommandHandler("resetsystem", reset_system_cmd))
application.add_handler(CallbackQueryHandler(reset_system_callback, pattern=r"^sysreset_(yes|no)$"))
application.add_handler(CommandHandler("tatroom", tatroom_cmd))
application.add_handler(CommandHandler("moroom", moroom_cmd))
application.add_handler(CommandHandler("trangthairoom", trangthairoom_cmd))
application.add_handler(CommandHandler("help", interaction_help_cmd))
application.add_handler(CommandHandler("topcuoc", topcuoc_cmd))
application.add_handler(CallbackQueryHandler(admin_user_callback, pattern=r"^admuser_"))

application.add_handler(CallbackQueryHandler(payout_link_callback, pattern=r"^payout:"))
application.add_handler(CommandHandler("xuctele", xuctele_cmd))
application.add_handler(CommandHandler("baucua", baucua_cmd))
application.add_handler(CommandHandler("soloxd", soloxd_cmd))
application.add_handler(CommandHandler("solo", solo_cmd))
application.add_handler(CommandHandler("huy", solo_cancel_cmd))
application.add_handler(CommandHandler("huykbb", solo_kbb_cancel_cmd))
application.add_handler(CommandHandler("solokbb", solokbb_cmd))
application.add_handler(CommandHandler("kbb", _solo_bot_kbb_cmd))
application.add_handler(CommandHandler("xucxacbot", _solo_bot_dice_cmd))
application.add_handler(CallbackQueryHandler(handle_callback))
application.add_handler(MessageHandler(filters.PHOTO, payout_link_photo), group=-2)
application.add_handler(MessageHandler(filters.TEXT, payout_link_text), group=-2)
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, adm_flow_input), group=-1)
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
    # Chặn chạy nhầm TOKEN của bot khác: chỉ khởi động với @xoclo88dtbot.
    _identity = await application.bot.get_me()
    if (_identity.username or "").lower() != BOT_USERNAME.lower():
        raise RuntimeError(
            f"BOT_TOKEN không thuộc @{BOT_USERNAME}; token hiện tại thuộc @{_identity.username}. "
            "Đã dừng để không ghi đè danh sách lệnh của bot khác."
        )
    # Gợi ý lệnh khi người dùng gõ "/" trong nhóm; chỉ đưa các lệnh dùng cho thành viên.
    group_commands = [
        BotCommand("nap", "Nạp tiền"),
        BotCommand("rut", "Rút tiền"),
        BotCommand("top", "Top tương tác nhóm hôm nay"),
        BotCommand("topnap", "Top nạp tiền"),
        BotCommand("topsodu", "Top số dư"),
        BotCommand("topcuoc", "Top cược"),
        BotCommand("checktt", "Kiểm tra tương tác nhóm hôm nay"),
        BotCommand("xuctele", "Chơi Xúc Xắc Tele"),
        BotCommand("baucua", "Chơi Bầu Cua"),
        BotCommand("soloxd", "Tạo phòng Solo Xúc Xắc"),
        BotCommand("solokbb", "Tạo phòng Solo Kéo Búa Bao"),
        BotCommand("daythang", "Top đu dây THẮNG hôm nay"),
        BotCommand("daythua", "Top đu dây THUA hôm nay"),
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
    _bg_tasks.append(asyncio.create_task(settle_day_streak_loop(application.bot)))
    _bg_tasks.append(asyncio.create_task(promo_golden_loop(application.bot)))
    _bg_tasks.append(asyncio.create_task(tx3d_loop()))
    
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
