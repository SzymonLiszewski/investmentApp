import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Area
} from 'recharts';
import React, {useState, useEffect} from "react";

const dateToTimestamp = (dateStr) => new Date(dateStr).getTime();

const formatDate = (timestamp) => {
  const date = new Date(timestamp);
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

const StockChart = ({startDate, endDate, ticker, predictedDays}) => {

  let [PriceHistory, setPriceHistory] = useState([])
  let [Predicted, setPredicted] = useState([])
  let [FullArray, setFullArray] = useState([])
  const [loading, setLoading] = useState(true);



    useEffect(()=>{
        //getData()
        getPrediction()
        //join()
    },[ticker])

    let getPrediction = async () =>{
      let response = await fetch(`/api/predict/${ticker}/?start=${startDate}&end=${endDate}`)
      let data = await response.json()
      const history = Object.keys(data).map(year => ({
        date: dateToTimestamp(year),
        price: data[year]
      }));
      setPredicted(history)
      setLoading(false)
      console.log("predicted", Predicted)
      history[history.length-1] = {date: history[history.length-1].date, predicted: history[history.length-1].price};
      history[history.length-2] = {date: history[history.length-2].date, price: history[history.length-2].price,predicted: history[history.length-2].price};
      const historyData = history.filter(item => !item.isPredicted);
      const predictionData = history.filter(item => item.isPredicted);
      setPredicted(predictionData)
      setPriceHistory(historyData)
      setFullArray(history)
      setLoading(false)
      return history
    }

    if (loading) {
      return <div>Loading...</div>; // Możesz dodać tutaj loader lub spinner
    }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={FullArray} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#fff"/>
        <XAxis dataKey="date" 
        type="number"
        domain={['auto', 'auto']}
        tickFormatter={formatDate}
        stroke="#fff"/>
        <YAxis stroke="#fff"/>
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="price" stroke="#8884d8" strokeWidth={5} dot={false}/>
        <Line type="monotone" dataKey="predicted" stroke="#82ca9d" strokeWidth={5} dot={false}/>
      </LineChart>
    </ResponsiveContainer>
  );
};

export default StockChart;
