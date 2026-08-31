<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  row: { type: Object, default: null },
  saving: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'save'])

const EMPTY = {
  setid: 1,
  destination: '',
  socket: '',
  state: 0,
  probe_mode: 0,
  weight: '1',
  priority: 0,
  attrs: '',
  description: '',
}

const form = ref({ ...EMPTY })
const valid = ref(false)

const required = (value) => (value !== null && value !== undefined && String(value).length > 0) || 'Обязательное поле'
const isSipUri = (value) => /^sips?:\S+$/i.test(String(value || '')) || 'Формат: sip:host[:port]'

watch(
  () => props.modelValue,
  (opened) => {
    if (opened) {
      form.value = props.row ? { ...EMPTY, ...props.row } : { ...EMPTY }
    }
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
    max-width="640"
    persistent
    @update:model-value="emit('update:modelValue', $event)"
  >
    <v-card>
      <v-card-title>{{ props.row ? 'Редактирование ноды dispatcher' : 'Новая нода dispatcher' }}</v-card-title>
      <v-card-text>
        <v-form v-model="valid" @submit.prevent="submit">
          <v-row dense>
            <v-col cols="12" sm="4">
              <v-text-field v-model.number="form.setid" label="setid" type="number" :rules="[required]" />
            </v-col>
            <v-col cols="12" sm="8">
              <v-text-field
                v-model="form.destination"
                label="destination"
                placeholder="sip:10.0.0.1:5060"
                :rules="[required, isSipUri]"
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="form.socket" label="socket" placeholder="udp:10.0.0.1:5060" />
            </v-col>
            <v-col cols="12" sm="3">
              <v-text-field v-model="form.weight" label="weight" />
            </v-col>
            <v-col cols="12" sm="3">
              <v-text-field v-model.number="form.priority" label="priority" type="number" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-select
                v-model="form.state"
                label="state (в БД)"
                :items="[
                  { title: '0 — active', value: 0 },
                  { title: '1 — inactive', value: 1 },
                  { title: '2 — probing', value: 2 },
                ]"
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-select
                v-model="form.probe_mode"
                label="probe_mode"
                :items="[
                  { title: '0 — без проверки состояния', value: 0 },
                  { title: '1 — проверка состояния только неактивных', value: 1 },
                  { title: '2 — проверка состояния всегда', value: 2 },
                ]"
              />
            </v-col>
            <v-col cols="12">
              <v-text-field v-model="form.attrs" label="attrs" />
            </v-col>
            <v-col cols="12">
              <v-text-field v-model="form.description" label="description" />
            </v-col>
          </v-row>
        </v-form>

        <v-alert type="info" variant="tonal" density="compact" class="mt-4">
          Изменения попадают в таблицу БД. Чтобы применить их на работающем OpenSIPS, нажмите
          «Обновить в памяти opensips».
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
