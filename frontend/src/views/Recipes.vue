<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  mealsApiRecipesCreateRecipe,
  mealsApiRecipesImportRecipe,
  mealsApiIngredientsListTags,
  mealsApiRecipesListPreferences,
  type DietaryPreferenceSchema
} from '../client'
import { useRouter } from 'vue-router'
import TagInput from '../components/TagInput.vue'
import { useI18n } from '../composables/useI18n'
import { useRecipeList } from '../composables/useRecipeList'

const { t } = useI18n()
const router = useRouter()

const searchQuery = ref('')
const selectedTags = ref<string[]>([])
const selectedPreferenceId = ref<number | null>(null)

const allTags = ref<string[]>([])
const allPreferences = ref<DietaryPreferenceSchema[]>([])

const { recipes, isLoading, totalCount, hasMore, fetchRecipes, loadMore } = useRecipeList({
  searchQuery,
  selectedTags,
  selectedPreferenceId,
})

const showCreateModal = ref(false)
const newRecipe = ref({
  name: '',
  description: '',
  instructions: '',
  default_portions: 4,
  tags: [] as string[]
})

const showImportModal = ref(false)
const importText = ref('')
const isImporting = ref(false)

async function fetchMetadata() {
  const [tagsRes, prefsRes] = await Promise.all([
    mealsApiIngredientsListTags(),
    mealsApiRecipesListPreferences()
  ])
  if (tagsRes.data) allTags.value = tagsRes.data
  if (prefsRes.data) allPreferences.value = prefsRes.data
}

async function handleCreateRecipe() {
  if (!newRecipe.value.name) return
  const { data } = await mealsApiRecipesCreateRecipe({ body: newRecipe.value })
  if (data) {
    recipes.value.push(data)
    showCreateModal.value = false
    newRecipe.value = { name: '', description: '', instructions: '', default_portions: 4, tags: [] }
  }
}

async function handleImportRecipe() {
  if (!importText.value) return
  isImporting.value = true
  try {
    const { data } = await mealsApiRecipesImportRecipe({ body: { raw_text: importText.value } })
    if (data) {
      showImportModal.value = false
      importText.value = ''
      router.push(`/recipes/${data.id}`)
    }
  } catch (e) {
    alert("Import failed. Make sure your GEMINI_API_KEY is set in .env")
  } finally {
    isImporting.value = false
  }
}

onMounted(() => {
  fetchRecipes()
  fetchMetadata()
})
</script>

<template>
  <div>
    <div class="page-header mb-4">
      <h2>{{ t('recipe.title') }}</h2>
      <div class="flex gap-2">
        <button class="btn btn-secondary" @click="showImportModal = true">✨ {{ t('recipe.import') }}</button>
        <button class="btn btn-primary" @click="showCreateModal = true">+ {{ t('recipe.create') }}</button>
      </div>
    </div>

    <div class="flex gap-4 items-end flex-wrap mb-8">
      <div class="filter-field">
        <label class="filter-label">{{ t('btn.search') }}</label>
        <input type="text" class="input" v-model="searchQuery" :placeholder="t('recipe.search_placeholder')" />
      </div>

      <div class="filter-field">
        <label class="filter-label">{{ t('recipe.tags') }}</label>
        <TagInput v-model="selectedTags" :suggestions="allTags" :placeholder="t('planner.filter')" />
      </div>

      <div class="filter-field filter-field-narrow">
        <label class="filter-label">{{ t('recipe.tags') }}</label>
        <select v-model="selectedPreferenceId" class="input filter-select">
          <option :value="null">{{ t('planner.all_recipes') }}</option>
          <option v-for="p in allPreferences" :key="p.id!" :value="p.id">{{ p.name }}</option>
        </select>
      </div>
    </div>

    <div class="flex-col gap-8 mt-8">
      <div class="grid-cards">
        <router-link v-for="recipe in recipes" :key="recipe.id as string" :to="`/recipes/${recipe.id}`"
          class="card recipe-card">
          <h3>{{ recipe.name }}</h3>
          <p class="text-mute">{{ recipe.default_portions }} {{ t('recipe.portions') }}</p>
          <div class="flex gap-1 flex-wrap mt-2" v-if="recipe.preferences && recipe.preferences.length > 0">
            <span v-for="pref in recipe.preferences" :key="pref.id!" class="badge-primary">
              {{ pref.name }}
            </span>
          </div>
        </router-link>
      </div>

      <div v-if="recipes.length === 0 && !isLoading" class="text-mute text-center py-8">
        {{ t('recipe.no_results') }}
      </div>

      <div v-if="hasMore" class="flex justify-center mt-8">
        <button class="btn btn-secondary" @click="loadMore" :disabled="isLoading">
          {{ isLoading ? t('btn.loading') : t('btn.search') }}
        </button>
      </div>
      <div v-else-if="recipes.length > 0" class="text-center text-mute text-sm mt-8">
        {{ totalCount }} {{ t('recipe.title') }}
      </div>
    </div>

    <!-- Create Recipe Modal -->
    <div v-if="showCreateModal" class="modal-backdrop" @click.self="showCreateModal = false">
      <div class="modal modal-wide">
        <h3>{{ t('recipe.create') }}</h3>
        <div class="flex-col gap-4 mt-4">
          <div>
            <label>{{ t('camp.name_label') }}</label>
            <input class="input" v-model="newRecipe.name" placeholder="Spaghetti Bolognese" />
          </div>
          <div>
            <label>{{ t('recipe.portions') }}</label>
            <input class="input" type="number" v-model="newRecipe.default_portions" />
          </div>
          <div>
            <label>{{ t('recipe.description') }}</label>
            <textarea class="input" v-model="newRecipe.description" rows="3"></textarea>
          </div>
          <div>
            <label>{{ t('recipe.tags') }}</label>
            <div class="mt-2">
              <TagInput v-model="newRecipe.tags" :suggestions="allTags" :placeholder="t('btn.add')" />
            </div>
          </div>
          <div class="flex gap-2 justify-end mt-4">
            <button class="btn btn-secondary" @click="showCreateModal = false">{{ t('btn.cancel') }}</button>
            <button class="btn btn-primary" @click="handleCreateRecipe">{{ t('btn.create') }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Magic Import Modal -->
    <div v-if="showImportModal" class="modal-backdrop" @click.self="showImportModal = false">
      <div class="modal modal-wide">
        <h3 class="flex items-center gap-2">✨ {{ t('recipe.import') }}</h3>
        <p class="text-mute text-sm mb-4">
          {{ t('recipe.import_text') }}
        </p>

        <div v-if="!isImporting" class="flex-col gap-4">
          <textarea class="input" v-model="importText" :placeholder="t('recipe.import_text')" rows="10"></textarea>
          <div class="flex gap-2 justify-end">
            <button class="btn btn-secondary" @click="showImportModal = false">{{ t('btn.cancel') }}</button>
            <button class="btn btn-primary" @click="handleImportRecipe" :disabled="!importText">{{ t('recipe.import')
              }}</button>
          </div>
        </div>

        <div v-else class="flex-col items-center justify-center py-8">
          <div class="spinner"></div>
          <p class="mt-6 font-bold">{{ t('recipe.importing') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.filter-field {
  flex: 1;
  min-width: 250px;
}

.filter-field-narrow {
  flex: 0.5;
  min-width: 150px;
}

.filter-label {
  font-size: 0.8rem;
  color: var(--color-text-mute);
  margin-bottom: 0.25rem;
}

.filter-select {
  height: 42px;
}

.recipe-card {
  text-decoration: none;
  color: inherit;
  cursor: pointer;
}
</style>
