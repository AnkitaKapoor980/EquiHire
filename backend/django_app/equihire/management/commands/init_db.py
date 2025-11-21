"""
Django management command to initialize database with pgvector extension.
"""
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Initialize database with pgvector extension'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                self.stdout.write(
                    self.style.SUCCESS('Successfully created pgvector extension')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'Extension may already exist: {str(e)}')
                )

