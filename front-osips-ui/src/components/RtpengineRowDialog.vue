<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  row: { type: Object, default: null },
  saving: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'save'])

const EMPTY = { socket: '', set_id: 0 }

const form = ref({ ...EMPTY })
const valid = ref(false)

const required = (value) => (value !== null && value !== undefined && String(value).length > 0) || 'Обязательное поле'
// сокет rtpengine задаётся как proto:host:port, например udp:127.0.0.1:2223
const isSocket = (value) => /^[a-z]+:\S+:\d+$/i.test(String(value || '')) || 'Формат: udp:host:port'

watch(
  () => props.modelValue,
  (opened) => {
    if (opened) form.value = props.row ? { ...EMPTY, ...props.row } : { ...EMPTY }
  },
)

function submit() {
  const payload = { ...form.value }
  delete payload.id
  delete payload.runtime
  delete payload.runtime_state
  emit('save', { id: props.row?.id ?? null, payload })
}
</script>

<template>
  <v-dialog
    :model-value="props.modelValue"
    max-width="560"
    persistent
    @update:model-value="emit('update:modelValue', $event)"
  >
    <v-card>
      <v-card-title>{{ props.row ? 'Редактирование сокета rtpengine' : 'Новый сокет rtpengine' }}</v-card-title>
      <v-card-text>
        <v-form v-model="valid" @submit.prevent="submit">
          <v-row dense>
            <v-col cols="12" sm="8">
              <v-text-field
                v-model="form.socket"
                label="socket"
                placeholder="udp:127.0.0.1:2223"
                :rules="[required, isSocket]"
              />
            </v-col>
            <v-col cols="12" sm="4">
              <v-text-field
                v-model.number="form.set_id"
                label="set_id"
                type="number"
                :rules="[required]"
                hint="Номер набора"
                persistent-hint
              />
            </v-col>
          </v-row>
        </v-form>

        <v-alert type="info" variant="tonal" density="compact" class="mt-4">
          Строка попадает в таблицу rtpengine. Чтобы opensips её увидел, нажмите «Обновить в памяти
          opensips» — команда работает, только если у модуля задан параметр db_url.
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
