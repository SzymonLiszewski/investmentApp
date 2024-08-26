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
import AddStocks from './components/portfolio/AddStocks';
import { AuthProvider } from './AuthContext';
import XtbLoginPage from './pages/XtbLoginPage';
import ConnectedAccounts from './components/portfolio/ConnectAccounts';

const App = () => {
    return (
        <Fragment>
            <AuthProvider>
                <NavBar isLoggedIn={true}/>
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
                        <Route path='/addStock' element={<AddStocks/>}/>
                        <Route path='/xtbLogin' element={<XtbLoginPage/>}/>
                        <Route path='/connectAccounts' element={<ConnectedAccounts/>}/>
                    </Routes>
                </div>
            </AuthProvider>
        </Fragment>
            
    );
};

export default App;
