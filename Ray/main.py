import os
import sys
import webbrowser
import eel
import logging
import traceback
import threading
import time
from dotenv import load_dotenv

# Ensure project root is on sys.path so engine.* imports work
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Load .env from project root (safe if missing)
load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env'))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Import engine modules safely so we can report errors without crashing the UI
import_error_text = ""
IMPORTS_OK = False

# Global flag to indicate when manual listening is active (prevents wake word conflicts)
manual_listening_active = False

try:
    # Attempt to import the core engine modules
    from engine import features as engine_features
    from engine.command import respond, allCommands   # noqa: F401,F403
    IMPORTS_OK = True
    logger.info("Engine modules imported successfully.")
except Exception:
    IMPORTS_OK = False
    import_error_text = traceback.format_exc()
    logger.exception("Failed to import engine modules.")

# Expose helper so frontend can request import error text (if any)
@eel.expose()
def get_import_error():
    return import_error_text

# Functions to control wake word listener state
@eel.expose()
def set_manual_listening(active: bool):
    """Set manual listening state to prevent wake word conflicts."""
    global manual_listening_active
    manual_listening_active = active
    logger.info(f"Manual listening set to: {active}")



def start():
    eel.init("www")
    logger.info("eel initialized with folder 'www'")

    # Start wake word listener in background thread
    if IMPORTS_OK:
        try:
            wake_thread = threading.Thread(target=wake_word_listener, daemon=True) # type: ignore
            wake_thread.start()
            logger.info("Wake word listener started in background thread")
        except Exception as e:
            logger.exception("Failed to start wake word listener")

    # Try to play startup sound if available (non-fatal, safe check)
    try:
        if IMPORTS_OK:
            play_fn = getattr(engine_features, "playAssistantSound", None)
            if callable(play_fn):
                try:
                    play_fn()
                except Exception:
                    logger.debug("playAssistantSound call failed", exc_info=True)
            else:
                logger.debug("playAssistantSound not available in engine.features")
    except Exception:
        logger.debug("playAssistantSound unavailable", exc_info=True)

    # Open UI in default browser (best-effort)
    try:
        webbrowser.open("http://localhost:8001/index.html", new=1, autoraise=True)
    except Exception:
        logger.debug("Failed to open browser automatically", exc_info=True)

    # Start eel server; keep process alive even if engine imports failed
    try:
        eel.start('index.html', mode=None, host='localhost', port=8001, block=True)
    except Exception:
        logger.exception("Failed to start eel server")
        # Keep the process alive for debugging
        input("Press Enter to exit...")

if __name__ == "__main__":
    start()
