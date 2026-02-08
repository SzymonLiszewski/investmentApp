import React, { useState, useEffect } from 'react';
import { Box, CircularProgress, Table, TableBody, TableCell, TableContainer, TableHead, TableRow, Paper } from '@mui/material';
import apiClient from '../../api/client';

const ASSET_TYPE_LABELS = {
  stocks: 'Stock',
  bonds: 'Bond',
  cryptocurrencies: 'Crypto',
};

function formatMoney(value, currency) {
  if (value == null) return '—';
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value) + ` ${currency}`;
}

function formatPercent(value) {
  if (value == null) return '—';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

function ActivePositionsTable({ currency }) {
  const [positions, setPositions] = useState([]);
  const [portfolioCurrency, setPortfolioCurrency] = useState('PLN');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPositions = async () => {
      setLoading(true);
      setError(null);
      try {
        const selectedCurrency = currency || localStorage.getItem('preferredCurrency') || 'PLN';
        const response = await apiClient.get(
          `api/portfolio/composition/?currency=${selectedCurrency}`
        );
        const data = response.data;
        setPortfolioCurrency(data.currency);
        setPositions(data.composition_by_asset || []);
      } catch (err) {
        console.error('Error fetching positions:', err);
        setError(err.message || 'Failed to load positions');
        setPositions([]);
      } finally {
        setLoading(false);
      }
    };

    fetchPositions();
  }, [currency]);

  if (loading) {
    return (
      <div className="activePositionsContent" id="activePositions">
        <h3 style={{ marginBottom: 16, textAlign: 'center' }}>Active positions</h3>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight={120}>
          <CircularProgress />
        </Box>
      </div>
    );
  }

  if (error) {
    return (
      <div className="activePositionsContent" id="activePositions">
        <h3 style={{ marginBottom: 16, textAlign: 'center' }}>Active positions</h3>
        <p style={{ color: '#c62828', padding: 24, textAlign: 'center' }}>{error}</p>
      </div>
    );
  }

  if (positions.length === 0) {
    return (
      <div className="activePositionsContent" id="activePositions">
        <h3 style={{ marginBottom: 16, textAlign: 'center' }}>Active positions</h3>
        <p style={{ color: '#666', padding: 24, textAlign: 'center' }}>
          No positions yet. Add assets to see your active positions here.
        </p>
      </div>
    );
  }

  return (
    <div className="activePositionsContent" id="activePositions">
      <h3 style={{ marginBottom: 16, textAlign: 'center' }}>Active positions</h3>
      <TableContainer component={Paper} sx={{ borderRadius: 2, boxShadow: 'none' }}>
        <Table size="small" aria-label="Active positions">
          <TableHead>
            <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
              <TableCell><strong>Asset</strong></TableCell>
              <TableCell><strong>Symbol</strong></TableCell>
              <TableCell><strong>Type</strong></TableCell>
              <TableCell align="right"><strong>Quantity</strong></TableCell>
              <TableCell align="right"><strong>Avg. purchase price</strong></TableCell>
              <TableCell align="right"><strong>Total cost</strong></TableCell>
              <TableCell align="right"><strong>Current value</strong></TableCell>
              <TableCell align="right"><strong>Profit / Loss</strong></TableCell>
              <TableCell align="right"><strong>Return %</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {positions.map((row) => (
              <TableRow key={row.id || row.symbol} hover>
                <TableCell>{row.name || row.symbol}</TableCell>
                <TableCell>{row.symbol}</TableCell>
                <TableCell>{ASSET_TYPE_LABELS[row.asset_type] || row.asset_type}</TableCell>
                <TableCell align="right">{row.quantity != null ? Number(row.quantity).toLocaleString('en-US', { maximumFractionDigits: 4 }) : '—'}</TableCell>
                <TableCell align="right">{formatMoney(row.average_purchase_price, portfolioCurrency)}</TableCell>
                <TableCell align="right">{formatMoney(row.total_cost, portfolioCurrency)}</TableCell>
                <TableCell align="right">{formatMoney(row.current_value, portfolioCurrency)}</TableCell>
                <TableCell align="right" sx={{ color: row.profit != null && row.profit >= 0 ? '#2e7d32' : row.profit != null ? '#c62828' : 'inherit' }}>
                  {row.profit != null ? formatMoney(row.profit, portfolioCurrency) : '—'}
                </TableCell>
                <TableCell align="right" sx={{ color: row.profit_percentage != null && row.profit_percentage >= 0 ? '#2e7d32' : row.profit_percentage != null ? '#c62828' : 'inherit' }}>
                  {formatPercent(row.profit_percentage)}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
}

export default ActivePositionsTable;
