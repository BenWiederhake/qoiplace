#!/usr/bin/env python3

import atomic_store
import datetime
import io
import logging
import myqoi
import mysecrets
import time

from telegram import InputMediaDocument, Update
from telegram.ext import filters, Application, CommandHandler, MessageHandler, ContextTypes


CACHED_STORE = None
PLACE_TIMEOUT_SECONDS = 59
ANCIENT_OFFSET_SECONDS = 3600 * 24
TYPICAL_BAN_LENGTH = 3600 * 12  # Half a day should be enough to stave off the worst
BUFFER_BYTE_LENGTH = 4 * 512 * 512
START_TEXT = f"""\
Hi! I have an internal buffer of {BUFFER_BYTE_LENGTH:,} bytes, that's the maximum file size of a 512×512 pixel QOI image.
You can read up on the QOI format here: https://qoiformat.org/qoi-specification.pdf
Send me messages like "456789 123" to set the 456789th byte to 123.
Every minute or so, I'll post the newest QOI image here: https://t.me/qoiplace
(Unless nothing changed.)

You'll have to wait {PLACE_TIMEOUT_SECONDS} seconds between any such message. Note that this is a retaliatory rate limit: If you try to cheat and send a message before the time is up, then the timer resets to {PLACE_TIMEOUT_SECONDS} seconds. So you might want to wait {PLACE_TIMEOUT_SECONDS + 1} seconds instead, or something like that.

We live in a society, so please be excellent. In particular:
- Have fun, and let other people also have fun (in particular, no hate speech or illegal imagery)
- Live and let live (in particular, don't behave in any way that might seem like attacking the people, bot, infrastructure, or anyone else)
- If you have any ideas how to make this project even more awesome, feel free to post them in the discussion group, linked in the main channel! I'd love to hear your suggestions :D

You're very much invited to coordinate and automate. Have fun! :D
"""
QOI_PREAMBLE = b"qoif" + bytes([0, 0, 2, 0, 0, 0, 2, 0, 3, 0])  # QOI, 512 wide, 512 high, 3 channels, sRGB.
QOI_EPILOGUE = bytes([0, 0, 0, 0, 0, 0, 0, 1])


class Store:
    def __init__(self):
        print(f"===== NEW STORE!!! ===== id={id(self)}")
        self.atomic_store = atomic_store.open("state.json", default=dict())
        if "users_times" not in self.atomic_store.value:
            self.atomic_store.value["users_times"] = dict()
        if "bytes_list" not in self.atomic_store.value:
            self.atomic_store.value["bytes_list"] = [0] * BUFFER_BYTE_LENGTH
        if "history" not in self.atomic_store.value:
            self.atomic_store.value["history"] = []  # Tuples of (UserID, time, index, value)
        self.dirty = False

    def get_singleton():
        global CACHED_STORE
        if CACHED_STORE is None:
            CACHED_STORE = Store()
        return CACHED_STORE

    def save_if_necessary(self):
        if not self.dirty:
            return False
        self.dirty = False
        self.atomic_store.commit()
        return True

    def ban(self, user_id, ban_time):
        now = time.time()
        if ban_time < 0:
            ban_time = 0
        self.atomic_store.value["users_times"][user_id] = now + ban_time

    def write_byte(self, index, byte_value, user_id) -> float:  # number of seconds left (negative if successful, positive otherwise)
        user_id = str(user_id)
        now = time.time()
        if not (0 <= index < BUFFER_BYTE_LENGTH):
            return 1
        if user_id in self.atomic_store.value["users_times"]:
            last_write = self.atomic_store.value["users_times"][user_id]
            remaining_wait = last_write + PLACE_TIMEOUT_SECONDS - now
            if remaining_wait > 0.05:
                if remaining_wait < 60:
                    # Punish users for being too eager. Effectively reset the timer to 60 seconds.
                    self.atomic_store.value["users_times"][user_id] = now
                return remaining_wait
        self.atomic_store.value["users_times"][user_id] = now
        self.atomic_store.value["history"].append([user_id, now, index, byte_value])
        self.atomic_store.value["bytes_list"][index] = byte_value
        self.dirty = True
        return -1

    def force_null_byte(self, index) -> bool:
        now = time.time()
        if not (0 <= index < BUFFER_BYTE_LENGTH):
            return False
        self.atomic_store.value["users_times"][""] = now
        self.atomic_store.value["history"].append(["", now, index, 0])
        self.atomic_store.value["bytes_list"][index] = 0
        self.dirty = True
        return True

    def get_num_bytes_written(self):
        return len(self.atomic_store.value["history"])

    def get_raw_data(self):
        return self.atomic_store.value["bytes_list"]

    def get_num_users(self):
        stats = dict(old=0, current=0, banned=0)
        now = time.time()
        ancient_threshold = now - ANCIENT_OFFSET_SECONDS
        print(f"Now processing: {self.atomic_store.value['users_times'].values()}")
        for last_write in self.atomic_store.value["users_times"].values():
            if last_write < ancient_threshold:
                stats["old"] += 1
            elif last_write > now:
                stats["banned"] += 1
            else:
                stats["current"] += 1
        return stats

    def str_stats(self):
        return f"{self.get_num_bytes_written()} bytes written, known users {self.get_num_users()}"

    def render(self):
        return myqoi.decode(self.atomic_store.value["bytes_list"], 512, 512)


async def swallow_store(context: ContextTypes.DEFAULT_TYPE):
    store = context.job.data
    if not store.save_if_necessary():
        # Nothing changed, no need to make a post about it.
        return
    # Something changed! Let's post about it:
    now = time.time()
    timestamp_str = datetime.datetime.fromtimestamp(now).strftime("%Y%m%d_%H%M%S")
    qoi_file = QOI_PREAMBLE + bytes(store.get_raw_data()) + QOI_EPILOGUE
    img = store.render()
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    png_file = buf.getvalue()
    qoi_doc = InputMediaDocument(qoi_file, filename=f"qoiplace_{timestamp_str}.qoi")
    png_doc = InputMediaDocument(png_file, filename=f"qoiplace_{timestamp_str}.png")
    await context.bot.send_media_group(
        chat_id=mysecrets.CHANNEL_ID,
        media=[qoi_doc, png_doc],
        caption=f"Whoop whoop! New frame: {store.get_num_users()} wrote a total of {store.get_num_bytes_written()} bytes. This is the result.",
        disable_notification=True,
    )


async def start(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends explanation on how to use the bot."""
    await update.message.reply_text(START_TEXT)


async def admin(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends explanation on how to use the bot."""
    await update.message.reply_text("""
/admin
/ban USER_ID [TIME_SECONDS]
/sigh
/stats
    """)


async def stats(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != mysecrets.OWNER_ID:
        return
    await update.message.reply_text(f"Current stats: {Store.get_singleton().str_stats()}")


async def sigh(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != mysecrets.OWNER_ID:
        return
    self.atomic_store.value["users_times"][mysecrets.OWNER_ID] = 0
    await update.message.reply_text("Reset")


async def null(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != mysecrets.OWNER_ID:
        return
    success = False
    exception = None
    try:
        index = int(update.message.text.split(" ")[1])
        self.atomic_store.force_null_byte(index)
        success = True
    except BaseException as e:
        exception = e
    if success:
        await update.message.reply_text("Done")
    else:
        await update.message.reply_text(f"Failed! Error: {exception}")


async def ban(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != mysecrets.OWNER_ID:
        return
    if update.message is None or update.message.text is None:
        return  # Don't consider Updates that don't stem from a text message.
    msg_parts = update.message.text.split(" ")[1:]  # Split, and remove "/ban" prefix
    try:
        int_parts = [int(p) for p in msg_parts]
    except:
        await update.message.reply_text(f"Couldn't convert some part to int?! >>{msg_parts}<<")
        return
    if len(int_parts) == 1:
        int_parts.append(TYPICAL_BAN_LENGTH)
    elif len(int_parts) == 2:
        pass
    else:
        await update.message.reply_text(f"Need only 1 or 2 parts `/ban USER_ID [TIME_SECONDS]` , instead got {len(int_parts)}<<")
        return
    store = Store.get_singleton()
    store.ban(*int_parts)
    await update.message.reply_text(f"User banned. New stats: {Store.get_singleton().str_stats()}")


async def set_byte(update: Update, _context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.text is None:
        return  # Don't consider Updates that don't stem from a text message.
    msg_parts = update.message.text.split(" ")
    int_parts = None
    if len(msg_parts) == 2 and all(len(p) < 25 for p in msg_parts):
        try:
            int_parts = [int(p) for p in msg_parts]
        except ValueError:
            int_parts = None
    if int_parts is None:
        await update.message.reply_text("I can't interpret that. Just write something like \"456789 123\" (without the quotation marks) to set the 456789th byte to 123. See /start for more explanation.")
        return
    index, value = int_parts
    if not (0 <= index < BUFFER_BYTE_LENGTH):
        await update.message.reply_text(f"The first number is the byte offset of the buffer, which has length {BUFFER_BYTE_LENGTH:,}. That means that {index} won't work. See /start for more explanation.")
        return
    if not (0 <= value < 256):
        await update.message.reply_text(f"The second number is the new byte value you want to write, which must be between 0 and 255 inclusively. That means that {value} won't work. See /start for more explanation.")
        return
    store = Store.get_singleton()
    remaining_wait = store.write_byte(index, value, update.effective_user.id)
    if remaining_wait > 0:
        await update.message.reply_text(f"Sorry, you should have waited {remaining_wait} more seconds. Timeout has been reset to at least {PLACE_TIMEOUT_SECONDS}.")
    else:
        await update.message.reply_text(f"Done, {update.effective_user.first_name}! You should see the result in the common channel soon.")


def run() -> None:
    # Enable logging
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
    )

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(mysecrets.TOKEN).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler(["start", "help"], start))
    application.add_handler(CommandHandler("admin", admin))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("sigh", sigh))
    application.add_handler(CommandHandler("ban", ban))
    application.add_handler(CommandHandler("null", null))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, set_byte))

    job_queue = application.job_queue
    store = Store.get_singleton()
    print(f"Starting with {store.str_stats()}")
    job_minute = job_queue.run_repeating(swallow_store, interval=60, first=10, data=store)

    # Run the bot until the user presses Ctrl-C
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    run()
