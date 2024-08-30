import feedparser
from newsdataapi import NewsDataApiClient
from transformers import pipeline

classifier = pipeline('sentiment-analysis')

from decouple import config

API_KEY = config('NEWSDATA_API_KEY')

def get_yahoo_finance_news(query, count=5):
    rss_url = f"https://finance.yahoo.com/rss/headline?s={query}"
    feed = feedparser.parse(rss_url)

    news = []
    for entry in feed.entries[:count]:
        title = entry.title
        link = entry.link
        summary = entry.summary if hasattr(entry, 'summary') else "No summary available."
        news.append({'title': title, 'link': link, 'summary': summary})

    return news

def get_newsdata_news(query, count=5, language="en"):
    api = NewsDataApiClient(apikey=API_KEY)
    response = api.news_api( q= query , language = "en")
    return response['results'][0:count]

def analize_sentiment(data):
    score = 0
    print(data)
    for i in data:
        sentiment = classifier(i['title'])
        if sentiment[0]['label']=='POSITIVE':
            score+=sentiment[0]['score']
        elif sentiment[0]['label']=='NEGATIVE':
            score-=sentiment[0]['score']
    score = score/len(data)
    return score

def getAllNews(_query, _count):
    news = []
    yahooNews = get_yahoo_finance_news(_query, _count)
    newsdataNews = get_newsdata_news(_query, count=_count)
    news = news + yahooNews
    news = news + newsdataNews
    print("news: ", news)
    sentiment = analize_sentiment(news)
    return {"sentiment": sentiment ,"news":news}