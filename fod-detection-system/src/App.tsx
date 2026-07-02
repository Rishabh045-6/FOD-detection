import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import { darkTheme } from './styles/theme';
import { UploadPage, ProcessingPage, ResultsPage, LiveDetectionPage } from './pages';
// Inside src/App.tsx
import { Navigation } from './components/Navigation';

const App: React.FC = () => {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <Router>
        <Navigation>
          <Routes>
            <Route path="/" element={<UploadPage />} />
            <Route path="/processing" element={<ProcessingPage />} />
            <Route path="/results" element={<ResultsPage />} />

            {/* New Live Hardware Stream Route */}
            <Route path="/live" element={<LiveDetectionPage />} />

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Navigation>
      </Router>
      <ToastContainer
        position="bottom-right"
        autoClose={5000}
        hideProgressBar={false}
        newestOnTop
        closeOnClick
        rtl={false}
        pauseOnFocusLoss
        draggable
        pauseOnHover
        theme="dark"
      />
    </ThemeProvider>
  );
};

export default App;