#!/bin/bash

export PYTHONPATH=$(pwd)/src

# Execute celery beat em segundo plano
celery -A ej_clusters beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler &

# Execute celery worker em segundo plano
celery -A ej_clusters worker -l INFO &

# Aguarde ambos os processos terminarem
wait