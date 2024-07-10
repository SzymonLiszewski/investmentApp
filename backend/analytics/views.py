from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from utils.dataFetcher import getStockPrice, getFundamentalAnalysis, getBasicStockInfo
from analytics.predictions import linear_regression_predict

# Create your views here.

@api_view(['GET'])
def stockDataView(request, ticker):
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    data = getStockPrice(ticker, start_date, end_date)
    return Response(data)

@api_view(['GET'])
def predictView(request, ticker):
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    prediction = linear_regression_predict(ticker, start_date, end_date)
    return Response(prediction)

@api_view(['GET'])
def fundamentalAnalysisView(request, ticker):
    data = getFundamentalAnalysis(ticker)
    return Response(data)

@api_view(['GET'])
def basicInfoView(request, ticker):
    data = getBasicStockInfo(ticker)
    return Response(data)