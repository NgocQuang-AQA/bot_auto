# test_slack_service.py - Unit tests for SlackService
# This file contains comprehensive unit tests for the Slack service functionality

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from slack_sdk.errors import SlackApiError

# Import the service to test
try:
    from services.slack_service import SlackService
except ImportError:
    # Fallback for testing without full project structure
    SlackService = None


class TestSlackService:
    """Test cases for SlackService class."""
    
    @pytest.fixture
    def slack_service(self, mock_slack_client):
        """Create SlackService instance with mocked client."""
        if SlackService is None:
            pytest.skip("SlackService not available")
        
        with patch('services.slack_service.WebClient', return_value=mock_slack_client):
            service = SlackService()
            return service
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration for testing."""
        return {
            'SLACK_BOT_TOKEN': 'xoxb-test-token',
            'SLACK_SIGNING_SECRET': 'test-signing-secret'
        }
    
    def test_init_with_valid_token(self, mock_config):
        """Test SlackService initialization with valid token."""
        if SlackService is None:
            pytest.skip("SlackService not available")
        
        with patch.dict(os.environ, mock_config):
            with patch('services.slack_service.WebClient') as mock_client:
                service = SlackService()
                assert service is not None
                mock_client.assert_called_once()
    
    def test_init_without_token(self):
        """Test SlackService initialization without token."""
        if SlackService is None:
            pytest.skip("SlackService not available")
        
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises((ValueError, KeyError)):
                SlackService()
    
    def test_send_message_success(self, slack_service, mock_slack_client):
        """Test successful message sending."""
        # Arrange
        channel = "#general"
        message = "Test message"
        
        # Act
        result = slack_service.send_message(channel, message)
        
        # Assert
        assert result is not None
        mock_slack_client.chat_postMessage.assert_called_once_with(
            channel=channel,
            text=message
        )
    
    def test_send_message_with_blocks(self, slack_service, mock_slack_client):
        """Test sending message with blocks."""
        # Arrange
        channel = "#general"
        message = "Test message"
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "Test block"
                }
            }
        ]
        
        # Act
        result = slack_service.send_message(channel, message, blocks=blocks)
        
        # Assert
        assert result is not None
        mock_slack_client.chat_postMessage.assert_called_once_with(
            channel=channel,
            text=message,
            blocks=blocks
        )
    
    def test_send_message_api_error(self, slack_service, mock_slack_client):
        """Test message sending with API error."""
        # Arrange
        channel = "#general"
        message = "Test message"
        mock_slack_client.chat_postMessage.side_effect = SlackApiError(
            message="channel_not_found",
            response={"error": "channel_not_found"}
        )
        
        # Act & Assert
        with pytest.raises(SlackApiError):
            slack_service.send_message(channel, message)
    
    def test_send_formatted_message(self, slack_service, mock_slack_client):
        """Test sending formatted message."""
        # Arrange
        channel = "#general"
        title = "Test Title"
        message = "Test message"
        color = "good"
        
        # Act
        result = slack_service.send_formatted_message(channel, title, message, color)
        
        # Assert
        assert result is not None
        mock_slack_client.chat_postMessage.assert_called_once()
        call_args = mock_slack_client.chat_postMessage.call_args
        assert call_args[1]['channel'] == channel
        assert 'attachments' in call_args[1]
    
    def test_send_formatted_message_with_fields(self, slack_service, mock_slack_client):
        """Test sending formatted message with fields."""
        # Arrange
        channel = "#general"
        title = "Test Title"
        message = "Test message"
        fields = [
            {"title": "Field 1", "value": "Value 1", "short": True},
            {"title": "Field 2", "value": "Value 2", "short": False}
        ]
        
        # Act
        result = slack_service.send_formatted_message(
            channel, title, message, fields=fields
        )
        
        # Assert
        assert result is not None
        call_args = mock_slack_client.chat_postMessage.call_args
        attachments = call_args[1]['attachments']
        assert len(attachments) > 0
        assert 'fields' in attachments[0]
        assert len(attachments[0]['fields']) == 2
    
    def test_get_channel_info(self, slack_service, mock_slack_client):
        """Test getting channel information."""
        # Arrange
        channel_id = "C1234567890"
        mock_slack_client.conversations_info.return_value = {
            'ok': True,
            'channel': {
                'id': channel_id,
                'name': 'general',
                'is_member': True
            }
        }
        
        # Act
        result = slack_service.get_channel_info(channel_id)
        
        # Assert
        assert result is not None
        assert result['ok'] is True
        mock_slack_client.conversations_info.assert_called_once_with(channel=channel_id)
    
    def test_list_channels(self, slack_service, mock_slack_client):
        """Test listing channels."""
        # Arrange
        mock_slack_client.conversations_list.return_value = {
            'ok': True,
            'channels': [
                {'id': 'C1234567890', 'name': 'general'},
                {'id': 'C0987654321', 'name': 'random'}
            ]
        }
        
        # Act
        result = slack_service.list_channels()
        
        # Assert
        assert result is not None
        assert result['ok'] is True
        assert len(result['channels']) == 2
        mock_slack_client.conversations_list.assert_called_once()
    
    def test_validate_token(self, slack_service, mock_slack_client):
        """Test token validation."""
        # Arrange
        mock_slack_client.auth_test.return_value = {
            'ok': True,
            'user_id': 'U1234567890',
            'team_id': 'T1234567890'
        }
        
        # Act
        result = slack_service.validate_token()
        
        # Assert
        assert result is not None
        assert result['ok'] is True
        mock_slack_client.auth_test.assert_called_once()
    
    def test_validate_token_invalid(self, slack_service, mock_slack_client):
        """Test token validation with invalid token."""
        # Arrange
        mock_slack_client.auth_test.side_effect = SlackApiError(
            message="invalid_auth",
            response={"error": "invalid_auth"}
        )
        
        # Act & Assert
        with pytest.raises(SlackApiError):
            slack_service.validate_token()
    
    def test_upload_file(self, slack_service, mock_slack_client):
        """Test file upload."""
        # Arrange
        channel = "#general"
        file_path = "/tmp/test.txt"
        filename = "test.txt"
        title = "Test File"
        
        mock_slack_client.files_upload.return_value = {
            'ok': True,
            'file': {
                'id': 'F1234567890',
                'name': filename
            }
        }
        
        # Act
        result = slack_service.upload_file(channel, file_path, filename, title)
        
        # Assert
        assert result is not None
        assert result['ok'] is True
        mock_slack_client.files_upload.assert_called_once()
    
    def test_delete_message(self, slack_service, mock_slack_client):
        """Test message deletion."""
        # Arrange
        channel = "#general"
        timestamp = "1234567890.123456"
        
        mock_slack_client.chat_delete.return_value = {
            'ok': True,
            'ts': timestamp
        }
        
        # Act
        result = slack_service.delete_message(channel, timestamp)
        
        # Assert
        assert result is not None
        assert result['ok'] is True
        mock_slack_client.chat_delete.assert_called_once_with(
            channel=channel,
            ts=timestamp
        )
    
    def test_update_message(self, slack_service, mock_slack_client):
        """Test message update."""
        # Arrange
        channel = "#general"
        timestamp = "1234567890.123456"
        new_text = "Updated message"
        
        mock_slack_client.chat_update.return_value = {
            'ok': True,
            'ts': timestamp,
            'text': new_text
        }
        
        # Act
        result = slack_service.update_message(channel, timestamp, new_text)
        
        # Assert
        assert result is not None
        assert result['ok'] is True
        mock_slack_client.chat_update.assert_called_once_with(
            channel=channel,
            ts=timestamp,
            text=new_text
        )
    
    def test_add_reaction(self, slack_service, mock_slack_client):
        """Test adding reaction to message."""
        # Arrange
        channel = "#general"
        timestamp = "1234567890.123456"
        emoji = "thumbsup"
        
        mock_slack_client.reactions_add.return_value = {
            'ok': True
        }
        
        # Act
        result = slack_service.add_reaction(channel, timestamp, emoji)
        
        # Assert
        assert result is not None
        assert result['ok'] is True
        mock_slack_client.reactions_add.assert_called_once_with(
            channel=channel,
            timestamp=timestamp,
            name=emoji
        )
    
    def test_get_user_info(self, slack_service, mock_slack_client):
        """Test getting user information."""
        # Arrange
        user_id = "U1234567890"
        mock_slack_client.users_info.return_value = {
            'ok': True,
            'user': {
                'id': user_id,
                'name': 'testuser',
                'real_name': 'Test User'
            }
        }
        
        # Act
        result = slack_service.get_user_info(user_id)
        
        # Assert
        assert result is not None
        assert result['ok'] is True
        mock_slack_client.users_info.assert_called_once_with(user=user_id)
    
    def test_send_ephemeral_message(self, slack_service, mock_slack_client):
        """Test sending ephemeral message."""
        # Arrange
        channel = "#general"
        user = "U1234567890"
        message = "Ephemeral message"
        
        mock_slack_client.chat_postEphemeral.return_value = {
            'ok': True,
            'message_ts': '1234567890.123456'
        }
        
        # Act
        result = slack_service.send_ephemeral_message(channel, user, message)
        
        # Assert
        assert result is not None
        assert result['ok'] is True
        mock_slack_client.chat_postEphemeral.assert_called_once_with(
            channel=channel,
            user=user,
            text=message
        )
    
    @pytest.mark.parametrize("channel,expected", [
        ("#general", "#general"),
        ("general", "#general"),
        ("C1234567890", "C1234567890"),
        ("@user", "@user")
    ])
    def test_format_channel(self, slack_service, channel, expected):
        """Test channel formatting."""
        # Act
        result = slack_service._format_channel(channel)
        
        # Assert
        assert result == expected
    
    def test_error_handling_network_error(self, slack_service, mock_slack_client):
        """Test error handling for network errors."""
        # Arrange
        channel = "#general"
        message = "Test message"
        mock_slack_client.chat_postMessage.side_effect = Exception("Network error")
        
        # Act & Assert
        with pytest.raises(Exception):
            slack_service.send_message(channel, message)
    
    def test_rate_limiting_handling(self, slack_service, mock_slack_client):
        """Test rate limiting handling."""
        # Arrange
        channel = "#general"
        message = "Test message"
        
        # Simulate rate limiting error
        rate_limit_error = SlackApiError(
            message="rate_limited",
            response={
                "error": "rate_limited",
                "headers": {"Retry-After": "30"}
            }
        )
        mock_slack_client.chat_postMessage.side_effect = rate_limit_error
        
        # Act & Assert
        with pytest.raises(SlackApiError):
            slack_service.send_message(channel, message)
    
    def test_message_formatting_special_characters(self, slack_service, mock_slack_client):
        """Test message formatting with special characters."""
        # Arrange
        channel = "#general"
        message = "Test message with <special> &characters& and *formatting*"
        
        # Act
        result = slack_service.send_message(channel, message)
        
        # Assert
        assert result is not None
        mock_slack_client.chat_postMessage.assert_called_once_with(
            channel=channel,
            text=message
        )
    
    def test_large_message_handling(self, slack_service, mock_slack_client):
        """Test handling of large messages."""
        # Arrange
        channel = "#general"
        large_message = "x" * 4000  # Slack has a 4000 character limit
        
        # Act
        result = slack_service.send_message(channel, large_message)
        
        # Assert
        assert result is not None
        mock_slack_client.chat_postMessage.assert_called_once()
    
    def test_concurrent_message_sending(self, slack_service, mock_slack_client):
        """Test concurrent message sending."""
        import threading
        import time
        
        # Arrange
        channel = "#general"
        messages = [f"Message {i}" for i in range(5)]
        results = []
        
        def send_message(msg):
            result = slack_service.send_message(channel, msg)
            results.append(result)
        
        # Act
        threads = []
        for message in messages:
            thread = threading.Thread(target=send_message, args=(message,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Assert
        assert len(results) == 5
        assert mock_slack_client.chat_postMessage.call_count == 5
    
    def test_message_with_mentions(self, slack_service, mock_slack_client):
        """Test sending message with user mentions."""
        # Arrange
        channel = "#general"
        message = "Hello <@U1234567890>! How are you?"
        
        # Act
        result = slack_service.send_message(channel, message)
        
        # Assert
        assert result is not None
        mock_slack_client.chat_postMessage.assert_called_once_with(
            channel=channel,
            text=message
        )
    
    def test_message_with_channel_mentions(self, slack_service, mock_slack_client):
        """Test sending message with channel mentions."""
        # Arrange
        channel = "#general"
        message = "Please check <#C1234567890|random> channel"
        
        # Act
        result = slack_service.send_message(channel, message)
        
        # Assert
        assert result is not None
        mock_slack_client.chat_postMessage.assert_called_once_with(
            channel=channel,
            text=message
        )


class TestSlackServiceIntegration:
    """Integration tests for SlackService."""
    
    @pytest.mark.integration
    def test_real_slack_connection(self):
        """Test real Slack connection (requires valid token)."""
        # This test requires a real Slack token and should be run separately
        token = os.getenv('SLACK_BOT_TOKEN_REAL')
        if not token:
            pytest.skip("Real Slack token not provided")
        
        # This would test actual Slack API calls
        # Implementation depends on having a test Slack workspace
        pass
    
    @pytest.mark.integration
    def test_slack_service_with_real_config(self, test_config):
        """Test SlackService with realistic configuration."""
        if SlackService is None:
            pytest.skip("SlackService not available")
        
        with patch.dict(os.environ, test_config):
            with patch('services.slack_service.WebClient') as mock_client:
                service = SlackService()
                assert service is not None
                mock_client.assert_called_once()


if __name__ == '__main__':
    pytest.main([__file__])