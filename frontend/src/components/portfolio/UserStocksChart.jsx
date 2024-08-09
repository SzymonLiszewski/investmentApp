import React from 'react';
import {
  PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { useState, useEffect } from 'react';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

function UserStocksChart(){
    const data = [
        { name: 'Produkt A', value: 400 },
        { name: 'Produkt B', value: 300 },
        { name: 'Produkt C', value: 300 },
        { name: 'Produkt D', value: 200 },
      ];
      const [userStock, setUserStock] = useState([]);

    useEffect(()=>{
      const getUserStock = async () => {
        try {
            const stockData = await fetchUserStock();
            setUserStock(stockData);
            console.log("userStock: ", stockData)
        } catch (error) {
            console.log(error.message);
        }
    };

    getUserStock();
    },[]);

    const fetchUserStock = async () => {
      try {
          const token = localStorage.getItem('access');

          const response = await fetch('api/userStock/', {
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
          console.log(data);
          const transformedData = data.map(item => ({
            name: item.ownedStock, 
            value: item.quantity 
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
              data={userStock}
              cx="40%"
              cy="50%"
              labelLine={false}
              outerRadius={150}
              fill="#8884d8"
              dataKey="value"
            >
              {
                data.map((entry, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)
              }
            </Pie>
            <Tooltip contentStyle={{ fontSize: 12 }} />
            <Legend wrapperStyle={{ fontSize: 12 } } layout="vertical" verticalAlign="middle" align="right" />
          </PieChart>
        </ResponsiveContainer>
      );
}
export default UserStocksChart