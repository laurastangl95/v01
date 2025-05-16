import streamlit as st
import hashlib
from datetime import datetime
from googletrans import Translator
import speech_recognition as sr
import threading

# --- Passwortschutz ---
def check_password():
    def verify_password(pwd):
        hash = hashlib.sha256(pwd.encode()).hexdigest()
        return hash == st.secrets["password_hash"]

    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if not st.session_state["password_correct"]:
        pwd = st.text_input("Passwort", type="password")
        if pwd:
            if verify_password(pwd):
                st.session_state["password_correct"] = True
            else:
                st.error("Falsches Passwort")
                st.stop()
        else:
            st.stop()

check_password()

st.title("Med Tech Heroes")

translator = Translator()
file_path = "output.txt"

def save_to_file(source, content):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] ({source}): {content}\n")

if "entries" not in st.session_state:
    st.session_state["entries"] = []

def insert_entry(source, content):
    st.session_state["entries"].append((datetime.now().strftime("%H:%M:%S"), source, content))
    save_to_file(source, content)

def recognize_speech():
    r = sr.Recognizer()
    r.energy_threshold = 300
    r.dynamic_energy_threshold = False
    try:
        with sr.Microphone() as source:
            st.info("Sprich jetzt...")
            r.adjust_for_ambient_noise(source, duration=1)
            audio = r.listen(source, timeout=7)
            text = r.recognize_google(audio)
            if len(text) < 2:
                st.warning("Eingabe zu kurz.")
                return
            lang_detected = translator.detect(text).lang
            translated = translator.translate(text, src=lang_detected, dest='de').text
            insert_entry("Voice", translated)
            st.success(f"Erkannt und übersetzt: {translated}")
    except sr.WaitTimeoutError:
        st.warning("Zeitüberschreitung, kein Ton erkannt.")
    except Exception as e:
        st.error(f"Fehler: {e}")

if st.button("🎤 Sprich"):
    threading.Thread(target=recognize_speech).start()

text_input = st.text_input("Oder Text eingeben und übersetzen:")
if st.button("Absenden") and text_input.strip():
    try:
        lang_detected = translator.detect(text_input).lang
        translated = translator.translate(text_input, src=lang_detected, dest='de').text
        insert_entry("Text", translated)
        st.success(f"Übersetzt: {translated}")
    except Exception as e:
        st.error(f"Übersetzung fehlgeschlagen: {e}")

if st.session_state["entries"]:
    st.write("### Gespeicherte Einträge")
    st.table(st.session_state["entries"])

with open(file_path, "rb") as f:
    data = f.read()

st.download_button(
    label="Gespeicherte Datei herunterladen",
    data=data,
    file_name="output.txt",
    mime="text/plain"
)
