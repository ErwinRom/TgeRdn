FROM python:3.12-slim

ARG BUILD_ARCH=amd64

LABEL io.hass.type="app" \
      io.hass.version="1.0.4" \
      io.hass.arch="${BUILD_ARCH}"

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY scraper.py scheduler.py run.sh ./
RUN chmod +x /app/run.sh

CMD ["/app/run.sh"]