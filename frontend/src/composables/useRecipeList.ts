import { ref, computed, watch, type Ref } from 'vue'
import { mealsApiRecipesListRecipes, type RecipeSchema } from '../client'

/**
 * Shared pagination + search logic for recipe lists.
 * Used by both RecipeSidebar (camp planner) and Recipes (recipe browser).
 */
export function useRecipeList(options: {
  searchQuery: Ref<string>
  selectedTags: Ref<string[]>
  selectedPreferenceId: Ref<number | null>
  /** If true, automatically watch filters and reset on change. Default: true */
  autoWatch?: boolean
}) {
  const { searchQuery, selectedTags, selectedPreferenceId, autoWatch = true } = options

  const recipes = ref<RecipeSchema[]>([])
  const currentPage = ref(1)
  const totalCount = ref(0)
  const isLoading = ref(false)

  const hasMore = computed(() => recipes.value.length < totalCount.value)

  async function fetchRecipes(reset = false) {
    if (reset) {
      currentPage.value = 1
    }
    isLoading.value = true
    try {
      const { data } = await mealsApiRecipesListRecipes({
        query: {
          page: currentPage.value,
          q: searchQuery.value || undefined,
          tags: selectedTags.value.length > 0 ? selectedTags.value.join(',') : undefined,
          preference_id: selectedPreferenceId.value || undefined,
        },
      })
      if (data) {
        if (reset) recipes.value = data.items
        else recipes.value.push(...data.items)
        totalCount.value = data.count
      }
    } finally {
      isLoading.value = false
    }
  }

  function loadMore() {
    if (hasMore.value && !isLoading.value) {
      currentPage.value++
      fetchRecipes()
    }
  }

  if (autoWatch) {
    watch([searchQuery, selectedTags, selectedPreferenceId], () => {
      fetchRecipes(true)
    })
  }

  return {
    recipes,
    currentPage,
    totalCount,
    isLoading,
    hasMore,
    fetchRecipes,
    loadMore,
  }
}
