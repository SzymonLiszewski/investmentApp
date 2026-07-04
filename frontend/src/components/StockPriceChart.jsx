/* eslint-disable react/prop-types */
import {
  ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { useState, useEffect } from "react";
import useReducedMotion from '../hooks/useReducedMotion';
import useMediaQuery from '../hooks/useMediaQuery';
import './styles/StockPriceChart.css';

const ACCENT = '#6d4fd2';
const FORECAST = '#3da06c';
const GRID = '#efebf6';
const TICK = '#a49bbd';
const CURSOR = '#d7cfe8';

const dateToTimestamp = (dateStr) => new Date(dateStr).getTime();

const formatDate = (timestamp) =>
  new Date(timestamp).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  });

const formatTick = (timestamp) => {
  const date = new Date(timestamp);
  const month = date.toLocaleDateString('en-US', { month: 'short' });
  const year = String(date.getFullYear()).slice(2);
  return `${month} '${year}`;
};

// The regression endpoint returns one flat {date: price} dict (history and
// forecast merged); sarima returns {history: {...}, forecast: [{date, predicted,
// lower, upper}]} — lower/upper feed the confidence band.
const buildChartData = (data, model, endDate) => {
  let history;
  let predicted;
  if (model === 'sarima') {
    history = Object.entries(data.history).map(([date, price]) => ({
      date: dateToTimestamp(date),
      price,
    }));
    predicted = data.forecast.map((point) => ({
      date: dateToTimestamp(point.date),
      predicted: point.predicted,
      band: point.lower != null && point.upper != null
        ? [point.lower, point.upper]
        : undefined,
    }));
  } else {
    const endTimestamp = dateToTimestamp(endDate);
    const entries = Object.entries(data).map(([date, value]) => ({
      date: dateToTimestamp(date),
      value,
    }));
    history = entries
      .filter((e) => e.date <= endTimestamp)
      .map((e) => ({date: e.date, price: e.value}));
    predicted = entries
      .filter((e) => e.date > endTimestamp)
      .map((e) => ({date: e.date, predicted: e.value}));
  }
  history.sort((a, b) => a.date - b.date);
  predicted.sort((a, b) => a.date - b.date);
  if (history.length && predicted.length) {
    // duplicate the last real price onto the predicted line so the two lines connect
    const last = history[history.length - 1];
    last.predicted = last.price;
    if (predicted[0].band) {
      last.band = [last.price, last.price];
    }
  }
  return [...history, ...predicted];
};

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload || payload.length === 0) return null;
  const rows = payload.filter((entry) => entry.value != null && entry.dataKey !== 'band');
  if (rows.length === 0) return null;
  return (
    <div className="price-chart-tooltip">
      <div className="price-chart-tooltip-date">{formatDate(label)}</div>
      {rows.map((entry) => (
        <div key={entry.dataKey} className="price-chart-tooltip-row">
          <span
            className={`price-chart-tooltip-key${entry.dataKey === 'predicted' ? ' dashed' : ''}`}
            style={{ borderColor: entry.color }}
          />
          <span className="price-chart-tooltip-value">${Number(entry.value).toFixed(2)}</span>
          <span className="price-chart-tooltip-name">{entry.name}</span>
        </div>
      ))}
    </div>
  );
}

const StockChart = ({startDate, endDate, ticker, model = 'regression'}) => {
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const reducedMotion = useReducedMotion();
  const narrow = useMediaQuery('(max-width: 640px)');

  useEffect(() => {
    let cancelled = false;
    const getPrediction = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await fetch(
          `/api/analytics/predict/${ticker}/?start=${startDate}&end=${endDate}&model=${model}`
        );
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.error || 'Failed to load forecast');
        }
        if (!cancelled) {
          setChartData(buildChartData(data, model, endDate));
        }
      } catch (err) {
        if (!cancelled) {
          setError(err.message);
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };
    getPrediction();
    return () => {
      cancelled = true;
    };
  }, [ticker, model, startDate, endDate]);

  if (loading) {
    return <div className="chart-status">Loading forecast…</div>;
  }
  if (error) {
    return <div className="chart-status">Could not load forecast: {error}</div>;
  }

  return (
    <div className="chart-area">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid stroke={GRID} vertical={false} />
          <XAxis
            dataKey="date"
            type="number"
            domain={['dataMin', 'dataMax']}
            tickFormatter={formatTick}
            tick={{ fontSize: 11, fill: TICK }}
            axisLine={false}
            tickLine={false}
            minTickGap={narrow ? 72 : 48}
          />
          <YAxis
            domain={['auto', 'auto']}
            tickFormatter={(value) => `$${Math.round(value)}`}
            tick={{ fontSize: 11, fill: TICK }}
            axisLine={false}
            tickLine={false}
            tickCount={narrow ? 4 : 6}
            width={narrow ? 44 : 52}
          />
          <Tooltip content={<ChartTooltip />} cursor={{ stroke: CURSOR, strokeWidth: 1 }} />
          <Area
            dataKey="band"
            name="Confidence band"
            stroke="none"
            fill={FORECAST}
            fillOpacity={0.1}
            activeDot={false}
            isAnimationActive={!reducedMotion}
          />
          <Line
            type="monotone"
            dataKey="price"
            name="Price"
            stroke={ACCENT}
            strokeWidth={2}
            strokeLinejoin="round"
            strokeLinecap="round"
            dot={false}
            activeDot={{ r: 4, stroke: '#fff', strokeWidth: 2 }}
            isAnimationActive={!reducedMotion}
          />
          <Line
            type="monotone"
            dataKey="predicted"
            name="Forecast"
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
    </div>
  );
};

export default StockChart;
