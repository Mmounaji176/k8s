python3 /app/Backend/worker_supervisor.py &
celery -A Backend.healthCheck beat &
python3 manage.py makemigrations Api &&
python3 manage.py migrate Api &&
python3 manage.py migrate &&
(sleep 15 && python3 manage.py load_roles &&
python3 manage.py createsuperuser --noinput || echo "already exist") &
python3 manage.py runserver 0.0.0.0:9898