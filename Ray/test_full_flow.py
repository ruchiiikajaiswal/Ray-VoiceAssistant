#!/usr/bin/env python3
"""
Complete test of the website opening flow as it would work in the app
"""
import sys
import os
import logging
import webbrowser

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

try:
    from engine.command import respond, WEBSITES_MAP
    logger.info("Successfully imported functions")
except ImportError as e:
    logger.error(f"Failed to import: {e}")
    sys.exit(1)

def test_user_scenarios():
    """Test various user input scenarios"""
    test_cases = [
        # Direct commands
        "open google",
        "open youtube",
        "open whatsapp",

        # With assistant name
        "ray open google",
        "Ray open youtube",

        # Case variations
        "OPEN GOOGLE",
        "Open Google",

        # Messaging
        "message john",
        "msg mary",

        # Invalid commands
        "open nonexistentwebsite",
        "open",
    ]

    print("Available websites:", list(WEBSITES_MAP.keys()))
    print("\n" + "="*60)

    for test_query in test_cases:
        print(f"\nTesting: '{test_query}'")
        print("-" * 40)

        try:
            result = respond(test_query)
            print(f"Response: {result}")
        except Exception as e:
            print(f"ERROR: {e}")

        print("-" * 40)

if __name__ == "__main__":
    test_user_scenarios()
