import sqlite3
import os
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
import re

# Function for adding an item set and price into the database
def AddLog(message, log_name, item_name, item_price):
    conn = sqlite3.connect('log.db')
    cursor = conn.cursor()

    user_id = message.from_user.id

    cursor.execute('''
    INSERT INTO log (user_id, log_name, item_name, item_price)
    VALUES (?, ?, ?, ?)
    ''', (user_id, log_name, item_name, item_price))

    conn.commit()
    conn.close()

# Function for viewing user's previous logs in chat, returning them as a list
def FetchPastLogs(message):
    conn = sqlite3.connect('log.db')
    cursor = conn.cursor()

    user_id = message.from_user.id

    cursor.execute('''
    SELECT DISTINCT log_name, timestamp
    FROM log
    WHERE user_id = ?
    ''', (user_id,))

    # Store logname and timestamp of all logs associated with user into PastLogs as a set of tuples
    PastLogs_unformatted = cursor.fetchall()
    conn.close()

    if PastLogs_unformatted:
        return PastLogs_unformatted
    else:
        return None

    

# Function for fetching a specific log's details
def FetchLog(log_name):
    conn = sqlite3.connect('log.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT item_name, item_price 
    FROM log
    WHERE log_name = ?
    ''', (log_name,))

    # Store item_name and item_price as a list of tuples
    PastLog_unformatted = cursor.fetchall()
    conn.close()
    return PastLog_unformatted

#function for editing specific log entry
def EditLog(item_name, log_name):
    conn = sqlite3.connect('log.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT DISTINCT log_name, timestamp
    FROM log
    WHERE log_name
    ''', (user_id,))

    # Store logname and timestamp of all logs associated with user into PastLogs as a set of tuples
    PastLogs_unformatted = cursor.fetchall()
    conn.close()

    if PastLogs_unformatted:
        return PastLogs_unformatted
    else:
        return None
    
# OCR the receipt, returns either the stripped items and price OR None
def ReceiptToText(image_path: str):
    try:
        img = Image.open(image_path)
        # Convert image to grayscale
        img = img.convert("L")
        # resize image
        img = img.resize((img.width * 2, img.height * 2), Image.Resampling.LANCZOS)
        # Enhance contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(2)
        # Perform thresholding
        img = img.point(lambda p: p > 128 and 255)
        # Light blur to reduce noise
        img = img.filter(ImageFilter.SMOOTH)

        text = pytesseract.image_to_string(img)
        os.remove(image_path)
        print("Raw OCR Output:\n", text)

        # Regex pattern to identify logged items
        item_price_pattern = r"([A-Za-z\s&]+)\s+(\$?\d+\.\d{2})"
        matches = re.findall(item_price_pattern, text)

        # Sort items into a list of tuples, filtering out some words
        receipt_items = []
        for item_name, item_price in matches:
            if not any(word in item_name.lower() for word in ["tax", "subtotal", "total", "take home", "cashier", "check", "table"]):
                receipt_items.append((item_name.strip(), item_price.strip()))

        return receipt_items

    except Exception as e:
        print(f"Error processing receipt: {e}")
        return None