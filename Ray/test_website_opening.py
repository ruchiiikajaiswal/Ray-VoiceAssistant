#!/usr/bin/env python3
"""
Test script to verify website opening functionality
"""
import sys
import os
import webbrowser
import logging

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Import the WEBSITES_MAP from command.py
try:
    from engine.command import WEBSITES_MAP
    logger.info("Successfully imported WEBSITES_MAP")
    logger.info(f"Available websites: {list(WEBSITES_MAP.keys())}")
except ImportError as e:
    logger.error(f"Failed to import WEBSITES_MAP: {e}")
    sys.exit(1)

def test_website_opening(target):
    """Test opening a website by name"""
    logger.info(f"Testing website opening for: '{target}'")

    # Check if it's a website
    website_url = WEBSITES_MAP.get(target.lower())
    logger.info(f"Website URL for '{target.lower()}': {website_url}")

    if website_url:
        try:
            logger.info(f"Opening website: {website_url}")
            webbrowser.open(website_url)
            print(f"SUCCESS: Opened {target} -> {website_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to open website {target}: {e}")
            print(f"FAILED: Could not open {target}")
            return False
    else:
        print(f"NOT FOUND: '{target}' not in WEBSITES_MAP")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
        test_website_opening(target)
    else:
        print("Testing all websites in WEBSITES_MAP...")
        for site in WEBSITES_MAP.keys():
            print(f"\nTesting '{site}':")
            test_website_opening(site)
            # Wait a bit between tests
            import time
            time.sleep(1)
