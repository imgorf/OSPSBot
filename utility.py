import sqlite3
import os

#libraries for ocr
from PIL import Image
import pytesseract
import re

#function for adding an item set and price into the database
async def AddLog(update: Update, context: ContextTypes.DEFAULT_TYPE, item_name, item_price):
    conn = sqlite3.connect('log.db')
    cursor = conn.cursor()

    user_id = update.effective_user.id
    log_name = context.user_data['log_name']

    cursor.execute('''
    INSERT INTO logs (user_id, log_name, item_name, item_price)
    VALUES (?, ?, ?, ?)
    ''', (user_id, log_name, item_name, item_price))
    
    conn.commit()
    conn.close()
    
#function for viewing user's previous logs in chat, returning them as a list
async def FetchPastLogs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    conn = sqlite3.connect('log.db')
    cursor = conn.cursor()

    user_id = update.effective_user.id

    cursor.execute('''
    SELECT log_name, timestamp 
    FROM log
    WHERE user_id = ?
    ''', (user_id))
    
    #store logname and timestamp of all logs associated with user into PastLogs as a set of tuples
    PastLogs_unformatted = cursor.fetchall()
    conn.close()
    if PastLogs_unformatted != []:
        return PastLogs_unformatted

    else:
        return None
    

async def FetchLog(update: Update, context: ContextTypes.DEFAULT_TYPE, log):
    conn = sqlite3.connect('log.db')
    cursor = conn.cursor()

    user_id = update.effective_user.id
    log_name = log[0]

    cursor.execute('''
    SELECT item_name, item_price 
    FROM log
    WHERE user_id = ?
    AND log_name = ?
    ''', (user_id, log_name))
    
    #store item_name and item_price as a list of tuples
    PastLog_unformatted = cursor.fetchall()
    conn.close()
    return PastLog_unformatted


#OCR the receipt, returns either the stripped items and price OR None
async def ReceiptToText(image_path: str) -> str:
    try:
        #scan image for text
        img = Image.open(image_path)
        text = pytesseract.image_to_string(img)
        os.remove(image_path)

        #regex pattern to identify logged items
        item_price_pattern = r"([A-Za-z\s\.\-]+)\s+(\$?\d+\.\d{2})"
        matches = re.findall(item_price_pattern, text)
        #sort items into a list of dicts
        receipt_items = [(item_name.strip(), item_price.strip()) for item_name, item_price in matches]
        return receipt_items
    
    except Exception as e:
        return None