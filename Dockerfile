FROM python:3.12-alpine
LABEL authors="TTLYTT0"

RUN apk add git build-base

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT ["python", "app.py"]