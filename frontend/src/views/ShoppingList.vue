<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { mealsApiGetShoppingList, type ShoppingListSchema } from '../client'

const route = useRoute()
const campId = route.params.id as string
const listId = route.query.id as string
const list = ref<ShoppingListSchema | null>(null)

async function fetchList() {
  if (!listId) return
  const { data } = await mealsApiGetShoppingList({ path: { list_id: listId } })
  if (data) list.value = data
}

onMounted(fetchList)

// For display, group items by category
const groupedItems = computed(() => {
  if (!list.value?.items) return {}
  const groups: Record<string, any[]> = {}
  for (const item of list.value.items) {
    if (!groups[item.category]) groups[item.category] = []
    groups[item.category].push(item)
  }
  return groups
})
</script>

<template>
  <div v-if="list">
    <div class="flex justify-between items-center" style="margin-bottom: 2rem;">
      <div>
        <RouterLink :to="`/camps/${campId}`" class="badge" style="margin-bottom: 0.5rem">← Back to Planner</RouterLink>
        <h2>Shopping List</h2>
      </div>
      <button class="btn btn-secondary">⎙ Export PDF</button>
    </div>

    <!-- Grouped lists -->
    <div v-for="(items, category) in groupedItems" :key="category" style="margin-bottom: 2rem;">
      <h3 style="margin-bottom: 1rem; border-bottom: 1px solid var(--color-border); padding-bottom: 0.5rem">
        {{ category }}
      </h3>
      <div v-for="item in items" :key="item.id as string" class="flex items-center gap-4" style="padding: 0.5rem 0;">
        <input type="checkbox" v-model="item.is_checked" style="width: 1.25rem; height: 1.25rem; border-radius: var(--radius-sm);" />
        <span>{{ item.amount }} {{ item.unit }} - <strong>{{ item.custom_name || item.ingredient?.name }}</strong></span>
      </div>
    </div>
  </div>
</template>
