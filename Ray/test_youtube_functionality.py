#!/usr/bin/env python3
"""
Test script for YouTube functionality - direct video playback by name
"""
import sys
import os
import logging
import webbrowser
import types

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Mock eel to prevent import errors
class MockEel:
    def expose(self, func):
        return func

    def DisplayMessage(self, msg):
        print(f"[MOCK EEL] DisplayMessage: {msg}")

    def addChatMessage(self, sender, msg):
        print(f"[MOCK EEL] addChatMessage: {sender}: {msg}")

    def StreamChunk(self, chunk):
        print(f"[MOCK EEL] StreamChunk: {chunk}")

    def openWebsite(self, url):
        print(f"[MOCK EEL] openWebsite: {url}")
        # Don't actually open browser in tests
        return True

sys.modules['eel'] = MockEel()

# Mock pyttsx3
class MockEngine:
    def say(self, text):
        print(f"[MOCK TTS] Saying: {text}")

    def runAndWait(self):
        pass

    def setProperty(self, prop, value):
        pass

    def getProperty(self, prop):
        return []

class MockPyttsx3:
    def init(self, driver):
        return MockEngine()

mock_pyttsx3 = types.ModuleType('pyttsx3')
mock_pyttsx3.init = MockPyttsx3().init
sys.modules['pyttsx3'] = mock_pyttsx3

# Mock speech_recognition
class MockSr:
    class Recognizer:
        pass

mock_sr = types.ModuleType('speech_recognition')
mock_sr.Recognizer = MockSr.Recognizer
sys.modules['speech_recognition'] = mock_sr

# Mock googleapiclient for testing without API key
class MockYouTube:
    def search(self):
        return self

    def list(self, **kwargs):
        return self

    def execute(self):
        # Mock response for "test song"
        return {
            'items': [{
                'id': {'videoId': 'dQw4w9WgXcQ'},  # Mock video ID
                'snippet': {'title': 'Test Song - Mock Artist'}
            }]
        }

class MockBuild:
    def __init__(self, *args, **kwargs):
        pass

    def search(self):
        return MockYouTube()

mock_googleapiclient = types.ModuleType('googleapiclient')
mock_googleapiclient.discovery = types.ModuleType('discovery')
mock_googleapiclient.discovery.build = MockBuild
mock_googleapiclient.errors = types.ModuleType('errors')
mock_googleapiclient.errors.HttpError = Exception

sys.modules['googleapiclient'] = mock_googleapiclient
sys.modules['googleapiclient.discovery'] = mock_googleapiclient.discovery
sys.modules['googleapiclient.errors'] = mock_googleapiclient.errors

def test_youtube_functionality():
    """Test YouTube direct video playback functionality"""
    print("="*60)
    print("TESTING YOUTUBE DIRECT VIDEO PLAYBACK FUNCTIONALITY")
    print("="*60)

    try:
        from engine.features import PlayYoutube
        logger.info("Successfully imported PlayYoutube function")
    except ImportError as e:
        logger.error(f"Failed to import PlayYoutube: {e}")
        return False

    # Test cases
    test_cases = [
        ("play test song", "Test Song"),
        ("play Bohemian Rhapsody", "Bohemian Rhapsody"),
        ("play funny cat videos", "funny cat videos"),
        ("play", ""),  # Empty term
    ]

    print("\nTesting PlayYoutube function directly:")
    print("-" * 40)

    for query, expected_term in test_cases:
        print(f"\nTest Query: '{query}'")
        print(f"Expected Term: '{expected_term}'")

        try:
            result = PlayYoutube(query)
            print(f"Function Result: {result}")

            if expected_term and expected_term in result:
                print("✓ PASS: Function returned expected result")
            elif not expected_term and "Please tell me what to play" in result:
                print("✓ PASS: Function handled empty term correctly")
            else:
                print("✗ FAIL: Unexpected result")
                return False

        except Exception as e:
            print(f"✗ FAIL: Exception occurred: {e}")
            return False

    print("\n" + "="*60)
    print("Testing integration with command system:")
    print("-" * 40)

    try:
        from engine.command import respond
        logger.info("Successfully imported respond function")
    except ImportError as e:
        logger.error(f"Failed to import respond: {e}")
        return False

    integration_tests = [
        "play test song on youtube",
        "play funny videos",
    ]

    for test_query in integration_tests:
        print(f"\nIntegration Test: '{test_query}'")

        try:
            result = respond(test_query)
            print(f"Response: {result}")

            if "Playing" in result and "on YouTube" in result:
                print("✓ PASS: Integration test successful")
            else:
                print("✗ FAIL: Integration test failed")
                return False

        except Exception as e:
            print(f"✗ FAIL: Exception in integration test: {e}")
            return False

    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED")
    print("YouTube direct video playback functionality is working correctly!")
    print("="*60)

    return True

if __name__ == "__main__":
    success = test_youtube_functionality()
    sys.exit(0 if success else 1)
