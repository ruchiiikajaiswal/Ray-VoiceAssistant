import os
import sys
import subprocess
import webbrowser
import platform
import time
import logging
import random
from datetime import datetime
from urllib.parse import quote_plus
import shutil
import glob
from typing import Optional, List, Dict, Any

# Import optional dependencies with error handling
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logging.warning("pyttsx3 not available")

try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False
    logging.warning("speech_recognition not available")

try:
    import eel
    EEL_AVAILABLE = True
except ImportError:
    EEL_AVAILABLE = False
    logging.warning("eel not available")

# Import ASSISTANT_NAME
try:
    from engine.config import ASSISTANT_NAME
except ImportError:
    ASSISTANT_NAME = "Ray"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def safe_eel_display(msg: str) -> None:
    if EEL_AVAILABLE:
        try:
            eel.DisplayMessage(msg)  # type: ignore
        except Exception:
            logger.debug("eel.DisplayMessage not available")
    else:
        logger.debug("eel not available")

def safe_eel_showhood() -> None:
    if EEL_AVAILABLE:
        try:
            eel.ShowHood()
        except Exception:
            logger.debug("eel.ShowHood not available")
    else:
        logger.debug("eel not available")

_engine = None
def _get_engine() -> Optional[Any]:
    global _engine
    if _engine is None and PYTTSX3_AVAILABLE:
        try:
            _engine = pyttsx3.init('sapi5')
            voices = _engine.getProperty('voices')
            if len(voices) > 1:
                _engine.setProperty('voice', voices[1].id)
            elif voices:
                _engine.setProperty('voice', voices[0].id)
            _engine.setProperty('rate', 174)
        except Exception as e:
            logger.warning(f"pyttsx3 init failed: {e}")
            _engine = None
    return _engine

def speak(text: str) -> None:
    """Speak and show message in UI if available."""
    safe_eel_display(text)
    if EEL_AVAILABLE:
        try:
            eel.addChatMessage('Ray', text)  # type: ignore
        except Exception:
            pass

    engine = _get_engine()
    if engine:
        try:
            engine.say(text)
            engine.runAndWait()
        except Exception as e:
            logger.warning(f"Speech engine error: {e}")
            print(text)
    else:
        print(text)

def takecommand() -> str:
    """
    Listen from microphone if available, otherwise fall back to typed input.
    Returns lowercased recognized string or empty string on failure.
    """
    if not SPEECH_RECOGNITION_AVAILABLE:
        logger.warning("Speech recognition not available, falling back to text input")
        try:
            text = input("Type command (speech recognition unavailable): ").strip()
            return text.lower()
        except Exception:
            return ""

    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print('listening....')
            if EEL_AVAILABLE:
                try:
                    eel.DisplayMessage('listening....')  # type: ignore
                except Exception:
                    pass

            r.pause_threshold = 1
            try:
                r.adjust_for_ambient_noise(source, duration=1)  # type: ignore
            except Exception:
                pass

            try:
                audio = r.listen(source, timeout=10, phrase_time_limit=6)
            except sr.WaitTimeoutError:
                print("Listening timed out waiting for phrase")
                return ""
        print('recognizing...')
        safe_eel_display('recognizing...')
        try:
            query = r.recognize_google(audio, language='en-in')
        except sr.UnknownValueError:
            print("Could not understand audio")
            return ""
        except sr.RequestError as e:
            print(f"Google API error: {e}")
            return ""
        print(f"user said: {query}")
        if EEL_AVAILABLE:
            try:
                eel.DisplayMessage(query)  # type: ignore
            except Exception:
                pass
        time.sleep(1)
        return str(query).lower()
    except (OSError, sr.RequestError, Exception) as e:
        logger.warning(f"Microphone/listen error: {e}")
        try:
            text = input("Type command (microphone unavailable): ").strip()
            return text.lower()
        except Exception:
            return ""

# Mapping of friendly names to executable candidates
APPS_MAP = {
    "chrome": ["chrome.exe", "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"],
    "google chrome": ["chrome.exe", "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"],
    "edge": ["msedge.exe", "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe", "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe"],
    "firefox": ["firefox.exe", "C:\\Program Files\\Mozilla Firefox\\firefox.exe", "C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe"],
    "vscode": ["code", "Code.exe", "C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"],
    "visual studio code": ["code", "Code.exe", "C:\\Users\\%USERNAME%\\AppData\\Local\\Programs\\Microsoft VS Code\\Code.exe"],
    "notepad": ["notepad.exe", "C:\\Windows\\System32\\notepad.exe"],
    "calculator": ["calc.exe", "C:\\Windows\\System32\\calc.exe"],
    "paint": ["mspaint.exe", "C:\\Windows\\System32\\mspaint.exe"],
    "spotify": ["spotify.exe", "C:\\Users\\%USERNAME%\\AppData\\Roaming\\Spotify\\Spotify.exe"],
    "slack": ["slack.exe"],
    "discord": ["Discord.exe"],
    "teams": ["Teams.exe", "C:\\Program Files\\Microsoft\\Teams\\current\\Teams.exe"],
    "word": ["WINWORD.EXE", "C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE"],
    "excel": ["EXCEL.EXE", "C:\\Program Files\\Microsoft Office\\root\\Office16\\EXCEL.EXE"],
    "powershell": ["powershell.exe", "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe"],
    "whatsapp": ["WhatsApp.exe", "C:\\Users\\%USERNAME%\\AppData\\Local\\WhatsApp\\WhatsApp.exe", "C:\\Program Files\\WindowsApps\\5319275A.WhatsAppDesktop_cv1g1gvanyjgm\\WhatsApp.exe"],
}

# Mapping of website names to URLs
WEBSITES_MAP = {
    "google": "https://www.google.com",
    "youtube": "https://www.youtube.com",
    "facebook": "https://www.facebook.com",
    "twitter": "https://www.twitter.com",
    "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com",
    "github": "https://www.github.com",
    "stackoverflow": "https://stackoverflow.com",
    "reddit": "https://www.reddit.com",
    "amazon": "https://www.amazon.com",
    "netflix": "https://www.netflix.com",
    "wikipedia": "https://www.wikipedia.org",
    "gmail": "https://mail.google.com",
    "outlook": "https://outlook.live.com",
    "yahoo": "https://www.yahoo.com",
    "bing": "https://www.bing.com",
    "duckduckgo": "https://duckduckgo.com",
    "whatsapp": "https://web.whatsapp.com",
}

COMMON_SEARCH_DIRS = [
    os.environ.get("PROGRAMFILES", ""),
    os.environ.get("PROGRAMFILES(X86)", ""),
    os.environ.get("LOCALAPPDATA", ""),
    "C:\\Program Files",
    "C:\\Program Files (x86)",
    "C:\\Windows\\System32",
    os.path.join(os.environ.get("USERPROFILE", ""), "AppData", "Local", "Programs"),
]

def find_executable_candidate(candidate: str) -> str | None:
    """Try to resolve candidate to an executable path."""
    if os.path.isabs(candidate) and os.path.exists(candidate):
        return candidate

    which = shutil.which(candidate)
    if which:
        return which

    for base in COMMON_SEARCH_DIRS:
        if not base:
            continue
        p = os.path.join(base, candidate)
        if os.path.exists(p):
            return p
        pattern = os.path.join(base, "**", os.path.basename(candidate))
        matches = glob.glob(pattern, recursive=True)
        if matches:
            for m in matches:
                if m.lower().endswith((".exe", ".bat", ".cmd")):
                    return m
            return matches[0]
    return None

def resolve_app(target: str) -> str | None:
    """Given a friendly target string, try to find an executable path."""
    key = target.strip().lower()
    if key in APPS_MAP:
        for cand in APPS_MAP[key]:
            found = find_executable_candidate(cand)
            if found:
                return found

    for name, candidates in APPS_MAP.items():
        if name in key:
            for cand in candidates:
                found = find_executable_candidate(cand)
                if found:
                    return found

    words = key.split()
    for w in words:
        if w in APPS_MAP:
            for cand in APPS_MAP[w]:
                found = find_executable_candidate(cand)
                if found:
                    return found

    last = words[-1]
    if shutil.which(last):
        return shutil.which(last)

    return None

def handle_builtin_commands(query: str) -> bool:
    """Handle simple built-in commands including casual greetings. Returns True if handled."""
    if not query:
        return False

    greetings = {
        "hello": ["Hello! How can I help you?", "Hi there! What can I do for you?", "Hey! What's up?"],
        "hi": ["Hi! How are you doing?", "Hello! What's on your mind?", "Hey there!"],
        "hey": ["Hey! What do you need?", "What's up?", "Hi! How can I assist?"],
        "good morning": ["Good morning! Ready to help!", "Morning! Let's get started.", "Good morning! What's your plan?"],
        "good afternoon": ["Good afternoon! How can I help?", "Afternoon! What do you need?", "Good afternoon!"],
        "good evening": ["Good evening! What can I do?", "Evening! How are things?", "Good evening!"],
        "good night": ["Good night! Sleep well!", "Night! See you later!", "Good night! Rest well!"],
    }

    casual = {
        "how are you": ["I'm doing great, thanks for asking!", "I'm functioning perfectly!", "All systems go!"],
        "what's up": ["Not much! Just ready to help. What do you need?", "Everything's good!", "Hey! What can I do for you?"],
        "who are you": [f"I'm {ASSISTANT_NAME}, your voice assistant!", "I'm your AI assistant!", "Your friendly AI!"],
    }

    thanks = {
        "thank you": ["You're welcome! Happy to help.", "Anytime! Glad I could assist.", "My pleasure!"],
        "thanks": ["No problem! Anything else?", "Happy to help!", "You're welcome!"],
    }

    query_lower = query.lower().strip()

    # Handle stopping/pausing
    if any(phrase in query_lower for phrase in ("stop listening", "pause listening", "don't listen")):
        speak("Okay — I will stop listening.")
        return True
    
    if any(phrase in query_lower for phrase in ("resume listening", "start listening", "listen")):
        speak("I'm listening again.")
        return True

    # Handle closing app
    if any(phrase in query_lower for phrase in ("close application", "close app", "exit application", "quit")):
        speak("Closing the application. Goodbye.")
        try:
            sys.exit(0)
        except Exception:
            pass
        return True

    # Handle opening app or website
    if query_lower.startswith("open "):
        target = query_lower.replace("open ", "", 1).strip()
        logger.info(f"Open command detected. Target: '{target}'")
        if target:
            # Special handling for YouTube
            if target.lower() == "youtube":
                try:
                    from engine.features import openCommand
                    result = openCommand(f"open {target}")
                    return True
                except Exception as e:
                    logger.warning(f"Failed to open YouTube: {e}")
                    speak("I couldn't open YouTube")
                    return True

            # Check if it's a website first
            website_url = WEBSITES_MAP.get(target.lower())
            logger.info(f"Website URL for '{target.lower()}': {website_url}")
            if website_url:
                try:
                    logger.info(f"Opening website: {website_url}")
                    # Use eel to open in the same browser window/tab
                    if EEL_AVAILABLE:
                        try:
                            eel.openWebsite(website_url)  # type: ignore
                        except Exception:
                            # Fallback to webbrowser if eel method not available
                            webbrowser.open(website_url)
                    else:
                        webbrowser.open(website_url)
                    speak(f"Opening {target}")
                    return True
                except Exception as e:
                    logger.warning(f"Failed to open website {target}: {e}")
                    speak(f"I couldn't open {target}")
                    return True

            # Otherwise, try to open as an app
            app_path = resolve_app(target)
            if app_path:
                try:
                    if platform.system() == "Windows":
                        os.startfile(app_path)
                    else:
                        subprocess.Popen([app_path])
                    speak(f"Opening {target}")
                    return True
                except Exception as e:
                    logger.warning(f"Failed to open {target}: {e}")
                    speak(f"I couldn't open {target}")
                    return True
            else:
                speak(f"I couldn't find {target} on your system or as a website")
                return True
        return False

    # Handle playing videos on YouTube
    if query_lower.startswith("play ") and "youtube" in query_lower:
        try:
            from engine.features import PlayYoutube
            result = PlayYoutube(query_lower)
            return True
        except Exception as e:
            logger.warning(f"Failed to play on YouTube: {e}")
            speak("I couldn't play that on YouTube")
            return True

    # Handle playing videos (defaults to YouTube if no platform specified)
    if query_lower.startswith("play ") and "spotify" not in query_lower:
        try:
            from engine.features import PlayYoutube
            result = PlayYoutube(query_lower)
            return True
        except Exception as e:
            logger.warning(f"Failed to play on YouTube: {e}")
            speak("I couldn't play that on YouTube")
            return True

    # Handle messaging on WhatsApp
    if query_lower.startswith("message ") or query_lower.startswith("msg ") or query_lower.startswith("whatsapp "):
        # Parse: "message john hello how are you" or "whatsapp to +1234567890 hello"
        parts = query_lower.split()
        if len(parts) >= 3:
            # Check if it's "whatsapp to +number message" format
            if "to" in parts and len(parts) >= 4:
                try:
                    to_index = parts.index("to")
                    recipient = parts[to_index + 1]
                    message = " ".join(parts[to_index + 2:])
                    from engine.features import send_whatsapp_message
                    send_whatsapp_message(recipient, message)
                    return True
                except Exception as e:
                    logger.warning(f"WhatsApp message parsing failed: {e}")
                    speak("Please specify WhatsApp message in format: whatsapp to +1234567890 your message")
                    return True
            else:
                # Original behavior: open WhatsApp for contact
                name = query_lower.replace("message ", "", 1).replace("msg ", "", 1).replace("whatsapp ", "", 1).strip()
                if name:
                    # Try to open WhatsApp desktop app first
                    app_path = resolve_app("whatsapp")
                    if app_path:
                        try:
                            if platform.system() == "Windows":
                                os.startfile(app_path)
                            else:
                                subprocess.Popen([app_path])
                            speak(f"Opening WhatsApp. Please search for {name} in your contacts to start messaging.")
                            return True
                        except Exception as e:
                            logger.warning(f"Failed to open WhatsApp desktop app: {e}")
                            # Fall back to web version
                            try:
                                webbrowser.open("https://web.whatsapp.com")
                                speak(f"Opening WhatsApp Web. Please search for {name} in your contacts to start messaging.")
                                return True
                            except Exception as e2:
                                logger.warning(f"Failed to open WhatsApp Web: {e2}")
                                speak("I couldn't open WhatsApp")
                                return True
                    else:
                        # No desktop app found, use web version
                        try:
                            webbrowser.open("https://web.whatsapp.com")
                            speak(f"Opening WhatsApp Web. Please search for {name} in your contacts to start messaging.")
                            return True
                        except Exception as e:
                            logger.warning(f"Failed to open WhatsApp Web: {e}")
                            speak("I couldn't open WhatsApp")
                            return True
        else:
            # Just open WhatsApp if no name specified - try desktop first
            app_path = resolve_app("whatsapp")
            if app_path:
                try:
                    if platform.system() == "Windows":
                        os.startfile(app_path)
                    else:
                        subprocess.Popen([app_path])
                    speak("Opening WhatsApp")
                    return True
                except Exception as e:
                    logger.warning(f"Failed to open WhatsApp desktop app: {e}")
                    # Fall back to web version
                    try:
                        webbrowser.open("https://web.whatsapp.com")
                        speak("Opening WhatsApp Web")
                        return True
                    except Exception as e2:
                        logger.warning(f"Failed to open WhatsApp Web: {e2}")
                        speak("I couldn't open WhatsApp")
                        return True
            else:
                # No desktop app found, use web version
                try:
                    webbrowser.open("https://web.whatsapp.com")
                    speak("Opening WhatsApp Web")
                    return True
                except Exception as e:
                    logger.warning(f"Failed to open WhatsApp Web: {e}")
                    speak("I couldn't open WhatsApp")
                    return True
        return False

    # Handle opening WhatsApp directly
    if query_lower in ["open whatsapp", "whatsapp", "start whatsapp"]:
        # Try desktop app first
        app_path = resolve_app("whatsapp")
        if app_path:
            try:
                if platform.system() == "Windows":
                    os.startfile(app_path)
                else:
                    subprocess.Popen([app_path])
                speak("Opening WhatsApp")
                return True
            except Exception as e:
                logger.warning(f"Failed to open WhatsApp desktop app: {e}")
                # Fall back to web version
                try:
                    webbrowser.open("https://web.whatsapp.com")
                    speak("Opening WhatsApp Web")
                    return True
                except Exception as e2:
                    logger.warning(f"Failed to open WhatsApp Web: {e2}")
                    speak("I couldn't open WhatsApp")
                    return True
        else:
            # No desktop app found, use web version
            try:
                webbrowser.open("https://web.whatsapp.com")
                speak("Opening WhatsApp Web")
                return True
            except Exception as e:
                logger.warning(f"Failed to open WhatsApp Web: {e}")
                speak("I couldn't open WhatsApp")
                return True

    for key, responses in greetings.items():
        if query_lower == key or query_lower.startswith(key):
            speak(random.choice(responses))
            return True

    for key, responses in casual.items():
        if key in query_lower:
            speak(random.choice(responses))
            return True

    for key, responses in thanks.items():
        if key in query_lower:
            speak(random.choice(responses))
            return True

    # Time and Date
    if "time" in query_lower and ("what" in query_lower or "tell" in query_lower or query_lower == "time"):
        now = datetime.now().strftime("%I:%M %p")
        speak(f"The time is {now}")
        return True

    if "date" in query_lower and ("what" in query_lower or "tell" in query_lower or query_lower == "date"):
        today = datetime.now().strftime("%A, %B %d, %Y")
        speak(f"Today is {today}")
        return True

    # Say/repeat command
    if query_lower.startswith("say ") or query_lower.startswith("repeat "):
        _, _, to_say = query_lower.partition(" ")
        if to_say:
            speak(to_say)
            return True

    # Battery status
    if "battery" in query_lower and ("status" in query_lower or "level" in query_lower):
        try:
            from engine.features import get_battery_status
            get_battery_status()
            return True
        except Exception as e:
            logger.warning(f"Battery status failed: {e}")
            speak("Battery status feature is not available.")
            return True

    # Weather - more flexible detection
    if "weather" in query_lower:
        # Parse city/state from query: "weather in New York", "weather New York", "weather for Mumbai, Maharashtra", "what's the weather in Delhi"
        city_query = query_lower.replace("weather", "").replace("what's", "").replace("what is", "").replace("the", "").replace("in", "").replace("for", "").replace("of", "").strip()

        # Handle cases like "weather in Los Angeles, California"
        if "," in city_query:
            parts = city_query.split(",")
            city = parts[0].strip()
            state = parts[1].strip() if len(parts) > 1 else ""
            if state:
                city_query = f"{city}, {state}"
            else:
                city_query = city
        else:
            city_query = city_query.strip()

        if not city_query:
            city_query = ""  # Empty string will trigger location-based weather

        try:
            from engine.features import get_weather
            get_weather(city_query)
            return True
        except Exception as e:
            logger.warning(f"Weather failed: {e}")
            speak("Weather feature is not available.")
            return True

    # Send email
    if query_lower.startswith("send email") or query_lower.startswith("email"):
        # Parse: "send email to john@example.com subject hello body how are you"
        parts = query_lower.split()
        if len(parts) >= 5 and "to" in parts and "subject" in parts and "body" in parts:
            try:
                to_index = parts.index("to")
                subject_index = parts.index("subject")
                body_index = parts.index("body")
                to_email = parts[to_index + 1]
                subject = " ".join(parts[subject_index + 1:body_index])
                body = " ".join(parts[body_index + 1:])
                from engine.features import send_email
                send_email(to_email, subject, body)
                return True
            except Exception as e:
                logger.warning(f"Send email parsing failed: {e}")
                speak("Please specify email in format: send email to recipient subject your subject body your message")
                return True
        else:
            speak("Please specify email in format: send email to recipient subject your subject body your message")
            return True

    return False

def ask_chatgpt(query: str) -> Optional[str]:
    """Use ChatGPT to answer questions."""
    try:
        from engine.openai_client import chat_completion, get_reply_text

        messages = [
            {"role": "system", "content": f"You are {ASSISTANT_NAME}, a helpful voice assistant. Provide concise, friendly answers (1-3 sentences max)."},
            {"role": "user", "content": query}
        ]

        resp = chat_completion(messages, model="gpt-4o-mini", temperature=0.7, max_tokens=500)
        reply_text = get_reply_text(resp)

        if reply_text:
            return reply_text
        return None
    except Exception as e:
        logger.warning(f"ChatGPT failed: {e}")
        return None

def ask_chatgpt_stream(query: str) -> Optional[str]:
    """Use ChatGPT to answer questions with streaming response."""
    try:
        from engine.openai_client import chat_completion_stream

        messages = [
            {"role": "system", "content": f"You are {ASSISTANT_NAME}, a helpful voice assistant. Provide concise, friendly answers (1-3 sentences max)."},
            {"role": "user", "content": query}
        ]

        full_response = ""

        for chunk in chat_completion_stream(messages, model="gpt-4o-mini", temperature=0.7, max_tokens=500):
            full_response += chunk
            # Display each chunk as it arrives
            if EEL_AVAILABLE:
                try:
                    eel.StreamChunk(chunk)  # type: ignore
                except Exception:
                    logger.debug("eel.StreamChunk not available")

        if full_response:
            return full_response
        return None
    except Exception as e:
        logger.warning(f"ChatGPT streaming failed: {e}")
        return None

@eel.expose()
def allCommands() -> None:
    """Exposed: called by frontend when microphone button is clicked."""
    try:
        # Set manual listening flag to prevent wake word conflicts
        if EEL_AVAILABLE:
            try:
                eel.set_manual_listening(True)  # type: ignore
            except Exception:
                logger.debug("eel.set_manual_listening not available")

        query = takecommand()
        print(f"[v0] Query: {query}")

        if not query:
            print("[v0] No command recognized")
            reply = "I didn't hear anything. Please try again."
            speak(reply)
            return

        # try built-in commands first
        if handle_builtin_commands(query):
            print("[v0] Built-in command handled")
            return

        print("[v0] Using ChatGPT to stream voice query response...")
        reply_text = ask_chatgpt_stream(query)

        if reply_text:
            speak(reply_text)
            return

        speak("I couldn't find an answer to that question. Please try asking something else.")

    except Exception as e:
        print(f"[v0] Error in allCommands: {e}")
        logger.exception("allCommands error")
        speak("Sorry, something went wrong.")
    finally:
        # Reset manual listening flag
        if EEL_AVAILABLE:
            try:
                eel.set_manual_listening(False)  # type: ignore
            except Exception:
                logger.debug("eel.set_manual_listening not available")
        safe_eel_showhood()

@eel.expose()
def respond(raw_query: str) -> str:
    """Exposed: for direct text queries with streaming."""
    try:
        if not raw_query or not raw_query.strip():
            reply_text = "Please say something."
            speak(reply_text)
            return reply_text

        q = raw_query.strip().lower()
        print(f"[v0] respond() called with: {q}")

        if ASSISTANT_NAME and ASSISTANT_NAME.lower() in q:
            q = q.replace(ASSISTANT_NAME.lower(), "").strip()

        if handle_builtin_commands(q):
            print(f"[v0] Built-in command handled: {q}")
            return f"Handled built-in command"

        print("[v0] Using ChatGPT to stream text query response...")
        reply_text = ask_chatgpt_stream(q)

        if reply_text:
            speak(reply_text)
            return reply_text

        return "I couldn't find an answer to that question. Please try asking something else."

    except Exception as e:
        logger.exception("respond failed")
        reply_text = "Sorry, something went wrong."
        speak(reply_text)
        return reply_text

@eel.expose()
def new_chat_session() -> str:
    """Initialize a new chat session."""
    try:
        print("[v0] New chat session started")
        # Clear any session-specific data if needed
        return "New chat session started"
    except Exception as e:
        logger.exception("new_chat_session failed")
        return "Failed to start new session"

@eel.expose()
def load_chat_history(chat_id: str) -> list:
    """Load conversation history for a specific chat."""
    try:
        print(f"[v0] Loading chat history for: {chat_id}")
        # For now, return empty list - in a real app, this would load from database
        # You could implement persistent chat storage here
        return []
    except Exception as e:
        logger.exception("load_chat_history failed")
        return []

@eel.expose()
def regenerate_response(chat_id: str, query: str) -> str:
    """Regenerate a response for a given query."""
    try:
        print(f"[v0] Regenerating response for: {query}")
        reply_text = ask_chatgpt(query)  # Use non-streaming version for regeneration
        if reply_text:
            return reply_text
        return "I couldn't generate a response. Please try again."
    except Exception as e:
        logger.exception("regenerate_response failed")
        return "Failed to regenerate response"

@eel.expose()
def upload_file(file_path: str) -> str:
    """Handle file upload."""
    try:
        print(f"[v0] File uploaded: {file_path}")
        # In a real implementation, you would:
        # 1. Save the file to a secure location
        # 2. Process the file (extract text, analyze, etc.)
        # 3. Store metadata in database
        # For now, just acknowledge
        return f"File {file_path} processed successfully"
    except Exception as e:
        logger.exception("upload_file failed")
        return "Failed to upload file"

@eel.expose()
def start_listening() -> None:
    """Start voice listening."""
    try:
        print("[v0] Starting voice listening")
        # Set manual listening flag
        if EEL_AVAILABLE:
            try:
                eel.set_manual_listening(True)
            except Exception:
                pass
        # This would trigger the voice input process
    except Exception as e:
        logger.exception("start_listening failed")

@eel.expose()
def stop_listening() -> None:
    """Stop voice listening."""
    try:
        print("[v0] Stopping voice listening")
        # Reset manual listening flag
        if EEL_AVAILABLE:
            try:
                eel.set_manual_listening(False)
            except Exception:
                pass
    except Exception as e:
        logger.exception("stop_listening failed")

@eel.expose()
def process_command(query: str) -> str:
    """Process a text command and return response."""
    try:
        if not query or not query.strip():
            return "Please enter a command."

        q = query.strip().lower()
        print(f"[v0] process_command() called with: {q}")

        if ASSISTANT_NAME and ASSISTANT_NAME.lower() in q:
            q = q.replace(ASSISTANT_NAME.lower(), "").strip()

        if handle_builtin_commands(q):
            print(f"[v0] Built-in command handled: {q}")
            return "Command executed successfully."

        print("[v0] Using ChatGPT for command response...")
        reply_text = ask_chatgpt(q)

        if reply_text:
            return reply_text

        return "I couldn't process that command. Please try again."

    except Exception as e:
        logger.exception("process_command failed")
        return "Sorry, something went wrong processing your command."
