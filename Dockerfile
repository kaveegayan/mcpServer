FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir "mcp[cli]<2" httpx \
 && useradd -m app
COPY server.py .
USER app
EXPOSE 8001
CMD ["python", "server.py"]
