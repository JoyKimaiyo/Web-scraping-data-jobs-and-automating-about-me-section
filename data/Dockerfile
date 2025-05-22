FROM python:3.10-slim

WORKDIR /data

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY web.py .

CMD ["python", "web.py"]

