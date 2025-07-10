from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.web import WebClient
from bot.utils import get_s3_presigned_url

from slack_sdk.socket_mode import SocketModeClient

import logging

logger = logging.getLogger(__name__)

class EventHandler:
    def __init__(self, web_client):
        """Initialize the EventHandler with necessary components and handlers."""
        self.web_client = web_client

    async def handle_request(self, client, req):
        # ✅ Acknowledge the request
        await client.send_socket_mode_response({
            "envelope_id": req.envelope_id
        })

        # Slash command
        if req.type == "slash_commands":
            payload = req.payload
            user_id = payload.get("user_id")
            channel_id = payload.get("channel_id")
            command = payload.get("command")

          
            await client.web_client.chat_postMessage(
                channel=channel_id,
                text=f"Hey <@{user_id}>, you used the `{command}` command!"
            )

        elif req.type == "events_api":
            event = req.payload.get("event", {})
            event_type = event.get("type")

            if event_type == "message" and not event.get("bot_id"):
                text = event.get("text", "").strip().lower()
                
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
