<script setup>
import { computed, ref, watch } from 'vue'
import { blacklistApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useServersStore } from '@/stores/servers'
import { useUiStore } from '@/stores/ui'
import BlacklistRowDialog from '@/components/BlacklistRowDialog.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const auth = useAuthStore()
const servers = useServersStore()
const ui = useUiStore()

const PER_PAGE = 25

const kind = ref('user')
const items = ref([])
const total = ref(0)
const page = ref(1)
const search = ref('')
const only = ref(null)
const loading = ref(false)
const saving = ref(false)
const reloading = ref(false)

const dialog = ref(false)
const editing = ref(null)
const confirmDelete = ref(false)
const rowToDelete = ref(null)

const serverId = computed(() => servers.selectedId)
const canWrite = computed(() => auth.can('blacklist:write'))
const pageCount = computed(() => Math.max(1, Math.ceil(total.value / PER_PAGE)))
const isUser = computed(() => kind.value === 'user')

const filterItems = [
  { title: 'Все правила', value: null },
  { title: 'Только запреты', value: 'black' },
  { title: 'Только разрешения', value: 'white' },
]

async function fetchEntries() {
  if (!serverId.value) return
  loading.value = true
  try {
    const data = await blacklistApi.list(serverId.value, kind.value, {
      page: page.value,
      per_page: PER_PAGE,
      search: search.value || undefined,
      only: only.value ?? undefined,
    })
    items.value = data.items
    total.value = data.total
  } catch (error) {
    items.value = []
    total.value = 0
    ui.error(error.uiMessage)
  } finally {
    loading.value = false
  }
}

watch(
  serverId,
  () => {
    page.value = 1
    fetchEntries()
  },
  { immediate: true },
)

watch(kind, () => {
  page.value = 1
  search.value = ''
  only.value = null
  fetchEntries()
})

watch(page, fetchEntries)
watch(only, () => {
  page.value = 1
  fetchEntries()
})

let searchTimer = null
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    fetchEntries()
  }, 350)
})

function openCreate() {
  editing.value = null
  dialog.value = true
}

function openEdit(row) {
  editing.value = row
  dialog.value = true
}

async function save({ id, payload }) {
  saving.value = true
  try {
    if (id) {
      await blacklistApi.update(serverId.value, kind.value, id, payload)
      ui.success('Правило обновлено')
    } else {
      await blacklistApi.create(serverId.value, kind.value, payload)
      ui.success('Правило добавлено')
    }
    dialog.value = false
    await fetchEntries()
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    saving.value = false
  }
}

function askDelete(row) {
  rowToDelete.value = row
  confirmDelete.value = true
}

async function remove() {
  saving.value = true
  try {
    await blacklistApi.remove(serverId.value, kind.value, rowToDelete.value.id)
    ui.success('Правило удалено')
    confirmDelete.value = false
    await fetchEntries()
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    saving.value = false
  }
}

async function reloadInMemory() {
  reloading.value = true
  try {
    await blacklistApi.reload(serverId.value)
    ui.success('reload_blacklist выполнен')
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    reloading.value = false
  }
}
</script>

<template>
  <v-card>
    <v-tabs v-model="kind" bg-color="surface" color="primary">
      <v-tab value="user" prepend-icon="mdi-account-cancel">userblacklist</v-tab>
      <v-tab value="global" prepend-icon="mdi-earth-off">globalblacklist</v-tab>
    </v-tabs>
    <v-divider />

    <v-card-item>
      <div class="d-flex flex-wrap align-center ga-2">
        <div>
          <v-card-title class="pa-0">Списки номеров</v-card-title>
          <v-card-subtitle class="pa-0">
            {{ isUser ? 'Правила на конкретного абонента' : 'Общие правила по префиксам' }}
          </v-card-subtitle>
        </div>
        <v-spacer />
        <v-select v-model="only" :items="filterItems" label="Тип" density="compact" hide-details style="max-width: 200px" />
        <v-text-field
          v-model="search"
          :placeholder="isUser ? 'Поиск по абоненту или префиксу' : 'Поиск по префиксу или описанию'"
          prepend-inner-icon="mdi-magnify"
          density="compact"
          hide-details
          clearable
          style="max-width: 280px"
        />
        <v-btn variant="text" prepend-icon="mdi-refresh" :loading="loading" @click="fetchEntries">Обновить</v-btn>
      </div>
    </v-card-item>

    <v-divider />

    <v-table density="comfortable">
      <thead>
        <tr>
          <template v-if="isUser">
            <th>username</th>
            <th>domain</th>
          </template>
          <th>prefix</th>
          <th v-if="!isUser">description</th>
          <th style="width: 160px">Тип правила</th>
          <th style="width: 100px" />
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading">
          <td :colspan="isUser ? 5 : 4" class="text-center py-6"><v-progress-circular indeterminate size="24" /></td>
        </tr>
        <tr v-else-if="!items.length">
          <td :colspan="isUser ? 5 : 4" class="text-center text-medium-emphasis py-6">Правила не найдены</td>
        </tr>
        <tr v-for="item in items" v-else :key="item.id">
          <template v-if="isUser">
            <td>{{ item.username || '—' }}</td>
            <td class="text-medium-emphasis">{{ item.domain || '—' }}</td>
          </template>
          <td class="font-monospace">{{ item.prefix || '—' }}</td>
          <td v-if="!isUser" class="text-medium-emphasis">{{ item.description || '—' }}</td>
          <td>
            <v-chip size="small" :color="item.whitelist ? 'success' : 'error'" variant="tonal" label>
              {{ item.whitelist ? 'разрешение' : 'запрет' }}
            </v-chip>
          </td>
          <td class="text-end">
            <v-btn v-if="canWrite" icon="mdi-pencil" size="small" variant="text" @click="openEdit(item)" />
            <v-btn v-if="canWrite" icon="mdi-delete" size="small" variant="text" color="error" @click="askDelete(item)" />
          </td>
        </tr>
      </tbody>
    </v-table>

    <v-divider />

    <div class="d-flex flex-wrap align-center ga-3 pa-4">
      <v-btn v-if="canWrite" color="primary" prepend-icon="mdi-plus" @click="openCreate">Добавить правило</v-btn>
      <v-btn
        v-if="canWrite && !isUser"
        color="secondary"
        prepend-icon="mdi-memory"
        :loading="reloading"
        @click="reloadInMemory"
      >
        Обновить в памяти opensips
      </v-btn>

      <v-spacer />

      <v-pagination v-if="pageCount > 1" v-model="page" :length="pageCount" :total-visible="7" density="comfortable" />
    </div>

    <v-divider />

    <v-card-text class="d-flex align-center ga-2 text-caption text-medium-emphasis">
      <v-icon icon="mdi-information-outline" size="16" />
      <span v-if="isUser">
        Записей: {{ total }}. Таблица читается на каждый вызов check_user_blacklist(), reload не нужен.
      </span>
      <span v-else>
        Записей: {{ total }}. Таблица загружается в память при старте — правки применяет reload_blacklist.
      </span>
    </v-card-text>
  </v-card>

  <BlacklistRowDialog v-model="dialog" :kind="kind" :row="editing" :saving="saving" @save="save" />

  <ConfirmDialog
    v-model="confirmDelete"
    title="Удалить правило?"
    :text="`Правило для префикса ${rowToDelete?.prefix} будет удалено.`"
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
