FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn
COPY . .

# Install logrotate and bash
RUN apt-get update && apt-get install -y logrotate bash vim postgresql-client && rm -rf /var/lib/apt/lists/*

# Make sure start.sh is executable
RUN chmod +x /app/start.sh

# Use start.sh to run the app with logging and logrotate
CMD ["./start.sh"]
