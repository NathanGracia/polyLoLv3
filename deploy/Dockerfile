FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir flask flask-cors

# Copy application
COPY bot.py .
COPY web_app.py .
COPY templates ./templates
COPY .env .

# Expose port
EXPOSE 5000

# Run app
CMD ["python", "web_app.py"]
