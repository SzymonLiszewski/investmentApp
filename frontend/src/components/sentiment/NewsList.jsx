import NewsBox from "./NewsBox";
import { useState, useEffect } from "react";
import { useParams } from "react-router-dom";
import './NewsBox.css'
import IndicatorsGaugeChart from "../portfolio/IndicatorsGaugeChart";
import SearchBox from "../SearchBox";

function NewsList(){
    const [sentimentValue, setSentimentValue] = useState(0)
    const [news, setNews] = useState([])
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const {ticker} = useParams();

    const getNews = async() =>{
        try {
            const response = await fetch(`/api/analytics/news/?ticker=${ticker}`);
            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}`);
            }
            const result = await response.json();
            setSentimentValue(result['sentiment']);
            setNews(result['news'])
            console.log("data: ", news)
          } catch (error) {
            setError(error);
          } finally {
            setLoading(false);
          }
    }

    useEffect(()=>{
        setLoading(true);
        getNews();
    }, [ticker]
    )

    const interpretSentiment = sentimentValue < -0.3 ? "Poor financial performance, negative news, or management issues may lead to low sentiment. Investors might avoid or sell shares, anticipating potential declines."
    : (sentimentValue >= -0,3 && sentimentValue < 0.3) ? "Mixed or inconclusive information about the company. It may be stable but lacks standout performance. Investors might be cautious, observing the company’s progress."
    : "Positive financial results, favorable news, or strategic innovations contribute to high sentiment. Investors may be more likely to buy shares, expecting growth and positive returns.";

    if (loading){
        return (<h1>Loading...</h1>)
    }
    return(
        <div>
            <div  className='searchNews'>
                <SearchBox navigation={'news'}/>
            </div>
            <div className="newsList"> 
                <div className="newsLeft">
                    {news.map((item)=>(
                        <NewsBox title={item.title} link={item.link} description=""/>
                    ))}
                </div>
                <IndicatorsGaugeChart data={sentimentValue} range={[-1, 1]} name="Sentiment" interpretation={interpretSentiment} className="sentimentChart" />
            </div>
        </div>
    )
}

export default NewsList;