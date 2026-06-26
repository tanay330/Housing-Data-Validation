FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

RUN mkdir -p uploads/output

EXPOSE 8000

CMD ["sh", "-c", "sleep 15 && uvicorn app.main:app --host 0.0.0.0 --port 8000"]