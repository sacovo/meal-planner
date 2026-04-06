<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import {
  mealsApiListRecipes,
  mealsApiCreateRecipe,
  mealsApiImportRecipe,
  mealsApiListTags,
  mealsApiListPreferences,
  type RecipeSchema,
  type DietaryPreferenceSchema
} from '../client'
import { useRouter } from 'vue-router'
import TagInput from '../components/TagInput.vue'
import { useI18n } from '../composables/useI18n'

const { t } = useI18n()
const router = useRouter()

const recipes = ref<RecipeSchema[]>([])
const searchQuery = ref('')
const selectedTags = ref<string[]>([])
const selectedPreferenceId = ref<number | null>(null)

const allTags = ref<string[]>([])
const allPreferences = ref<DietaryPreferenceSchema[]>([])

const totalCount = ref(0)
const currentPage = ref(1)
const isLoading = ref(false)

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

async function fetchData(reset = false) {
  if (reset) {
    currentPage.value = 1
  }

  isLoading.value = true
  try {
    const [recipesRes, tagsRes, prefsRes] = await Promise.all([
      mealsApiListRecipes({
        query: {
          page: currentPage.value,
          q: searchQuery.value || undefined,
          tags: selectedTags.value.length > 0 ? selectedTags.value.join(',') : undefined,
          preference_id: selectedPreferenceId.value || undefined
        }
      }),
      mealsApiListTags(),
      mealsApiListPreferences()
    ])

    if (recipesRes.data) {
      if (reset) {
        recipes.value = recipesRes.data.items
      } else {
        recipes.value.push(...recipesRes.data.items)
      }
      totalCount.value = recipesRes.data.count
    }
    if (tagsRes.data) allTags.value = tagsRes.data
    if (prefsRes.data) allPreferences.value = prefsRes.data
  } finally {
    isLoading.value = false
  }
}

const hasMore = computed(() => recipes.value.length < totalCount.value)

function loadMore() {
  if (hasMore.value && !isLoading.value) {
    currentPage.value++
    fetchData()
  }
}

watch([searchQuery, selectedTags, selectedPreferenceId], () => {
  fetchData(true)
})

async function handleCreateRecipe() {
  if (!newRecipe.value.name) return
  const { data } = await mealsApiCreateRecipe({ body: newRecipe.value })
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
    const { data } = await mealsApiImportRecipe({ body: { raw_text: importText.value } })
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

onMounted(fetchData)
</script>

<template>
  <div>
    <div class="flex justify-between items-center" style="margin-bottom: 1rem;">
      <h2>{{ t('recipe.title') }}</h2>
      <div class="flex gap-2">
        <button class="btn btn-secondary" @click="showImportModal = true">✨ {{ t('recipe.import') }}</button>
        <button class="btn btn-primary" @click="showCreateModal = true">+ {{ t('recipe.create') }}</button>
      </div>
    </div>

    <div class="flex gap-4 items-end filters-bar" style="margin-bottom: 2rem; flex-wrap: wrap;">
      <div style="flex: 1; min-width: 250px;">
        <label class="text-mute" style="font-size: 0.8rem; margin-bottom: 0.25rem; display: block;">{{ t('btn.search')
          }}</label>
        <input type="text" class="input" v-model="searchQuery" :placeholder="t('recipe.search_placeholder')" />
      </div>

      <div style="flex: 1; min-width: 250px;">
        <label class="text-mute" style="font-size: 0.8rem; margin-bottom: 0.25rem; display: block;">{{ t('recipe.tags')
          }}</label>
        <TagInput v-model="selectedTags" :suggestions="allTags" :placeholder="t('planner.filter')" />
      </div>

      <div style="flex: 0.5; min-width: 150px;">
        <label class="text-mute" style="font-size: 0.8rem; margin-bottom: 0.25rem; display: block;">{{ t('recipe.tags')
          }}</label>
        <select v-model="selectedPreferenceId" class="input" style="height: 42px;">
          <option :value="null">{{ t('planner.all_recipes') }}</option>
          <option v-for="p in allPreferences" :key="p.id!" :value="p.id">{{ p.name }}</option>
        </select>
      </div>
    </div>

    <div class="flex-col gap-8" style="margin-top: 2rem;">
      <div class="grid" style="grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem;">
        <router-link v-for="recipe in recipes" :key="recipe.id as string" :to="`/recipes/${recipe.id}`" class="card"
          style="text-decoration: none; color: inherit; cursor: pointer;">
          <h3>{{ recipe.name }}</h3>
          <p class="text-mute">{{ recipe.default_portions }} {{ t('recipe.portions') }}</p>
          <div class="flex gap-1 flex-wrap" style="margin-top: 0.5rem;"
            v-if="recipe.preferences && recipe.preferences.length > 0">
            <span v-for="pref in recipe.preferences" :key="pref.id!"
              style="font-size: 0.75rem; background: var(--color-primary); color: white; padding: 2px 6px; border-radius: 4px;">
              {{ pref.name }}
            </span>
          </div>
        </router-link>
      </div>

      <div v-if="recipes.length === 0 && !isLoading" class="text-mute text-center" style="padding: 2rem;">
        {{ t('recipe.no_results') }}
      </div>

      <div v-if="hasMore" class="flex justify-center" style="margin-top: 2rem;">
        <button class="btn btn-secondary" @click="loadMore" :disabled="isLoading">
          {{ isLoading ? t('btn.loading') : t('btn.search') }}
        </button>
      </div>
      <div v-else-if="recipes.length > 0" class="text-center text-mute" style="font-size: 0.85rem; margin-top: 2rem;">
        {{ totalCount }} {{ t('recipe.title') }}
      </div>
    </div>

    <!-- Modal for Recipe -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="card modal-card">
        <h3>{{ t('recipe.create') }}</h3>
        <div class="flex-col gap-4" style="margin-top: 1rem;">
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
            <div style="margin-top: 0.25rem;">
              <TagInput v-model="newRecipe.tags" :suggestions="allTags" :placeholder="t('btn.add')" />
            </div>
          </div>
          <div class="flex gap-2" style="margin-top: 1rem; justify-content: flex-end;">
            <button class="btn btn-secondary" @click="showCreateModal = false">{{ t('btn.cancel') }}</button>
            <button class="btn btn-primary" @click="handleCreateRecipe">{{ t('btn.create') }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal for Magic Import -->
    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="card modal-card">
        <h3 class="flex items-center gap-2">✨ {{ t('recipe.import') }}</h3>
        <p class="text-mute" style="margin-bottom: 1rem; font-size: 0.9rem;">
          {{ t('recipe.import_text') }}
        </p>

        <div v-if="!isImporting" class="flex-col gap-4">
          <textarea class="input" v-model="importText" :placeholder="t('recipe.import_text')" rows="10"
            style="font-family: inherit;"></textarea>
          <div class="flex gap-2 justify-end">
            <button class="btn btn-secondary" @click="showImportModal = false">{{ t('btn.cancel') }}</button>
            <button class="btn btn-primary" @click="handleImportRecipe" :disabled="!importText">{{ t('recipe.import')
              }}</button>
          </div>
        </div>

        <div v-else class="flex-col items-center justify-center" style="padding: 3rem 1rem;">
          <div class="loader-spinner"></div>
          <p style="margin-top: 1.5rem; font-weight: 500;">{{ t('recipe.importing') }}</p>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.modal-card {
  width: 100%;
  max-width: 600px;
  box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1);
}

.loader-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--color-bg-mute);
  border-top: 4px solid var(--color-primary);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}
</style>
