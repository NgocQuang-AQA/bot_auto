# conftest.py - Pytest configuration and shared fixtures
# This file contains common test fixtures and configuration for the Bot Slack Service

import os
import sys
import pytest
import tempfile
import shutil
from unittest.mock import Mock, patch
from flask import Flask

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Test configuration
TEST_CONFIG = {
    'TESTING': True,
    'DEBUG': True,
    'SLACK_BOT_TOKEN': 'xoxb-test-token',
    'SLACK_SIGNING_SECRET': 'test-signing-secret',
    'FLASK_ENV': 'testing',
    'LOG_LEVEL': 'DEBUG',
    'REPORT_PATHS': {
        'test_project': '/tmp/test/reports'
    },
    'BATCH_PATHS': {
        'test_project': '/tmp/test/batch.bat'
    },
    'SUPPORTED_PROJECTS': ['test_project'],
    'DATABASE_URL': 'sqlite:///:memory:',
    'SECRET_KEY': 'test-secret-key'
}


@pytest.fixture(scope='session')
def test_config():
    """Provide test configuration."""
    return TEST_CONFIG.copy()


@pytest.fixture(scope='session')
def temp_dir():
    """Create a temporary directory for test files."""
    temp_path = tempfile.mkdtemp(prefix='bot_slack_test_')
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope='function')
def mock_env_vars(test_config):
    """Mock environment variables for testing."""
    with patch.dict(os.environ, test_config, clear=False):
        yield


@pytest.fixture(scope='function')
def flask_app(test_config, temp_dir):
    """Create a Flask app instance for testing."""
    # Update config with temp directory paths
    config = test_config.copy()
    config['REPORT_PATHS'] = {'test_project': os.path.join(temp_dir, 'reports')}
    config['BATCH_PATHS'] = {'test_project': os.path.join(temp_dir, 'batch.bat')}
    
    # Create directories
    os.makedirs(config['REPORT_PATHS']['test_project'], exist_ok=True)
    
    # Create test batch file
    with open(config['BATCH_PATHS']['test_project'], 'w') as f:
        f.write('@echo off\necho Test batch file\n')
    
    app = Flask(__name__)
    app.config.update(config)
    
    # Add test routes
    @app.route('/health')
    def health():
        return {'status': 'healthy'}, 200
    
    @app.route('/test')
    def test_route():
        return {'message': 'test'}, 200
    
    with app.app_context():
        yield app


@pytest.fixture(scope='function')
def client(flask_app):
    """Create a test client for the Flask app."""
    return flask_app.test_client()


@pytest.fixture(scope='function')
def mock_slack_client():
    """Mock Slack WebClient for testing."""
    mock_client = Mock()
    
    # Mock successful responses
    mock_client.chat_postMessage.return_value = {
        'ok': True,
        'message': {
            'ts': '1234567890.123456',
            'text': 'Test message'
        }
    }
    
    mock_client.conversations_list.return_value = {
        'ok': True,
        'channels': [
            {
                'id': 'C1234567890',
                'name': 'general',
                'is_member': True
            }
        ]
    }
    
    mock_client.auth_test.return_value = {
        'ok': True,
        'user_id': 'U1234567890',
        'team_id': 'T1234567890'
    }
    
    return mock_client


@pytest.fixture(scope='function')
def mock_slack_service(mock_slack_client):
    """Mock SlackService for testing."""
    with patch('services.slack_service.WebClient', return_value=mock_slack_client):
        from services.slack_service import SlackService
        service = SlackService()
        yield service


@pytest.fixture(scope='function')
def mock_process_service():
    """Mock ProcessService for testing."""
    mock_service = Mock()
    
    # Mock successful process execution
    mock_service.run_batch_file.return_value = {
        'success': True,
        'output': 'Process completed successfully',
        'error': None,
        'return_code': 0
    }
    
    mock_service.stop_containers.return_value = {
        'success': True,
        'stopped_containers': ['container1', 'container2'],
        'message': 'Containers stopped successfully'
    }
    
    return mock_service


@pytest.fixture(scope='function')
def mock_report_service(temp_dir):
    """Mock ReportService for testing."""
    mock_service = Mock()
    
    # Create test report file
    report_path = os.path.join(temp_dir, 'test_report.txt')
    with open(report_path, 'w') as f:
        f.write('Test report content\nLine 2\nLine 3')
    
    mock_service.read_report.return_value = {
        'success': True,
        'content': 'Test report content\nLine 2\nLine 3',
        'file_path': report_path
    }
    
    mock_service.list_reports.return_value = {
        'success': True,
        'reports': ['test_report.txt'],
        'count': 1
    }
    
    return mock_service


@pytest.fixture(scope='function')
def mock_docker_client():
    """Mock Docker client for testing."""
    mock_client = Mock()
    
    # Mock container operations
    mock_container = Mock()
    mock_container.name = 'test_container'
    mock_container.status = 'running'
    mock_container.stop.return_value = None
    mock_container.remove.return_value = None
    
    mock_client.containers.list.return_value = [mock_container]
    mock_client.containers.get.return_value = mock_container
    
    return mock_client


@pytest.fixture(scope='function')
def sample_slack_event():
    """Provide a sample Slack event for testing."""
    return {
        'type': 'message',
        'channel': 'C1234567890',
        'user': 'U1234567890',
        'text': 'Hello, bot!',
        'ts': '1234567890.123456',
        'event_ts': '1234567890.123456',
        'channel_type': 'channel'
    }


@pytest.fixture(scope='function')
def sample_slack_command():
    """Provide a sample Slack slash command for testing."""
    return {
        'token': 'test-token',
        'team_id': 'T1234567890',
        'team_domain': 'test-team',
        'channel_id': 'C1234567890',
        'channel_name': 'general',
        'user_id': 'U1234567890',
        'user_name': 'testuser',
        'command': '/bot-slack',
        'text': 'help',
        'response_url': 'https://hooks.slack.com/commands/1234/5678',
        'trigger_id': '1234567890.123456.abcdef'
    }


@pytest.fixture(scope='function')
def mock_file_system(temp_dir):
    """Mock file system operations for testing."""
    # Create test directory structure
    test_dirs = [
        'reports',
        'logs',
        'batch',
        'config'
    ]
    
    for dir_name in test_dirs:
        os.makedirs(os.path.join(temp_dir, dir_name), exist_ok=True)
    
    # Create test files
    test_files = {
        'reports/test_report.txt': 'Test report content',
        'logs/app.log': 'Test log content',
        'batch/test.bat': '@echo off\necho Test batch',
        'config/test.conf': 'test_setting=value'
    }
    
    for file_path, content in test_files.items():
        full_path = os.path.join(temp_dir, file_path)
        with open(full_path, 'w') as f:
            f.write(content)
    
    return temp_dir


@pytest.fixture(scope='function')
def mock_logging():
    """Mock logging for testing."""
    with patch('logging.getLogger') as mock_logger:
        logger_instance = Mock()
        mock_logger.return_value = logger_instance
        yield logger_instance


@pytest.fixture(scope='function')
def mock_requests():
    """Mock requests library for testing."""
    with patch('requests.post') as mock_post, \
         patch('requests.get') as mock_get:
        
        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'ok': True}
        mock_response.text = 'Success'
        
        mock_post.return_value = mock_response
        mock_get.return_value = mock_response
        
        yield {
            'post': mock_post,
            'get': mock_get,
            'response': mock_response
        }


@pytest.fixture(scope='function')
def mock_subprocess():
    """Mock subprocess operations for testing."""
    with patch('subprocess.run') as mock_run, \
         patch('subprocess.Popen') as mock_popen:
        
        # Mock successful subprocess execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = 'Process completed successfully'
        mock_result.stderr = ''
        
        mock_run.return_value = mock_result
        
        # Mock Popen
        mock_process = Mock()
        mock_process.communicate.return_value = ('Success', '')
        mock_process.returncode = 0
        mock_popen.return_value = mock_process
        
        yield {
            'run': mock_run,
            'popen': mock_popen,
            'result': mock_result,
            'process': mock_process
        }


@pytest.fixture(autouse=True)
def setup_test_environment(mock_env_vars):
    """Automatically set up test environment for all tests."""
    # This fixture runs automatically for all tests
    # Set up any global test configuration here
    pass


@pytest.fixture(scope='function')
def clean_imports():
    """Clean up imported modules after test."""
    # Store original modules
    original_modules = sys.modules.copy()
    
    yield
    
    # Remove any modules that were imported during the test
    modules_to_remove = []
    for module_name in sys.modules:
        if module_name not in original_modules:
            modules_to_remove.append(module_name)
    
    for module_name in modules_to_remove:
        if module_name in sys.modules:
            del sys.modules[module_name]


# Pytest configuration
def pytest_configure(config):
    """Configure pytest settings."""
    # Add custom markers
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "external: mark test as requiring external services"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file location."""
    for item in items:
        # Add markers based on test file location
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        
        # Add slow marker for tests that might take longer
        if "slow" in item.name or "performance" in str(item.fspath):
            item.add_marker(pytest.mark.slow)


# Custom pytest fixtures for specific test scenarios
@pytest.fixture(scope='function')
def error_scenario():
    """Fixture for testing error scenarios."""
    return {
        'slack_error': {
            'ok': False,
            'error': 'channel_not_found'
        },
        'process_error': {
            'success': False,
            'error': 'Process execution failed',
            'return_code': 1
        },
        'file_error': FileNotFoundError('Test file not found')
    }


@pytest.fixture(scope='function')
def performance_data():
    """Fixture for performance testing data."""
    return {
        'large_message': 'x' * 1000,  # 1KB message
        'many_items': list(range(1000)),
        'complex_data': {
            'nested': {
                'data': {
                    'with': {
                        'many': {
                            'levels': 'value'
                        }
                    }
                }
            }
        }
    }