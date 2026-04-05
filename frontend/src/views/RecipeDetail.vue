<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  mealsApiGetRecipe, 
  mealsApiUpdateRecipe,
  mealsApiListRecipeIngredients, 
  mealsApiAddRecipeIngredient, 
  mealsApiUpdateRecipeIngredient,
  mealsApiDeleteRecipeIngredient,
  mealsApiListIngredients,
  mealsApiListPreferences,
  mealsApiListUnits,
  type RecipeSchema, 
  type RecipeIngredientSchema, 
  type IngredientSchema,
  type DietaryPreferenceSchema
} from '../client'
import MarkdownView from '../components/MarkdownView.vue'

const route = useRoute()
const router = useRouter()
const recipeId = route.params.id as string

const recipe = ref<RecipeSchema | null>(null)
const ingredients = ref<RecipeIngredientSchema[]>([])

// Smart Dropdown States
const ingredientQuery = ref('')
const amountInput = ref(1)
const unitInput = ref('g')

const allKnownIngredients = ref<IngredientSchema[]>([])
const searchResults = ref<IngredientSchema[]>([])
const showSuggestions = ref(false)

const allKnownUnits = ref<string[]>([])
const unitSearchResults = ref<string[]>([])
const showUnitSuggestions = ref(false)

// Recipe Edit State
const isEditingRecipe = ref(false)
const allPreferences = ref<DietaryPreferenceSchema[]>([])
const editRecipeData = ref({
  description: '',
  instructions: '',
  default_portions: 4,
  preference_ids: [] as number[]
})

const isPolling = ref(false)
let pollTimer: any = null

async function fetchRecipe() {
  const { data: r } = await mealsApiGetRecipe({ path: { recipe_id: recipeId } })
  if (r) {
    recipe.value = r
    editRecipeData.value = {
      description: r.description || '',
      instructions: r.instructions || '',
      default_portions: r.default_portions,
      preference_ids: r.preferences ? r.preferences.map((p: any) => p.id) : []
    }
    
    // Manage polling
    if (r.is_importing && !isPolling.value) {
      startPolling()
    } else if (!r.is_importing && isPolling.value) {
      stopPolling()
    }
  }
}

function startPolling() {
  isPolling.value = true
  pollTimer = setInterval(async () => {
    await fetchRecipe()
    await fetchIngredients()
  }, 2000)
}

function stopPolling() {
  isPolling.value = false
  if (pollTimer) clearInterval(pollTimer)
}

async function saveRecipeDetails() {
  if (!recipe.value) return
  const { data } = await mealsApiUpdateRecipe({
    path: { recipe_id: recipeId },
    body: {
      description: editRecipeData.value.description,
      instructions: editRecipeData.value.instructions,
      default_portions: editRecipeData.value.default_portions,
      preference_ids: editRecipeData.value.preference_ids
    }
  })
  if (data) {
    recipe.value = data
    isEditingRecipe.value = false
  }
}

async function fetchPreferences() {
  const { data } = await mealsApiListPreferences()
  if (data) allPreferences.value = data
}

async function fetchUnits() {
  const { data } = await mealsApiListUnits()
  if (data) allKnownUnits.value = data
}

// Quick fetch helper
import { mealsApiListRecipes } from '../client'

async function fetchIngredients() {
  const { data } = await mealsApiListRecipeIngredients({ path: { recipe_id: recipeId } })
  if (data) ingredients.value = data
}

// Debounce-like logic for search
watch(ingredientQuery, async (newQuery) => {
  if (newQuery.length < 2) {
    searchResults.value = []
    showSuggestions.value = false
    return
  }
  const { data } = await mealsApiListIngredients({ query: { q: newQuery } })
  if (data) {
    searchResults.value = data
    showSuggestions.value = data.length > 0
  }
})

// Unit suggestions
watch(unitInput, (newVal) => {
  if (!newVal) {
    unitSearchResults.value = allKnownUnits.value
    return
  }
  unitSearchResults.value = allKnownUnits.value.filter(u => 
    u.toLowerCase().includes(newVal.toLowerCase())
  )
})

function selectUnitSuggestion(unit: string) {
  unitInput.value = unit
  showUnitSuggestions.value = false
}

function selectSuggestion(ingredient: IngredientSchema) {
  ingredientQuery.value = ingredient.name
  // Predict default unit if it exists based on base unit?
  if (ingredient.base_unit === 'kg') unitInput.value = 'g'
  else if (ingredient.base_unit === 'l') unitInput.value = 'dl'
  else unitInput.value = ingredient.base_unit
  
  showSuggestions.value = false
}

async function handleAddIngredient() {
  if (!ingredientQuery.value) return
  
  const { data, error } = await mealsApiAddRecipeIngredient({
    path: { recipe_id: recipeId },
    body: {
      ingredient_name: ingredientQuery.value,
      amount: amountInput.value,
      unit: unitInput.value
    }
  })
  
  if (data) {
    ingredients.value.push(data)
    ingredientQuery.value = ''
    amountInput.value = 1
    unitInput.value = 'g'
    showSuggestions.value = false
  } else {
    alert("Error adding ingredient: " + JSON.stringify(error))
  }
}

// Editing ingredients
const editingIngId = ref<string | null>(null)
const editIngAmount = ref(0)
const editIngUnit = ref('')

function startEditIng(ing: RecipeIngredientSchema) {
  editingIngId.value = ing.id as string
  editIngAmount.value = ing.amount
  editIngUnit.value = ing.unit
}

async function saveEditIng(ing: RecipeIngredientSchema) {
  const { data } = await mealsApiUpdateRecipeIngredient({
    path: { recipe_id: recipeId, ingredient_id: ing.id as string },
    body: { amount: editIngAmount.value, unit: editIngUnit.value }
  })
  if (data) {
    ing.amount = data.amount
    ing.unit = data.unit
    editingIngId.value = null
  }
}

async function removeIngredient(ing: RecipeIngredientSchema) {
  if (!confirm("Remove ingredient?")) return
  await mealsApiDeleteRecipeIngredient({
    path: { recipe_id: recipeId, ingredient_id: ing.id as string }
  })
  ingredients.value = ingredients.value.filter(i => i.id !== ing.id)
}

onMounted(() => {
  fetchRecipe()
  fetchIngredients()
  fetchPreferences()
  fetchUnits()
})

import { onUnmounted } from 'vue'
onUnmounted(() => {
  stopPolling()
})
</script>

<template>
  <div v-if="recipe" style="position: relative;">
    <!-- AI Loading Overlay -->
    <div v-if="recipe.is_importing" class="ai-overlay">
      <div class="ai-loader-card">
        <div class="magic-spinner">✨</div>
        <h3>AI is crafting your recipe...</h3>
        <p>Gemini is parsing your text and categorizing ingredients.</p>
        <div class="progress-bar-container">
          <div class="progress-bar-fill"></div>
        </div>
      </div>
    </div>

    <div class="flex items-center gap-4" :class="{ 'blur-bg': recipe.is_importing }" style="margin-bottom: 2rem;">
      <button class="btn btn-secondary" @click="router.push('/recipes')">&larr; Back</button>
      <h2>{{ recipe.name }}</h2>
    </div>

    <div class="grid" :class="{ 'blur-bg': recipe.is_importing }" style="grid-template-columns: 1fr 2fr; gap: 2rem;">
      <!-- Details Panel -->
      <div class="card flex-col gap-4" style="position: relative;">
        <div class="flex justify-between items-start">
          <h3>Details</h3>
          <button v-if="!isEditingRecipe" class="btn btn-secondary" @click="isEditingRecipe = true">Edit</button>
        </div>

        <div v-if="!isEditingRecipe">
          <div style="margin-bottom: 1rem;">
            <label>Tags & Preferences</label>
            <div class="flex gap-1 flex-wrap" style="margin-top: 0.25rem;">
              <span v-for="pref in recipe.preferences" :key="pref.id" style="font-size: 0.8rem; background: var(--color-primary); color: white; padding: 2px 6px; border-radius: 4px;">
                {{ pref.name }}
              </span>
              <span v-if="!recipe.preferences || recipe.preferences.length === 0" class="text-mute" style="font-size: 0.8rem;">
                No preferences tagged.
              </span>
            </div>
          </div>
          <div style="margin-bottom: 1rem;">
            <label>Default Portions</label>
            <div class="text-mute" style="font-size: 1.25rem;">{{ recipe.default_portions }}</div>
          </div>
          <div>
            <label>Description</label>
            <p>{{ recipe.description || 'No description provided.' }}</p>
          </div>
          <div>
            <label>Instructions</label>
            <div style="margin-top: 0.5rem;">
              <MarkdownView v-if="recipe.instructions" :content="recipe.instructions" />
              <p v-else class="text-mute">No instructions provided.</p>
            </div>
          </div>
        </div>

        <div v-else class="flex-col gap-4">
          <div>
            <label>Dietary Preferences / Tags</label>
            <div class="flex gap-2 flex-wrap" style="margin-top: 0.5rem;">
              <label 
                v-for="pref in allPreferences" 
                :key="pref.id" 
                class="flex items-center gap-1"
                style="padding: 4px 8px; border: 1px solid var(--color-border); border-radius: 6px; cursor:pointer;"
              >
                <input type="checkbox" :value="pref.id" v-model="editRecipeData.preference_ids" />
                <span style="font-size: 0.85rem;">{{ pref.name }}</span>
              </label>
            </div>
          </div>
          <div>
            <label>Default Portions</label>
            <input type="number" class="input" v-model="editRecipeData.default_portions" />
          </div>
          <div>
            <label>Description</label>
            <textarea class="input" v-model="editRecipeData.description" rows="3"></textarea>
          </div>
          <div>
            <label>Instructions</label>
            <textarea class="input" v-model="editRecipeData.instructions" rows="6"></textarea>
          </div>
          <div class="flex gap-2 justify-end">
            <button class="btn btn-secondary" @click="isEditingRecipe = false">Cancel</button>
            <button class="btn btn-primary" @click="saveRecipeDetails">Save</button>
          </div>
        </div>
      </div>

      <!-- Ingredients Panel -->
      <div class="card">
        <h3>Ingredients</h3>
        <p class="text-mute" style="margin-bottom: 1rem;">Add ingredients. They will be auto-categorized and unit-converged when possible.</p>
        
        <!-- Smart Added Form -->
        <div class="flex items-end gap-2" style="margin-bottom: 1.5rem; position: relative;">
          <div style="flex: 2;">
            <label>Ingredient</label>
            <input 
              class="input" 
              v-model="ingredientQuery" 
              placeholder="e.g. Tomato" 
              @focus="showSuggestions = searchResults.length > 0"
              autocomplete="off"
            />
            
            <!-- Dropdown -->
            <ul v-if="showSuggestions" class="dropdown">
              <li 
                v-for="res in searchResults" 
                :key="res.id as string" 
                @click="selectSuggestion(res)"
                @mousedown.prevent
              >
                {{ res.name }} <span class="text-mute" style="font-size: 0.8rem;">(Base: {{ res.base_unit }})</span>
              </li>
            </ul>
          </div>
          
          <div style="flex: 1;">
            <label>Amount</label>
            <input class="input" type="number" step="0.01" v-model="amountInput" />
          </div>
          
          <div style="flex: 1; position: relative;">
            <label>Unit</label>
            <input 
              class="input" 
              v-model="unitInput" 
              placeholder="g, ml, pcs" 
              @focus="showUnitSuggestions = true; unitSearchResults = allKnownUnits"
            />
            
            <ul v-if="showUnitSuggestions && unitSearchResults.length" class="dropdown dropdown-units">
              <li 
                v-for="u in unitSearchResults" 
                :key="u" 
                @click="selectUnitSuggestion(u)"
                @mousedown.prevent
              >
                {{ u }}
              </li>
            </ul>
          </div>
          
          <button class="btn btn-primary" @click="handleAddIngredient" style="height: 48px;">Add</button>
        </div>

        <hr style="margin: 1.5rem 0;" />

        <ul style="list-style: none; padding: 0;" class="flex-col gap-2">
          <li v-for="ing in ingredients" :key="ing.id as string" class="flex justify-between items-center" style="padding: 0.75rem; background: var(--color-bg-mute); border-radius: var(--radius-sm);">
            <div style="flex: 2;">
              <strong>{{ ing.ingredient.name }}</strong>
            </div>

            <!-- View Mode -->
            <div v-if="editingIngId !== ing.id" class="flex items-center gap-4" style="flex: 1; justify-content: flex-end;">
              <span class="text-mute" style="min-width: 60px; text-align: right;">{{ ing.amount }} {{ ing.unit }}</span>
              <div class="flex gap-2">
                <button class="btn btn-secondary" style="padding: 0.25rem 0.5rem;" @click="startEditIng(ing)">✎</button>
                <button class="btn" style="padding: 0.25rem 0.5rem; color: var(--color-danger); background: transparent;" @click="removeIngredient(ing)">✕</button>
              </div>
            </div>

            <!-- Edit Mode -->
            <div v-else class="flex items-center gap-2" style="flex: 1; justify-content: flex-end;">
              <input type="number" step="0.01" class="input" style="width: 80px; padding: 0.25rem;" v-model="editIngAmount" />
              <input class="input" style="width: 60px; padding: 0.25rem;" v-model="editIngUnit" />
              <button class="btn btn-primary" style="padding: 0.25rem 0.5rem;" @click="saveEditIng(ing)">✔</button>
              <button class="btn btn-secondary" style="padding: 0.25rem 0.5rem;" @click="editingIngId = null">✕</button>
            </div>
          </li>
          <li v-if="ingredients.length === 0" class="text-mute">
            No ingredients added yet.
          </li>
        </ul>
      </div>
    </div>
  </div>
  <div v-else>
    Loading recipe...
  </div>
</template>

<style scoped>
.dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  width: 50%;
  min-width: 200px;
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  margin-top: 0.5rem;
  padding: 0.5rem;
  list-style: none;
  z-index: 10;
  box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
}
.dropdown li {
  padding: 0.5rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
}
.dropdown li:hover {
  background: var(--color-bg-mute);
}

.dropdown-units {
  width: 100%;
  left: 0;
  max-height: 200px;
  overflow-y: auto;
}

.ai-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(4px);
  z-index: 100;
  display: flex;
  justify-content: center;
  align-items: flex-start;
  padding-top: 100px;
  border-radius: var(--radius-lg);
}

.ai-loader-card {
  background: var(--color-bg-surface);
  padding: 3rem;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  text-align: center;
  border: 1px solid var(--color-border);
  max-width: 400px;
}

.magic-spinner {
  font-size: 3rem;
  animation: pulse-rotate 2s infinite ease-in-out;
  margin-bottom: 1rem;
}

@keyframes pulse-rotate {
  0% { transform: scale(1) rotate(0deg); opacity: 0.8; }
  50% { transform: scale(1.2) rotate(180deg); opacity: 1; }
  100% { transform: scale(1) rotate(360deg); opacity: 0.8; }
}

.blur-bg {
  filter: blur(2px);
  opacity: 0.6;
  pointer-events: none;
}

.progress-bar-container {
  width: 100%;
  height: 6px;
  background: var(--color-bg-mute);
  border-radius: 3px;
  margin-top: 1.5rem;
  overflow: hidden;
}

.progress-bar-fill {
  height: 100%;
  background: var(--color-primary);
  width: 30%;
  border-radius: 3px;
  animation: progress-slide 2s infinite ease-in-out;
}

@keyframes progress-slide {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(300%); }
}
</style>
