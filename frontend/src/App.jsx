import { useState } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from '/vite.svg'
import './App.css'
import { BrowserRouter as Router, Route, Link, Routes } from 'react-router-dom';
import Home from './pages/Home';
import ResultPage from './pages/Result';
import MobileResultPage from './pages/MobileResult';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />}></Route>
        <Route path="/result" element={<ResultPage />}></Route>
        <Route path="/result-mobile" element={<MobileResultPage />}></Route>
      </Routes>
    </Router>
  );
}

export default App
