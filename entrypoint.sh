# Apply database migrations
python manage.py makemigrations --no-input
python manage.py migrate --no-input

# Collect static files
python manage.py collectstatic --no-input --clear

# Start server
daphne -b 0.0.0.0 -p 8000 project.asgi:application
