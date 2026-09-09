# 1. Use an official, lightweight Python runtime
FROM python:3.11-slim

# 2. Set the working directory IN THE CONTAINER
WORKDIR /app

# 3. Create the workspace folder so the AI doesn't crash looking for it
RUN mkdir -p /app/healer-workspace/repo-to-heal

# 4. Copy your requirements and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5. Copy your AI script into the container
COPY healeragent.py .

# 6. How to run the script when the container starts
ENTRYPOINT ["python", "healeragent.py", "REPO", "/app/healer-workspace/repo-to-heal"]