FROM python:3.7-slim-buster
RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements/ requirements/
RUN pip install --upgrade pip
RUN pip install -r requirements/local.txt --src=/root/pip
