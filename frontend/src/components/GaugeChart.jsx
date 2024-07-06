import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Label } from 'recharts';

const GaugeChart = ({ value }) => {
  const data = [
    { name: 'value', value: value },
    { name: 'rest', value: 1 - value },
  ];

  const COLORS = ['#00C49F', '#FF8042'];

  return (
    <ResponsiveContainer width="100%" height={200}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="80%"
          startAngle={180}
          endAngle={0}
          innerRadius="70%"
          outerRadius="100%"
          fill="#8884d8"
          paddingAngle={5}
          dataKey="value"
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index]} />
          ))}
          <Label
              value={value}
              position="centerBottom" //
              offset={-20}
              className="gauge-label"
              fontSize="50px"
              fontWeight="bold"
            />
        </Pie>
      </PieChart>
    </ResponsiveContainer>
  );
};

export default GaugeChart;
