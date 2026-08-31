<script setup>
import { computed, ref } from 'vue'
import { useServersStore } from '@/stores/servers'
import { useAuthStore } from '@/stores/auth'
import DispatcherPanel from '@/components/DispatcherPanel.vue'
import LoadBalancerPanel from '@/components/LoadBalancerPanel.vue'

const servers = useServersStore()
const auth = useAuthStore()
const tab = ref('dispatcher')

const serverId = computed(() => servers.selectedId)
</script>

<template>
  <v-card>
    <v-tabs v-model="tab" bg-color="surface" color="primary">
      <v-tab value="dispatcher" prepend-icon="mdi-call-split">Dispatcher</v-tab>
      <v-tab v-if="auth.can('lb:read')" value="loadbalancer" prepend-icon="mdi-scale-balance">Load balancer</v-tab>
    </v-tabs>
    <v-divider />

    <v-card-text>
      <v-window v-model="tab">
        <v-window-item value="dispatcher">
          <DispatcherPanel v-if="serverId" :server-id="serverId" />
        </v-window-item>
        <v-window-item value="loadbalancer">
          <LoadBalancerPanel v-if="serverId && auth.can('lb:read')" :server-id="serverId" />
        </v-window-item>
      </v-window>
    </v-card-text>
  </v-card>
</template>
