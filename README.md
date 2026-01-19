# Housewarming Wishlist Bot

A Telegram bot for managing a wishlist with group forum integration.

## Features

- **Add items** via `/add` command (restricted to authorized user)
- **Item details**: name, price, link (optional), remarks (optional)
- **Auto-creates forum topic** for each item in the group
- **Posts item summary** to a dedicated wishlist topic with a "I'll chip in!" button linking to the item's discussion topic
- **Persists data** to JSON file

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Create a `.env` file with your bot token:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

3. Configure the bot in `bot.py`:
   - `ALLOWED_USERNAME` - Telegram username allowed to add items
   - `GROUP_ID` - Your Telegram group ID (with forum topics enabled)
   - `WISHLIST_TOPIC_ID` - Topic ID where item summaries are posted

4. Run the bot:
   ```bash
   python bot.py
   ```

## Commands

| Command | Description |
|---------|-------------|
| `/add` | Start adding a new item (authorized user only) |
| `/skip` | Skip optional fields (link, remarks) |
| `/cancel` | Cancel the current operation |

## How it works

1. Authorized user runs `/add`
2. Bot asks for item name, price, link, and remarks
3. Bot creates a new forum topic named after the item
4. Bot posts the item summary to the wishlist topic with a button to join the discussion
