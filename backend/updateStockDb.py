import json
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

django.setup()
from api.serializers import AssetSerializer
from api.models import Asset

def updateFromXTB():
    file_path = os.path.join(settings.STATIC_ROOT, 'xtbSymbols.json')
    with open(file_path, 'r') as file:
        data = json.load(file)
        for i in data:
            serializer = AssetSerializer(data={'symbol':i['symbol'], 'name': i['description'], 'asset_type':'stocks'})
            if serializer.is_valid():
                serializer.save()
                #print("added: ", i['symbol'])
            else:
                print(serializer.errors)
    print("succes")

def populateMajorStocks():
    file_path = os.path.join(settings.STATIC_ROOT, 'majorStocks.json')
    with open(file_path, 'r') as file:
        data = json.load(file)
        added_count = 0
        skipped_count = 0
        
        for item in data:
            # Check if asset already exists
            existing_asset = Asset.objects.filter(symbol=item['symbol']).first()
            if existing_asset:
                print(f"Skipped (already exists): {item['symbol']} - {item['name']}")
                skipped_count += 1
                continue
            
            serializer = AssetSerializer(data={
                'symbol': item['symbol'], 
                'name': item['name'], 
                'asset_type': 'stocks'
            })
            if serializer.is_valid():
                serializer.save()
                print(f"Added: {item['symbol']} - {item['name']}")
                added_count += 1
            else:
                print(f"Error adding {item['symbol']}: {serializer.errors}")
        
        print(f"\nSuccessfully populated assets table: {added_count} added, {skipped_count} skipped")

if __name__ == "__main__":
    #updateFromXTB()
    populateMajorStocks()
