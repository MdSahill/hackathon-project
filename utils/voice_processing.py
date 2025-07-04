import os
import openai
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.environ.get("OPENAI_API_KEY")

class VoiceProcessor:
    @staticmethod
    def transcribe_audio(audio_file_path: str):
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = openai.Audio.transcribe("whisper-1", audio_file)
            return transcript["text"]
        except Exception as e:
            print(f"Error in transcription: {e}")
            return None