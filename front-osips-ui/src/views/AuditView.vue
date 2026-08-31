<script setup>
import { onMounted, ref, watch } from 'vue'
import { auditApi } from '@/api'
import { useUiStore } from '@/stores/ui'

const ui = useUiStore()

const items = ref([])
const total = ref(0)
const page = ref(1)
const perPage = 50
const loading = ref(false)
const filters = ref({ username: '', action: '' })

const headers = [
  { title: 'Время', key: 'created_at', width: 180 },
  { title: 'Пользователь', key: 'username', width: 150 },
  { title: 'Роль', key: 'role', width: 120 },
  { title: 'Действие', key: 'action', width: 190 },
  { title: 'Сервер', key: 'server_name', width: 140 },
  { title: 'Объект', key: 'target' },
  { title: 'Детали', key: 'details' },
]

function formatDate(value) {
  if (!value) return '—'
  return new Date(`${value}Z`).toLocaleString('ru-RU')
}

async function fetchAudit() {
  loading.value = true
  try {
    const data = await auditApi.list({
      page: page.value,
      per_page: perPage,
      username: filters.value.username || undefined,
      action: filters.value.action || undefined,
    })
    items.value = data.items
    total.value = data.total
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    loading.value = false
  }
}

onMounted(fetchAudit)
watch(page, fetchAudit)

let timer = null
watch(
  filters,
  () => {
    clearTimeout(timer)
    timer = setTimeout(() => {
      page.value = 1
      fetchAudit()
    }, 350)
  },
  { deep: true },
)
</script>

<template>
  <v-card>
    <v-card-item>
      <div class="d-flex flex-wrap align-center ga-2">
        <v-card-title class="pa-0">Журнал действий</v-card-title>
        <v-spacer />
        <v-text-field
          v-model="filters.username"
          placeholder="Пользователь"
          density="compact"
          hide-details
          clearable
          style="max-width: 200px"
        />
        <v-text-field
          v-model="filters.action"
          placeholder="Действие, например dialplan.create"
          density="compact"
          hide-details
          clearable
          style="max-width: 260px"
        />
        <v-btn variant="text" prepend-icon="mdi-refresh" :loading="loading" @click="fetchAudit">Обновить</v-btn>
      </div>
    </v-card-item>

    <v-divider />

    <v-data-table
      :headers="headers"
      :items="items"
      :loading="loading"
      density="compact"
      :items-per-page="perPage"
      hide-default-footer
    >
      <template #item.created_at="{ item }">
        <span class="text-caption">{{ formatDate(item.created_at) }}</span>
      </template>
      <template #item.details="{ item }">
        <span class="text-caption text-medium-emphasis">{{ item.details }}</span>
      </template>
    </v-data-table>

    <v-divider />

    <div class="d-flex align-center pa-4">
      <div class="text-caption text-medium-emphasis">Всего записей: {{ total }}</div>
      <v-spacer />
      <v-pagination
        v-if="total > perPage"
        v-model="page"
        :length="Math.ceil(total / perPage)"
        :total-visible="7"
        density="comfortable"
      />
    </div>
  </v-card>
</template>
