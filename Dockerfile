# Base image
FROM python:3.12-slim

# Set working directory inside the container
WORKDIR /app

# Install system packages including bash and SSH
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    build-essential \
    bash \
    openssh-server \
    && rm -rf /var/lib/apt/lists/*

# Set up SSH
RUN mkdir /var/run/sshd && echo 'root:root' | chpasswd

# Copy requirements and install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your full app
COPY . .

# Expose FastAPI and SSH ports
EXPOSE 8000 22

# Start both SSH and FastAPI
CMD ["bash", "-c", "service ssh start && uvicorn server.server:app --host 0.0.0.0 --port 8000"]
