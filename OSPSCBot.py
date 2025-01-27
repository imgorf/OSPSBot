import logging
import os
from dotenv import load_dotenv
import telebot
import json
from telebot import types
from utility import *  # Assuming utility.py contains your helper functions

# Load environment variables
load_dotenv()
api_key = os.getenv('OSPSCBot_Key')  # Import API key from .env file
IMAGE_FOLDER = 'LogProcessing'  # Folder for storing receipt images

# Initialize the bot
bot = telebot.TeleBot(api_key)

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Dictionary to store user data temporarily
user_data = {}

# Send a message when the command /start is issued
@bot.message_handler(commands=['start'])
def start(message):
    user = message.from_user
    # Generate greeting message
    text = f"Hi {user.first_name}!"
    # Call main menu function with greeting text
    main_menu(message, text)

# Display main menu
def main_menu(message, text):
    # Buttons for the main menu
    main_menu_keyboard = types.InlineKeyboardMarkup([
        [types.InlineKeyboardButton("New Log", callback_data='NewLog')],
        [types.InlineKeyboardButton("View Past Logs", callback_data='ViewPastLogs')],
    ])

    # Send the main menu to chat along with greeting
    bot.send_message(
        chat_id=message.chat.id,
        text=text,
        reply_markup=main_menu_keyboard
    )

# Handle New Log callback
@bot.callback_query_handler(func=lambda call: call.data == 'NewLog')
def new_log(call):
    # Request user for log name
    bot.send_message(call.message.chat.id, "What would you like to name your new log?")
    bot.register_next_step_handler(call.message, new_log_name)

# Handle log name input
def new_log_name(message):
    log_name = message.text
    # Store log name in user data
    user_data[message.chat.id] = {'log_name': log_name}
    # Request user for receipt
    bot.send_message(message.chat.id, "Send an image of the receipt you would like to log.")
    bot.register_next_step_handler(message, new_log_receipt)

# Handle receipt image input
def new_log_receipt(message):
    if message.photo:
        # Save the image to LogProcessing
        photo_file = bot.get_file(message.photo[-1].file_id)
        file_path = os.path.join(IMAGE_FOLDER, f"{message.from_user.id}_{photo_file.file_id}.jpg")
        downloaded_file = bot.download_file(photo_file.file_path)
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)

        # Process the receipt
        receipt_items = ReceiptToText(file_path)
        if receipt_items:
            user_data[message.chat.id]['receipt_items'] = receipt_items
            formatted_text = "\n".join([f"{item_name}: {item_price}" for item_name, item_price in receipt_items])
            bot.send_message(message.chat.id, formatted_text)

            # Ask for confirmation
            receipt_confirmation_keyboard = types.InlineKeyboardMarkup([
                [types.InlineKeyboardButton("Yes", callback_data='ReceiptYes')],
                [types.InlineKeyboardButton("No", callback_data='ReceiptNo')],
            ])
            bot.send_message(message.chat.id, "Are these items correct?", reply_markup=receipt_confirmation_keyboard)
        else:
            bot.send_message(message.chat.id, "Please send a clearer image.")
            bot.register_next_step_handler(message, new_log_receipt)
    else:
        bot.send_message(message.chat.id, "Please send a valid image.")
        bot.register_next_step_handler(message, new_log_receipt)

# Handle receipt confirmation
@bot.callback_query_handler(func=lambda call: call.data in ['ReceiptYes', 'ReceiptNo'])
def receipt_confirmation(call):
    if call.data == 'ReceiptYes':
        # Save the log
        for item_name, item_price in user_data[call.message.chat.id]['receipt_items']:
            AddLog(call.message, user_data[call.message.chat.id]['log_name'], item_name, item_price)
        main_menu(call.message, "Log saved successfully!")
    elif call.data == 'ReceiptNo':
        # Request a new receipt
        bot.send_message(call.message.chat.id, "Send an image of the receipt you would like to log.")
        bot.register_next_step_handler(call.message, new_log_receipt)

# Handle View Past Logs callback
@bot.callback_query_handler(func=lambda call: call.data == 'ViewPastLogs')
def view_past_logs(call):
    # Fetch past logs
    PastLogs_unformatted = FetchPastLogs(call.message)
    if not PastLogs_unformatted:
        text = "No logs found."
        main_menu(call.message, text)
    else:
        # Format logs for display
        PastLogs_formatted = [f"{log[0]} - {log[1]}" for log in PastLogs_unformatted]
        keyboard = types.InlineKeyboardMarkup()
        for unformatted, formatted in zip(PastLogs_unformatted, PastLogs_formatted):
            #generate buttons with text of the formatted logs, while the log name is the callback
            log_name = unformatted[0]
            keyboard.add(types.InlineKeyboardButton(formatted, callback_data=f'check:{log_name}'))

        bot.send_message(call.message.chat.id, "Which would you like to check?", reply_markup=keyboard)

# Handle Check Past Log callback
@bot.callback_query_handler(func=lambda call: call.data.startswith('check:'))
def check_past_log(call):
    log_name = call.data.replace('check:', '')
    # fetchlog the item_name and item_price using the log_name
    PastLog_unformatted = FetchLog(log_name)
    PastLog_formatted = [f"{log[0]} - {log[1]}" for log in PastLog_unformatted]
    keyboard = types.InlineKeyboardMarkup()
    keyboard.add(types.InlineKeyboardButton('Delete Log', callback_data=f'delete:{log_name}'))

    for unformatted, formatted in zip(PastLog_unformatted, PastLog_formatted):
        #generate buttons with item_name and item_price, while the item details are log_name:item_name
        item_details = f'{log_name}:{unformatted[0]}'
        keyboard.add(types.InlineKeyboardButton(formatted, callback_data=f'price:{item_details}'))
    #add button for log deletion
    bot.send_message(call.message.chat.id, 'Which entry would you like to edit?', reply_markup=keyboard)

#receives the info about the specific log entry, gets price from user, passes it all to editlog
@bot.callback_query_handler(func=lambda call: call.data.startswith('price:'))
def get_log_price(call):
    log_details = call.data.replace('price:', '')
    chat_id = call.message.chat.id
    user_data[chat_id] = {'log_details': log_details}
    bot.send_message(call.message.chat.id, "What is the new price you would like to assign?")
    bot.register_next_step_handler_by_chat_id(chat_id, edit_Log)

def edit_Log(message):
    updated_price = message.text
    chat_id = message.chat.id
    log_details = user_data.get(chat_id, {}).get('log_details')
    log_name, item_name = log_details.split(":")
    text = EditLog(log_name, item_name, updated_price)
    main_menu(message, text)

@bot.callback_query_handler(func=lambda call: call.data.startswith('delete:'))
def delete_log(call):
    log_name = call.data.replace('delete:', '')
    user_id = call.from_user.id
    text = DeleteLog(log_name, user_id)
    main_menu(call.message,text)



# Start the bot
if __name__ == '__main__':
    print("Bot is running...")
    bot.polling()