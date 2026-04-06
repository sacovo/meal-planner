import { ref, computed, watch } from 'vue'
import {
  mealsApiRecipesGetRecipe,
  mealsApiRecipesUpdateRecipe,
  mealsApiRecipesListRecipeIngredients,
  mealsApiRecipesAddRecipeIngredient,
  mealsApiRecipesUpdateRecipeIngredient,
  mealsApiRecipesDeleteRecipeIngredient,
  mealsApiIngredientsListIngredients,
  mealsApiRecipesListPreferences,
  mealsApiIngredientsListUnits,
  mealsApiIngredientsListTags,
  coreApiGetCurrentUserStatus,
  mealsApiRecipesInviteRecipeCollaborator,
  mealsApiRecipesRemoveRecipeCollaborator,
  type RecipeSchema,
  type RecipeIngredientSchema,
  type IngredientSchema,
  type DietaryPreferenceSchema,
} from '../client'

/**
 * Controller logic for the RecipeDetail view.
 * Manages recipe CRUD, ingredient editing, collaborators, and AI import polling.
 */
export function useRecipeDetail(recipeId: string) {
  // ---- Core state ----
  const recipe = ref<RecipeSchema | null>(null)
  const ingredients = ref<RecipeIngredientSchema[]>([])

  // ---- Ingredient form state ----
  const ingredientQuery = ref('')
  const amountInput = ref(1)
  const unitInput = ref('g')
  const searchResults = ref<IngredientSchema[]>([])
  const showSuggestions = ref(false)
  const allKnownUnits = ref<string[]>([])
  const unitSearchResults = ref<string[]>([])
  const showUnitSuggestions = ref(false)

  // ---- Recipe edit state ----
  const isEditingRecipe = ref(false)
  const allPreferences = ref<DietaryPreferenceSchema[]>([])
  const allTags = ref<string[]>([])
  const editRecipeData = ref({
    description: '',
    instructions: '',
    default_portions: 4,
    preference_ids: [] as number[],
    tags: [] as string[],
  })

  // ---- Auth state ----
  const currentUser = ref<string | null>(null)
  const isOwner = computed(() => recipe.value && currentUser.value === recipe.value.owner_username)
  const isCollaborator = computed(
    () => recipe.value && recipe.value.collaborators?.includes(currentUser.value || ''),
  )
  const canEdit = computed(() => isOwner.value || isCollaborator.value)

  // ---- Collaborator modal ----
  const showCollaboratorModal = ref(false)
  const inviteUsername = ref('')

  // ---- Inline ingredient editing ----
  const editingIngId = ref<string | null>(null)
  const editIngAmount = ref(0)
  const editIngUnit = ref('')

  // ---- Polling for AI import ----
  const isPolling = ref(false)
  let pollTimer: ReturnType<typeof setInterval> | null = null

  // ---- Data fetching ----
  async function fetchCurrentUser() {
    const { data } = await coreApiGetCurrentUserStatus()
    const status = data as { is_logged_in: boolean; username: string }
    if (status?.is_logged_in) {
      currentUser.value = status.username
    }
  }

  async function fetchRecipe() {
    const { data: r } = await mealsApiRecipesGetRecipe({ path: { recipe_id: recipeId } })
    if (r) {
      recipe.value = r
      editRecipeData.value = {
        description: r.description || '',
        instructions: r.instructions || '',
        default_portions: r.default_portions ?? 4,
        preference_ids: r.preferences ? r.preferences.map((p: any) => p.id) : [],
        tags: r.tags || [],
      }

      if (r.is_importing && !isPolling.value) startPolling()
      else if (!r.is_importing && isPolling.value) stopPolling()
    }
  }

  async function fetchIngredients() {
    const { data } = await mealsApiRecipesListRecipeIngredients({ path: { recipe_id: recipeId } })
    if (data) ingredients.value = data
  }

  async function fetchPreferences() {
    const { data } = await mealsApiRecipesListPreferences()
    if (data) allPreferences.value = data
  }

  async function fetchUnits() {
    const { data } = await mealsApiIngredientsListUnits()
    if (data) allKnownUnits.value = data
  }

  async function fetchTags() {
    const { data } = await mealsApiIngredientsListTags()
    if (data) allTags.value = data
  }

  // ---- Polling ----
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

  // ---- Recipe editing ----
  async function saveRecipeDetails() {
    if (!recipe.value) return
    const { data } = await mealsApiRecipesUpdateRecipe({
      path: { recipe_id: recipeId },
      body: {
        description: editRecipeData.value.description,
        instructions: editRecipeData.value.instructions,
        default_portions: editRecipeData.value.default_portions,
        preference_ids: editRecipeData.value.preference_ids,
        tags: editRecipeData.value.tags,
      },
    })
    if (data) {
      recipe.value = data
      isEditingRecipe.value = false
      fetchTags()
    }
  }

  // ---- Ingredient search ----
  watch(ingredientQuery, async (newQuery) => {
    if (newQuery.length < 2) {
      searchResults.value = []
      showSuggestions.value = false
      return
    }
    const { data } = await mealsApiIngredientsListIngredients({ query: { q: newQuery } })
    if (data) {
      searchResults.value = data
      showSuggestions.value = data.length > 0
    }
  })

  watch(unitInput, (newVal) => {
    if (!newVal) {
      unitSearchResults.value = allKnownUnits.value
      return
    }
    unitSearchResults.value = allKnownUnits.value.filter((u) =>
      u.toLowerCase().includes(newVal.toLowerCase()),
    )
  })

  function selectUnitSuggestion(unit: string) {
    unitInput.value = unit
    showUnitSuggestions.value = false
  }

  function selectSuggestion(ingredient: IngredientSchema) {
    ingredientQuery.value = ingredient.name
    if (ingredient.base_unit === 'kg') unitInput.value = 'g'
    else if (ingredient.base_unit === 'l') unitInput.value = 'dl'
    else unitInput.value = ingredient.base_unit
    showSuggestions.value = false
  }

  // ---- Ingredient CRUD ----
  async function handleAddIngredient() {
    if (!ingredientQuery.value) return
    const { data, error } = await mealsApiRecipesAddRecipeIngredient({
      path: { recipe_id: recipeId },
      body: {
        ingredient_name: ingredientQuery.value,
        amount: amountInput.value,
        unit: unitInput.value,
      },
    })
    if (data) {
      ingredients.value.push(data)
      ingredientQuery.value = ''
      amountInput.value = 1
      unitInput.value = 'g'
      showSuggestions.value = false
    } else {
      alert('Error adding ingredient: ' + JSON.stringify(error))
    }
  }

  function startEditIng(ing: RecipeIngredientSchema) {
    editingIngId.value = ing.id ? String(ing.id) : null
    editIngAmount.value = ing.amount
    editIngUnit.value = ing.unit
  }

  async function saveEditIng(ing: RecipeIngredientSchema) {
    const { data } = await mealsApiRecipesUpdateRecipeIngredient({
      path: { recipe_id: recipeId, ingredient_id: String(ing.id) },
      body: { amount: editIngAmount.value, unit: editIngUnit.value },
    })
    if (data) {
      ing.amount = data.amount
      ing.unit = data.unit
      editingIngId.value = null
    }
  }

  async function removeIngredient(ing: RecipeIngredientSchema) {
    if (!confirm('Remove ingredient?')) return
    await mealsApiRecipesDeleteRecipeIngredient({
      path: { recipe_id: recipeId, ingredient_id: String(ing.id) },
    })
    ingredients.value = ingredients.value.filter((i) => i.id !== ing.id)
  }

  // ---- Collaborators ----
  async function inviteCollaborator() {
    if (!inviteUsername.value) return
    const { data, error } = await mealsApiRecipesInviteRecipeCollaborator({
      path: { recipe_id: recipeId },
      body: { username: inviteUsername.value },
    })
    if (data) {
      recipe.value = data
      inviteUsername.value = ''
    } else {
      alert('Error inviting collaborator: ' + JSON.stringify(error))
    }
  }

  async function removeCollaborator(username: string) {
    if (!confirm(`Remove ${username} from collaborators?`)) return
    const { data } = await mealsApiRecipesRemoveRecipeCollaborator({
      path: { recipe_id: recipeId, username },
    })
    if (data) {
      if (recipe.value) {
        recipe.value.collaborators = (recipe.value.collaborators || []).filter(
          (u) => u !== username,
        )
      }
    }
  }

  // ---- Lifecycle ----
  function init() {
    fetchCurrentUser()
    fetchRecipe()
    fetchIngredients()
    fetchPreferences()
    fetchUnits()
    fetchTags()
  }

  function cleanup() {
    stopPolling()
  }

  return {
    // State
    recipe,
    ingredients,
    ingredientQuery,
    amountInput,
    unitInput,
    searchResults,
    showSuggestions,
    allKnownUnits,
    unitSearchResults,
    showUnitSuggestions,
    isEditingRecipe,
    allPreferences,
    allTags,
    editRecipeData,
    currentUser,
    isOwner,
    isCollaborator,
    canEdit,
    showCollaboratorModal,
    inviteUsername,
    editingIngId,
    editIngAmount,
    editIngUnit,
    isPolling,
    // Methods
    init,
    cleanup,
    fetchRecipe,
    saveRecipeDetails,
    selectUnitSuggestion,
    selectSuggestion,
    handleAddIngredient,
    startEditIng,
    saveEditIng,
    removeIngredient,
    inviteCollaborator,
    removeCollaborator,
  }
}
