import { Link } from "react-router-dom"
import "../styles/ConnectAccounts.css"

function ConnectedAccounts(){
    return (
    <div className="accountsList">
            <h1>connect your accounts</h1>
            <ul>
                <li><h2><Link to="/xtbLogin" style={{color: "black"}}><img src="https://img.logo.dev/xtb.com?token=pk_F06zMPFbR5yUJmwRi1Y-Jg" style={{width: "40px", height: "40px", marginRight: "40px"}} />xtb</Link></h2></li>
            </ul>
    </div>)
}

export default ConnectedAccounts