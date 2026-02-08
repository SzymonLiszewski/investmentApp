import React from 'react';
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { useState, useEffect } from 'react';
import { Box, CircularProgress } from '@mui/material';
import apiClient from '../../api/client';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D'];

const ASSET_CLASS_LABELS = {
  stocks: 'Stocks',
  bonds: 'Bonds',
  cryptocurrencies: 'Cryptocurrencies',
};

function AssetClassAllocationChart({ currency }) {
  const [compositionByClass, setCompositionByClass] = useState([]);
  const [portfolioCurrency, setPortfolioCurrency] = useState('PLN');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchComposition = async () => {
      setLoading(true);
      try {
        const data = await fetchCompositionByClass();
        setCompositionByClass(data.byClass);
        setPortfolioCurrency(data.currency);
      } catch (error) {
        console.error(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchComposition();
  }, [currency]);

  const fetchCompositionByClass = async () => {
    const selectedCurrency = currency || localStorage.getItem('preferredCurrency') || 'PLN';
    const response = await apiClient.get(
      `api/portfolio/composition/?currency=${selectedCurrency}`
    );
    const data = response.data;

    const byClass = Object.entries(data.composition_by_type || {}).map(
      ([assetType, item]) => ({
        name: ASSET_CLASS_LABELS[assetType] || assetType,
        value: item.value,
        percentage: item.percentage,
      })
    );

    return { byClass, currency: data.currency };
  };

  const titleStyle = { marginBottom: 8, textAlign: 'center' };

  if (loading) {
    return (
      <div>
        <h3 style={titleStyle}>Allocation by asset class</h3>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight={360}>
          <CircularProgress />
        </Box>
      </div>
    );
  }

  if (compositionByClass.length === 0) {
    return (
      <div>
        <h3 style={titleStyle}>Allocation by asset class</h3>
        <p style={{ color: '#666', padding: 24, textAlign: 'center' }}>No asset class data. Add assets to see allocation by class.</p>
      </div>
    );
  }

  return (
    <div>
      <h3 style={titleStyle}>Allocation by asset class</h3>
      <ResponsiveContainer width="100%" height={400}>
        <PieChart>
          <Pie
            data={compositionByClass}
            cx="40%"
            cy="50%"
            labelLine={false}
            label={({ name, percent, cx, cy, midAngle, innerRadius, outerRadius }) => {
              const RADIAN = Math.PI / 180;
              const radius = outerRadius * 1.2;
              const x = cx + radius * Math.cos(-midAngle * RADIAN);
              const y = cy + radius * Math.sin(-midAngle * RADIAN);

              return (
                <text
                  x={x}
                  y={y}
                  fill="#000"
                  textAnchor="middle"
                  dominantBaseline="central"
                  fontSize="12px"
                >
                  {`${name}: ${(percent * 100).toFixed(0)}%`}
                </text>
              );
            }}
            outerRadius={150}
            fill="#8884d8"
            dataKey="value"
          >
            {compositionByClass.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{ fontSize: 12 }}
            formatter={(value) => [
              typeof value === 'number' ? `${value.toFixed(2)} ${portfolioCurrency}` : value,
            ]}
            labelFormatter={(name) => name}
          />
          <Legend
            wrapperStyle={{ fontSize: 12 }}
            layout="vertical"
            verticalAlign="middle"
            align="right"
          />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}

export default AssetClassAllocationChart;
