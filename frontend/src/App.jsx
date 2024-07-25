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
                    <Route path='calendar' element={<EventsCalendar/>}/>
                </Routes>
            </div>
        </Fragment>
            
    );
};

export default App;
