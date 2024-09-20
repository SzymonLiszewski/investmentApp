import React from 'react';
import '../components/styles/AboutPage.css';
import {Link} from 'react-router-dom';

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
            <h2>Creators</h2>
            <div className="team-section">
                <div className="team-info">
                    <div className="team-member">
                        <h3>Szymon Liszewski</h3>
                        <p>github: <Link to='https://github.com/SzymonLiszewski'>https://github.com/SzymonLiszewski</Link></p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default AboutPage;
