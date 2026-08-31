<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  user: { type: Object, default: null },
  roles: { type: Array, default: () => [] },
  saving: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'save'])

const EMPTY = { username: '', full_name: '', email: '', role: '', is_active: true, password: '' }
const form = ref({ ...EMPTY })
const valid = ref(false)

const roleHint = computed(() => {
  const role = props.roles.find((item) => item.slug === form.value.role)
  if (!role) return ' '
  return role.description || `Код роли: ${role.slug}`
})

const rules = {
  username: [
    (value) => Boolean(value) || 'Обязательное поле',
    (value) => /^[A-Za-z0-9._@-]+$/.test(String(value || '')) || 'Латиница, цифры и . _ - @',
  ],
  role: [(value) => Boolean(value) || 'Выберите роль'],
  password: [
    (value) => (props.user ? true : Boolean(value)) || 'Обязательное поле',
    (value) => !value || String(value).length >= 8 || 'Минимум 8 символов',
  ],
}

watch(
  () => props.modelValue,
  (opened) => {
    if (opened) {
      // роли динамические: у новой учётки подставляем первую из списка, а не жёстко 'reader'
      form.value = props.user
        ? { ...EMPTY, ...props.user, password: '' }
        : { ...EMPTY, role: props.roles[0]?.slug || '' }
    }
  },
)

function submit() {
  const payload = { ...form.value }
  delete payload.id
  delete payload.created_at
  delete payload.last_login_at
  delete payload.auth_provider
  if (props.user) {
    delete payload.username
    if (!payload.password) delete payload.password
  }
  emit('save', { id: props.user?.id ?? null, payload })
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
      <v-card-title>{{ props.user ? `Пользователь «${props.user.username}»` : 'Новый пользователь' }}</v-card-title>
      <v-card-text>
        <v-form v-model="valid" @submit.prevent="submit">
          <v-text-field
            v-model="form.username"
            label="Логин"
            :rules="rules.username"
            :disabled="Boolean(props.user)"
          />
          <v-text-field v-model="form.full_name" label="ФИО" />
          <v-text-field v-model="form.email" label="Email" />
          <v-select
            v-model="form.role"
            label="Роль"
            :items="props.roles"
            item-title="title"
            item-value="slug"
            :rules="rules.role"
            :hint="roleHint"
            persistent-hint
            class="mb-4"
          />
          <v-text-field
            v-model="form.password"
            label="Пароль"
            type="password"
            autocomplete="new-password"
            :rules="rules.password"
            :placeholder="props.user ? 'оставьте пустым, чтобы не менять' : ''"
          />
          <v-switch v-model="form.is_active" label="Активен" color="primary" hide-details />
        </v-form>
      </v-card-text>
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="emit('update:modelValue', false)">Отмена</v-btn>
        <v-btn color="primary" :disabled="!valid" :loading="props.saving" @click="submit">Сохранить</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>
