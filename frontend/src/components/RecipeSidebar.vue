<script setup lang="ts">
import { computed } from 'vue'
import type { RecipeSchema } from '../client'

const props = defineProps<{
  recipes: RecipeSchema[]
  searchQuery: string
  isCollapsed: boolean
}>()

const emit = defineEmits<{
  (e: 'update:searchQuery', val: string): void
  (e: 'update:isCollapsed', val: boolean): void
  (e: 'dragstart', event: DragEvent, recipe: RecipeSchema): void
}>()

const filteredRecipes = computed(() => {
  if (!props.searchQuery) return props.recipes
  const q = props.searchQuery.toLowerCase()
  return props.recipes.filter(r => r.name.toLowerCase().includes(q))
})

function onDragStart(event: DragEvent, recipe: RecipeSchema) {
  emit('dragstart', event, recipe)
}
</script>

<template>
  <div class="card flex-col gap-2 sidebar" :class="{ 'sidebar-collapsed': isCollapsed }">
    <button 
      class="btn btn-secondary toggle-sidebar-btn shadow-md"
      @click="$emit('update:isCollapsed', !isCollapsed)"
      :title="isCollapsed ? 'Show Menu Pool' : 'Hide Menu Pool'"
    >
      {{ isCollapsed ? '»' : '«' }}
    </button>

    <div v-show="!isCollapsed" class="flex-col gap-2 content">
      <h3>Menu Pool</h3>
      <p class="text-mute subtitle">Drag a recipe into the timetable.</p>
      
      <input 
        type="text" 
        class="input search-input" 
        :value="searchQuery" 
        @input="$emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
        placeholder="Search menus..." 
      />

      <div class="recipes-list flex-col gap-2">
        <div 
          v-for="recipe in filteredRecipes" 
          :key="recipe.id as string" 
          class="recipe-draggable"
          draggable="true"
          @dragstart="onDragStart($event, recipe)"
        >
          <div class="flex justify-between items-start header-row">
            <strong class="recipe-name" :title="recipe.name">{{ recipe.name }}</strong>
            <span class="text-mute portions">{{ recipe.default_portions }}p</span>
          </div>
          <div class="flex gap-1 flex-wrap badges-row" v-if="recipe.preferences && recipe.preferences.length > 0">
            <span v-for="pref in recipe.preferences" :key="pref.id" class="badge-tiny">
              {{ pref.name }}
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <div v-show="isCollapsed" class="flex-col items-center justify-center h-full collapsed-indicator">
       <div class="vertical-text">
         MENU POOL
       </div>
    </div>
  </div>
</template>

<style scoped>
.sidebar {
  background: var(--color-bg-mute); 
  border: 1px solid var(--color-border);
  position: relative; 
  overflow: visible;
}

.sidebar-collapsed {
  /* Width is controlled by grid in parent but we set min-height etc if needed */
}

.toggle-sidebar-btn {
  position: absolute;
  right: -0.75rem;
  top: 1rem;
  width: 1.5rem;
  height: 1.5rem;
  padding: 0;
  border-radius: 50%;
  z-index: 10;
  background: var(--color-bg-surface);
}

.content {
  height: 100%;
}

.subtitle {
  font-size: 0.9rem;
}

.search-input {
  font-size: 0.9rem; 
  padding: 0.4rem; 
  margin-bottom: 0.5rem;
}

.recipes-list {
  overflow-y: auto; 
  max-height: calc(100vh - 250px); 
  padding-right: 0.5rem;
}

.recipe-draggable {
  padding: 0.75rem; 
  background: var(--color-bg-surface); 
  border: 1px solid var(--color-border); 
  border-radius: var(--radius-sm);
  cursor: grab;
  user-select: none;
  transition: transform 0.15s ease, box-shadow 0.15s ease;
}

.recipe-draggable:active {
  cursor: grabbing;
  transform: scale(0.98);
  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
}

.header-row {
  gap: 0.5rem;
}

.recipe-name {
  white-space: nowrap; 
  overflow: hidden; 
  text-overflow: ellipsis;
}

.portions {
  font-size: 0.75rem; 
  flex-shrink: 0;
}

.badges-row {
  margin-top: 0.25rem;
}

.badge-tiny {
  background: var(--color-primary-light);
  color: var(--color-primary-hover);
  padding: 0.1rem 0.3rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 500;
}

.collapsed-indicator {
  height: 100%;
}

.vertical-text {
  writing-mode: vertical-rl; 
  transform: rotate(180deg); 
  opacity: 0.5; 
  font-weight: bold; 
  font-size: 0.8rem; 
  margin-top: 2rem;
}
</style>
