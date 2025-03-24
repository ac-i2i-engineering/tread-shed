from celery import shared_task
from django.core.management import call_command


@shared_task
def initiate_hub_workflow():
    call_command("hub_workflow")


@shared_task
def initiate_daily_mammoth_workflow():
    call_command("daily_mammoth_workflow")


@shared_task
def remove_old_events():
    call_command("remove_old_events")
