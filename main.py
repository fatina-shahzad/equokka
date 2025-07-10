"""
Slack Bot Application Entry Point.

This module serves as the main entry point for a Slack bot application. It handles the initial setup,
configuration of logging, and launches the bot with appropriate credentials from environment variables.

The application supports different logging levels based on the environment (development/production).
"""

import asyncio
import logging
import os
from bot.slack_bot import SlackBot
from dotenv import load_dotenv

load_dotenv()

# Ensure AWS credentials are set in environment variables
os.environ["AWS_ACCESS_KEY_ID"] = os.getenv("AWS_ACCESS_KEY_ID")
os.environ["AWS_SECRET_ACCESS_KEY"] = os.getenv("AWS_SECRET_ACCESS_KEY")


def configure_logging():
    """
    Configure the application's logging settings based on the environment.

    The function sets up basic logging configuration with different levels:
    - DEBUG level for development environment
    - INFO level for production environment

    The environment is determined by the 'ENV' environment variable, defaulting to 'production'
    if not specified.

    Returns:
        None
    """
    # Get environment (default is "production")
    env = os.getenv("ENV", "production")

    # Set logging level based on environment
    if env == "development":
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO

    # Configure root logger
    logging.basicConfig(
        level=logging_level,  # Dynamically set the level
    )

async def main():
    """
    Initialize and run the Slack bot application.

    This asynchronous function performs the following operations:
    1. Logs the application startup
    2. Loads required Slack tokens from environment variables
    3. Initializes the SlackBot instance
    4. Runs the bot

    The function expects the following environment variables to be set:
    - SLACK_APP_TOKEN: The Slack app-level token
    - SLACK_BOT_TOKEN: The bot user OAuth token

    Returns:
        None

    Raises:
        EnvConfigError: If required environment variables are missing
    """
    logging.info("Starting the Slack bot application...")

    # Load environment variables
    slack_app_token = os.environ["SLACK_APP_TOKEN"]
    slack_bot_token = os.environ["SLACK_BOT_TOKEN"]

    # Initialize and run the bot
    bot = SlackBot(app_token=slack_app_token, bot_token=slack_bot_token)
    await bot.run()

if __name__ == "__main__":
    configure_logging()

    logging.info("Application started in %s environment", os.getenv("ENV", "production"))
    asyncio.run(main())