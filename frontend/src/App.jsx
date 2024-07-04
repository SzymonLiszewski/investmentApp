// src/HomePage.jsx
import React, { Fragment } from 'react';
import NavBar from './components/navbar';
import {Route, Routes} from 'react-router-dom';
import Analysis from './pages/Analysis';
import HomePage from './pages/HomePage';
import News from './pages/News';

const App = () => {
    return (
        <Fragment>
            <NavBar/>
            <div className='container'>
                <Routes>
                    <Route path='/' element={<HomePage/>}/>
                    <Route path='/news' element={<News/>}/>
                    <Route path='/analysis' element={<Analysis/>}/>
                </Routes>
            </div>
        </Fragment>
            
    );
};

export default App;
