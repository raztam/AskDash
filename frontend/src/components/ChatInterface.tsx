import { useState, useRef, useEffect } from 'react'
import { Send, Code, Loader2, Plus } from 'lucide-react'
import { useAppStore } from '../store/appStore'
import { chatService } from '../services/chat'
import type { ChatMessage, ChatSessionListItem } from '../types'
import ChartRenderer from './ChartRenderer'

export default function ChatInterface() {
  const {
    selectedDatabaseId,
    selectedSessionId,
    currentMessages,
    showSql,
    isAskingQuestion,
    databases,
    setShowSql,
    setIsAskingQuestion,
    addMessage,
    addSession,
    selectSession,
    setShowAddDatabaseModal,
  } = useAppStore()

  const [input, setInput] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [currentMessages])

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = Math.min(inputRef.current.scrollHeight, 200) + 'px'
    }
  }, [input])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !selectedDatabaseId || isAskingQuestion) return

    const question = input.trim()
    setInput('')
    setIsAskingQuestion(true)

    // Add user message immediately
    const userMessage: ChatMessage = {
      id: Date.now(),
      session: selectedSessionId || 0,
      message_type: 'user',
      content: question,
      sql_query: null,
      query_results: [],
      chart_type: null,
      chart_config: {},
      explanation: null,
      insights: null,
      created_at: new Date().toISOString(),
    }
    addMessage(userMessage)

    try {
      const response = await chatService.askQuestion({
        question,
        database_id: selectedDatabaseId,
        session_id: selectedSessionId || undefined,
        show_sql: showSql,
      })

      // If new session was created, add it
      if (!selectedSessionId && response.session_id) {
        const newSession: ChatSessionListItem = {
          id: response.session_id,
          title: question.slice(0, 50) + (question.length > 50 ? '...' : ''),
          database_connection: selectedDatabaseId,
          database_name: '',
          message_count: 2,
          last_message: {
            content: response.answer,
            type: 'assistant',
            created_at: new Date().toISOString(),
          },
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }
        addSession(newSession)
        selectSession(response.session_id)
      }

      // Add assistant message
      const assistantMessage: ChatMessage = {
        id: response.message_id,
        session: response.session_id,
        message_type: response.error ? 'error' : 'assistant',
        content: response.answer || response.error || 'No response',
        sql_query: response.sql_query,
        query_results: response.results || [],
        chart_type: response.chart_type,
        chart_config: response.chart_config || {},
        explanation: response.explanation,
        insights: response.insights,
        created_at: new Date().toISOString(),
      }
      addMessage(assistantMessage)
    } catch (error) {
      // Add error message
      const errorMessage: ChatMessage = {
        id: Date.now() + 1,
        session: selectedSessionId || 0,
        message_type: 'error',
        content: error instanceof Error ? error.message : 'An error occurred',
        sql_query: null,
        query_results: [],
        chart_type: null,
        chart_config: {},
        explanation: null,
        insights: null,
        created_at: new Date().toISOString(),
      }
      addMessage(errorMessage)
    } finally {
      setIsAskingQuestion(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  if (!selectedDatabaseId) {
    // Check if there are no databases connected at all
    if (databases.length === 0) {
      return (
        <div className="flex-1 flex items-center justify-center">
          <div className="text-center">
            <p className="text-lg text-gray-600 mb-2">No databases connected.</p>
            <p className="text-gray-500 mb-6">Add one to start chatting!</p>
            <button
              onClick={() => setShowAddDatabaseModal(true)}
              className="w-16 h-16 bg-primary hover:bg-primary-600 text-white rounded-full flex items-center justify-center mx-auto transition-colors shadow-lg hover:shadow-xl"
            >
              <Plus className="w-8 h-8" />
            </button>
          </div>
        </div>
      )
    }

    return (
      <div className="flex-1 flex items-center justify-center text-gray-500">
        <div className="text-center">
          <p className="text-lg">Select or add a database to start chatting</p>
          <p className="text-sm mt-2">
            Click "Add Database" to connect your first database
          </p>
        </div>
      </div>
    )
  }

  const examplePrompts = [
    "What are the top 10 customers by revenue?",
    "Show me sales trends over the last year",
    "How many orders were placed last month?",
  ]

  const handleExampleClick = (example: string) => {
    setInput(example)
    inputRef.current?.focus()
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="max-w-4xl mx-auto space-y-4">
          {currentMessages.length === 0 ? (
            <div className="flex items-center justify-center h-full min-h-[400px] text-gray-500">
              <div className="text-center">
                <h2 className="text-3xl font-semibold text-gray-800 mb-2">Ask anything about your data</h2>
                <p className="text-gray-500">Start by typing a question below</p>
              </div>
            </div>
          ) : (
            currentMessages.map((message) => (
              <MessageBubble key={message.id} message={message} showSql={showSql} />
            ))
          )}

          {isAskingQuestion && (
            <div className="flex items-center gap-2 text-gray-500">
              <Loader2 className="w-5 h-5 animate-spin" />
              <span className="loading-dots text-base">Thinking</span>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 p-6 bg-white">
        <div className="max-w-4xl mx-auto space-y-4">
          <form onSubmit={handleSubmit} className="space-y-3">
            {/* Show SQL Toggle */}
            <div className="flex items-center gap-2">
              <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showSql}
                  onChange={(e) => setShowSql(e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-primary focus:ring-primary"
                />
                <Code className="w-4 h-4" />
                Show raw SQL
              </label>
            </div>

            {/* Input */}
            <div className="flex gap-3">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask a question about your data..."
                disabled={isAskingQuestion}
                rows={1}
                className="flex-1 px-5 py-4 border border-gray-300 rounded-2xl resize-none focus:ring-2 focus:ring-primary focus:border-primary disabled:opacity-50 text-base"
              />
              <button
                type="submit"
                disabled={!input.trim() || isAskingQuestion}
                className="px-5 py-4 bg-primary text-white rounded-2xl hover:bg-primary-600 disabled:opacity-50 transition-colors"
              >
                <Send className="w-6 h-6" />
              </button>
            </div>
          </form>

          {/* Example Prompts */}
          {currentMessages.length === 0 && (
            <div className="flex flex-wrap justify-center gap-3 pt-2">
              {examplePrompts.map((prompt, index) => (
                <button
                  key={index}
                  onClick={() => handleExampleClick(prompt)}
                  className="px-4 py-2.5 bg-primary/10 text-primary border border-primary/20 rounded-full text-sm font-medium hover:bg-primary/20 hover:border-primary/30 transition-colors"
                >
                  {prompt}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Message Bubble Component
function MessageBubble({
  message,
  showSql,
}: {
  message: ChatMessage
  showSql: boolean
}) {
  const isUser = message.message_type === 'user'
  const isError = message.message_type === 'error'

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? 'bg-primary text-white'
            : isError
            ? 'bg-red-50 text-red-700 border border-red-200'
            : 'bg-white border border-gray-200 shadow-sm'
        }`}
      >
        {/* Message Content */}
        <p className="whitespace-pre-wrap">{message.content}</p>

        {/* AI Insights - Show prominently for assistant messages */}
        {!isUser && !isError && message.insights && (
          <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start gap-2">
              <div className="flex-shrink-0 w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center mt-0.5">
                <span className="text-white text-xs font-bold">💡</span>
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold text-blue-900 mb-1">Key Insights</p>
                <p className="text-sm text-blue-800 leading-relaxed">{message.insights}</p>
              </div>
            </div>
          </div>
        )}

        {/* Explanation */}
        {!isUser && message.explanation && (
          <div className="mt-3 text-sm text-gray-600 italic border-t border-gray-100 pt-3">
            {message.explanation}
          </div>
        )}

        {/* SQL Query (if enabled and available) */}
        {!isUser && showSql && message.sql_query && (
          <div className="mt-3 p-3 bg-gray-900 text-gray-100 rounded-lg overflow-x-auto">
            <pre className="text-sm font-mono">{message.sql_query}</pre>
          </div>
        )}

        {/* Query Results */}
        {!isUser && message.query_results && message.query_results.length > 0 && (
          <div className="mt-4">
            {/* Chart */}
            {message.chart_type && message.chart_type !== 'none' && message.chart_type !== 'table' && (
              <div className="mb-4">
                <ChartRenderer
                  type={message.chart_type}
                  data={message.query_results}
                  config={message.chart_config}
                />
              </div>
            )}

            {/* Data Table */}
            <div className="overflow-x-auto">
              <ResultsTable data={message.query_results} />
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

// Results Table Component
function ResultsTable({ data }: { data: Record<string, unknown>[] }) {
  if (!data || data.length === 0) return null

  const columns = Object.keys(data[0])
  const displayData = data.slice(0, 100) // Limit to 100 rows for display

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {columns.map((col) => (
              <th
                key={col}
                className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {displayData.map((row, i) => (
            <tr key={i} className="hover:bg-gray-50">
              {columns.map((col) => (
                <td key={col} className="px-3 py-2 text-sm text-gray-900 whitespace-nowrap">
                  {String(row[col] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {data.length > 100 && (
        <div className="px-3 py-2 bg-gray-50 text-sm text-gray-500 text-center">
          Showing 100 of {data.length} rows
        </div>
      )}
    </div>
  )
}
