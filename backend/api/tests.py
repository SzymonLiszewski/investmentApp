from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status
from django.urls import reverse
from .models import Asset


class SearchAssetsTestCase(TestCase):
    """Test cases for the searchAssets endpoint."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        self.url = reverse('search_assets')
        
        # Create test assets
        Asset.objects.create(
            symbol='AAPL',
            name='Apple Inc.',
            asset_type=Asset.AssetType.STOCKS
        )
        Asset.objects.create(
            symbol='MSFT',
            name='Microsoft Corporation',
            asset_type=Asset.AssetType.STOCKS
        )
        Asset.objects.create(
            symbol='GOOGL',
            name='Alphabet Inc.',
            asset_type=Asset.AssetType.STOCKS
        )
        Asset.objects.create(
            symbol='TSLA',
            name='Tesla Inc.',
            asset_type=Asset.AssetType.STOCKS
        )
        Asset.objects.create(
            symbol='BOND001',
            name='US Treasury Bond 10Y',
            asset_type=Asset.AssetType.BONDS
        )
        Asset.objects.create(
            symbol='BTC',
            name='Bitcoin',
            asset_type=Asset.AssetType.CRYPTOCURRENCIES
        )
        Asset.objects.create(
            symbol='ETH',
            name='Ethereum',
            asset_type=Asset.AssetType.CRYPTOCURRENCIES
        )
    
    def test_search_by_symbol_exact_match(self):
        """Test searching by exact symbol match."""
        response = self.client.get(self.url, {'q': 'AAPL'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['symbol'], 'AAPL')
        self.assertEqual(response.data[0]['name'], 'Apple Inc.')
    
    def test_search_by_symbol_partial_match(self):
        """Test searching by partial symbol match."""
        response = self.client.get(self.url, {'q': 'AAP'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['symbol'], 'AAPL')
    
    def test_search_by_name_exact_match(self):
        """Test searching by exact name match."""
        response = self.client.get(self.url, {'q': 'Apple Inc.'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['symbol'], 'AAPL')
    
    def test_search_by_name_partial_match(self):
        """Test searching by partial name match."""
        response = self.client.get(self.url, {'q': 'Apple'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['symbol'], 'AAPL')
    
    def test_search_case_insensitive(self):
        """Test that search is case-insensitive."""
        response_lower = self.client.get(self.url, {'q': 'aapl'})
        response_upper = self.client.get(self.url, {'q': 'AAPL'})
        response_mixed = self.client.get(self.url, {'q': 'AaPl'})
        
        self.assertEqual(response_lower.status_code, status.HTTP_200_OK)
        self.assertEqual(response_upper.status_code, status.HTTP_200_OK)
        self.assertEqual(response_mixed.status_code, status.HTTP_200_OK)
        
        # All should return the same result
        self.assertEqual(len(response_lower.data), 1)
        self.assertEqual(len(response_upper.data), 1)
        self.assertEqual(len(response_mixed.data), 1)
        self.assertEqual(response_lower.data[0]['symbol'], 'AAPL')
        self.assertEqual(response_upper.data[0]['symbol'], 'AAPL')
        self.assertEqual(response_mixed.data[0]['symbol'], 'AAPL')
    
    def test_search_by_name_case_insensitive(self):
        """Test that name search is case-insensitive."""
        response = self.client.get(self.url, {'q': 'apple'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['symbol'], 'AAPL')
    
    def test_search_multiple_results(self):
        """Test search that returns multiple results."""
        response = self.client.get(self.url, {'q': 'Inc'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)
        # Should include Apple Inc., Microsoft Corporation, Tesla Inc., Alphabet Inc.
        symbols = [item['symbol'] for item in response.data]
        self.assertIn('AAPL', symbols)
        self.assertIn('TSLA', symbols)
        self.assertIn('GOOGL', symbols)
    
    def test_search_filter_by_asset_type(self):
        """Test filtering by asset type (stocks)."""
        response = self.client.get(self.url, {'q': 'BOND001', 'asset_type': 'stocks'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # All results should be stocks
        for item in response.data:
            self.assertEqual(item['asset_type'], 'stocks')
        # Should not include bonds or cryptocurrencies
        symbols = [item['symbol'] for item in response.data]
        self.assertNotIn('BOND001', symbols)
        self.assertNotIn('BTC', symbols)
    
    def test_search_no_results(self):
        """Test search with no matching results."""
        response = self.client.get(self.url, {'q': 'XYZ123'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 0)
    
    def test_search_query_too_short(self):
        """Test that query must be at least 2 characters."""
        response = self.client.get(self.url, {'q': 'A'})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertIn('at least 2 characters', response.data['error'])
    
    def test_search_empty_query(self):
        """Test search with empty query."""
        response = self.client.get(self.url, {'q': ''})
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_search_missing_query_parameter(self):
        """Test search without query parameter."""
        response = self.client.get(self.url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
    
    def test_search_limit_default(self):
        """Test that default limit is applied."""
        # Create more than 20 assets
        for i in range(25):
            Asset.objects.create(
                symbol=f'SYM{i}',
                name=f'Stock {i}',
                asset_type=Asset.AssetType.STOCKS
            )
        
        response = self.client.get(self.url, {'q': 'Stock'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data), 20)
    
    def test_search_limit_custom(self):
        """Test custom limit parameter."""
        # Create more than 10 assets
        for i in range(15):
            Asset.objects.create(
                symbol=f'SYM{i}',
                name=f'Stock {i}',
                asset_type=Asset.AssetType.STOCKS
            )
        
        response = self.client.get(self.url, {'q': 'Stock', 'limit': '10'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data), 10)
    
    def test_search_limit_max(self):
        """Test that limit cannot exceed 50."""
        # Create more than 50 assets
        for i in range(60):
            Asset.objects.create(
                symbol=f'SYM{i}',
                name=f'Stock {i}',
                asset_type=Asset.AssetType.STOCKS
            )
        
        response = self.client.get(self.url, {'q': 'Stock', 'limit': '100'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(response.data), 50)
    
    def test_search_results_ordered(self):
        """Test that results are ordered by symbol and name."""
        response = self.client.get(self.url, {'q': 'Inc'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if len(response.data) > 1:
            # Check that results are ordered
            symbols = [item['symbol'] for item in response.data]
            sorted_symbols = sorted(symbols)
            self.assertEqual(symbols, sorted_symbols)
    
    def test_search_with_whitespace(self):
        """Test that whitespace in query is trimmed."""
        response = self.client.get(self.url, {'q': '  AAPL  '})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['symbol'], 'AAPL')
    
    def test_search_symbol_or_name_both_match(self):
        """Test that search matches both symbol and name fields."""
        # Search for something that could match both
        response = self.client.get(self.url, {'q': 'MS'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Should find MSFT (symbol match) and possibly others with 'MS' in name
        symbols = [item['symbol'] for item in response.data]
        self.assertIn('MSFT', symbols)

    def test_search_with_special_characters(self):
        """Test search with special characters in query."""
        Asset.objects.create(
            symbol='TEST-001',
            name='Test & Company',
            asset_type=Asset.AssetType.STOCKS
        )
        
        response = self.client.get(self.url, {'q': 'TEST-'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        symbols = [item['symbol'] for item in response.data]
        self.assertIn('TEST-001', symbols)
