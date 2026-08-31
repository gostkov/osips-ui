<script setup>
import { computed, onMounted, ref } from 'vue'
import { rolesApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import RoleDialog from '@/components/RoleDialog.vue'

const auth = useAuthStore()
const ui = useUiStore()

const roles = ref([])
const groups = ref([])
const loading = ref(false)
const saving = ref(false)
const dialog = ref(false)
const editing = ref(null)
const confirmDelete = ref(false)
const roleToDelete = ref(null)

const headers = [
  { title: 'Роль', key: 'title' },
  { title: 'Доступ к разделам', key: 'permissions', sortable: false },
  { title: 'Пользователей', key: 'users_count', width: 130, align: 'end' },
  { title: '', key: 'actions', width: 110, sortable: false, align: 'end' },
]

const totalPerms = computed(() => groups.value.reduce((sum, group) => sum + group.permissions.length, 0))

// раздел показывается чипом: серый - только чтение, зелёный - есть право на изменение
function sections(role) {
  return groups.value
    .map((group) => {
      const granted = group.permissions.filter((perm) => role.permissions.includes(perm.value))
      if (!granted.length) return null
      const writable = granted.some((perm) => perm.value.endsWith(':write') || perm.value === 'users:manage')
      return { section: group.section, writable, granted: granted.length, all: granted.length === group.permissions.length }
    })
    .filter(Boolean)
}

async function fetchData() {
  loading.value = true
  try {
    ;[roles.value, groups.value] = await Promise.all([rolesApi.list(), rolesApi.permissions()])
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    loading.value = false
  }
}

onMounted(fetchData)

function openCreate() {
  editing.value = null
  dialog.value = true
}

function openEdit(role) {
  editing.value = role
  dialog.value = true
}

async function save({ id, payload }) {
  saving.value = true
  try {
    if (id) {
      await rolesApi.update(id, payload)
      ui.success('Роль обновлена')
    } else {
      await rolesApi.create(payload)
      ui.success('Роль создана')
    }
    dialog.value = false
    await fetchData()
    // права собственной роли могли измениться - перечитываем профиль
    await auth.fetchMe()
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    saving.value = false
  }
}

function askDelete(role) {
  roleToDelete.value = role
  confirmDelete.value = true
}

async function remove() {
  saving.value = true
  try {
    await rolesApi.remove(roleToDelete.value.id)
    ui.success('Роль удалена')
    confirmDelete.value = false
    await fetchData()
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
          <v-card-title class="pa-0">Роли и права</v-card-title>
          <v-card-subtitle class="pa-0">
            Роль — это набор прав. Доступ к разделам проверяет backend, поэтому изменения действуют сразу.
          </v-card-subtitle>
        </div>
        <v-spacer />
        <v-btn variant="text" prepend-icon="mdi-refresh" :loading="loading" @click="fetchData">Обновить</v-btn>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreate">Добавить роль</v-btn>
      </div>
    </v-card-item>

    <v-divider />

    <v-data-table :headers="headers" :items="roles" :loading="loading" density="comfortable" items-per-page="25">
      <template #item.title="{ item }">
        <div class="d-flex align-center ga-2">
          <span>{{ item.title }}</span>
          <v-chip size="x-small" variant="tonal" label class="font-monospace">{{ item.slug }}</v-chip>
          <v-chip v-if="item.is_builtin" size="x-small" color="primary" variant="tonal" label>встроенная</v-chip>
        </div>
        <div v-if="item.description" class="text-caption text-medium-emphasis">{{ item.description }}</div>
      </template>

      <template #item.permissions="{ item }">
        <span v-if="!item.permissions.length" class="text-caption text-medium-emphasis">нет доступа</span>
        <template v-else-if="item.permissions.length === totalPerms">
          <v-chip size="small" color="primary" variant="tonal" label>все разделы</v-chip>
        </template>
        <template v-else>
          <v-chip
            v-for="entry in sections(item)"
            :key="entry.section"
            size="small"
            class="mr-1 mb-1"
            :color="entry.writable ? 'success' : undefined"
            variant="tonal"
            label
          >
            {{ entry.section }}
            <span class="text-caption ml-1">{{ entry.writable ? 'изменение' : 'чтение' }}</span>
          </v-chip>
        </template>
      </template>

      <template #item.users_count="{ item }">
        <span :class="item.users_count ? '' : 'text-medium-emphasis'">{{ item.users_count }}</span>
      </template>

      <template #item.actions="{ item }">
        <v-tooltip :disabled="!item.is_builtin" text="Встроенная роль не редактируется" location="top">
          <template #activator="{ props: tip }">
            <span v-bind="tip">
              <v-btn icon="mdi-pencil" size="small" variant="text" :disabled="item.is_builtin" @click="openEdit(item)" />
              <v-btn
                icon="mdi-delete"
                size="small"
                variant="text"
                color="error"
                :disabled="item.is_builtin"
                @click="askDelete(item)"
              />
            </span>
          </template>
        </v-tooltip>
      </template>
    </v-data-table>

    <v-divider />

    <v-card-text class="d-flex align-center ga-2 text-caption text-medium-emphasis">
      <v-icon icon="mdi-information-outline" size="16" />
      Перечень прав задан в коде — из интерфейса настраивается их состав в ролях. Роль, назначенную
      пользователям, удалить нельзя: сначала переведите их на другую.
    </v-card-text>
  </v-card>

  <RoleDialog v-model="dialog" :role="editing" :groups="groups" :saving="saving" @save="save" />

  <ConfirmDialog
    v-model="confirmDelete"
    title="Удалить роль?"
    :text="`Роль «${roleToDelete?.title}» будет удалена.`"
    confirm-text="Удалить"
    color="error"
    :loading="saving"
    @confirm="remove"
  />
</template>

<style scoped>
.font-monospace {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
</style>
