FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Expose the port (Render will set PORT environment variable) 
EXPOSE $PORT

# Start with comprehensive port binding logging and uvicorn configuration
CMD ["sh", "-c", "echo 'Starting with PORT='${PORT:-10000} && echo 'Binding to 0.0.0.0:'${PORT:-10000} && uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000} --workers 1 --timeout-keep-alive 30"]
