import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { supabase } from './lib/supabase';
import HomePage from './pages/HomePage';
import ElderlyDashboard from './pages/ElderlyDashboard';
import FamilyDashboard from './pages/FamilyDashboard';
import CareDashboard from './pages/CareDashboard';
import DemoPage from './pages/DemoPage';
import AppointmentBookingPage from './pages/escort/AppointmentBookingPage';
import EscortWorkerDashboard from './pages/escort/EscortWorkerDashboard';
import EscortManagementPage from './pages/escort/EscortManagementPage';
import HealthDashboard from './pages/health/HealthDashboard';
import HealthRiskPrediction from './pages/health/HealthRiskPrediction';
import HealthSimplified from './pages/elderly/HealthSimplified';
import HealthMonitor from './pages/family/HealthMonitor';
import PatientManagement from './pages/doctor/PatientManagement';
import HealthPlanExecution from './pages/caregiver/HealthPlanExecution';
import CompanionDashboard from './pages/companion/CompanionDashboard';
import CompanionChat from './pages/companion/CompanionChat';
import ContentRecommend from './pages/companion/ContentRecommend';
import CognitiveGames from './pages/companion/CognitiveGames';
import VirtualPet from './pages/companion/VirtualPet';
import './App.css';

function App() {
  const [session, setSession] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setLoading(false);
    });

    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setSession(session);
    });

    return () => subscription.unsubscribe();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-indigo-600 mx-auto"></div>
          <p className="mt-4 text-gray-600 text-lg">系统加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage session={session} />} />
        <Route path="/demo" element={<DemoPage />} />
        <Route 
          path="/elderly" 
          element={session ? <ElderlyDashboard session={session} /> : <Navigate to="/" />} 
        />
        <Route 
          path="/family" 
          element={session ? <FamilyDashboard session={session} /> : <Navigate to="/" />} 
        />
        <Route 
          path="/care" 
          element={session ? <CareDashboard session={session} /> : <Navigate to="/" />} 
        />
        <Route 
          path="/escort/booking" 
          element={session ? <AppointmentBookingPage session={session} /> : <Navigate to="/" />} 
        />
        <Route 
          path="/escort/worker" 
          element={session ? <EscortWorkerDashboard session={session} /> : <Navigate to="/" />} 
        />
        <Route 
          path="/escort/management" 
          element={session ? <EscortManagementPage session={session} /> : <Navigate to="/" />} 
        />
        <Route 
          path="/health" 
          element={session ? <HealthDashboard session={session} /> : <Navigate to="/" />} 
        />
        <Route 
          path="/health/prediction" 
          element={session ? <HealthRiskPrediction session={session} /> : <Navigate to="/" />} 
        />
        <Route 
          path="/health/elderly" 
          element={session ? <HealthSimplified /> : <Navigate to="/" />} 
        />
        <Route 
          path="/health/family" 
          element={session ? <HealthMonitor /> : <Navigate to="/" />} 
        />
        <Route 
          path="/health/doctor" 
          element={session ? <PatientManagement /> : <Navigate to="/" />} 
        />
        <Route 
          path="/health/caregiver" 
          element={session ? <HealthPlanExecution /> : <Navigate to="/" />} 
        />
        <Route 
          path="/companion" 
          element={session ? <CompanionDashboard session={session} /> : <Navigate to="/" />} 
        />
        <Route 
          path="/companion/chat" 
          element={session ? <CompanionChat session={session} /> : <Navigate to="/" />} 
        />
        <Route 
          path="/companion/content" 
          element={session ? <ContentRecommend session={session} /> : <Navigate to="/" />} 
        />
        <Route 
          path="/companion/games" 
          element={session ? <CognitiveGames session={session} /> : <Navigate to="/" />} 
        />
        <Route 
          path="/companion/pet" 
          element={session ? <VirtualPet session={session} /> : <Navigate to="/" />} 
        />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
