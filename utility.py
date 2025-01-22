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