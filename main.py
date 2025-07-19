import speech_recognition as sr
import pyttsx3
import webbrowser
import os
import getpass
from datetime import datetime, timedelta
import random
import threading
import time
import playsound
import tkinter as tk
from tkvideo import tkvideo
import requests
import openai
from deep_translator import GoogleTranslator
import psycopg2
import cv2
from reportlab.pdfgen import canvas
import pywhatkit
import smtplib
from email.message import EmailMessage
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from deepface import Deepface


# ========= CONFIG =========
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "assets")
MP3_PATH = os.path.join(ASSETS_DIR, "reminder.mp3")
ROBOT_VIDEO_PATH = os.path.join(ASSETS_DIR, "robot1.mp4")
ASSISTANT_NAME = "Anu"
USER_NAME = "Anwesha"
WAKE_WORD = "anu"
WEATHER_API_KEY = "0ae9f868e7d775bf6bac7968579366f1"
NEWS_API_KEY = "4c63e9561a384e7abe3e4fe62b6db452"
GMAIL_USER = "your_email@gmail.com"
GMAIL_PASS = "Badal@143._"
openai.api_key = "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"

# ========= MEMORY DB (PostgreSQL) =========
try:
    conn = psycopg2.connect(
        dbname="aether_db",
        user="postgres",
        password="Badal@143._$",
        host="localhost",
        port="5432"
    )
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP,
            entry TEXT
        );
        CREATE TABLE IF NOT EXISTS analytics (
            id SERIAL PRIMARY KEY,
            timestamp TIMESTAMP,
            command TEXT,
            intent TEXT
        );
    """)
    conn.commit()
except Exception as e:
    print(f"Database setup error: {e}")
    conn = None

engine = pyttsx3.init()
emotion_mode = "pro"

# ========= INTENT DETECTION =========
intent_examples = {
    "open": ["open youtube", "open google", "open linkedin"],
    "play": ["play video", "play song", "play something"],
    "notes": ["generate notes", "make pdf", "create summary"],
    "email": ["send email", "email someone"],
    "thank": ["thank you", "thanks for conversation"],
    "weather": ["weather update", "today weather"],
    "news": ["latest news", "news headlines"],
    "reminder": ["remind me", "set reminder"],
    "alarm": ["set alarm", "wake me up"],
    "motivate": ["motivate me", "inspire me"],
    "calendar": ["my schedule", "google calendar"],
    "call": ["whatsapp call", "call friend"],
    "memory": ["remember this", "recall memory"],
    "translate": ["translate this", "speak in hindi"],
    "chatgpt": ["ask chatgpt", "openai query"],
    "ai_task": ["run ai task", "microtask mode"],
    "joke": ["tell joke", "make me laugh"],
    "analytics": ["usage analytics", "show stats"],
    "face_unlock": ["unlock with face"],
    "social": ["open instagram", "open facebook"],
    "daily_briefing": ["give me daily briefing"],
    "log_workout": ["log workout"],
    "learn_language": ["teach me spanish"],
    "recipe": ["suggest recipe"],
    "travel": ["tell me about paris"],
    "mobile_mode": ["activate mobile mode"],
    "cloud": ["upload to cloud", "aws backup"],
    "command_gui": ["show command dashboard"],
    "calculator": ["calculate", "do some math"],
    "mood_check": ["how do I feel", "check my mood"],
    "daily_affirmation": ["give me an affirmation", "positive affirmation"],
    "trivia": ["trivia quiz", "ask me trivia"],
    "personalized_recommendation": ["recommend a movie", "suggest a book"],
    "dream_interpretation": ["interpret my dream", "what does my dream mean"],
    "storytelling": ["tell me a story", "create a story"],
    "mood_based_music": ["play music for my mood", "mood music"],
    "virtual_pet": ["interact with my pet", "play with my pet"],
    "life_coach": ["help me set goals", "motivate me"],
    "cultural_exchange": ["tell me about another culture", "cultural facts"],
    "health_monitoring": ["give me health tips", "track my health"],
    "creative_writing": ["help me write a story", "brainstorm ideas"],
    "meditation": ["guide me in meditation", "start meditation"],
    "astrology": ["what's my horoscope", "tell me my zodiac sign"],
    "virtual_travel": ["take me to a virtual tour", "explore a country"],
    "skill_development": ["suggest a course", "help me learn a skill"],
    "event_planning": ["help me plan an event", "event ideas"],
    "sustainability_tips": ["give me sustainability tips", "eco-friendly practices"],
    "random_kindness": ["suggest a random act of kindness", "kindness ideas"],
    "personal_finance": ["track my expenses", "budgeting tips"],
    "book_club": ["discuss a book", "suggest a book for reading"],
    "interactive_games": ["play a game", "let's play a quiz"],
    "community_energy": ["community-driven renewable energy microgrid"],
    "urban_quality": ["urban area quality monitor"],
    "water_management": ["smart water management system"],
    "food_waste": ["AI driven food waste reduction platform"],
    "career_guidance": ["career guidance platform"],
    "chat_app": ["real-time chat app with authentication"],
    "wildrisk_prediction": ["wildrisk prediction alert system"],
    "cyber_guard": ["cyber guard AI 2025"],
    "handwritten_recognizer": ["handwritten text recognizer"],
    "password_manager": ["password manager"],
    "attendance_system": ["auto attendance taking system"],
    "word_puzzle": ["word puzzle game"],
    "candy_crush": ["candy crush"],
    "calculator_game": ["calculator"],
    "taskflow_dashboard": ["taskflow dashboard"],
    "balance_track": ["balance track hub"],
    "ping_pong_game": ["ping pong game"],
    "snake_game": ["snake game"],
    "rock_paper_game": ["rock paper game"],
    "ecommerce": ["ecommerce website"],
    "weather_app": ["weather app"],
    "healthcare_assistant": ["AI smart healthcare diagnosis assistant"],
    "price_negotiator": ["price negotiator ecommerce chatbot"],
    "project_review_monitor": ["fake project review monitor"]
}
all_texts = sum(intent_examples.values(), [])
all_labels = [k for k, v in intent_examples.items() for _ in v]
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(all_texts)
clf = LogisticRegression()
clf.fit(X, all_labels)

# ========= CORE UTILS =========
def speak(text):
    print(f"{ASSISTANT_NAME} ➤ {text}")
    engine.say(text)
    engine.runAndWait()

def listen():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)
    try:
        return r.recognize_google(audio, language='en-in').lower()
    except:
        return ""

def log_command(command, intent):
    if conn:
        cursor.execute("INSERT INTO analytics (timestamp, command, intent) VALUES (%s, %s, %s)",
                       (datetime.now(), command, intent))
        conn.commit()

def detect_intent(text):
    vec = vectorizer.transform([text])
    return clf.predict(vec)[0]

# ========= MEMORY FUNCTIONS =========
def add_to_memory(item):
    if conn:
        cursor.execute("INSERT INTO memory (timestamp, entry) VALUES (%s, %s)", (datetime.now(), item))
        conn.commit()
        speak(f"I have remembered: {item}")

def recall_memory():
    speak("What do you want to recall?")
    keyword = listen()
    if conn:
        cursor.execute("SELECT entry FROM memory WHERE entry ILIKE %s", (f"%{keyword}%",))
        rows = cursor.fetchall()
        if rows:
            for row in rows:
                speak(row[0])
        else:
            speak("Nothing found for that keyword.")

# ========= FEATURE MODULES =========
def face_unlock():
    speak("Scanning face... please look at the camera.")
    cap = cv2.VideoCapture(0)
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        try:
            result = deepface.analyze(frame, actions=['emotion'], enforce_detection=False)
            emotion = result[0]['dominant_emotion']
            speak(f"You look {emotion} right now.")
            break
        except Exception as e:
            speak("Face not detected clearly. Please adjust your position.")
    cap.release()
    speak("Face scan complete.")
def daily_briefing():
    weather = get_weather("Delhi")
    news = get_news()
    speak(f"Here’s your daily briefing. Weather in Delhi is {weather}. Top headlines: {news}.")

def log_workout():
    speak("What workout did you do today?")
    workout = listen()
    speak(f"Logged your workout: {workout}")

def learn_language():
    speak("What phrase would you like to translate?")
    phrase = listen()
    translation = GoogleTranslator(source='auto', target='es').translate(phrase)
    speak(f"In Spanish, that's: {translation}")

def suggest_recipe():
    speak("Tell me your available ingredients.")
    ingredients = listen()
    speak(f"With {ingredients}, try making a stir-fry or pasta.")

def command_dashboard():
    speak("Launching GUI command dashboard")
    root = tk.Tk()
    root.title("Aether AI Command Center")
    cmds = list(intent_examples.keys())
    for idx, cmd in enumerate(cmds):
        tk.Button(root, text=cmd, command=lambda c=cmd: speak(f"Command triggered: {c}"), width=25).grid(row=idx, column=0, padx=10, pady=2)
    root.mainloop()

def activate_mobile_mode():
    speak("Mobile mode activated. Optimized for smaller screen.")
def fetch_analytics():
    speak("Analytics tracking coming soon.")

def travel_info():
    speak("Travel information feature coming soon.")

def cloud_backup():
    speak("Cloud backup functionality not implemented yet.")

# ========= OPEN LINKS FUNCTIONS =========
def open_link(url):
    webbrowser.open(url)
    speak(f"Opening {url}")

def handle_command(command):
    intent = detect_intent(command)
    log_command(command, intent)
    if intent == "open":
        open_apps(command)
    elif intent == "weather":
        speak("Which city?")
        speak(get_weather(listen()))
    elif intent == "news":
        speak(get_news())
    elif intent == "reminder":
        speak("Reminder?")
        msg = listen()
        speak("When? HH:MM:SS")
        t = datetime.strptime(listen(), "%H:%M:%S")
        threading.Thread(target=lambda: (
            time.sleep((datetime.now().replace(hour=t.hour, minute=t.minute, second=t.second) - datetime.now()).total_seconds()),
            speak(f"Reminder: {msg}")
        ), daemon=True).start()
    elif intent == "alarm":
        speak("Alarm time HH:MM:SS")
        t = datetime.strptime(listen(), "%H:%M:%S")
        threading.Thread(target=lambda: (
            time.sleep((datetime.now().replace(hour=t.hour, minute=t.minute, second=t.second) - datetime.now()).total_seconds()),
            speak("Alarm ringing!")
        ), daemon=True).start()
    elif intent == "motivate":
        speak(random.choice(["Push harder!", "Stay focused!", "Make today count!"]))
    elif intent == "translate":
        txt = listen()
        speak("Language?")
        lang = listen()
        lang_map = {"hindi": "hi", "english": "en", "spanish": "es"}
        translated = GoogleTranslator(source='auto', target=lang_map.get(lang, "en")).translate(txt)
        speak(translated)
    elif intent == "chatgpt":
        speak("What should I ask?")
        prompt = listen()
        res = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": prompt}])
        speak(res['choices'][0]['message']['content'])
    elif intent == "memory":
        add_to_memory(command) if "remember" in command else recall_memory()
    elif intent == "ai_task":
        speak("Starting AI task mode...")
    elif intent == "joke":
        speak(random.choice(["What do you call a smart assistant? Anu-telligent!", "I would tell a UDP joke, but you might not get it."]))
    elif intent == "analytics":
        fetch_analytics()
    elif intent == "face_unlock":
        face_unlock()
    elif intent == "daily_briefing":
        daily_briefing()
    elif intent == "log_workout":
        log_workout()
    elif intent == "learn_language":
        learn_language()
    elif intent == "recipe":
        suggest_recipe()
    elif intent == "travel":
        travel_info()
    elif intent == "mobile_mode":
        activate_mobile_mode()
    elif intent == "cloud":
        cloud_backup()
    elif intent == "command_gui":
        command_dashboard()
    elif intent == "community_energy":
        open_link("https://community-driven-renewable-energy-microgrid.vercel.app/")
    elif intent == "urban_quality":
        open_link("https://urban-area-quality-monitor.vercel.app/")
    elif intent == "water_management":
        open_link("https://smart-water-management-system-kappa.vercel.app/")
    elif intent == "food_waste":
        open_link("https://ai-driven-food-waste-reduction-platform.vercel.app/")
    elif intent == "career_guidance":
        open_link("https://carrer-guidance-platform.vercel.app/")
    elif intent == "chat_app":
        open_link("https://real-time-chat-app-with-authentication-web-socket.vercel.app/")
    elif intent == "wildrisk_prediction":
        open_link("https://wildrisk-prediction-alert-system.vercel.app/")
    elif intent == "cyber_guard":
        open_link("https://cyber-guard-ai-2025.vercel.app/")
    elif intent == "handwritten_recognizer":
        open_link("https://handritten-text-recognizer.vercel.app/")
    elif intent == "password_manager":
        open_link("https://password-maneger-tau.vercel.app/")
    elif intent == "attendance_system":
        open_link("https://auto-attendance-taling-system.vercel.app/")
    elif intent == "word_puzzle":
        open_link("https://word-puzzle-game-orpin.vercel.app/")
    elif intent == "candy_crush":
        open_link("https://candy-crush-smoky.vercel.app/")
    elif intent == "calculator_game":
        open_link("https://arcade-math-wizard.vercel.app/")
    elif intent == "taskflow_dashboard":
        open_link("https://taskflow-dashboard-craft.vercel.app/")
    elif intent == "balance_track":
        open_link("https://balance-track-hub-viny.vercel.app/")
    elif intent == "ping_pong_game":
        open_link("https://ping-pong-game-one-rosy.vercel.app/")
    elif intent == "snake_game":
        open_link("https://snake-game-online-rcx0zu4hd-anwesha-mishras-projects.vercel.app/")
    elif intent == "rock_paper_game":
        open_link("https://rock-paper-game-psi.vercel.app/")
    elif intent == "ecommerce":
        open_link("https://ecommerce-seven-eta-21.vercel.app/")
    elif intent == "weather_app":
        open_link("https://weather-app-ruddy-zeta.vercel.app/")
    elif intent == "healthcare_assistant":
        open_link("https://ai-smart-healthcare-diagonys-assisant.netlify.app/")
    elif intent == "price_negotiator":
        open_link("https://price-negotiator-ecommerce-chatbot.netlify.app/")
    elif intent == "project_review_monitor":
        open_link("https://fake-project-review-monitor.netlify.app/")
    elif "exit" in command or "bye" in command:
        speak(f"Goodbye {USER_NAME}")
        exit()
    else:
        speak("You said: " + command)

def open_apps(command):
    apps = {
        "youtube": "https://youtube.com",
        "google": "https://google.com",
        "whatsapp": "https://web.whatsapp.com",
        "gmail": "https://mail.google.com",
        "linkedin": "https://linkedin.com",
        "instagram": "https://instagram.com",
        "facebook": "https://facebook.com",
        "leetcode": "https://leetcode.com",
        "spotify": "https://spotify.com"
    }
    for key, url in apps.items():
        if key in command:
            webbrowser.open(url)
            speak(f"Opening {key}")
            return
    speak("App not found")

# ========= ADDITIONAL FUNCTIONS =========
def get_weather(city="Delhi"):
    """Fetch weather information for a given city."""
    try:
        url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()
        if data.get("cod") != 200:
            return "Weather data not found."
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]
        return f"{desc} with {temp}°C"
    except:
        return "Weather data unavailable."

def get_news():
    """Fetch the latest news headlines."""
    try:
        url = f"https://newsapi.org/v2/top-headlines?country=in&apiKey={NEWS_API_KEY}"
        articles = requests.get(url).json().get("articles", [])
        return " | ".join([a["title"] for a in articles[:3]])
    except:
        return "News unavailable."

def play_robot_video():
    """Play a robot video."""
    if not os.path.exists(ROBOT_VIDEO_PATH): return
    def show_video():
        win = tk.Tk()
        lbl = tk.Label(win)
        lbl.pack()
        player = tkvideo(ROBOT_VIDEO_PATH, lbl, loop=1, size=(400, 400))
        player.play()
        win.after(15000, win.destroy)
        win.mainloop()
    threading.Thread(target=show_video, daemon=True).start()

# ========= INIT =========
if __name__ == "__main__":
    play_robot_video()
    speak(f"Hello {USER_NAME}, I am {ASSISTANT_NAME}. How can I help you today?")
    while True:
        command = listen()
        if command:
            if WAKE_WORD in command:
                command = command.replace(WAKE_WORD, "").strip()
            handle_command(command)
        if "exit" in command or "bye" in command:
            speak("Shutting down. Bye!")
            break
