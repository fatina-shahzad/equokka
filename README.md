
```
# Slack Bot

A Python-based Slack bot using Socket Mode for real-time event handling. The bot maintains a stable connection to Slack, processes incoming events, and supports automatic reconnection and graceful shutdown.

## Features

- Real-time Slack event handling via Socket Mode
- Asynchronous operation using `asyncio`
- Automatic reconnection with retry logic
- Configurable logging for development and production
- Environment-based credential management
- Podcast generation on free text commands
- Infographic generation on free text commands

## Requirements

- Python 3.8+
- Slack App with Socket Mode enabled
- Slack Bot Token (`xoxb-...`)
- Slack App Token (`xapp-...`)
- [slack-sdk](https://pypi.org/project/slack-sdk/)
- [python-dotenv](https://pypi.org/project/python-dotenv/)

## Installation

```bash
git clone https://github.com/fatina-shahzad/equokka.git
cd slackbot
pip install -r requirements.txt
```

## Configuration
Setup a Slack App in your own Slack workspace and enable Socket Mode. Obtain the necessary tokens.
Create a `.env` file in the project root with the following variables:

```
SLACK_APP_TOKEN=xapp-...
SLACK_BOT_TOKEN=xoxb-...
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
S3_BUCKET_NAME_PODCASTS=
S3_BUCKET_NAME_MINDMAPS=
ENV=development  # or production
```

## Usage

Run the bot with:

```bash
python main.py
```

## Project Structure

- `main.py` — Application entry point
- `bot/slack_bot.py` — Slack bot implementation
- `bot/event_handler.py` — Event handling logic


(Note: Once the bot is running, you can interact with it in your Slack workspace. 
For podcast generation, you can send a message like follows:
'podcast on loan policy', 
'podcast on asset policy', 
'podcast on gym passport'.

For infographic generation, you can send a message like follows:
'loan policy',
'slack guidelines',
'leave request procedure'
)



