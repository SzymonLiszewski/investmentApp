from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def updateTransactions(request):
    return JsonResponse({'status': 'OK'})


@api_view(['POST'])
@permission_classes([AllowAny])
def xtbLogin(request):
    return JsonResponse({'status': False, 'deprecated': True})
