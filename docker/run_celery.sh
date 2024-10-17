#!/bin/bash

export PYTHONPATH=$(pwd)/src

# Execute celery beat as a background task
celery -A ej beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler &

# Execute celery worker as a background task
celery -A ej worker -l INFO &

# Wait for both process to finish
wait