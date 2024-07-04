import "./styles/NavBar.css"

function NavBar(){
    return (
        <nav className="navigation">
            <a href="/" className="site-title">StockSense</a>
            <ul>
                <li>
                    <a href="/analysis">analysis</a>
                </li>
                <li>
                    <a href="/news">news</a>
                </li>
                <li>
                    <a href="/calendar">calendar</a>
                </li>
                <li>
                    <a href="/about">about</a>
                </li>
                
            </ul>
            <ul className="UserButtons">
                <li>
                <a href="/signup">sign up</a>
                </li>
                <li>
                <a href="/signin">sign in</a>
                </li>
            </ul>
        </nav>
    )
}
export default NavBar