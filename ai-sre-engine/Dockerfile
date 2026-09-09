FROM python:3.11-slim
WORKDIR /app
RUN mkdir -p /app/healer-workspace/repo-to-heal
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY healeragent.py .
ENTRYPOINT ["python", "healeragent.py", "REPO", "/app/healer-workspace/repo-to-heal"]