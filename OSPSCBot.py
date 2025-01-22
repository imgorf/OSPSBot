import logging
import os
from dotenv import load_dotenv
from telegram import Update, ForceReply, Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ConversationHandler
from utility import *


load_dotenv() #loads env file
api_key=os.getenv('OSPSCBot_Key') #imports api key from env file
IMAGE_FOLDER = 'LogProcessing' #declares log processing folder

#Define conversation states
NEW_LOG_NAME = 1
NEW_LOG_RECEIPT = 2

#enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

#Send a message when the command /start is issued
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    #generate greeting message upon start activation
    text = f"Hi {user.mention_html()}!"
    #call main menu function with greeting text
    await main_menu(update, context, text)

# Display main menu
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, text:str):    
    # Buttons for the main menu
    main_menu_keyboard = [
        [InlineKeyboardButton("New Log", callback_data='NewLog')],
        [InlineKeyboardButton("View Log History", callback_data='ViewLogHistory')],
    ]
    reply_markup=InlineKeyboardMarkup(main_menu_keyboard)

    #send the main menu to chat along with greeting
    await update.message.reply_html(
        text=text,
        reply_markup=reply_markup
    )

# begin conversation for making new log
async def NewLog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    #Request user for log name
    await update.callback_query.message.reply_text("What would you like to name your new log?")
    return NEW_LOG_NAME
    
async def NewLogName(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    log_name = update.message.text
    #store log name
    context.user_data['log_name'] = log_name
    #Request user for receipt
    await update.message.reply_text("Send an image of the receipt you would like to log.")
    return NEW_LOG_RECEIPT

#returns itself if image is rejected by tessaract
async def NewLogReceipt(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
        user_image = update.message
        #save the image to LogProcessing
        photo_file = user_image.photo[-1].get_file()
        file_path = os.path.join(IMAGE_FOLDER, f"{update.message.from_user.id}_{photo_file.file_id}.jpg")
        await photo_file.download(file_path)
        receipt_items = ReceiptToText(file_path)

        if receipt_items:
            context.user_data['receipt_items'] = receipt_items
            formatted_text = "\n".join([f"{item_name}: {item_price}" for item_name, item_price in matches])
            await update.message.reply_text(formatted_text)
            receipt_confirmation_keyboard = [
                [InlineKeyboardButton("Yes", callback_data='ReceiptYes')],
                [InlineKeyboardButton("No", callback_data='ReceiptNo')],
            ]
            reply_markup = InlineKeyboardMarkup(receipt_confirmation_keyboard)
            await update.message.reply_text("Are these items correct?", reply_markup=reply_markup)

        #in case None is returned
        else:
            await update.message.reply_text("Please send a clearer image.")
            return NEW_LOG_RECEIPT

#restart NewLogReceipt if no, save data if yes
async def ReceiptConfirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # Acknowledge the callback query

    if query.data =='ReceiptYes':
        for item_name, item_price in context.user_data['receipt_items']:
            AddLog(update, context, item_name, item_price)
    
    if query.data =='ReceiptNo':
        await update.message.reply_text("Send an image of the receipt you would like to log.")
        return NEW_LOG_RECEIPT

async def main():
    bot = telegram.Bot(api_key)
    async with bot:
        print(await bot.get_me())


if __name__ == '__main__':
    application = ApplicationBuilder().token(api_key).build()

    #sets conversation states
    conversation_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],  # Triggered when /start is called
        states={
            NEW_LOG_NAME: [MessageHandler(filters.Text & ~filters.command, NewLogName)],
            NEW_LOG_RECEIPT: [MessageHandler(filters.Text & ~filters.command, NewLogReceipt)],
        },
    )
    
    start_handler = CommandHandler('start', start)
    application.add_handler(start_handler)
    application.add_handler(CallbackQueryHandler(NewLog, pattern='^NewLog$'))
    #add handler for viewing log history
    application.add_handler(CallbackQueryHandler(ReceiptConfirmation, pattern='^(ReceiptYes|ReceiptNo)$'))

    application.run_polling()