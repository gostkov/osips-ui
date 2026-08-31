<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  row: { type: Object, default: null },
  dpids: { type: Array, default: () => [] },
  saving: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'save'])

const EMPTY = {
  dpid: 1,
  pr: 0,
  match_op: 0,
  match_exp: '',
  match_flags: 0,
  subst_exp: '',
  repl_exp: '',
  timerec: '',
  disabled: 0,
  attrs: '',
}

const form = ref({ ...EMPTY })
const valid = ref(false)

const required = (value) => (value !== null && value !== undefined && String(value).length > 0) || 'Обязательное поле'

// match_flags: бит 1 — сравнение без учёта регистра (DP_CASE_INSENSITIVE)
const caseInsensitive = computed({
  get: () => (Number(form.value.match_flags) & 1) === 1,
  set: (value) => {
    form.value.match_flags = value ? Number(form.value.match_flags) | 1 : Number(form.value.match_flags) & ~1
  },
})

const dpidItems = computed(() => props.dpids.map((item) => item.dpid))

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
  for (const key of ['subst_exp', 'repl_exp', 'timerec', 'attrs']) {
    if (payload[key] === '') payload[key] = null
  }
  emit('save', { id: props.row?.id ?? null, payload })
}
</script>

<template>
  <v-dialog
    :model-value="props.modelValue"
    max-width="720"
    persistent
    scrollable
    @update:model-value="emit('update:modelValue', $event)"
  >
    <v-card>
      <v-card-title>{{ props.row ? 'Редактирование правила dialplan' : 'Новое правило dialplan' }}</v-card-title>
      <v-card-text>
        <v-form v-model="valid" @submit.prevent="submit">
          <v-row dense>
            <v-col cols="12" sm="4">
              <v-combobox
                v-model.number="form.dpid"
                label="dpid"
                :items="dpidItems"
                type="number"
                :rules="[required]"
                hint="Набор правил, который вызывается из скрипта"
                persistent-hint
              />
            </v-col>
            <v-col cols="12" sm="4">
              <v-text-field
                v-model.number="form.pr"
                label="pr (приоритет)"
                type="number"
                hint="Меньше — раньше проверяется"
                persistent-hint
              />
            </v-col>
            <v-col cols="12" sm="4">
              <v-select
                v-model="form.match_op"
                label="match_op"
                :items="[
                  { title: '0 — равенство строк', value: 0 },
                  { title: '1 — регулярное выражение', value: 1 },
                ]"
              />
            </v-col>

            <v-col cols="12" sm="8">
              <v-text-field
                v-model="form.match_exp"
                label="match_exp"
                :placeholder="form.match_op === 1 ? '^7(\\d{10})$' : '1234'"
                :rules="[required]"
                hint="С чем сравнивается входная строка"
                persistent-hint
              />
            </v-col>
            <v-col cols="12" sm="4" class="d-flex align-center">
              <v-checkbox v-model="caseInsensitive" label="Без учёта регистра" hide-details density="compact" />
            </v-col>

            <v-col cols="12" sm="6">
              <v-text-field
                v-model="form.subst_exp"
                label="subst_exp"
                placeholder="^7(\d{10})$"
                hint="Регулярное выражение для замены. Пусто — замены нет"
                persistent-hint
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="form.repl_exp"
                label="repl_exp"
                placeholder="8\1"
                hint="Результат. Пусто — строка остаётся прежней"
                persistent-hint
              />
            </v-col>

            <v-col cols="12" sm="6">
              <v-text-field
                v-model="form.timerec"
                label="timerec"
                placeholder="20240101T080000|20240101T180000|||||"
                hint="Окно действия правила, формат RFC 2445. Пусто — всегда"
                persistent-hint
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="form.attrs"
                label="attrs"
                hint="Произвольная строка, возвращается в скрипт вторым результатом"
                persistent-hint
              />
            </v-col>

            <v-col cols="12">
              <v-switch
                :model-value="form.disabled === 0"
                label="Правило включено"
                color="primary"
                hide-details
                @update:model-value="form.disabled = $event ? 0 : 1"
              />
            </v-col>
          </v-row>
        </v-form>

        <v-alert type="info" variant="tonal" density="compact" class="mt-2">
          Изменения попадают в таблицу БД. Чтобы применить их на работающем OpenSIPS, нажмите
          «Обновить в памяти opensips» (dp_reload).
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
