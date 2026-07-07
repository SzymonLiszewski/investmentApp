import React from 'react';
import {
  ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import useMediaQuery from '../../hooks/useMediaQuery';


const UserEarningsChart = ({ data, currency = 'PLN' }) => {
  const narrow = useMediaQuery('(max-width: 640px)');
  if (!data || data.length === 0) {
    return <p>No portfolio history available yet.</p>;
  }

  const formatValue = (value) =>
    typeof value === 'number' ? value.toLocaleString(undefined, { maximumFractionDigits: 2 }) : value;

  const chartData = data.map((point) => ({
    ...point,
    total_value: point.total_value ?? 0,
    total_invested: point.total_invested ?? 0,
  }));

  return (
    <ResponsiveContainer width="100%" height={narrow ? 300 : 400}>
      <ComposedChart
        data={chartData}
        margin={narrow ? { top: 16, right: 12, left: 0, bottom: 5 } : { top: 20, right: 30, left: 20, bottom: 5 }}
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
          tick={{ fontSize: narrow ? 11 : 14 }}
          interval="preserveStartEnd"
          tickCount={narrow ? 4 : 8}
        />
        <YAxis
          tick={{ fontSize: narrow ? 11 : 14 }}
          tickFormatter={formatValue}
          width={narrow ? 56 : 80}
        />
        <Tooltip
          contentStyle={{ fontSize: 14 }}
          formatter={(value, name) => [`${formatValue(value)} ${currency}`, name]}
          labelFormatter={(label) => `Date: ${label}`}
        />
        <Legend />
        <Area
          type="monotone"
          dataKey="total_value"
          name="Portfolio Value"
          stroke="#8884d8"
          strokeWidth={3}
          fill="url(#colorValue)"
          activeDot={{ r: 6 }}
        />
        <Line
          type="monotone"
          dataKey="total_invested"
          name="Total Invested"
          stroke="#ff7c43"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 5 }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

export default UserEarningsChart;
