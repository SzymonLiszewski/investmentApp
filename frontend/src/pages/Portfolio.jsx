import "../components/styles/Portfolio.css"
import UserEarningsChart from "../components/portfolio/UserEarningsChart"
import UserStocksChart from "../components/portfolio/UserStocksChart"
import AssetClassAllocationChart from "../components/portfolio/AssetClassAllocationChart"
import IndicatorsGaugeChart from "../components/portfolio/IndicatorsGaugeChart"
import CurrencySelector from "../components/portfolio/CurrencySelector"
import ActivePositionsTable from "../components/portfolio/ActivePositionsTable"
import { Fragment, useEffect, useState } from 'react';
import { Link } from "react-router-dom"
import apiClient from "../api/client"

function Portfolio(){
    const [sharpeRatio, setSharpeRatio] = useState(-100)
    const [sortinoRatio, setSortinoRatio] = useState(-100)
    const [alpha, setAlpha] = useState(-100)
    const [valueHistory, setValueHistory] = useState([])
    const [selectedCurrency, setSelectedCurrency] = useState(() => {
        return localStorage.getItem('preferredCurrency') || 'PLN';
    })

    // Fetch portfolio value history from snapshot-based endpoint
    useEffect(() => {
        const fetchValueHistory = async () => {
            try {
                const currency = selectedCurrency || 'PLN';
                const response = await apiClient.get(
                    `api/portfolio/value-history/?currency=${currency}&rebuild=true`
                );
                setValueHistory(response.data);
            } catch (error) {
                console.error('Error fetching value history:', error);
            }
        };
        fetchValueHistory();
    }, [selectedCurrency]);

    // Fetch indicators (Sharpe, Sortino, Alpha) from snapshot-based backend; use selected currency
    useEffect(() => {
        const fetchIndicators = async () => {
            try {
                const currency = selectedCurrency || 'PLN';
                const response = await apiClient.get('api/portfolio/indicators/', {
                    params: { currency },
                });
                const data = response.data;
                setSharpeRatio(data.sharpe);
                setSortinoRatio(data.sortino);
                setAlpha(data.alpha);
            } catch (error) {
                console.error('Error fetching indicators:', error);
            }
        };
        fetchIndicators();
    }, [selectedCurrency]);
    //  value interpretation
    const interpretSharpe = sharpeRatio < 1 ? "Low return relative to its risk."
    : (sharpeRatio >= 1 && sharpeRatio < 2) ? "Decent return for its risk."
    : "Optimal return for its risk.";

    const interpretSortino = sortinoRatio < 0.5 ? "High downside risk relative to its return."
    : (sortinoRatio >= 0.5 && sortinoRatio < 1) ? "Moderate downside risk."
    : "Low downside risk relative to its return.";

    const interpretAlpha = alpha < 0 ? "Underperforms compared to the benchmark"
    : (alpha >= 0 && alpha < 0.02) ? "Performs similarly to the benchmark"
    : "Outperforms the benchmark";

    const handleCurrencyChange = (currency) => {
        setSelectedCurrency(currency);
    };

    return (
        <Fragment>
        <div style={{display: 'flex', gap: '10px', marginLeft: '5vw', marginRight: '5vw', marginBottom: '10px', alignItems: 'center', justifyContent: 'space-between'}}>
            <div style={{display: 'flex', gap: '10px'}}>
                <button className="connectedAccountsButton"><Link to="/connectAccounts" style={{color: "#000000"}}>connected accounts</Link></button>
                <button className="connectedAccountsButton"><Link to="/addStock" style={{color: "#000000"}}>add assets</Link></button>
            </div>
            <CurrencySelector onCurrencyChange={handleCurrencyChange} />
        </div>
        <div className="portfolio">
            <div className="portfolioDiv" id="return">
                <h1><UserEarningsChart data={valueHistory} currency={selectedCurrency} /></h1>
            </div>
            <div className="portfolioDiv" id="composition">
                <UserStocksChart currency={selectedCurrency} />
            </div>
            <div className="portfolioDiv" id="compositionByClass">
                <AssetClassAllocationChart currency={selectedCurrency} />
            </div>
            <div className="portfolioDiv" id="indicators">
                <div className="indicatorsRow">
                    <IndicatorsGaugeChart data={sharpeRatio} range={[-1, 3]} name="Sharpe Ratio" interpretation={interpretSharpe}/>
                    <IndicatorsGaugeChart data={sortinoRatio} range={[-0.5, 2]} name="Sortino Ratio" interpretation={interpretSortino}/>
                    <IndicatorsGaugeChart data={alpha} range={[-0.2, 0.2]} name="Alpha" interpretation={interpretAlpha}/>
                </div>
            </div>
            <div className="portfolioDiv" id="positions">
                <ActivePositionsTable currency={selectedCurrency} />
            </div>
        </div>
        </Fragment>
    )
}
    

export default Portfolio