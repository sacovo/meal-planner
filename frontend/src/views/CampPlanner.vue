<script setup lang="ts">
import { onMounted } from "vue";
import { useRoute, useRouter } from "vue-router";
// @ts-ignore
import html2pdf from "html2pdf.js";
import { type RecipeSchema } from "../client";
import CampNotes from "../components/CampNotes.vue";
import GeneralItems from "../components/GeneralItems.vue";
import RecipeSidebar from "../components/RecipeSidebar.vue";
import PlannerMatrix from "../components/PlannerMatrix.vue";
import ShoppingListManager from "../components/ShoppingListManager.vue";
import EditCampModal from "../components/EditCampModal.vue";
import EditMealModal from "../components/EditMealModal.vue";
import CollaboratorsModal from "../components/CollaboratorsModal.vue";
import { useI18n } from "../composables/useI18n";
import { useCampPlanner } from "../composables/useCampPlanner";
import { MEAL_TYPES } from "../composables/useMealTypes";
import { ref } from "vue";
import type { CampMealSchema } from "../client";

const route = useRoute();
const router = useRouter();
const { t } = useI18n();
const campId = route.params.id as string;

const {
  camp,
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
  campDays,
  mealsGrid,
  recipeNames,
  fetchData,
  addMeal,
  removeMeal,
  updateMeal,
  toggleMealDone,
  toggleDay,
  generateShoppingList,
  deleteShoppingList,
  addGeneralItem,
  deleteGeneralItem,
  moveGeneralItemsToShoppingList,
  saveEditCamp,
  inviteCollaborator,
  removeCollaborator,
} = useCampPlanner(campId);

const isSidebarCollapsed = ref(false);
const searchRecipeQuery = ref("");
const showCollaboratorsModal = ref(false);
const editingMeal = ref<CampMealSchema | null>(null);

// Drag & Drop
function startDrag(event: DragEvent, recipe: RecipeSchema) {
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = "copy";
    event.dataTransfer.effectAllowed = "copy";
    event.dataTransfer.setData("recipe_id", recipe.id as string);
  }
}

async function onDrop(event: DragEvent, date: string, mealType: string) {
  const recipeId = event.dataTransfer?.getData("recipe_id");
  if (!recipeId) return;
  await addMeal(recipeId, date, mealType);
}

function openEditMeal(meal: CampMealSchema) {
  editingMeal.value = meal;
}

async function saveEditMeal(data: {
  overridePeopleCount: number | null;
  preferenceId: number | null;
}) {
  if (!editingMeal.value) return;
  const updated = await updateMeal(editingMeal.value, data);
  if (updated) editingMeal.value = null;
}

async function handleRemoveMeal(meal: CampMealSchema) {
  await removeMeal(meal, t("planner.remove_meal_from_slot"));
}

async function handleGenerateShoppingList() {
  const data = await generateShoppingList();
  if (data) router.push(`/share/${data.shared_token}`);
}

function handleOpenShoppingList(token: string) {
  router.push(`/share/${token}`);
}

async function handleRemoveCollaborator(username: string) {
  const shouldRedirect = await removeCollaborator(username);
  if (shouldRedirect) router.push("/");
}

function switchToDayDetail(day: string) {
  router.push(`/camps/${campId}/day/${day}`);
}

// PDF Export
function exportMatrixPDF() {
  const element = document.getElementById("planner-matrix-canvas");
  if (!element) return;

  const originalOverflow = element.style.overflowX;
  const originalMaxWidth = element.style.maxWidth;
  element.style.overflowX = "visible";
  element.style.maxWidth = "none";

  const opt = {
    margin: 5,
    filename: `CampPlan_${camp.value?.name}.pdf`,
    image: { type: "jpeg" as const, quality: 0.98 },
    html2canvas: {
      scale: 2,
      useCORS: true,
      scrollX: 0,
      scrollY: 0,
      windowWidth: element.scrollWidth + 50,
      width: element.scrollWidth,
    },
    jsPDF: { unit: "mm", format: "a4", orientation: "landscape" },
  } as const;

  html2pdf()
    .set(opt)
    .from(element)
    .save()
    .then(() => {
      element.style.overflowX = originalOverflow;
      element.style.maxWidth = originalMaxWidth;
    });
}

onMounted(fetchData);
</script>

<template>
  <div v-if="camp" class="flex-col gap-4">
    <div class="page-header">
      <div class="flex items-center gap-4">
        <button class="btn btn-secondary" @click="router.push('/')">
          &larr; {{ t("back") }}
        </button>
        <h2 class="page-title">{{ t("plan") }} {{ camp.name }}</h2>
        <button class="btn btn-ghost" v-if="camp" @click="editingCamp = true">
          ⚙️ {{ t("edit") }}
        </button>
      </div>

      <div class="flex gap-2">
        <button
          class="btn btn-secondary no-print"
          @click="showCollaboratorsModal = true"
        >
          👥 {{ t("collaborators.title") }}
        </button>
        <button
          class="btn btn-secondary no-print"
          @click="router.push(`/camps/${campId}/inventory`)"
        >
          📦 {{ t("inventory.title") }}
        </button>
        <button class="btn btn-secondary no-print" @click="exportMatrixPDF">
          📋 {{ t("export") }}
        </button>
      </div>
    </div>

    <!-- Planner Matrix Area -->
    <div
      class="planner-layout"
      :class="{ 'sidebar-collapsed': isSidebarCollapsed }"
    >
      <!-- Recipes Sidebar -->
      <RecipeSidebar
        :preferences="preferences"
        :all-tags="allTags"
        v-model:searchQuery="searchRecipeQuery"
        v-model:isCollapsed="isSidebarCollapsed"
        @dragstart="startDrag"
      />

      <!-- Matrix Canvas -->
      <PlannerMatrix
        :camp="camp"
        :camp-days="campDays"
        :meal-types-config="MEAL_TYPES"
        :meals-grid="mealsGrid"
        v-model:selected-meals="selectedMeals"
        :recipe-names="recipeNames"
        @drop="onDrop"
        @edit-meal="openEditMeal"
        @toggle-done="toggleMealDone"
        @remove-meal="handleRemoveMeal"
        @switch-day="switchToDayDetail"
        @toggle-day="toggleDay"
      />
    </div>

    <ShoppingListManager
      :selected-meals-count="selectedMeals.length"
      v-model:showShoppingLists="showShoppingLists"
      :shopping-lists="shoppingLists"
      :loading="loadingShoppingLists"
      @generate="handleGenerateShoppingList"
      @delete="deleteShoppingList"
      @open="handleOpenShoppingList"
    />

    <div class="grid bottom-grid">
      <div class="flex-col gap-4">
        <CampNotes :notes="camp?.notes" @edit="editingCamp = true" />
      </div>
      <GeneralItems
        :items="generalItems"
        :can-move="!!latestShoppingListId"
        :is-moving="isMovingGeneralItems"
        @add="addGeneralItem"
        @delete="deleteGeneralItem"
        @move="moveGeneralItemsToShoppingList"
      />
    </div>

    <!-- Modals -->
    <EditCampModal
      v-model:show="editingCamp"
      :camp-data="editCampData"
      @save="saveEditCamp"
    />

    <EditMealModal
      :show="!!editingMeal"
      @update:show="editingMeal = $event ? editingMeal : null"
      :meal="editingMeal"
      :preferences="preferences"
      :recipe-name="
        editingMeal ? recipeNames[editingMeal.recipe as string] : ''
      "
      @save="saveEditMeal"
    />

    <CollaboratorsModal
      v-if="camp"
      v-model:show="showCollaboratorsModal"
      :collaborators="camp.collaborators || []"
      :owner-username="camp.owner_username || ''"
      :current-user-username="currentUser.username || ''"
      @invite="inviteCollaborator"
      @remove="handleRemoveCollaborator"
    />
  </div>
  <div v-else>Loading camp planning...</div>
</template>

<style scoped>
.planner-layout {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 1.5rem;
  transition: grid-template-columns 0.3s ease;
}

.planner-layout.sidebar-collapsed {
  grid-template-columns: 60px 1fr;
}

.bottom-grid {
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  margin-top: 1rem;
}

.meal-done {
  opacity: 0.6;
  background: var(--color-bg-mute) !important;
  filter: grayscale(0.5);
}
</style>
