<script setup>
import { computed, ref, watch } from 'vue'
import { rtpengineApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useServersStore } from '@/stores/servers'
import { useUiStore } from '@/stores/ui'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import NodeStateSwitch from '@/components/NodeStateSwitch.vue'
import RtpengineRowDialog from '@/components/RtpengineRowDialog.vue'

const auth = useAuthStore()
const servers = useServersStore()
const ui = useUiStore()

const rows = ref([])
const miAvailable = ref(true)
const miError = ref(null)
const loading = ref(false)
const saving = ref(false)
const reloading = ref(false)
const togglingId = ref(null)
const search = ref('')

const dialog = ref(false)
const editing = ref(null)
const confirmDelete = ref(false)
const rowToDelete = ref(null)
const softReload = ref(true)

const serverId = computed(() => servers.selectedId)
const canWrite = computed(() => auth.can('rtpengine:write'))

const headers = [
  { title: 'set_id', key: 'set_id', width: 100 },
  { title: 'socket', key: 'socket' },
  { title: 'weight', key: 'weight', width: 100, sortable: false },
  { title: 'Состояние', key: 'runtime_state', width: 200, sortable: false },
  { title: '', key: 'actions', width: 100, sortable: false, align: 'end' },
]

async function fetchRows() {
  if (!serverId.value) return
  loading.value = true
  try {
    const data = await rtpengineApi.list(serverId.value)
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
      await rtpengineApi.update(serverId.value, id, payload)
      ui.success('Сокет обновлён в БД')
    } else {
      await rtpengineApi.create(serverId.value, payload)
      ui.success('Сокет добавлен в БД')
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
    await rtpengineApi.remove(serverId.value, rowToDelete.value.id)
    ui.success('Сокет удалён из таблицы')
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
    const enabled = state === 'active'
    await rtpengineApi.setEnabled(serverId.value, row.id, enabled)
    ui.success(enabled ? `${row.socket} включён` : `${row.socket} выключен`)
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
    await rtpengineApi.reload(serverId.value, softReload.value)
    ui.success('rtpengine_reload выполнен')
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
          <v-card-title class="pa-0">RTPEngine</v-card-title>
          <v-card-subtitle class="pa-0">Сокеты медиасерверов (таблица rtpengine) и их состояние</v-card-subtitle>
        </div>
        <v-spacer />
        <v-text-field
          v-model="search"
          placeholder="Поиск по сокету"
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
        Состояние сокетов недоступно: {{ miError }}. Показаны только строки таблицы.
      </v-alert>

      <v-data-table
        :headers="headers"
        :items="rows"
        :loading="loading"
        :search="search"
        items-per-page="25"
        density="comfortable"
        class="border rounded"
        no-data-text="Таблица rtpengine пуста"
      >
        <template #item.socket="{ item }">
          <span class="font-monospace">{{ item.socket }}</span>
          <v-chip v-if="item.runtime && item.runtime.index !== null" size="x-small" class="ml-2" variant="tonal" label>
            index {{ item.runtime.index }}
          </v-chip>
        </template>

        <template #item.weight="{ item }">
          <span class="text-medium-emphasis">{{ item.runtime?.weight ?? '—' }}</span>
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
    </v-card-text>

    <v-divider />

    <div class="d-flex flex-wrap align-center ga-3 pa-4">
      <v-btn v-if="canWrite" color="primary" prepend-icon="mdi-plus" @click="openCreate">Добавить сокет</v-btn>
      <v-btn
        v-if="canWrite"
        color="secondary"
        prepend-icon="mdi-memory"
        :loading="reloading"
        @click="reloadInMemory"
      >
        Обновить в памяти opensips
      </v-btn>
      <v-switch
        v-if="canWrite"
        v-model="softReload"
        label="soft-режим"
        color="primary"
        hide-details
        density="compact"
      />
      <span v-if="canWrite" class="text-caption text-medium-emphasis">
        soft оставляет уже работающие сокеты нетронутыми
      </span>
    </div>

    <v-divider />

    <v-card-text class="d-flex align-center ga-2 text-caption text-medium-emphasis">
      <v-icon icon="mdi-information-outline" size="16" />
      Выключение сокета (rtpengine_enable) действует до перезапуска opensips и в таблицу не пишется.
      Красное состояние — сокет выключил сам модуль после неудачного пинга.
    </v-card-text>
  </v-card>

  <RtpengineRowDialog v-model="dialog" :row="editing" :saving="saving" @save="save" />

  <ConfirmDialog
    v-model="confirmDelete"
    title="Удалить сокет?"
    :text="`Строка ${rowToDelete?.socket} будет удалена из таблицы rtpengine.`"
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
