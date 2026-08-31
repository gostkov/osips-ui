<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  role: { type: Object, default: null },
  groups: { type: Array, default: () => [] },
  saving: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'save'])

const EMPTY = { slug: '', title: '', description: '', permissions: [] }
const form = ref({ ...EMPTY })
const valid = ref(false)

const rules = {
  slug: [
    (value) => Boolean(value) || 'Обязательное поле',
    (value) => /^[a-z][a-z0-9._-]{1,31}$/.test(String(value || '')) || 'Латиница в нижнем регистре, цифры и . _ -',
  ],
  title: [(value) => String(value || '').length >= 2 || 'Минимум 2 символа'],
}

const total = computed(() => props.groups.reduce((sum, group) => sum + group.permissions.length, 0))

watch(
  () => props.modelValue,
  (opened) => {
    if (!opened) return
    form.value = props.role
      ? {
          slug: props.role.slug,
          title: props.role.title,
          description: props.role.description || '',
          permissions: [...props.role.permissions],
        }
      : { ...EMPTY, permissions: [] }
  },
)

function groupState(group) {
  const granted = group.permissions.filter((perm) => form.value.permissions.includes(perm.value)).length
  return { granted, all: granted === group.permissions.length }
}

function toggleGroup(group) {
  const values = group.permissions.map((perm) => perm.value)
  form.value.permissions = groupState(group).all
    ? form.value.permissions.filter((value) => !values.includes(value))
    : [...new Set([...form.value.permissions, ...values])]
}

function submit() {
  emit('save', {
    id: props.role?.id ?? null,
    payload: {
      slug: form.value.slug,
      title: form.value.title,
      description: form.value.description || null,
      permissions: form.value.permissions,
    },
  })
}
</script>

<template>
  <v-dialog
    :model-value="props.modelValue"
    max-width="760"
    scrollable
    persistent
    @update:model-value="emit('update:modelValue', $event)"
  >
    <v-card>
      <v-card-title>{{ props.role ? `Роль «${props.role.title}»` : 'Новая роль' }}</v-card-title>
      <v-divider />
      <v-card-text>
        <v-form v-model="valid" @submit.prevent="submit">
          <v-row dense>
            <v-col cols="12" sm="4">
              <v-text-field
                v-model="form.slug"
                label="Код роли"
                :rules="rules.slug"
                hint="Хранится у пользователей и в токенах"
                persistent-hint
              />
            </v-col>
            <v-col cols="12" sm="8">
              <v-text-field v-model="form.title" label="Название" :rules="rules.title" />
            </v-col>
            <v-col cols="12">
              <v-text-field v-model="form.description" label="Описание" />
            </v-col>
          </v-row>

          <div class="d-flex align-center mt-4 mb-1">
            <span class="text-subtitle-2">Доступ к разделам</span>
            <v-spacer />
            <span class="text-caption text-medium-emphasis">
              выбрано {{ form.permissions.length }} из {{ total }}
            </span>
          </div>
          <v-divider class="mb-2" />

          <div v-for="group in props.groups" :key="group.section" class="mb-2">
            <div class="d-flex align-center ga-2">
              <span class="text-body-2 font-weight-medium">{{ group.section }}</span>
              <v-btn size="x-small" variant="text" @click="toggleGroup(group)">
                {{ groupState(group).all ? 'снять все' : 'выбрать все' }}
              </v-btn>
            </div>
            <v-row dense>
              <v-col v-for="perm in group.permissions" :key="perm.value" cols="12" sm="6">
                <v-checkbox
                  v-model="form.permissions"
                  :value="perm.value"
                  :label="perm.title"
                  density="compact"
                  hide-details
                />
                <div class="text-caption text-medium-emphasis ml-8 font-monospace">{{ perm.value }}</div>
              </v-col>
            </v-row>
          </div>
        </v-form>
      </v-card-text>
      <v-divider />
      <v-card-actions>
        <v-spacer />
        <v-btn variant="text" @click="emit('update:modelValue', false)">Отмена</v-btn>
        <v-btn color="primary" :disabled="!valid" :loading="props.saving" @click="submit">Сохранить</v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>
</template>

<style scoped>
.font-monospace {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}
</style>
