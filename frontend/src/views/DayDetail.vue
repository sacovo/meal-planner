<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { 
  mealsApiGetCamp,
  mealsApiListCampMeals,
  mealsApiListRecipes,
  mealsApiListRecipeIngredients,
  mealsApiToggleCampMealDone,
  type CampSchema,
  type CampMealSchema,
  type RecipeSchema,
  type RecipeIngredientSchema
} from '../client'
// @ts-ignore
import html2pdf from 'html2pdf.js'

const route = useRoute()
const router = useRouter()

const campId = route.params.id as string
const dateStr = route.params.date as string

const camp = ref<CampSchema | null>(null)
const meals = ref<CampMealSchema[]>([])
const recipes = ref<RecipeSchema[]>([])
const ingredientsMap = ref<Record<string, RecipeIngredientSchema[]>>({})
const loading = ref(true)

const mealTypesConfig = [
  { val: "BREAKFAST", label: "Frühstück" },
  { val: "MORNING_SNACK", label: "Znüni" },
  { val: "LUNCH", label: "Mittagessen" },
  { val: "AFTERNOON_SNACK", label: "Zvieri" },
  { val: "DINNER", label: "Abendessen" },
  { val: "DESSERT", label: "Dessert" },
]

async function fetchData() {
  loading.value = true
  try {
    const { data: campData } = await mealsApiGetCamp({ path: { camp_id: campId } })
    if (campData) camp.value = campData

    const { data: allMeals } = await mealsApiListCampMeals({ path: { camp_id: campId } })
    if (allMeals) {
      meals.value = allMeals.filter(m => m.date === dateStr)
    }

    const { data: allRecipes } = await mealsApiListRecipes()
    if (allRecipes) recipes.value = allRecipes

    // Fetch ingredients for these meals
    for (const meal of meals.value) {
      if (!ingredientsMap.value[meal.recipe]) {
        const { data: ingData } = await mealsApiListRecipeIngredients({ path: { recipe_id: meal.recipe } })
        if (ingData) {
          ingredientsMap.value[meal.recipe] = ingData
        }
      }
    }
  } finally {
    loading.value = false
  }
}

async function toggleMealDone(meal: CampMealSchema) {
  try {
    const { data } = await mealsApiToggleCampMealDone({
      path: { camp_id: campId, meal_id: meal.id as string }
    })
    if (data) {
      meal.is_done = data.is_done
    }
  } catch (e) {
    console.error(e)
  }
}

function getRecipe(id: string) {
  return recipes.value.find(r => r.id === id)
}

function getScaledAmount(ri: RecipeIngredientSchema, meal: CampMealSchema) {
  const recipe = getRecipe(meal.recipe)
  if (!recipe || !recipe.default_portions) return ri.amount
  const people = meal.override_people_count !== null ? meal.override_people_count : (camp.value?.default_people_count || 4)
  return (ri.amount * people) / recipe.default_portions
}

function exportPDF() {
  const element = document.getElementById('printable-content')
  const opt = {
    margin: 10,
    filename: `DayPlan_${dateStr}.pdf`,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { scale: 2 },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
  }
  html2pdf().set(opt).from(element).save()
}

onMounted(fetchData)
</script>

<template>
  <div class="container page-container">
    <div class="flex justify-between items-center no-print" style="margin-bottom: 2rem;">
      <div class="flex items-center gap-4">
        <button class="btn btn-secondary" @click="router.push(`/camps/${campId}`)">&larr; Back to Plan</button>
        <h2 v-if="camp">{{ camp.name }} - {{ new Date(dateStr).toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long' }) }}</h2>
      </div>
      <div class="flex gap-2">
        <button class="btn btn-primary" @click="exportPDF">🖨 Export PDF / Print</button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-20">
      <div class="text-mute">Loading daily details...</div>
    </div>

    <div v-else id="printable-content" class="flex-col gap-8 print-container">
      <div class="print-header only-print">
        <h1>{{ camp?.name }}</h1>
        <h2>{{ new Date(dateStr).toLocaleDateString(undefined, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }) }}</h2>
      </div>

      <div v-if="meals.length === 0" class="card text-center py-10 text-mute">
        No meals scheduled for this day.
      </div>

      <div v-for="meal in meals" :key="meal.id as string" class="meal-section card" :class="{ 'meal-done': meal.is_done }">
        <div class="flex justify-between items-end border-b pb-4 mb-4">
          <div>
            <div class="flex items-center gap-2 no-print" style="margin-bottom: 0.5rem;">
               <div class="badge">{{ mealTypesConfig.find(m => m.val === meal.meal_type)?.label }}</div>
               <div v-if="meal.is_done" class="badge" style="background: var(--color-success); color: white;">✓ Cooked</div>
            </div>
            <h1 class="meal-title" style="margin: 0; color: var(--color-primary);">{{ getRecipe(meal.recipe)?.name }}</h1>
          </div>
          <div class="flex flex-col items-end gap-2">
            <button class="btn btn-secondary no-print" @click="toggleMealDone(meal)">
              {{ meal.is_done ? '🍳 Mark as todo' : '✅ Mark as Cooked' }}
            </button>
            <div class="text-right">
              <div style="font-size: 1.25rem; font-weight: bold;">{{ meal.override_people_count || camp?.default_people_count }} Persons</div>
              <div v-if="meal.serves_preference" style="color: var(--color-primary); font-weight: bold;">
                Target Group: {{ meal.serves_preference.name }}
              </div>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-8">
          <div>
            <h3 style="margin-bottom: 1rem; border-bottom: 2px solid var(--color-bg-mute);">Ingredients</h3>
            <ul class="ingredient-list">
              <li v-for="ri in ingredientsMap[meal.recipe]" :key="ri.id as number" class="flex justify-between py-2 border-b">
                <span style="font-weight: 500;">{{ ri.ingredient.name }}</span>
                <span class="text-mute">{{ Math.round(getScaledAmount(ri, meal) * 100) / 100 }} {{ ri.unit }}</span>
              </li>
              <li v-if="!ingredientsMap[meal.recipe]" class="text-mute italic">No ingredients found.</li>
            </ul>
          </div>
          <div>
            <h3 style="margin-bottom: 1rem; border-bottom: 2px solid var(--color-bg-mute);">Instructions</h3>
            <div class="instructions-text">
              {{ getRecipe(meal.recipe)?.instructions || 'No instructions provided.' }}
            </div>
          </div>
        </div>
      </div>
      
      <div class="only-print text-center text-mute" style="margin-top: 2rem; font-size: 0.8rem;">
        Generated by Camp Meal Planner
      </div>
    </div>
  </div>
</template>

<style scoped>
.print-container {
  max-width: 1000px;
  margin: 0 auto;
}

.meal-section {
  page-break-inside: avoid;
  margin-bottom: 2rem;
  box-shadow: none;
  border: 1px solid var(--color-border);
}

.instructions-text {
  white-space: pre-wrap;
  font-size: 0.95rem;
  line-height: 1.6;
}

.ingredient-list {
  list-style: none;
  padding: 0;
}

.grid-cols-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

@media print {
  .no-print {
    display: none !important;
  }
  .only-print {
    display: block !important;
  }
  .card {
    border: none;
    padding: 0;
  }
  body {
    background: white;
  }
}

.only-print {
  display: none;
}

.print-header {
  text-align: center;
  margin-bottom: 2rem;
}

.meal-done {
  opacity: 0.7;
  border-style: dashed;
  filter: grayscale(0.4);
}
</style>
