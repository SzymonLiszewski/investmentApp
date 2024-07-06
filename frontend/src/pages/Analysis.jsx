import StockPriceChart from "../components/StockPriceChart"
import "../components/styles/Analysis.css"

function Analysis() {
    return (
        <div className="grid-container">
            <div className="grid-item">
                <h1>Stock Price Chart</h1>
            </div>
            <div className="grid-item">
                <StockPriceChart />
            </div>
            <div className="grid-item">
                <StockPriceChart />
            </div>
        </div>
    )
}
export default Analysis