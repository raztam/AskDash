import { useEffect } from 'react'
import { useAuthStore } from '../store/authStore'
import { useAppStore } from '../store/appStore'
import Sidebar from './Sidebar'
import Header from './Header'

interface LayoutProps {
  children: React.ReactNode
}

export default function Layout({ children }: LayoutProps) {
  const { user, fetchUser } = useAuthStore()
  const { isSidebarOpen, fetchDatabases } = useAppStore()

  useEffect(() => {
    if (!user) {
      fetchUser()
    }
    fetchDatabases()
  }, [user, fetchUser, fetchDatabases])

  return (
    <div className="h-screen flex flex-col bg-gray-100">
      <Header />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar isOpen={isSidebarOpen} />
        <main className="flex-1 overflow-hidden">
          {children}
        </main>
      </div>
    </div>
  )
}
