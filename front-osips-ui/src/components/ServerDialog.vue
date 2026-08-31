<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  server: { type: Object, default: null },
  saving: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'save'])

const EMPTY = {
  name: '',
  description: '',
  ip_address: '',
  mi_host: '',
  mi_port: 8888,
  mi_path: '/mi',
  mi_username: '',
  db_host: '',
  db_port: 3306,
  db_name: 'opensips',
  db_user: '',
  dispatcher_partition: 'default',
  is_active: true,
  sort_order: 100,
}

const form = ref({ ...EMPTY })
// секреты не приходят с backend: пустое поле = оставить как есть
const secrets = ref({ mi_password: '', db_password: '' })
const valid = ref(false)

const required = (value) => Boolean(String(value ?? '').length) || 'Обязательное поле'

watch(
  () => props.modelValue,
  (opened) => {
    if (opened) {
      form.value = props.server ? { ...EMPTY, ...props.server } : { ...EMPTY }
      secrets.value = { mi_password: '', db_password: '' }
    }
  },
)

function submit() {
  const payload = { ...form.value }
  delete payload.id
  delete payload.has_db
  delete payload.has_mi
  delete payload.created_at
  delete payload.updated_at

  for (const [key, value] of Object.entries(secrets.value)) {
    if (value !== '') payload[key] = value
    else if (!props.server) payload[key] = null
  }
  emit('save', { id: props.server?.id ?? null, payload })
}
</script>

<template>
  <v-dialog
    :model-value="props.modelValue"
    max-width="820"
    persistent
    scrollable
    @update:model-value="emit('update:modelValue', $event)"
  >
    <v-card>
      <v-card-title>{{ props.server ? `Сервер «${props.server.name}»` : 'Новый сервер OpenSIPS' }}</v-card-title>
      <v-divider />
      <v-card-text style="max-height: 70vh">
        <v-form v-model="valid" @submit.prevent="submit">
          <div class="text-subtitle-2 mb-2">Общее</div>
          <v-row dense>
            <v-col cols="12" sm="6">
              <v-text-field v-model="form.name" label="Имя" :rules="[required]" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="form.ip_address" label="IP-адрес" :rules="[required]" />
            </v-col>
            <v-col cols="12">
              <v-text-field v-model="form.description" label="Описание" />
            </v-col>
          </v-row>

          <v-divider class="my-4" />
          <div class="text-subtitle-2 mb-2">HTTP MI (модуль mi_http)</div>
          <v-row dense>
            <v-col cols="12" sm="5">
              <v-text-field v-model="form.mi_host" label="Хост MI" :placeholder="form.ip_address || '127.0.0.1'" />
            </v-col>
            <v-col cols="6" sm="3">
              <v-text-field v-model.number="form.mi_port" label="Порт MI" type="number" />
            </v-col>
            <v-col cols="6" sm="4">
              <v-text-field v-model="form.mi_path" label="Путь" placeholder="/mi" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="form.mi_username" label="Basic-auth логин (если есть)" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="secrets.mi_password"
                label="Basic-auth пароль"
                type="password"
                autocomplete="new-password"
                :placeholder="props.server ? 'оставьте пустым, чтобы не менять' : ''"
              />
            </v-col>
          </v-row>

          <v-divider class="my-4" />
          <div class="text-subtitle-2 mb-2">База данных OpenSIPS</div>
          <v-row dense>
            <v-col cols="12" sm="5">
              <v-text-field v-model="form.db_host" label="Хост" />
            </v-col>
            <v-col cols="6" sm="3">
              <v-text-field v-model.number="form.db_port" label="Порт" type="number" />
            </v-col>
            <v-col cols="6" sm="4">
              <v-text-field v-model="form.db_name" label="База" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="form.db_user" label="Пользователь" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="secrets.db_password"
                label="Пароль"
                type="password"
                autocomplete="new-password"
                :placeholder="props.server ? 'оставьте пустым, чтобы не менять' : ''"
              />
            </v-col>
          </v-row>

          <v-divider class="my-4" />
          <div class="text-subtitle-2 mb-2">Дополнительно</div>
          <v-row dense>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="form.dispatcher_partition"
                label="Партиция dispatcher"
                hint="Обычно default"
                persistent-hint
              />
            </v-col>
            <v-col cols="6" sm="3">
              <v-text-field v-model.number="form.sort_order" label="Порядок в списке" type="number" />
            </v-col>
            <v-col cols="6" sm="3" class="d-flex align-center">
              <v-switch v-model="form.is_active" label="Активен" color="primary" hide-details />
            </v-col>
          </v-row>
        </v-form>
      </v-card-text>
      <v-divider />
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="emit('update:modelValue', false)">Отмена</v-btn>
        <v-btn color="primary" :disabled="!valid" :loading="props.saving" @click="submit">Сохранить</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
