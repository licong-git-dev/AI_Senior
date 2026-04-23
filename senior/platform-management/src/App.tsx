import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import GovernmentDashboard from './pages/GovernmentDashboard';
import CommunityManagement from './pages/CommunityManagement';
import ProviderManagement from './pages/ProviderManagement';
import DataDashboard from './pages/DataDashboard';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/government" element={<GovernmentDashboard />} />
        <Route path="/community" element={<CommunityManagement />} />
        <Route path="/provider" element={<ProviderManagement />} />
        <Route path="/dashboard" element={<DataDashboard />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
