"""Management command to reprocess applications with ML services."""
from django.core.management.base import BaseCommand
from jobs.models import Application
from jobs.services import process_application
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Reprocess applications to generate scores, fairness metrics, and explanations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Process all applications (default: only those without scores)',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Limit number of applications to process (default: 100)',
        )

    def handle(self, *args, **options):
        if options['all']:
            applications = Application.objects.all()[:options['limit']]
        else:
            applications = Application.objects.filter(score__isnull=True)[:options['limit']]
        
        total = applications.count()
        self.stdout.write(f'Processing {total} application(s)...')
        
        processed = 0
        for application in applications:
            try:
                process_application(application)
                processed += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Processed application {application.id}')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to process application {application.id}: {str(e)}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\nSuccessfully processed {processed}/{total} applications')
        )

