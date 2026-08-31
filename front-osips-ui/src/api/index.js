import client from './client'

export const authApi = {
  login: (username, password) => client.post('/auth/login', { username, password }).then((r) => r.data),
  me: () => client.get('/auth/me').then((r) => r.data),
  changePassword: (payload) => client.post('/auth/change-password', payload).then((r) => r.data),
}

export const serversApi = {
  list: (onlyActive = false) => client.get('/servers', { params: { only_active: onlyActive } }).then((r) => r.data),
  create: (payload) => client.post('/servers', payload).then((r) => r.data),
  update: (id, payload) => client.put(`/servers/${id}`, payload).then((r) => r.data),
  remove: (id) => client.delete(`/servers/${id}`).then((r) => r.data),
  check: (id) => client.post(`/servers/${id}/check`).then((r) => r.data),
}

export const usersApi = {
  list: () => client.get('/users').then((r) => r.data),
  create: (payload) => client.post('/users', payload).then((r) => r.data),
  update: (id, payload) => client.put(`/users/${id}`, payload).then((r) => r.data),
  remove: (id) => client.delete(`/users/${id}`).then((r) => r.data),
}

export const rolesApi = {
  list: () => client.get('/roles').then((r) => r.data),
  permissions: () => client.get('/roles/permissions').then((r) => r.data),
  create: (payload) => client.post('/roles', payload).then((r) => r.data),
  update: (id, payload) => client.put(`/roles/${id}`, payload).then((r) => r.data),
  remove: (id) => client.delete(`/roles/${id}`).then((r) => r.data),
}

export const dispatcherApi = {
  list: (serverId) => client.get(`/servers/${serverId}/dispatcher`).then((r) => r.data),
  create: (serverId, payload) => client.post(`/servers/${serverId}/dispatcher`, payload).then((r) => r.data),
  update: (serverId, rowId, payload) => client.put(`/servers/${serverId}/dispatcher/${rowId}`, payload).then((r) => r.data),
  remove: (serverId, rowId) => client.delete(`/servers/${serverId}/dispatcher/${rowId}`).then((r) => r.data),
  setState: (serverId, rowId, state) => client.post(`/servers/${serverId}/dispatcher/${rowId}/state`, { state }).then((r) => r.data),
  reload: (serverId) => client.post(`/servers/${serverId}/dispatcher/reload`).then((r) => r.data),
}

export const loadBalancerApi = {
  list: (serverId) => client.get(`/servers/${serverId}/loadbalancer`).then((r) => r.data),
  create: (serverId, payload) => client.post(`/servers/${serverId}/loadbalancer`, payload).then((r) => r.data),
  update: (serverId, rowId, payload) => client.put(`/servers/${serverId}/loadbalancer/${rowId}`, payload).then((r) => r.data),
  remove: (serverId, rowId) => client.delete(`/servers/${serverId}/loadbalancer/${rowId}`).then((r) => r.data),
  setStatus: (serverId, rowId, enabled) => client.post(`/servers/${serverId}/loadbalancer/${rowId}/status`, { enabled }).then((r) => r.data),
  reload: (serverId) => client.post(`/servers/${serverId}/loadbalancer/reload`).then((r) => r.data),
}

export const dialplanApi = {
  list: (serverId, params) => client.get(`/servers/${serverId}/dialplan`, { params }).then((r) => r.data),
  dpids: (serverId) => client.get(`/servers/${serverId}/dialplan/dpids`).then((r) => r.data),
  partitions: (serverId) => client.get(`/servers/${serverId}/dialplan/partitions`).then((r) => r.data),
  create: (serverId, payload) => client.post(`/servers/${serverId}/dialplan`, payload).then((r) => r.data),
  update: (serverId, rowId, payload) => client.put(`/servers/${serverId}/dialplan/${rowId}`, payload).then((r) => r.data),
  remove: (serverId, rowId) => client.delete(`/servers/${serverId}/dialplan/${rowId}`).then((r) => r.data),
  reload: (serverId, partition) => client.post(`/servers/${serverId}/dialplan/reload`, null, { params: { partition } }).then((r) => r.data),
  translate: (serverId, payload) => client.post(`/servers/${serverId}/dialplan/translate`, payload).then((r) => r.data),
}

export const rtpengineApi = {
  list: (serverId) => client.get(`/servers/${serverId}/rtpengine`).then((r) => r.data),
  create: (serverId, payload) => client.post(`/servers/${serverId}/rtpengine`, payload).then((r) => r.data),
  update: (serverId, rowId, payload) => client.put(`/servers/${serverId}/rtpengine/${rowId}`, payload).then((r) => r.data),
  remove: (serverId, rowId) => client.delete(`/servers/${serverId}/rtpengine/${rowId}`).then((r) => r.data),
  setEnabled: (serverId, rowId, enabled) => client.post(`/servers/${serverId}/rtpengine/${rowId}/enabled`, { enabled }).then((r) => r.data),
  reload: (serverId, soft = false) => client.post(`/servers/${serverId}/rtpengine/reload`, { soft }).then((r) => r.data),
}

// kind: 'user' (userblacklist) или 'global' (globalblacklist)
export const blacklistApi = {
  list: (serverId, kind, params) => client.get(`/servers/${serverId}/blacklist/${kind}`, { params }).then((r) => r.data),
  create: (serverId, kind, payload) => client.post(`/servers/${serverId}/blacklist/${kind}`, payload).then((r) => r.data),
  update: (serverId, kind, rowId, payload) => client.put(`/servers/${serverId}/blacklist/${kind}/${rowId}`, payload).then((r) => r.data),
  remove: (serverId, kind, rowId) => client.delete(`/servers/${serverId}/blacklist/${kind}/${rowId}`).then((r) => r.data),
  reload: (serverId) => client.post(`/servers/${serverId}/blacklist/reload`).then((r) => r.data),
}

export const addressApi = {
  list: (serverId) => client.get(`/servers/${serverId}/address`).then((r) => r.data),
  create: (serverId, payload) => client.post(`/servers/${serverId}/address`, payload).then((r) => r.data),
  update: (serverId, rowId, payload) => client.put(`/servers/${serverId}/address/${rowId}`, payload).then((r) => r.data),
  remove: (serverId, rowId) => client.delete(`/servers/${serverId}/address/${rowId}`).then((r) => r.data),
  reload: (serverId, partition = null) => client.post(`/servers/${serverId}/address/reload`, { partition }).then((r) => r.data),
}

export const sipRegsApi = {
  list: (serverId, params) => client.get(`/servers/${serverId}/sip-regs`, { params }).then((r) => r.data),
}

export const auditApi = {
  list: (params) => client.get('/audit', { params }).then((r) => r.data),
}
