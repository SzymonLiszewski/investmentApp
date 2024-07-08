import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const data = [
  { name: '2019', uv: 4000, pv: 2400 },
  { name: '2020', uv: 3000, pv: 1398 },
  { name: '2021', uv: 2000, pv: 9800 },
  { name: '2022', uv: 2780, pv: 3908 },
  { name: '2023', uv: 1890, pv: 4800 },

];

const RevenueChart = () => {
  return (
    <ResponsiveContainer width="100%" height="92%">
      <BarChart
        layout="vertical"
        data={data}
        margin={{
          top: 20,
          right: 50,
          left: 20,
          bottom: 20,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis xAxisId="top" type="number"  orientation='top' stroke="#8884d8"/>
        <XAxis xAxisId="bottom" type="number"  orientation='bottom' stroke="#82ca9d"/>
        <YAxis type="category" dataKey="name" stroke="#fff"/>
        <Tooltip />
        <Legend />
        <Bar xAxisId="top" dataKey="pv" name="Revenue" fill="#8884d8" />
        <Bar xAxisId="bottom" dataKey="uv" name="Net income" fill="#82ca9d" />
      </BarChart>
    </ResponsiveContainer>
  );
};

export default RevenueChart;
