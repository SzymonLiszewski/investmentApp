import "../components/styles/Portfolio.css"
import UserEarningsChart from "../components/UserEarningsChart"

function Portfolio(){
    return (
        <div className="portfolio">
            <div className="portfolioDiv" id="return">
                <h1><UserEarningsChart/></h1>
            </div>
            <div className="portfolioDiv" id="composition">
                <h1>composition</h1>
            </div>
            <div className="portfolioDiv" id="indicators">
                <h1>indicators</h1>
            </div>
        </div>
    )
}
    

export default Portfolio