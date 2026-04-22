from django.core.management.base import BaseCommand
from ml_models.trainer import get_trainer

class Command(BaseCommand):
    help = 'Retrain the Recommendation Model artifacts'

    def handle(self, *args, **options):
        self.stdout.write("Fetching training data from database...")
        trainer = get_trainer()

        try:
            self.stdout.write("Running training pipeline...")
            success = trainer.run_full_training()
            if success:
                self.stdout.write(self.style.SUCCESS('Successfully retrained model artifacts!'))
            else:
                self.stdout.write(self.style.ERROR('Training failed to complete.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {str(e)}'))