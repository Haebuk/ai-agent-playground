import openai
from env import OPENAI_API_KEY


def speech_to_text(audio_file_path: str) -> str:
    try:
        ai = openai.OpenAI(api_key=OPENAI_API_KEY)

        with open(audio_file_path, "rb") as audio_file:
            transcript = ai.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
            )
            return transcript.text
    except Exception as e:
        return f"Speech to text conversion failed: {e}"


def text_to_speech(text: str, output_path: str = "response.mp3"):
    try:
        ai = openai.OpenAI(api_key=OPENAI_API_KEY)
        response = ai.audio.speech.create(
            model="tts-1",
            input=text,
            voice="alloy",
        )
        with open(output_path, "wb") as f:
            f.write(response.content)
        return output_path
    except Exception as e:
        return f"Text to speech conversion failed: {e}"
