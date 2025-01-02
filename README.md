# StockSense

StockSense is a hobby project aimed at providing stock market data, designed for finance enthusiasts and investors. The application allows you to track stock quotes, analyze key financial indicators, make simple predictions, access news with sentiment analysis, and connect with XTB for basic portfolio analysis.
You can access the live version of the application hosted on AWS EC2 here: http://ec2-54-175-92-99.compute-1.amazonaws.com/

## Features

- **Real-time quotes**:
  Fetch the latest data on stocks and indices.

- **Basic technical and fundamental indicators**:
  Analyze data such as moving averages, RSI, P/E, and Dividend Yield.

- **Simple predictions**:
  Generate straightforward forecasts based on historical trends and basic algorithms.

- **News and sentiment analysis**:
  Access relevant financial news and evaluate sentiment to inform decision-making.

- **Portfolio analysis with XTB integration**:
  Connect your XTB account to analyze your investment portfolio.

## Technologies

The repository contains two branches:

**Main branch**: Includes the full version of the application with all features.

**Deploy branch**: Optimized for deployment, including Docker Compose configuration and simplified analysis.

The project is built using:

- **Backend**: Python (django)
- **Data retrieval**: External APIs (Alpha Vantage, Yahoo Finance, newsdata, XTB API)
- **Frontend**: React.js
- **Database**: SQLite

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/SzymonLiszewski/investmentApp
   cd investmentApp
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables for API keys:

    Linux:
     ```bash
     export ALPHAVANTAGE_API_KEY=your_api_key
     export NEWSDATA_API_KEY=your_api_key
     ```
     Windows:
     ```bash
     set ALPHAVANTAGE_API_KEY=your_api_key
     set NEWSDATA_API_KEY=your_api_key
     ```

1. Run the application:
   ```bash
   cd backend
   python manage.py runserver
   ```

2. Navigate to the frontend directory and start it:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```
3. Open the application in your browser (default: ` http://localhost:5173/`).


## Requirements

- Python 3.8+
- API keys for fetching stock market data (Alpha Vantage, newsdata)
- Node.js and npm for running the frontend

## Contributions

The project is open to contributions. If you have ideas for new features or improvements, open an issue or submit a pull request!

## License

This project is available under the MIT License. See the [LICENSE](LICENSE) file for details.



