import os
import re
from django.core.management.base import BaseCommand
from api.models import Asset
from api.serializers import AssetSerializer


class Command(BaseCommand):
    help = 'Seed database with Polish stocks and ETFs from stocks_pl.txt and ETF_pl.txt files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--etf-only',
            action='store_true',
            help='Only seed ETFs from ETF_pl.txt',
        )
        parser.add_argument(
            '--stocks-only',
            action='store_true',
            help='Only seed stocks from stocks_pl.txt',
        )

    def parse_line(self, line):
        """
        Parse a line from the Polish stocks/ETF files.
        Format: Ticker    yfinance Ticker    Name
        Returns: (yfinance_ticker, name) or None if invalid
        """
        line = line.strip()
        if not line:
            return None
        
        # Split by multiple spaces and filter out empty strings
        parts = [p for p in re.split(r'\s{2,}', line) if p]
        
        # Should have at least 3 parts: Ticker, yfinance Ticker, Name
        if len(parts) < 3:
            return None
        
        yfinance_ticker = parts[1].strip()
        # Name might be split across multiple parts if it contains spaces
        name = ' '.join(parts[2:]).strip()
        
        if not yfinance_ticker or not name:
            return None
        
        return (yfinance_ticker, name)

    def process_file(self, file_path, file_type='stocks'):
        """
        Process a single file and add assets to the database.
        file_type: 'stocks' or 'etf' (for logging purposes)
        """
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
            return 0, 0, 0
        
        added_count = 0
        skipped_count = 0
        error_count = 0
        
        self.stdout.write(self.style.SUCCESS(f'Reading file: {file_path}'))
        
        with open(file_path, 'r', encoding='utf-8') as file:
            # Skip header line
            next(file, None)
            # Skip separator line
            next(file, None)
            
            for line_num, line in enumerate(file, start=3):
                parsed = self.parse_line(line)
                
                if not parsed:
                    if line.strip():  # Only warn if line is not empty
                        self.stdout.write(self.style.WARNING(
                            f'Line {line_num}: Invalid format, skipping'
                        ))
                        error_count += 1
                    continue
                
                yfinance_ticker, name = parsed
                
                # Check if asset already exists
                existing_asset = Asset.objects.filter(symbol=yfinance_ticker).first()
                if existing_asset:
                    skipped_count += 1
                    if self.verbosity >= 2:
                        self.stdout.write(
                            f'Skipped (already exists): {yfinance_ticker} - {name}'
                        )
                    continue
                
                # Create asset using serializer
                serializer = AssetSerializer(data={
                    'symbol': yfinance_ticker,
                    'name': name,
                    'asset_type': 'stocks'  # ETFs are treated as stocks in this model
                })
                
                if serializer.is_valid():
                    serializer.save()
                    added_count += 1
                    if self.verbosity >= 2:
                        asset_label = f' ({file_type.upper()})' if file_type == 'etf' else ''
                        self.stdout.write(
                            f'Added: {yfinance_ticker} - {name}{asset_label}'
                        )
                else:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(
                        f'Error adding {yfinance_ticker}: {serializer.errors}'
                    ))
        
        return added_count, skipped_count, error_count

    def handle(self, *args, **options):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, 'data')
        
        stocks_file = os.path.join(data_dir, 'stocks_pl.txt')
        etf_file = os.path.join(data_dir, 'ETF_pl.txt')
        
        self.verbosity = options.get('verbosity', 1)
        
        total_added = 0
        total_skipped = 0
        total_errors = 0
        
        # Process stocks file
        if not options.get('etf_only', False):
            self.stdout.write(self.style.SUCCESS('\n=== Processing Polish Stocks ==='))
            added, skipped, errors = self.process_file(stocks_file, 'stocks')
            total_added += added
            total_skipped += skipped
            total_errors += errors
        
        # Process ETF file
        if not options.get('stocks_only', False):
            self.stdout.write(self.style.SUCCESS('\n=== Processing Polish ETFs ==='))
            added, skipped, errors = self.process_file(etf_file, 'etf')
            total_added += added
            total_skipped += skipped
            total_errors += errors
        
        # Summary
        self.stdout.write(self.style.SUCCESS(
            f'\n=== Summary ===\n'
            f'Added: {total_added}\n'
            f'Skipped (already exists): {total_skipped}\n'
            f'Errors: {total_errors}\n'
            f'Total processed: {total_added + total_skipped + total_errors}'
        ))
