<script setup lang="ts">
import { onMounted, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import MarkdownView from "../components/MarkdownView.vue";
import TagInput from "../components/TagInput.vue";
import { useI18n } from "../composables/useI18n";
import { useRecipeDetail } from "../composables/useRecipeDetail";

const route = useRoute();
const router = useRouter();
const { t } = useI18n();
const recipeId = route.params.id as string;

const {
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
  isOwner,
  canEdit,
  showCollaboratorModal,
  inviteUsername,
  editingIngId,
  editIngAmount,
  editIngUnit,
  init,
  cleanup,
  saveRecipeDetails,
  selectUnitSuggestion,
  selectSuggestion,
  handleAddIngredient,
  startEditIng,
  saveEditIng,
  removeIngredient,
  inviteCollaborator,
  removeCollaborator,
} = useRecipeDetail(recipeId);

onMounted(init);
onUnmounted(cleanup);
</script>

<template>
  <div v-if="recipe" class="recipe-detail">
    <!-- AI Loading Overlay -->
    <div v-if="recipe.is_importing" class="ai-overlay">
      <div class="ai-loader-card">
        <div class="magic-spinner">✨</div>
        <h3>{{ t("recipe.ai_is_crafting_your_recipe") }}</h3>
        <p>
          {{ t("recipe.ai_is_parsing_your_text_and_categorizing_ingredients") }}
        </p>
        <div class="progress-bar-container">
          <div class="progress-bar-fill"></div>
        </div>
      </div>
    </div>

    <div
      class="flex items-center gap-4 mb-8"
      :class="{ 'blur-bg': recipe.is_importing }"
    >
      <button class="btn btn-secondary" @click="router.push('/recipes')">
        &larr; {{ t("btn.back") }}
      </button>
      <h2 class="page-title">{{ recipe.name }}</h2>
    </div>

    <div class="recipe-grid" :class="{ 'blur-bg': recipe.is_importing }">
      <!-- Details Panel -->
      <div class="card flex-col gap-4">
        <div class="flex justify-between items-start">
          <h3>{{ t("recipe.details") }}</h3>
          <div class="flex gap-2">
            <button
              v-if="isOwner"
              class="btn btn-secondary"
              @click="showCollaboratorModal = true"
            >
              👥 {{ t("recipe.collaborators") }}
            </button>
            <button
              v-if="!isEditingRecipe && canEdit"
              class="btn btn-secondary"
              @click="isEditingRecipe = true"
            >
              {{ t("btn.edit") }}
            </button>
          </div>
        </div>

        <div v-if="!isEditingRecipe">
          <div class="mb-4">
            <label>{{ t("recipe.tags_and_preferences") }}</label>
            <div class="flex gap-1 flex-wrap mt-2">
              <span
                v-for="pref in recipe.preferences"
                :key="pref.id || 0"
                class="badge"
              >
                {{ pref.name }}
              </span>
              <span v-for="tag in recipe.tags" :key="tag" class="badge-outline">
                #{{ tag }}
              </span>
              <span
                v-if="
                  (!recipe.preferences || recipe.preferences.length === 0) &&
                  (!recipe.tags || recipe.tags.length === 0)
                "
                class="text-mute text-xs"
              >
                {{ t("recipe.no_tags_or_preferences") }}
              </span>
            </div>
          </div>
          <div class="mb-4">
            <label>{{ t("recipe.default_portions") }}</label>
            <div class="portions-display">{{ recipe.default_portions }}</div>
          </div>
          <div>
            <label>{{ t("recipe.description") }}</label>
            <p>{{ recipe.description || t("recipe.no_description") }}</p>
          </div>
          <div>
            <label>{{ t("recipe.instructions") }}</label>
            <div class="mt-2">
              <MarkdownView
                v-if="recipe.instructions"
                :content="recipe.instructions"
              />
              <p v-else class="text-mute">{{ t("recipe.no_instructions") }}</p>
            </div>
          </div>
        </div>

        <div v-else class="flex-col gap-4">
          <div>
            <label>{{ t("recipe.dietary_preferences") }}</label>
            <div class="flex gap-2 flex-wrap mt-2">
              <label
                v-for="pref in allPreferences"
                :key="pref.id || 0"
                class="pref-checkbox"
              >
                <input
                  type="checkbox"
                  :value="pref.id"
                  v-model="editRecipeData.preference_ids"
                />
                <span class="text-sm">{{ pref.name }}</span>
              </label>
            </div>
          </div>
          <div>
            <label>{{ t("recipe.tags") }}</label>
            <div class="mt-2">
              <TagInput
                v-model="editRecipeData.tags"
                :suggestions="allTags"
                placeholder="Add tags..."
              />
            </div>
          </div>
          <div>
            <label>{{ t("recipe.default_portions") }}</label>
            <input
              type="number"
              class="input"
              v-model="editRecipeData.default_portions"
            />
          </div>
          <div>
            <label>{{ t("recipe.description") }}</label>
            <textarea
              class="input"
              v-model="editRecipeData.description"
              rows="3"
            ></textarea>
          </div>
          <div>
            <label>{{ t("recipe.instructions") }}</label>
            <textarea
              class="input"
              v-model="editRecipeData.instructions"
              rows="6"
            ></textarea>
          </div>
          <div class="flex gap-2 justify-end">
            <button class="btn btn-secondary" @click="isEditingRecipe = false">
              {{ t("btn.cancel") }}
            </button>
            <button class="btn btn-primary" @click="saveRecipeDetails">
              {{ t("btn.save") }}
            </button>
          </div>
        </div>
      </div>

      <!-- Ingredients Panel -->
      <div class="card">
        <h3>{{ t("recipe.ingredients") }}</h3>
        <p class="text-mute mb-4">{{ t("recipe.ingredients_description") }}</p>

        <!-- Smart Add Form -->
        <div v-if="canEdit" class="ingredient-form">
          <div class="flex-1" style="position: relative">
            <label>{{ t("recipe.ingredient") }}</label>
            <input
              class="input"
              v-model="ingredientQuery"
              :placeholder="t('recipe.ingredient_placeholder')"
              @focus="showSuggestions = searchResults.length > 0"
              autocomplete="off"
            />
            <ul v-if="showSuggestions" class="dropdown">
              <li
                v-for="res in searchResults"
                :key="res.id as string"
                @click="selectSuggestion(res)"
                @mousedown.prevent
              >
                {{ res.name }}
                <span class="text-mute text-xs"
                  >(Base: {{ res.base_unit }})</span
                >
              </li>
            </ul>
          </div>

          <div class="ingredient-amount-col">
            <label>{{ t("recipe.amount") }}</label>
            <input
              class="input"
              type="number"
              step="0.01"
              v-model="amountInput"
            />
          </div>

          <div class="ingredient-unit-col">
            <label>{{ t("recipe.unit") }}</label>
            <input
              class="input"
              v-model="unitInput"
              placeholder="g, ml, pcs"
              @focus="
                showUnitSuggestions = true;
                unitSearchResults = allKnownUnits;
              "
            />
            <ul
              v-if="showUnitSuggestions && unitSearchResults.length"
              class="dropdown dropdown-full"
            >
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

          <button
            class="btn btn-primary ingredient-add-btn"
            @click="handleAddIngredient"
          >
            {{ t("btn.add") }}
          </button>
        </div>

        <hr class="ingredient-divider" />

        <ul class="list-reset flex-col gap-2">
          <li
            v-for="ing in ingredients"
            :key="String(ing.id)"
            class="list-item flex justify-between items-center"
          >
            <div class="flex-1">
              <strong>{{ ing.ingredient.name }}</strong>
            </div>

            <!-- View Mode -->
            <div
              v-if="editingIngId !== String(ing.id)"
              class="flex items-center gap-4 justify-end flex-1"
            >
              <span class="text-mute ingredient-amount"
                >{{ ing.amount }} {{ ing.unit }}</span
              >
              <div v-if="canEdit" class="flex gap-2">
                <button
                  class="btn btn-secondary btn-sm"
                  @click="startEditIng(ing)"
                >
                  ✎
                </button>
                <button
                  class="btn btn-ghost btn-sm text-danger"
                  @click="removeIngredient(ing)"
                >
                  ✕
                </button>
              </div>
            </div>

            <!-- Edit Mode -->
            <div v-else class="flex items-center gap-2 justify-end flex-1">
              <input
                type="number"
                step="0.01"
                class="input input-inline ingredient-edit-amount"
                v-model="editIngAmount"
              />
              <input
                class="input input-inline ingredient-edit-unit"
                v-model="editIngUnit"
              />
              <button class="btn btn-primary btn-sm" @click="saveEditIng(ing)">
                ✔
              </button>
              <button
                class="btn btn-secondary btn-sm"
                @click="editingIngId = null"
              >
                ✕
              </button>
            </div>
          </li>
          <li v-if="ingredients.length === 0" class="text-mute">
            No ingredients added yet.
          </li>
        </ul>
      </div>
    </div>

    <!-- Collaborator Modal -->
    <div v-if="showCollaboratorModal" class="modal-backdrop">
      <div class="modal">
        <div class="flex justify-between items-center mb-6">
          <h3 class="mb-0">Recipe Collaborators</h3>
          <button class="btn-ghost" @click="showCollaboratorModal = false">
            ✕
          </button>
        </div>

        <p class="text-mute text-sm mb-4">
          Collaborators can edit the recipe but cannot manage other
          collaborators.
        </p>

        <div class="flex gap-2 mb-6">
          <input
            class="input"
            v-model="inviteUsername"
            placeholder="Enter username"
            @keyup.enter="inviteCollaborator"
          />
          <button class="btn btn-primary" @click="inviteCollaborator">
            Invite
          </button>
        </div>

        <ul class="list-reset flex-col gap-2">
          <li class="list-item flex justify-between items-center">
            <span>{{ recipe.owner_username }}</span>
            <span class="badge">Owner</span>
          </li>
          <li
            v-for="user in recipe.collaborators"
            :key="user"
            class="list-item flex justify-between items-center"
          >
            <span>{{ user }}</span>
            <button
              class="btn btn-ghost text-danger btn-sm"
              @click="removeCollaborator(user)"
            >
              Remove
            </button>
          </li>
        </ul>
      </div>
    </div>
  </div>
  <div v-else>Loading recipe...</div>
</template>

<style scoped>
.recipe-detail {
  position: relative;
}

.recipe-grid {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 2rem;
}

.portions-display {
  font-size: 1.25rem;
  color: var(--color-text-mute);
}

.pref-checkbox {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 4px 8px;
  border: 1px solid var(--color-border);
  border-radius: 6px;
  cursor: pointer;
}

.ingredient-form {
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.ingredient-amount-col {
  flex: 0 0 100px;
}

.ingredient-unit-col {
  flex: 0 0 100px;
  position: relative;
}

.ingredient-add-btn {
  height: 48px;
  align-self: flex-end;
}

.ingredient-divider {
  margin: 1.5rem 0;
}

.ingredient-amount {
  min-width: 60px;
  text-align: right;
}

.ingredient-edit-amount {
  width: 80px;
}

.ingredient-edit-unit {
  width: 60px;
}

/* AI Overlay */
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
  0% {
    transform: scale(1) rotate(0deg);
    opacity: 0.8;
  }
  50% {
    transform: scale(1.2) rotate(180deg);
    opacity: 1;
  }
  100% {
    transform: scale(1) rotate(360deg);
    opacity: 0.8;
  }
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
  0% {
    transform: translateX(-100%);
  }
  100% {
    transform: translateX(300%);
  }
}
</style>
