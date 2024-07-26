import csv
import requests
from decouple import config

API_KEY = config('ALPHAVANTAGE_API_KEY')

def getEarnings():
    CSV_URL = f'https://www.alphavantage.co/query?function=EARNINGS_CALENDAR&horizon=3month&apikey={API_KEY}'
    with requests.Session() as s:
        download = s.get(CSV_URL)
        decoded_content = download.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        my_list = list(cr)
        return my_list[1:]

def getIPO():
    CSV_URL = f'https://www.alphavantage.co/query?function=IPO_CALENDAR&apikey={API_KEY}'
    with requests.Session() as s:
        download = s.get(CSV_URL)
        decoded_content = download.content.decode('utf-8')
        cr = csv.reader(decoded_content.splitlines(), delimiter=',')
        my_list = list(cr)
        return my_list[1:]