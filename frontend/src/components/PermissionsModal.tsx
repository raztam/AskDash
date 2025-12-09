import { useState, useEffect } from 'react'
import { Plus, X, Trash2, Users, Table, ChevronDown, ChevronRight } from 'lucide-react'
import { databaseService } from '../services/database'
import { userService } from '../services/user'
import type { DatabaseConnection, User, PermissionGroup } from '../types'

interface PermissionsModalProps {
  database: DatabaseConnection
  onClose: () => void
}

export default function PermissionsModal({ database, onClose }: PermissionsModalProps) {
  const [activeTab, setActiveTab] = useState<'groups' | 'legacy'>('groups')
  const [permissionGroups, setPermissionGroups] = useState<PermissionGroup[]>([])
  const [permissions, setPermissions] = useState<
    { user_username: string; table_name: string; permission_level: string }[]
  >([])
  const [isLoading, setIsLoading] = useState(true)
  const [users, setUsers] = useState<User[]>([])
  const [tables, setTables] = useState<string[]>([])

  // Create group form
  const [showCreateGroup, setShowCreateGroup] = useState(false)
  const [newGroupName, setNewGroupName] = useState('')
  const [newGroupDescription, setNewGroupDescription] = useState('')
  const [selectedTables, setSelectedTables] = useState<string[]>([])

  // Expanded group for viewing/editing
  const [expandedGroupId, setExpandedGroupId] = useState<number | null>(null)
  const [selectedUserId, setSelectedUserId] = useState<string>('')

  // Load data
  useEffect(() => {
    const load = async () => {
      try {
        const [groups, perms, tablesRes, usersRes] = await Promise.all([
          databaseService.getPermissionGroups(database.id),
          databaseService.getPermissions(database.id),
          databaseService.getTables(database.id),
          userService.listUsers(),
        ])
        setPermissionGroups(groups)
        setPermissions(perms)
        setTables(tablesRes.tables)
        setUsers(usersRes)
      } catch (err) {
        console.error('Failed to load data:', err)
      } finally {
        setIsLoading(false)
      }
    }
    load()
  }, [database.id])

  const handleCreateGroup = async () => {
    if (!newGroupName.trim()) return

    try {
      const group = await databaseService.createPermissionGroup({
        name: newGroupName,
        description: newGroupDescription,
        database_id: database.id,
        tables: selectedTables.map((t) => ({ table_name: t, permission_level: 'read' })),
      })
      setPermissionGroups((prev) => [...prev, group])
      setShowCreateGroup(false)
      setNewGroupName('')
      setNewGroupDescription('')
      setSelectedTables([])
    } catch (err) {
      console.error('Failed to create group:', err)
    }
  }

  const handleDeleteGroup = async (groupId: number) => {
    if (
      !confirm(
        'Delete this permission group? Users will lose access to tables assigned through this group.'
      )
    )
      return

    try {
      await databaseService.deletePermissionGroup(groupId)
      setPermissionGroups((prev) => prev.filter((g) => g.id !== groupId))
      if (expandedGroupId === groupId) {
        setExpandedGroupId(null)
      }
    } catch (err) {
      console.error('Failed to delete group:', err)
    }
  }

  const handleAddTableToGroup = async (groupId: number, tableName: string) => {
    try {
      const result = await databaseService.addTablesToGroup(groupId, {
        tables: [{ table_name: tableName, permission_level: 'read' }],
      })
      setPermissionGroups((prev) => prev.map((g) => (g.id === groupId ? result.group : g)))
    } catch (err) {
      console.error('Failed to add table to group:', err)
    }
  }

  const handleRemoveTableFromGroup = async (groupId: number, tableName: string) => {
    try {
      const result = await databaseService.removeTableFromGroup(groupId, tableName)
      setPermissionGroups((prev) => prev.map((g) => (g.id === groupId ? result.group : g)))
    } catch (err) {
      console.error('Failed to remove table from group:', err)
    }
  }

  const handleAssignUser = async (groupId: number, username: string) => {
    try {
      const result = await databaseService.assignUserToGroup(groupId, { username })
      setPermissionGroups((prev) => prev.map((g) => (g.id === groupId ? result.group : g)))
      // Refresh permissions list
      const perms = await databaseService.getPermissions(database.id)
      setPermissions(perms)
    } catch (err) {
      console.error('Failed to assign user:', err)
    }
  }

  const handleRemoveUser = async (groupId: number, username: string) => {
    try {
      const result = await databaseService.removeUserFromGroup(groupId, username)
      setPermissionGroups((prev) => prev.map((g) => (g.id === groupId ? result.group : g)))
      // Refresh permissions list
      const perms = await databaseService.getPermissions(database.id)
      setPermissions(perms)
    } catch (err) {
      console.error('Failed to remove user:', err)
    }
  }

  // Legacy single-table permission handlers
  const [legacySelectedUserId, setLegacySelectedUserId] = useState<string>('')
  const [legacyTableName, setLegacyTableName] = useState('')

  const handleLegacyGrant = async () => {
    const selectedUser = users.find((u) => u.id.toString() === legacySelectedUserId)
    if (!selectedUser || !legacyTableName) return

    try {
      await databaseService.grantPermission({
        database_id: database.id,
        username: selectedUser.username,
        table_name: legacyTableName,
        permission_level: 'read',
      })
      const perms = await databaseService.getPermissions(database.id)
      setPermissions(perms)
      setLegacySelectedUserId('')
      setLegacyTableName('')
    } catch (err) {
      console.error('Failed to grant permission:', err)
    }
  }

  const handleLegacyRevoke = async (user: string, table: string) => {
    try {
      await databaseService.revokePermission({
        database_id: database.id,
        username: user,
        table_name: table,
      })
      setPermissions((prev) =>
        prev.filter((p) => !(p.user_username === user && p.table_name === table))
      )
    } catch (err) {
      console.error('Failed to revoke permission:', err)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl w-full max-w-2xl mx-4 max-h-[85vh] flex flex-col">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h2 className="text-lg font-semibold">Manage Permissions - {database.name}</h2>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex border-b px-6">
          <button
            onClick={() => setActiveTab('groups')}
            className={`px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors ${
              activeTab === 'groups'
                ? 'border-primary text-primary'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              Permission Groups
            </div>
          </button>
          <button
            onClick={() => setActiveTab('legacy')}
            className={`px-4 py-3 text-sm font-medium border-b-2 -mb-px transition-colors ${
              activeTab === 'legacy'
                ? 'border-primary text-primary'
                : 'border-transparent text-gray-500 hover:text-gray-700'
            }`}
          >
            <div className="flex items-center gap-2">
              <Table className="w-4 h-4" />
              Single Table Access
            </div>
          </button>
        </div>

        <div className="p-6 overflow-y-auto flex-1">
          {isLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            </div>
          ) : activeTab === 'groups' ? (
            <div className="space-y-6">
              {/* Create Group Section */}
              {!showCreateGroup ? (
                <button
                  onClick={() => setShowCreateGroup(true)}
                  className="flex items-center gap-2 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-600 transition-colors"
                >
                  <Plus className="w-4 h-4" />
                  Create Permission Group
                </button>
              ) : (
                <div className="border rounded-lg p-4 space-y-4 bg-gray-50">
                  <h3 className="font-medium">Create New Permission Group</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Group Name *
                      </label>
                      <input
                        type="text"
                        value={newGroupName}
                        onChange={(e) => setNewGroupName(e.target.value)}
                        placeholder="e.g., HR Department"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Description
                      </label>
                      <input
                        type="text"
                        value={newGroupDescription}
                        onChange={(e) => setNewGroupDescription(e.target.value)}
                        placeholder="Access to HR-related tables"
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                      />
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Select Tables
                    </label>
                    <div className="grid grid-cols-3 gap-2 max-h-40 overflow-y-auto p-2 bg-white border rounded-lg">
                      {tables.map((table) => (
                        <label key={table} className="flex items-center gap-2 text-sm">
                          <input
                            type="checkbox"
                            checked={selectedTables.includes(table)}
                            onChange={(e) => {
                              if (e.target.checked) {
                                setSelectedTables([...selectedTables, table])
                              } else {
                                setSelectedTables(selectedTables.filter((t) => t !== table))
                              }
                            }}
                            className="rounded border-gray-300 text-primary focus:ring-primary"
                          />
                          {table}
                        </label>
                      ))}
                    </div>
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={() => {
                        setShowCreateGroup(false)
                        setNewGroupName('')
                        setNewGroupDescription('')
                        setSelectedTables([])
                      }}
                      className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleCreateGroup}
                      disabled={!newGroupName.trim()}
                      className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 transition-colors"
                    >
                      Create Group
                    </button>
                  </div>
                </div>
              )}

              {/* Permission Groups List */}
              <div className="space-y-3">
                <h3 className="font-medium text-gray-700">Permission Groups</h3>
                {permissionGroups.length === 0 ? (
                  <p className="text-gray-500 text-sm">No permission groups created yet.</p>
                ) : (
                  <div className="space-y-2">
                    {permissionGroups.map((group) => (
                      <div key={group.id} className="border rounded-lg overflow-hidden">
                        {/* Group Header */}
                        <div
                          className="flex items-center justify-between p-4 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
                          onClick={() =>
                            setExpandedGroupId(expandedGroupId === group.id ? null : group.id)
                          }
                        >
                          <div className="flex items-center gap-3">
                            {expandedGroupId === group.id ? (
                              <ChevronDown className="w-4 h-4 text-gray-500" />
                            ) : (
                              <ChevronRight className="w-4 h-4 text-gray-500" />
                            )}
                            <div>
                              <h4 className="font-medium">{group.name}</h4>
                              {group.description && (
                                <p className="text-sm text-gray-500">{group.description}</p>
                              )}
                            </div>
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="flex items-center gap-4 text-sm text-gray-500">
                              <span className="flex items-center gap-1">
                                <Table className="w-4 h-4" />
                                {group.table_count} tables
                              </span>
                              <span className="flex items-center gap-1">
                                <Users className="w-4 h-4" />
                                {group.user_count} users
                              </span>
                            </div>
                            <button
                              onClick={(e) => {
                                e.stopPropagation()
                                handleDeleteGroup(group.id)
                              }}
                              className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>

                        {/* Group Details (Expanded) */}
                        {expandedGroupId === group.id && (
                          <div className="p-4 border-t space-y-4">
                            {/* Tables Section */}
                            <div>
                              <h5 className="text-sm font-medium text-gray-700 mb-2">
                                Tables in Group
                              </h5>
                              <div className="flex flex-wrap gap-2 mb-3">
                                {group.tables.map((table) => (
                                  <span
                                    key={table.id}
                                    className="inline-flex items-center gap-1 px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                                  >
                                    {table.table_name}
                                    <button
                                      onClick={() =>
                                        handleRemoveTableFromGroup(group.id, table.table_name)
                                      }
                                      className="ml-1 hover:text-blue-600"
                                    >
                                      <X className="w-3 h-3" />
                                    </button>
                                  </span>
                                ))}
                                {group.tables.length === 0 && (
                                  <span className="text-sm text-gray-500">No tables added</span>
                                )}
                              </div>
                              <div className="flex gap-2">
                                <select
                                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm"
                                  onChange={(e) => {
                                    if (e.target.value) {
                                      handleAddTableToGroup(group.id, e.target.value)
                                      e.target.value = ''
                                    }
                                  }}
                                >
                                  <option value="">Add a table...</option>
                                  {tables
                                    .filter((t) => !group.tables.some((gt) => gt.table_name === t))
                                    .map((t) => (
                                      <option key={t} value={t}>
                                        {t}
                                      </option>
                                    ))}
                                </select>
                              </div>
                            </div>

                            {/* Users Section */}
                            <div>
                              <h5 className="text-sm font-medium text-gray-700 mb-2">
                                Users with Access
                              </h5>
                              <div className="space-y-2 mb-3">
                                {group.user_assignments.map((assignment) => (
                                  <div
                                    key={assignment.id}
                                    className="flex items-center justify-between p-2 bg-gray-50 rounded-lg"
                                  >
                                    <div>
                                      <span className="font-medium">{assignment.user_username}</span>
                                      {assignment.user_email && (
                                        <span className="text-sm text-gray-500 ml-2">
                                          ({assignment.user_email})
                                        </span>
                                      )}
                                    </div>
                                    <button
                                      onClick={() =>
                                        handleRemoveUser(group.id, assignment.user_username)
                                      }
                                      className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                                    >
                                      <X className="w-4 h-4" />
                                    </button>
                                  </div>
                                ))}
                                {group.user_assignments.length === 0 && (
                                  <p className="text-sm text-gray-500">No users assigned</p>
                                )}
                              </div>
                              <div className="flex gap-2">
                                <select
                                  value={selectedUserId}
                                  onChange={(e) => setSelectedUserId(e.target.value)}
                                  className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary text-sm"
                                >
                                  <option value="">Select user to add...</option>
                                  {users
                                    .filter(
                                      (u) => !group.user_assignments.some((a) => a.user === u.id)
                                    )
                                    .map((user) => (
                                      <option key={user.id} value={user.id}>
                                        {user.username} {user.email ? `(${user.email})` : ''}
                                      </option>
                                    ))}
                                </select>
                                <button
                                  onClick={() => {
                                    const user = users.find(
                                      (u) => u.id.toString() === selectedUserId
                                    )
                                    if (user) {
                                      handleAssignUser(group.id, user.username)
                                      setSelectedUserId('')
                                    }
                                  }}
                                  disabled={!selectedUserId}
                                  className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 transition-colors text-sm"
                                >
                                  Add User
                                </button>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ) : (
            /* Legacy Single Table Access Tab */
            <div className="space-y-6">
              {/* Grant Permission Form */}
              <div className="space-y-3">
                <h3 className="font-medium text-gray-700">Grant Single Table Access</h3>
                <p className="text-sm text-gray-500">
                  For quick access to individual tables. For managing access to multiple tables,
                  use Permission Groups.
                </p>
                <div className="grid grid-cols-2 gap-3">
                  <select
                    value={legacySelectedUserId}
                    onChange={(e) => setLegacySelectedUserId(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                  >
                    <option value="">Select user</option>
                    {users.map((user) => (
                      <option key={user.id} value={user.id}>
                        {user.username} {user.email ? `(${user.email})` : ''}
                      </option>
                    ))}
                  </select>
                  <select
                    value={legacyTableName}
                    onChange={(e) => setLegacyTableName(e.target.value)}
                    className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-primary"
                  >
                    <option value="">Select table</option>
                    {tables.map((t) => (
                      <option key={t} value={t}>
                        {t}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={handleLegacyGrant}
                    disabled={!legacySelectedUserId || !legacyTableName}
                    className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 transition-colors"
                  >
                    Grant Read Access
                  </button>
                </div>
                {users.length === 0 && (
                  <p className="text-sm text-gray-500">
                    No other users found. Invite users to register first.
                  </p>
                )}
              </div>

              {/* Current Permissions */}
              <div className="space-y-3">
                <h3 className="font-medium text-gray-700">Current Permissions</h3>
                {permissions.length === 0 ? (
                  <p className="text-gray-500 text-sm">No permissions granted yet.</p>
                ) : (
                  <div className="space-y-2">
                    {permissions.map((p, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                      >
                        <div>
                          <span className="font-medium">{p.user_username}</span>
                          <span className="text-gray-500"> → </span>
                          <span className="text-gray-700">{p.table_name}</span>
                          <span className="ml-2 px-2 py-0.5 rounded text-xs bg-green-100 text-green-700">
                            read
                          </span>
                        </div>
                        <button
                          onClick={() => handleLegacyRevoke(p.user_username, p.table_name)}
                          className="p-1 text-gray-400 hover:text-red-500 transition-colors"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
