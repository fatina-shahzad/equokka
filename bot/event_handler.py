import os
import boto3
import re
import logging
from slack_sdk.errors import SlackApiError
from slack_sdk.socket_mode.response import SocketModeResponse
from bot.utils import get_s3_presigned_url

logger = logging.getLogger(__name__)

class EventHandler:
    def __init__(self, web_client):
        self.web_client = web_client
        self.s3 = boto3.client("s3")
        self.bucket = os.getenv("S3_BUCKET_NAME")

    async def handle_request(self, client, req):
        await client.send_socket_mode_response({"envelope_id": req.envelope_id})

        if req.type == "events_api":
            event = req.payload.get("event", {})
            event_type = event.get("type")

            if event_type == "message" and "bot_id" not in event:
                text = event.get("text", "").lower()
                channel_id = event.get("channel")

                # Look for mindap requests
                if text == "leave request procedure":
                    html_url = get_s3_presigned_url(bucket_name="equokka-mindmaps-poc", region="us-west-2", file_name="emumba_leave_mindmap.html", expiration=3000)
                    await client.web_client.chat_postMessage(
                        channel=event.get("channel"),
                        text=f"View here: <{html_url}|Leave guidelines>"
                    )
                elif text == "loan policy":
                    html_url = get_s3_presigned_url(bucket_name="equokka-mindmaps-poc", region="us-west-2", file_name="emumba_leave_mindmap.html", expiration=3000)
                    await client.web_client.chat_postMessage(
                        channel=event.get("channel"),
                        text=f"View here: <{html_url}|Loan Request Policy>"
                    )
                elif text == "day care":
                    html_url = get_s3_presigned_url(bucket_name="equokka-mindmaps-poc", region="us-west-2", file_name="emumba_leave_mindmap.html", expiration=3000)
                    await client.web_client.chat_postMessage(
                        channel=event.get("channel"),
                        text=f"View here: <{html_url}|Day Care Policy>"
                    )
                elif text == "slack guidelines":
                    html_url = get_s3_presigned_url(bucket_name="equokka-mindmaps-poc", region="us-west-2", file_name="emumba_leave_mindmap.html", expiration=3000)
                    await client.web_client.chat_postMessage(
                        channel=event.get("channel"),
                        text=f"View here: <{html_url}|Slack Guidelines>"
                    )    
                else:
                    await client.web_client.chat_postMessage(
                        channel=event.get("channel"),
                        text="Thanks for your message!"
                    )

                # Look for a pattern like "podcast on XYZ"
                match = re.search(r"podcast (?:on|about)\s+(.*)", text)
                if match:
                    topic = match.group(1).strip()
                    logger.info(f"🎙️ User requested podcast on topic: {topic}")
                    await self.handle_podcast_command(topic, channel_id)

    async def handle_podcast_command(self, topic: str, channel_id: str):
        file_key = self.find_relevant_audio(topic)

        if file_key:
            logger.info(f"Found matching file: {file_key}")
            presigned_url = self.generate_presigned_url(file_key)
            await self.share_podcast_link(presigned_url, topic, channel_id)
        else:
            await self.web_client.chat_postMessage(
                channel=channel_id,
                text=f" No podcast found for *{topic}*."
            )
            logger.info(f" No matching podcast found for topic: {topic}")

    def find_relevant_audio(self, topic_keywords: str) -> str | None:
        topic_words = topic_keywords.lower().split()
        best_match = None

        paginator = self.s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=self.bucket):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith(".wav") or key.endswith(".mp3"):
                    filename = key.rsplit("/", 1)[-1].lower()
                    if all(word in filename for word in topic_words):
                        return key
                    elif any(word in filename for word in topic_words) and not best_match:
                        best_match = key
        return best_match

    def generate_presigned_url(self, file_key: str, expiration=3600) -> str:
        return self.s3.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': self.bucket,
                'Key': file_key,
                'ResponseContentDisposition': 'inline'
            },
            ExpiresIn=expiration
        )

    async def share_podcast_link(self, presigned_url: str, topic: str, channel_id: str):
        try:
            await self.web_client.chat_postMessage(
                channel=channel_id,
                blocks=[
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"Here's your podcast on *{topic}*"
                        }
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "🎧 Listen Now"
                                },
                                "url": presigned_url,
                                "style": "primary"
                            }
                        ]
                    }
                ]
            )

            logger.info("Podcast link sent successfully.")
        except SlackApiError as e:
            logger.error(f"Slack API error while sharing link: {e.response['error']}")
            await self.web_client.chat_postMessage(
                channel=channel_id,
                text=f"Could not share podcast for *{topic}*."
            )
