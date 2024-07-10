import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';


const DividendChart = ({data}) => {
  const history = Object.keys(data).map(year => ({
    year: year,
    dividend: data[year]
  }));
  //<Bar yAxisId="right" dataKey="DPS" name="dividend yield" fill="#82ca9d" /
  return (
    <ResponsiveContainer width="100%" height="85%">
      <BarChart
        data={history}
        margin={{
          top: 20,
          right: 50,
          left: 20,
          bottom: 20,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="year" stroke="#fff"/>
        <YAxis yAxisId="left" orientation="left" stroke="#8884d8" />
        <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
        <Tooltip />
        <Legend />
        <Bar yAxisId="left" dataKey="dividend" name="dividend per share"  fill="#8884d8" />
        
      </BarChart>
    </ResponsiveContainer>
  );
};

export default DividendChart;
