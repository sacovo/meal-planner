<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  mealsApiCampsGetCamp,
  mealsApiMealsListCampMeals,
  mealsApiRecipesListRecipes,
  mealsApiRecipesListRecipeIngredients,
  mealsApiMealsToggleCampMealDone,
  type CampSchema,
  type CampMealSchema,
  type RecipeSchema,
  type RecipeIngredientSchema
} from '../client'
import MarkdownView from '../components/MarkdownView.vue'
import { getMealTypeLabel } from '../composables/useMealTypes'
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

async function fetchData() {
  loading.value = true
  try {
    const { data: campData } = await mealsApiCampsGetCamp({ path: { camp_id: campId } })
    if (campData) camp.value = campData

    const { data: allMeals } = await mealsApiMealsListCampMeals({ path: { camp_id: campId } })
    if (allMeals) {
      meals.value = allMeals.filter(m => m.date === dateStr)
    }

    const { data: allRecipes } = await mealsApiRecipesListRecipes()
    if (allRecipes) recipes.value = allRecipes.items

    for (const meal of meals.value) {
      if (!ingredientsMap.value[meal.recipe]) {
        const { data: ingData } = await mealsApiRecipesListRecipeIngredients({ path: { recipe_id: meal.recipe } })
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
    const { data } = await mealsApiMealsToggleCampMealDone({
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
  if (!people) return ri.amount
  return (ri.amount * people) / recipe.default_portions
}

function exportPDF() {
  const element = document.getElementById('printable-content')
  if (!element) return

  const opt = {
    margin: 10,
    filename: `DayPlan_${dateStr}.pdf`,
    image: { type: 'jpeg' as const, quality: 0.98 },
    html2canvas: { scale: 2 },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
  } as const
  html2pdf().set(opt).from(element).save()
}

onMounted(fetchData)
</script>

<template>
  <div class="container page-container">
    <div class="page-header no-print mb-8">
      <div class="flex items-center gap-4">
        <button class="btn btn-secondary" @click="router.push(`/camps/${campId}`)">&larr; Back to Plan</button>
        <h2 v-if="camp" class="page-title">{{ camp.name }} - {{ new Date(dateStr).toLocaleDateString(undefined, {
          weekday: 'long', day:
            'numeric', month: 'long'
        }) }}</h2>
      </div>
      <div class="flex gap-2">
        <button class="btn btn-primary" @click="exportPDF">🖨 Export PDF / Print</button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-8">
      <div class="text-mute">Loading daily details...</div>
    </div>

    <div v-else id="printable-content" class="flex-col gap-8 print-container">
      <div class="print-header only-print">
        <h1>{{ camp?.name }}</h1>
        <h2>{{ new Date(dateStr).toLocaleDateString(undefined, {
          weekday: 'long', day: 'numeric', month: 'long', year:
            'numeric'
        }) }}</h2>
      </div>

      <div v-if="meals.length === 0" class="card text-center py-8 text-mute">
        No meals scheduled for this day.
      </div>

      <div v-for="meal in meals" :key="meal.id as string" class="meal-section card"
        :class="{ 'meal-done': meal.is_done }">
        <div class="flex justify-between items-end meal-header">
          <div>
            <div class="flex items-center gap-2 no-print mb-2">
              <div class="badge">{{getMealTypeLabel(meal.meal_type)}}</div>
              <div v-if="meal.is_done" class="badge badge-success">✓ Cooked</div>
            </div>
            <h1 class="meal-title">{{ getRecipe(meal.recipe)?.name }}</h1>
          </div>
          <div class="flex flex-col items-end gap-2">
            <button class="btn btn-secondary no-print" @click="toggleMealDone(meal)">
              {{ meal.is_done ? '🍳 Mark as todo' : '✅ Mark as Cooked' }}
            </button>
            <div class="text-right">
              <div class="meal-people-count">{{ meal.override_people_count ||
                camp?.default_people_count }} Persons</div>
              <div v-if="meal.serves_preference" class="meal-preference">
                Target Group: {{ meal.serves_preference.name }}
              </div>
            </div>
          </div>
        </div>

        <div class="grid grid-cols-2 gap-8">
          <div>
            <h3 class="section-heading">Ingredients</h3>
            <ul class="list-reset">
              <li v-for="ri in ingredientsMap[meal.recipe]" :key="ri.id as number"
                class="flex justify-between py-2 ingredient-row">
                <span class="font-bold">{{ ri.ingredient.name }}</span>
                <span class="text-mute">{{ Math.round(getScaledAmount(ri, meal) * 100) / 100 }} {{ ri.unit }}</span>
              </li>
              <li v-if="!ingredientsMap[meal.recipe]" class="text-mute">No ingredients found.</li>
            </ul>
          </div>
          <div>
            <h3 class="section-heading">Instructions</h3>
            <div class="instructions-text">
              <MarkdownView v-if="getRecipe(meal.recipe)?.instructions"
                :content="getRecipe(meal.recipe)?.instructions" />
              <div v-else class="text-mute">No instructions provided.</div>
            </div>
          </div>
        </div>
      </div>

      <div class="only-print text-center text-mute mt-8 text-xs">
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

.meal-header {
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 1rem;
  margin-bottom: 1rem;
}

.meal-title {
  margin: 0;
  color: var(--color-primary);
}

.meal-people-count {
  font-size: 1.25rem;
  font-weight: bold;
}

.meal-preference {
  color: var(--color-primary);
  font-weight: bold;
}

.badge-success {
  background: var(--color-success);
  color: white;
}

.section-heading {
  margin-bottom: 1rem;
  border-bottom: 2px solid var(--color-bg-mute);
}

.ingredient-row {
  border-bottom: 1px solid var(--color-bg-mute);
}

.instructions-text {
  font-size: 0.95rem;
  line-height: 1.6;
}

.grid-cols-2 {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
}

.py-2 {
  padding-top: 0.5rem;
  padding-bottom: 0.5rem;
}

.meal-done {
  opacity: 0.7;
  border-style: dashed;
  filter: grayscale(0.4);
}

.print-header {
  text-align: center;
  margin-bottom: 2rem;
}

@media print {
  .card {
    border: none;
    padding: 0;
  }

  body {
    background: white;
  }
}
</style>
