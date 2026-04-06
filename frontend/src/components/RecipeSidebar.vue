<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { mealsApiListRecipes, type RecipeSchema, type DietaryPreferenceSchema } from '../client'
import TagInput from './TagInput.vue'
import { useI18n } from '../composables/useI18n'

const { t } = useI18n()

const props = defineProps<{
  preferences: DietaryPreferenceSchema[]
  allTags: string[]
  searchQuery: string
  isCollapsed: boolean
}>()

const emit = defineEmits<{
  (e: 'update:searchQuery', val: string): void
  (e: 'update:isCollapsed', val: boolean): void
  (e: 'dragstart', event: DragEvent, recipe: RecipeSchema): void
}>()

const recipes = ref<RecipeSchema[]>([])
const selectedTags = ref<string[]>([])
const selectedPreferenceId = ref<number | null>(null)
const currentPage = ref(1)
const totalCount = ref(0)
const isLoading = ref(false)

async function fetchRecipes(reset = false) {
  if (reset) {
    currentPage.value = 1
  }
  isLoading.value = true
  try {
    const { data } = await mealsApiListRecipes({
      query: {
        page: currentPage.value,
        q: props.searchQuery || undefined,
        tags: selectedTags.value.length > 0 ? selectedTags.value.join(',') : undefined,
        preference_id: selectedPreferenceId.value || undefined
      }
    })
    if (data) {
      if (reset) recipes.value = data.items
      else recipes.value.push(...data.items)
      totalCount.value = data.count
    }
  } finally {
    isLoading.value = false
  }
}

const hasMore = computed(() => recipes.value.length < totalCount.value)

function loadMore() {
  if (hasMore.value && !isLoading.value) {
    currentPage.value++
    fetchRecipes()
  }
}

watch(() => props.searchQuery, () => {
  fetchRecipes(true)
})

watch([selectedTags, selectedPreferenceId], () => {
  fetchRecipes(true)
})

onMounted(() => {
  fetchRecipes()
})

function onDragStart(event: DragEvent, recipe: RecipeSchema) {
  emit('dragstart', event, recipe)
}
</script>

<template>
  <div class="card flex-col gap-2 sidebar" :class="{ 'sidebar-collapsed': isCollapsed }">
    <button class="btn btn-secondary toggle-sidebar-btn shadow-md" @click="$emit('update:isCollapsed', !isCollapsed)"
      :title="isCollapsed ? 'Show Menu Pool' : 'Hide Menu Pool'">
      {{ isCollapsed ? '»' : '«' }}
    </button>

    <div v-show="!isCollapsed" class="flex-col gap-2 content">
      <h3>{{ t('planner.menu_pool') }}</h3>
      <p class="text-mute subtitle">{{ t('recipe.search_placeholder') }}</p>

      <div class="flex-col gap-1.5 filters-area">
        <input type="text" class="input search-input" :value="searchQuery"
          @input="$emit('update:searchQuery', ($event.target as HTMLInputElement).value)"
          :placeholder="t('recipe.search_placeholder')" />

        <TagInput v-model="selectedTags" :suggestions="allTags" :placeholder="t('planner.filter')"
          class="sidebar-tag-input" />

        <select v-model="selectedPreferenceId" class="input filter-select">
          <option :value="null">{{ t('planner.all_recipes') }}</option>
          <option v-for="p in preferences" :key="p.id!" :value="p.id">{{ p.name }}</option>
        </select>
      </div>

      <div class="recipes-list flex-col gap-2">
        <div v-for="recipe in recipes" :key="recipe.id!" class="recipe-draggable" draggable="true"
          @dragstart="onDragStart($event, recipe)">
          <div class="flex justify-between items-start header-row">
            <strong class="recipe-name" :title="recipe.name">{{ recipe.name }}</strong>
            <span class="text-mute portions">{{ recipe.default_portions }}p</span>
          </div>
          <div class="flex gap-1 flex-wrap badges-row" v-if="recipe.preferences && recipe.preferences.length > 0">
            <span v-for="pref in recipe.preferences" :key="pref.id!" class="badge-tiny">
              {{ pref.name }}
            </span>
          </div>
        </div>

        <div v-if="recipes.length === 0 && !isLoading" class="text-mute text-center" style="padding: 1rem;">
          {{ t('recipe.no_results') }}
        </div>

        <div v-if="hasMore" class="flex justify-center" style="margin-top: 0.5rem; margin-bottom: 1rem;">
          <button class="btn btn-secondary btn-sm" @click="loadMore" :disabled="isLoading"
            style="font-size: 0.75rem; padding: 0.3rem 0.6rem;">
            {{ isLoading ? '...' : t('btn.search') }}
          </button>
        </div>
      </div>
    </div>

    <div v-show="isCollapsed" class="flex-col items-center justify-center h-full collapsed-indicator">
      <div class="vertical-text">
        {{ t('planner.menu_pool') }}
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
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.search-input,
.filter-select {
  font-size: 0.85rem;
  padding: 0.5rem 0.75rem;
  height: 38px;
}

.filter-select {
  cursor: pointer;
}

.filters-area {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.sidebar-tag-input :deep(.tag-input-box) {
  padding: 0.25rem 0.5rem;
  min-height: 38px;
  border-radius: var(--radius-md);
}

.sidebar-tag-input :deep(.tag-badge) {
  padding: 1px 6px;
  font-size: 0.75rem;
}

.sidebar-tag-input :deep(.tag-input-field) {
  font-size: 0.85rem;
}

.recipes-list {
  overflow-y: auto;
  max-height: 520px;
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
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.1);
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
