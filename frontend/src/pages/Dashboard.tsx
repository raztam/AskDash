import DatabaseTabs from '../components/DatabaseTabs'
import ChatInterface from '../components/ChatInterface'

export default function Dashboard() {
  return (
    <div className="h-full flex flex-col bg-gray-50">
      <DatabaseTabs />
      <ChatInterface />
    </div>
  )
}
