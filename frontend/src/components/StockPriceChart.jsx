import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import {useState, useEffect} from "react";

const dateToTimestamp = (dateStr) => new Date(dateStr).getTime();

const formatDate = (timestamp) => {
  const date = new Date(timestamp);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

// The regression endpoint returns one flat {date: price} dict (history and
// forecast merged); sarima returns {history: {...}, forecast: [{date, predicted, ...}]}.
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
    history[history.length - 1].predicted = history[history.length - 1].price;
  }
  return [...history, ...predicted];
};

const StockChart = ({startDate, endDate, ticker, model = 'regression'}) => {
  const [chartData, setChartData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

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
    return <div>Loading...</div>;
  }
  if (error) {
    return <div>Could not load forecast: {error}</div>;
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e0e0e0"/>
        <XAxis dataKey="date"
        type="number"
        domain={['auto', 'auto']}
        tickFormatter={formatDate}
        stroke="#000000"/>
        <YAxis stroke="#000000"/>
        <Tooltip labelFormatter={formatDate} />
        <Legend />
        <Line type="monotone" dataKey="price" name="Price" stroke="#8884d8" strokeWidth={5} dot={false}/>
        <Line type="monotone" dataKey="predicted" name="Forecast" stroke="#82ca9d" strokeWidth={5} dot={false}/>
      </LineChart>
    </ResponsiveContainer>
  );
};

export default StockChart;
