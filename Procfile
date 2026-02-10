# Web process - runs Flask API and dashboard
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120

# Worker process - runs scheduled analysis (uncomment to enable)
# worker: python3 scheduler.py
