/* eslint-disable react/prop-types */
import { NavLink } from 'react-router-dom';
import './styles/AnalysisNavigation.css';

const tabClass = ({ isActive }) => `analysis-tab${isActive ? ' active' : ''}`;

const AnalysisNavigation = ({ ticker }) => {
  return (
    <nav className="analysis-tabs" aria-label="Stock analysis sections">
      <NavLink end to="" className={tabClass}>Overview</NavLink>
      <NavLink to="fundamental" className={tabClass}>Fundamental analysis</NavLink>
      <NavLink to="technical" className={tabClass}>Technical analysis</NavLink>
      <NavLink to={`/news/${(ticker || '').toLowerCase()}`} className={tabClass}>News</NavLink>
    </nav>
  );
};

export default AnalysisNavigation;
