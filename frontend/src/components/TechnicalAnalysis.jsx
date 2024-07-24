import "./styles/TechnicalAnalysis.css"
import DividendChart from "./DividendChart"
import RevenueChart from "./RevenueChart"
import React, {useState, useEffect} from "react";

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
        let response = await fetch(`/api/technical/${ticker}/`)
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
                    <h3>Volume</h3>
                    <h1>{formatNumberWithSuffix(SMA200)}</h1>
                </div>
                <div className="TechnicalContainer" id="Boelinger"> 
                     <h3>Boelinger Bands</h3>
                     <div className="IndicatorInline">
                        <h1>{Bollinger_High.toFixed(2)}</h1>
                        <h1>{Bollinger_Low.toFixed(2)}</h1>
                     </div>
                </div>
                <div className="TechnicalContainer" id="ma"> 
                    <h3>moving average</h3>
                    <div className="IndicatorInline">
                        <h1>{SMA50.toFixed(2)}</h1>
                        <h1>{SMA200.toFixed(2)}</h1>
                    </div>
                </div>
                <div className="TechnicalContainer" id="macd">
                    <h3>MACD</h3>
                    <h1>{SMA50}</h1> 
                </div>
                <div className="TechnicalContainer" id="RSI">
                    <h3>RSi</h3>
                    <h1>{RSI.toFixed(2)}</h1> 
                </div>
                
            </div>
    )
}

export default TechnicalAnalysis