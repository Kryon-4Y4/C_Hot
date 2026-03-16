import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from 'antd'
import MainLayout from './components/Layout/MainLayout'
import LoginPage from './pages/Login'
import Dashboard from './pages/Dashboard'
import TradeData from './pages/TradeData'
import DataAdd from './pages/DataAdd'
import Statistics from './pages/Statistics'
import { useAuthStore } from './store/authStore'

const { Content } = Layout

// 受保护路由组件
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token } = useAuthStore()
  
  if (!token) {
    return <Navigate to="/login" replace />
  }
  
  return <>{children}</>
}

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/trade-data" element={<TradeData />} />
                  <Route path="/data-add" element={<DataAdd />} />
                  <Route path="/statistics" element={<Statistics />} />
                </Routes>
              </MainLayout>
            </ProtectedRoute>
          }
        />
      </Routes>
    </Router>
  )
}

export default App
