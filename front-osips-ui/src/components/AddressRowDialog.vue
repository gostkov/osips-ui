<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  row: { type: Object, default: null },
  saving: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'save'])

const EMPTY = { grp: 0, ip: '', mask: 32, port: 0, proto: 'any', pattern: '', context_info: '' }

const PROTOCOLS = ['any', 'udp', 'tcp', 'tls', 'sctp', 'ws', 'wss']

const form = ref({ ...EMPTY })
const valid = ref(false)

const required = (value) => (value !== null && value !== undefined && String(value).length > 0) || 'Обязательное поле'
const isIp = (value) => /^[0-9a-f.:]+$/i.test(String(value || '')) || 'IPv4 или IPv6 адрес'

watch(
  () => props.modelValue,
  (opened) => {
    if (opened) form.value = props.row ? { ...EMPTY, ...props.row } : { ...EMPTY }
  },
)

function submit() {
  const payload = { ...form.value }
  delete payload.id
  delete payload.in_memory
  delete payload.partition
  for (const key of ['pattern', 'context_info']) {
    if (payload[key] === '') payload[key] = null
  }
  emit('save', { id: props.row?.id ?? null, payload })
}
</script>

<template>
  <v-dialog
    :model-value="props.modelValue"
    max-width="640"
    persistent
    @update:model-value="emit('update:modelValue', $event)"
  >
    <v-card>
      <v-card-title>{{ props.row ? 'Редактирование адреса' : 'Новый доверенный адрес' }}</v-card-title>
      <v-card-text>
        <v-form v-model="valid" @submit.prevent="submit">
          <v-row dense>
            <v-col cols="12" sm="3">
              <v-text-field
                v-model.number="form.grp"
                label="grp"
                type="number"
                :rules="[required]"
                hint="Группа, её проверяет check_address()"
                persistent-hint
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="form.ip" label="ip" placeholder="10.0.0.1" :rules="[required, isIp]" />
            </v-col>
            <v-col cols="12" sm="3">
              <v-text-field
                v-model.number="form.mask"
                label="mask"
                type="number"
                :rules="[required]"
                hint="32 — один адрес"
                persistent-hint
              />
            </v-col>

            <v-col cols="12" sm="4">
              <v-text-field
                v-model.number="form.port"
                label="port"
                type="number"
                hint="0 — любой порт"
                persistent-hint
              />
            </v-col>
            <v-col cols="12" sm="4">
              <v-select v-model="form.proto" label="proto" :items="PROTOCOLS" />
            </v-col>
            <v-col cols="12" sm="4">
              <v-text-field
                v-model="form.context_info"
                label="context_info"
                hint="Возвращается в скрипт"
                persistent-hint
              />
            </v-col>

            <v-col cols="12">
              <v-text-field
                v-model="form.pattern"
                label="pattern"
                hint="Регулярное выражение для сверки с From/RURI, если оно задано в вызове check_address()"
                persistent-hint
              />
            </v-col>
          </v-row>
        </v-form>

        <v-alert type="info" variant="tonal" density="compact" class="mt-4">
          Запись попадает в таблицу address. Чтобы opensips её увидел, нажмите «Обновить в памяти
          opensips» (address_reload).
        </v-alert>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="emit('update:modelValue', false)">Отмена</v-btn>
        <v-btn color="primary" :disabled="!valid" :loading="props.saving" @click="submit">Сохранить</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
