from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view
from utils.dataFetcher import getStockPrice, getFundamentalAnalysis, getBasicStockInfo
from analytics.predictions import linear_regression_predict
from analytics.technical_indicators import get_technical_indicators
from analytics.portfolioAnalysis import calculateProfit, calculateIndicators
from utils.economicCalendar import getEarnings, getIPO
from django.contrib.auth.decorators import login_required
from api.models import Transactions
# Create your views here.

#* Analysis views

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

@api_view(['GET'])
def technicalAnalysisView(request, ticker):
    data = get_technical_indicators(ticker)
    return Response(data)

#* Calendar views

@api_view(['GET'])
def CalendarEarningsView(request):
    data = getEarnings()
    return Response(data)

@api_view(['GET'])
def CalendarIPOView(request):
    data = getIPO()
    return Response(data)

#* portfolio analysis views

@login_required
def profitView(request):
    userTransactions = get_object_or_404(Transactions, owner = request.user)
    profit = calculateProfit(userTransactions) #! or profit = calculateProfit(userTransactions.eg)
    return profit