import "./styles/NavBar.css"
import { Link } from "react-router-dom"

function NavBar(){
    return (
        <nav className="navigation">
            <Link to="/" className="site-title">StockSense</Link>
            <ul>
                <li>
                    <Link to="/analysis">analysis</Link>
                </li>
                <li>
                    <Link to="/news">news</Link>
                </li>
                <li>
                    <Link to="/calendar">calendar</Link>
                </li>
                <li>
                    <Link to="/about">about</Link>
                </li>
                
            </ul>
            <ul className="UserButtons">
                <li>
                <Link to="/signup" id="signup">sign up</Link>
                </li>
                <li>
                <Link to="/signin" id="signin">sign in</Link>
                </li>
            </ul>
        </nav>
    )
}
export default NavBar