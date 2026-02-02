import os
import json
from datetime import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from api.models import Asset
from api.serializers import AssetSerializer


class Command(BaseCommand):
    help = 'Seed database with Polish Treasury Bonds from polish_treasury_bonds.json file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing bonds if they exist',
        )

    def handle(self, *args, **options):
        script_dir = os.path.dirname(os.path.abspath(__file__))
        data_dir = os.path.join(script_dir, 'data')
        file_path = os.path.join(data_dir, 'polish_treasury_bonds.json')
        
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
        
        for bond_type, bonds_list in data.items():
            self.stdout.write(self.style.SUCCESS(f'\nProcessing {bond_type} bonds...'))
            
            for bond_data in bonds_list:
                try:
                    series = bond_data.get('series', '')
                    name = bond_data.get('name', f'Obligacja {series}')
                    maturity_date_str = bond_data.get('maturity_date')
                    interest_rate_type = bond_data.get('interest_rate_type', 'fixed')
                    face_value = bond_data.get('face_value', 100)
                    
                    # Parse maturity date
                    maturity_date = None
                    if maturity_date_str:
                        try:
                            maturity_date = datetime.strptime(maturity_date_str, '%Y-%m-%d').date()
                        except ValueError:
                            self.stdout.write(self.style.WARNING(f'Invalid maturity_date format: {maturity_date_str}, skipping'))
                            error_count += 1
                            continue
                    
                    # Prepare asset data
                    asset_data = {
                        'name': name,
                        'asset_type': 'bonds',
                        'bond_type': bond_type,
                        'bond_series': series,
                        'maturity_date': maturity_date,
                        'interest_rate_type': interest_rate_type,
                        'face_value': Decimal(str(face_value)),
                    }
                    
                    # Add symbol if series exists
                    if series:
                        asset_data['symbol'] = series
                    
                    # Add interest rate fields based on type
                    if interest_rate_type == 'fixed':
                        interest_rate = bond_data.get('interest_rate')
                        if interest_rate is not None:
                            asset_data['interest_rate'] = Decimal(str(interest_rate))
                    elif interest_rate_type == 'variable_wibor':
                        wibor_margin = bond_data.get('wibor_margin')
                        if wibor_margin is not None:
                            asset_data['wibor_margin'] = Decimal(str(wibor_margin))
                    elif interest_rate_type == 'indexed_inflation':
                        base_rate = bond_data.get('base_interest_rate')
                        inflation_margin = bond_data.get('inflation_margin')
                        if base_rate is not None:
                            asset_data['base_interest_rate'] = Decimal(str(base_rate))
                        if inflation_margin is not None:
                            asset_data['inflation_margin'] = Decimal(str(inflation_margin))
                    
                    # Check if asset already exists (by symbol or name and bond_type)
                    existing = None
                    if series:
                        existing = Asset.objects.filter(symbol=series, asset_type='bonds').first()
                    if not existing:
                        existing = Asset.objects.filter(
                            name=name,
                            asset_type='bonds',
                            bond_type=bond_type
                        ).first()
                    
                    if existing:
                        if options.get('update', False):
                            # Update existing asset
                            serializer = AssetSerializer(existing, data=asset_data, partial=True)
                            if serializer.is_valid():
                                serializer.save()
                                updated_count += 1
                                if self.verbosity >= 2:
                                    self.stdout.write(f'Updated: {series or name}')
                            else:
                                error_count += 1
                                self.stdout.write(self.style.ERROR(f'Error updating {series or name}: {serializer.errors}'))
                        else:
                            skipped_count += 1
                            if self.verbosity >= 2:
                                self.stdout.write(f'Skipped (already exists): {series or name}')
                    else:
                        # Create new asset
                        serializer = AssetSerializer(data=asset_data)
                        if serializer.is_valid():
                            serializer.save()
                            added_count += 1
                            if self.verbosity >= 2:
                                self.stdout.write(f'Added: {series or name}')
                        else:
                            error_count += 1
                            self.stdout.write(self.style.ERROR(f'Error adding {series or name}: {serializer.errors}'))
                            
                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'Error processing bond: {str(e)}'))
        
        # Summary
        self.stdout.write(self.style.SUCCESS(
            f'\n=== Summary ===\n'
            f'Added: {added_count}\n'
            f'Updated: {updated_count}\n'
            f'Skipped (already exists): {skipped_count}\n'
            f'Errors: {error_count}\n'
            f'Total processed: {added_count + updated_count + skipped_count + error_count}'
        ))
