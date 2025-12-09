import { Database, LogOut, Menu, Settings } from 'lucide-react'
import { useAuthStore } from '../store/authStore'
import { useAppStore } from '../store/appStore'

export default function Header() {
  const { user, logout } = useAuthStore()
  const { toggleSidebar } = useAppStore()

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-5">
          <button
            onClick={toggleSidebar}
            className="p-2.5 hover:bg-gray-100 rounded-xl transition-colors"
          >
            <Menu className="w-6 h-6 text-gray-600" />
          </button>

          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-primary rounded-xl flex items-center justify-center">
              <Database className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-gray-800">AskDash</h1>
          </div>
        </div>

        <div className="flex items-center gap-5">
          <span className="text-base text-gray-600">
            Welcome, <span className="font-semibold">{user?.username}</span>
          </span>

          <button
            className="p-2.5 hover:bg-gray-100 rounded-xl transition-colors"
            title="Settings"
          >
            <Settings className="w-6 h-6 text-gray-600" />
          </button>

          <button
            onClick={logout}
            className="flex items-center gap-2 px-4 py-2.5 text-base text-gray-600 hover:bg-gray-100 rounded-xl transition-colors"
          >
            <LogOut className="w-5 h-5" />
            Logout
          </button>
        </div>
      </div>
    </header>
  )
}
