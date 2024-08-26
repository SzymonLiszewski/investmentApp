import React from 'react';
import { PieChart, Pie, Cell, Tooltip, Legend, Label } from 'recharts';

const IndicatorsGaugeChart = ({ data, range, name, interpretation }) => {
  const value = Math.min(Math.max(data, range[0]), range[1]);
  const gaugeData = [
    { name, value, fill: '#8884d8' },
    { name: 'Remaining', value: range[1] - value, fill: '#e0e0e0' },
  ];
  if (data==-100){
    return(
      <p>Loading...</p>
    )
  }

  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', margin: '10px' }}>
    <PieChart width={200} height={200}>
      <Pie
        data={gaugeData}
        startAngle={180}
        endAngle={0}
        innerRadius={60}
        outerRadius={80}
        dataKey="value"
      >
        {gaugeData.map((entry, index) => (
          <Cell key={`cell-${index}`} fill={entry.fill} />
        ))}
        <Label
          value={value.toFixed(2)}
          position="center"
          fill="#000"
          fontSize="24px"
          fontWeight="bold"
        />
      </Pie>
      <Tooltip />
    </PieChart>
    <p style={{ color: 'black', marginLeft: '20px', whiteSpace: 'pre-wrap', wordWrap: 'break-word', maxWidth: '200px' }}>{interpretation}</p>
    </div>
  );
};

export default IndicatorsGaugeChart;