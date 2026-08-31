<script setup>
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const username = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const error = ref('')

async function submit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value.trim(), password.value)
    router.push(route.query.redirect || '/')
  } catch (exception) {
    error.value = exception.uiMessage || 'Не удалось войти'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <v-main class="login-bg">
    <v-container class="fill-height">
      <v-row justify="center" align="center">
        <v-col cols="12" sm="8" md="5" lg="4">
          <v-card class="pa-2">
            <v-card-item>
              <div class="d-flex align-center ga-3 mb-2">
                <v-icon icon="mdi-phone-in-talk" color="primary" size="34" />
                <div>
                  <v-card-title class="pa-0 text-h6">OpenSIPS UI</v-card-title>
                  <v-card-subtitle class="pa-0">Управление серверами OpenSIPS</v-card-subtitle>
                </div>
              </div>
            </v-card-item>

            <v-card-text>
              <v-form @submit.prevent="submit">
                <v-text-field
                  v-model="username"
                  label="Логин"
                  prepend-inner-icon="mdi-account"
                  autocomplete="username"
                  autofocus
                  required
                />
                <v-text-field
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  label="Пароль"
                  prepend-inner-icon="mdi-lock"
                  :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                  autocomplete="current-password"
                  required
                  @click:append-inner="showPassword = !showPassword"
                />

                <v-alert v-if="error" type="error" variant="tonal" density="compact" class="mb-4">
                  {{ error }}
                </v-alert>

                <v-btn type="submit" color="primary" block size="large" :loading="loading"> Войти </v-btn>
              </v-form>
            </v-card-text>

            <v-card-text class="text-caption text-medium-emphasis pt-0">
              Вход через SSO будет добавлен позже.
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </v-main>
</template>

<style scoped>
.login-bg {
  background: linear-gradient(135deg, #eef2f7 0%, #dde6f2 100%);
}
</style>
