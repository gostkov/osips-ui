<script setup>
import { ref } from 'vue'
import { authApi } from '@/api'
import { useAuthStore } from '@/stores/auth'
import { useUiStore } from '@/stores/ui'

const auth = useAuthStore()
const ui = useUiStore()

const form = ref({ current_password: '', new_password: '', repeat_password: '' })
const valid = ref(false)
const saving = ref(false)

const rules = {
  required: [(value) => Boolean(value) || 'Обязательное поле'],
  password: [
    (value) => Boolean(value) || 'Обязательное поле',
    (value) => String(value || '').length >= 8 || 'Минимум 8 символов',
  ],
  repeat: [(value) => value === form.value.new_password || 'Пароли не совпадают'],
}

async function submit() {
  saving.value = true
  try {
    await authApi.changePassword({
      current_password: form.value.current_password,
      new_password: form.value.new_password,
    })
    ui.success('Пароль изменён')
    form.value = { current_password: '', new_password: '', repeat_password: '' }
  } catch (error) {
    ui.error(error.uiMessage)
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <v-row>
    <v-col cols="12" md="5">
      <v-card>
        <v-card-item>
          <v-card-title>Профиль</v-card-title>
        </v-card-item>
        <v-divider />
        <v-list density="comfortable">
          <v-list-item title="Логин" :subtitle="auth.user?.username" />
          <v-list-item title="Имя" :subtitle="auth.user?.full_name || '—'" />
          <v-list-item title="Роль" :subtitle="auth.user?.role" />
          <v-list-item title="Способ входа" :subtitle="auth.user?.auth_provider" />
        </v-list>
        <v-divider />
        <v-card-text>
          <div class="text-caption text-medium-emphasis mb-2">Доступные права:</div>
          <v-chip v-for="permission in auth.permissions" :key="permission" size="small" class="mr-1 mb-1" label>
            {{ permission }}
          </v-chip>
        </v-card-text>
      </v-card>
    </v-col>

    <v-col cols="12" md="7">
      <v-card>
        <v-card-item>
          <v-card-title>Смена пароля</v-card-title>
        </v-card-item>
        <v-divider />
        <v-card-text>
          <v-form v-model="valid" @submit.prevent="submit">
            <v-text-field
              v-model="form.current_password"
              label="Текущий пароль"
              type="password"
              autocomplete="current-password"
              :rules="rules.required"
            />
            <v-text-field
              v-model="form.new_password"
              label="Новый пароль"
              type="password"
              autocomplete="new-password"
              :rules="rules.password"
            />
            <v-text-field
              v-model="form.repeat_password"
              label="Повторите новый пароль"
              type="password"
              autocomplete="new-password"
              :rules="rules.repeat"
            />
            <v-btn type="submit" color="primary" :disabled="!valid" :loading="saving">Сохранить</v-btn>
          </v-form>
        </v-card-text>
      </v-card>
    </v-col>
  </v-row>
</template>
