import React from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import MainLayout from './components/MainLayout'
import LoginPage from './pages/Login'
import TradeData from './pages/TradeData'
import Profile from './pages/Profile'
import { useAuthStore } from './store/authStore'

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
            <MainLayout>
              <Routes>
                {/* 公开路由 - 数据查询 */}
                <Route path="/" element={<TradeData readOnly={true} />} />
                
                {/* 受保护路由 - 需要登录 */}
                <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
              </Routes>
            </MainLayout>
          }
        />
      </Routes>
    </Router>
  )
}

export default App
