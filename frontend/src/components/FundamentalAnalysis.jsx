import "./styles/FundamentalAnalysis.css"
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

function FundamentalAnalysis({ticker}){
    let [MarketCap, setMarketCap] = useState(0)
    let [PERatio, setPERatio] = useState(0)
    let [PSRatio, setPSRatio] = useState(0)
    let [EPS, setEPS] = useState(0)
    let [Revenue, setRevenue] = useState([])
    let [Dividends, setDividends] = useState([])

    useEffect(()=>{
        getData()
    },[])
    
    let getData = async () =>{
        let response = await fetch(`/api/fundamental/${ticker}/`)
        let data = await response.json()
        setMarketCap(data['Market Cap'])
        setPSRatio(data['P/S Ratio'])
        setPERatio(data['P/E Ratio'])
        setEPS(data['EPS'])
        setRevenue(data['Revenue History'])
        setDividends(data['Dividend History'])
        console.log('data2:',data)
    }

    return(
        <div className="bx">
            <div className="FundamentalAnalysisContainer">
                <div className="FundamentalContainer" id="MarketCap"> 
                    <h3>Market Capitalization</h3>
                    <h1>{formatNumberWithSuffix(MarketCap)}</h1>
                </div>
                <div className="FundamentalContainer" id="pe"> 
                     <h3>P/E ratio</h3>
                     <h1>{PERatio.toFixed(2)}x</h1>
                </div>
                <div className="FundamentalContainer" id="ps"> 
                    <h3>P/S ratio</h3>
                    <h1>{PSRatio.toFixed(2)}x</h1>
                </div>
                <div className="FundamentalContainer" id="eps">
                    <h3>Earnings Per Share</h3>
                    <h1>{EPS} USD</h1> 
                </div>
                <div className="FundamentalContainer" id="Dividends">
                    <h3>Dividends</h3>
                    <DividendChart data={Dividends}/> 
                </div>
                <div className="FundamentalContainer" id="Earnings"> 
                    <h3>Revenue</h3>
                    <RevenueChart/>
                </div>
            </div>
            </div>
    )
}

export default FundamentalAnalysis