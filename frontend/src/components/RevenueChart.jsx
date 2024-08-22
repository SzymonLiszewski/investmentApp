import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';


const RevenueChart = ({data}) => {
  const history = Object.keys(data).map(year => ({
    name: year,
    pv: data[year]
  }));
  console.log("tr:",history)
  return (
    <ResponsiveContainer width="100%" height="92%">
      <BarChart
        layout="vertical"
        data={history}
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
