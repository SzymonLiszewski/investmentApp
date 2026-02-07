import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';


const UserEarningsChart = ({ data, currency = 'PLN' }) => {
  if (!data || data.length === 0) {
    return <p>No portfolio history available yet.</p>;
  }

  const formatValue = (value) =>
    typeof value === 'number' ? value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : value;

  return (
    <ResponsiveContainer width="100%" height={400}>
      <AreaChart
        data={data}
        margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
      >
        <defs>
          <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#8884d8" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#8884d8" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey="date"
          tick={{ fontSize: 14 }}
          interval="preserveStartEnd"
          tickCount={8}
        />
        <YAxis
          tick={{ fontSize: 14 }}
          tickFormatter={formatValue}
          width={80}
        />
        <Tooltip
          contentStyle={{ fontSize: 14 }}
          formatter={(value) => [`${formatValue(value)} ${currency}`, 'Portfolio Value']}
          labelFormatter={(label) => `Date: ${label}`}
        />
        <Area
          type="monotone"
          dataKey="total_value"
          name="Portfolio Value"
          stroke="#8884d8"
          strokeWidth={3}
          fill="url(#colorValue)"
          activeDot={{ r: 6 }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
};

export default UserEarningsChart;
