<script setup>
import { computed, ref, watch } from 'vue'
import { dispatcherApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import DispatcherRowDialog from '@/components/DispatcherRowDialog.vue'
import NodeStateSwitch from '@/components/NodeStateSwitch.vue'

const props = defineProps({ serverId: { type: Number, required: true } })

const auth = useAuthStore()
const ui = useUiStore()

const rows = ref([])
const miAvailable = ref(true)
const miError = ref(null)
const loading = ref(false)
const reloading = ref(false)
const saving = ref(false)
const togglingId = ref(null)
const search = ref('')

const dialog = ref(false)
const editing = ref(null)
const confirmDelete = ref(false)
const rowToDelete = ref(null)

const canWrite = computed(() => auth.can('dispatcher:write'))

const headers = [
  { title: 'setid', key: 'setid', width: 90 },
  { title: 'destination', key: 'destination' },
  { title: 'description', key: 'description' },
  { title: 'socket', key: 'socket' },
  { title: 'weight', key: 'weight', width: 90 },
  { title: 'priority', key: 'priority', width: 90 },
  { title: 'Состояние', key: 'runtime_state', width: 190, sortable: false },
  { title: '', key: 'actions', width: 100, sortable: false, align: 'end' },
]

async function fetchRows() {
  if (!props.serverId) return
  loading.value = true
  try {
    const data = await dispatcherApi.list(props.serverId)
    rows.value = data.rows
    miAvailable.value = data.mi_available
    miError.value = data.mi_error
  } catch (error) {
    rows.value = []
    ui.error(error.uiMessage)
  } finally {
    loading.value = false
  }
}

watch(() => props.serverId, fetchRows, { immediate: true })

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
      await dispatcherApi.update(props.serverId, id, payload)
      ui.success('Строка обновлена в БД')
    } else {
      await dispatcherApi.create(props.serverId, payload)
      ui.success('Строка добавлена в БД')
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
    await dispatcherApi.remove(props.serverId, rowToDelete.value.id)
    ui.success('Строка удалена')
    confirmDelete.value = false
    await fetchRows()
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    saving.value = false
  }
}

async function changeState(row, state) {
  togglingId.value = row.id
  try {
    await dispatcherApi.setState(props.serverId, row.id, state)
    ui.success(state === 'active' ? `${row.destination} возвращена в работу` : `${row.destination} выведена из обслуживания`)
    await fetchRows()
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    togglingId.value = null
  }
}

async function reloadInMemory() {
  reloading.value = true
  try {
    await dispatcherApi.reload(props.serverId)
    ui.success('ds_reload выполнен')
    await fetchRows()
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    reloading.value = false
  }
}
</script>

<template>
  <div>
    <v-alert v-if="!miAvailable" type="warning" variant="tonal" density="compact" class="mb-4">
      Состояние нод недоступно: {{ miError }}. Показаны только данные из таблицы БД.
    </v-alert>

    <div class="d-flex flex-wrap align-center ga-2 mb-4">
      <v-text-field
        v-model="search"
        placeholder="Поиск по таблице"
        prepend-inner-icon="mdi-magnify"
        density="compact"
        hide-details
        clearable
        style="max-width: 320px"
      />
      <v-spacer />
      <v-btn variant="text" prepend-icon="mdi-refresh" :loading="loading" @click="fetchRows">Обновить</v-btn>
      <v-btn
        v-if="canWrite"
        color="secondary"
        prepend-icon="mdi-memory"
        :loading="reloading"
        @click="reloadInMemory"
      >
        Обновить в памяти opensips
      </v-btn>
      <v-btn v-if="canWrite" color="primary" prepend-icon="mdi-plus" @click="openCreate">Добавить ноду</v-btn>
    </div>

    <v-data-table
      :headers="headers"
      :items="rows"
      :loading="loading"
      :search="search"
      items-per-page="25"
      density="comfortable"
      class="border rounded"
      no-data-text="Таблица dispatcher пуста"
    >
      <template #item.destination="{ item }">
        <span class="font-monospace">{{ item.destination }}</span>
      </template>

      <template #item.runtime_state="{ item }">
        <NodeStateSwitch
          :state="item.runtime_state"
          :disabled="!canWrite"
          :loading="togglingId === item.id"
          @change="changeState(item, $event)"
        />
      </template>

      <template #item.actions="{ item }">
        <v-btn v-if="canWrite" icon="mdi-pencil" size="small" variant="text" @click="openEdit(item)" />
        <v-btn v-if="canWrite" icon="mdi-delete" size="small" variant="text" color="error" @click="askDelete(item)" />
      </template>
    </v-data-table>

    <DispatcherRowDialog v-model="dialog" :row="editing" :saving="saving" @save="save" />

    <ConfirmDialog
      v-model="confirmDelete"
      title="Удалить строку?"
      :text="`Строка ${rowToDelete?.destination} будет удалена из таблицы dispatcher.`"
      confirm-text="Удалить"
      color="error"
      :loading="saving"
      @confirm="remove"
    />
  </div>
</template>

<style scoped>
.font-monospace {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
</style>
