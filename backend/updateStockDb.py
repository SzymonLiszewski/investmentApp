
import json
import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')


django.setup()
file_path = os.path.join(settings.STATIC_ROOT, 'xtbSymbols.json')
from api.serializers import StockSerializer
def updateFromXTB():
    with open(file_path, 'r') as file:
        data = json.load(file)
        for i in data:
            serializer = StockSerializer(data={'ticker':i['symbol'], 'companyName': i['description'], 'sector':'NULL', 'industry':'NULL'})
            if serializer.is_valid():
                serializer.save()
                #print("added: ", i['symbol'])
            else:
                print(serializer.errors)
    print("succes")

if __name__ == "__main__":
    updateFromXTB()
