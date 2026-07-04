import '../HomePage.css';
import { Link } from 'react-router-dom';
import HeroSearch from '../components/home/HeroSearch';
import TickerCard from '../components/home/TickerCard';
import HeroForecastChart from '../components/charts/HeroForecastChart';

// Purely illustrative series for the hero preview card; real quotes come from
// the API on the analysis pages.
const HERO_HISTORY = [
  210, 214, 212, 218, 226, 231, 228, 236, 248, 255, 251, 262, 270, 266, 274,
  281, 276, 268, 272, 258, 250, 255, 246, 192, 196, 190, 187, 191, 186, 183,
  188, 186, 189,
];
const HERO_FORECAST = [188, 186.5, 185, 185.5, 184, 183.5];

// Prices and changes are fetched per card from /api/basic/<ticker>/.
const STOCKS = [
  { name: 'Apple', ticker: 'AAPL' },
  { name: 'Google', ticker: 'GOOGL' },
  { name: 'Microsoft', ticker: 'MSFT' },
  { name: 'Tesla', ticker: 'TSLA' },
];

function HomePage() {
  const isDemoMode = import.meta.env.VITE_USE_MOCK_DATA_FETCHER === 'true';

  return (
    <main className="home">
      <section className="hero">
        <div className="hero-copy">
          <h1>
            Keep your investments
            <br />
            under control.
          </h1>
          <p className="hero-lead">
            Portfolio analysis, price forecasts and market sentiment - in one
            clear dashboard. <Link to="/login">Sign in</Link> to unlock
            portfolio insights.
          </p>
          <HeroSearch />
          {isDemoMode && (
            <p className="demo-note">
              Demo version - prices and predictions are for illustrative
              purposes only.
            </p>
          )}
        </div>

        <div className="hero-card">
          <div className="hero-card-head">
            <div>
              <div className="hero-card-company">Your stock</div>
              <div className="hero-card-symbol">Example - illustrative data</div>
            </div>
            <div className="hero-card-quote">
              <div className="hero-card-price">$188.86</div>
              <div className="hero-card-change">−0.34%</div>
            </div>
          </div>
          <div className="hero-card-chart">
            <HeroForecastChart history={HERO_HISTORY} forecast={HERO_FORECAST} />
          </div>
          <div className="hero-card-legend">
            <span>
              <span className="legend-key legend-key-price" />
              Price history
            </span>
            <span>
              <span className="legend-key legend-key-forecast" />
              30-day forecast
            </span>
          </div>
        </div>
      </section>

      <section className="popular">
        <div className="popular-head">
          <h2>Popular stocks</h2>
        </div>
        <div className="ticker-grid">
          {STOCKS.map((stock) => (
            <TickerCard key={stock.ticker} {...stock} />
          ))}
        </div>
      </section>
    </main>
  );
}
export default HomePage;
