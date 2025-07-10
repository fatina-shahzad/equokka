import boto3
import tempfile
import os
import re
from slack_sdk.errors import SlackApiError
import logging
from tempfile import NamedTemporaryFile

from slack_sdk.socket_mode.response import SocketModeResponse

logger = logging.getLogger(__name__)


class EventHandler:
    def __init__(self, web_client):
        self.web_client = web_client
        self.cache = {}  # Format: {s3_key: {"file_id": "F123", "local_path": "/tmp/file.wav"}}
        self.cache_dir = "/tmp/slack_podcast_cache"  # Local cache directory

        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)

    def extract_podcast_topic(self, text: str) -> str | None:
        """
        Tries to extract a podcast topic from a free-text message.
        Example matches: "podcast on marketing", "send a podcast about AI", etc.
        """
        text = text.lower()

        # Regex looks for "podcast on X", "podcast about Y", or "send me a podcast on Z"
        patterns = [
            r"podcast (?:on|about) ([\w\s-]+)",
            r"send.*podcast.*(?:on|about)? ([\w\s-]+)",
            r"i want.*podcast.*(?:on|about)? ([\w\s-]+)"
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                topic = match.group(1).strip()
                return topic

        return None

    async def handle_request(self, client, req):
        await client.send_socket_mode_response({
            "envelope_id": req.envelope_id
        })

        if req.type == "slash_commands":
            payload = req.payload
            user_id = payload.get("user_id")
            channel_id = payload.get("channel_id")
            command = payload.get("command")
            text = payload.get("text", "").strip()


        elif req.type == "events_api":
            event = req.payload.get("event", {})
            if event.get("type") == "message" and not event.get("bot_id"):
                text = event.get("text", "")
                channel_id = event.get("channel")
                topic = self.extract_podcast_topic(text)

                if topic:
                    print(f"Detected podcast request in free-text: '{text}' → topic: '{topic}'")
                    await self.handle_podcast_command(topic, channel_id)

    async def handle_podcast_command(self, topic: str, channel_id: str):
        print("handling podcast command")
        file_key = self.find_relevant_audio(topic)

        if file_key:
            print(f"Found relevant audio file: {file_key}")
            await self.web_client.chat_postMessage(
                channel=channel_id,
                text=f"🎧 Sending you the podcast on *{topic}*..."
            )
            await self.upload_audio_to_slack(file_key, channel_id)
        else:
            await self.web_client.chat_postMessage(
                channel=channel_id,
                text=f"No matching podcast found for *{topic}*."
            )

    def find_relevant_audio(self, topic_keywords: str) -> str | None:
        print("Finding relevant audio for topic:", topic_keywords)
        s3 = boto3.client("s3")
        paginator = s3.get_paginator("list_objects_v2")
        topic_words = topic_keywords.lower().split()
        best_match = None

        for page in paginator.paginate(Bucket=os.getenv("S3_BUCKET_NAME")):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith(".wav"):
                    filename = key.rsplit("/", 1)[-1].lower()
                    if all(word in filename for word in topic_words):
                        return key
                    elif any(word in filename for word in topic_words) and not best_match:
                        best_match = key
        return best_match

    async def upload_audio_to_slack(self, file_key: str, channel_id: str):
        print(f"Uploading audio to Slack: {file_key}")

        # Check if file exists in cache
        if file_key in self.cache:
            cache_entry = self.cache[file_key]
            try:
                # Re-upload from local cache
                with open(cache_entry["local_path"], "rb") as f:
                    response = await self.web_client.files_upload_v2(
                        channel=channel_id,
                        file=f,
                        title="Your Podcast 🎧 (Cached)",
                        filename=os.path.basename(file_key)
                    )
                print(f"Reused cached file: {cache_entry['local_path']}")
                return
            except (SlackApiError, FileNotFoundError) as e:
                print(f"Cache reuse failed: {e}. Re-downloading from S3...")
                del self.cache[file_key]  # Remove invalid cache entry

        # Download from S3 (first-time upload)
        s3 = boto3.client("s3")
        try:
            s3_object = s3.get_object(Bucket=os.getenv("S3_BUCKET_NAME"), Key=file_key)
            audio_data = s3_object["Body"].read()

            # Store in local cache
            local_path = os.path.join(self.cache_dir, os.path.basename(file_key))
            with open(local_path, "wb") as f:
                f.write(audio_data)

            # Upload to Slack and cache metadata
            with open(local_path, "rb") as f:
                response = await self.web_client.files_upload_v2(
                    channel=channel_id,
                    file=f,
                    title="Your Podcast",
                    filename=os.path.basename(file_key)
                )

                self.cache[file_key] = {
                    "file_id": response["file"]["id"],
                    "local_path": local_path
                }
                print(f"Cached file locally at: {local_path}")

        except Exception as e:
            print(f"Failed to upload: {e}")
            if os.path.exists(local_path):
                os.remove(local_path)

