import React from 'react';
import '../components/styles/AboutPage.css';

const AboutPage = () => {
    return (
        <div className="about-container">
            <h1>About Investment Analysis Tool</h1>
            <div className="app-description">
                <p>
                    The Investment Analysis Tool is designed to help you analyze your investment portfolio using advanced techniques. 
                    This includes fundamental and technical analysis, predictions based on regression, LSTM networks, and SARIMA models.
                </p>
            </div>
            <h2>Features</h2>
            <ul>
                <li>Portfolio analysis with key indicators like Sharpe and Sortino ratios.</li>
                <li>Integration with popular brokers for automatic portfolio updates.</li>
                <li>Sentiment analysis of news related to your investments.</li>
                <li>Advanced forecasting techniques for better investment decisions.</li>
                <li>Access to IPO calendars and market news.</li>
            </ul>
            <h2>Source code</h2>
            <p className="source-code-text">
                Check out the source code: <a href="https://github.com/SzymonLiszewski/investmentApp" target="_blank" rel="noopener noreferrer">GitHub repository</a>
            </p>
            <h2>Attributions</h2>
            <p className="attributions-text">
                Logos provided by <a href="https://logo.dev" target="_blank" rel="noopener noreferrer">Logo.dev</a>.
            </p>
        </div>
    );
};

export default AboutPage;
