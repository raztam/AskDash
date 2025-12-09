import { useState } from 'react'
import { MessageSquare, Plus, Trash2, ChevronDown, ChevronRight } from 'lucide-react'
import { useAppStore } from '../store/appStore'
import { chatService } from '../services/chat'
import type { ChatSessionListItem } from '../types'

interface SidebarProps {
  isOpen: boolean
}

export default function Sidebar({ isOpen }: SidebarProps) {
  const {
    databases,
    selectedDatabaseId,
    sessions,
    selectedSessionId,
    selectSession,
    addSession,
    removeSession,
  } = useAppStore()

  const [expandedDbs, setExpandedDbs] = useState<number[]>([])
  const [isCreating, setIsCreating] = useState(false)

  const toggleExpand = (dbId: number) => {
    setExpandedDbs((prev) =>
      prev.includes(dbId)
        ? prev.filter((id) => id !== dbId)
        : [...prev, dbId]
    )
  }

  const handleCreateSession = async () => {
    if (!selectedDatabaseId || isCreating) return

    setIsCreating(true)
    try {
      const session = await chatService.createSession(selectedDatabaseId)
      const listItem: ChatSessionListItem = {
        id: session.id,
        title: session.title,
        database_connection: session.database_connection,
        database_name: session.database_name,
        message_count: 0,
        last_message: null,
        created_at: session.created_at,
        updated_at: session.updated_at,
      }
      addSession(listItem)
      selectSession(session.id)
    } catch (error) {
      console.error('Failed to create session:', error)
    } finally {
      setIsCreating(false)
    }
  }

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: number) => {
    e.stopPropagation()
    if (confirm('Delete this chat session?')) {
      try {
        await chatService.deleteSession(sessionId)
        removeSession(sessionId)
      } catch (error) {
        console.error('Failed to delete session:', error)
      }
    }
  }

  // Group sessions by database
  const sessionsByDb: Record<number, ChatSessionListItem[]> = {}
  sessions.forEach((session) => {
    if (!sessionsByDb[session.database_connection]) {
      sessionsByDb[session.database_connection] = []
    }
    sessionsByDb[session.database_connection].push(session)
  })

  if (!isOpen) {
    return null
  }

  return (
    <aside className="w-80 bg-white border-r border-gray-200 flex flex-col">
      {/* Header */}
      <div className="p-5 border-b border-gray-200">
        <button
          onClick={handleCreateSession}
          disabled={!selectedDatabaseId || isCreating}
          className="w-full flex items-center justify-center gap-2 px-5 py-3 bg-primary text-white text-base font-medium rounded-xl hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <Plus className="w-5 h-5" />
          New Chat
        </button>
      </div>

      {/* Chat History */}
      <div className="flex-1 overflow-y-auto p-3">
        <h3 className="px-3 py-2 text-sm font-semibold text-gray-500 uppercase tracking-wider">
          Chat History
        </h3>

        {databases.map((db) => {
          const dbSessions = sessionsByDb[db.id] || []
          const isExpanded = expandedDbs.includes(db.id) || db.id === selectedDatabaseId

          return (
            <div key={db.id} className="mb-2">
              <button
                onClick={() => toggleExpand(db.id)}
                className="w-full flex items-center gap-2 px-2 py-2 text-base text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                {isExpanded ? (
                  <ChevronDown className="w-5 h-5" />
                ) : (
                  <ChevronRight className="w-5 h-5" />
                )}
                <span className="truncate font-medium">{db.name}</span>
                <span className="ml-auto text-sm text-gray-400">
                  {dbSessions.length}
                </span>
              </button>

              {isExpanded && (
                <div className="ml-4 mt-1 space-y-1">
                  {dbSessions.length === 0 ? (
                    <p className="px-2 py-1 text-sm text-gray-400">No chats yet</p>
                  ) : (
                    dbSessions.map((session) => (
                      <button
                        key={session.id}
                        onClick={() => selectSession(session.id)}
                        className={`w-full flex items-center gap-2 px-2 py-2 text-base rounded-lg transition-colors group ${
                          selectedSessionId === session.id
                            ? 'bg-primary-50 text-primary-700'
                            : 'text-gray-600 hover:bg-gray-100'
                        }`}
                      >
                        <MessageSquare className="w-5 h-5 flex-shrink-0" />
                        <span className="truncate flex-1 text-left">
                          {session.title}
                        </span>
                        <button
                          onClick={(e) => handleDeleteSession(e, session.id)}
                          className="opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-100 rounded transition-all"
                        >
                          <Trash2 className="w-4 h-4 text-gray-400 group-hover:text-red-500" />
                        </button>
                      </button>
                    ))
                  )}
                </div>
              )}
            </div>
          )
        })}

        {databases.length === 0 && (
          <p className="px-2 py-4 text-sm text-gray-500 text-center">
            No databases connected.
            <br />
            Add one to start chatting!
          </p>
        )}
      </div>
    </aside>
  )
}
