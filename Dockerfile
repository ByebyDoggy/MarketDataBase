FROM python:3.11-slim

LABEL authors="byebyedoggy"

WORKDIR /market-data-collector

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["python", "main.py"]
