<script setup>
import { computed } from 'vue'

/**
 * Состояние ноды по данным MI:
 *   active   - в работе (зелёный)
 *   inactive - выключена (серый)
 *   probing  - в состоянии probing (красный)
 *   unknown  - MI недоступен либо ноды нет в выхлопе ds_list/lb_list
 */
const props = defineProps({
  state: { type: String, default: 'unknown' },
  disabled: { type: Boolean, default: false },
  loading: { type: Boolean, default: false },
})
const emit = defineEmits(['change'])

const META = {
  active: { color: 'success', label: 'В работе' },
  inactive: { color: 'grey', label: 'Выведена из обслуживания' },
  probing: { color: 'error', label: 'Probing — нода не отвечает' },
  unknown: { color: 'grey-lighten-1', label: 'Состояние неизвестно (нет данных от MI)' },
}

const meta = computed(() => META[props.state] || META.unknown)
const isOn = computed(() => props.state === 'active')

function toggle(value) {
  emit('change', value ? 'active' : 'inactive')
}
</script>

<template>
  <div class="d-flex align-center ga-2">
    <v-switch
      :model-value="isOn"
      :color="meta.color"
      :disabled="props.disabled || props.loading || props.state === 'unknown'"
      :loading="props.loading"
      hide-details
      density="compact"
      inset
      @update:model-value="toggle"
    />
    <v-tooltip :text="meta.label" location="top">
      <template #activator="{ props: tooltipProps }">
        <v-chip v-bind="tooltipProps" size="small" :color="meta.color" variant="tonal" label>
          {{ props.state === 'unknown' ? 'н/д' : props.state }}
        </v-chip>
      </template>
    </v-tooltip>
  </div>
</template>
