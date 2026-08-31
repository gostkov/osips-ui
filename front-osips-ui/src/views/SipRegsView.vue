<script setup>
import { computed, ref, watch } from 'vue'
import { sipRegsApi } from '@/api'
import { useServersStore } from '@/stores/servers'
import { useUiStore } from '@/stores/ui'

const servers = useServersStore()
const ui = useUiStore()

const PER_PAGE = 25
const SOURCE_KEY = 'osips-ui-sipregs-source'

const items = ref([])
const total = ref(0)
const users = ref(0)
const page = ref(1)
const search = ref('')
const onlyActive = ref(false)
const source = ref(localStorage.getItem(SOURCE_KEY) === 'mi' ? 'mi' : 'db')
const loading = ref(false)
const failed = ref(false)
const expanded = ref(new Set())

const serverId = computed(() => servers.selectedId)
const server = computed(() => servers.selected)
const pageCount = computed(() => Math.max(1, Math.ceil(total.value / PER_PAGE)))
const fromMi = computed(() => source.value === 'mi')

const STATUS_META = {
  active: { color: 'success', label: 'активна' },
  expired: { color: 'error', label: 'истекла' },
  permanent: { color: 'info', label: 'постоянная' },
}

function statusMeta(status) {
  return STATUS_META[status] || { color: 'grey', label: status }
}

function humanSeconds(seconds) {
  const value = Math.abs(seconds)
  if (value < 60) return `${value} сек`
  if (value < 3600) return `${Math.floor(value / 60)} мин`
  if (value < 86400) return `${Math.floor(value / 3600)} ч`
  return `${Math.floor(value / 86400)} дн`
}

function expiresText(item) {
  if (item.status === 'permanent') return 'без истечения'
  if (item.expires_in === null || item.expires_in === undefined) return '—'
  return item.expires_in > 0 ? `через ${humanSeconds(item.expires_in)}` : `${humanSeconds(item.expires_in)} назад`
}

function formatDate(value) {
  if (!value) return '—'
  // время приходит из БД opensips как есть, без часового пояса - показываем без пересчёта
  return String(value).replace('T', ' ').slice(0, 19)
}

function details(item) {
  const common = [
    { title: 'contact_id', value: item.id },
    { title: 'domain', value: item.domain },
    { title: 'path', value: item.path },
    { title: 'socket', value: item.socket },
    { title: 'call-id', value: item.callid },
    { title: 'cseq', value: item.cseq },
    { title: 'q', value: item.q },
    { title: 'flags / cflags', value: [item.flags, item.cflags].filter((v) => v !== null && v !== undefined && v !== '').join(' / ') },
    { title: 'methods', value: item.methods },
    { title: 'sip_instance', value: item.sip_instance },
    { title: 'attr', value: item.attr },
    { title: 'kv_store', value: item.kv_store },
    { title: 'expires', value: formatDate(item.expires_at) },
  ]
  if (fromMi.value) {
    return common.concat([
      { title: 'state', value: item.state },
      { title: 'ping-latency, мкс', value: item.ping_latency },
      { title: 'usrloc domain', value: item.table },
    ])
  }
  return common.concat([{ title: 'last_modified', value: formatDate(item.last_modified) }])
}

function toggle(id) {
  const next = new Set(expanded.value)
  next.has(id) ? next.delete(id) : next.add(id)
  expanded.value = next
}

async function fetchData() {
  if (!serverId.value) {
    items.value = []
    return
  }
  loading.value = true
  try {
    const data = await sipRegsApi.list(serverId.value, {
      source: source.value,
      page: page.value,
      per_page: PER_PAGE,
      search: search.value || undefined,
      only_active: onlyActive.value || undefined,
    })
    items.value = data.items
    total.value = data.total
    users.value = data.users
    failed.value = false
  } catch (error) {
    items.value = []
    total.value = 0
    users.value = 0
    failed.value = true
    ui.error(error.uiMessage)
  } finally {
    loading.value = false
    expanded.value = new Set()
  }
}

// источник переключаем только на тот, что настроен у выбранного сервера
watch(server, (value) => {
  if (!value) return
  if (fromMi.value && !value.has_mi && value.has_db) source.value = 'db'
  if (!fromMi.value && !value.has_db && value.has_mi) source.value = 'mi'
}, { immediate: true })

watch(serverId, () => {
  page.value = 1
  fetchData()
}, { immediate: true })

watch(source, (value) => {
  localStorage.setItem(SOURCE_KEY, value)
  page.value = 1
  fetchData()
})

watch(page, fetchData)
watch(onlyActive, () => {
  page.value = 1
  fetchData()
})

let searchTimer = null
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    fetchData()
  }, 350)
})
</script>

<template>
  <v-card>
    <v-card-item>
      <div class="d-flex flex-wrap align-center ga-2">
        <div>
          <v-card-title class="pa-0">SIP-регистрации</v-card-title>
          <v-card-subtitle class="pa-0">
            Сервер «{{ server?.name || '—' }}» ·
            {{ fromMi ? 'память opensips (ul_dump)' : 'таблица location' }}
          </v-card-subtitle>
        </div>
        <v-spacer />
        <v-btn-toggle v-model="source" mandatory density="comfortable" variant="outlined" divided>
          <v-btn value="db" size="small" prepend-icon="mdi-database" :disabled="server && !server.has_db">
            Из БД
          </v-btn>
          <v-btn value="mi" size="small" prepend-icon="mdi-memory" :disabled="server && !server.has_mi">
            Из памяти
          </v-btn>
        </v-btn-toggle>
        <v-switch
          v-model="onlyActive"
          label="Только активные"
          color="primary"
          density="compact"
          hide-details
          class="flex-grow-0"
        />
        <v-text-field
          v-model="search"
          placeholder="Номер, contact, received, user-agent"
          prepend-inner-icon="mdi-magnify"
          density="compact"
          hide-details
          clearable
          style="max-width: 300px"
        />
        <v-btn variant="text" prepend-icon="mdi-refresh" :loading="loading" @click="fetchData">Обновить</v-btn>
      </div>
    </v-card-item>

    <v-alert
      v-if="fromMi && loading"
      type="info"
      variant="tonal"
      density="compact"
      class="mx-4 mb-2"
      icon="mdi-timer-sand"
    >
      ul_dump выгружает всю память usrloc — на большой базе ответ может занять до 15 секунд.
    </v-alert>

    <v-divider />

    <v-table density="comfortable">
      <thead>
        <tr>
          <th style="width: 48px" />
          <th>Абонент</th>
          <th>Contact</th>
          <th>Через</th>
          <th>User-Agent</th>
          <th style="width: 200px">Регистрация</th>
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading">
          <td colspan="6" class="text-center py-6">
            <v-progress-circular indeterminate size="24" />
          </td>
        </tr>
        <tr v-else-if="!items.length">
          <td colspan="6" class="text-center text-medium-emphasis py-6">
            <template v-if="failed">Не удалось получить данные ({{ fromMi ? 'MI ul_dump' : 'БД opensips' }})</template>
            <template v-else-if="search || onlyActive">Ничего не найдено</template>
            <template v-else-if="fromMi">В памяти opensips нет ни одной регистрации</template>
            <template v-else>
              Таблица location пуста. Если абоненты зарегистрированы, проверьте <code>db_mode</code>
              модуля usrloc: при 0/1 регистрации живут только в памяти — смотрите их через «Из памяти».
            </template>
          </td>
        </tr>
        <template v-for="item in items" v-else :key="item.id">
          <tr>
            <td>
              <v-btn
                :icon="expanded.has(item.id) ? 'mdi-chevron-up' : 'mdi-chevron-down'"
                size="small"
                variant="text"
                @click="toggle(item.id)"
              />
            </td>
            <td>
              <span class="font-monospace">{{ item.aor }}</span>
            </td>
            <td class="font-monospace text-truncate" style="max-width: 320px" :title="item.contact">
              {{ item.contact }}
            </td>
            <td class="font-monospace text-medium-emphasis">{{ item.received || item.socket || '—' }}</td>
            <td class="text-truncate" style="max-width: 200px" :title="item.user_agent">
              {{ item.user_agent || '—' }}
            </td>
            <td>
              <v-chip size="small" :color="statusMeta(item.status).color" variant="tonal" label>
                {{ statusMeta(item.status).label }}
              </v-chip>
              <span class="text-caption text-medium-emphasis ml-2">{{ expiresText(item) }}</span>
            </td>
          </tr>
          <tr v-if="expanded.has(item.id)" class="details-row">
            <td colspan="6">
              <v-row dense class="py-2">
                <v-col v-for="field in details(item)" :key="field.title" cols="12" sm="6" md="4">
                  <div class="text-caption text-medium-emphasis">{{ field.title }}</div>
                  <div class="font-monospace text-body-2 text-break">
                    {{ field.value === null || field.value === undefined || field.value === '' ? '—' : field.value }}
                  </div>
                </v-col>
              </v-row>
            </td>
          </tr>
        </template>
      </tbody>
    </v-table>

    <v-divider />

    <div class="d-flex flex-wrap align-center ga-3 pa-4">
      <span class="text-caption text-medium-emphasis">
        Контактов: {{ total }} · абонентов: {{ users }}
      </span>
      <v-spacer />
      <v-pagination
        v-if="pageCount > 1"
        v-model="page"
        :length="pageCount"
        :total-visible="7"
        density="comfortable"
      />
    </div>
  </v-card>
</template>

<style scoped>
.font-monospace {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.details-row td {
  background: rgba(var(--v-theme-on-surface), 0.03);
}

.text-break {
  word-break: break-all;
}
</style>
