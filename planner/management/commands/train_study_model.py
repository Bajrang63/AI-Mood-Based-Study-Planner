from django.core.management.base import BaseCommand
from planner.ml_model import train_model
class Command(BaseCommand):
    help='Train the optional synthetic-data study intensity model.'
    def handle(self,*args,**options):
        _, accuracy=train_model()
        self.stdout.write(f'Synthetic holdout accuracy: {accuracy}. This does not measure study effectiveness.')
