from env import TELEGRAM_BOT_TOKEN
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    ContextTypes,
)
from tutor_crew import EnglishTutorCrew, add_to_conversation
from utils import speech_to_text, text_to_speech
import os


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.voice is None:
        return

    await update.message.reply_text(
        "Processing your voice message... Please wait a moment!"
    )

    # 음성 파일 다운로드
    voice_file = await update.message.voice.get_file()
    audio_path = f"voice_{update.message.message_id}.ogg"
    await voice_file.download_to_drive(audio_path)

    # 음성을 텍스트로 변환
    user_message = speech_to_text(audio_path)

    # 임시 파일 삭제
    if os.path.exists(audio_path):
        os.remove(audio_path)

    if user_message.startswith("Error"):
        await update.message.reply_text(
            "Sorry, I couldn't understand your voice message. Please try again."
        )
        return

    # 최신 대화 기록이 포함된 크루를 동적으로 생성
    tutor_crew = EnglishTutorCrew()
    crew = tutor_crew.crew()
    result = crew.kickoff(inputs={"message": user_message})

    # 대화를 히스토리에 저장
    bot_response = result.raw
    add_to_conversation(user_message, bot_response)

    # 응답을 음성으로 변환하고 전송
    voice_response_path = text_to_speech(
        bot_response, f"response_{update.message.message_id}.mp3"
    )

    if not voice_response_path.startswith("Error"):
        await update.message.reply_voice(voice=open(voice_response_path, "rb"))
        # 임시 파일 삭제
        if os.path.exists(voice_response_path):
            os.remove(voice_response_path)
    else:
        await update.message.reply_text(
            "Sorry, I encountered an error generating the voice response."
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None or update.message.text is None:
        return

    # 음성으로만 소통한다는 메시지를 음성으로 전송
    rejection_message = (
        "Please send me a voice message. I only communicate through voice!"
    )
    voice_path = text_to_speech(
        rejection_message, f"rejection_{update.message.message_id}.mp3"
    )

    if not voice_path.startswith("Error"):
        await update.message.reply_voice(voice=open(voice_path, "rb"))
        # 임시 파일 삭제
        if os.path.exists(voice_path):
            os.remove(voice_path)
    else:
        await update.message.reply_text(
            "Please send me a voice message. I only communicate through voice!"
        )


app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# 음성 메시지 핸들러 추가
app.add_handler(MessageHandler(filters.VOICE, handle_voice))

# 텍스트 메시지 핸들러 추가 (음성만 사용하라고 알려줌)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

app.run_polling()
