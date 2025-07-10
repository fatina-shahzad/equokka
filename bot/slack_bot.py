"""
Slack Bot Implementation Module.

This module provides the core implementation of a Slack bot using Socket Mode.
It handles real-time message events, maintains connection with Slack,
and provides retry mechanisms for connection stability.

Classes:
    SlackBot: Main class for managing Slack bot operations and lifecycle.
"""

import asyncio
import logging
from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.web.async_client import AsyncWebClient
from bot.event_handler import EventHandler

# Create a logger for this module
logger = logging.getLogger(__name__)


class SlackBot:
    """
    A class to manage Slack bot operations using Socket Mode.

    This class handles the lifecycle of a Slack bot, including connection management,
    event handling, and graceful shutdown. It implements automatic reconnection logic
    and proper error handling.

    Attributes:
        app_token (str): Slack app-level token for Socket Mode.
        bot_token (str): Slack bot user token for API calls.
        web_client (AsyncWebClient): Async client for Slack Web API calls.
        socket_client (SocketModeClient): Client for Socket Mode connection.
        event_handler (EventHandler): Handler for processing Slack events.

    Args:
        app_token (str): Slack app-level token starting with 'xapp-'.
        bot_token (str): Slack bot user token starting with 'xoxb-'.
    """

    def __init__(self, app_token, bot_token):
        """
        Initialize the SlackBot with necessary tokens and clients.

        Args:
            app_token (str): Slack app-level token for Socket Mode.
            bot_token (str): Slack bot user token for API calls.

        Raises:
            ValueError: If tokens are empty or have invalid formats.
        """
        self.app_token = app_token
        self.bot_token = bot_token
        self.web_client = AsyncWebClient(token=bot_token, timeout=60)
        self.socket_client = SocketModeClient(
            app_token=app_token,
            web_client=self.web_client
        )
        self.event_handler = EventHandler(self.web_client)
        self.setup_listeners()

    def setup_listeners(self):
        """
        Configure event listeners for the Socket Mode client.

        Sets up the main event handler to process incoming Socket Mode requests.
        This method is called during initialization to establish event handling.
        """
        # Add the main event handler
        self.socket_client.socket_mode_request_listeners.append(
            self.event_handler.handle_request
        )

    async def start(self):
        """
        Start the bot and maintain the connection with automatic retry logic.

        Implements an exponential backoff retry mechanism for connection attempts.
        Continues running until maximum retry attempts are exhausted or interrupted.

        Raises:
            Exception: For unexpected errors during connection or operation.
        """
        retry_count = 0
        max_retries = 5
        retry_delay = 5  # seconds

        while retry_count < max_retries:
            try:
                logger.info("Attempting to connect to Slack...")
                await self.socket_client.connect()
                logger.info("Successfully connected to Slack!")
                retry_count = 0

                # Keep the connection alive
                while True:
                    try:
                        await asyncio.sleep(1)
                    except Exception as e:
                        logger.error(f"ERROR: Error in connection loop: {e}")
                        break

            except Exception as e:
                retry_count += 1
                logger.error(f"ERROR: Connection attempt {retry_count} failed: {e}")

                if retry_count < max_retries:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("ERROR: Max retries reached. Shutting down.")
                    break

    async def stop(self):
        """
        Gracefully shutdown the bot and clean up resources.

        Ensures proper disconnection from Slack and cleanup of any resources.
        Should be called before the application exits.

        Raises:
            Exception: If an error occurs during shutdown.
        """
        try:
            await self.socket_client.disconnect()
            logger.info("Bot disconnected successfully")
        except Exception as e:
            logger.error(f"ERROR: during shutdown: {e}")

    async def run(self):
        """
        Main entry point for running the bot.

        Handles the complete lifecycle of the bot including startup, operation,
        and shutdown. Implements proper error handling and cleanup.

        This method should be called to start the bot's operation.
        """
        try:
            await self.start()
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        except Exception as e:
            logger.error(f"ERROR: Unexpected error: {e}")
        finally:
            await self.stop()