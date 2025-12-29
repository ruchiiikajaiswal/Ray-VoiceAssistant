import os
import re
import sqlite3
import time
import webbrowser
import logging
import platform
from typing import Optional, List, Dict
import requests
from urllib.parse import quote_plus

# Import psutil for battery status
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available for battery status")

try:
    import eel
    EEL_AVAILABLE = True
except ImportError:
    eel = None
    EEL_AVAILABLE = False
    logging.warning("eel not available")

# Optional audio / hotword libs — import safely
try:
    import pygame
except Exception:
    pygame = None

try:
    import winsound
except Exception:
    winsound = None

# optional hotword / mic libraries — not required for core functionality
try:
    import pvporcupine
    import pyaudio
    import struct
except Exception:
    pvporcupine = None
    pyaudio = None
    struct = None

# helper functions and config
from engine.command import speak, resolve_app  # reuse existing command helpers
try:
    from engine.config import ASSISTANT_NAME
except Exception:
    ASSISTANT_NAME = "assistant"

# optional helper to extract youtube term
try:
    from engine.helper import extract_yt_term
except Exception:
    def extract_yt_term(query: str) -> str:
        return re.sub(r"play|on youtube", "", query, flags=re.I).strip()

# YouTube API client
try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    YOUTUBE_API_AVAILABLE = True
except ImportError:
    YOUTUBE_API_AVAILABLE = False
    logging.warning("google-api-python-client not available for YouTube API")

try:
    from engine.config import YOUTUBE_API_KEY
except ImportError:
    YOUTUBE_API_KEY = None
    logging.warning("YouTube API key not configured")

try:
    from engine.openai_client import chat_completion, get_reply_text
    OPENAI_AVAILABLE = True
except Exception as e:
    print(f"Warning: OpenAI client not available: {e}")
    OPENAI_AVAILABLE = False

# duckduckgo search (optional)
try:
    from duckduckgo_search import ddg_answers, ddg
    DDG_AVAILABLE = True
except Exception:
    DDG_AVAILABLE = False

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def playAssistantSound() -> None:
    """Play a short beep to indicate assistant is ready. Safe no-op if libs not present."""
    try:
        # prefer pygame mp3 if available in www assets
        sound_path = os.path.join("www", "assets", "audio", "start_sound.mp3")
        if pygame and os.path.exists(sound_path):
            try:
                pygame.mixer.init()
                pygame.mixer.music.load(sound_path)
                pygame.mixer.music.play()
                return
            except Exception:
                pass
        # fallback to winsound on Windows
        if winsound and platform.system() == "Windows":
            winsound.MessageBeep(winsound.MB_ICONASTERISK)
    except Exception:
        logger.debug("playAssistantSound failed", exc_info=True)

def openCommand(query: str) -> str:
    """Open an application or URL; returns message spoken."""
    try:
        q = query.lower().replace(ASSISTANT_NAME.lower(), "").replace("open", "").strip()
        if not q:
            speak("What should I open?")
            return "What should I open?"
        # Try DB definitions if available
        try:
            con = sqlite3.connect("ray.db")
            cursor = con.cursor()
            cursor.execute('SELECT path FROM sys_command WHERE LOWER(name)=?', (q,))
            row = cursor.fetchone()
            if row and row[0]:
                path = row[0]
                speak(f"Opening {q}")
                try:
                    os.startfile(path) if platform.system() == "Windows" else __import__("subprocess").Popen([path])
                    return f"Opening {q}"
                except Exception:
                    # fallback to web search
                    webbrowser.open(path)
                    return f"Opened {q}"
            cursor.execute('SELECT url FROM web_command WHERE LOWER(name)=?', (q,))
            row = cursor.fetchone()
            if row and row[0]:
                webbrowser.open(row[0])
                speak(f"Opening {q}")
                return f"Opening {q}"
        except Exception:
            # ignore DB problems and continue resolution
            pass

        # Try to resolve installed app
        app_path = resolve_app(q)
        if app_path:
            try:
                if platform.system() == "Windows":
                    os.startfile(app_path)
                else:
                    __import__("subprocess").Popen([app_path])
                speak(f"Opening {q}")
                return f"Opening {q}"
            except Exception:
                logger.debug("launch failed", exc_info=True)

        # treat as URL if it looks like one
        if q.startswith("http") or "." in q or "www" in q:
            url = q if q.startswith("http") else f"https://{q}"
            webbrowser.open(url)
            speak(f"Opening {q}")
            return f"Opening {q}"

        # final fallback: web search
        url = f"https://www.google.com/search?q={q.replace(' ', '+')}"
        webbrowser.open(url)
        speak(f"I couldn't find {q} locally. I searched the web instead.")
        return f"Searched web for {q}"
    except Exception as e:
        logger.exception("openCommand failed")
        speak("I couldn't open that.")
        return "I couldn't open that."

def PlayYoutube(query: str) -> str:
    """Search YouTube for the requested term and play the first video result."""
    try:
        term = extract_yt_term(query)
        if not term:
            speak("Please tell me what to play on YouTube.")
            return "Please tell me what to play on YouTube."

        # Try to use YouTube API for direct video playback
        if YOUTUBE_API_AVAILABLE and YOUTUBE_API_KEY:
            try:
                youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
                request = youtube.search().list(
                    part='snippet',
                    q=term,
                    type='video',
                    maxResults=1,
                    order='relevance'
                )
                response = request.execute()

                if response['items']:
                    video_id = response['items'][0]['id']['videoId']
                    video_title = response['items'][0]['snippet']['title']
                    url = f"https://www.youtube.com/watch?v={video_id}"

                    # Use eel to open in the app's browser if available
                    if EEL_AVAILABLE:
                        try:
                            eel.openWebsite(url)  # type: ignore
                        except Exception:
                            # Fallback to system browser if eel method not available
                            webbrowser.open(url)
                    else:
                        webbrowser.open(url)

                    speak(f"Playing {video_title} on YouTube")
                    return f"Playing {video_title} on YouTube"
                else:
                    # No results found, fall back to search
                    url = f"https://www.youtube.com/results?search_query={term.replace(' ', '+')}"
                    if EEL_AVAILABLE:
                        try:
                            eel.openWebsite(url)  # type: ignore
                        except Exception:
                            webbrowser.open(url)
                    else:
                        webbrowser.open(url)
                    speak(f"Searching for {term} on YouTube")
                    return f"Searching for {term} on YouTube"
            except HttpError as e:
                logger.warning(f"YouTube API error: {e}")
                # Fall back to search on API error
            except Exception as e:
                logger.warning(f"YouTube API failed, falling back to search: {e}")
                # Fall back to search

        # Fallback: Open YouTube search results
        url = f"https://www.youtube.com/results?search_query={term.replace(' ', '+')}"

        # Use eel to open in the app's browser if available
        if EEL_AVAILABLE:
            try:
                eel.openWebsite(url)  # type: ignore
            except Exception:
                # Fallback to system browser if eel method not available
                webbrowser.open(url)
        else:
            webbrowser.open(url)

        speak(f"Searching for {term} on YouTube")
        return f"Searching for {term} on YouTube"
    except Exception:
        logger.exception("PlayYoutube failed")
        speak("I couldn't play that on YouTube.")
        return "I couldn't play that on YouTube."

def ask_chatgpt(query: str) -> Optional[str]:
    """
    Ask ChatGPT a question. Returns answer string or None on failure.
    """
    if not OPENAI_AVAILABLE:
        return None
    
    try:
        messages = [
            {"role": "system", "content": f"You are {ASSISTANT_NAME}, a helpful voice assistant. Provide concise, friendly answers (1-3 sentences max). Keep responses brief and suitable for voice output."},
            {"role": "user", "content": query}
        ]
        
        resp = chat_completion(messages, model="gpt-4o-mini", temperature=0.7, max_tokens=500)
        text = get_reply_text(resp)
        
        if text:
            return text.strip()
    except Exception as e:
        logger.warning(f"ChatGPT failed: {e}")
    
    return None

@eel.expose()
def ask_web(query: str) -> str:
    """
    Main question-answering function.
    Uses ChatGPT only - no web search fallback.
    """
    if not query or not query.strip():
        speak("I didn't hear anything.")
        return "I didn't hear anything."

    try:
        print(f"[v0] Asking ChatGPT: {query}")
        answer = ask_chatgpt(query)
        
        if answer:
            print(f"[v0] ChatGPT answered: {answer}")
            speak(answer)
            return answer
        
        return "I couldn't find an answer to that question."
        
    except Exception as e:
        logger.exception(f"ask_web failed: {e}")
        speak("Sorry, I couldn't find an answer.")
        return "Sorry, I couldn't find an answer."

@eel.expose()
def open_url(url: str) -> None:
    try:
        webbrowser.open(url)
    except Exception:
        logger.exception("open_url failed")

def get_battery_status() -> None:
    """Get and speak the current battery status."""
    if not PSUTIL_AVAILABLE:
        speak("Battery status feature is not available.")
        return

    try:
        battery = psutil.sensors_battery()
        if battery is None:
            speak("Battery information is not available on this system.")
            return

        percent = battery.percent
        plugged = battery.power_plugged
        status = "plugged in" if plugged else "on battery"
        time_left = ""
        if not plugged and battery.secsleft != psutil.POWER_TIME_UNLIMITED:
            hours, remainder = divmod(battery.secsleft, 3600)
            minutes, _ = divmod(remainder, 60)
            time_left = f" with {hours} hours and {minutes} minutes remaining"

        message = f"Battery is at {percent} percent and {status}{time_left}."
        speak(message)
    except Exception as e:
        logger.exception("get_battery_status failed")
        speak("I couldn't get the battery status.")

def get_weather(city: str = "") -> None:
    """Get and speak the current weather using OpenWeatherMap API."""
    api_key = "b8aea450ddbacf4d8ba209e0a9d22b67"

    try:
        if not city or city.lower() == "here" or city.lower() == "my location":
            # Get weather for current location using IP geolocation
            try:
                # Get location from IP
                ip_response = requests.get("http://ip-api.com/json/")
                ip_data = ip_response.json()

                if ip_data["status"] == "success":
                    lat = ip_data["lat"]
                    lon = ip_data["lon"]
                    city_name = ip_data["city"]
                    url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units=metric"
                    location_desc = f"your location ({city_name})"
                else:
                    # Fallback to default city if IP geolocation fails
                    url = f"http://api.openweathermap.org/data/2.5/weather?q=New%20York&appid={api_key}&units=metric"
                    location_desc = "New York"
            except Exception:
                # Fallback if IP geolocation fails
                url = f"http://api.openweathermap.org/data/2.5/weather?q=New%20York&appid={api_key}&units=metric"
                location_desc = "New York"
        else:
            # Get weather for specified city
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
            location_desc = city

        response = requests.get(url)
        data = response.json()

        if data["cod"] != "404":
            main = data["main"]
            weather = data["weather"][0]
            temperature = main["temp"]
            humidity = main["humidity"]
            description = weather["description"]
            wind_speed = data["wind"]["speed"]

            message = f"The weather in {location_desc} is {description} with a temperature of {temperature} degrees Celsius, humidity of {humidity} percent, and wind speed of {wind_speed} meters per second."
            speak(message)
        else:
            speak(f"I couldn't find weather information for {location_desc}.")
    except Exception as e:
        logger.exception("get_weather failed")
        speak("I couldn't get the weather information.")

def send_email(to_email: str, subject: str, body: str) -> None:
    """Send an email using Gmail SMTP. Requires user credentials."""
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart

    # Note: This requires the user to provide their email and app password
    # For security, these should be stored securely, not hardcoded
    sender_email = "your_email@gmail.com"  # Replace with user's email
    sender_password = "your_app_password"  # Replace with Gmail app password

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, to_email, text)
        server.quit()

        speak(f"Email sent to {to_email} with subject '{subject}'.")
    except Exception as e:
        logger.exception("send_email failed")
        speak("I couldn't send the email. Please check your email settings.")

def send_whatsapp_message(recipient: str, message: str) -> None:
    """Send a WhatsApp message using Twilio API. Requires Twilio credentials."""
    try:
        # Note: This requires the user to provide their Twilio credentials
        # For security, these should be stored securely, not hardcoded
        account_sid = "your_twilio_account_sid"  # Replace with user's Twilio SID
        auth_token = "your_twilio_auth_token"  # Replace with user's Twilio token
        from_number = "your_twilio_phone_number"  # Replace with user's Twilio phone number

        from twilio.rest import Client

        client = Client(account_sid, auth_token)

        # Ensure recipient has + prefix
        if not recipient.startswith('+'):
            recipient = '+' + recipient

        message = client.messages.create(
            body=message,
            from_=from_number,
            to=recipient
        )

        speak(f"WhatsApp message sent to {recipient}.")
    except Exception as e:
        logger.exception("send_whatsapp_message failed")
        speak("I couldn't send the WhatsApp message. Please check your Twilio settings.")

def send_whatsapp_message(recipient: str, message: str) -> None:
    """Send a WhatsApp message using Twilio API. Requires Twilio credentials."""
    # Note: This requires the user to provide their Twilio credentials
    # For security, these should be stored securely, not hardcoded
    account_sid = "your_twilio_account_sid"  # Replace with user's Twilio Account SID
    auth_token = "your_twilio_auth_token"    # Replace with user's Twilio Auth Token
    from_number = "your_twilio_phone_number"  # Replace with user's Twilio phone number

    try:
        from twilio.rest import Client
        client = Client(account_sid, auth_token)

        # Ensure recipient has country code
        if not recipient.startswith('+'):
            recipient = '+' + recipient

        message = client.messages.create(
            body=message,
            from_=from_number,
            to=recipient
        )

        speak(f"WhatsApp message sent to {recipient}.")
    except ImportError:
        logger.warning("Twilio not installed. Install with: pip install twilio")
        speak("WhatsApp messaging requires Twilio. Please install twilio package.")
    except Exception as e:
        logger.exception("send_whatsapp_message failed")
        speak("I couldn't send the WhatsApp message. Please check your Twilio settings.")
