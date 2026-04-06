<script setup lang="ts">
import { useI18n } from '../composables/useI18n';
import MarkdownView from './MarkdownView.vue'
const { t } = useI18n()

defineProps<{
  notes?: string | null
}>()

defineEmits<{
  (e: 'edit'): void
}>()
</script>

<template>
  <div class="card camp-notes">
    <div class="flex justify-between items-center header">
      <h3 class="title">{{ t('notes.title') }}</h3>
      <button class="btn btn-secondary edit-btn" @click="$emit('edit')">⚙️ {{ t('edit') }}</button>
    </div>
    <div class="text-mute notes-content">
      <MarkdownView v-if="notes" :content="notes" />
      <span v-else>{{ t('notes.empty') }}</span>
    </div>
  </div>
</template>

<style scoped>
.camp-notes {
  border: 1px solid var(--color-border);
  background: var(--color-bg-base);
}

.header {
  margin-bottom: 1rem;
}

.title {
  margin: 0;
}

.edit-btn {
  font-size: 0.8rem;
  padding: 0.25rem 0.5rem;
}

.notes-content {
  font-size: 0.9rem;
  margin: 0;
  line-height: 1.5;
}
</style>
