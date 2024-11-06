from celery import Celery
import os


# Use the name of the RabbitMQ container as the hostname.
broker_url = os.getenv("CELERY_BROKER_URL", "pyamqp://guest@rabbitmq//")
app = Celery("src/ej/", broker=broker_url)
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()
