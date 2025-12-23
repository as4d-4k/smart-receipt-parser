import os
import pandas as pd
from ocr_engine import extract_data

# 1. Load Images
image_folder = "./CORD/train/image"
results = []

for filename in os.listdir(image_folder):
    if filename.endswith(".png"):
        # 2. Run your Engine
        data = extract_data(os.path.join(image_folder, filename))

        # 3. Log Success/Failure
        results.append({
            "file": filename,
            "total_found": data['total'],
            "items_count": len(data['items']),
            "currency": data['currency']
        })

# 4. Save Report
df = pd.DataFrame(results)
df.to_csv("ocr_report.csv", index=False)