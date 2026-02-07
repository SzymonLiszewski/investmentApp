import feedparser
from newsdataapi import NewsDataApiClient
from decouple import config
from django.conf import settings

API_KEY = config('NEWSDATA_API_KEY', default="default_api_key")

_sentiment_classifier = None


def _get_sentiment_classifier():
    """Lazy-load the sentiment pipeline only when ENABLE_ML_FUNCTIONS is True."""
    global _sentiment_classifier
    if _sentiment_classifier is None:
        from transformers import pipeline
        _sentiment_classifier = pipeline('sentiment-analysis')
    return _sentiment_classifier

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
    if not getattr(settings, 'ENABLE_ML_FUNCTIONS', False) or not data:
        return 0.0
    classifier = _get_sentiment_classifier()
    score = 0
    for i in data:
        sentiment = classifier(i['title'])
        if sentiment[0]['label'] == 'POSITIVE':
            score += sentiment[0]['score']
        elif sentiment[0]['label'] == 'NEGATIVE':
            score -= sentiment[0]['score']
    return score / len(data)

def getAllNews(_query, _count):
    news = []
    yahooNews = get_yahoo_finance_news(_query, _count)
    newsdataNews = get_newsdata_news(_query, count=_count)
    news = news + yahooNews
    news = news + newsdataNews
    sentiment = analize_sentiment(news)
    return {"sentiment": sentiment ,"news":news}