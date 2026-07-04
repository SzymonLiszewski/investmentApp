/* eslint-disable react/prop-types */
import "../components/styles/Analysis2.css"
import FundamentalAnalysis from "../components/FundamentalAnalysis"
import AnalysisNavigation from "../components/AnalysisNavigation"
import TechnicalAnalysis from "../components/TechnicalAnalysis";
import { Route, Routes, useParams, Link } from 'react-router-dom';
import ForecastView from "../components/ForecastView";
import { useState, useEffect, useRef } from "react";
import HeroSearch from "../components/home/HeroSearch";

// Example watchlist (in future the user can choose preferred stocks)
const WATCHLIST = [
    { symbol: 'AAPL', logo: 'https://img.logo.dev/apple.com?token=pk_F06zMPFbR5yUJmwRi1Y-Jg' },
    { symbol: 'NVDA', logo: 'https://img.logo.dev/nvidia.com?token=pk_F06zMPFbR5yUJmwRi1Y-Jg' },
    { symbol: 'MSFT', logo: 'https://img.logo.dev/microsoft.com?token=pk_F06zMPFbR5yUJmwRi1Y-Jg' },
];

const isNumeric = (value) =>
    value !== null && value !== 'N/A' && !isNaN(Number(value));

// Company logo inside a watchlist chip; falls back to the ticker initial.
function ChipLogo({ symbol, logo }) {
    const [failed, setFailed] = useState(false);
    if (!logo || failed) {
        return <span className="watch-chip-dot" aria-hidden="true">{symbol[0]}</span>;
    }
    return (
        <img
            className="watch-chip-logo"
            src={logo}
            alt=""
            onError={() => setFailed(true)}
        />
    );
}

function Analysis2() {
    const { ticker } = useParams();

    const [companyName, setCompanyName] = useState('');
    const [currentPrice, setCurrentPrice] = useState(null);
    const [priceChange, setPriceChange] = useState(null);
    const [logoFailed, setLogoFailed] = useState(false);
    const searchInputRef = useRef(null);

    useEffect(() => {
        const getData = async () => {
            const response = await fetch(`/api/basic/${ticker}/`);
            const data = await response.json();
            setCompanyName(data['Company Name']);
            setCurrentPrice(data['Current Price']);
            setPriceChange(data['Percent Change']);
        };
        setLogoFailed(false);
        getData();
    }, [ticker]);

    const symbol = (ticker || '').toUpperCase();
    const changeUp = isNumeric(priceChange) && Number(priceChange) >= 0;
    // logo.dev for the selected stock too: exact URL when it's a watchlist
    // ticker, otherwise derive the domain from the company name.
    const watchEntry = WATCHLIST.find((stock) => stock.symbol === symbol);
    const logoUrl = watchEntry
        ? watchEntry.logo
        : companyName
            ? `https://img.logo.dev/${companyName.replace(/[.,/#!$%^&*;:{}=\-_`~()]/g, '').split(' ')[0]}.com?token=pk_F06zMPFbR5yUJmwRi1Y-Jg`
            : null;

    return (
        <div className="stock-page">
            <div className="watchlist-row">
                <HeroSearch
                    variant="compact"
                    placeholder="Find your stock…"
                    inputRef={searchInputRef}
                />
                {WATCHLIST.map((stock) => (
                    <Link
                        key={stock.symbol}
                        to={`/analysis2/${stock.symbol}/`}
                        className={`watch-chip${stock.symbol === symbol ? ' active' : ''}`}
                    >
                        <ChipLogo symbol={stock.symbol} logo={stock.logo} />
                        {stock.symbol}
                    </Link>
                ))}
                <button
                    type="button"
                    className="watch-add"
                    aria-label="Find a stock to add"
                    onClick={() => searchInputRef.current && searchInputRef.current.focus()}
                >
                    +
                </button>
            </div>

            <div className="stock-head">
                <div className="stock-identity">
                    <div className="stock-logo">
                        {logoUrl && !logoFailed ? (
                            <img src={logoUrl} alt="" onError={() => setLogoFailed(true)} />
                        ) : (
                            <span>{symbol ? symbol[0] : '?'}</span>
                        )}
                    </div>
                    <div>
                        <h1 className="stock-name">{companyName || symbol}</h1>
                        <div className="stock-sub">{symbol}</div>
                    </div>
                </div>
                <div className="stock-quote">
                    <div className="stock-price">
                        {isNumeric(currentPrice) ? `$${Number(currentPrice).toFixed(2)}` : 'N/A'}
                    </div>
                    {isNumeric(priceChange) && (
                        <div className={`stock-change ${changeUp ? 'up' : 'down'}`}>
                            {changeUp ? '+' : '−'}{Math.abs(Number(priceChange)).toFixed(2)}% today
                        </div>
                    )}
                </div>
            </div>

            <AnalysisNavigation ticker={symbol} />
            <Routes>
                <Route path='/' element={<ForecastView ticker={ticker} />} />
                <Route path='/fundamental/' element={<FundamentalAnalysis ticker={ticker} />} />
                <Route path='/technical/' element={<TechnicalAnalysis ticker={ticker} />} />
            </Routes>
        </div>
    )
}

export default Analysis2
