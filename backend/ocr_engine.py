import pytesseract
import re
import cv2
import numpy as np
from PIL import Image
import os
import shutil

# --- CONFIGURATION ---
# Check if we are on Windows (Local) or Linux (Server)
if os.name == 'nt':
    # Your local path
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
else:
    # Linux server path (Standard location)
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'



def preprocess_image(image_path):
    try:
        img = cv2.imread(image_path)
        h, w = img.shape[:2]
        if w < 1000:
            scale = 2
            img = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC)
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        denoised = cv2.fastNlMeansDenoising(gray, None, h=10, templateWindowSize=7, searchWindowSize=21)
        norm_img = np.zeros((img.shape[0], img.shape[1]))
        processed = cv2.normalize(denoised, norm_img, 0, 255, cv2.NORM_MINMAX)
        return processed
    except Exception as e:
        print(f"Error processing image: {e}")
        return None

def detect_currency(text):
    patterns = [
        (r'€', '€'), (r'£', '£'), (r'¥', '¥'), (r'\$', '$'),
        (r'(?i)\bPKR\b', 'PKR'), (r'(?i)\bRs\.?\b', 'Rs'), 
        (r'(?i)\bUSD\b', '$'), (r'(?i)\bEUR\b', '€'), (r'(?i)\bGBP\b', '£'),
        (r'(?i)PAKISTAN', 'PKR'), (r'(?i)LAHORE', 'PKR'), 
        (r'(?i)USA', '$'), (r'(?i)UK', '£'), (r'(?i)IRELAND', '€'), (r'(?i)DUBLIN', '€'), 
        (r'(?i)CANADA', 'CAD'),
    ]
    for pattern, symbol in patterns:
        if re.search(pattern, text):
            return symbol
    return '' 

def assign_category(text):
    text_upper = text.upper()
    categories = {
        "GROCERIES": ["WALMART", "TARGET", "COSTCO", "MARKET", "FOOD", "GROCERY", "MILK", "BREAD", "MEAT", "EGGS", "SVESTON"], 
        "DINING": ["RESTAURANT", "CAFE", "COFFEE", "BURGER", "PIZZA", "GRILL", "KITCHEN", "STARBUCKS", "MCDONALDS", "BAR", "TIKKA", "KARHAI", "STEAKHOUSE", "OUTBACK", "DINNER", "LUNCH"],
        "TECH": ["BEST BUY", "APPLE", "MICROSOFT", "PHONE", "ELECTRONICS", "COMPUTER", "DATA", "MOBILE", "GADGET", "TECHNO", "MACBOOK", "LAPTOP"], 
        "GAS": ["SHELL", "FUEL", "GAS", "PETROL", "STATION"],
        "TRAVEL": ["HOTEL", "UBER", "LYFT", "FLIGHT", "AIRLINE", "TAXI"],
        "FASHION": ["CLOTHES", "ZARA", "H&M", "JEWELRY", "WATCH", "SVESTON", "WEAR", "SHIRT", "PANT"]
    }
    for category, keywords in categories.items():
        if any(keyword in text_upper for keyword in keywords):
            return category
    return "EXPENSE"

def parse_items(text):
    items = []
    lines = text.split('\n')
    
    # --- UPDATED IGNORE LIST ---
    ignore_markers = [
        "SUBTOTAL", "NET AMOUNT", "TAX", "CASH", "CHANGE", "CREDIT", "BALANCE",
        "TEL", "FAX", "PHONE", "CONTACT", "HELPLINE", "NTN", "STRN", "TRN", "GST", "FBR",
        "DATE", "TIME", "BILL", "ORDER", "RECEIPT", "ST#", "OP#", "TE#", "TR#", "TC#", "REF #",
        "CUSTOMER", "USER", "CASHIER", "ACCOUNT", "APPROVAL", "TERMINAL", "MERCHANT",
        "VISA", "MASTERCARD", "AMEX", "SOFTWARE", "POWERED BY", "VERSION",
        "QTY", "DESCRIPTION", "PRICE", "AMOUNT", "ITEM", "TOTAL",
        "STREET", "AVENUE", "ROAD", "DUBLIN", "IRELAND", "PAYMENT METHOD", "VAT", "CARD", "INVOICE",
        "SOLD", "COPY", "STORE", "LB", "KG",
        
        # NEW ADDRESS BLOCKERS:
        "MANAGER", "CITY", "STATE", "ZIP", "LANE", "DRIVE", "BLVD", "HWY", "WALL ST"
    ]

    for line in lines:
        clean_line = line.strip().upper()
        if len(clean_line) < 4: continue
        if any(marker in clean_line for marker in ignore_markers): continue

        price_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*[A-Z]{0,3}$', clean_line)
        if not price_match:
             price_match = re.search(r'(\d{1,5}\.\d{2})\s*[A-Z]{0,3}$', clean_line)

        if price_match:
            price_str_full = price_match.group(0)
            price_value_match = re.search(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)', price_str_full)
            if not price_value_match: continue
            
            price_str = price_value_match.group(1).replace(',', '')

            try:
                # --- NEW FILTER: ZIP CODE KILLER ---
                # If it's exactly 5 digits (like 88888) and has no decimal, it's a Zip Code.
                if re.match(r'^\d{5}$', price_str): continue
                
                if float(price_str) == 0: continue
                if float(price_str) < 10 and "." not in price_str: continue 
            except: continue

            if len(price_str) == 4 and (price_str.startswith("20") or price_str.startswith("19")): continue
            
            # Extract Name
            raw_text = clean_line[:price_match.start()].strip()
            raw_text = re.sub(r'\d{5,}', '', raw_text) # Remove long numbers from name
            raw_text = re.sub(r'[\d\.\#\*\-\:]+$', '', raw_text).strip()
            
            if len(raw_text) > 2 and re.search(r'[A-Z]', raw_text):
                items.append({"name": raw_text, "price": price_str, "qty": 1})    
    return items

def extract_data(image_path):
    clean_img = preprocess_image(image_path)
    if clean_img is None: return {"error": "Could not process image"}

    custom_config = r'--oem 3 --psm 6'
    text = pytesseract.image_to_string(clean_img, config=custom_config)
    
    currency_symbol = detect_currency(text)

    total_amount = "0.00"
    high_priority_pattern = r'(?i)(?:NET AMOUNT|GRAND TOTAL|AMOUNT DUE|TOTAL PAYABLE|BALANCE DUE|TOTAL PAID)[^\d]*([\d,]+\.?\d*)'
    priority_match = re.search(high_priority_pattern, text)
    
    if priority_match:
        total_amount = priority_match.group(1).replace(',', '')
    else:
        fallback_pattern = r'(?i)\bTOTAL\b(?!\s+(?:QTY|ITEM|ITEMS|COUNT|CNTS))[^\d]*([\d,]+\.?\d*)'
        fallback_match = re.search(fallback_pattern, text)
        if fallback_match:
            total_amount = fallback_match.group(1).replace(',', '')

    items_list = parse_items(text)

    try:
        float_total = float(total_amount)
        calculated_sum = sum(float(item['price']) for item in items_list)
        if float_total == 0 or (float_total < 10 and calculated_sum > float_total):
            total_amount = "{:.2f}".format(calculated_sum)
    except:
        pass 

    date_pattern = r'(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})'
    date_match = re.search(date_pattern, text)
    date_value = date_match.group(1) if date_match else "Unknown"
    category_value = assign_category(text)

    return {
        "total": total_amount,
        "date": date_value,
        "category": category_value,
        "currency": currency_symbol,
        "items": items_list,
        "raw_text": text 
    }

if __name__ == "__main__":
    result = extract_data("test.png")
    print(f"Currency: {result.get('currency')}")
    print(f"Total: {result.get('total')}")
    print(f"Items: {result.get('items')}")