FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend ./backend
COPY frontend ./frontend
COPY database ./database
EXPOSE 5000
CMD ["waitress-serve","--listen=0.0.0.0:5000","backend.app:app"]
