"""
Tests for analytics views.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, Mock
from decimal import Decimal
from api.models import Asset, UserAsset


class TestGetUserAssetComposition(TestCase):
    """Test the getUserAssetComposition endpoint."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()
        
        # Create a test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test assets
        self.stock1 = Asset.objects.create(
            symbol='AAPL',
            name='Apple Inc.',
            asset_type='stocks'
        )
        self.stock2 = Asset.objects.create(
            symbol='GOOGL',
            name='Alphabet Inc.',
            asset_type='stocks'
        )
        
        # Create user assets
        self.user_asset1 = UserAsset.objects.create(
            owner=self.user,
            ownedAsset=self.stock1,
            quantity=10
        )
        self.user_asset2 = UserAsset.objects.create(
            owner=self.user,
            ownedAsset=self.stock2,
            quantity=5
        )

    def test_get_composition_requires_authentication(self):
        """Test that endpoint requires authentication."""
        response = self.client.get('/api/analytics/portfolio/composition/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('analytics.services.data_fetchers.yf.Ticker')
    def test_get_composition_with_custom_currency(self, mock_ticker):
        """Test getting portfolio composition with custom currency."""
        # Mock yfinance responses
        def mock_ticker_side_effect(symbol):
            mock_instance = Mock()
            mock_instance.info = {'currentPrice': 150.00, 'currency': 'USD'}
            return mock_instance

        mock_ticker.side_effect = mock_ticker_side_effect
        
        # Authenticate
        self.client.force_authenticate(user=self.user)
        
        # Make request with USD currency
        response = self.client.get('/api/analytics/portfolio/composition/?currency=USD')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['currency'], 'USD')

    @patch('analytics.services.data_fetchers.yf.Ticker')
    def test_get_composition_validates_assets(self, mock_ticker):
        """Test that composition includes correct assets."""
        # Mock yfinance responses
        def mock_ticker_side_effect(symbol):
            mock_instance = Mock()
            if symbol == 'AAPL':
                mock_instance.info = {'currentPrice': 150.00, 'currency': 'USD'}
            elif symbol == 'GOOGL':
                mock_instance.info = {'currentPrice': 100.00, 'currency': 'USD'}
            return mock_instance

        mock_ticker.side_effect = mock_ticker_side_effect
        
        # Authenticate
        self.client.force_authenticate(user=self.user)
        
        # Make request
        response = self.client.get('/api/analytics/portfolio/composition/?currency=USD')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['assets']), 2)
        
        # Check that assets have required fields
        for asset in response.data['assets']:
            self.assertIn('id', asset)
            self.assertIn('symbol', asset)
            self.assertIn('name', asset)
            self.assertIn('asset_type', asset)
            self.assertIn('quantity', asset)
            self.assertIn('current_value', asset)
