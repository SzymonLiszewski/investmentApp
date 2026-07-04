/* eslint-disable react/prop-types */
import { useMemo } from 'react';
import {
  ComposedChart,
  Area,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';
import useReducedMotion from '../../hooks/useReducedMotion';
import './HeroForecastChart.css';

const ACCENT = '#6d4fd2';
const FORECAST = '#3da06c';
const CURSOR = '#d7cfe8';

const DAY_MS = 24 * 60 * 60 * 1000;

function formatDay(date) {
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

// Merge history and forecast into one series; the forecast line starts at the
// last historical point so the two lines connect visually.
function buildData(history, forecast) {
  const today = Date.now();
  const rows = history.map((value, index) => ({
    date: formatDay(new Date(today - (history.length - 1 - index) * DAY_MS)),
    price: value,
    forecast: index === history.length - 1 ? value : null,
  }));
  forecast.forEach((value, index) => {
    rows.push({
      date: formatDay(new Date(today + (index + 1) * DAY_MS)),
      price: null,
      forecast: value,
    });
  });
  return rows;
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload || payload.length === 0) return null;
  const rows = payload.filter((entry) => entry.value != null);
  if (rows.length === 0) return null;
  return (
    <div className="hero-chart-tooltip">
      <div className="hero-chart-tooltip-date">{label}</div>
      {rows.map((entry) => (
        <div key={entry.dataKey} className="hero-chart-tooltip-row">
          <span
            className={`hero-chart-tooltip-key${entry.dataKey === 'forecast' ? ' dashed' : ''}`}
            style={{ borderColor: entry.color }}
          />
          <span className="hero-chart-tooltip-value">${Number(entry.value).toFixed(2)}</span>
          <span className="hero-chart-tooltip-name">{entry.name}</span>
        </div>
      ))}
    </div>
  );
}

const HeroForecastChart = ({ history, forecast }) => {
  const reducedMotion = useReducedMotion();
  const data = useMemo(() => buildData(history, forecast), [history, forecast]);

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ComposedChart data={data} margin={{ top: 4, right: 0, bottom: 0, left: 0 }}>
        <defs>
          <linearGradient id="heroPriceFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={ACCENT} stopOpacity={0.16} />
            <stop offset="100%" stopColor={ACCENT} stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis dataKey="date" hide />
        <YAxis hide domain={['dataMin - 8', 'dataMax + 8']} />
        <Tooltip content={<ChartTooltip />} cursor={{ stroke: CURSOR, strokeWidth: 1 }} />
        <Area
          type="monotone"
          dataKey="price"
          name="Price history"
          stroke={ACCENT}
          strokeWidth={2}
          strokeLinejoin="round"
          strokeLinecap="round"
          fill="url(#heroPriceFill)"
          dot={false}
          activeDot={{ r: 4, stroke: '#fff', strokeWidth: 2 }}
          isAnimationActive={!reducedMotion}
        />
        <Line
          type="monotone"
          dataKey="forecast"
          name="30-day forecast"
          stroke={FORECAST}
          strokeWidth={2}
          strokeDasharray="6 5"
          strokeLinejoin="round"
          strokeLinecap="round"
          dot={false}
          activeDot={{ r: 4, stroke: '#fff', strokeWidth: 2 }}
          isAnimationActive={!reducedMotion}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

export default HeroForecastChart;
