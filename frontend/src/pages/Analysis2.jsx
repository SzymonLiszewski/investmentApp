import "../components/styles/Analysis2.css"
import FundamentalAnalysis from "../components/FundamentalAnalysis"
import AnalysisNavigation from "../components/AnalysisNavigation"
import {Route, Routes} from 'react-router-dom';
import ForecastView from "../components/ForecastView";
import React, {useState, useEffect} from "react";

function Analysis2(){

    let ticker = "AAPL"

    let [CompanyName, setCompanyName] = useState('')
    let [CurrentPrice, setCurrentPrice] = useState()
    let [PriceChange, setPriceChange] = useState()

    useEffect(()=>{
        getData()
    }, [])

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
            <div className="stock-name">
                <svg id="logo" eight="80" width="80" xmlns="http://www.w3.org/2000/svg" viewBox="0 -3.552713678800501e-15 820 950"><path d="M404.345 229.846c52.467 0 98.494-20.488 138.08-61.465s59.38-88.626 59.38-142.947c0-5.966-.472-14.444-1.414-25.434-6.912.942-12.096 1.727-15.552 2.355-48.383 6.908-90.954 30.615-127.713 71.12-36.758 40.506-55.137 83.838-55.137 129.996 0 5.337.785 14.13 2.356 26.375zM592.379 950c37.387 0 78.701-25.59 123.943-76.772S796.122 761.915 820 692.836c-88.912-45.844-133.368-111.626-133.368-197.348 0-71.591 35.973-132.82 107.92-183.688-49.954-62.486-115.931-93.729-197.931-93.729-34.56 0-66.134 5.181-94.724 15.543l-17.908 6.594-24.035 9.42c-15.709 5.966-30.004 8.95-42.885 8.95-10.054 0-23.25-3.455-39.586-10.363l-18.38-7.536-17.436-7.065c-25.449-10.676-52.782-16.014-82-16.014-78.23 0-141.065 26.376-188.506 79.128C23.72 349.479 0 419.03 0 505.379c0 121.517 38.015 233.772 114.046 336.763C166.828 914.047 215.054 950 258.724 950c18.537 0 36.916-3.611 55.138-10.833l23.092-9.42 18.38-6.594c25.762-9.106 49.482-13.659 71.16-13.659 22.935 0 49.326 5.81 79.173 17.427l14.609 5.652C550.75 944.191 574.786 950 592.379 950z"/></svg>
                <h1 id="name">{CompanyName}</h1>
                <h1 id="price">{CurrentPrice} USD</h1>
                <p id="priceChange">{PriceChange} %</p>
            </div>
            <div className="stock-analysis">
            <AnalysisNavigation/>
            <Routes>
                    <Route path='/' element={<ForecastView ticker={ticker}/>}/>
                    <Route path='/fundamental' element={<FundamentalAnalysis ticker={ticker}/>}/>
                </Routes>
            </div>
        </div>
    )
}

export default Analysis2