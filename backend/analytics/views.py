from django.shortcuts import render, get_object_or_404
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from utils.dataFetcher import getStockPrice, getFundamentalAnalysis, getBasicStockInfo
from analytics.predictions import linear_regression_predict
from analytics.technical_indicators import get_technical_indicators
from analytics.portfolioAnalysis import calculateProfit, calculateIndicators
from utils.economicCalendar import getEarnings, getIPO
from rest_framework.permissions import IsAuthenticated, AllowAny
from api.models import Transactions, UserStock
from django.http import JsonResponse
from utils.xtb_integration import getTransactions_xtb
from api.serializers import TransactionSerializer
# Create your views here.

#* Analysis views


@api_view(['GET'])
@permission_classes([AllowAny])
def stockDataView(request, ticker):
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    data = getStockPrice(ticker, start_date, end_date)
    return Response(data)


@api_view(['GET'])
@permission_classes([AllowAny])
def predictView(request, ticker):
    start_date = request.GET.get('start')
    end_date = request.GET.get('end')
    prediction = linear_regression_predict(ticker, start_date, end_date)
    return Response(prediction)

@api_view(['GET'])
@permission_classes([AllowAny])
def fundamentalAnalysisView(request, ticker):
    data = getFundamentalAnalysis(ticker)
    return Response(data)

@api_view(['GET'])
@permission_classes([AllowAny])
def basicInfoView(request, ticker):
    data = getBasicStockInfo(ticker)
    return Response(data)

@api_view(['GET'])
@permission_classes([AllowAny])
def technicalAnalysisView(request, ticker):
    data = get_technical_indicators(ticker)
    return Response(data)

#* Calendar views

@api_view(['GET'])
@permission_classes([AllowAny])
def CalendarEarningsView(request):
    data = getEarnings()
    return Response(data)

@api_view(['GET'])
@permission_classes([AllowAny])
def CalendarIPOView(request):
    data = getIPO()
    return Response(data)

#* portfolio analysis views

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def profitView(request):
    userTransactions = Transactions.objects.filter(owner = request.user)
    userId = request.headers.get("userId")
    password = request.headers.get("password")
    profit, benchmark = calculateProfit(userTransactions, userId, password)
    sharpe, sortino, alpha = calculateIndicators(profit, benchmark)
    profit = profit.to_json(orient='index')
    return JsonResponse({'calculated_data': profit, 'sharpe': sharpe, 'sortino': sortino, 'alpha': alpha})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def updateTransactions(request):
    userId = request.headers.get("userId")
    password = request.headers.get("password")
    xtb_transactions = getTransactions_xtb(userId, password)
    if xtb_transactions!=None:
        for i in xtb_transactions:
            if i != {}:
                #* add transaction if it does not exists in database
                isTransactionCreated = Transactions.objects.filter(external_id=i['order']).first()
                if isTransactionCreated==None:
                    serializer = TransactionSerializer(data={'product': i['symbol'], 'transactionType': "B", 'quantity': i['volume'], 'price': i['open_price'], 'date': i['date'], 'external_id': i['order']})
                    if serializer.is_valid():
                        transaction = serializer.save(owner=request.user)
                        #* if USER_STOCK does not exits in db create new object, otherwise add value of owned shares
                        user_product, created = UserStock.objects.get_or_create(
                            owner=transaction.owner,
                            ownedStock=transaction.product
                        )
                        if created:
                            user_product.quantity = transaction.quantity
                        else:
                            user_product.quantity += transaction.quantity
                        user_product.save()
                    else:
                        print(serializer.errors)
    return JsonResponse({'status': 'OK'})