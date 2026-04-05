<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { 
  mealsApiListRecipes, 
  mealsApiCreateRecipe, 
  mealsApiImportRecipe,
  type RecipeSchema 
} from '../client'
import { useRouter } from 'vue-router'

const router = useRouter()

const recipes = ref<RecipeSchema[]>([])
const searchQuery = ref('')
const filteredRecipes = computed(() => {
  if (!searchQuery.value) return recipes.value
  const q = searchQuery.value.toLowerCase()
  return recipes.value.filter(r => r.name.toLowerCase().includes(q))
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

async function fetchRecipes() {
  const { data } = await mealsApiListRecipes()
  if (data) recipes.value = data
}

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

onMounted(fetchRecipes)
</script>

<template>
  <div>
    <div class="flex justify-between items-center" style="margin-bottom: 1rem;">
      <h2>Recipes & Ingredients</h2>
      <div class="flex gap-2">
        <button class="btn btn-secondary" @click="showImportModal = true">✨ Magic AI Import</button>
        <button class="btn btn-primary" @click="showCreateModal = true">+ Create Recipe</button>
      </div>
    </div>
    
    <div style="margin-bottom: 2rem;">
      <input type="text" class="input" v-model="searchQuery" placeholder="Search recipes..." style="max-width: 400px;" />
    </div>
    
    <div class="grid" style="grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 1.5rem;">
      <router-link v-for="recipe in filteredRecipes" :key="recipe.id as string" :to="`/recipes/${recipe.id}`" class="card" style="text-decoration: none; color: inherit; cursor: pointer;">
        <h3>{{ recipe.name }}</h3>
        <p class="text-mute">{{ recipe.default_portions }} portions</p>
        <div class="flex gap-1 flex-wrap" style="margin-top: 0.5rem;" v-if="recipe.preferences && recipe.preferences.length > 0">
          <span v-for="pref in recipe.preferences" :key="pref.id" style="font-size: 0.75rem; background: var(--color-primary); color: white; padding: 2px 6px; border-radius: 4px;">
            {{ pref.name }}
          </span>
        </div>
      </router-link>
      <div v-if="filteredRecipes.length === 0" class="text-mute">
        No recipes found.
      </div>
    </div>

    <!-- Modal for Recipe -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="card modal-card">
        <h3>Create New Recipe</h3>
        <div class="flex-col gap-4" style="margin-top: 1rem;">
          <div>
            <label>Name</label>
            <input class="input" v-model="newRecipe.name" placeholder="Spaghetti Bolognese" />
          </div>
          <div>
            <label>Default Portions</label>
            <input class="input" type="number" v-model="newRecipe.default_portions" />
          </div>
          <div>
            <label>Description</label>
            <textarea class="input" v-model="newRecipe.description" rows="3"></textarea>
          </div>
          <div class="flex gap-2" style="margin-top: 1rem; justify-content: flex-end;">
            <button class="btn btn-secondary" @click="showCreateModal = false">Cancel</button>
            <button class="btn btn-primary" @click="handleCreateRecipe">Create</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Modal for Magic Import -->
    <div v-if="showImportModal" class="modal-overlay" @click.self="showImportModal = false">
      <div class="card modal-card">
        <h3 class="flex items-center gap-2">✨ Magic AI Recipe Import</h3>
        <p class="text-mute" style="margin-bottom: 1rem; font-size: 0.9rem;">
          Paste a recipe from a website, notes, or chat. Our AI will automatically extract the name, portions, instructions, and all ingredients for you.
        </p>
        
        <div v-if="!isImporting" class="flex-col gap-4">
          <textarea 
            class="input" 
            v-model="importText" 
            placeholder="Paste your recipe text here..." 
            rows="10"
            style="font-family: inherit;"
          ></textarea>
          <div class="flex gap-2 justify-end">
            <button class="btn btn-secondary" @click="showImportModal = false">Cancel</button>
            <button class="btn btn-primary" @click="handleImportRecipe" :disabled="!importText">Start AI Import</button>
          </div>
        </div>

        <div v-else class="flex-col items-center justify-center" style="padding: 3rem 1rem;">
          <div class="loader-spinner"></div>
          <p style="margin-top: 1.5rem; font-weight: 500;">AI is analyzing ingredients...</p>
          <p class="text-mute" style="font-size: 0.85rem;">This takes about 5 seconds.</p>
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
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
