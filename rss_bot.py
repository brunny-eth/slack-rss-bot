import os
import json
import ssl
import certifi
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import feedparser
import requests
from datetime import datetime, timedelta
import time
import hashlib
import logging

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def get_or_create_thread_ts():
    today = datetime.now().strftime('%Y-%m-%d')
    
    if os.path.exists(THREAD_TS_FILE):
        with open(THREAD_TS_FILE, 'r') as f:
            data = json.load(f)
            if data['date'] == today:
                logging.info(f"Using existing thread for {today}: {data['thread_ts']}")
                return data['thread_ts']
    
    logging.info(f"Creating new thread for {today}")
    thread_ts = create_daily_thread()
    if thread_ts:
        with open(THREAD_TS_FILE, 'w') as f:
            json.dump({'date': today, 'thread_ts': thread_ts}, f)
        logging.info(f"New thread created with ts: {thread_ts}")
    else:
        logging.error("Failed to create new thread")
    return thread_ts

def post_to_thread(thread_ts, text):
    """Post a message to the specified thread."""
    try:
        result = client.chat_postMessage(
            channel=CHANNEL_ID,
            thread_ts=thread_ts,
            text=text
        )
        logging.info(f"Full Slack API response: {result}")
        logging.info(f"Message posted successfully: {result['ts']}")
    except SlackApiError as e:
        logging.error(f"Error posting to thread: {e}")
        if e.response['error'] == 'invalid_auth':
            logging.error("Invalid authentication. Please check your Slack token.")
        elif e.response['error'] == 'channel_not_found':
            logging.error(f"Channel not found. Please check your CHANNEL_ID: {CHANNEL_ID}")

# Load environment variables
load_dotenv()

# Set up Slack client with proper SSL verification
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')
client = WebClient(token=SLACK_BOT_TOKEN)

# RSS feed URLs
RSS_FEEDS = [
    "https://eprint.iacr.org/rss/rss.xml?order=recent",
    "https://rss.arxiv.org/rss/cs.CR"
]

THREAD_TS_FILE = 'thread_timestamp.json'
POSTED_ENTRIES_FILE = os.path.join(os.path.dirname(__file__), 'posted_entries.json')



def fetch_feed(url):
    try:
        response = requests.get(url, verify=certifi.where())
        response.raise_for_status()
        return feedparser.parse(response.content)
    except requests.RequestException as e:
        print(f"Error fetching feed {url}: {e}")
        return None

# def test_feeds():
    for feed_url in RSS_FEEDS:
        print(f"Testing feed: {feed_url}")
        feed = fetch_feed(feed_url)
        if feed is None:
            print("  Error: Failed to fetch feed")
        elif feed.bozo:
            print(f"  Error: {feed.bozo_exception}")
        elif feed.entries:
            print(f"  Feed title: {feed.feed.title}")
            print(f"  Number of entries: {len(feed.entries)}")
            print(f"  Most recent entry: {feed.entries[0].title}")
            print(f"  Published: {feed.entries[0].get('published', 'No date available')}")
        else:
            print("  No entries found in feed")
        print()

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
        result = client.chat_postMessage(
            channel=CHANNEL_ID,
            thread_ts=thread_ts,
            text=text
        )
        print(f"Message posted successfully: {result['ts']}")
    except SlackApiError as e:
        print(f"Error posting to thread: {e}")
        if e.response['error'] == 'invalid_auth':
            print("Invalid authentication. Please check your Slack token.")
        elif e.response['error'] == 'channel_not_found':
            print(f"Channel not found. Please check your CHANNEL_ID: {CHANNEL_ID}")

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
        feed = fetch_feed(feed_url)
        if feed is None:
            continue
        
        if feed_url not in posted_entries:
            posted_entries[feed_url] = []

        new_entries = []
        for entry in feed.entries:
            entry_url = entry.link
            entry_hash = hash_url(entry_url)
            entry_date = datetime(*entry.published_parsed[:6]) if 'published_parsed' in entry else current_time
            
            if entry_hash not in posted_entries[feed_url] and current_time - entry_date <= timedelta(hours=24):
                new_entries.append(entry)
                posted_entries[feed_url].append(entry_hash)

        logging.info(f"Found {len(new_entries)} new entries for {feed_url}")
        
        # Post new entries (up to 7)
        for entry in new_entries[:7]:
            message = f"New post from {feed.feed.title}: {entry.title}\n{entry.link}"
            print(f"Posting: {message[:50]}...")  # Print first 50 chars of the message
            post_to_thread(thread_ts, message)

      # Save all new entries before pruning
    save_posted_entries(posted_entries)

    # Remove older entries to manage file size
    for feed_url in posted_entries:
        posted_entries[feed_url] = posted_entries[feed_url][-100:]  # Keep last 100 entries

    # Save again after pruning
    save_posted_entries(posted_entries)

def main():
    logging.info("Starting RSS Bot...")
    
    while True:
        thread_ts = get_or_create_thread_ts()
        if not thread_ts:
            print("Failed to create or get thread. Retrying in 1 minute.")
            time.sleep(60)  # Waits 1 minute before retrying to create the thread
            continue

        print("Checking RSS feeds...")
        check_feeds(thread_ts)
        print("Waiting for next check...")
        time.sleep(3600)   # Checks every hour for new posts

if __name__ == "__main__":
    main()