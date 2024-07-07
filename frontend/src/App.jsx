// src/HomePage.jsx
import React, { Fragment } from 'react';
import NavBar from './components/navbar';
import {Route, Routes} from 'react-router-dom';
import Analysis from './pages/Analysis';
import HomePage from './pages/HomePage';
import News from './pages/News';
import FundamentalAnalysis from './components/FundamentalAnalysis';

const App = () => {
    return (
        <Fragment>
            
            <div className='container'>
                <Routes>
                    <Route path='/' element={<HomePage/>}/>
                    <Route path='/news' element={<News/>}/>
                    <Route path='/analysis' element={<Analysis/>}/>
                    <Route path='/analysis/fundamental' element={<FundamentalAnalysis/>}/>
                </Routes>
            </div>
        </Fragment>
            
    );
};

export default App;
