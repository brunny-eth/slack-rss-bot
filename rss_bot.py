import os
import json
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import feedparser
from datetime import datetime, timedelta
import time
import hashlib

import certifi
import ssl

ssl_context = ssl.create_default_context(cafile=certifi.where())

# Load environment variables
load_dotenv()

# Set up Slack client
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
client = WebClient(token=SLACK_BOT_TOKEN, ssl=ssl_context)

# RSS feed URLs (replace with your feed URLs)
RSS_FEEDS = [
    "https://eprint.iacr.org/rss/rss.xml?order=recent",
    "https://rss.arxiv.org/rss/cs.CR",
]

THREAD_TS_FILE = 'thread_timestamp.json'
POSTED_ENTRIES_FILE = os.path.join(os.path.dirname(__file__), 'posted_entries.json')

def get_or_create_thread_ts():
    today = datetime.now().strftime('%Y-%m-%d')
    
    if os.path.exists(THREAD_TS_FILE):
        with open(THREAD_TS_FILE, 'r') as f:
            data = json.load(f)
            if data['date'] == today:
                print(f"Using existing thread for {today}")
                return data['thread_ts']
    
    # If file doesn't exist or it's a new day, create a new thread
    print(f"Creating new thread for {today}")
    thread_ts = create_daily_thread()
    if thread_ts:
        with open(THREAD_TS_FILE, 'w') as f:
            json.dump({'date': today, 'thread_ts': thread_ts}, f)
    return thread_ts

def create_daily_thread():
    """Create a new thread for today's updates."""
    try:
        result = client.chat_postMessage(
            channel=CHANNEL_ID,
            text=f"RSS Updates for {datetime.now().strftime('%Y-%m-%d')}"
        )
        return result["ts"]
    except SlackApiError as e:
        print(f"Error creating thread: {e}")
        return None

def post_to_thread(thread_ts, text):
    """Post a message to the specified thread."""
    try:
        client.chat_postMessage(
            channel=CHANNEL_ID,
            thread_ts=thread_ts,
            text=text
        )
    except SlackApiError as e:
        print(f"Error posting to thread: {e}")

def hash_url(url):
    return hashlib.sha256(url.encode()).hexdigest()

def load_posted_entries():
    if os.path.exists(POSTED_ENTRIES_FILE):
        with open(POSTED_ENTRIES_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_posted_entries(posted_entries):
    with open(POSTED_ENTRIES_FILE, 'w') as f:
        json.dump(posted_entries, f)

def check_feeds(thread_ts):
    """Check all RSS feeds for new entries and post them to the thread."""
    posted_entries = load_posted_entries()
    current_time = datetime.now()

    for feed_url in RSS_FEEDS:
        print(f"Checking feed: {feed_url}")
        feed = feedparser.parse(feed_url)
        
        if feed_url not in posted_entries:
            posted_entries[feed_url] = []

        new_entries = []
        for entry in feed.entries:
            entry_url = entry.link
            entry_hash = hash_url(entry_url)
            entry_date = datetime(*entry.published_parsed[:6]) if 'published_parsed' in entry else current_time
            
            # Check if the entry is new (not in posted_entries) and not older than 24 hours
            if entry_hash not in posted_entries[feed_url] and current_time - entry_date <= timedelta(hours=24):
                new_entries.append(entry)
                posted_entries[feed_url].append(entry_hash)

        # Post new entries (up to 5)
        for entry in new_entries[:5]:
            post_to_thread(thread_ts, f"New post from {feed.feed.title}: {entry.title}\n{entry.link}")

    # Remove entries older than 24 hours from our tracking
    for feed_url in posted_entries:
        posted_entries[feed_url] = posted_entries[feed_url][-100:]  # Keep last 100 entries to manage file size

    save_posted_entries(posted_entries)

def main():
    print("Starting Multi-Feed RSS Bot...")
    
    while True:
        thread_ts = get_or_create_thread_ts()
        if not thread_ts:
            print("Failed to create or get thread. Retrying in 5 minutes.")
            time.sleep(300)  # Wait 5 minutes before retrying
            continue

        print("Checking RSS feeds...")
        check_feeds(thread_ts)
        print("Waiting for next check...")
        time.sleep(2400)  

if __name__ == "__main__":
    main()