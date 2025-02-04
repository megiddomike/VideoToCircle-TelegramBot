import os
import subprocess
import logging
import tempfile
import asyncio

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# Logging Settings
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Change YOUR_BOT_TOKEN_HERE on your token from @BotFather
TOKEN = "YOUR_BOT_TOKEN_HERE"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """The handler of the command /start"""
    await update.message.reply_text("Send Me The Video")

async def videotonote(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Video Handler: downloads, converts and send video message"""
    # Checking, that a video exists in the message
    if not update.message.video:
        await update.message.reply_text("Please send file")
        return

    logger.info("Received a video from the user: %s", update.effective_user.username)
    status_message = await update.message.reply_text("Wait...")
    status_message_2 = await update.message.reply_text("P.S. If the message doesn't arrive, just wait. The bot may be overloaded")

    try:
        video = update.message.video
        file = await video.get_file()

        # Creating a temporary directory for storing files
        with tempfile.TemporaryDirectory() as tmpdirname:
            inputpath = os.path.join(tmpdirname, "inputvideo.mp4")
            outputpath = os.path.join(tmpdirname, "videonote.mp4")

            # Downloading original video
            await file.download_to_drive(custom_path=inputpath)
            logger.info("Video saved: %s", inputpath)

            # Forming the ffmpeg command:
            # 1. Crop the video to a square with a size equal to the minimum side. (min(iw,ih)).
            # 2. Scaling the result to 240x240 pixels (required size for video note).
            # 3. The -y option allows you to overwrite the output file without prompting..
            ffmpegcmd = "ffmpeg", "-y", "-i", inputpath, "-vf", "crop='min(iw,ih)':'min(iw,ih)',scale=240:240", "-c:a", "copy", outputpath
            

            process = subprocess.run(ffmpegcmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            if process.returncode != 0:
                logger.error("ffmpeg error: %s", process.stderr)
                await update.message.reply_text("An error occurred while processing the video.")
                return

            logger.info("Video successfully converted: %s", outputpath)
            # Deleting the temporary message
            await context.bot.deleteMessage(chat_id=update.effective_chat.id, message_id=status_message_2.message_id)
            await context.bot.deleteMessage(chat_id=update.effective_chat.id, message_id=status_message.message_id)
            await asyncio.sleep(2)
            await update.message.reply_text("Video successfully converted!")

            # We are sending the converted video as a video message. (video note)
            with open(outputpath, "rb") as videofile:
                await context.bot.sendVideoNote(
                    chat_id=update.effective_chat.id,
                    video_note=videofile,
                    duration=video.duration  # We specify the duration of the original video
                )
    except Exception as e:
        logger.exception("Error in video processing")
        await update.message.reply_text(f"An error has occurred: {e}")

def main() -> None:
    """The main function for launching a bot"""
    app = Application.builder().token(TOKEN).build()

    # Registering command and message handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.VIDEO, videotonote))

    logger.info("The bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()