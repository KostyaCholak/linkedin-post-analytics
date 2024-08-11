FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Run the uvicorn server
CMD ["uvicorn", "src.app:app", "--host", "0.0.0.0", "--port", "80"]