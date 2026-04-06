<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { mealsApiShoppingGetShoppingList, mealsApiShoppingExportShoppingList, type ShoppingListSchema } from '../client'
import { useFileDownload } from '../composables/useFileDownload'

const route = useRoute()
const { downloadBlob } = useFileDownload()
const campId = route.params.id as string
const listId = route.query.id as string
const list = ref<ShoppingListSchema | null>(null)

async function fetchList() {
  if (!listId) return
  const { data } = await mealsApiShoppingGetShoppingList({ path: { list_id: listId } })
  if (data) list.value = data
}

async function exportExcel() {
  if (!listId) return
  const res = await mealsApiShoppingExportShoppingList({
    path: { list_id: listId },
    parseAs: 'blob'
  })
  if (res.data) {
    downloadBlob(res.data as unknown as Blob, 'shopping_list.xlsx')
  }
}

onMounted(fetchList)

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
    <div class="page-header mb-8">
      <div>
        <RouterLink :to="`/camps/${campId}`" class="badge mb-2">← Back to Planner</RouterLink>
        <h2 class="page-title">Shopping List</h2>
      </div>
      <div class="flex gap-2">
        <button class="btn btn-secondary" @click="exportExcel">📥 Export Excel</button>
        <button class="btn btn-secondary">⎙ Export PDF</button>
      </div>
    </div>

    <!-- Grouped lists -->
    <div v-for="(items, category) in groupedItems" :key="category" class="mb-8">
      <h3 class="category-divider">
        {{ category }}
      </h3>
      <div v-for="item in items" :key="item.id as string" class="flex items-center gap-4 shopping-item-row">
        <input type="checkbox" v-model="item.is_checked" class="shopping-checkbox" />
        <span>{{ item.amount }} {{ item.unit }} - <strong>{{ item.custom_name || item.ingredient?.name }}</strong></span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.category-divider {
  margin-bottom: 1rem;
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 0.5rem;
}

.shopping-item-row {
  padding: 0.5rem 0;
}

.shopping-checkbox {
  width: 1.25rem;
  height: 1.25rem;
  border-radius: var(--radius-sm);
}
</style>
