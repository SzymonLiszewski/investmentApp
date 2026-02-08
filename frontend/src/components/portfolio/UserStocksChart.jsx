import React from 'react';
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { useState, useEffect } from 'react';
import { Box, CircularProgress } from '@mui/material';
import apiClient from '../../api/client';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', '#82CA9D', '#FFC658', '#FF6B6B'];

function UserStocksChart({ currency }){
    const [userAsset, setUserAsset] = useState([]);
    const [portfolioCurrency, setPortfolioCurrency] = useState('PLN');
    const [loading, setLoading] = useState(true);

    useEffect(()=>{
      const getUserAsset = async () => {
        setLoading(true);
        try {
            const assetData = await fetchUserAsset();
            setUserAsset(assetData);
        } catch (error) {
            console.log(error.message);
        } finally {
            setLoading(false);
        }
    };

    getUserAsset();
    }, [currency]); // Re-fetch when currency changes

    const fetchUserAsset = async () => {
      try {
          const selectedCurrency = currency || localStorage.getItem('preferredCurrency') || 'PLN';
          const response = await apiClient.get(
            `api/portfolio/composition/?currency=${selectedCurrency}`
          );
          const data = response.data;
          
          // Store the currency used for display
          setPortfolioCurrency(data.currency);
          
          // Transform the new API response to chart format
          // Use composition_by_asset which includes current values and percentages
          const transformedData = data.composition_by_asset.map(item => ({
            name: item.symbol || item.name,
            value: item.current_value
          }));
          
          return transformedData;
      } catch (error) {
          console.error('There has been a problem with your fetch operation:', error);
          throw error;
      }
  };

    const titleStyle = { marginBottom: 8, textAlign: 'center' };

    if (loading) {
      return (
        <div>
          <h3 style={titleStyle}>Allocation by asset</h3>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
            <CircularProgress />
          </Box>
        </div>
      );
    }

    return (
        <div>
          <h3 style={titleStyle}>Allocation by asset</h3>
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
            <Pie
              data={userAsset}
              cx="40%"
              cy="50%"
              labelLine={false}
              label={({ name, percent, cx, cy, midAngle, innerRadius, outerRadius }) => {
                const RADIAN = Math.PI / 180;
                
                // Calculate radius for label placement
                // Use 1.2 to place labels outside the chart (20% beyond outerRadius)
                const radius = outerRadius * 1.2;
                
                // Calculate x and y coordinates for the label based on:
                // - cx, cy: center coordinates of the chart
                // - radius: distance from center where we place the label
                // - midAngle: middle angle of the segment (in degrees, provided by Recharts)
                // - Math.cos/sin: trigonometric functions to calculate position on circle
                // - negative midAngle: because in SVG angles go in opposite direction
                const x = cx + radius * Math.cos(-midAngle * RADIAN);
                const y = cy + radius * Math.sin(-midAngle * RADIAN);
                
                return (
                  <text 
                    x={x} 
                    y={y} 
                    fill="#000" 
                    textAnchor="middle" 
                    dominantBaseline="central"
                    fontSize="10px"
                  >
                    {`${name}: ${(percent * 100).toFixed(0)}%`}
                  </text>
                );
              }}
              outerRadius={150}
              fill="#8884d8"
              dataKey="value"
            >
              {
                userAsset.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)
              }
            </Pie>
            <Tooltip 
              contentStyle={{ fontSize: 12 }} 
              formatter={(value, name) => [typeof value === 'number' ? value.toFixed(2) : value, name]}
            />
            <Legend wrapperStyle={{ fontSize: 12 } } layout="vertical" verticalAlign="middle" align="right" />
          </PieChart>
        </ResponsiveContainer>
        </div>
      );
}
export default UserStocksChart