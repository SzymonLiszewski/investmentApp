import "./styles/ForecastView.css"
import StockChart from "./StockPriceChart";


function ForecastView({ticker}){
    const today = new Date();
    const threeYearsAgo = new Date();
    threeYearsAgo.setFullYear(today.getFullYear() - 1);
    const todayString = today.toISOString().split('T')[0];
    console.log(todayString)
    const threeYearsAgoString = threeYearsAgo.toISOString().split('T')[0];
    return (
        <div className="ForecastContainer">
            <div className="chart">
                <StockChart startDate={threeYearsAgoString} endDate={todayString} ticker={ticker} predictedDays={30}/>
            </div>
            <div className="description">
                <p>Our stock price predictions are based on advanced AI and machine learning models. These models analyze historical stock prices, volatility, momentum, and relevant market indices to forecast future prices. By leveraging techniques like LSTM (Long Short-Term Memory) neural networks, regression and Seasonal Auto-Regressive Integrated Moving Average, we provide precise and reliable predictions.</p>
            </div>
        </div>
    )
}
export default ForecastView;