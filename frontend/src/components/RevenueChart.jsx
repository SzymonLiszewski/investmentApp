/* eslint-disable react/prop-types */
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import useReducedMotion from '../hooks/useReducedMotion';
import { formatNumberWithSuffix } from '../utils/format';

const ACCENT = '#6d4fd2';

const tooltipStyles = {
  contentStyle: {
    borderRadius: 10,
    border: '1px solid #e9e4f2',
    boxShadow: '0 8px 24px -8px rgba(29, 26, 38, 0.18)',
    fontSize: 12.5,
  },
  labelStyle: { color: '#8d86a0', marginBottom: 4 },
  itemStyle: { color: '#1d1a26', fontWeight: 600 },
};

const RevenueChart = ({ data }) => {
  const reducedMotion = useReducedMotion();
  const history = Object.keys(data).map((year) => ({
    year,
    revenue: data[year],
  }));
  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart data={history} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="#efebf6" vertical={false} />
        <XAxis
          dataKey="year"
          tick={{ fontSize: 11, fill: '#a49bbd' }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 11, fill: '#a49bbd' }}
          axisLine={false}
          tickLine={false}
          width={52}
          tickFormatter={(value) => `$${formatNumberWithSuffix(value)}`}
        />
        <Tooltip
          {...tooltipStyles}
          cursor={{ fill: '#efeaf6' }}
          formatter={(value) => [`$${formatNumberWithSuffix(value)}`, 'Revenue']}
        />
        <Bar
          dataKey="revenue"
          name="Revenue"
          fill={ACCENT}
          radius={[4, 4, 0, 0]}
          maxBarSize={24}
          isAnimationActive={!reducedMotion}
        />
      </BarChart>
    </ResponsiveContainer>
  );
};

export default RevenueChart;
