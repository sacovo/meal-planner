<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  mealsApiListPreferences,
  mealsApiGetCamp,
  mealsApiListCampMeals,
  mealsApiListCampGeneralItems,
  mealsApiUpdateCamp,
  mealsApiListCampShoppingLists,
  mealsApiToggleCampMealDone,
  mealsApiCreateCampMeal,
  mealsApiUpdateCampMeal,
  mealsApiDeleteCampMeal,
  mealsApiCreateCampGeneralItem,
  mealsApiDeleteCampGeneralItem,
  mealsApiGenerateShoppingList,
  mealsApiDeleteShoppingList,
  mealsApiInviteCollaborator,
  mealsApiRemoveCollaborator,
  mealsApiMoveGeneralItemsToShoppingList,
  mealsApiListTags,
  coreApiAccount,
  type CampSchema,
  type CampMealSchema,
  type RecipeSchema,
  type GeneralCampItemSchema,
  type DietaryPreferenceSchema,
  type ShoppingListOverviewSchema,
} from '../client'
// @ts-ignore
import html2pdf from 'html2pdf.js'
import CampNotes from '../components/CampNotes.vue'
import GeneralItems from '../components/GeneralItems.vue'
import RecipeSidebar from '../components/RecipeSidebar.vue'
import PlannerMatrix from '../components/PlannerMatrix.vue'
import ShoppingListManager from '../components/ShoppingListManager.vue'
import EditCampModal from '../components/EditCampModal.vue'
import EditMealModal from '../components/EditMealModal.vue'
import CollaboratorsModal from '../components/CollaboratorsModal.vue'
import { useI18n } from '../composables/useI18n'

const route = useRoute()
const router = useRouter()

const { t } = useI18n()

const campId = route.params.id as string
const camp = ref<CampSchema | null>(null)
const meals = ref<CampMealSchema[]>([])
const selectedMeals = ref<string[]>([]) // Holds selected meal IDs
const isSidebarCollapsed = ref(false)
const preferences = ref<DietaryPreferenceSchema[]>([])
const searchRecipeQuery = ref('')
const allTags = ref<string[]>([])

const shoppingLists = ref<ShoppingListOverviewSchema[]>([])
const showShoppingLists = ref(false)
const loadingShoppingLists = ref(false)

const generalItems = ref<GeneralCampItemSchema[]>([])
const isMovingGeneralItems = ref(false)
const latestShoppingListId = computed(() => shoppingLists.value[0]?.id as string | undefined)

const currentUser = ref<{ is_logged_in?: boolean, username?: string | null }>({ is_logged_in: false })

const editingCamp = ref(false)
const showCollaboratorsModal = ref(false)
const editCampData = ref({ name: '', default_people_count: 0, notes: '' })



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
    selectedMeals.value = mealsData.map(m => m.id!).filter(id => !!id)
  }

  const { data: prefData } = await mealsApiListPreferences()
  if (prefData) preferences.value = prefData

  const { data: tagsData } = await mealsApiListTags()
  if (tagsData) allTags.value = tagsData

  // Fetch current user
  try {
    const { data: userData } = await coreApiAccount()
    if (userData) {
      currentUser.value = {
        is_logged_in: !!userData.username,
        username: userData.username
      }
    }
  } catch (e) {
    console.error("Auth check failed", e)
  }

  // Pre-fetch shopping lists so they are available for general items move
  await fetchShoppingLists()
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

const recipeNames = computed(() => {
  const map: Record<string, string> = {}
  meals.value.forEach(m => {
    if (m.recipe) map[m.recipe] = m.recipe_name || ''
  })
  return map
})

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
  if (!confirm(t('planner.remove_meal_from_slot'))) return
  await mealsApiDeleteCampMeal({
    path: { camp_id: campId, meal_id: meal.id as string }
  })
  meals.value = meals.value.filter(m => m.id !== meal.id)
  selectedMeals.value = selectedMeals.value.filter(id => id !== meal.id)
}

// Quick edit state for overriding logic
const editingMeal = ref<CampMealSchema | null>(null)

function openEditMeal(meal: CampMealSchema) {
  editingMeal.value = meal
}

async function saveEditMeal(data: { overridePeopleCount: number | null, preferenceId: number | null }) {
  if (!editingMeal.value) return
  const { data: updatedMeal } = await mealsApiUpdateCampMeal({
    path: { camp_id: campId, meal_id: editingMeal.value.id as string },
    body: {
      override_people_count: data.overridePeopleCount,
      serves_preference_id: data.preferenceId
    }
  })
  if (updatedMeal) {
    const idx = meals.value.findIndex(m => m.id === editingMeal.value?.id)
    if (idx !== -1) meals.value[idx] = updatedMeal
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

watch(showShoppingLists, (newVal) => {
  if (newVal) {
    fetchShoppingLists()
  }
})

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

async function addGeneralItem(item: { name: string, amount: string }) {
  await mealsApiCreateCampGeneralItem({
    path: { camp_id: campId },
    body: {
      name: item.name,
      amount: item.amount,
      category: 'NON_FOOD'
    }
  })
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

async function handleMoveGeneralItems() {
  if (!latestShoppingListId.value) {
    alert("Please create a shopping list first.")
    return
  }
  if (!confirm("Move all general items to the most recent shopping list? They will be removed from this list.")) return

  isMovingGeneralItems.value = true
  try {
    await mealsApiMoveGeneralItemsToShoppingList({
      path: {
        camp_id: campId,
        list_id: latestShoppingListId.value
      }
    })
    await fetchGeneralItems()
    await fetchShoppingLists()
  } catch (e) {
    console.error(e)
    alert("Failed to move items")
  } finally {
    isMovingGeneralItems.value = false
  }
}

async function saveEditCamp(data: { name: string, default_people_count: number, notes: string }) {
  try {
    const { data: updatedCamp } = await mealsApiUpdateCamp({
      path: { camp_id: campId },
      body: {
        name: data.name,
        default_people_count: data.default_people_count,
        notes: data.notes
      }
    })
    if (updatedCamp) {
      camp.value = updatedCamp
      editingCamp.value = false
    }
  } catch (e) {
    console.error(e)
    alert("Error saving camp")
  }
}

function handleOpenShoppingList(token: string) {
  router.push(`/share/${token}`)
}

async function inviteCollaborator(username: string) {
  try {
    const { data } = await mealsApiInviteCollaborator({
      path: { camp_id: campId },
      body: { username }
    })
    if (data && camp.value) {
      camp.value.collaborators = data.collaborators
    }
  } catch (e: any) {
    alert(e.response?.data?.detail || "Failed to invite user. Check if username exists.")
  }
}

async function removeCollaborator(username: string) {
  const confirmMsg = username === currentUser.value.username ? "Are you sure you want to leave this camp?" : `Remove ${username} from camp?`
  if (!confirm(confirmMsg)) return

  try {
    await mealsApiRemoveCollaborator({
      path: { camp_id: campId, username }
    })
    if (camp.value && camp.value.collaborators) {
      camp.value.collaborators = camp.value.collaborators.filter((u: string) => u !== username)
    }
    if (username === currentUser.value.username) {
      router.push('/')
    }
  } catch (e: any) {
    alert("Failed to remove user.")
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
    image: { type: 'jpeg' as const, quality: 0.98 },
    html2canvas: {
      scale: 2,
      useCORS: true,
      scrollX: 0,
      scrollY: 0,
      windowWidth: element.scrollWidth + 50,
      width: element.scrollWidth
    },
    jsPDF: { unit: 'mm', format: 'a4', orientation: 'landscape' }
  } as const

  html2pdf().set(opt).from(element).save().then(() => {
    // Restore original styles
    element.style.overflowX = originalOverflow
    element.style.maxWidth = originalMaxWidth
  })
}

function switchToDayDetail(day: string) {
  router.push(`/camps/${campId}/day/${day}`)
}

// Unused but kept for reference or removed if strictly needed
// function getMealTypeLabel(val: string) {
//   return mealTypesConfig.find(mt => mt.val === val)?.label || val
// }

function getMealsForDay(day: string) {
  if (!mealsGrid.value[day]) return []
  return Object.values(mealsGrid.value[day]).flat()
}

function isDaySelected(day: string) {
  const dayMeals = getMealsForDay(day)
  if (dayMeals.length === 0) return false
  return dayMeals.every(m => selectedMeals.value.includes(m.id!))
}

// function isDayPartial(day: string) {
//   const dayMeals = getMealsForDay(day)
//   if (dayMeals.length === 0) return false
//   const selectedCount = dayMeals.filter(m => selectedMeals.value.includes(m.id!)).length
//   return selectedCount > 0 && selectedCount < dayMeals.length
// }

function toggleDay(day: string) {
  const dayMeals = getMealsForDay(day)
  const dayMealIds = dayMeals.map(m => m.id!).filter(id => !!id)
  const currentlySelected = isDaySelected(day)

  if (currentlySelected) {
    selectedMeals.value = selectedMeals.value.filter(id => !dayMealIds.includes(id))
  } else {
    const existing = selectedMeals.value.filter(id => !dayMealIds.includes(id))
    selectedMeals.value = [...existing, ...dayMealIds]
  }
}

watch(() => camp.value, (newCamp) => {
  if (newCamp) {
    editCampData.value = {
      name: newCamp.name,
      default_people_count: newCamp.default_people_count || 0,
      notes: newCamp.notes || ''
    }
  }
}, { immediate: true })

onMounted(fetchData)
</script>

<template>
  <div v-if="camp" class="flex-col gap-4">
    <div class="flex items-center justify-between" style="margin-bottom: 1.5rem;">
      <div class="flex items-center gap-4">
        <button class="btn btn-secondary" @click="router.push('/')">&larr; {{ t('back') }}</button>
        <h2 style="margin: 0;">{{ t('plan') }} {{ camp.name }}</h2>
        <button class="btn btn-secondary" v-if="camp" @click="editingCamp = true"
          style="padding: 0.25rem 0.6rem; border: none; box-shadow: none; font-size: 0.9rem;">⚙️ {{ t('edit')
          }}</button>
      </div>

      <div class="flex gap-2">
        <button class="btn btn-secondary no-print" @click="showCollaboratorsModal = true">👥 {{ t('collaborators.title')
          }}</button>
        <button class="btn btn-secondary no-print" @click="router.push(`/camps/${campId}/inventory`)">📦 {{
          t('inventory.title') }}</button>
        <button class="btn btn-secondary no-print" @click="exportMatrixPDF">📋 {{ t('export') }}</button>
      </div>
    </div>

    <!-- Planner Matrix Area -->
    <div class="grid" :style="{ gridTemplateColumns: isSidebarCollapsed ? '60px 1fr' : '300px 1fr' }"
      style="gap: 1.5rem; transition: grid-template-columns 0.3s ease;">

      <!-- Recipes Sidebar -->
      <RecipeSidebar :preferences="preferences" :all-tags="allTags" v-model:searchQuery="searchRecipeQuery"
        v-model:isCollapsed="isSidebarCollapsed" @dragstart="startDrag" />

      <!-- Matrix Canvas -->
      <PlannerMatrix :camp="camp" :camp-days="campDays" :meal-types-config="mealTypesConfig" :meals-grid="mealsGrid"
        v-model:selected-meals="selectedMeals" :recipe-names="recipeNames" @drop="onDrop" @edit-meal="openEditMeal"
        @toggle-done="toggleMealDone" @remove-meal="removeMeal" @switch-day="switchToDayDetail"
        @toggle-day="toggleDay" />
    </div>

    <ShoppingListManager :selected-meals-count="selectedMeals.length" v-model:showShoppingLists="showShoppingLists"
      :shopping-lists="shoppingLists" :loading="loadingShoppingLists" @generate="generateShoppingList"
      @delete="deleteShoppingList" @open="handleOpenShoppingList" />

    <div class="grid bottom-grid">
      <div class="flex-col gap-4">
        <CampNotes :notes="camp?.notes" @edit="editingCamp = true" />
      </div>
      <GeneralItems :items="generalItems" :can-move="!!latestShoppingListId" :is-moving="isMovingGeneralItems"
        @add="addGeneralItem" @delete="deleteGeneralItem" @move="handleMoveGeneralItems" />
    </div>

    <!-- Modals -->
    <EditCampModal v-model:show="editingCamp" :camp-data="editCampData" @save="saveEditCamp" />

    <EditMealModal :show="!!editingMeal" @update:show="editingMeal = $event ? editingMeal : null" :meal="editingMeal"
      :preferences="preferences" :recipe-name="editingMeal ? recipeNames[editingMeal.recipe as string] : ''"
      @save="saveEditMeal" />

    <CollaboratorsModal v-if="camp" v-model:show="showCollaboratorsModal" :collaborators="camp.collaborators || []"
      :owner-username="camp.owner_username || ''" :current-user-username="currentUser.username || ''"
      @invite="inviteCollaborator" @remove="removeCollaborator" />

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

.bottom-grid {
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 1rem;
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
