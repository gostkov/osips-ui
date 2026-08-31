<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // 'user' - таблица userblacklist, 'global' - globalblacklist
  kind: { type: String, default: 'user' },
  row: { type: Object, default: null },
  saving: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'save'])

const EMPTY = {
  user: { username: '', domain: '', prefix: '', whitelist: 0 },
  global: { prefix: '', whitelist: 0, description: '' },
}

const form = ref({ ...EMPTY.user })
const valid = ref(false)

const isUser = computed(() => props.kind === 'user')
const title = computed(() => {
  const table = isUser.value ? 'userblacklist' : 'globalblacklist'
  return props.row ? `Редактирование правила ${table}` : `Новое правило ${table}`
})

const required = (value) => (value !== null && value !== undefined && String(value).length > 0) || 'Обязательное поле'
const digitsOnly = (value) => /^\d*$/.test(String(value || '')) || 'Только цифры'

watch(
  () => props.modelValue,
  (opened) => {
    if (opened) {
      const empty = { ...EMPTY[props.kind] }
      form.value = props.row ? { ...empty, ...props.row } : empty
    }
  },
)

function submit() {
  const payload = { ...form.value }
  delete payload.id
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
      <v-card-title>{{ title }}</v-card-title>
      <v-card-text>
        <v-form v-model="valid" @submit.prevent="submit">
          <v-row dense>
            <template v-if="isUser">
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="form.username"
                  label="username"
                  hint="Абонент, к которому относится правило"
                  persistent-hint
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field v-model="form.domain" label="domain" hint="Пусто, если use_domain=0" persistent-hint />
              </v-col>
            </template>

            <v-col cols="12" :sm="isUser ? 12 : 6">
              <v-text-field
                v-model="form.prefix"
                label="prefix"
                placeholder="7900"
                :rules="[required, digitsOnly]"
                hint="Префикс вызываемого номера; сравнение идёт по самому длинному совпадению"
                persistent-hint
              />
            </v-col>

            <v-col v-if="!isUser" cols="12" sm="6">
              <v-text-field v-model="form.description" label="description" />
            </v-col>

            <v-col cols="12">
              <v-select
                v-model="form.whitelist"
                label="Тип правила"
                :items="[
                  { title: 'Запрет (whitelist = 0)', value: 0 },
                  { title: 'Разрешение (whitelist = 1)', value: 1 },
                ]"
                hint="Разрешающее правило снимает запрет для более короткого префикса"
                persistent-hint
              />
            </v-col>
          </v-row>
        </v-form>

        <v-alert :type="isUser ? 'success' : 'info'" variant="tonal" density="compact" class="mt-4">
          <template v-if="isUser">
            Правила userblacklist читаются из БД на каждый вызов — изменения действуют сразу.
          </template>
          <template v-else>
            globalblacklist загружается в память при старте: после правки нажмите «Обновить в памяти
            opensips» (reload_blacklist).
          </template>
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
