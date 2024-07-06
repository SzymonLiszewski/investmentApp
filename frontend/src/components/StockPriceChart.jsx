import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Area
} from 'recharts';

// Przykładowe dane
const data = [
  { date: '2023-01-01', price: 150 },
  { date: '2023-01-02', price: 152 },
  { date: '2023-01-03', price: 153 },
  { date: '2023-01-04', price: 155 },
  { date: '2023-01-05', price: 157 },
  { date: '2023-01-06', price: 158 },
  { date: '2023-01-07', price: 160 },
  { date: '2023-01-08', price: 162 },
  { date: '2023-01-09', price: 164 },
  { date: '2023-01-10', price: 165 },
  // Przewidywane dane
  { date: '2023-01-11', predicted: 166, lowerBound: 160, upperBound: 170 },
  { date: '2023-01-12', predicted: 167, lowerBound: 161, upperBound: 171 },
  { date: '2023-01-13', predicted: 168, lowerBound: 162, upperBound: 172 },
  { date: '2023-01-14', predicted: 169, lowerBound: 163, upperBound: 173 },
  { date: '2023-01-15', predicted: 170, lowerBound: 164, upperBound: 174 },
];

const StockChart = () => {
  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#fff"/>
        <XAxis dataKey="date" stroke="#fff"/>
        <YAxis stroke="#fff"/>
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="price" stroke="#009127" strokeWidth={5}/>
        <Line type="monotone" dataKey="predicted" stroke="#FF8042" strokeDasharray="5 5" strokeWidth={5}/>
        <Area type="monotone" dataKey="upperBound" stroke="none" fill="#82ca9d" fillOpacity={0.2} />
        <Area type="monotone" dataKey="lowerBound" stroke="none" fill="#82ca9d" fillOpacity={0.2} />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default StockChart;
