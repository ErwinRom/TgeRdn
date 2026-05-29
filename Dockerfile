FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chmod +x /app/run.sh

ENV OUTPUT_DIR=/data/tgerdn
ENV INTERVAL=1
ENV HOUR="*"

CMD ["/app/run.sh"]
