import React from 'react';
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { useState, useEffect } from 'react';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

function UserStocksChart(){
    const [userAsset, setUserAsset] = useState([]);

    useEffect(()=>{
      const getUserAsset = async () => {
        try {
            const assetData = await fetchUserAsset();
            setUserAsset(assetData);
        } catch (error) {
            console.log(error.message);
        }
    };

    getUserAsset();
    },[]);

    const fetchUserAsset = async () => {
      try {
          const token = localStorage.getItem('access');

          const response = await fetch('api/userAsset/', {
              method: 'GET',
              headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${token}`
              }
          });

          if (!response.ok) {
              throw new Error('Network response was not ok');
          }

          const data = await response.json();
          const transformedData = data.map(item => ({
            name: item.name, 
            value: item.market_value || 0
          }));
          return transformedData;
      } catch (error) {
          console.error('There has been a problem with your fetch operation:', error);
          throw error;
      }
  };


      return (
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
            <Tooltip contentStyle={{ fontSize: 12 }} />
            <Legend wrapperStyle={{ fontSize: 12 } } layout="vertical" verticalAlign="middle" align="right" />
          </PieChart>
        </ResponsiveContainer>
      );
}
export default UserStocksChart