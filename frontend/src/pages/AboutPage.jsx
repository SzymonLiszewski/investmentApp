import '../components/styles/AboutPage.css';

const FEATURES = [
    {
        num: '01',
        title: 'Portfolio analysis',
        body: 'Key risk-adjusted indicators like Sharpe and Sortino ratios, explained in plain language.',
    },
    {
        num: '02',
        title: 'News sentiment',
        body: 'Sentiment analysis of news related to the stocks you actually hold.',
    },
    {
        num: '03',
        title: 'Price forecasting',
        body: 'SARIMA and regression models project prices 30 days ahead.',
    },
    {
        num: '04',
        title: 'Market calendar',
        body: 'IPO dates and earnings announcements for the companies you follow.',
    },
];

const AboutPage = () => {
    return (
        <main className="about-page">
            <div className="about-intro">
                <div className="about-eyebrow">About Captrivio</div>
                <h1>
                    Investment analysis,
                    <br />
                    without the noise.
                </h1>
                <p>
                    Captrivio helps you analyze your portfolio with the techniques
                    professionals use — fundamental and technical analysis, plus price
                    forecasts from regression and SARIMA models — presented in plain
                    language.
                </p>
            </div>

            <div className="about-features">
                <h2>What you get</h2>
                <div className="feature-grid">
                    {FEATURES.map((feature) => (
                        <div key={feature.num} className="feature-card">
                            <div className="feature-num">{feature.num}</div>
                            <div className="feature-title">{feature.title}</div>
                            <div className="feature-body">{feature.body}</div>
                        </div>
                    ))}
                </div>
            </div>

            <div className="about-cards">
                <div className="about-card-dark">
                    <div className="about-card-title">Open source</div>
                    <p>
                        Captrivio is built in the open. Browse the code, report issues,
                        or contribute.
                    </p>
                    <a
                        href="https://github.com/SzymonLiszewski/investmentApp"
                        target="_blank"
                        rel="noopener noreferrer"
                    >
                        View on GitHub →
                    </a>
                </div>
                <div className="about-card-soft">
                    <div className="about-card-title">Demo version</div>
                    <p>
                        Market data — prices, news and calendar events — is for
                        illustrative purposes only and is not financial advice.
                        <br />
                        Company logos provided by{' '}
                        <a
                            href="https://logo.dev"
                            target="_blank"
                            rel="noopener noreferrer"
                        >
                            Logo.dev
                        </a>
                        .
                    </p>
                </div>
            </div>
        </main>
    );
};

export default AboutPage;
