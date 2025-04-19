import React, { useEffect } from 'react';
import { Routes, Route } from 'react-router-dom';
import { useDispatch } from 'react-redux';

import Layout from './components/layout/Layout';
import Overview from './views/Overview';
import IoTMonitoring from './views/IoTMonitoring';
import SalesAnalysis from './views/SalesAnalysis';
import MarketingDashboard from './views/MarketingDashboard';
import FinancialReports from './views/FinancialReports';
import StaffManagement from './views/StaffManagement';
import NotFound from './views/NotFound';

import { initializeWebSocket } from './services/socketService';
import { loadInitialData } from './store/actions/dataActions';

function App() {
  const dispatch = useDispatch();

  useEffect(() => {
    // Initialiser le WebSocket pour les mises à jour en temps réel
    const cleanupSocket = initializeWebSocket();
    
    // Charger les données initiales
    dispatch(loadInitialData());

    return () => {
      cleanupSocket();
    };
  }, [dispatch]);

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Overview />} />
        <Route path="/iot" element={<IoTMonitoring />} />
        <Route path="/sales" element={<SalesAnalysis />} />
        <Route path="/marketing" element={<MarketingDashboard />} />
        <Route path="/finance" element={<FinancialReports />} />
        <Route path="/staff" element={<StaffManagement />} />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </Layout>
  );
}

export default App;
