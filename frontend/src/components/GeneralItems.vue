<script setup lang="ts">
import { ref } from 'vue'
import type { GeneralCampItemSchema } from '../client'

defineProps<{
  items: GeneralCampItemSchema[]
}>()

const emit = defineEmits<{
  (e: 'add', item: { name: string, amount: string }): void
  (e: 'delete', id: string): void
}>()

const newItemName = ref('')
const newItemAmount = ref('')

function handleAdd() {
  if (!newItemName.value || !newItemAmount.value) return
  emit('add', { name: newItemName.value, amount: newItemAmount.value })
  newItemName.value = ''
  newItemAmount.value = ''
}
</script>

<template>
  <div class="card general-items">
    <div class="header">
      <h3 class="title">General Shopping Items</h3>
      <p class="text-mute subtitle">Non-food items or special products.</p>
    </div>
    
    <div class="flex gap-2 input-group">
      <input type="text" v-model="newItemName" placeholder="e.g. Abfallkübel" class="input slim-input" />
      <input type="text" v-model="newItemAmount" placeholder="e.g. 5x" class="input amount-input" />
      <button class="btn btn-primary add-btn" @click="handleAdd">Add</button>
    </div>
    
    <ul class="items-list">
      <li v-for="item in items" :key="item.id as string" class="item-row">
        <span>{{ item.amount }} {{ item.name }}</span>
        <button class="text-mute delete-btn" @click="$emit('delete', item.id as string)" title="Delete item">✕</button>
      </li>
      <li v-if="items.length === 0" class="text-mute empty-msg">No items added yet.</li>
    </ul>
  </div>
</template>

<style scoped>
.general-items {
  border: 1px solid var(--color-border);
  background: var(--color-bg-base);
}

.header {
  margin-bottom: 1rem;
}

.title {
  margin: 0;
}

.subtitle {
  font-size: 0.8rem;
  margin: 0.2rem 0 0 0;
}

.input-group {
  margin-top: 0.5rem;
}

.slim-input {
  padding: 0.4rem;
  font-size: 0.85rem;
}

.amount-input {
  width: 80px;
  padding: 0.4rem;
  font-size: 0.85rem;
}

.add-btn {
  padding: 0.4rem 0.8rem;
}

.items-list {
  margin-top: 1rem;
  padding-left: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  max-height: 120px;
  overflow-y: auto;
}

.item-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.4rem 0.5rem;
  border: 1px solid var(--color-border);
  border-radius: 4px;
  background: var(--color-bg-surface);
  font-size: 0.85rem;
}

.delete-btn {
  cursor: pointer;
  background: none;
  border: none;
  font-size: 0.8rem;
}

.empty-msg {
  font-size: 0.85rem;
  text-align: center;
}
</style>
