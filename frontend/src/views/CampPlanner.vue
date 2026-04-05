<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter, RouterLink } from 'vue-router'
import { 
  mealsApiGetCamp, 
  mealsApiListCampMeals,
  mealsApiListRecipes,
  mealsApiCreateCampMeal,
  mealsApiUpdateCampMeal,
  mealsApiDeleteCampMeal,
  mealsApiGenerateShoppingList, 
  mealsApiListCampShoppingLists,
  mealsApiDeleteShoppingList,
  mealsApiUpdateCamp,
  mealsApiListCampGeneralItems,
  mealsApiCreateCampGeneralItem,
  mealsApiDeleteCampGeneralItem,
  mealsApiToggleCampMealDone,
  mealsApiListPreferences,
  type CampSchema, 
  type CampMealSchema,
  type RecipeSchema,
  type DietaryPreferenceSchema,
  type ShoppingListOverviewSchema,
  type GeneralCampItemSchema
} from '../client'

const route = useRoute()
const router = useRouter()

const campId = route.params.id as string
const camp = ref<CampSchema | null>(null)
const meals = ref<CampMealSchema[]>([])
const selectedMeals = ref<string[]>([]) // Holds selected meal IDs
const isSidebarCollapsed = ref(false)
const recipes = ref<RecipeSchema[]>([])
const preferences = ref<DietaryPreferenceSchema[]>([])
const searchRecipeQuery = ref('')

const shoppingLists = ref<ShoppingListOverviewSchema[]>([])
const showShoppingLists = ref(false)
const loadingShoppingLists = ref(false)

const generalItems = ref<GeneralCampItemSchema[]>([])
const newItemName = ref('')
const newItemAmount = ref('')
const newItemCategory = ref('NON_FOOD')

const editingCamp = ref(false)
const editCampData = ref({ name: '', default_people_count: 0, notes: '' })

const filteredRecipes = computed(() => {
  if (!searchRecipeQuery.value) return recipes.value
  const q = searchRecipeQuery.value.toLowerCase()
  return recipes.value.filter(r => r.name.toLowerCase().includes(q))
})

const mealTypesConfig = [
  { val: "BREAKFAST", label: "Frühstück" },
  { val: "MORNING_SNACK", label: "Znüni" },
  { val: "LUNCH", label: "Mittagessen" },
  { val: "AFTERNOON_SNACK", label: "Zvieri" },
  { val: "DINNER", label: "Abendessen" },
  { val: "DESSERT", label: "Dessert" },
]

async function fetchData() {
  const { data: campData } = await mealsApiGetCamp({ path: { camp_id: campId } })
  if (campData) camp.value = campData

  await fetchGeneralItems()
  
  const { data: mealsData } = await mealsApiListCampMeals({ path: { camp_id: campId } })
  if (mealsData) {
    meals.value = mealsData
    // By default, select all for shopping
    selectedMeals.value = mealsData.map(m => m.id)
  }

  const { data: recipesData } = await mealsApiListRecipes()
  if (recipesData) recipes.value = recipesData

  const { data: prefData } = await mealsApiListPreferences()
  if (prefData) preferences.value = prefData
}

// Compute Days Array bounds between Start and End points
const campDays = computed(() => {
  if (!camp.value || !camp.value.start_date || !camp.value.end_date) return []
  const arr: string[] = []
  const start = new Date(camp.value.start_date)
  const end = new Date(camp.value.end_date)
  let current = new Date(start)
  while (current <= end) {
    arr.push(current.toISOString().split('T')[0])
    current.setDate(current.getDate() + 1)
  }
  return arr
})

const mealsGrid = computed(() => {
  // Helpers to get all meals mapping for O(1) access
  const map: Record<string, Record<string, CampMealSchema[]>> = {}
  campDays.value.forEach(d => {
    map[d] = {}
    mealTypesConfig.forEach(mt => {
      map[d][mt.val] = []
    })
  })

  meals.value.forEach(m => {
    if (map[m.date] && map[m.date][m.meal_type]) {
      map[m.date][m.meal_type].push(m)
    }
  })
  return map
})

function getRecipeName(recipeId: string) {
  return recipes.value.find(r => r.id === recipeId)?.name || 'Unknown'
}

// Drag & Drop Handlers
function startDrag(event: DragEvent, recipe: RecipeSchema) {
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'copy'
    event.dataTransfer.effectAllowed = 'copy'
    event.dataTransfer.setData('recipe_id', recipe.id as string)
  }
}

async function onDrop(event: DragEvent, date: string, mealType: string) {
  const recipeId = event.dataTransfer?.getData('recipe_id')
  if (!recipeId) return
  
  // Call API
  const { data } = await mealsApiCreateCampMeal({
    path: { camp_id: campId },
    body: {
      recipe_id: recipeId,
      meal_type: mealType,
      date: date
    }
  })

  // Append Locally
  if (data) {
    meals.value.push(data)
    selectedMeals.value.push(data.id as string)
  }
}

async function removeMeal(meal: CampMealSchema) {
  if(!confirm("Remove meal from slot?")) return
  await mealsApiDeleteCampMeal({
    path: { camp_id: campId, meal_id: meal.id as string }
  })
  meals.value = meals.value.filter(m => m.id !== meal.id)
  selectedMeals.value = selectedMeals.value.filter(id => id !== meal.id)
}

// Quick edit state for overriding logic
const editingMeal = ref<CampMealSchema | null>(null)
const editPeopleCount = ref<number | null>(null)
const editPreferenceId = ref<number | null>(null)

function openEditMeal(meal: CampMealSchema) {
  editingMeal.value = meal
  editPeopleCount.value = meal.override_people_count || null
  editPreferenceId.value = meal.serves_preference?.id || null
}

async function saveEditMeal() {
  if (!editingMeal.value) return
  const { data } = await mealsApiUpdateCampMeal({
    path: { camp_id: campId, meal_id: editingMeal.value.id as string },
    body: {
      override_people_count: editPeopleCount.value,
      serves_preference_id: editPreferenceId.value
    }
  })
  if (data) {
    const idx = meals.value.findIndex(m => m.id === editingMeal.value?.id)
    if (idx !== -1) meals.value[idx] = data
    editingMeal.value = null
  }
}

async function generateShoppingList() {
  if (selectedMeals.value.length === 0) {
    alert('Please select at least one meal.')
    return
  }
  
  const { data } = await mealsApiGenerateShoppingList({
    path: { camp_id: campId },
    body: { meal_ids: selectedMeals.value }
  })
  
  if (data) {
    router.push(`/share/${data.shared_token}`)
  }
}

async function toggleShoppingListManager() {
  showShoppingLists.value = !showShoppingLists.value
  if (showShoppingLists.value) {
    fetchShoppingLists()
  }
}

async function fetchShoppingLists() {
  loadingShoppingLists.value = true
  try {
    const { data } = await mealsApiListCampShoppingLists({ path: { camp_id: campId } })
    if (data) shoppingLists.value = data
  } finally {
    loadingShoppingLists.value = false
  }
}

async function deleteShoppingList(listId: string) {
  if (!confirm('Are you sure you want to delete this shopping list?')) return
  await mealsApiDeleteShoppingList({ path: { list_id: listId } })
  fetchShoppingLists()
}

async function addGeneralItem() {
  if (!newItemName.value || !newItemAmount.value) return
  await mealsApiCreateCampGeneralItem({
    path: { camp_id: campId },
    body: {
      name: newItemName.value,
      amount: newItemAmount.value,
      category: newItemCategory.value as 'NON_FOOD'
    }
  })
  newItemName.value = ''
  newItemAmount.value = ''
  fetchGeneralItems()
}

async function deleteGeneralItem(id: string) {
  await mealsApiDeleteCampGeneralItem({ path: { camp_id: campId, item_id: id } })
  fetchGeneralItems()
}

async function fetchGeneralItems() {
  const { data } = await mealsApiListCampGeneralItems({ path: { camp_id: campId } })
  if (data) generalItems.value = data
}

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

async function startEditCamp() {
  if (!camp.value) return
  editCampData.value = {
    name: camp.value.name,
    default_people_count: camp.value.default_people_count,
    notes: camp.value.notes || ''
  }
  editingCamp.value = true
}

async function saveEditCamp() {
  try {
    const { data } = await mealsApiUpdateCamp({
      path: { camp_id: campId },
      body: {
        name: editCampData.value.name,
        default_people_count: editCampData.value.default_people_count,
        notes: editCampData.value.notes
      }
    })
    if (data) {
      camp.value = data
      editingCamp.value = false
    }
  } catch (e) {
    console.error(e)
    alert("Error saving camp")
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

// Logic for Matrix PDF Export
// @ts-ignore
import html2pdf from 'html2pdf.js'

function exportMatrixPDF() {
  const element = document.getElementById('planner-matrix-canvas')
  if (!element) return

  // Temporarily remove overflow constraints so html2canvas captures the full width
  const originalOverflow = element.style.overflowX
  const originalMaxWidth = element.style.maxWidth
  element.style.overflowX = 'visible'
  element.style.maxWidth = 'none'

  const opt = {
    margin: 5,
    filename: `CampPlan_${camp.value?.name}.pdf`,
    image: { type: 'jpeg', quality: 0.98 },
    html2canvas: { 
      scale: 2, 
      useCORS: true, 
      scrollX: 0, 
      scrollY: 0,
      windowWidth: element.scrollWidth + 50,
      width: element.scrollWidth
    },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'landscape' }
  }
  
  html2pdf().set(opt).from(element).save().then(() => {
    // Restore original styles
    element.style.overflowX = originalOverflow
    element.style.maxWidth = originalMaxWidth
  })
}

function switchToDayDetail(day: string) {
  router.push(`/camps/${campId}/day/${day}`)
}

function getMealTypeLabel(val: string) {
  return mealTypesConfig.find(mt => mt.val === val)?.label || val
}

function getMealsForDay(day: string) {
  if (!mealsGrid.value[day]) return []
  return Object.values(mealsGrid.value[day]).flat()
}

function isDaySelected(day: string) {
  const dayMeals = getMealsForDay(day)
  if (dayMeals.length === 0) return false
  return dayMeals.every(m => selectedMeals.value.includes(m.id))
}

function isDayPartial(day: string) {
  const dayMeals = getMealsForDay(day)
  if (dayMeals.length === 0) return false
  const selectedCount = dayMeals.filter(m => selectedMeals.value.includes(m.id)).length
  return selectedCount > 0 && selectedCount < dayMeals.length
}

function toggleDay(day: string) {
  const dayMeals = getMealsForDay(day)
  const dayMealIds = dayMeals.map(m => m.id)
  const currentlySelected = isDaySelected(day)
  
  if (currentlySelected) {
    selectedMeals.value = selectedMeals.value.filter(id => !dayMealIds.includes(id))
  } else {
    const existing = selectedMeals.value.filter(id => !dayMealIds.includes(id))
    selectedMeals.value = [...existing, ...dayMealIds]
  }
}

onMounted(fetchData)
</script>

<template>
  <div v-if="camp" class="flex-col gap-4">
    <div class="flex items-center justify-between" style="margin-bottom: 1.5rem;">
      <div class="flex items-center gap-4">
        <button class="btn btn-secondary" @click="router.push('/')">&larr; Back</button>
        <h2 style="margin: 0;">Plan: {{ camp.name }}</h2>
        <button class="btn btn-secondary" v-if="camp" @click="startEditCamp" style="padding: 0.25rem 0.6rem; border: none; box-shadow: none; font-size: 0.9rem;">⚙️ Edit</button>
      </div>
      
      <div class="flex gap-2">
        <button class="btn btn-secondary no-print" @click="router.push(`/camps/${campId}/inventory`)">📦 Inventory</button>
        <button class="btn btn-secondary no-print" @click="exportMatrixPDF">📋 Export</button>
      </div>
    </div>

    <!-- Planner Matrix Area -->
    <div class="grid" :style="{ gridTemplateColumns: isSidebarCollapsed ? '60px 1fr' : '300px 1fr' }" style="gap: 1.5rem; transition: grid-template-columns 0.3s ease;">
      
      <!-- Recipes Sidebar -->
      <div class="card flex-col gap-2 sidebar" :class="{ 'sidebar-collapsed': isSidebarCollapsed }" style="position: relative; overflow: visible;">
        <button 
          class="btn btn-secondary toggle-sidebar-btn shadow-md"
          @click="isSidebarCollapsed = !isSidebarCollapsed"
          :title="isSidebarCollapsed ? 'Show Menu Pool' : 'Hide Menu Pool'"
        >
          {{ isSidebarCollapsed ? '»' : '«' }}
        </button>

        <div v-show="!isSidebarCollapsed" class="flex-col gap-2">
          <h3>Menu Pool</h3>
          <p class="text-mute" style="font-size: 0.9rem;">Drag a recipe into the timetable.</p>
          
          <input type="text" class="input" v-model="searchRecipeQuery" placeholder="Search menus..." style="font-size: 0.9rem; padding: 0.4rem; margin-bottom: 0.5rem;" />
  
          <div style="overflow-y: auto; max-height: calc(100vh - 250px); padding-right: 0.5rem;" class="flex-col gap-2">
            <div 
              v-for="recipe in filteredRecipes" 
              :key="recipe.id as string" 
              class="recipe-draggable"
              draggable="true"
              @dragstart="startDrag($event, recipe)"
            >
              <div class="flex justify-between items-start" style="gap: 0.5rem;">
                <strong style="white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" :title="recipe.name">{{ recipe.name }}</strong>
                <span class="text-mute" style="font-size: 0.75rem; flex-shrink: 0;">{{ recipe.default_portions }}p</span>
              </div>
              <div class="flex gap-1 flex-wrap" style="margin-top: 0.25rem;" v-if="recipe.preferences && recipe.preferences.length > 0">
                <span v-for="pref in recipe.preferences" :key="pref.id" class="badge-tiny">
                  {{ pref.name }}
                </span>
              </div>
            </div>
          </div>
        </div>
        <div v-show="isSidebarCollapsed" class="flex-col items-center justify-center h-full">
           <div style="writing-mode: vertical-rl; transform: rotate(180deg); opacity: 0.5; font-weight: bold; font-size: 0.8rem; margin-top: 2rem;">
             MENU POOL
           </div>
        </div>
      </div>

      <!-- Matrix Canvas -->
      <div id="planner-matrix-canvas" class="card matrix-container" style="overflow-x: auto;">
        <h3 class="only-print" style="margin-bottom: 1rem; display: none;">{{ camp.name }} - Matrix Plan</h3>
        <table class="planner-table">
          <thead>
            <tr>
              <th class="sticky-col">Time</th>
              <th v-for="day in campDays" :key="day" style="min-width: 150px; text-align: center;">
                <div class="flex-col items-center gap-1 group cursor-pointer" @click="switchToDayDetail(day)">
                  <div style="font-size: 1rem; margin-bottom: 0.2rem; font-weight: normal;" class="group-hover:text-primary day-header">
                    {{ new Date(day).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' }) }}
                  </div>
                  <label v-if="getMealsForDay(day).length > 0" class="flex items-center gap-1" style="font-weight: normal; font-size: 0.75rem; cursor: pointer;" @click.stop>
                    <input 
                      type="checkbox" 
                      :checked="isDaySelected(day)" 
                      :indeterminate="isDayPartial(day)"
                      @change="toggleDay(day)"
                    />
                    Select Day
                  </label>
                  <span v-else class="text-mute" style="font-size: 0.7rem; font-weight: normal;">No meals</span>
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
                @drop="onDrop($event, day, mt.val)"
              >
                <!-- Render Assigned Meals -->
                <div 
                  v-for="meal in (mealsGrid[day] && mealsGrid[day][mt.val] ? mealsGrid[day][mt.val] : [])" 
                  :key="meal.id as string" 
                  class="allocated-meal flex-col"
                  :class="{ 'meal-done': meal.is_done }"
                  style="cursor: pointer;"
                  @click="openEditMeal(meal)"
                >
                  <div class="flex justify-between items-center w-full">
                    <label class="flex items-center gap-1" style="font-size: 0.85rem; padding: 2px;" @click.stop>
                      <input type="checkbox" :value="meal.id" v-model="selectedMeals" style="width: 12px; height: 12px;" />
                      <span style="overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 80px;" :title="getRecipeName(meal.recipe as string)">
                        {{ getRecipeName(meal.recipe as string) }}
                      </span>
                    </label>
                    <div class="flex items-center gap-1">
                      <button 
                        class="btn-icon" 
                        style="font-size: 0.7rem; padding: 0 2px;"
                        @click.stop="toggleMealDone(meal)"
                        :title="meal.is_done ? 'Mark as Not Cooked' : 'Mark as Cooked'"
                      >
                        {{ meal.is_done ? '✅' : '🍳' }}
                      </button>
                      <button class="remove-btn" @click.stop="removeMeal(meal)">✕</button>
                    </div>
                  </div>
                  
                  <div class="flex justify-between items-center text-mute" style="font-size: 0.7rem; margin-top: 2px; padding-left: 18px;">
                    <span v-if="meal.override_people_count !== null">{{ meal.override_people_count }} people</span>
                    <span v-else>{{ camp.default_people_count }} people</span>
                    
                    <span v-if="meal.serves_preference" style="color: var(--color-primary); font-weight: bold;">
                      ({{ meal.serves_preference.name }})
                    </span>
                  </div>
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
    </div>

    <!-- Shopping Generate Action -->
    <div class="card flex justify-between items-center" style="margin-top: 1rem;">
      <p style="margin: 0;"><strong>Shopping Planner:</strong> Only the {{ selectedMeals.length }} checked menus will be aggregated.</p>
      <div class="flex gap-2">
        <button class="btn btn-secondary" @click="toggleShoppingListManager">🛍️ {{ showShoppingLists ? 'Hide' : 'Manage' }} Lists</button>
        <button class="btn btn-primary" @click="generateShoppingList">🛒 Generate New</button>
      </div>
    </div>

    <!-- Camp Notes & General Items Container -->
    <div class="grid" style="grid-template-columns: 1fr 1fr; gap: 1rem; margin-top: 1rem;">
      <!-- Camp Notes Inline Display -->
      <div class="card" style="border: 1px solid var(--color-border); background: var(--color-bg-base);">
        <div class="flex justify-between items-center" style="margin-bottom: 1rem;">
          <h3 style="margin: 0;">Camp Notes</h3>
          <button class="btn btn-secondary" style="font-size: 0.8rem; padding: 0.25rem 0.5rem;" @click="startEditCamp">Edit</button>
        </div>
        <div class="text-mute" style="white-space: pre-wrap; font-size: 0.9rem; margin: 0; line-height: 1.5;">{{ camp?.notes || 'No special notes or information for this camp yet. Click edit to add.' }}</div>
      </div>
      
      <!-- General Camp Items -->
      <div class="card" style="border: 1px solid var(--color-border); background: var(--color-bg-base);">
        <div style="margin-bottom: 1rem;">
          <h3 style="margin: 0;">General Shopping Items</h3>
          <p class="text-mute" style="font-size: 0.8rem; margin: 0.2rem 0 0 0;">Non-food items or special products.</p>
        </div>
        
        <div class="flex gap-2" style="margin-top: 0.5rem;">
          <input type="text" v-model="newItemName" placeholder="e.g. Abfallkübel" class="input" style="padding: 0.4rem; font-size: 0.85rem;" />
          <input type="text" v-model="newItemAmount" placeholder="e.g. 5x" class="input" style="width: 80px; padding: 0.4rem; font-size: 0.85rem;" />
          <button class="btn btn-primary" @click="addGeneralItem" style="padding: 0.4rem 0.8rem;">Add</button>
        </div>
        
        <ul style="margin-top: 1rem; padding-left: 0; list-style: none; display: flex; flex-direction: column; gap: 0.5rem; max-height: 120px; overflow-y: auto;">
          <li v-for="item in generalItems" :key="item.id as string" class="flex justify-between items-center border border-border" style="padding: 0.4rem 0.5rem; border-radius: 4px; background: var(--color-bg-surface); font-size: 0.85rem;">
            <span>{{ item.amount }} {{ item.name }}</span>
            <button class="text-mute" @click="deleteGeneralItem(item.id as string)" style="cursor: pointer; background: none; border: none; font-size: 0.8rem;">✕</button>
          </li>
          <li v-if="generalItems.length === 0" class="text-mute text-center" style="font-size: 0.85rem;">No items added yet.</li>
        </ul>
      </div>
    </div>

    <!-- Edit Camp Modal -->
    <div v-if="editingCamp" class="modal-backdrop" @click="editingCamp = false">
      <div class="modal" @click.stop style="width: 100%; max-width: 500px;">
        <h3>Edit Camp Settings</h3>
        
        <div class="flex-col gap-4" style="margin-top: 1rem;">
          <div>
            <label>Camp Name</label>
            <input type="text" class="input" v-model="editCampData.name" />
          </div>
          <div>
            <label>Default People Count</label>
            <input type="number" class="input" v-model="editCampData.default_people_count" />
          </div>
          <div>
            <label>Notes & Special Information</label>
            <textarea class="input" v-model="editCampData.notes" rows="6" placeholder="Special requirements, events, or reminders..."></textarea>
          </div>
          
          <div class="flex justify-end gap-2" style="margin-top: 1rem;">
            <button class="btn btn-secondary" @click="editingCamp = false">Cancel</button>
            <button class="btn btn-primary" @click="saveEditCamp">Save Camp</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Meal Modal -->
    <div v-if="editingMeal" class="modal-backdrop" @click="editingMeal = null">
      <div class="modal" @click.stop>
        <h3>Edit Assigned Meal</h3>
        <p class="text-mute">Specify participant overrides or subgroups for {{ getRecipeName(editingMeal.recipe as string) }}</p>
        
        <div class="flex-col gap-4" style="margin-top: 1rem;">
          <div>
            <label>Override People Count (Optional)</label>
            <input type="number" class="input" v-model="editPeopleCount" placeholder="Default from camp settings" />
          </div>
          <div>
            <label>Meal Target Subgroup (Optional)</label>
            <select class="input" v-model="editPreferenceId">
              <option :value="null">-- For Main Group --</option>
              <option v-for="pref in preferences" :key="pref.id" :value="pref.id">{{ pref.name }}</option>
            </select>
          </div>
          <div class="flex justify-end gap-2" style="margin-top: 1rem;">
            <button class="btn btn-secondary" @click="editingMeal = null">Cancel</button>
            <button class="btn btn-primary" @click="saveEditMeal">Save Variables</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Inline Shopping Lists Manager -->
    <div v-show="showShoppingLists" class="card" style="margin-top: 1rem; border: 1px solid var(--color-border); background: var(--color-bg-base);">
      <div class="flex justify-between items-center" style="margin-bottom: 1rem;">
        <h3 style="margin: 0;">Shopping Lists</h3>
      </div>
      
      <div v-if="loadingShoppingLists" class="text-center py-4 text-mute">Loading lists...</div>
      
      <div v-else-if="shoppingLists.length === 0" class="text-center py-4 text-mute" style="margin-top: 1rem;">
        No shopping lists generated yet.
      </div>
      
      <div v-else class="flex-col gap-4">
        <div v-for="sl in shoppingLists" :key="sl.id as string" class="card border flex-col gap-2 shadow-sm" style="padding: 1rem; border-color: var(--color-border); background: var(--color-bg-surface);">
          <div class="flex justify-between items-start">
            <strong style="color: var(--color-primary); font-size: 1.1rem;">List from {{ new Date(sl.created_at).toLocaleString([], { dateStyle: 'short', timeStyle: 'short' }) }}</strong>
            <div class="flex gap-2">
              <button class="btn btn-secondary" style="font-size: 0.8rem; padding: 0.25rem 0.6rem;" @click="router.push(`/share/${sl.shared_token}`)">Open</button>
              <button class="btn" style="font-size: 0.8rem; padding: 0.25rem 0.6rem; color: var(--color-danger); border: 1px solid var(--color-danger);" @click="deleteShoppingList(sl.id as string)">Delete</button>
            </div>
          </div>
          
          <div style="margin-top: 1rem;">
            <strong style="font-size: 0.9rem; border-bottom: 1px solid var(--color-border); padding-bottom: 0.25rem; display: block; margin-bottom: 0.5rem;">Included Meals ({{ sl.included_meals.length }})</strong>
            
            <div class="meal-groups-grid" v-if="sl.included_meals.length > 0">
              <div v-for="(meals, day) in groupMealsByDay(sl.included_meals)" :key="day">
                <div style="font-size: 0.8rem; font-weight: bold; color: var(--color-primary); margin-bottom: 0.2rem;">{{ day }}</div>
                <div v-for="(m, i) in meals" :key="i" style="font-size: 0.8rem; color: var(--color-text-mute); line-height: 1.3; margin-bottom: 0.2rem; display: flex; gap: 0.25rem;">
                   <span>{{ m.split(':')[1] }}</span>
                </div>
              </div>
            </div>
            
            <div v-else class="text-mute" style="font-size: 0.85rem;">
              No meals attached
            </div>
          </div>
        </div>
      </div>
    </div>

  </div>
  <div v-else>
    Loading camp planning...
  </div>
</template>

<style scoped>
.sidebar {
  background: var(--color-bg-mute); 
  border: 1px solid var(--color-border);
}

.recipe-draggable {
  padding: 0.75rem; 
  background: var(--color-surface); 
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

.matrix-container {
  padding: 0;
  border: 1px solid var(--color-border);
  background: var(--color-bg-surface);
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

.sticky-col {
  position: sticky;
  left: 0;
  background: var(--color-bg-mute);
  font-weight: bold;
  z-index: 3;
}

.label-cell {
  background: var(--color-surface);
  box-shadow: 2px 0 5px rgba(0,0,0,0.05); /* Slight shadow to separate from scrollable row */
  display: flex;
  align-items: center;
  min-height: 80px;
}

.droppable-cell {
  background: var(--color-surface);
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

.allocated-meal {
  background: var(--color-bg-mute);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 0.25rem 0.5rem;
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.02);
}

.allocated-meal:last-child {
  margin-bottom: 0;
}

.remove-btn {
  background: transparent;
  border: none;
  font-size: 0.8rem;
  color: var(--color-danger);
  cursor: pointer;
  opacity: 0.5;
  transition: opacity 0.2s;
}

.remove-btn:hover {
  opacity: 1;
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
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  background: var(--color-bg-surface);
  box-shadow: var(--shadow-md);
  border: 1px solid var(--color-border);
}

.badge-tiny {
  font-size: 0.65rem; 
  background: var(--color-primary-light); 
  color: var(--color-primary-hover); 
  padding: 1px 4px; 
  border-radius: 3px;
}

.sidebar-collapsed {
  padding: 1rem 0.5rem !important;
}

.day-header {
  cursor: pointer;
}

.day-header:hover {
  text-decoration: underline; 
}

.meal-done {
  opacity: 0.6;
  background: var(--color-bg-mute) !important;
  filter: grayscale(0.5);
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px;
  font-size: 0.9rem;
  border-radius: 4px;
  transition: background 0.2s;
}

.btn-icon:hover {
  background: var(--color-bg-mute);
}

.meal-groups-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 1rem;
}

@media (min-width: 768px) {
  .meal-groups-grid {
    grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  }
}
</style>
