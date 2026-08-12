FROM python:3.12-slim

WORKDIR /opt/sandbox-agent
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY agent ./agent

ENV PYTHONUNBUFFERED=1
CMD ["python", "-m", "agent"]
