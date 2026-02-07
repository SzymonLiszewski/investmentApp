"""
Tests for analytics views.
"""
from datetime import date
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, Mock
from decimal import Decimal
from api.models import Asset, UserAsset
from analytics.models import PortfolioSnapshot


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


class TestValueHistoryEndpoint(TestCase):
    """Tests for the portfolio value-history endpoint."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="histuser", email="hist@test.com", password="pass",
        )

        PortfolioSnapshot.objects.create(
            user=self.user,
            date=date(2026, 1, 1),
            currency="PLN",
            total_value=Decimal("10000.00"),
        )
        PortfolioSnapshot.objects.create(
            user=self.user,
            date=date(2026, 1, 2),
            currency="PLN",
            total_value=Decimal("10500.00"),
        )
        PortfolioSnapshot.objects.create(
            user=self.user,
            date=date(2026, 1, 3),
            currency="PLN",
            total_value=Decimal("10200.00"),
        )

    def test_requires_authentication(self):
        response = self.client.get("/api/analytics/portfolio/value-history/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_returns_snapshots_in_range(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            "/api/analytics/portfolio/value-history/",
            {"start_date": "2026-01-01", "end_date": "2026-01-03", "currency": "PLN"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        self.assertEqual(len(data), 3)
        self.assertEqual(data[0]["date"], "2026-01-01")
        self.assertAlmostEqual(data[0]["total_value"], 10000.0)
        self.assertEqual(data[2]["date"], "2026-01-03")

    def test_filters_by_date_range(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            "/api/analytics/portfolio/value-history/",
            {"start_date": "2026-01-02", "end_date": "2026-01-02", "currency": "PLN"},
        )
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["date"], "2026-01-02")

    def test_filters_by_currency(self):
        self.client.force_authenticate(user=self.user)
        # No snapshots in USD
        response = self.client.get(
            "/api/analytics/portfolio/value-history/",
            {"start_date": "2026-01-01", "end_date": "2026-01-03", "currency": "USD"},
        )
        data = response.json()
        self.assertEqual(len(data), 0)

    def test_invalid_date_format_returns_400(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            "/api/analytics/portfolio/value-history/",
            {"start_date": "not-a-date"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_correct_fields(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(
            "/api/analytics/portfolio/value-history/",
            {"start_date": "2026-01-01", "end_date": "2026-01-01", "currency": "PLN"},
        )
        data = response.json()
        self.assertEqual(len(data), 1)
        entry = data[0]
        self.assertIn("date", entry)
        self.assertIn("total_value", entry)
        self.assertIn("currency", entry)
        self.assertEqual(entry["currency"], "PLN")
