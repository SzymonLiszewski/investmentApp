import { useState } from "react";
import "./styles/ForecastView.css"
import StockChart from "./StockPriceChart";

const MODELS = {
    regression: {
        name: "Regression",
        description: "A linear regression model retrained every night on S&P 500 index history. " +
            "Instead of raw prices it learns from scale-free signals — daily and multi-day returns, " +
            "trend, volatility and technical indicators such as RSI and MACD — and predicts the next " +
            "day's percentage change. The 30-day forecast is built by applying the model to this " +
            "stock's own indicators and rolling the prediction forward one day at a time.",
    },
    sarima: {
        name: "SARIMA",
        description: "A Seasonal Auto-Regressive Integrated Moving Average model fitted to this " +
            "stock's own price history. It captures the trend and recurring seasonal patterns in the " +
            "series to project prices 30 days ahead. Forecasts for the most popular stocks are " +
            "precomputed every night; for other tickers the model is fitted on demand, which can " +
            "take a moment longer.",
    },
};

function ForecastView({ticker}){
    const [model, setModel] = useState("regression");
    const today = new Date();
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(today.getFullYear() - 1);
    const todayString = today.toISOString().split('T')[0];
    const oneYearAgoString = oneYearAgo.toISOString().split('T')[0];
    return (
        <div className="ForecastContainer">
            <div className="chart">
                <StockChart startDate={oneYearAgoString} endDate={todayString} ticker={ticker} model={model} predictedDays={30}/>
            </div>
            <div className="description">
                <div className="model-select">
                    <label htmlFor="forecast-model">Forecast model</label>
                    <select
                        id="forecast-model"
                        value={model}
                        onChange={(e) => setModel(e.target.value)}
                    >
                        {Object.entries(MODELS).map(([value, {name}]) => (
                            <option key={value} value={value}>{name}</option>
                        ))}
                    </select>
                </div>
                <h3>{MODELS[model].name}</h3>
                <p>{MODELS[model].description}</p>
                <p className="disclaimer">
                    Forecasts are statistical estimates based on historical data and are
                    not financial advice.
                </p>
            </div>
        </div>
    )
}
export default ForecastView;
