<script setup lang="ts">
import MarkdownView from './MarkdownView.vue'

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
      <h3 class="title">Camp Notes</h3>
      <button class="btn btn-secondary edit-btn" @click="$emit('edit')">Edit</button>
    </div>
    <div class="text-mute notes-content">
      <MarkdownView v-if="notes" :content="notes" />
      <span v-else>No special notes or information for this camp yet. Click edit to add.</span>
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
