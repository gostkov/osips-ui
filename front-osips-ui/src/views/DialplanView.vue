<script setup>
import { computed, ref, watch } from 'vue'
import { dialplanApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useServersStore } from '@/stores/servers'
import { useUiStore } from '@/stores/ui'
import ConfirmDialog from '@/components/ConfirmDialog.vue'
import DialplanRowDialog from '@/components/DialplanRowDialog.vue'

const auth = useAuthStore()
const servers = useServersStore()
const ui = useUiStore()

const PER_PAGE = 25

const items = ref([])
const dpids = ref([])
const total = ref(0)
const page = ref(1)
const search = ref('')
const dpidFilter = ref(null)
const onlyEnabled = ref(false)
const loading = ref(false)
const saving = ref(false)
const reloading = ref(false)

const dialog = ref(false)
const editing = ref(null)
const confirmDelete = ref(false)
const rowToDelete = ref(null)

// dp_translate: прогон строки через правила набора прямо из интерфейса
const translateDialog = ref(false)
const translateForm = ref({ dpid: null, value: '' })
const translateResult = ref(null)
const translating = ref(false)

const serverId = computed(() => servers.selectedId)
const canWrite = computed(() => auth.can('dialplan:write'))
const pageCount = computed(() => Math.max(1, Math.ceil(total.value / PER_PAGE)))

const dpidItems = computed(() => [
  { title: 'Все наборы', value: null },
  ...dpids.value.map((item) => ({ title: `dpid ${item.dpid} (${item.rules})`, value: item.dpid })),
])

async function fetchDpids() {
  if (!serverId.value) return
  try {
    dpids.value = await dialplanApi.dpids(serverId.value)
  } catch (error) {
    dpids.value = []
    ui.error(error.uiMessage)
  }
}

async function fetchRules() {
  if (!serverId.value) return
  loading.value = true
  try {
    const data = await dialplanApi.list(serverId.value, {
      page: page.value,
      per_page: PER_PAGE,
      search: search.value || undefined,
      dpid: dpidFilter.value ?? undefined,
      only_enabled: onlyEnabled.value || undefined,
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

async function reload() {
  await Promise.all([fetchDpids(), fetchRules()])
}

watch(
  serverId,
  () => {
    page.value = 1
    dpidFilter.value = null
    reload()
  },
  { immediate: true },
)

watch(page, fetchRules)
watch([dpidFilter, onlyEnabled], () => {
  page.value = 1
  fetchRules()
})

let searchTimer = null
watch(search, () => {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    fetchRules()
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
      await dialplanApi.update(serverId.value, id, payload)
      ui.success('Правило обновлено в БД')
    } else {
      await dialplanApi.create(serverId.value, payload)
      ui.success('Правило добавлено в БД')
    }
    dialog.value = false
    await reload()
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
    await dialplanApi.remove(serverId.value, rowToDelete.value.id)
    ui.success('Правило удалено')
    confirmDelete.value = false
    await reload()
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    saving.value = false
  }
}

async function reloadInMemory() {
  reloading.value = true
  try {
    await dialplanApi.reload(serverId.value)
    ui.success('dp_reload выполнен')
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    reloading.value = false
  }
}

function openTranslate() {
  translateResult.value = null
  translateForm.value = { dpid: dpidFilter.value ?? dpids.value[0]?.dpid ?? null, value: '' }
  translateDialog.value = true
}

async function runTranslate() {
  translating.value = true
  translateResult.value = null
  try {
    translateResult.value = await dialplanApi.translate(serverId.value, {
      dpid: translateForm.value.dpid,
      value: translateForm.value.value,
    })
  } catch (error) {
    // «No translation» opensips отдаёт как ошибку MI — показываем её текстом, а не снекбаром
    translateResult.value = { error: error.uiMessage }
  } finally {
    translating.value = false
  }
}
</script>

<template>
  <v-card>
    <v-card-item>
      <div class="d-flex flex-wrap align-center ga-2">
        <div>
          <v-card-title class="pa-0">Dialplan</v-card-title>
          <v-card-subtitle class="pa-0">Правила трансляции строк (таблица dialplan)</v-card-subtitle>
        </div>
        <v-spacer />
        <v-select
          v-model="dpidFilter"
          :items="dpidItems"
          label="Набор"
          density="compact"
          hide-details
          style="max-width: 200px"
        />
        <v-text-field
          v-model="search"
          placeholder="Поиск по выражениям"
          prepend-inner-icon="mdi-magnify"
          density="compact"
          hide-details
          clearable
          style="max-width: 260px"
        />
        <v-switch v-model="onlyEnabled" label="Только включённые" color="primary" hide-details density="compact" />
        <v-btn variant="text" prepend-icon="mdi-refresh" :loading="loading" @click="reload">Обновить</v-btn>
      </div>
    </v-card-item>

    <v-divider />

    <v-table density="comfortable">
      <thead>
        <tr>
          <th style="width: 90px">dpid</th>
          <th style="width: 70px">pr</th>
          <th>match_exp</th>
          <th>subst_exp → repl_exp</th>
          <th>attrs</th>
          <th style="width: 120px">Состояние</th>
          <th style="width: 100px" />
        </tr>
      </thead>
      <tbody>
        <tr v-if="loading">
          <td colspan="7" class="text-center py-6"><v-progress-circular indeterminate size="24" /></td>
        </tr>
        <tr v-else-if="!items.length">
          <td colspan="7" class="text-center text-medium-emphasis py-6">Правила не найдены</td>
        </tr>
        <tr v-for="item in items" v-else :key="item.id">
          <td>{{ item.dpid }}</td>
          <td class="text-medium-emphasis">{{ item.pr }}</td>
          <td>
            <span class="font-monospace">{{ item.match_exp }}</span>
            <v-chip size="x-small" class="ml-2" variant="tonal" label>
              {{ item.match_op === 1 ? 'regex' : 'строка' }}
            </v-chip>
            <v-chip v-if="item.match_flags & 1" size="x-small" class="ml-1" variant="tonal" label>
              без регистра
            </v-chip>
            <div v-if="item.timerec" class="text-caption text-medium-emphasis">
              <v-icon icon="mdi-clock-outline" size="12" /> {{ item.timerec }}
            </div>
          </td>
          <td>
            <span v-if="item.subst_exp || item.repl_exp" class="font-monospace">
              {{ item.subst_exp || '—' }} → {{ item.repl_exp || '—' }}
            </span>
            <span v-else class="text-medium-emphasis">без замены</span>
          </td>
          <td class="font-monospace text-caption">{{ item.attrs || '—' }}</td>
          <td>
            <v-chip size="small" :color="item.disabled ? 'grey' : 'success'" variant="tonal" label>
              {{ item.disabled ? 'выключено' : 'включено' }}
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
        v-if="canWrite"
        color="secondary"
        prepend-icon="mdi-memory"
        :loading="reloading"
        @click="reloadInMemory"
      >
        Обновить в памяти opensips
      </v-btn>
      <v-btn variant="outlined" prepend-icon="mdi-play-circle-outline" :disabled="!dpids.length" @click="openTranslate">
        Проверить правило
      </v-btn>

      <v-spacer />

      <v-pagination v-if="pageCount > 1" v-model="page" :length="pageCount" :total-visible="7" density="comfortable" />
    </div>

    <v-divider />

    <v-card-text class="d-flex align-center ga-2 text-caption text-medium-emphasis">
      <v-icon icon="mdi-information-outline" size="16" />
      Всего правил по фильтру: {{ total }}. Правки в таблице применяются после dp_reload.
    </v-card-text>
  </v-card>

  <DialplanRowDialog v-model="dialog" :row="editing" :dpids="dpids" :saving="saving" @save="save" />

  <ConfirmDialog
    v-model="confirmDelete"
    title="Удалить правило?"
    :text="`Правило ${rowToDelete?.match_exp} (dpid ${rowToDelete?.dpid}) будет удалено из таблицы dialplan.`"
    confirm-text="Удалить"
    color="error"
    :loading="saving"
    @confirm="remove"
  />

  <v-dialog v-model="translateDialog" max-width="560">
    <v-card>
      <v-card-title>Проверка правила (dp_translate)</v-card-title>
      <v-card-text>
        <v-row dense>
          <v-col cols="12" sm="4">
            <v-select
              v-model="translateForm.dpid"
              label="dpid"
              :items="dpids.map((item) => item.dpid)"
              density="comfortable"
            />
          </v-col>
          <v-col cols="12" sm="8">
            <v-text-field
              v-model="translateForm.value"
              label="Входная строка"
              placeholder="79001234567"
              density="comfortable"
              @keyup.enter="runTranslate"
            />
          </v-col>
        </v-row>

        <v-alert v-if="translateResult?.error" type="warning" variant="tonal" density="compact">
          {{ translateResult.error }}
        </v-alert>
        <v-alert v-else-if="translateResult" type="success" variant="tonal" density="compact">
          <div>
            Результат: <span class="font-monospace">{{ translateResult.output }}</span>
          </div>
          <div v-if="translateResult.attributes" class="text-caption mt-1">
            attrs: <span class="font-monospace">{{ translateResult.attributes }}</span>
          </div>
        </v-alert>

        <div class="text-caption text-medium-emphasis mt-2">
          Проверка идёт по правилам, загруженным в память opensips, а не по таблице БД.
        </div>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="translateDialog = false">Закрыть</v-btn>
        <v-btn
          color="primary"
          :loading="translating"
          :disabled="!translateForm.value || translateForm.dpid === null"
          @click="runTranslate"
        >
          Проверить
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.font-monospace {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
</style>
