import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  Area
} from 'recharts';
import React, {useState, useEffect} from "react";

// Przykładowe dane
const data = [
  { date: '2023-01-11', price: 150, lowerBound: 145, upperBound: 155 },
  { date: '2023-01-12', price: 152, lowerBound: 147, upperBound: 157 },
  { date: '2023-01-13', price: 148, lowerBound: 143, upperBound: 153 },
  { date: '2023-01-14', price: 155, lowerBound: 150, upperBound: 160 },
  { date: '2023-01-15', price: 157, lowerBound: 152, upperBound: 162 },
  { date: '2023-01-16', price: 153, lowerBound: 148, upperBound: 158 },
  { date: '2023-01-17', price: 160, lowerBound: 155, upperBound: 165 },
  { date: '2023-01-18', price: 158, lowerBound: 153, upperBound: 163 },
  { date: '2023-01-19', price: 162, lowerBound: 157, upperBound: 167 },
  { date: '2023-01-20', price: 159, lowerBound: 154, upperBound: 164 },
  { date: '2023-01-21', price: 165, lowerBound: 160, upperBound: 170 },
  { date: '2023-01-22', price: 163, lowerBound: 158, upperBound: 168 },
  { date: '2023-01-23', price: 168, lowerBound: 163, upperBound: 173 },
  { date: '2023-01-24', price: 170, lowerBound: 165, upperBound: 175 },
  { date: '2023-01-25', price: 166, lowerBound: 161, upperBound: 171 },
  { date: '2023-01-26', price: 172, lowerBound: 167, upperBound: 177 },
  { date: '2023-01-27', price: 149, lowerBound: 164, upperBound: 174 },
  { date: '2023-01-28', price: 174, lowerBound: 169, upperBound: 179 },
  { date: '2023-01-29', price: 171, lowerBound: 166, upperBound: 176 },
  { date: '2023-01-30', price: 177, lowerBound: 172, upperBound: 182 },
  { date: '2023-01-31', price: 175, lowerBound: 170, upperBound: 180 },
  { date: '2023-02-01', price: 180, lowerBound: 175, upperBound: 185 },
  { date: '2023-02-02', price: 178, lowerBound: 173, upperBound: 183 },
  { date: '2023-02-03', price: 202, lowerBound: 177, upperBound: 187 },
  { date: '2023-02-04', price: 179, lowerBound: 174, upperBound: 184 },
  { date: '2023-02-05', price: 185, lowerBound: 180, upperBound: 190 },
  { date: '2023-02-06', price: 183, lowerBound: 178, upperBound: 188 },
  { date: '2023-02-07', price: 188, lowerBound: 183, upperBound: 193 },
  { date: '2023-02-08', price: 186, lowerBound: 181, upperBound: 191 },
  { date: '2023-02-09', price: 150, lowerBound: 185, upperBound: 195 },
  { date: '2023-02-10', price: 188, lowerBound: 183, upperBound: 193 },
  { date: '2023-02-11', price: 193, lowerBound: 188, upperBound: 198 },
  { date: '2023-02-12', price: 191, lowerBound: 186, upperBound: 196 },
  { date: '2023-02-13', price: 175, lowerBound: 190, upperBound: 200 },
  { date: '2023-02-14', price: 193, lowerBound: 188, upperBound: 198 },
  { date: '2023-02-15', price: 198, lowerBound: 193, upperBound: 203 },
  { date: '2023-02-16', price: 196, lowerBound: 191, upperBound: 201 },
  { date: '2023-02-17', price: 200, lowerBound: 195, upperBound: 205 },
  { date: '2023-02-18', price: 198, lowerBound: 193, upperBound: 203 },
  { date: '2023-02-19', price: 202, lowerBound: 197, upperBound: 207 },
  { date: '2023-02-20', price: 200, lowerBound: 195, upperBound: 205 },
  { date: '2023-02-21', price: 205, lowerBound: 200, upperBound: 210 },
  { date: '2023-02-22', price: 233, lowerBound: 198, upperBound: 208 },
  { date: '2023-02-23', price: 207, lowerBound: 202, upperBound: 212 },
  { date: '2023-02-24', price: 205, lowerBound: 200, upperBound: 210 },
  { date: '2023-02-25', price: 210, lowerBound: 205, upperBound: 215 },
  { date: '2023-02-26', price: 208, lowerBound: 203, upperBound: 213 },
  { date: '2023-02-27', price: 213, lowerBound: 208, upperBound: 218 },
  { date: '2023-02-28', price: 211, lowerBound: 206, upperBound: 216 },
  { date: '2023-03-01', price: 215, lowerBound: 210, upperBound: 220 },
  { date: '2023-03-02', price: 213, lowerBound: 208, upperBound: 218 },
  { date: '2023-03-03', price: 218, lowerBound: 213, upperBound: 223 },
  { date: '2023-03-04', price: 216, lowerBound: 211, upperBound: 221 },
  { date: '2023-03-05', price: 220, lowerBound: 215, upperBound: 225 },
  { date: '2023-03-06', price: 218, lowerBound: 213, upperBound: 223 },
  { date: '2023-03-07', predicted: 223, lowerBound: 218, upperBound: 228 },
  { date: '2023-03-08', predicted: 221, lowerBound: 216, upperBound: 226 },
  { date: '2023-03-09', predicted: 225, lowerBound: 220, upperBound: 230 },
  { date: '2023-03-10', predicted: 223, lowerBound: 218, upperBound: 228 },
  { date: '2023-03-11', predicted: 228, lowerBound: 223, upperBound: 233 },
  { date: '2023-03-12', predicted: 226, lowerBound: 221, upperBound: 231 },
  { date: '2023-03-13', predicted: 230, lowerBound: 225, upperBound: 235 },
  { date: '2023-03-14', predicted: 208, lowerBound: 223, upperBound: 233 },
  { date: '2023-03-15', predicted: 233, lowerBound: 228, upperBound: 238 },
  { date: '2023-03-16', predicted: 231, lowerBound: 226, upperBound: 236 },
  { date: '2023-03-17', predicted: 265, lowerBound: 230, upperBound: 240 },
  { date: '2023-03-18', predicted: 233, lowerBound: 228, upperBound: 238 },
  { date: '2023-03-19', predicted: 238, lowerBound: 233, upperBound: 243 },
  { date: '2023-03-20', predicted: 236, lowerBound: 231, upperBound: 241 },

];

const StockChart = ({startDate, endDate, ticker, predictedDays}) => {

  let [PriceHistory, setPriceHistory] = useState()

    useEffect(()=>{
        getData()
    },[])

    let getData = async () =>{
      let response = await fetch(`/api/stockData/${ticker}/?start=2022-01-01&end=2024-01-01`)
      let data = await response.json()
      const history = Object.keys(data).map(year => ({
        date: year,
        price: data[year]
      }));
      setPriceHistory(history)
    }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <LineChart data={PriceHistory} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#fff"/>
        <XAxis dataKey="date" stroke="#fff"/>
        <YAxis stroke="#fff"/>
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="price" stroke="#8884d8" strokeWidth={5}/>
        <Line type="monotone" dataKey="predicted" stroke="#82ca9d" strokeDasharray="5 5" strokeWidth={5}/>
        <Area type="monotone" dataKey="upperBound" stroke="none" fill="#82ca9d" fillOpacity={0.2} />
        <Area type="monotone" dataKey="lowerBound" stroke="none" fill="#82ca9d" fillOpacity={0.2} />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default StockChart;
