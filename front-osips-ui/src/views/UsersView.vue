<script setup>
import { computed, onMounted, ref } from 'vue'
import { rolesApi, usersApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import UserDialog from '@/components/UserDialog.vue'

const auth = useAuthStore()
const ui = useUiStore()

const users = ref([])
const roles = ref([])
const loading = ref(false)
const saving = ref(false)
const dialog = ref(false)
const editing = ref(null)
const confirmDelete = ref(false)
const userToDelete = ref(null)

const rolesBySlug = computed(() => Object.fromEntries(roles.value.map((role) => [role.slug, role])))

function roleTitle(slug) {
  return rolesBySlug.value[slug]?.title || slug
}

const headers = [
  { title: 'Логин', key: 'username' },
  { title: 'ФИО', key: 'full_name' },
  { title: 'Роль', key: 'role', width: 150 },
  { title: 'Вход', key: 'auth_provider', width: 110 },
  { title: 'Последний вход', key: 'last_login_at', width: 180 },
  { title: 'Статус', key: 'is_active', width: 110 },
  { title: '', key: 'actions', width: 110, sortable: false, align: 'end' },
]

function formatDate(value) {
  if (!value) return '—'
  // backend хранит время в UTC
  return new Date(`${value}Z`).toLocaleString('ru-RU')
}

async function fetchUsers() {
  loading.value = true
  try {
    ;[users.value, roles.value] = await Promise.all([usersApi.list(), rolesApi.list()])
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    loading.value = false
  }
}

onMounted(fetchUsers)

function openCreate() {
  editing.value = null
  dialog.value = true
}

function openEdit(user) {
  editing.value = user
  dialog.value = true
}

async function save({ id, payload }) {
  saving.value = true
  try {
    if (id) {
      await usersApi.update(id, payload)
      ui.success('Пользователь обновлён')
    } else {
      await usersApi.create(payload)
      ui.success('Пользователь создан')
    }
    dialog.value = false
    await fetchUsers()
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    saving.value = false
  }
}

function askDelete(user) {
  userToDelete.value = user
  confirmDelete.value = true
}

async function remove() {
  saving.value = true
  try {
    await usersApi.remove(userToDelete.value.id)
    ui.success('Пользователь удалён')
    confirmDelete.value = false
    await fetchUsers()
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <v-card>
    <v-card-item>
      <div class="d-flex align-center ga-2">
        <div>
          <v-card-title class="pa-0">Пользователи</v-card-title>
          <v-card-subtitle class="pa-0">
            Учётные записи. Набор разделов определяет роль — настраивается в разделе «Роли и права».
          </v-card-subtitle>
        </div>
        <v-spacer />
        <v-btn variant="text" prepend-icon="mdi-refresh" :loading="loading" @click="fetchUsers">Обновить</v-btn>
        <v-btn color="primary" prepend-icon="mdi-account-plus" @click="openCreate">Добавить</v-btn>
      </div>
    </v-card-item>

    <v-divider />

    <v-data-table :headers="headers" :items="users" :loading="loading" density="comfortable" items-per-page="25">
      <template #item.role="{ item }">
        <v-chip size="small" :color="rolesBySlug[item.role]?.is_builtin ? 'primary' : 'grey'" variant="tonal" label>
          {{ roleTitle(item.role) }}
        </v-chip>
      </template>

      <template #item.last_login_at="{ item }">
        <span class="text-caption text-medium-emphasis">{{ formatDate(item.last_login_at) }}</span>
      </template>

      <template #item.is_active="{ item }">
        <v-chip size="small" :color="item.is_active ? 'success' : 'grey'" variant="tonal" label>
          {{ item.is_active ? 'активен' : 'заблокирован' }}
        </v-chip>
      </template>

      <template #item.actions="{ item }">
        <v-btn icon="mdi-pencil" size="small" variant="text" @click="openEdit(item)" />
        <v-btn
          icon="mdi-delete"
          size="small"
          variant="text"
          color="error"
          :disabled="item.id === auth.user?.id"
          @click="askDelete(item)"
        />
      </template>
    </v-data-table>

    <v-card-text class="text-caption text-medium-emphasis">
      Вход через SSO пока не подключён: все учётные записи локальные (auth_provider = local).
    </v-card-text>
  </v-card>

  <UserDialog v-model="dialog" :user="editing" :roles="roles" :saving="saving" @save="save" />

  <ConfirmDialog
    v-model="confirmDelete"
    title="Удалить пользователя?"
    :text="`Учётная запись «${userToDelete?.username}» будет удалена.`"
    confirm-text="Удалить"
    color="error"
    :loading="saving"
    @confirm="remove"
  />
</template>
