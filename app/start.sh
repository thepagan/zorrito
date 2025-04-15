#!/bin/bash

# Ensure zorrito.log is a regular file, not a directory
if [ -d /app/zorrito.log ]; then
  echo "Removing directory named zorrito.log..."
  rm -rf /app/zorrito.log
fi

# Create zorrito.log if it doesn't exist
touch /app/zorrito.log

# Ensure logrotate state directory exists
mkdir -p /var/lib/logrotate

# Create a basic logrotate config
cat <<EOF > /etc/logrotate.d/zorrito
/app/zorrito.log {
    daily
    rotate 7
    missingok
    notifempty
    compress
    delaycompress
    copytruncate
}
EOF

# Run logrotate in the background every 24 hours
(while true; do logrotate -s /var/lib/logrotate/status /etc/logrotate.d/zorrito; sleep 86400; done) &

# Start the Flask app
echo "Starting Zorrito Flask app..."
exec python3 main.py
