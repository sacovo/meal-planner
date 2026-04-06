import { ref, computed, watch } from 'vue'
import {
  mealsApiCampsGetCamp,
  mealsApiMealsListCampMeals,
  mealsApiMealsCreateCampMeal,
  mealsApiMealsUpdateCampMeal,
  mealsApiMealsDeleteCampMeal,
  mealsApiMealsToggleCampMealDone,
  mealsApiCampsUpdateCamp,
  mealsApiCampsInviteCollaborator,
  mealsApiCampsRemoveCollaborator,
  mealsApiCampsListCampGeneralItems,
  mealsApiCampsCreateCampGeneralItem,
  mealsApiCampsDeleteCampGeneralItem,
  mealsApiShoppingListCampShoppingLists,
  mealsApiShoppingGenerateShoppingList,
  mealsApiShoppingDeleteShoppingList,
  mealsApiShoppingMoveGeneralItemsToShoppingList,
  mealsApiRecipesListPreferences,
  mealsApiIngredientsListTags,
  coreApiAccount,
  type CampSchema,
  type CampMealSchema,
  type DietaryPreferenceSchema,
  type GeneralCampItemSchema,
  type ShoppingListOverviewSchema,
} from '../client'
import { MEAL_TYPES } from './useMealTypes'
import { useI18n } from './useI18n'

/**
 * Controller logic for the Camp Planner view.
 * Manages camp data, meals grid, shopping lists, general items, and collaborators.
 */
export function useCampPlanner(campId: string) {
  // ---- Core state ----
  const camp = ref<CampSchema | null>(null)
  const meals = ref<CampMealSchema[]>([])
  const selectedMeals = ref<string[]>([])
  const preferences = ref<DietaryPreferenceSchema[]>([])
  const allTags = ref<string[]>([])
  const currentUser = ref<{ is_logged_in?: boolean; username?: string | null }>({ is_logged_in: false })

  // ---- Translation ----
  const { t } = useI18n()

  // ---- Shopping lists ----
  const shoppingLists = ref<ShoppingListOverviewSchema[]>([])
  const showShoppingLists = ref(false)
  const loadingShoppingLists = ref(false)

  // ---- General items ----
  const generalItems = ref<GeneralCampItemSchema[]>([])
  const isMovingGeneralItems = ref(false)
  const latestShoppingListId = computed(() => shoppingLists.value[0]?.id as string | undefined)

  // ---- Camp editing ----
  const editingCamp = ref(false)
  const editCampData = ref({ name: '', default_people_count: 0, notes: '' })

  // ---- Computed: day array ----
  const campDays = computed(() => {
    if (!camp.value || !camp.value.start_date || !camp.value.end_date) return []
    const arr: string[] = []
    const start = new Date(camp.value.start_date)
    const end = new Date(camp.value.end_date)
    const current = new Date(start)
    while (current <= end) {
      arr.push(current.toISOString().split('T')[0])
      current.setDate(current.getDate() + 1)
    }
    return arr
  })

  // ---- Computed: meals grid (day × meal_type) ----
  const mealsGrid = computed(() => {
    const map: Record<string, Record<string, CampMealSchema[]>> = {}
    campDays.value.forEach((d) => {
      map[d] = {}
      MEAL_TYPES.forEach((mt: { val: string; label: string }) => {
        map[d][mt.val] = []
      })
    })
    meals.value.forEach((m) => {
      if (map[m.date] && map[m.date][m.meal_type]) {
        map[m.date][m.meal_type].push(m)
      }
    })
    return map
  })

  const recipeNames = computed(() => {
    const map: Record<string, string> = {}
    meals.value.forEach((m) => {
      if (m.recipe) map[m.recipe] = m.recipe_name || ''
    })
    return map
  })

  // ---- Data fetching ----
  async function fetchData() {
    const { data: campData } = await mealsApiCampsGetCamp({ path: { camp_id: campId } })
    if (campData) camp.value = campData

    await fetchGeneralItems()

    const { data: mealsData } = await mealsApiMealsListCampMeals({ path: { camp_id: campId } })
    if (mealsData) {
      meals.value = mealsData
      selectedMeals.value = mealsData.map((m) => m.id!).filter((id) => !!id)
    }

    const { data: prefData } = await mealsApiRecipesListPreferences()
    if (prefData) preferences.value = prefData

    const { data: tagsData } = await mealsApiIngredientsListTags()
    if (tagsData) allTags.value = tagsData

    try {
      const { data: userData } = await coreApiAccount()
      if (userData) {
        currentUser.value = {
          is_logged_in: !!userData.username,
          username: userData.username,
        }
      }
    } catch (e) {
      console.error('Auth check failed', e)
    }

    await fetchShoppingLists()
  }

  // ---- Meal CRUD ----
  async function addMeal(recipeId: string, date: string, mealType: string) {
    const { data } = await mealsApiMealsCreateCampMeal({
      path: { camp_id: campId },
      body: { recipe_id: recipeId, meal_type: mealType, date },
    })
    if (data) {
      meals.value.push(data)
      selectedMeals.value.push(data.id as string)
    }
  }

  async function removeMeal(meal: CampMealSchema, confirmMsg: string) {
    if (!confirm(confirmMsg)) return
    await mealsApiMealsDeleteCampMeal({
      path: { camp_id: campId, meal_id: meal.id as string },
    })
    meals.value = meals.value.filter((m) => m.id !== meal.id)
    selectedMeals.value = selectedMeals.value.filter((id) => id !== meal.id)
  }

  async function updateMeal(
    meal: CampMealSchema,
    data: { overridePeopleCount: number | null; preferenceId: number | null },
  ) {
    const { data: updatedMeal } = await mealsApiMealsUpdateCampMeal({
      path: { camp_id: campId, meal_id: meal.id as string },
      body: {
        override_people_count: data.overridePeopleCount,
        serves_preference_id: data.preferenceId,
      },
    })
    if (updatedMeal) {
      const idx = meals.value.findIndex((m) => m.id === meal.id)
      if (idx !== -1) meals.value[idx] = updatedMeal
    }
    return updatedMeal
  }

  async function toggleMealDone(meal: CampMealSchema) {
    try {
      const { data } = await mealsApiMealsToggleCampMealDone({
        path: { camp_id: campId, meal_id: meal.id as string },
      })
      if (data) {
        meal.is_done = data.is_done
      }
    } catch (e) {
      console.error(e)
    }
  }

  // ---- Day selection ----
  function getMealsForDay(day: string) {
    if (!mealsGrid.value[day]) return []
    return Object.values(mealsGrid.value[day]).flat()
  }

  function isDaySelected(day: string) {
    const dayMeals = getMealsForDay(day)
    if (dayMeals.length === 0) return false
    return dayMeals.every((m) => selectedMeals.value.includes(m.id!))
  }

  function toggleDay(day: string) {
    const dayMeals = getMealsForDay(day)
    const dayMealIds = dayMeals.map((m) => m.id!).filter((id) => !!id)
    if (isDaySelected(day)) {
      selectedMeals.value = selectedMeals.value.filter((id) => !dayMealIds.includes(id))
    } else {
      const existing = selectedMeals.value.filter((id) => !dayMealIds.includes(id))
      selectedMeals.value = [...existing, ...dayMealIds]
    }
  }

  // ---- Shopping lists ----
  async function fetchShoppingLists() {
    loadingShoppingLists.value = true
    try {
      const { data } = await mealsApiShoppingListCampShoppingLists({ path: { camp_id: campId } })
      if (data) shoppingLists.value = data
    } finally {
      loadingShoppingLists.value = false
    }
  }

  async function generateShoppingList() {
    if (selectedMeals.value.length === 0) {
      alert(t('confirm.select_at_least_one_meal'))
      return null
    }
    const { data } = await mealsApiShoppingGenerateShoppingList({
      path: { camp_id: campId },
      body: { meal_ids: selectedMeals.value },
    })
    return data
  }

  async function deleteShoppingList(listId: string) {
    if (!confirm(t('confirm.delete_shopping_list'))) return
    await mealsApiShoppingDeleteShoppingList({ path: { list_id: listId } })
    fetchShoppingLists()
  }

  watch(showShoppingLists, (newVal) => {
    if (newVal) fetchShoppingLists()
  })

  // ---- General items ----
  async function fetchGeneralItems() {
    const { data } = await mealsApiCampsListCampGeneralItems({ path: { camp_id: campId } })
    if (data) generalItems.value = data
  }

  async function addGeneralItem(item: { name: string; amount: string }) {
    await mealsApiCampsCreateCampGeneralItem({
      path: { camp_id: campId },
      body: { name: item.name, amount: item.amount, category: 'NON_FOOD' },
    })
    fetchGeneralItems()
  }

  async function deleteGeneralItem(id: string) {
    await mealsApiCampsDeleteCampGeneralItem({ path: { camp_id: campId, item_id: id } })
    fetchGeneralItems()
  }

  async function moveGeneralItemsToShoppingList() {
    if (!latestShoppingListId.value) {
      alert(t('confirm.please_create_a_shopping_list_first'))
      return
    }
    if (!confirm(t('confirm.move_general_items_to_shopping_list')))
      return

    isMovingGeneralItems.value = true
    try {
      await mealsApiShoppingMoveGeneralItemsToShoppingList({
        path: { camp_id: campId, list_id: latestShoppingListId.value },
      })
      await fetchGeneralItems()
      await fetchShoppingLists()
    } catch (e) {
      console.error(e)
      alert('Failed to move items')
    } finally {
      isMovingGeneralItems.value = false
    }
  }

  // ---- Camp editing ----
  async function saveEditCamp(data: { name: string; default_people_count: number; notes: string }) {
    try {
      const { data: updatedCamp } = await mealsApiCampsUpdateCamp({
        path: { camp_id: campId },
        body: { name: data.name, default_people_count: data.default_people_count, notes: data.notes },
      })
      if (updatedCamp) {
        camp.value = updatedCamp
        editingCamp.value = false
      }
    } catch (e) {
      console.error(e)
      alert(t('error.failed_to_save_camp'))
    }
  }

  watch(
    () => camp.value,
    (newCamp) => {
      if (newCamp) {
        editCampData.value = {
          name: newCamp.name,
          default_people_count: newCamp.default_people_count || 0,
          notes: newCamp.notes || '',
        }
      }
    },
    { immediate: true },
  )

  // ---- Collaborators ----
  async function inviteCollaborator(username: string) {
    try {
      const { data } = await mealsApiCampsInviteCollaborator({
        path: { camp_id: campId },
        body: { username },
      })
      if (data && camp.value) {
        camp.value.collaborators = data.collaborators
      }
    } catch (e: any) {
      alert(e.response?.data?.detail || t('error.failed_to_invite_user'))
    }
  }

  async function removeCollaborator(username: string) {
    const isSelf = username === currentUser.value.username
    const confirmMsg = isSelf
      ? t('confirm.leave_camp')
      : t('confirm.remove_collaborator') + ' ' + username
    if (!confirm(confirmMsg)) return

    try {
      await mealsApiCampsRemoveCollaborator({ path: { camp_id: campId, username } })
      if (camp.value && camp.value.collaborators) {
        camp.value.collaborators = camp.value.collaborators.filter((u: string) => u !== username)
      }
      return isSelf // tells caller to redirect
    } catch (e: any) {
      alert(t('error.failed_to_remove_user'))
      return false
    }
  }

  return {
    // State
    camp,
    meals,
    selectedMeals,
    preferences,
    allTags,
    currentUser,
    shoppingLists,
    showShoppingLists,
    loadingShoppingLists,
    generalItems,
    isMovingGeneralItems,
    latestShoppingListId,
    editingCamp,
    editCampData,
    // Computed
    campDays,
    mealsGrid,
    recipeNames,
    // Methods
    fetchData,
    addMeal,
    removeMeal,
    updateMeal,
    toggleMealDone,
    getMealsForDay,
    isDaySelected,
    toggleDay,
    fetchShoppingLists,
    generateShoppingList,
    deleteShoppingList,
    fetchGeneralItems,
    addGeneralItem,
    deleteGeneralItem,
    moveGeneralItemsToShoppingList,
    saveEditCamp,
    inviteCollaborator,
    removeCollaborator,
  }
}
