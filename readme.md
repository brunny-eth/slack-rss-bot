## Slack RSS Bot

This bot checks an RSS feed (or multiple) on a periodic basis (set to hourly but could be set to smaller or longer timeframes) and, once the bot is added to the correct channel, will create a new daily thread and drop in all daily posts from the RSS feed 

Useful for staying up-to-date with research channels (e.g., Arxiv posts) in an organized way with a larger team  

Currently configured for IACR Cryptology eprint and Arxiv Cryptography but really easy switch to include other feeds (simply change the rss link in rss_bot.py)

### Setup

1. Create a `.env` file with:
    ```
    SLACK_BOT_TOKEN=your-token
    CHANNEL_ID=specific-channel-id
    ```

2. Install requirements in venv:
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install slack-sdk python-dotenv feedparser requests certifi
    ```

### Run

1. Copy service file to systemd:
    ```bash
    sudo cp rss-bot.service /etc/systemd/system/
    ```

2. Start service and auto-start on boot:
    ```bash
    sudo systemctl start rss-bot
    sudo systemctl enable rss-bot 
    ```

3. Check status:
    ```bash
    sudo systemctl status rss-bot
    ```


