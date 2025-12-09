import { useState } from 'react'
import { Plus, X, Database, Settings } from 'lucide-react'
import { useAppStore } from '../store/appStore'
import { databaseService } from '../services/database'
import PermissionsModal from './PermissionsModal'
import type { DatabaseConnection, CreateDatabaseRequest } from '../types'

const DB_TYPE_OPTIONS = [
  { value: 'postgresql', label: 'PostgreSQL' },
  { value: 'mysql', label: 'MySQL' },
  { value: 'sqlite', label: 'SQLite' },
  { value: 'mariadb', label: 'MariaDB' },
  { value: 'mssql', label: 'SQL Server' },
]

export default function DatabaseTabs() {
  const {
    databases,
    selectedDatabaseId,
    selectDatabase,
    addDatabase,
    removeDatabase,
    showAddDatabaseModal,
    setShowAddDatabaseModal,
  } = useAppStore()

  const [showPermissions, setShowPermissions] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [formData, setFormData] = useState<CreateDatabaseRequest>({
    name: '',
    db_type: 'postgresql',
    host: 'localhost',
    port: 5432,
    database_name: '',
    username: '',
    password: '',
    file_path: '',
  })

  const resetForm = () => {
    setFormData({
      name: '',
      db_type: 'postgresql',
      host: 'localhost',
      port: 5432,
      database_name: '',
      username: '',
      password: '',
      file_path: '',
    })
    setError(null)
  }

  const handleDbTypeChange = (type: DatabaseConnection['db_type']) => {
    const defaultPorts: Record<string, number> = {
      postgresql: 5432,
      mysql: 3306,
      mariadb: 3306,
      mssql: 1433,
      sqlite: 0,
    }
    setFormData({
      ...formData,
      db_type: type,
      port: defaultPorts[type] || 5432,
    })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    setError(null)

    try {
      const newDb = await databaseService.create(formData)
      addDatabase(newDb)
      selectDatabase(newDb.id)
      setShowAddDatabaseModal(false)
      resetForm()
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to create connection'
      setError(message)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleDelete = async (e: React.MouseEvent, id: number) => {
    e.stopPropagation()
    if (confirm('Delete this database connection?')) {
      try {
        await databaseService.delete(id)
        removeDatabase(id)
      } catch (err) {
        console.error('Failed to delete database:', err)
      }
    }
  }

  const selectedDb = databases.find((db) => db.id === selectedDatabaseId)

  return (
    <>
      {/* Tab Bar */}
      <div className="bg-white border-b border-gray-200">
        <div className="flex items-center gap-1 px-4 py-2 overflow-x-auto">
          {databases.map((db) => (
            <button
              key={db.id}
              onClick={() => selectDatabase(db.id)}
              className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm whitespace-nowrap transition-colors group ${
                selectedDatabaseId === db.id
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Database className="w-4 h-4" />
              <span>{db.name}</span>
              {db.is_owner && (
                <button
                  onClick={(e) => handleDelete(e, db.id)}
                  className={`p-0.5 rounded opacity-0 group-hover:opacity-100 transition-opacity ${
                    selectedDatabaseId === db.id
                      ? 'hover:bg-primary-600'
                      : 'hover:bg-gray-300'
                  }`}
                >
                  <X className="w-3 h-3" />
                </button>
              )}
            </button>
          ))}

          <button
            onClick={() => setShowAddDatabaseModal(true)}
            className="flex items-center gap-1 px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <Plus className="w-4 h-4" />
            Add Database
          </button>

          {selectedDb?.is_owner && (
            <>
              <div className="flex-1" />
              <button
                onClick={() => setShowPermissions(true)}
                className="flex items-center gap-1 px-3 py-2 text-sm text-gray-600 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <Settings className="w-4 h-4" />
                Permissions
              </button>
            </>
          )}
        </div>
      </div>

      {/* Add Database Modal */}
      {showAddDatabaseModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-md mx-4">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="text-lg font-semibold">Add Database Connection</h2>
              <button
                onClick={() => {
                  setShowAddDatabaseModal(false)
                  resetForm()
                }}
                className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              {error && (
                <div className="p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                  {error}
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Connection Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                  placeholder="My Database"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Database Type
                </label>
                <select
                  value={formData.db_type}
                  onChange={(e) => handleDbTypeChange(e.target.value as DatabaseConnection['db_type'])}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                >
                  {DB_TYPE_OPTIONS.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>

              {formData.db_type === 'sqlite' ? (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    File Path
                  </label>
                  <input
                    type="text"
                    required
                    value={formData.file_path}
                    onChange={(e) => setFormData({ ...formData, file_path: e.target.value })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                    placeholder="/path/to/database.db"
                  />
                </div>
              ) : (
                <>
                  <div className="grid grid-cols-3 gap-4">
                    <div className="col-span-2">
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Host
                      </label>
                      <input
                        type="text"
                        required
                        value={formData.host}
                        onChange={(e) => setFormData({ ...formData, host: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                        placeholder="localhost"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Port
                      </label>
                      <input
                        type="number"
                        required
                        value={formData.port}
                        onChange={(e) => setFormData({ ...formData, port: parseInt(e.target.value) })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Database Name
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.database_name}
                      onChange={(e) => setFormData({ ...formData, database_name: e.target.value })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                      placeholder="mydb"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Username
                      </label>
                      <input
                        type="text"
                        value={formData.username}
                        onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Password
                      </label>
                      <input
                        type="password"
                        value={formData.password}
                        onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                      />
                    </div>
                  </div>
                </>
              )}

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => {
                    setShowAddDatabaseModal(false)
                    resetForm()
                  }}
                  className="flex-1 px-4 py-2 text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 transition-colors"
                >
                  {isSubmitting ? 'Connecting...' : 'Connect'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Permissions Modal */}
      {showPermissions && selectedDb && (
        <PermissionsModal
          database={selectedDb}
          onClose={() => setShowPermissions(false)}
        />
      )}
    </>
  )
}
