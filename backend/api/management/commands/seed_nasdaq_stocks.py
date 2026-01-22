import os
from django.core.management.base import BaseCommand
from api.models import Asset
from api.serializers import AssetSerializer


class Command(BaseCommand):
    help = 'Seed database with stocks and ETFs from stocks_nasdaq.txt file'

    def handle(self, *args, **options):

        # Path to the stocks file - relative to this script's directory
        script_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(script_dir, 'data', 'stocks_nasdaq.txt')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return

        added_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write(self.style.SUCCESS(f'Reading file: {file_path}'))

        with open(file_path, 'r', encoding='utf-8') as file:
            # Skip header line
            next(file)
            
            for line_num, line in enumerate(file, start=2):
                line = line.strip()
                if not line:
                    continue
                
                # Parse pipe-delimited line
                parts = line.split('|')
                
                if len(parts) < 8:
                    self.stdout.write(self.style.WARNING(f'Line {line_num}: Invalid format, skipping'))
                    error_count += 1
                    continue
                
                symbol = parts[0].strip()
                security_name = parts[1].strip()
                is_etf = parts[6].strip().upper() == 'Y'
                
                # Skip if symbol or name is empty
                if not symbol or not security_name:
                    self.stdout.write(self.style.WARNING(f'Line {line_num}: Empty symbol or name, skipping'))
                    error_count += 1
                    continue
                
                # Check if asset already exists
                existing_asset = Asset.objects.filter(symbol=symbol).first()
                if existing_asset:
                    skipped_count += 1
                    if options.get('verbosity', 1) >= 2:
                        self.stdout.write(f'Skipped (already exists): {symbol} - {security_name}')
                    continue
                
                # Determine asset type: ETF or stock
                asset_type = 'stocks'  # Default to stocks
                # Note: You might want to add an ETF asset type to your model if needed
                # For now, treating ETFs as stocks with symbol and name
                
                # Create asset using serializer
                serializer = AssetSerializer(data={
                    'symbol': symbol,
                    'name': security_name,
                    'asset_type': asset_type
                })
                
                if serializer.is_valid():
                    serializer.save()
                    added_count += 1
                    if options.get('verbosity', 1) >= 2:
                        etf_label = ' (ETF)' if is_etf else ''
                        self.stdout.write(f'Added: {symbol} - {security_name}{etf_label}')
                else:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(
                        f'Error adding {symbol}: {serializer.errors}'
                    ))
        
        # Summary
        self.stdout.write(self.style.SUCCESS(
            f'\n=== Summary ===\n'
            f'Added: {added_count}\n'
            f'Skipped (already exists): {skipped_count}\n'
            f'Errors: {error_count}\n'
            f'Total processed: {added_count + skipped_count + error_count}'
        ))
