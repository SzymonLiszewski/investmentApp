import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { useEffect } from 'react';


const UserEarningsChart = () => {
    const data = [
        { date: '2023-01-01', profit: 100, benchmark: 90 },
        { date: '2023-02-01', profit: 150, benchmark: 130 },
        { date: '2023-03-01', profit: 200, benchmark: 180 },
        { date: '2023-04-01', profit: 250, benchmark: 220 },
        { date: '2023-05-01', profit: 300, benchmark: 270 },
        { date: '2023-06-01', profit: 350, benchmark: 320 },
        { date: '2023-07-01', profit: 400, benchmark: 370 },
        { date: '2023-08-01', profit: 450, benchmark: 420 },
        { date: '2023-09-01', profit: 500, benchmark: 470 },
        { date: '2023-10-01', profit: 550, benchmark: 520 },
        { date: '2023-11-01', profit: 600, benchmark: 570 },
        { date: '2023-12-01', profit: 650, benchmark: 620 },
      ];
      useEffect(()=>{
        const getUserStock = async () => {
          try {
              const stockData = await fetchUserProfit();
              console.log("userProfit: ", stockData)
          } catch (error) {
              console.log(error.message);
          }
      };
  
      getUserStock();
      },[]);
      const fetchUserProfit = async () => {
        try {
            const token = localStorage.getItem('access');
  
            const response = await fetch('api/portfolio/profit', {
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
      <LineChart
        data={data}
        margin={{
          top: 20, right: 30, left: 20, bottom: 5,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fontSize: 20 }} />
        <YAxis tick={{ fontSize: 20 }} />
        <Tooltip contentStyle={{ fontSize: 16 }} />
        <Legend wrapperStyle={{ fontSize: 16 }} />
        <Line type="monotone" dataKey="profit" stroke="#8884d8" activeDot={{ r: 8 }} />
        <Line type="monotone" dataKey="benchmark" stroke="#82ca9d" />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default UserEarningsChart;
