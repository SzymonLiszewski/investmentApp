import "./styles/ForecastView.css"
import StockChart from "./StockPriceChart";
function ForecastView(){
    return (
        <div className="ForecastContainer">
            <div className="chart">
                <StockChart/>
            </div>
            <div className="description">
                <p>Our stock price predictions are based on advanced AI and machine learning models. These models analyze historical stock prices, volatility, momentum, and relevant market indices to forecast future prices. By leveraging techniques like LSTM (Long Short-Term Memory) neural networks and SVM (Support Vector Machines), we provide precise and reliable predictions.</p>
            </div>
        </div>
    )
}
export default ForecastView;