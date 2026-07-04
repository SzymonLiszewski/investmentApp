/* eslint-disable react/prop-types */
import "./styles/TechnicalAnalysis.css"
import { useState, useEffect } from "react";
import { FaQuestionCircle } from 'react-icons/fa';
import { Tooltip } from 'react-tooltip';
import { formatNumberWithSuffix } from '../utils/format';

function StatLabel({ children, tip }) {
    return (
        <div className="indicator-label">
            {children}
            <FaQuestionCircle
                className="questionCircle"
                data-tooltip-id="indicator-tip"
                data-tooltip-content={tip}
            />
        </div>
    );
}

function TechnicalAnalysis({ ticker }) {
    const [rsi, setRsi] = useState(0);
    const [sma50, setSma50] = useState(0);
    const [sma200, setSma200] = useState(0);
    const [macd, setMacd] = useState(0);
    const [bollingerHigh, setBollingerHigh] = useState(0);
    const [bollingerLow, setBollingerLow] = useState(0);

    useEffect(() => {
        const getData = async () => {
            const response = await fetch(`/api/technical/${ticker}/`);
            const data = await response.json();
            setSma50(data['SMA_50']);
            setSma200(data['SMA_200']);
            setRsi(data['RSI']);
            setMacd(data['MACD']);
            setBollingerHigh(data['Bollinger_High']);
            setBollingerLow(data['Bollinger_Low']);
        };
        getData();
    }, [ticker]);

    return (
        <div className="technical-view">
            <div className="indicator-grid indicator-grid-3">
                <div className="indicator-card">
                    <StatLabel tip="The total number of shares traded during a given period. High volume often indicates strong investor interest and can confirm the strength of a price move, while low volume might suggest a lack of conviction or weak price movements.">
                        Volume
                    </StatLabel>
                    <div className="indicator-value">{formatNumberWithSuffix(sma200)}</div>
                </div>
                <div className="indicator-card">
                    <StatLabel tip="Upper Band: Represents a level of high volatility. When the price approaches or exceeds this band, it may indicate an overbought condition. Lower Band: Represents a level of low volatility. When the price approaches or drops below this band, it may suggest an oversold condition.">
                        Bollinger bands
                    </StatLabel>
                    <div className="indicator-pair">
                        <div>
                            <div className="indicator-sublabel">Upper</div>
                            <div className="indicator-value">{(Number(bollingerHigh) || 0).toFixed(2)}</div>
                        </div>
                        <div>
                            <div className="indicator-sublabel">Lower</div>
                            <div className="indicator-value">{(Number(bollingerLow) || 0).toFixed(2)}</div>
                        </div>
                    </div>
                </div>
                <div className="indicator-card">
                    <StatLabel tip="Short-Term Moving Average: Calculates the average price over a short period. It helps identify recent trends and short-term momentum. Long-Term Moving Average: Calculates the average price over a longer period. It smooths out long-term trends and provides insights into the overall direction of the market.">
                        Moving average
                    </StatLabel>
                    <div className="indicator-pair">
                        <div>
                            <div className="indicator-sublabel">50-day</div>
                            <div className="indicator-value">{(Number(sma50) || 0).toFixed(2)}</div>
                        </div>
                        <div>
                            <div className="indicator-sublabel">200-day</div>
                            <div className="indicator-value">{(Number(sma200) || 0).toFixed(2)}</div>
                        </div>
                    </div>
                </div>
                <div className="indicator-card">
                    <StatLabel tip="A high value indicates strong bullish momentum (consider buying or holding), while a low value signals strong bearish momentum (consider selling or avoiding).">
                        MACD
                    </StatLabel>
                    <div className="indicator-value">{(Number(macd) || 0).toFixed(2)}</div>
                </div>
                <div className="indicator-card">
                    <StatLabel tip="Measures the speed and change of price movements on a scale from 0 to 100. An RSI above 70 can indicate an overbought condition, while an RSI below 30 might suggest an oversold condition.">
                        RSI
                    </StatLabel>
                    <div className="indicator-value">{(Number(rsi) || 0).toFixed(2)}</div>
                </div>
            </div>

            <Tooltip id="indicator-tip" className="custom-tooltip" />
        </div>
    )
}

export default TechnicalAnalysis
