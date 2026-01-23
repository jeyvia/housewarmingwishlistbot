import os
import json
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g., https://<YOUR_VM_IP>:8443

if not BOT_TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN environment variable is not set")

if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL environment variable is not set")

DATA_FILE = "wishlist.json"
ALLOWED_USERNAME = os.getenv("ALLOWED_USERNAME")
GROUP_ID = int(os.getenv("GROUP_ID"))
WISHLIST_TOPIC_ID = int(os.getenv("WISHLIST_TOPIC_ID"))

NAME, PRICE, LINK, REMARKS = range(4)


def load_wishlist() -> list:
    """Load wishlist from JSON file."""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []


def save_wishlist(wishlist: list) -> None:
    """Save wishlist to JSON file."""
    with open(DATA_FILE, "w") as f:
        json.dump(wishlist, f, indent=2)


async def add_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the add item conversation."""
    username = update.effective_user.username
    if username != ALLOWED_USERNAME:
        await update.message.reply_text("You are not authorized to add items.")
        return ConversationHandler.END

    await update.message.reply_text("What's the name of the item?")
    return NAME


async def add_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store name and ask for price."""
    context.user_data["item"] = {"name": update.message.text}
    await update.message.reply_text("What's the price?")
    return PRICE


async def add_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store price and ask for link."""
    context.user_data["item"]["price"] = update.message.text
    await update.message.reply_text("Link to the item? (or /skip)")
    return LINK


async def add_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store link and ask for remarks."""
    context.user_data["item"]["link"] = update.message.text
    await update.message.reply_text("Any remarks? (or /skip)")
    return REMARKS


async def skip_link(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip link and ask for remarks."""
    context.user_data["item"]["link"] = None
    await update.message.reply_text("Any remarks? (or /skip)")
    return REMARKS


async def add_remarks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store remarks and save item."""
    context.user_data["item"]["remarks"] = update.message.text
    return await save_item(update, context)


async def skip_remarks(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skip remarks and save item."""
    context.user_data["item"]["remarks"] = None
    return await save_item(update, context)


def format_item_message(item: dict) -> str:
    """Format item for display."""
    lines = [
        f"🎁 <b>{item['name']}</b>",
        "",
        f"💰 Price: {item['price']}",
    ]
    if item.get("remarks"):
            lines.append(f"📝 Remarks: {item['remarks']}")

    if item.get("link"):
        lines.append(f"🔗 <a href=\"{item['link']}\">Link</a>")

    return "\n".join(lines)


async def save_item(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Save the item to the wishlist and post to channel."""
    item = context.user_data.pop("item")
    wishlist = load_wishlist()
    wishlist.append(item)
    save_wishlist(wishlist)

    message = format_item_message(item)

    forum_topic = await context.bot.create_forum_topic(
        chat_id=GROUP_ID,
        name=item["name"]
    )

    topic_link = f"https://t.me/c/{str(GROUP_ID)[4:]}/{forum_topic.message_thread_id}"

    keyboard = [[InlineKeyboardButton("I'll chip in! 🙋‍♂️", url=topic_link)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        chat_id=GROUP_ID,
        message_thread_id=WISHLIST_TOPIC_ID,
        text=message,
        parse_mode="HTML",
        reply_markup=reply_markup
    )

    await update.message.reply_text("Item added and posted, topic created!")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    context.user_data.pop("item", None)
    await update.message.reply_text("Cancelled.")
    return ConversationHandler.END


def main() -> None:
    """Start the bot."""
    application = Application.builder().token(BOT_TOKEN).build()

    add_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add_start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_name)],
            PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_price)],
            LINK: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_link),
                CommandHandler("skip", skip_link),
            ],
            REMARKS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_remarks),
                CommandHandler("skip", skip_remarks),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(add_handler)

    logger.info("Bot started")
    application.run_webhook(
        listen="0.0.0.0",
        port=8443,
        url_path=BOT_TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{BOT_TOKEN}",
        cert="cert.pem",
        key="private.key",
    )


if __name__ == "__main__":
    main()
