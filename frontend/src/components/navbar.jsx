import "./styles/NavBar.css"
import { Link } from "react-router-dom"
import { useAuth } from "../AuthContext";

function NavBar(){
    const { isLoggedIn, logout } = useAuth();
    return (
        <nav className="navigation">
            <Link to="/" className="site-title">Captrivio</Link>
            <ul>
                <li>
                    <Link to="/analysis2/aapl">analysis</Link>
                </li>
                <li>
                    <Link to="/news/aapl">news</Link>
                </li>
                <li>
                    <Link to="/calendar">calendar</Link>
                </li>
                <li>
                    <Link to="/about">about</Link>
                </li>
                {isLoggedIn == true? <li>
                    <Link to="/portfolio">portfolio</Link>
                </li>: null}
            </ul>
            <ul className="UserButtons">
            {isLoggedIn == true? <li>
                    <Link to="/logout" onClick={logout}>logout</Link>
                </li>: 
                <ul className="UserButtons">
                <li>
                <Link to="/register" id="signup">register</Link>
                </li>
                <li>
                <Link to="/login" id="signin">login</Link>
                </li>
                </ul>
                }
                
            </ul>
        </nav>
    )
}
export default NavBar