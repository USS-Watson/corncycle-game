from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
from elevenlabs import play
import os
import random
import json

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
    for line in join_lines:
        #replace placeholder {x}
        line = line.replace("{x}", name)
        print(line)
    line = random.choice(join_lines)
    play_audio(line)    

def play_win(name: str):
    win_lines = []
    with open("voice.json", "r") as f:
        win_lines = json.load(f)
        win_lines = win_lines["win"]
    for line in win_lines:
        #replace placeholder {x}
        line = line.replace("{x}", name)
        print(line)
    line = random.choice(win_lines)
    play_audio(line)
    
def play_lose(name: str):
    lose_lines = []
    with open("voice.json", "r") as f:
        lose_lines = json.load(f)
        lose_lines = lose_lines["crash"]
    for line in lose_lines:
        #replace placeholder {x}
        line = line.replace("{x}", name)
        print(line)
    line = random.choice(lose_lines)
    play_audio(line)
    
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