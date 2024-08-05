import "../components/styles/Portfolio.css"
import UserEarningsChart from "../components/portfolio/UserEarningsChart"
import UserStocksChart from "../components/portfolio/UserStocksChart"
import IndicatorsGaugeChart from "../components/portfolio/IndicatorsGaugeChart"

function Portfolio(){
    const sharpeRatio = 1.5;
    const sortinoRatio = 1.2;
    const alpha = 0.05;

    //  value interpretation
    const interpretSharpe = sharpeRatio < 1 ? "Low return relative to its risk."
    : (sharpeRatio >= 1 && sharpeRatio < 2) ? "Decent return for its risk."
    : "Optimal return for its risk.";

    const interpretSortino = sortinoRatio < 0.5 ? "High downside risk relative to its return."
    : (sortinoRatio >= 0.5 && sortinoRatio < 1) ? "Moderate downside risk."
    : "Low downside risk relative to its return.";

    const interpretAlpha = alpha < 0 ? "Underperforms compared to the benchmark after adjusting for market risk."
    : (alpha >= 0 && alpha < 0.02) ? "Performs similarly to the benchmark after adjusting for market risk."
    : "Outperforms the benchmark after adjusting for market risk.";

    return (
        <div className="portfolio">
            <div className="portfolioDiv" id="return">
                <h1><UserEarningsChart/></h1>
            </div>
            <div className="portfolioDiv" id="composition">
                <h1><UserStocksChart/></h1>
            </div>
            <div className="portfolioDiv" id="indicators">
                <h3>Sharpe Ratio</h3>
                <IndicatorsGaugeChart data={sharpeRatio} range={[-1, 3]} name="Sharpe Ratio" interpretation={interpretSharpe}/>

                <h3>Sortino Ratio</h3>
                <IndicatorsGaugeChart data={sortinoRatio} range={[-0.5, 2]} name="Sortino Ratio" interpretation={interpretSortino}/>

                <h3>Alpha</h3>
                <IndicatorsGaugeChart data={alpha} range={[-0.05, 0.05]} name="Alpha" interpretation={interpretAlpha}/>
            </div>
        </div>
    )
}
    

export default Portfolio