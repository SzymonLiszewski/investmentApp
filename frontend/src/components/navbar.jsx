import "./styles/NavBar.css"
import { useEffect, useState } from "react"
import { Link, useLocation } from "react-router-dom"
import { useAuth } from "../AuthContext";

const NAV_LINKS = [
    { to: "/analysis2/AAPL", label: "Analysis" },
    { to: "/news/aapl", label: "News" },
    { to: "/calendar", label: "Calendar" },
    { to: "/about", label: "About" },
];

function NavBar(){
    const { isLoggedIn, logout } = useAuth();
    const [drawerOpen, setDrawerOpen] = useState(false);
    const location = useLocation();

    const links = isLoggedIn
        ? [...NAV_LINKS, { to: "/portfolio", label: "Portfolio" }]
        : NAV_LINKS;

    // Close the drawer on navigation
    useEffect(() => {
        setDrawerOpen(false);
    }, [location]);

    useEffect(() => {
        if (!drawerOpen) return;
        const onKeyDown = (event) => {
            if (event.key === "Escape") setDrawerOpen(false);
        };
        document.addEventListener("keydown", onKeyDown);
        return () => document.removeEventListener("keydown", onKeyDown);
    }, [drawerOpen]);

    const authActions = isLoggedIn ? (
        <button type="button" className="btn-ghost" onClick={logout}>Log out</button>
    ) : (
        <>
            <Link className="btn-ghost" to="/login">Log in</Link>
            <Link className="btn-primary" to="/register">Get started</Link>
        </>
    );

    return (
        <header className="site-header">
            <div className="site-header-inner">
                <Link to="/" className="brand">cap<span>trivio</span></Link>
                <nav className="desktop-nav" aria-label="Main">
                    {links.map((link) => (
                        <Link key={link.to} to={link.to}>{link.label}</Link>
                    ))}
                </nav>
                <div className="header-actions">{authActions}</div>
                <button
                    type="button"
                    className="menu-toggle"
                    aria-expanded={drawerOpen}
                    aria-controls="mobile-drawer"
                    aria-label={drawerOpen ? "Close menu" : "Open menu"}
                    onClick={() => setDrawerOpen((open) => !open)}
                >
                    <span className={`menu-icon${drawerOpen ? " open" : ""}`} aria-hidden="true">
                        <span /><span /><span />
                    </span>
                </button>
            </div>
            <div
                className={`drawer-backdrop${drawerOpen ? " show" : ""}`}
                onClick={() => setDrawerOpen(false)}
                aria-hidden="true"
            />
            <nav
                id="mobile-drawer"
                className={`drawer${drawerOpen ? " open" : ""}`}
                aria-label="Mobile"
            >
                <div className="drawer-head">
                    <span className="brand" aria-hidden="true">cap<span>trivio</span></span>
                    <button
                        type="button"
                        className="drawer-close"
                        aria-label="Close menu"
                        onClick={() => setDrawerOpen(false)}
                    >
                        ×
                    </button>
                </div>
                {links.map((link) => (
                    <Link key={link.to} to={link.to}>{link.label}</Link>
                ))}
                <div className="drawer-actions">{authActions}</div>
            </nav>
        </header>
    )
}
export default NavBar
