FROM python:3.10-slim

RUN apt-get update && apt-get install -y \
    && pip install --upgrade pip

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python3", "userbot.py"]
