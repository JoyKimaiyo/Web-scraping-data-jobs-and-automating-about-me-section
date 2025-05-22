# app/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY data_app.py .

CMD ["streamlit", "run", "data_app.py", "--server.port=8501", "--server.enableCORS=false"]

