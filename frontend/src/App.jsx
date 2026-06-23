import React, { useState, useEffect } from 'react';
import { UploadPage } from './pages/UploadPage';
import { DashboardPage } from './pages/DashboardPage';
import { ReportPage } from './pages/ReportPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { apiClient } from './api/client';

function App() {
  const [user, setUser] = useState(null);
  const [checkingSession, setCheckingSession] = useState(true);
  const [authView, setAuthView] = useState('login'); // 'login' | 'register'
  
  const [currentView, setCurrentView] = useState('upload'); // 'upload' | 'dashboard' | 'report'
  const [assessmentId, setAssessmentId] = useState(null);

  // Check user session on application startup
  useEffect(() => {
    const verifySession = async () => {
      try {
        const currentUser = await apiClient.getCurrentUser();
        setUser(currentUser);
      } catch (err) {
        console.log('No active session found.');
        setUser(null);
      } finally {
        setCheckingSession(false);
      }
    };
    verifySession();
  }, []);

  const handleAuthSuccess = async () => {
    try {
      setCheckingSession(true);
      const currentUser = await apiClient.getCurrentUser();
      setUser(currentUser);
      setCurrentView('upload');
    } catch (err) {
      console.error('Failed to retrieve user profile after auth success:', err);
    } finally {
      setCheckingSession(false);
    }
  };

  const handleLogout = async () => {
    try {
      await apiClient.logout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      setUser(null);
      setAssessmentId(null);
      setCurrentView('upload');
      setAuthView('login');
    }
  };

  const handleUploadSuccess = (id) => {
    setAssessmentId(id);
    setCurrentView('dashboard');
  };

  if (checkingSession) {
    return (
      <div style={{ 
        display: 'flex', 
        flexDirection: 'column', 
        justifyContent: 'center', 
        alignItems: 'center', 
        minHeight: '100vh',
        backgroundColor: '#0f172a',
        color: '#f8fafc',
        fontFamily: "'Outfit', sans-serif"
      }}>
        <div className="glass-card" style={{ padding: '3rem', textAlign: 'center' }}>
          <h2 style={{ marginBottom: '1rem', background: 'linear-gradient(135deg, #fff 30%, #6366f1 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            Initializing AIKosh Toolkit...
          </h2>
          <p style={{ color: '#64748b' }}>Verifying secure session credentials...</p>
        </div>
      </div>
    );
  }

  // Render Authentication screen if user is not logged in
  if (!user) {
    return authView === 'login' ? (
      <LoginPage 
        onLoginSuccess={handleAuthSuccess} 
        onSwitchToRegister={() => setAuthView('register')} 
      />
    ) : (
      <RegisterPage 
        onRegisterSuccess={handleAuthSuccess} 
        onSwitchToLogin={() => setAuthView('login')} 
      />
    );
  }

  return (
    <div className="App">
      <header className="app-header">
        <div className="logo-container">
          <div style={{ width: '10px', height: '24px', background: 'linear-gradient(135deg, #6366f1, #a855f7)', borderRadius: '4px' }}></div>
          <span className="logo-text">AIKosh Quality Toolkit</span>
        </div>
        
        <nav className="nav-menu">
          <button 
            onClick={() => setCurrentView('upload')} 
            className={`btn-nav ${currentView === 'upload' ? 'active' : ''}`}
          >
            Upload
          </button>
          {assessmentId && (
            <>
              <button 
                onClick={() => setCurrentView('dashboard')} 
                className={`btn-nav ${currentView === 'dashboard' ? 'active' : ''}`}
              >
                Dashboard
              </button>
              <button 
                onClick={() => setCurrentView('report')} 
                className={`btn-nav ${currentView === 'report' ? 'active' : ''}`}
              >
                Report
              </button>
            </>
          )}
        </nav>

        <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
          <span style={{ fontSize: '0.85rem', color: '#cbd5e1', fontStyle: 'italic' }}>
            {user.email}
          </span>
          <button onClick={handleLogout} className="btn btn-secondary" style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}>
            Sign Out
          </button>
        </div>
      </header>

      <main style={{ padding: '2rem' }}>
        {currentView === 'upload' && <UploadPage onUploadSuccess={handleUploadSuccess} />}
        {currentView === 'dashboard' && <DashboardPage assessmentId={assessmentId} />}
        {currentView === 'report' && <ReportPage assessmentId={assessmentId} />}
      </main>
    </div>
  );
}

export default App;
