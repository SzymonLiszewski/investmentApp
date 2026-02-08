"""
Sentiment analysis service.
"""
from django.conf import settings

_sentiment_classifier = None


def _get_sentiment_classifier():
    """Lazy-load the sentiment pipeline only when ENABLE_ML_FUNCTIONS is True."""
    global _sentiment_classifier
    if _sentiment_classifier is None:
        from transformers import pipeline
        _sentiment_classifier = pipeline('sentiment-analysis')
    return _sentiment_classifier


def analyze_sentiment(data):
    """
    Analyze sentiment of news articles.

    Args:
        data: List of dicts, each containing at least a 'title' key.

    Returns:
        Average sentiment score (float). Positive = positive sentiment.
    """
    if not getattr(settings, 'ENABLE_ML_FUNCTIONS', False) or not data:
        return 0.0
    classifier = _get_sentiment_classifier()
    score = 0
    for item in data:
        sentiment = classifier(item['title'])
        if sentiment[0]['label'] == 'POSITIVE':
            score += sentiment[0]['score']
        elif sentiment[0]['label'] == 'NEGATIVE':
            score -= sentiment[0]['score']
    return score / len(data)
