from django.core.management.base import BaseCommand
from tgbot import Bot

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        Bot()