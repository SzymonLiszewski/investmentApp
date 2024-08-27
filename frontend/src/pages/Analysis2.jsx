import "../components/styles/Analysis2.css"
import FundamentalAnalysis from "../components/FundamentalAnalysis"
import AnalysisNavigation from "../components/AnalysisNavigation"
import TechnicalAnalysis from "../components/TechnicalAnalysis";
import {Route, Routes, useParams, Link} from 'react-router-dom';
import ForecastView from "../components/ForecastView";
import React, {useState, useEffect} from "react";
import SearchBar from "../components/SearchBar";
import StockBubble from "../components/StockBubble";
import { Box, Typography } from '@mui/material';


function Analysis2(){

    //example stocks (in future user can chose preffered stocks in front page)
    const stocks = [
        { symbol: 'AAPL', logo: 'https://logo.clearbit.com/apple.com' },
        { symbol: 'NVDA', logo: 'https://logo.clearbit.com/nvidia.com' },
        { symbol: 'MSFT', logo: 'https://logo.clearbit.com/microsoft.com' },
    ];

    const {ticker} = useParams();

    let [CompanyName, setCompanyName] = useState('')
    let [CurrentPrice, setCurrentPrice] = useState(0)
    let [PriceChange, setPriceChange] = useState(0)

    useEffect(()=>{
        getData()
    }, [ticker])

    let getData = async () =>{
        let response = await fetch(`/api/basic/${ticker}/`)
        let data = await response.json()
        //console.log('data:', data)
        setCompanyName(data['Company Name'])
        setCurrentPrice(data['Current Price'])
        setPriceChange(data['Percent Change'])
    }

    
    return (
        <div className="analysis-container">
            <div className="topAnalysisNavigation">
                <Box display="flex" alignItems="center" p={2}>
                    <SearchBar />
                    {stocks.map(stock => (
                        <Link to={`/analysis2/${stock.symbol}/`}>
                        <StockBubble key={stock.symbol} logo={stock.logo} symbol={stock.symbol} />
                        </Link>
                    ))}
                    <Box display="flex" alignItems="center" justifyContent="center"
                        borderRadius="50%"
                        boxShadow={3}
                        p={1}
                        m={1}
                        bgcolor="white"
                        width={48}
                        height={48}
                        sx={{
                            '&:hover': {
                        bgcolor: '#b8b8b8',
                      }
                        }}
                    >
                        <Typography variant="h4" textAlign={"center"}>+</Typography>
                    </Box>
                </Box>
            </div>
           
            <div className="stock-name">
                <img id="logo" src={`https://logo.clearbit.com/${CompanyName.replace(/[.,\/#!$%\^&\*;:{}=\-_`~()]/g, "").split(" ")[0]}.com`}/>
                <h1 id="name">{CompanyName}</h1>
                <h1 id="price">{CurrentPrice.toFixed(2)} USD</h1>
                <p id="priceChange">{PriceChange.toFixed(2)} %</p>
            </div>
            <div className="stock-analysis">
            <AnalysisNavigation/>
            <Routes>
                    <Route path='/' element={<ForecastView ticker={ticker}/>}/>
                    <Route path='/fundamental/' element={<FundamentalAnalysis ticker={ticker}/>}/>
                    <Route path="/technical/" element={<TechnicalAnalysis ticker={ticker}/>}/>
                </Routes>
            </div>
        </div>
    )
}

export default Analysis2