import StockPriceChart from "../components/StockPriceChart"
import "../components/styles/Analysis.css"
import GaugeChart from "../components/GaugeChart"

function Analysis() {
    return (
        <div className="back">
            <div className="grid-container">
                <div className="div1">
                    <div className="div4">
                        <StockPriceChart/>
                    </div>
                    <div className="div5">
                        <p>Our stock price predictions are based on advanced AI and machine learning models. These models analyze historical stock prices, volatility, momentum, and relevant market indices to forecast future prices. By leveraging techniques like LSTM (Long Short-Term Memory) neural networks and SVM (Support Vector Machines), we provide precise and reliable predictions.</p>
                    </div>
                </div>
                <div className="div2">
                    <div className="div6">
                        <p>RSI indicator</p>
                        <GaugeChart value={0.7}/>
                    </div>
                    <div className="div7">
                        <p>MACD indicator</p>
                        <GaugeChart value={0.4}/>
                    </div>
                </div>
                <div className="div3">
                    <StockPriceChart/>
                </div>
            </div>
        </div>
    )
}
export default Analysis