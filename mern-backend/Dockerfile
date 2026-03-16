# Start with a solid Linux base
FROM ubuntu:22.04

# Prevent interactive popups during installation
ENV DEBIAN_FRONTEND=noninteractive

# Install standard Python, pip, and Git
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# 👇 FIX 1: Upgraded Node.js to Version 22 to fix EBADENGINE warning
RUN curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
RUN apt-get install -y nodejs

# Set up the working directory
WORKDIR /app

# Copy your entire backend code into the container
COPY . .

# Install Node dependencies
RUN npm install

# 👇 FIX 2: Removed the broken flag from pip3 install
RUN pip3 install -r requirements.txt

# Expose the port
EXPOSE 5000

# Start the Titan Engine
CMD ["node", "server.js"]