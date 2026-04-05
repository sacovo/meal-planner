<script setup lang="ts">
import MealCard from './MealCard.vue'
import type { CampSchema, CampMealSchema } from '../client'

const props = defineProps<{
  camp: CampSchema
  campDays: string[]
  mealTypesConfig: { val: string, label: string }[]
  mealsGrid: Record<string, Record<string, CampMealSchema[]>>
  selectedMeals: string[]
  recipeNames: Record<string, string>
}>()

const emit = defineEmits<{
  (e: 'update:selectedMeals', val: string[]): void
  (e: 'drop', event: DragEvent, day: string, mt: string): void
  (e: 'edit-meal', meal: CampMealSchema): void
  (e: 'toggle-done', meal: CampMealSchema): void
  (e: 'remove-meal', meal: CampMealSchema): void
  (e: 'switch-day', day: string): void
  (e: 'toggle-day', day: string): void
}>()

function isDaySelected(day: string) {
  const dayMeals = getMealsForDay(day)
  if (dayMeals.length === 0) return false
  return dayMeals.every(m => props.selectedMeals.includes(m.id))
}

function isDayPartial(day: string) {
  const dayMeals = getMealsForDay(day)
  if (dayMeals.length === 0) return false
  const selectedCount = dayMeals.filter(m => props.selectedMeals.includes(m.id)).length
  return selectedCount > 0 && selectedCount < dayMeals.length
}

function getMealsForDay(day: string) {
  if (!props.mealsGrid[day]) return []
  return Object.values(props.mealsGrid[day]).flat()
}

function handleMealSelection(mealId: string, isSelected: boolean) {
  let updated = [...props.selectedMeals]
  if (isSelected) {
    if (!updated.includes(mealId)) updated.push(mealId)
  } else {
    updated = updated.filter(id => id !== mealId)
  }
  emit('update:selectedMeals', updated)
}
</script>

<template>
  <div id="planner-matrix-canvas" class="card matrix-container">
    <h3 class="only-print title-print">{{ camp.name }} - Matrix Plan</h3>
    <table class="planner-table">
      <thead>
        <tr>
          <th class="sticky-col">Time</th>
          <th v-for="day in campDays" :key="day" class="day-col">
            <div class="flex-col items-center gap-1 group day-header-container" @click="$emit('switch-day', day)">
              <div class="day-header">
                {{ new Date(day).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' }) }}
              </div>
              <label v-if="getMealsForDay(day).length > 0" class="flex items-center gap-1 select-day-label" @click.stop>
                <input 
                  type="checkbox" 
                  :checked="isDaySelected(day)" 
                  :indeterminate="isDayPartial(day)"
                  @change="$emit('toggle-day', day)"
                />
                Select Day
              </label>
              <span v-else class="text-mute empty-day-msg">No meals</span>
            </div>
          </th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="mt in mealTypesConfig" :key="mt.val">
          <td class="sticky-col label-cell">{{ mt.label }}</td>
          <td 
            v-for="day in campDays" 
            :key="day" 
            class="droppable-cell"
            @dragover.prevent
            @dragenter.prevent
            @drop="$emit('drop', $event, day, mt.val)"
          >
            <!-- Render Assigned Meals -->
            <div class="meals-list">
              <MealCard 
                v-for="meal in (mealsGrid[day] && mealsGrid[day][mt.val] ? mealsGrid[day][mt.val] : [])" 
                :key="meal.id as string"
                :meal="meal"
                :camp="camp"
                :recipe-name="recipeNames[meal.recipe as string] || 'Unknown'"
                :is-selected="selectedMeals.includes(meal.id)"
                @update:is-selected="handleMealSelection(meal.id, $event)"
                @edit="$emit('edit-meal', meal)"
                @toggle-done="$emit('toggle-done', meal)"
                @remove="$emit('remove-meal', meal)"
              />
            </div>
            
            <!-- Blank Canvas Text -->
            <div v-if="!(mealsGrid[day] && mealsGrid[day][mt.val] && mealsGrid[day][mt.val].length > 0)" class="empty-drop">
              Drop Here
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.matrix-container {
  padding: 0;
  border: 1px solid var(--color-border);
  background: var(--color-bg-surface);
  overflow-x: auto;
}

.title-print {
  margin-bottom: 1rem; 
  display: none;
}

.planner-table {
  width: 100%;
  border-collapse: collapse;
}

.planner-table th, .planner-table td {
  border: 1px solid var(--color-border);
  padding: 0.5rem;
  vertical-align: top;
}

.planner-table th {
  background: var(--color-bg-mute);
  position: sticky;
  top: 0;
  z-index: 2;
}

.day-col {
  min-width: 150px; 
  text-align: center;
}

.day-header-container {
  cursor: pointer;
}

.day-header {
  font-size: 1rem; 
  margin-bottom: 0.2rem; 
  font-weight: normal;
  transition: color 0.2s;
}

.day-header-container:hover .day-header {
  color: var(--color-primary);
}

.select-day-label {
  font-weight: normal; 
  font-size: 0.75rem; 
  cursor: pointer;
}

.empty-day-msg {
  font-size: 0.7rem; 
  font-weight: normal;
}

.sticky-col {
  position: sticky;
  left: 0;
  background: var(--color-bg-mute);
  font-weight: bold;
  z-index: 3;
}

.label-cell {
  background: var(--color-bg-surface);
  box-shadow: 2px 0 5px rgba(0,0,0,0.05); /* Slight shadow to separate from scrollable row */
  display: flex;
  align-items: center;
  min-height: 80px;
}

.droppable-cell {
  background: var(--color-bg-surface);
  min-height: 80px;
  position: relative;
  transition: background 0.2s ease;
}

.droppable-cell:hover, .droppable-cell:-moz-drag-over {
  background: #fdf5e6;
}

.empty-drop {
  opacity: 0;
  font-size: 0.8rem;
  color: var(--color-primary);
  text-align: center;
  padding: 1rem 0;
  transition: opacity 0.2s ease;
}

.droppable-cell:hover .empty-drop {
  opacity: 0.5;
}

.meals-list {
  display: flex;
  flex-direction: column;
}

@media print {
  .only-print {
    display: block !important;
  }
}
</style>
