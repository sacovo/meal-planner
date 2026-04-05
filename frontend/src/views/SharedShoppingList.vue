<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { 
  mealsApiGetSharedShoppingList, 
  mealsApiToggleSharedShoppingItem,
  mealsApiGetCurrentUserStatus,
  type ShoppingListSchema,
  type ShoppingListItemSchema
} from '../client'

const route = useRoute()
const sharedToken = route.params.token as string

const shoppingList = ref<ShoppingListSchema | null>(null)
let pollInterval: any = null
const isLoggedIn = ref(false)

async function checkAuth() {
  const { data } = await mealsApiGetCurrentUserStatus()
  if (data?.is_logged_in) {
    isLoggedIn.value = true
  }
}
const collapsedCategories = ref<Record<string, boolean>>({})
const collapsedCompleted = ref(true)

function toggleCategory(cat: string) {
  collapsedCategories.value[cat] = !collapsedCategories.value[cat]
}

async function fetchList() {
  const { data } = await mealsApiGetSharedShoppingList({
    path: { token: sharedToken }
  })
  if (data) {
    shoppingList.value = data
  }
}

// Perform optimistic update
async function toggleItem(item: ShoppingListItemSchema) {
  // Optimistically toggle locally directly so user gets instant feedback
  item.is_checked = !item.is_checked
  
  // Await the backend reality
  const { data } = await mealsApiToggleSharedShoppingItem({
    path: { token: sharedToken, item_id: item.id as string }
  })
  
  // If it failed for some reason, the next poll will repair it automatically.
  if (data) {
    // Optionally sync up in case backend returned forced data
    item.is_checked = data.is_checked
  }
}

// Aggregation by category
const itemsByCategory = computed(() => {
  if (!shoppingList.value?.items) return {}
  const grouped: Record<string, ShoppingListItemSchema[]> = {}
  shoppingList.value.items.forEach((item: any) => {
    if (!grouped[item.category]) grouped[item.category] = []
    grouped[item.category].push(item)
  })
  return grouped
})

const doneItems = computed(() => {
  if (!shoppingList.value) return []
  return shoppingList.value.items.filter((i:any) => i.is_checked)
})

const categoryCounts = computed(() => {
  const counts: Record<string, { done: number, total: number }> = {}
  if (!shoppingList.value) return counts
  shoppingList.value.items.forEach(item => {
    const cat = item.category
    if (!counts[cat]) counts[cat] = { done: 0, total: 0 }
    counts[cat].total++
    if (item.is_checked) counts[cat].done++
  })
  return counts
})

function copyLink() {
  const url = window.location.href
  navigator.clipboard.writeText(url)
  alert("Link copied to clipboard! Anyone with this link can check off items.")
}

onMounted(() => {
  fetchList()
  checkAuth()
  // Start polling every 5 seconds
  pollInterval = setInterval(fetchList, 5000)
})

onUnmounted(() => {
  if (pollInterval) clearInterval(pollInterval)
})
</script>

<template>
  <div v-if="shoppingList" class="flex-col gap-4">
    <div class="flex items-center justify-between" style="background: var(--color-surface); padding: 1rem; border-radius: var(--radius-md); box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 1rem; position: sticky; top: 0; z-index: 10;">
      <div>
        <RouterLink v-if="isLoggedIn && shoppingList" :to="`/camps/${shoppingList.camp_id}`" class="badge" style="margin-bottom: 0.5rem; text-decoration: none; display: inline-block;">← Back to Planner</RouterLink>
        <h2 style="margin: 0; font-size: 1.5rem;">Live Shopping List</h2>
        <p class="text-mute" style="margin: 0; font-size: 0.9rem;">Changes are synchronized in real-time.</p>
      </div>
      <button class="btn btn-secondary" @click="copyLink">🔗 Share Link</button>
    </div>

    <div v-if="!shoppingList.value?.items?.length" class="card text-center text-mute" style="padding: 3rem;">
      <h3 style="color: var(--color-primary);">List is empty</h3>
      <p>Add some items to get started.</p>
    </div>

    <!-- Grouped Categories -->
    <div v-for="(items, category) in itemsByCategory" :key="category" class="card" :style="categoryCounts[category as string].done === categoryCounts[category as string].total ? 'opacity: 0.7; border-style: dashed;' : ''">
      <div 
        class="flex justify-between items-center cursor-pointer" 
        style="margin-top: 0; border-bottom: 2px solid var(--color-border); padding-bottom: 0.5rem; text-transform: uppercase; font-size: 0.9rem; letter-spacing: 1px;"
        @click="toggleCategory(category as string)"
      >
        <div class="flex items-center gap-2">
          <h3 style="margin: 0; font-size: inherit;" :class="{ 'text-success': categoryCounts[category as string].done === categoryCounts[category as string].total }">
            {{ categoryCounts[category as string].done === categoryCounts[category as string].total ? '✓ ' : '' }}{{ category }}
          </h3>
          <span style="font-size: 0.75rem; color: var(--color-text-mute); text-transform: none; font-weight: normal;">
            ({{ categoryCounts[category as string].done }} / {{ categoryCounts[category as string].total }} done)
          </span>
        </div>
        <span class="text-mute" style="font-size: 1.2rem; line-height: 1;">
          {{ collapsedCategories[category as string] ? '+' : '−' }}
        </span>
      </div>
      
      <ul v-show="!collapsedCategories[category as string]" style="list-style: none; padding: 0; padding-top: 1rem; margin: 0;" class="flex-col gap-2">
        <li 
          v-for="item in items" 
          :key="(item.id as string)" 
          class="shopping-item"
          :class="{ 'checked-item text-mute': item.is_checked }"
          @click="toggleItem(item)"
        >
          <div class="checkbox" :class="{ 'checked': item.is_checked }">
            {{ item.is_checked ? '✓' : '' }}
          </div>
          
          <div class="item-content" :style="item.is_checked ? 'text-decoration: line-through' : ''">
            <div class="item-name">
              <strong v-if="item.ingredient">{{ (item as any).ingredient.name }}</strong>
              <strong v-else>{{ item.custom_name }}</strong>
            </div>

            <div class="item-sources" v-if="item.source_meals_text && item.source_meals_text.length" @click.stop>
              <!-- Mobile Collapsible -->
              <details class="source-details hidden-desktop">
                <summary class="text-mute">{{ item.source_meals_text.length }} Menus (Show)</summary>
                <ul>
                  <li v-for="(src, idx) in item.source_meals_text" :key="idx">{{ src }}</li>
                </ul>
              </details>
              
              <!-- Desktop flat list -->
              <div class="source-desktop hidden-mobile text-mute">
                <ul :style="item.is_checked ? 'text-decoration: none' : ''">
                  <li v-for="(src, idx) in item.source_meals_text" :key="idx">{{ src }}</li>
                </ul>
              </div>
            </div>
          </div>
          
          <div class="item-measurement text-right text-mute border-left" :style="item.is_checked ? 'text-decoration: line-through' : ''">
            <strong>{{ parseFloat((item.amount).toFixed(2)) }} {{ item.unit }}</strong>
          </div>
        </li>
      </ul>
    </div>



  </div>
  <div v-else class="text-center text-mute" style="padding: 4rem;">
    Connecting to Live Shopping List...
  </div>
</template>

<style scoped>
.shopping-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.75rem 1rem;
  background: var(--color-bg-mute);
  border-radius: var(--radius-sm);
  cursor: pointer;
  user-select: none;
}

.shopping-item.checked-item {
  background: var(--color-surface);
  border: 1px dashed var(--color-border);
}

.checkbox {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  border: 2px solid var(--color-border);
  margin-right: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease;
  color: transparent;
}

.checkbox.checked {
  background: var(--color-success);
  border-color: var(--color-success);
  color: white;
}

.item-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.item-measurement {
  flex-shrink: 0;
  min-width: 60px;
  margin-left: 1rem;
}

.hidden-desktop {
  display: block;
}
.hidden-mobile {
  display: none;
}

.source-details {
  margin-top: 4px;
  font-size: 0.8rem;
}
.source-details summary {
  cursor: pointer;
  font-size: 0.75rem;
}
.source-details ul {
  padding-left: 1rem;
  margin: 4px 0 0 0;
}

@media (min-width: 768px) {
  .item-content {
    display: grid;
    grid-template-columns: 200px 1fr;
    align-items: center;
    gap: 1rem;
  }
  .item-name {
    flex: none;
    width: 200px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .item-sources {
    flex: none;
    padding: 0;
  }
  .hidden-desktop {
    display: none;
  }
  .hidden-mobile {
    display: block;
  }
  .source-desktop ul {
    padding: 0;
    margin: 0;
    list-style: disc;
    padding-left: 1rem;
    font-size: 0.75rem;
  }
}
</style>
