import logging
import asyncio
import os
from dotenv import load_dotenv
from telegram import Update, ForceReply, Bot
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler

load_dotenv() #loads env file
api_key=os.getenv('OSPSCBot_Key') #imports api key from env file

#enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

#Send a message when the command /start is issued
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )

async def NewLog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    Bot.send_message(chat_id=chat_id, text="What would you like to name this log?")



async def main():
    bot = telegram.Bot(api_key)
    async with bot:
        print(await bot.get_me())


if __name__ == '__main__':
    application = ApplicationBuilder().token(api_key).build()
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    
    application.run_polling()