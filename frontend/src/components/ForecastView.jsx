/* eslint-disable react/prop-types */
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

const RANGES = [
    { label: '1M', months: 1 },
    { label: '6M', months: 6 },
    { label: '1Y', months: 12 },
    { label: 'All', months: 60 },
];

function ForecastView({ ticker }) {
    const [model, setModel] = useState("regression");
    const [range, setRange] = useState('1Y');

    const today = new Date();
    const start = new Date();
    const months = RANGES.find((r) => r.label === range).months;
    start.setMonth(today.getMonth() - months);
    const todayString = today.toISOString().split('T')[0];
    const startString = start.toISOString().split('T')[0];

    return (
        <div className="forecast-grid">
            <div className="chart-card">
                <div className="chart-card-head">
                    <div className="chart-card-title">Price &amp; 30-day forecast</div>
                    <div className="range-group" role="group" aria-label="History range">
                        {RANGES.map((r) => (
                            <button
                                key={r.label}
                                type="button"
                                className={`range-btn${range === r.label ? ' active' : ''}`}
                                onClick={() => setRange(r.label)}
                            >
                                {r.label}
                            </button>
                        ))}
                    </div>
                </div>
                <StockChart
                    startDate={startString}
                    endDate={todayString}
                    ticker={ticker}
                    model={model}
                />
                <div className="chart-legend">
                    <span>
                        <span className="legend-key legend-key-price" />
                        Price
                    </span>
                    <span>
                        <span className="legend-key legend-key-forecast" />
                        Forecast ({MODELS[model].name})
                    </span>
                    {model === 'sarima' && (
                        <span>
                            <span className="legend-key legend-key-band" />
                            Confidence band
                        </span>
                    )}
                </div>
            </div>

            <div className="forecast-side">
                <div className="model-card">
                    <div className="model-card-title">Forecast model</div>
                    <div className="model-options" role="group" aria-label="Forecast model">
                        {Object.entries(MODELS).map(([value, { name }]) => (
                            <button
                                key={value}
                                type="button"
                                className={`model-btn${model === value ? ' active' : ''}`}
                                onClick={() => setModel(value)}
                            >
                                {name}
                            </button>
                        ))}
                    </div>
                    <p className="model-desc">{MODELS[model].description}</p>
                </div>

                <div className="forecast-disclaimer">
                    Forecasts are statistical estimates based on historical data and are
                    not financial advice.
                </div>
            </div>
        </div>
    )
}
export default ForecastView;
