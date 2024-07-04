// src/HomePage.jsx
import React, { Fragment } from 'react';
import './HomePage.css';
import NavBar from './components/navbar';

const App = () => {
    return (
        <Fragment>
            <NavBar/>
            <div className="homepage">
                <header className="homepage-header">
                    <h1>StockSense</h1>
                    <h3>Unlock the power of investment insights</h3>
                </header>
                <main>
                    <section className="features">
                        <div className="feature">
                            <h2>Predict Stock Prices</h2>
                            <p>Use our AI-powered models to predict future stock prices.</p>
                        </div>
                        <div className="feature">
                            <h2>Portfolio Analysis</h2>
                            <p>Analyze the performance of your investment portfolio.</p>
                        </div>
                        <div className="feature">
                            <h2>Market Sentiment</h2>
                            <p>Get insights on market sentiment from news and social media.</p>
                        </div>
                    </section>
                    <section className="cta">
                        <button onClick={() => alert('Get Started!')}>Get Started</button>
                    </section>
                </main>
            </div>
        </Fragment>
            
    );
};

export default App;
