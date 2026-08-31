<script setup>
import { onMounted, ref } from 'vue'
import { serversApi } from '@/api'
import { useServersStore } from '@/stores/servers'
import { useUiStore } from '@/stores/ui'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import ServerDialog from '@/components/ServerDialog.vue'

const servers = useServersStore()
const ui = useUiStore()

const loading = ref(false)
const saving = ref(false)
const dialog = ref(false)
const editing = ref(null)
const confirmDelete = ref(false)
const serverToDelete = ref(null)
const checking = ref(null)
const checks = ref({})

const headers = [
  { title: 'Имя', key: 'name' },
  { title: 'IP', key: 'ip_address' },
  { title: 'http MI', key: 'mi', sortable: false },
  { title: 'БД', key: 'db', sortable: false },
  { title: 'Статус', key: 'is_active', width: 110 },
  { title: '', key: 'actions', width: 150, sortable: false, align: 'end' },
]

async function fetchServers() {
  loading.value = true
  try {
    await servers.fetch(true)
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    loading.value = false
  }
}

onMounted(fetchServers)

function openCreate() {
  editing.value = null
  dialog.value = true
}

function openEdit(server) {
  editing.value = server
  dialog.value = true
}

async function save({ id, payload }) {
  saving.value = true
  try {
    if (id) {
      await serversApi.update(id, payload)
      ui.success('Сервер обновлён')
    } else {
      await serversApi.create(payload)
      ui.success('Сервер добавлен')
    }
    dialog.value = false
    await fetchServers()
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    saving.value = false
  }
}

function askDelete(server) {
  serverToDelete.value = server
  confirmDelete.value = true
}

async function remove() {
  saving.value = true
  try {
    await serversApi.remove(serverToDelete.value.id)
    ui.success('Сервер удалён')
    confirmDelete.value = false
    await fetchServers()
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    saving.value = false
  }
}

async function check(server) {
  checking.value = server.id
  try {
    checks.value = { ...checks.value, [server.id]: await serversApi.check(server.id) }
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    checking.value = null
  }
}
</script>

<template>
  <v-card>
    <v-card-item>
      <div class="d-flex align-center ga-2">
        <div>
          <v-card-title class="pa-0">Серверы OpenSIPS</v-card-title>
          <v-card-subtitle class="pa-0">Реестр управляемых серверов: доступ к БД и http MI</v-card-subtitle>
        </div>
        <v-spacer />
        <v-btn variant="text" prepend-icon="mdi-refresh" :loading="loading" @click="fetchServers">Обновить</v-btn>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreate">Добавить сервер</v-btn>
      </div>
    </v-card-item>

    <v-divider />

    <v-data-table :headers="headers" :items="servers.items" :loading="loading" density="comfortable" items-per-page="25">
      <template #item.name="{ item }">
        <div class="font-weight-medium">{{ item.name }}</div>
        <div class="text-caption text-medium-emphasis">{{ item.description }}</div>
      </template>

      <template #item.mi="{ item }">
        <template v-if="item.has_mi">
          <span class="font-monospace text-caption">{{ item.mi_host || item.ip_address }}:{{ item.mi_port }}</span>
          <v-chip
            v-if="checks[item.id]"
            size="x-small"
            class="ml-2"
            :color="checks[item.id].mi.ok ? 'success' : 'error'"
            variant="tonal"
            label
          >
            {{ checks[item.id].mi.ok ? 'ok' : 'ошибка' }}
          </v-chip>
        </template>
        <span v-else class="text-medium-emphasis">—</span>
      </template>

      <template #item.db="{ item }">
        <template v-if="item.has_db">
          <span class="font-monospace text-caption">{{ item.db_host }}:{{ item.db_port }}/{{ item.db_name }}</span>
          <v-chip
            v-if="checks[item.id]"
            size="x-small"
            class="ml-2"
            :color="checks[item.id].db.ok ? 'success' : 'error'"
            variant="tonal"
            label
          >
            {{ checks[item.id].db.ok ? 'ok' : 'ошибка' }}
          </v-chip>
        </template>
        <span v-else class="text-medium-emphasis">—</span>
      </template>

      <template #item.is_active="{ item }">
        <v-chip size="small" :color="item.is_active ? 'success' : 'grey'" variant="tonal" label>
          {{ item.is_active ? 'активен' : 'выключен' }}
        </v-chip>
      </template>

      <template #item.actions="{ item }">
        <v-btn
          icon="mdi-lan-connect"
          size="small"
          variant="text"
          :loading="checking === item.id"
          title="Проверить доступность"
          @click="check(item)"
        />
        <v-btn icon="mdi-pencil" size="small" variant="text" @click="openEdit(item)" />
        <v-btn icon="mdi-delete" size="small" variant="text" color="error" @click="askDelete(item)" />
      </template>
    </v-data-table>

    <v-card-text v-if="Object.keys(checks).length" class="text-caption text-medium-emphasis">
      <div v-for="(result, id) in checks" :key="id">
        <template v-if="!result.db.ok || !result.mi.ok">
          <b>{{ servers.items.find((server) => server.id === Number(id))?.name }}:</b>
          <span v-if="!result.db.ok"> БД — {{ result.db.detail }}.</span>
          <span v-if="!result.mi.ok"> MI — {{ result.mi.detail }}.</span>
        </template>
      </div>
    </v-card-text>
  </v-card>

  <ServerDialog v-model="dialog" :server="editing" :saving="saving" @save="save" />

  <ConfirmDialog
    v-model="confirmDelete"
    title="Удалить сервер?"
    :text="`Сервер «${serverToDelete?.name}» будет удалён из реестра. На сам OpenSIPS это не влияет.`"
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
