import React from 'react';
import { BrowserRouter as Router, Route, Link, useLocation } from 'react-router-dom';
import './styles/AnalysisNavigation.css';

const Home = () => <div>Home</div>;
const About = () => <div>About</div>;
const Contact = () => <div>Contact</div>;

const AnalysisNavigation = () => {
  const location = useLocation();
  
  return (
    <nav className="navbar">
      <ul>
        <li className={location.pathname === '/analysis2' ? 'active' : ''}>
          <Link to="/overwiev">overview</Link>
        </li>
        <li className={location.pathname === '/fundamental' ? 'active' : ''}>
          <Link to="/fundamental">fundamental analysis</Link>
        </li>
        <li className={location.pathname === '/technical' ? 'active' : ''}>
          <Link to="/technical">technical analysis</Link>
        </li>
        <li className={location.pathname === '/news' ? 'active' : ''}>
          <Link to="/news">news</Link>
        </li>
      </ul>
    </nav>
  );
};

export default AnalysisNavigation;
