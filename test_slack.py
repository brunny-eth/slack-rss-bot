import os
from dotenv import load_dotenv
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import certifi
import ssl

load_dotenv()

SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
CHANNEL_ID = os.getenv('CHANNEL_ID')

ssl_context = ssl.create_default_context(cafile=certifi.where())
client = WebClient(token=SLACK_BOT_TOKEN, ssl=ssl_context)

try:
    response = client.chat_postMessage(
        channel=CHANNEL_ID,
        text="Hello! This is a test message from your RSS bot."
    )
    print(f"Message sent successfully. Timestamp: {response['ts']}")
except SlackApiError as e:
    print(f"Error sending message: {e}")