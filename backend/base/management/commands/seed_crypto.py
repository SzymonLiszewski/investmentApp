import os
import json
from django.core.management.base import BaseCommand
from base.models import Asset
from base.serializers import AssetSerializer


class Command(BaseCommand):
    help = 'Seed database with popular cryptocurrency pairs from cryptocurrencies.json'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing cryptocurrencies if they exist',
        )

    def handle(self, *args, **options):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, 'data')
        file_path = os.path.join(data_dir, 'cryptocurrencies.json')

        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        self.stdout.write(self.style.SUCCESS(f'Reading file: {file_path}'))

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except json.JSONDecodeError as e:
            self.stdout.write(self.style.ERROR(f'Error parsing JSON: {str(e)}'))
            return

        if not isinstance(data, list):
            self.stdout.write(self.style.ERROR('JSON must be a list of { "symbol", "name" } objects'))
            return

        added_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0

        for item in data:
            try:
                symbol = item.get('symbol', '').strip()
                name = item.get('name', '').strip() or symbol

                if not symbol:
                    self.stdout.write(self.style.WARNING('Skipping entry with empty symbol'))
                    error_count += 1
                    continue

                asset_data = {
                    'symbol': symbol,
                    'name': name,
                    'asset_type': Asset.AssetType.CRYPTOCURRENCIES,
                }

                existing = Asset.objects.filter(
                    symbol=symbol,
                    asset_type=Asset.AssetType.CRYPTOCURRENCIES,
                ).first()

                if existing:
                    if options.get('update', False):
                        serializer = AssetSerializer(existing, data=asset_data, partial=True)
                        if serializer.is_valid():
                            serializer.save()
                            updated_count += 1
                            if self.verbosity >= 2:
                                self.stdout.write(f'Updated: {symbol}')
                        else:
                            error_count += 1
                            self.stdout.write(self.style.ERROR(f'Error updating {symbol}: {serializer.errors}'))
                    else:
                        skipped_count += 1
                        if self.verbosity >= 2:
                            self.stdout.write(f'Skipped (already exists): {symbol}')
                else:
                    serializer = AssetSerializer(data=asset_data)
                    if serializer.is_valid():
                        serializer.save()
                        added_count += 1
                        if self.verbosity >= 2:
                            self.stdout.write(f'Added: {symbol}')
                    else:
                        error_count += 1
                        self.stdout.write(self.style.ERROR(f'Error adding {symbol}: {serializer.errors}'))

            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'Error processing entry: {str(e)}'))

        self.stdout.write(self.style.SUCCESS(
            f'\n=== Summary ===\n'
            f'Added: {added_count}\n'
            f'Updated: {updated_count}\n'
            f'Skipped (already exists): {skipped_count}\n'
            f'Errors: {error_count}\n'
            f'Total processed: {added_count + updated_count + skipped_count + error_count}'
        ))
