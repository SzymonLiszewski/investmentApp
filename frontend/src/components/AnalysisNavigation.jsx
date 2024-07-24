import React from 'react';
import { BrowserRouter as Router, Route, Link, useLocation, NavLink } from 'react-router-dom';
import './styles/AnalysisNavigation.css';
import { styled } from '@mui/system';



const AnalysisNavigation = () => {
  const location = useLocation();
  
  return (
    <nav className="navbar">
      <ul>
        <li className="">
          <NavLink end to="" activeclassname="active">overview</NavLink>
        </li>
        <li>
          <NavLink to="fundamental" activeclassname="active">fundamental analysis</NavLink>
        </li>
        <li>
          <NavLink to="technical" activeclassname="active">technical analysis</NavLink>
        </li>
        <li>
          <NavLink to="news" activeclassname="active">news</NavLink>
        </li>
      </ul>
    </nav>
  );
};

export default AnalysisNavigation;
