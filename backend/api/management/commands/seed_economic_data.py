import os
import json
from datetime import datetime
from django.core.management.base import BaseCommand
from analytics.models import EconomicData
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed database with economic data (WIBOR rates and inflation) from economic_data.json file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing records if they exist',
        )

    def handle(self, *args, **options):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, 'data')
        file_path = os.path.join(data_dir, 'economic_data.json')
        
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
        
        added_count = 0
        updated_count = 0
        skipped_count = 0
        error_count = 0
        
        for item in data:
            try:
                date_str = item.get('date')
                if not date_str:
                    self.stdout.write(self.style.WARNING(f'Missing date field, skipping'))
                    error_count += 1
                    continue
                
                # Parse date
                try:
                    date = datetime.strptime(date_str, '%Y-%m-%d').date()
                except ValueError:
                    self.stdout.write(self.style.WARNING(f'Invalid date format: {date_str}, skipping'))
                    error_count += 1
                    continue
                
                # Get economic data values
                wibor_3m = item.get('wibor_3m')
                wibor_6m = item.get('wibor_6m')
                inflation_cpi = item.get('inflation_cpi')
                
                if wibor_3m is None or wibor_6m is None or inflation_cpi is None:
                    self.stdout.write(self.style.WARNING(f'Missing required fields for date {date_str}, skipping'))
                    error_count += 1
                    continue
                
                # Convert to Decimal
                try:
                    wibor_3m = Decimal(str(wibor_3m))
                    wibor_6m = Decimal(str(wibor_6m))
                    inflation_cpi = Decimal(str(inflation_cpi))
                except (ValueError, TypeError) as e:
                    self.stdout.write(self.style.WARNING(f'Invalid numeric values for date {date_str}: {str(e)}, skipping'))
                    error_count += 1
                    continue
                
                # Check if record exists
                existing = EconomicData.objects.filter(date=date).first()
                
                if existing:
                    if options.get('update', False):
                        existing.wibor_3m = wibor_3m
                        existing.wibor_6m = wibor_6m
                        existing.inflation_cpi = inflation_cpi
                        existing.save()
                        updated_count += 1
                        if self.verbosity >= 2:
                            self.stdout.write(f'Updated: {date_str}')
                    else:
                        skipped_count += 1
                        if self.verbosity >= 2:
                            self.stdout.write(f'Skipped (already exists): {date_str}')
                else:
                    EconomicData.objects.create(
                        date=date,
                        wibor_3m=wibor_3m,
                        wibor_6m=wibor_6m,
                        inflation_cpi=inflation_cpi
                    )
                    added_count += 1
                    if self.verbosity >= 2:
                        self.stdout.write(f'Added: {date_str}')
                        
            except Exception as e:
                error_count += 1
                self.stdout.write(self.style.ERROR(f'Error processing item: {str(e)}'))
        
        # Summary
        self.stdout.write(self.style.SUCCESS(
            f'\n=== Summary ===\n'
            f'Added: {added_count}\n'
            f'Updated: {updated_count}\n'
            f'Skipped (already exists): {skipped_count}\n'
            f'Errors: {error_count}\n'
            f'Total processed: {added_count + updated_count + skipped_count + error_count}'
        ))
