import "./styles/FundamentalAnalysis.css"
import DividendChart from "./DividendChart"
import RevenueChart from "./RevenueChart"
function FundamentalAnalysis(){
    return(
        <div className="bx">
            <div className="FundamentalAnalysisContainer">
                <div className="FundamentalContainer" id="MarketCap"> 
                    <h3>Market Capitalization</h3>
                    <h1>40.5B USDT</h1>
                </div>
                <div className="FundamentalContainer" id="pe"> 
                     <h3>P/E ratio</h3>
                     <h1>34.45x</h1>
                </div>
                <div className="FundamentalContainer" id="ps"> 
                    <h3>P/S ratio</h3>
                    <h1>8.985x</h1>
                </div>
                <div className="FundamentalContainer" id="eps">
                    <h3>Earnings Per Share</h3>
                    <h1>6.46 USD</h1> 
                </div>
                <div className="FundamentalContainer" id="Dividends">
                    <DividendChart/> 
                </div>
                <div className="FundamentalContainer" id="Earnings"> 
                    <RevenueChart/>
                </div>
            </div>
            </div>
    )
}

export default FundamentalAnalysis