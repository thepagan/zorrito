#!/bin/bash
set -e
# Requires DATABASE_URL env variable and optional RESET_DB=true to reinitialize the DB

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

echo "Waiting for database to be ready..."
until pg_isready -h db -p 5432 -U zorrito; do
  sleep 1
done

echo "Running any .sql files in /app/sql/ (if mounted)..."
for file in /app/sql/*.sql; do
  if [ -f "$file" ]; then
    echo "Executing $file"
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$file"
  fi
done

echo "Checking if tables exist..."
TABLES_EXIST=$(psql "$DATABASE_URL" -tAc "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_name IN ('\"user\"', 'county');")
if [ "$TABLES_EXIST" -lt 2 ]; then
  echo "Tables not found. Running all SQL files in /app/sql..."
  for file in /app/sql/*.sql; do
    echo "Executing $file"
    psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$file"
  done
else
  echo "✅ Tables already exist. Skipping SQL bootstrap."
fi

# Start the Flask app with Gunicorn
echo "Starting Zorrito Flask app..."
exec gunicorn -w 4 -b 0.0.0.0:8181 main:app
