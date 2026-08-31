FROM python:3.12-alpine

WORKDIR /app
COPY server.py .

RUN mkdir -p /data
VOLUME ["/data"]

EXPOSE 80
CMD ["python", "server.py"]
