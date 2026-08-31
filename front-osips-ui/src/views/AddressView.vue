<script setup>
import { computed, ref, watch } from 'vue'
import { addressApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useServersStore } from '@/stores/servers'
import { useUiStore } from '@/stores/ui'
import AddressRowDialog from '@/components/AddressRowDialog.vue'
import ConfirmDialog from '@/components/ConfirmDialog.vue'

const auth = useAuthStore()
const servers = useServersStore()
const ui = useUiStore()

const rows = ref([])
const memoryOnly = ref([])
const miAvailable = ref(true)
const miError = ref(null)
const loading = ref(false)
const saving = ref(false)
const reloading = ref(false)
const search = ref('')

const dialog = ref(false)
const editing = ref(null)
const confirmDelete = ref(false)
const rowToDelete = ref(null)

const serverId = computed(() => servers.selectedId)
const canWrite = computed(() => auth.can('address:write'))
// строки таблицы, которых ещё нет в памяти opensips: нужен address_reload
const pending = computed(() => rows.value.filter((row) => row.in_memory === false).length)

const headers = [
  { title: 'grp', key: 'grp', width: 80 },
  { title: 'Адрес', key: 'ip' },
  { title: 'port', key: 'port', width: 90 },
  { title: 'proto', key: 'proto', width: 90 },
  { title: 'pattern', key: 'pattern' },
  { title: 'context_info', key: 'context_info' },
  { title: 'В памяти', key: 'in_memory', width: 130, sortable: false },
  { title: '', key: 'actions', width: 100, sortable: false, align: 'end' },
]

async function fetchRows() {
  if (!serverId.value) return
  loading.value = true
  try {
    const data = await addressApi.list(serverId.value)
    rows.value = data.rows
    memoryOnly.value = data.memory_only
    miAvailable.value = data.mi_available
    miError.value = data.mi_error
  } catch (error) {
    rows.value = []
    memoryOnly.value = []
    ui.error(error.uiMessage)
  } finally {
    loading.value = false
  }
}

watch(serverId, fetchRows, { immediate: true })

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
      await addressApi.update(serverId.value, id, payload)
      ui.success('Адрес обновлён в БД')
    } else {
      await addressApi.create(serverId.value, payload)
      ui.success('Адрес добавлен в БД')
    }
    dialog.value = false
    await fetchRows()
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
    await addressApi.remove(serverId.value, rowToDelete.value.id)
    ui.success('Адрес удалён из таблицы')
    confirmDelete.value = false
    await fetchRows()
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    saving.value = false
  }
}

async function reloadInMemory() {
  reloading.value = true
  try {
    await addressApi.reload(serverId.value)
    ui.success('address_reload выполнен')
    await fetchRows()
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    reloading.value = false
  }
}
</script>

<template>
  <v-card>
    <v-card-item>
      <div class="d-flex flex-wrap align-center ga-2">
        <div>
          <v-card-title class="pa-0">Доверенные адреса</v-card-title>
          <v-card-subtitle class="pa-0">Таблица address модуля permissions</v-card-subtitle>
        </div>
        <v-spacer />
        <v-text-field
          v-model="search"
          placeholder="Поиск по таблице"
          prepend-inner-icon="mdi-magnify"
          density="compact"
          hide-details
          clearable
          style="max-width: 260px"
        />
        <v-btn variant="text" prepend-icon="mdi-refresh" :loading="loading" @click="fetchRows">Обновить</v-btn>
      </div>
    </v-card-item>

    <v-divider />

    <v-card-text>
      <v-alert v-if="!miAvailable" type="warning" variant="tonal" density="compact" class="mb-4">
        Дамп из памяти недоступен: {{ miError }}. Показаны только строки таблицы.
      </v-alert>
      <v-alert v-else-if="pending" type="warning" variant="tonal" density="compact" class="mb-4">
        Строк, которых ещё нет в памяти opensips: {{ pending }}. Нажмите «Обновить в памяти opensips».
      </v-alert>
      <v-alert v-if="memoryOnly.length" type="info" variant="tonal" density="compact" class="mb-4">
        В памяти opensips есть {{ memoryOnly.length }} записей, которых нет в таблице — например,
        таблицу правили в обход интерфейса, а reload ещё не делали.
      </v-alert>

      <v-data-table
        :headers="headers"
        :items="rows"
        :loading="loading"
        :search="search"
        items-per-page="25"
        density="comfortable"
        class="border rounded"
        no-data-text="Таблица address пуста"
      >
        <template #item.ip="{ item }">
          <span class="font-monospace">{{ item.ip }}/{{ item.mask }}</span>
        </template>

        <template #item.port="{ item }">
          <span :class="{ 'text-medium-emphasis': !item.port }">{{ item.port || 'любой' }}</span>
        </template>

        <template #item.pattern="{ item }">
          <span class="font-monospace text-caption">{{ item.pattern || '—' }}</span>
        </template>

        <template #item.context_info="{ item }">
          <span class="text-medium-emphasis">{{ item.context_info || '—' }}</span>
        </template>

        <template #item.in_memory="{ item }">
          <v-chip
            size="small"
            :color="item.in_memory === null ? 'grey-lighten-1' : item.in_memory ? 'success' : 'warning'"
            variant="tonal"
            label
          >
            {{ item.in_memory === null ? 'н/д' : item.in_memory ? 'загружен' : 'нужен reload' }}
          </v-chip>
        </template>

        <template #item.actions="{ item }">
          <v-btn v-if="canWrite" icon="mdi-pencil" size="small" variant="text" @click="openEdit(item)" />
          <v-btn v-if="canWrite" icon="mdi-delete" size="small" variant="text" color="error" @click="askDelete(item)" />
        </template>
      </v-data-table>
    </v-card-text>

    <v-divider />

    <div class="d-flex flex-wrap align-center ga-3 pa-4">
      <v-btn v-if="canWrite" color="primary" prepend-icon="mdi-plus" @click="openCreate">Добавить адрес</v-btn>
      <v-btn
        v-if="canWrite"
        color="secondary"
        prepend-icon="mdi-memory"
        :loading="reloading"
        @click="reloadInMemory"
      >
        Обновить в памяти opensips
      </v-btn>
    </div>

    <v-divider />

    <v-card-text class="d-flex align-center ga-2 text-caption text-medium-emphasis">
      <v-icon icon="mdi-information-outline" size="16" />
      Состояние «в памяти» сверяется с выхлопом address_dump и subnet_dump.
    </v-card-text>
  </v-card>

  <AddressRowDialog v-model="dialog" :row="editing" :saving="saving" @save="save" />

  <ConfirmDialog
    v-model="confirmDelete"
    title="Удалить адрес?"
    :text="`Запись ${rowToDelete?.ip}/${rowToDelete?.mask} будет удалена из таблицы address.`"
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
