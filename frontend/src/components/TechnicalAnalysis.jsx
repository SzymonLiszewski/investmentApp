import "./styles/TechnicalAnalysis.css"
import DividendChart from "./DividendChart"
import RevenueChart from "./RevenueChart"
import React, {useState, useEffect} from "react";
import { FaQuestionCircle } from 'react-icons/fa';
import {Tooltip } from 'react-tooltip';

function formatNumberWithSuffix(number) {
    const suffixes = ["", "K", "M", "B", "T"]; 

    let suffixIndex = 0;
    while (number >= 1000 && suffixIndex < suffixes.length - 1) {
        number /= 1000;
        suffixIndex++;
    }

    return number.toFixed(2) + suffixes[suffixIndex];
}

function TechnicalAnalysis({ticker}){
    let [RSI, setRSI] = useState(0)
    let [SMA50, setSMA50] = useState(0)
    let [SMA200, setSMA200] = useState(0)
    let [MACD, setMACD] = useState(0)
    let [MACD_Signal, setMACD_Signal] = useState(0)
    let [Bollinger_High, setBollinger_High] = useState(0)
    let [Bollinger_Low, setBollinger_Low] = useState(0)
    let [Price, setPrice] = useState(0)

    useEffect(()=>{
        getData()
    },[])
    
    let getData = async () =>{
        let response = await fetch(`/api/analytics/technical/${ticker}/`)
        let data = await response.json()
        setSMA50(data['SMA_50'])
        setSMA200(data['SMA_200'])
        setRSI(data['RSI'])
        setMACD(data['MACD'])
        setMACD_Signal(data['MACD_Signal'])
        setBollinger_High(data['Bollinger_High'])
        setBollinger_Low(data['Bollinger_Low'])
        setPrice(data['Current Price'])
        console.log('data2:',data)
    }

    return(
            <div className="TechnicalAnalysisContainer">
                <div className="TechnicalContainer" id="Volume"> 
                    <h3>Volume
                     <FaQuestionCircle className="questionCircle" data-tooltip-id="marketCap" data-tooltip-content=" The total number of shares traded during a given period. High volume often indicates strong investor interest and can confirm the strength of a price move, while low volume might suggest a lack of conviction or weak price movements."/>
                     <Tooltip id="marketCap" className="custom-tooltip"/>
                    </h3>
                    <h1>{formatNumberWithSuffix(SMA200)}</h1>
                </div>
                <div className="TechnicalContainer" id="Boelinger"> 
                     <h3>Boelinger Bands
                     <FaQuestionCircle className="questionCircle" data-tooltip-id="marketCap" data-tooltip-content="Upper Band: Represents a level of high volatility. When the price approaches or exceeds this band, it may indicate an overbought condition.
 Lower Band: Represents a level of low volatility. When the price approaches or drops below this band, it may suggest an oversold condition."/>
                     <Tooltip id="marketCap" className="custom-tooltip"/>
                     </h3>
                     <div className="IndicatorInline">
                        <h1>{Bollinger_High.toFixed(2)}</h1>
                        <h1>{Bollinger_Low.toFixed(2)}</h1>
                     </div>
                </div>
                <div className="TechnicalContainer" id="ma"> 
                    <h3>moving average
                    <FaQuestionCircle className="questionCircle" data-tooltip-id="marketCap" data-tooltip-content="Short-Term Moving Average: Calculates the average price over a short period. It helps identify recent trends and short-term momentum.
Long-Term Moving Average: Calculates the average price over a longer period. It smooths out long-term trends and provides insights into the overall direction of the market."/>
                    <Tooltip id="marketCap" className="custom-tooltip"/>
                    </h3>
                    <div className="IndicatorInline">
                        <h1>{SMA50.toFixed(2)}</h1>
                        <h1>{SMA200.toFixed(2)}</h1>
                    </div>
                </div>
                <div className="TechnicalContainer" id="macd">
                    <h3>MACD
                    <FaQuestionCircle className="questionCircle" data-tooltip-id="marketCap" data-tooltip-content="A high value indicates strong bullish momentum (consider buying or holding), while a low value signals strong bearish momentum (consider selling or avoiding)."/>
                    <Tooltip id="marketCap" className="custom-tooltip"/>
                    </h3>
                    <h1>{SMA50}</h1> 
                </div>
                <div className="TechnicalContainer" id="RSI">
                    <h3>RSi
                    <FaQuestionCircle className="questionCircle" data-tooltip-id="marketCap" data-tooltip-content="Measures the speed and change of price movements on a scale from 0 to 100. An RSI above 70 can indicate an overbought condition, while an RSI below 30 might suggest an oversold condition."/>
                    <Tooltip id="marketCap" className="custom-tooltip"/>
                    </h3>
                    <h1>{RSI.toFixed(2)}</h1> 
                </div>
                
            </div>
    )
}

export default TechnicalAnalysis