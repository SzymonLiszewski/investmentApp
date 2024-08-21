import React from 'react';
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';



const UserEarningsChart = ({profit}) => {
    

  return (
    <ResponsiveContainer width="100%" height={400}>
      <LineChart
        data={profit}
        margin={{
          top: 20, right: 30, left: 20, bottom: 5,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fontSize: 20 }} interval={7}/>
        <YAxis tick={{ fontSize: 20 }} />
        <Tooltip contentStyle={{ fontSize: 16 }} />
        <Legend wrapperStyle={{ fontSize: 16 }} />
        <Line type="monotone" dataKey="price" stroke="#8884d8" strokeWidth={4} activeDot={{ r: 8 }} />
        <Line type="monotone" dataKey="benchmark" stroke="#82ca9d" />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default UserEarningsChart;
