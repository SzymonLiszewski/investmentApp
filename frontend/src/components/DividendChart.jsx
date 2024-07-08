import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const data = [
  { name: '2019', DPS: 0.75, DY: 1.37 },
  { name: '2020', DPS: 0.80, DY: 0.71 },
  { name: '2021', DPS: 0.85, DY: 0.58 },
  { name: '2022', DPS: 0.90, DY: 0.60 },
  { name: '2023', DPS: 0.94, DY: 0.55 },
];

const DividendChart = () => {
  return (
    <ResponsiveContainer width="100%" height="85%">
      <BarChart
        data={data}
        margin={{
          top: 20,
          right: 50,
          left: 20,
          bottom: 20,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="name" stroke="#fff"/>
        <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
        <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
        <Tooltip />
        <Legend />
        <Bar yAxisId="left" dataKey="DY" name="dividend per share"  fill="#8884d8" />
        <Bar yAxisId="right" dataKey="DPS" name="dividend yield" fill="#82ca9d" />
      </BarChart>
    </ResponsiveContainer>
  );
};

export default DividendChart;
