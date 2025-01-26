import os

#libraries for ocr
from PIL import Image
import pytesseract
import re


#OCR the receipt, returns either the stripped items and price OR None
def ReceiptToText():
    try:
        #check if test image is present
        if not os.path.exists(r"D:\Projects\Git\OSPSCB\LogProcessing\test picture.jpg"):
            print("Image file not found!")
            return None
        
        img = Image.open(r"D:\Projects\Git\OSPSCB\LogProcessing\test picture.jpg")
        print("image stored into img")
        text = pytesseract.image_to_string(img)
        print("pytessaract worked")

        #regex pattern to identify logged items
        item_price_pattern = r"([A-Za-z\s\.\-]+)\s+(\$?\d+\.\d{2})"
        matches = re.findall(item_price_pattern, text)
        print("regex worked")
        #sort items into a list of dicts
        receipt_items = [(item_name.strip(), item_price.strip()) for item_name, item_price in matches]
        for item in receipt_items:
            print(item)
        return receipt_items
    
    except Exception as e:
        print('exception')
        return None
    

if __name__ == "__main__":
    result = ReceiptToText()
    print("Function Result:", result)
    