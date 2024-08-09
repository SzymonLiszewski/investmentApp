import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import { useEffect, useState } from 'react';
import { format } from 'date-fns';


const UserEarningsChart = () => {
    const [profit, setProfit] = useState([])
      useEffect(()=>{
        const getUserStock = async () => {
          try {
              const stockData = await fetchUserProfit();
              console.log("userProfit: ", profit)
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

            const rawCalculatedData = data.calculated_data;
        
        const jsonString = rawCalculatedData.replace(/^"(.+)"$/, '$1');

        const parsedData = JSON.parse(jsonString);

        console.log('Parsed Data:', parsedData);

            const formattedData = Object.entries(parsedData).map(([unixTime, price]) => ({
              date: format(new Date(Number(unixTime)), 'yyyy-MM-dd'),
              price: price
          }));
        console.log("raz", formattedData);
        setProfit(formattedData);
            return formattedData;
        } catch (error) {
            console.error('There has been a problem with your fetch operation:', error);
            throw error;
        }
    };

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart
        data={profit}
        margin={{
          top: 20, right: 30, left: 20, bottom: 5,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fontSize: 20 }} interval={50}/>
        <YAxis tick={{ fontSize: 20 }} />
        <Tooltip contentStyle={{ fontSize: 16 }} />
        <Legend wrapperStyle={{ fontSize: 16 }} />
        <Line type="monotone" dataKey="price" stroke="#8884d8" activeDot={{ r: 8 }} />
        <Line type="monotone" dataKey="benchmark" stroke="#82ca9d" />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default UserEarningsChart;
