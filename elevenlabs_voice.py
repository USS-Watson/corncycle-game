from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import os
import random
import json
import threading

load_dotenv()

client = ElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))

def generate_audio(text: str):
    audio = client.text_to_speech.convert(
        text=text,
        voice_id="weA4Q36twV5kwSaTEL0Q",
        output_format="mp3_44100_128",
    )
    return audio

def play_audio(text: str):
    audio = generate_audio(text)
    play(audio)
    
def play_audio_async(text: str):
    audio = generate_audio(text)
    threading.Thread(target=play, args=(audio,)).start()
    
def save_audio(text: str, filename: str):
    audio = generate_audio(text)
    with open(filename, "wb") as f:
        f.write(audio)

def play_audio_file(filename: str):
    play(filename)
    
def play_join(name: str):
    join_lines = []
    with open("voice.json", "r") as f:
        join_lines = json.load(f)
        join_lines = join_lines["join"]
    named_lines = []
    for line in join_lines:
        #replace placeholder {x}
        named_lines.append(line.replace("{x}", name))
    
    line = random.choice(named_lines)
    play_audio(line)    

def play_win(name: str):
    win_lines = []
    with open("voice.json", "r") as f:
        win_lines = json.load(f)
        win_lines = win_lines["win"]
    named_lines = []
    for line in win_lines:
        #replace placeholder {x}
        named_lines.append(line.replace("{x}", name))
    
    line = random.choice(named_lines)
    play_audio_async(line) #async to avoid blocking
    
def play_crash(name: str):
    crash_lines = []
    with open("voice.json", "r") as f:
        crash_lines = json.load(f)
        crash_lines = crash_lines["crash"]
    named_lines = []
    for line in crash_lines:
        #replace placeholder {x}
        named_lines.append(line.replace("{x}", name))
    line = random.choice(named_lines)
    play_audio_async(line) #async to avoid blocking
    
def get_start_filenames():
    return ["voice/start1.mp3", "voice/start2.mp3"]

def get_count_filename(count: int):
    if count == 1:
        return "voice/one.mp3"
    elif count == 2:
        return "voice/two.mp3"
    elif count == 3:
        return "voice/three.mp3"
    return "voice/go.mp3"