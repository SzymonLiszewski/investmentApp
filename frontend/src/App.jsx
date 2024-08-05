// src/HomePage.jsx
import React, { Fragment } from 'react';
import NavBar from './components/navbar';
import {Route, Routes} from 'react-router-dom';
import Analysis from './pages/Analysis';
import HomePage from './pages/HomePage';
import News from './pages/News';
import FundamentalAnalysis from './components/FundamentalAnalysis';
import Analysis2 from './pages/Analysis2';
import ForecastView from './components/ForecastView';
import EventsCalendar from './components/EventsCalendar';
import Portfolio from './pages/Portfolio';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage'

const App = () => {
    return (
        <Fragment>
            <NavBar/>
            <div className='container'>
                <Routes>
                    <Route path='/' element={<HomePage/>}/>
                    <Route path='/news' element={<News/>}/>
                    <Route path='/analysis' element={<Analysis/>}/>
                    <Route path='/analysis2/:ticker/*' element={<Analysis2/>}/>
                    <Route path='/calendar' element={<EventsCalendar/>}/>
                    <Route path='/portfolio' element={<Portfolio/>}/>
                    <Route path='/login' element={<LoginPage/>}/>
                    <Route path='/register' element={<RegisterPage/>}/>
                </Routes>
            </div>
        </Fragment>
            
    );
};

export default App;
