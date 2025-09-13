#!/usr/bin/env python3
"""
Comprehensive checker for ChatRoom module functionality.

This checker validates:
- ChatMessage serialization/deserialization
- ChatRoom initialization and configuration
- Message handling and publishing
- Peer connectivity and discovery
- Error handling and edge cases
- System logging functionality
"""

import asyncio
import json
import logging
import os
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch

# Import the ChatRoom module from the app directory
try:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))
    from chatroom import ChatRoom, ChatMessage, CHAT_TOPIC, PUBSUB_DISCOVERY_TOPIC
except ImportError as e:
    print(f"❌ Error importing ChatRoom module: {e}")
    print("   Expected file structure:")
    print("   checkpoint/")
    print("   ├── app/")
    print("   │   └── chatroom.py")
    print("   └── check.py")
    print(f"   Current directory: {os.getcwd()}")
    print(f"   Looking for: {os.path.join(os.getcwd(), 'app', 'chatroom.py')}")
    sys.exit(1)


class ChatRoomChecker:
    """Comprehensive checker for ChatRoom functionality."""
    
    def __init__(self):
        self.test_results = []
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for the checker."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("checker")
    
    def log_test_result(self, test_name: str, passed: bool, details: str = ""):
        """Log a test result."""
        status = "✅ PASS" if passed else "❌ FAIL"
        result = {
            'test': test_name,
            'passed': passed,
            'details': details,
            'timestamp': time.time()
        }
        self.test_results.append(result)
        
        log_message = f"{status}: {test_name}"
        if details:
            log_message += f" - {details}"
        
        if passed:
            self.logger.info(log_message)
        else:
            self.logger.error(log_message)
        
        print(log_message)
    
    def test_chat_message_functionality(self):
        """Test ChatMessage class functionality."""
        print("\n🧪 Testing ChatMessage functionality...")
        
        # Test 1: Basic message creation
        try:
            msg = ChatMessage("Hello world", "peer123", "Alice")
            assert msg.message == "Hello world"
            assert msg.sender_id == "peer123"
            assert msg.sender_nick == "Alice"
            assert msg.timestamp is not None
            self.log_test_result("ChatMessage creation", True)
        except Exception as e:
            self.log_test_result("ChatMessage creation", False, str(e))
        
        # Test 2: JSON serialization
        try:
            msg = ChatMessage("Test message", "peer456", "Bob", 1234567890.0)
            json_str = msg.to_json()
            data = json.loads(json_str)
            
            assert data["message"] == "Test message"
            assert data["sender_id"] == "peer456"
            assert data["sender_nick"] == "Bob"
            assert data["timestamp"] == 1234567890.0
            self.log_test_result("JSON serialization", True)
        except Exception as e:
            self.log_test_result("JSON serialization", False, str(e))
        
        # Test 3: JSON deserialization
        try:
            json_data = {
                "message": "Deserialized message",
                "sender_id": "peer789",
                "sender_nick": "Charlie",
                "timestamp": 9876543210.0
            }
            json_str = json.dumps(json_data)
            msg = ChatMessage.from_json(json_str)
            
            assert msg.message == "Deserialized message"
            assert msg.sender_id == "peer789"
            assert msg.sender_nick == "Charlie"
            assert msg.timestamp == 9876543210.0
            self.log_test_result("JSON deserialization", True)
        except Exception as e:
            self.log_test_result("JSON deserialization", False, str(e))
        
        # Test 4: Timestamp auto-generation
        try:
            msg = ChatMessage("Auto timestamp", "peer000", "Auto")
            assert msg.timestamp is not None
            assert isinstance(msg.timestamp, float)
            assert msg.timestamp > 0
            self.log_test_result("Auto timestamp generation", True)
        except Exception as e:
            self.log_test_result("Auto timestamp generation", False, str(e))
    
    def test_chatroom_initialization(self):
        """Test ChatRoom initialization."""
        print("\n🧪 Testing ChatRoom initialization...")
        
        # Create mock objects
        mock_host = MagicMock()
        mock_host.get_id.return_value = "test_peer_id_12345"
        
        mock_pubsub = MagicMock()
        mock_pubsub.peers = {}
        
        try:
            # Test 1: Basic initialization
            chatroom = ChatRoom(mock_host, mock_pubsub, "TestNick")
            
            assert chatroom.nickname == "TestNick"
            assert chatroom.peer_id == "test_peer_id_12345"
            assert chatroom.host == mock_host
            assert chatroom.pubsub == mock_pubsub
            assert not chatroom.running
            assert chatroom.message_handlers == []
            assert chatroom.system_message_handlers == []
            
            self.log_test_result("Basic ChatRoom initialization", True)
        except Exception as e:
            self.log_test_result("Basic ChatRoom initialization", False, str(e))
        
        try:
            # Test 2: Initialization with multiaddr
            chatroom = ChatRoom(mock_host, mock_pubsub, "TestNick", "/ip4/127.0.0.1/tcp/8080")
            assert chatroom.multiaddr == "/ip4/127.0.0.1/tcp/8080"
            self.log_test_result("ChatRoom initialization with multiaddr", True)
        except Exception as e:
            self.log_test_result("ChatRoom initialization with multiaddr", False, str(e))
    
    async def test_subscription_functionality(self):
        """Test subscription functionality."""
        print("\n🧪 Testing subscription functionality...")
        
        # Create mock objects
        mock_host = MagicMock()
        mock_host.get_id.return_value = "test_peer_subscription"
        
        mock_subscription = AsyncMock()
        mock_pubsub = AsyncMock()
        mock_pubsub.subscribe.return_value = mock_subscription
        mock_pubsub.peers = {}
        
        try:
            # Test subscription process
            chatroom = ChatRoom(mock_host, mock_pubsub, "SubTest")
            await chatroom._subscribe_to_topics()
            
            # Verify subscribe was called with correct topics
            expected_calls = [
                ((CHAT_TOPIC,),),
                ((PUBSUB_DISCOVERY_TOPIC,),)
            ]
            
            actual_calls = [call.args for call in mock_pubsub.subscribe.call_args_list]
            
            assert len(actual_calls) == 2
            assert (CHAT_TOPIC,) in actual_calls
            assert (PUBSUB_DISCOVERY_TOPIC,) in actual_calls
            
            self.log_test_result("Topic subscription", True)
        except Exception as e:
            self.log_test_result("Topic subscription", False, str(e))
    
    async def test_message_publishing(self):
        """Test message publishing functionality."""
        print("\n🧪 Testing message publishing...")
        
        # Create mock objects
        mock_host = MagicMock()
        mock_host.get_id.return_value = "test_peer_publish"
        
        mock_pubsub = AsyncMock()
        mock_pubsub.peers = {"peer1": MagicMock(), "peer2": MagicMock()}
        
        try:
            chatroom = ChatRoom(mock_host, mock_pubsub, "PubTest")
            
            # Test message publishing
            test_message = "Hello, this is a test message!"
            await chatroom.publish_message(test_message)
            
            # Verify publish was called correctly
            mock_pubsub.publish.assert_called_once_with(CHAT_TOPIC, test_message.encode())
            
            self.log_test_result("Message publishing", True)
        except Exception as e:
            self.log_test_result("Message publishing", False, str(e))
    
    def test_peer_management(self):
        """Test peer management functionality."""
        print("\n🧪 Testing peer management...")
        
        # Create mock objects
        mock_host = MagicMock()
        mock_host.get_id.return_value = "test_peer_mgmt"
        
        mock_pubsub = MagicMock()
        
        try:
            # Test 1: No peers connected
            mock_pubsub.peers = {}
            chatroom = ChatRoom(mock_host, mock_pubsub, "PeerTest")
            
            peers = chatroom.get_connected_peers()
            count = chatroom.get_peer_count()
            
            assert len(peers) == 0
            assert count == 0
            self.log_test_result("No peers connected", True)
        except Exception as e:
            self.log_test_result("No peers connected", False, str(e))
        
        try:
            # Test 2: Multiple peers connected
            mock_pubsub.peers = {
                "peer1": MagicMock(),
                "peer2": MagicMock(),
                "peer3": MagicMock()
            }
            chatroom = ChatRoom(mock_host, mock_pubsub, "PeerTest")
            
            peers = chatroom.get_connected_peers()
            count = chatroom.get_peer_count()
            
            assert len(peers) == 3
            assert count == 3
            assert "peer1" in peers
            assert "peer2" in peers
            assert "peer3" in peers
            self.log_test_result("Multiple peers connected", True)
        except Exception as e:
            self.log_test_result("Multiple peers connected", False, str(e))
    
    def test_message_handlers(self):
        """Test message handler management."""
        print("\n🧪 Testing message handlers...")
        
        # Create mock objects
        mock_host = MagicMock()
        mock_host.get_id.return_value = "test_peer_handlers"
        
        mock_pubsub = MagicMock()
        mock_pubsub.peers = {}
        
        try:
            chatroom = ChatRoom(mock_host, mock_pubsub, "HandlerTest")
            
            # Test adding message handlers
            handler1 = MagicMock()
            handler2 = MagicMock()
            
            chatroom.add_message_handler(handler1)
            chatroom.add_message_handler(handler2)
            
            assert len(chatroom.message_handlers) == 2
            assert handler1 in chatroom.message_handlers
            assert handler2 in chatroom.message_handlers
            
            self.log_test_result("Message handler management", True)
        except Exception as e:
            self.log_test_result("Message handler management", False, str(e))
        
        try:
            # Test adding system message handlers
            sys_handler1 = MagicMock()
            sys_handler2 = MagicMock()
            
            chatroom.add_system_message_handler(sys_handler1)
            chatroom.add_system_message_handler(sys_handler2)
            
            assert len(chatroom.system_message_handlers) == 2
            assert sys_handler1 in chatroom.system_message_handlers
            assert sys_handler2 in chatroom.system_message_handlers
            
            self.log_test_result("System message handler management", True)
        except Exception as e:
            self.log_test_result("System message handler management", False, str(e))
    
    def test_error_handling(self):
        """Test error handling scenarios."""
        print("\n🧪 Testing error handling...")
        
        try:
            # Test 1: Invalid JSON deserialization
            try:
                ChatMessage.from_json("invalid json")
                self.log_test_result("Invalid JSON handling", False, "Should have raised exception")
            except json.JSONDecodeError:
                self.log_test_result("Invalid JSON handling", True)
            except Exception as e:
                self.log_test_result("Invalid JSON handling", False, f"Wrong exception type: {e}")
        except Exception as e:
            self.log_test_result("Invalid JSON handling", False, str(e))
        
        try:
            # Test 2: Missing required JSON fields
            try:
                ChatMessage.from_json('{"message": "test"}')  # Missing sender_id and sender_nick
                self.log_test_result("Missing JSON fields handling", False, "Should have raised exception")
            except KeyError:
                self.log_test_result("Missing JSON fields handling", True)
            except Exception as e:
                self.log_test_result("Missing JSON fields handling", False, f"Wrong exception type: {e}")
        except Exception as e:
            self.log_test_result("Missing JSON fields handling", False, str(e))
    
    def test_system_logging(self):
        """Test system logging functionality."""
        print("\n🧪 Testing system logging...")
        
        try:
            
            # Create mock objects
            mock_host = MagicMock()
            mock_host.get_id.return_value = "test_peer_logging"
            
            mock_pubsub = MagicMock()
            mock_pubsub.peers = {}
            
            # Import the system logger from chatroom module to check its configuration
            from chatroom import system_logger
            
            # Check if system logger is properly configured
            has_file_handler = any(isinstance(handler, logging.FileHandler) 
                                 for handler in system_logger.handlers)
            
            # Check logger level and propagation settings
            correct_level = system_logger.level == logging.INFO
            correct_propagation = system_logger.propagate == False
            
            if has_file_handler and correct_level and correct_propagation:
                # Create ChatRoom to trigger some logging
                chatroom = ChatRoom(mock_host, mock_pubsub, "LogTest")
                
                # Test that _log_system_message method exists and is callable
                if hasattr(chatroom, '_log_system_message') and callable(chatroom._log_system_message):
                    self.log_test_result("System logging functionality", True, 
                                       "Logger properly configured with FileHandler")
                else:
                    self.log_test_result("System logging functionality", False, 
                                       "_log_system_message method not found")
            else:
                issues = []
                if not has_file_handler:
                    issues.append("No FileHandler found")
                if not correct_level:
                    issues.append(f"Wrong log level: {system_logger.level}")
                if not correct_propagation:
                    issues.append("Propagation should be False")
                
                self.log_test_result("System logging functionality", False, 
                                   f"Logger configuration issues: {', '.join(issues)}")
                    
        except ImportError as e:
            self.log_test_result("System logging functionality", False, 
                               f"Could not import system_logger: {e}")
        except Exception as e:
            self.log_test_result("System logging functionality", False, str(e))
    
    def test_constants_and_configuration(self):
        """Test constants and configuration values."""
        print("\n🧪 Testing constants and configuration...")
        
        try:
            # Test topic constants
            assert CHAT_TOPIC == "universal-connectivity"
            assert PUBSUB_DISCOVERY_TOPIC == "universal-connectivity-browser-peer-discovery"
            self.log_test_result("Topic constants", True)
        except Exception as e:
            self.log_test_result("Topic constants", False, str(e))
        
        try:
            # Test that constants are strings
            assert isinstance(CHAT_TOPIC, str)
            assert isinstance(PUBSUB_DISCOVERY_TOPIC, str)
            assert len(CHAT_TOPIC) > 0
            assert len(PUBSUB_DISCOVERY_TOPIC) > 0
            self.log_test_result("Topic constant types", True)
        except Exception as e:
            self.log_test_result("Topic constant types", False, str(e))
    
    async def run_all_tests(self):
        """Run all tests."""
        print("🚀 Starting ChatRoom module validation...")
        print("=" * 50)
        
        # Run synchronous tests
        self.test_chat_message_functionality()
        self.test_chatroom_initialization()
        self.test_peer_management()
        self.test_message_handlers()
        self.test_error_handling()
        self.test_system_logging()
        self.test_constants_and_configuration()
        
        # Run asynchronous tests
        await self.test_subscription_functionality()
        await self.test_message_publishing()
        
        # Generate summary
        self.generate_summary()
    
    def generate_summary(self):
        """Generate test summary report."""
        print("\n" + "=" * 50)
        print("📊 TEST SUMMARY")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['passed'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total tests run: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['passed']:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n🔍 DETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['passed'] else "❌"
            print(f"  {status} {result['test']}")
            if result['details']:
                print(f"      {result['details']}")
        
        # Save results to file
        self.save_results_to_file()
        
        # Return overall success
        return failed_tests == 0
    
    def save_results_to_file(self):
        """Save test results to a JSON file."""
        try:
            results_file = "checker_results.json"
            with open(results_file, 'w') as f:
                json.dump({
                    'timestamp': time.time(),
                    'total_tests': len(self.test_results),
                    'passed_tests': sum(1 for r in self.test_results if r['passed']),
                    'failed_tests': sum(1 for r in self.test_results if not r['passed']),
                    'results': self.test_results
                }, f, indent=2)
            
            print(f"\n💾 Detailed results saved to: {results_file}")
        except Exception as e:
            print(f"⚠️  Could not save results to file: {e}")


async def main():
    """Main entry point for the checker."""
    checker = ChatRoomChecker()
    
    try:
        success = await checker.run_all_tests()
        
        if success:
            print("\n🎉 All tests passed! ChatRoom module is working correctly.")
            sys.exit(0)
        else:
            print("\n💥 Some tests failed. Please check the output above.")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Fatal error during testing: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7+ is required to run this checker.")
        sys.exit(1)
    
    print("🔍 ChatRoom Module Checker")
    print("This tool validates the functionality of the ChatRoom module.")
    print()
    
    # Run the checker
    asyncio.run(main())