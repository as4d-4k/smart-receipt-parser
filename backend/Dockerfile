# 1. Use Python 3.11 as the base
FROM python:3.11-slim

# 2. Install System Dependencies
# - tesseract-ocr: The OCR engine
# - libgl1 & libglib2.0: Required for OpenCV to work
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# 3. Set up the working directory inside the container
WORKDIR /app

# 4. Copy dependency file and install Python libraries
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy the rest of your backend code
COPY . .

# 6. Expose the port Flask runs on
EXPOSE 5000

# 7. Start the app using Gunicorn (Production Server)
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]