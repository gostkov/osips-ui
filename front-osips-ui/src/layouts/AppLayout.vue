<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useServersStore } from '@/stores/servers'
import { useUiStore } from '@/stores/ui'

const auth = useAuthStore()
const servers = useServersStore()
const ui = useUiStore()
const route = useRoute()
const router = useRouter()

const drawer = ref(true)

const navItems = computed(() =>
  router
    .getRoutes()
    .filter((item) => item.meta?.nav && auth.can(item.meta.permission))
    .map((item) => ({ to: item.path, title: item.meta.title, icon: item.meta.icon })),
)

// на этих страницах работа идёт в контексте выбранного сервера
const serverAware = computed(() =>
  ['dispatcher', 'dialplan', 'rtpengine', 'blacklist', 'address', 'sip-regs'].includes(route.name),
)

const currentTitle = computed(() => route.meta?.title || 'OpenSIPS UI')

onMounted(async () => {
  try {
    await servers.fetch()
  } catch (error) {
    ui.error(error.uiMessage || 'Не удалось загрузить список серверов')
  }
})

function logout() {
  auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <v-navigation-drawer v-model="drawer" width="270">
    <div class="pa-4 d-flex align-center ga-2">
      <v-icon icon="mdi-phone-in-talk" color="primary" size="28" />
      <div>
        <div class="text-subtitle-1 font-weight-bold">OpenSIPS UI</div>
        <div class="text-caption text-medium-emphasis">управление кластером</div>
      </div>
    </div>
    <v-divider />

    <v-list nav density="comfortable">
      <v-list-item
        v-for="item in navItems"
        :key="item.to"
        :to="item.to"
        :prepend-icon="item.icon"
        :title="item.title"
      />
    </v-list>

    <template #append>
      <v-divider />
      <v-list density="compact" nav>
        <v-list-item to="/profile" prepend-icon="mdi-account-circle" :title="auth.user?.username" :subtitle="auth.role" />
        <v-list-item prepend-icon="mdi-logout" title="Выйти" @click="logout" />
      </v-list>
    </template>
  </v-navigation-drawer>

  <v-app-bar flat border="b">
    <v-app-bar-nav-icon @click="drawer = !drawer" />
    <v-app-bar-title>{{ currentTitle }}</v-app-bar-title>

    <v-spacer />

    <div v-if="serverAware" class="d-flex align-center ga-2 mr-4" style="min-width: 260px">
      <v-icon icon="mdi-server" size="20" class="text-medium-emphasis" />
      <v-select
        :model-value="servers.selectedId"
        :items="servers.activeItems"
        item-title="name"
        item-value="id"
        label="Сервер OpenSIPS"
        density="compact"
        hide-details
        :loading="servers.loading"
        @update:model-value="servers.select($event)"
      />
    </div>
  </v-app-bar>

  <v-main>
    <v-container fluid class="pa-4 pa-md-6">
      <v-alert
        v-if="serverAware && servers.loaded && !servers.activeItems.length"
        type="info"
        variant="tonal"
        class="mb-4"
      >
        Нет ни одного активного сервера OpenSIPS.
        <template v-if="auth.can('servers:write')">
          Добавьте его в разделе <router-link to="/servers">«Серверы OpenSIPS»</router-link>.
        </template>
        <template v-else> Обратитесь к администратору системы.</template>
      </v-alert>

      <router-view v-else />
    </v-container>
  </v-main>
</template>
