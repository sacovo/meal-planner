<script setup lang="ts">
import type { ShoppingListOverviewSchema } from '../client'
import { useI18n } from '../composables/useI18n'

const { t } = useI18n()

const props = defineProps<{
  selectedMealsCount: number
  showShoppingLists: boolean
  shoppingLists: ShoppingListOverviewSchema[]
  loading: boolean
}>()

defineEmits<{
  (e: 'update:showShoppingLists', val: boolean): void
  (e: 'generate'): void
  (e: 'delete', id: string): void
  (e: 'open', token: string): void
}>()

function groupMealsByDay(messages: string[]) {
  const groups: Record<string, string[]> = {}
  for (const msg of messages) {
    const match = msg.match(/^(.*?)\s+\((.*?)\):\s+(.*)$/)
    if (match) {
      const day = match[1]
      const type = match[2]
      const recipe = match[3]
      if (!groups[day]) groups[day] = []
      groups[day].push(`${type}: ${recipe}`)
    } else {
      if (!groups['Other']) groups['Other'] = []
      groups['Other'].push(msg)
    }
  }
  return groups
}
</script>

<template>
  <div class="shopping-manager">
    <!-- Shopping Generate Action -->
    <div class="card flex justify-between items-center action-bar">
      <p class="summary-text"><strong>{{ t('shopping.title') }}:</strong> {{ selectedMealsCount }} {{ t('misc.meals') }}
      </p>
      <div class="flex gap-2 buttons">
        <button class="btn btn-secondary" @click="$emit('update:showShoppingLists', !showShoppingLists)">
          🛍️ {{ showShoppingLists ? t('btn.close') : t('planner.shopping_lists') }}
        </button>
        <button class="btn btn-primary" @click="$emit('generate')">📋 {{ t('shopping.generate') }}</button>
      </div>
    </div>

    <!-- Inline Shopping Lists Manager -->
    <div v-show="showShoppingLists" class="card lists-container">
      <div class="flex justify-between items-center header">
        <h3 class="title">{{ t('shopping.title') }}</h3>
      </div>

      <div v-if="loading" class="text-center py-4 text-mute">{{ t('btn.loading') }}</div>

      <div v-else-if="shoppingLists.length === 0" class="text-center py-4 text-mute empty-msg">
        {{ t('shopping.no_items') }}
      </div>

      <div v-else class="flex-col gap-4 lists">
        <div v-for="sl in shoppingLists" :key="sl.id as string" class="card border flex-col gap-2 shadow-sm list-card">
          <div class="flex justify-between items-start list-header">
            <strong class="list-date">{{ t('shopping.list_from') }} {{ new Date(sl.created_at).toLocaleString([], {
              dateStyle: 'short',
              timeStyle: 'short'
            }) }}</strong>
            <div class="flex gap-2 list-actions">
              <button class="btn btn-secondary action-btn" @click="$emit('open', sl.shared_token as string)">{{
                t('btn.edit') }}</button>
              <button class="btn delete-btn" @click="$emit('delete', sl.id as string)">{{ t('btn.delete') }}</button>
            </div>
          </div>

          <div class="meals-summary">
            <strong class="meals-title">{{ t('shopping.included_meals') }} ({{ sl.included_meals.length }})</strong>

            <div class="meal-groups-grid" v-if="sl.included_meals.length > 0">
              <div v-for="(meals, day) in groupMealsByDay(sl.included_meals)" :key="day" class="day-group">
                <div class="day-name">{{ day }}</div>
                <div v-for="(m, i) in meals" :key="i" class="meal-item">
                  <span>{{ m.split(':')[1] }}</span>
                </div>
              </div>
            </div>

            <div v-else class="text-mute empty-meals">
              {{ t('shopping.no_meals') }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.shopping-manager {
  margin-top: 1rem;
}

.action-bar {
  margin-top: 0;
}

.summary-text {
  margin: 0;
}

.lists-container {
  margin-top: 1rem;
  border: 1px solid var(--color-border);
  background: var(--color-bg-base);
}

.header {
  margin-bottom: 1rem;
}

.title {
  margin: 0;
}

.empty-msg {
  margin-top: 1rem;
}

.list-card {
  padding: 1rem;
  border: 1px solid var(--color-border);
  background: var(--color-bg-surface);
}

.list-date {
  color: var(--color-primary);
  font-size: 1.1rem;
}

.action-btn {
  font-size: 0.8rem;
  padding: 0.25rem 0.6rem;
}

.delete-btn {
  font-size: 0.8rem;
  padding: 0.25rem 0.6rem;
  color: var(--color-danger);
  border: 1px solid var(--color-danger);
}

.meals-summary {
  margin-top: 1rem;
}

.meals-title {
  font-size: 0.9rem;
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 0.25rem;
  display: block;
  margin-bottom: 0.5rem;
}

.meal-groups-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 1rem;
}

.day-group {
  margin-bottom: 0.5rem;
}

.day-name {
  font-size: 0.8rem;
  font-weight: bold;
  color: var(--color-primary);
  margin-bottom: 0.2rem;
}

.meal-item {
  font-size: 0.8rem;
  color: var(--color-text-mute);
  line-height: 1.3;
  margin-bottom: 0.2rem;
  display: flex;
  gap: 0.25rem;
}

.empty-meals {
  font-size: 0.85rem;
}
</style>
