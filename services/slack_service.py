import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from config.settings import Config

logger = logging.getLogger(__name__)

class SlackService:
    """Service for Slack API interactions"""
    
    def __init__(self):
        self.client = WebClient(token=Config.SLACK_TOKEN)
        self.channel = Config.SLACK_CHANNEL
    
    def send_message(self, message: str, ephemeral: bool = False) -> bool:
        """Send message to Slack channel
        
        Args:
            message: Message content
            ephemeral: Whether message should be ephemeral
            
        Returns:
            bool: Success status
        """
        try:
            response = self.client.chat_postMessage(
                channel=self.channel,
                text=message
            )
            logger.info(f"Message sent successfully: {response['ts']}")
            return True
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error sending message: {str(e)}")
            return False
    
    def send_formatted_message(self, blocks: list) -> bool:
        """Send formatted message with blocks
        
        Args:
            blocks: Slack block kit blocks
            
        Returns:
            bool: Success status
        """
        try:
            response = self.client.chat_postMessage(
                channel=self.channel,
                blocks=blocks
            )
            logger.info(f"Formatted message sent successfully: {response['ts']}")
            return True
            
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            return False
            
        except Exception as e:
            logger.error(f"Unexpected error sending formatted message: {str(e)}")
            return False