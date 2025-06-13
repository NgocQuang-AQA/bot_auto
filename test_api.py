#!/usr/bin/env python3
"""
Bot Slack Service API Tests

This script provides comprehensive testing for the Bot Slack service API endpoints.
It includes unit tests, integration tests, and performance tests.
"""

import unittest
import requests
import json
import time
import threading
from unittest.mock import patch, MagicMock
import sys
import os

# Add the current directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from config import Config

class TestBotSlackAPI(unittest.TestCase):
    """Test cases for Bot Slack API"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
        cls.base_url = 'http://localhost:5000'
    
    def setUp(self):
        """Set up each test"""
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        self.slack_data = {
            'token': 'test-token',
            'team_id': 'T1234567890',
            'team_domain': 'test-team',
            'channel_id': 'C1234567890',
            'channel_name': 'test-channel',
            'user_id': 'U1234567890',
            'user_name': 'testuser',
            'command': '/bot-slack',
            'response_url': 'https://hooks.slack.com/commands/1234/5678'
        }
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get('/health')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('status', data)
        self.assertIn('version', data)
        self.assertIn('uptime', data)
        self.assertIn('services', data)
    
    def test_metrics_endpoint(self):
        """Test metrics endpoint"""
        response = self.client.get('/metrics')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertIn('system', data)
        self.assertIn('application', data)
    
    def test_help_command(self):
        """Test help command"""
        data = self.slack_data.copy()
        data['text'] = 'help'
        
        response = self.client.post('/bot-slack/help', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertIn('text', response_data)
        self.assertIn('Available commands', response_data['text'])
    
    @patch('slack_service.SlackService.send_message')
    def test_run_command_valid_project(self, mock_send):
        """Test run command with valid project"""
        mock_send.return_value = True
        
        data = self.slack_data.copy()
        data['text'] = 'mlm'
        
        response = self.client.post('/bot-slack/run', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertIn('text', response_data)
    
    def test_run_command_invalid_project(self):
        """Test run command with invalid project"""
        data = self.slack_data.copy()
        data['text'] = 'invalid_project'
        
        response = self.client.post('/bot-slack/run', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertIn('text', response_data)
        self.assertIn('Invalid project', response_data['text'])
    
    def test_run_command_no_project(self):
        """Test run command without project parameter"""
        data = self.slack_data.copy()
        data['text'] = ''
        
        response = self.client.post('/bot-slack/run', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertIn('text', response_data)
        self.assertIn('Please specify a project', response_data['text'])
    
    @patch('report_service.ReportService.generate_report')
    def test_report_command(self, mock_report):
        """Test report command"""
        mock_report.return_value = "Test report generated"
        
        data = self.slack_data.copy()
        data['text'] = 'mlm'
        
        response = self.client.post('/bot-slack/report', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertIn('text', response_data)
    
    @patch('process_service.ProcessService.stop_docker_container')
    def test_stop_command(self, mock_stop):
        """Test stop command"""
        mock_stop.return_value = True
        
        data = self.slack_data.copy()
        data['text'] = 'mlm'
        
        response = self.client.post('/bot-slack/stop', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertIn('text', response_data)
    
    @patch('process_service.ProcessService.pull_docker_image')
    def test_deploy_command(self, mock_deploy):
        """Test deploy command"""
        mock_deploy.return_value = True
        
        data = self.slack_data.copy()
        data['text'] = 'mlm'
        
        response = self.client.post('/bot-slack/deploy', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertIn('text', response_data)
    
    def test_status_command(self):
        """Test status command"""
        data = self.slack_data.copy()
        
        response = self.client.post('/bot-slack/status', data=data, headers=self.headers)
        self.assertEqual(response.status_code, 200)
        
        response_data = json.loads(response.data)
        self.assertIn('text', response_data)
    
    def test_invalid_endpoint(self):
        """Test invalid endpoint"""
        response = self.client.get('/invalid-endpoint')
        self.assertEqual(response.status_code, 404)
    
    def test_method_not_allowed(self):
        """Test method not allowed"""
        response = self.client.get('/bot-slack/run')
        self.assertEqual(response.status_code, 405)

class TestAPIPerformance(unittest.TestCase):
    """Performance tests for the API"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        cls.app = app
        cls.app.config['TESTING'] = True
        cls.client = cls.app.test_client()
    
    def test_health_endpoint_performance(self):
        """Test health endpoint response time"""
        start_time = time.time()
        response = self.client.get('/health')
        end_time = time.time()
        
        response_time = end_time - start_time
        self.assertEqual(response.status_code, 200)
        self.assertLess(response_time, 1.0)  # Should respond within 1 second
    
    def test_concurrent_requests(self):
        """Test handling of concurrent requests"""
        def make_request():
            response = self.client.get('/health')
            return response.status_code
        
        threads = []
        results = []
        
        # Create 10 concurrent threads
        for _ in range(10):
            thread = threading.Thread(target=lambda: results.append(make_request()))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should succeed
        self.assertEqual(len(results), 10)
        self.assertTrue(all(status == 200 for status in results))

class TestLiveAPI(unittest.TestCase):
    """Live API tests (requires running server)"""
    
    def setUp(self):
        """Set up live tests"""
        self.base_url = 'http://localhost:5000'
        self.timeout = 5
    
    def test_live_health_endpoint(self):
        """Test live health endpoint"""
        try:
            response = requests.get(f'{self.base_url}/health', timeout=self.timeout)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn('status', data)
            self.assertEqual(data['status'], 'healthy')
        except requests.exceptions.ConnectionError:
            self.skipTest("Server not running")
    
    def test_live_metrics_endpoint(self):
        """Test live metrics endpoint"""
        try:
            response = requests.get(f'{self.base_url}/metrics', timeout=self.timeout)
            self.assertEqual(response.status_code, 200)
            
            data = response.json()
            self.assertIn('system', data)
            self.assertIn('application', data)
        except requests.exceptions.ConnectionError:
            self.skipTest("Server not running")

def run_unit_tests():
    """Run unit tests"""
    print("\n🧪 Running Unit Tests...")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBotSlackAPI)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

def run_performance_tests():
    """Run performance tests"""
    print("\n⚡ Running Performance Tests...")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAPIPerformance)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

def run_live_tests():
    """Run live API tests"""
    print("\n🌐 Running Live API Tests...")
    suite = unittest.TestLoader().loadTestsFromTestCase(TestLiveAPI)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()

def main():
    """Main test runner"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Bot Slack API Test Suite')
    parser.add_argument('--unit', action='store_true', help='Run unit tests')
    parser.add_argument('--performance', action='store_true', help='Run performance tests')
    parser.add_argument('--live', action='store_true', help='Run live API tests')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    
    args = parser.parse_args()
    
    if not any([args.unit, args.performance, args.live, args.all]):
        args.all = True
    
    success = True
    
    if args.unit or args.all:
        success &= run_unit_tests()
    
    if args.performance or args.all:
        success &= run_performance_tests()
    
    if args.live or args.all:
        success &= run_live_tests()
    
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()