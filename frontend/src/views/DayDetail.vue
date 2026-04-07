<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  mealsApiCampsGetCamp,
  mealsApiMealsListCampMeals,
  mealsApiRecipesListRecipes,
  mealsApiRecipesListRecipeIngredients,
  mealsApiMealsToggleCampMealDone,
  type CampSchema,
  type CampMealSchema,
  type RecipeSchema,
  type RecipeIngredientSchema,
} from "../client";
import MarkdownView from "../components/MarkdownView.vue";
import { MEAL_TYPES } from "../composables/useMealTypes";
// @ts-ignore
import html2pdf from "html2pdf.js";
import { useI18n } from "@/composables/useI18n";

const route = useRoute();
const router = useRouter();

const campId = route.params.id as string;
const dateStr = route.params.date as string;

const camp = ref<CampSchema | null>(null);
const meals = ref<CampMealSchema[]>([]);
const recipes = ref<RecipeSchema[]>([]);
const ingredientsMap = ref<Record<string, RecipeIngredientSchema[]>>({});
const loading = ref(true);
const isNavOpen = ref(false);
const { t } = useI18n();

const groupedMeals = computed(() => {
  const knownTypeSet = new Set(MEAL_TYPES.map((mt) => mt.val));
  const knownGroups = MEAL_TYPES.map((mt) => ({
    type: mt.val,
    label: mt.label,
    meals: meals.value
      .filter((meal) => meal.meal_type === mt.val)
      .sort((a, b) => a.id!.localeCompare(b.id!)),
  })).filter((group) => group.meals.length > 0);

  const unknownMeals = meals.value.filter(
    (meal) => !knownTypeSet.has(meal.meal_type),
  );
  if (unknownMeals.length > 0) {
    knownGroups.push({
      type: "UNKNOWN",
      label: "Other",
      meals: unknownMeals,
    });
  }

  return knownGroups;
});

async function fetchData() {
  loading.value = true;
  try {
    const { data: campData } = await mealsApiCampsGetCamp({
      path: { camp_id: campId },
    });
    if (campData) camp.value = campData;

    const { data: allMeals } = await mealsApiMealsListCampMeals({
      path: { camp_id: campId },
    });
    if (allMeals) {
      meals.value = allMeals.filter((m) => m.date === dateStr);
    }

    const { data: allRecipes } = await mealsApiRecipesListRecipes();
    if (allRecipes) recipes.value = allRecipes.items;

    for (const meal of meals.value) {
      if (!ingredientsMap.value[meal.recipe]) {
        const { data: ingData } = await mealsApiRecipesListRecipeIngredients({
          path: { recipe_id: meal.recipe },
        });
        if (ingData) {
          ingredientsMap.value[meal.recipe] = ingData;
        }
      }
    }
  } finally {
    loading.value = false;
  }
}

async function toggleMealDone(meal: CampMealSchema) {
  try {
    const { data } = await mealsApiMealsToggleCampMealDone({
      path: { camp_id: campId, meal_id: meal.id as string },
    });
    if (data) {
      meal.is_done = data.is_done;
    }
  } catch (e) {
    console.error(e);
  }
}

function getRecipe(id: string) {
  return recipes.value.find((r) => r.id === id);
}

function getScaledAmount(ri: RecipeIngredientSchema, meal: CampMealSchema) {
  const recipe = getRecipe(meal.recipe);
  if (!recipe || !recipe.default_portions) return ri.amount;
  const people =
    meal.override_people_count !== null
      ? meal.override_people_count
      : camp.value?.default_people_count || 4;
  if (!people) return ri.amount;
  return (ri.amount * people) / recipe.default_portions;
}

function exportPDF() {
  const element = document.getElementById("printable-content");
  if (!element) return;

  element.classList.add("exporting");
  const opt = {
    margin: 10,
    filename: `DayPlan_${dateStr}.pdf`,
    image: { type: "jpeg" as const, quality: 0.98 },
    html2canvas: { scale: 2 },
    jsPDF: { unit: "mm", format: "a4", orientation: "portrait" },
  } as const;
  html2pdf()
    .set(opt)
    .from(element)
    .save()
    .then(() => {
      element.classList.remove("exporting");
    });
}

function getSlotAnchor(type: string) {
  return `slot-${type.toLowerCase()}`;
}

function closeNav() {
  isNavOpen.value = false;
}

onMounted(fetchData);
</script>

<template>
  <div class="container page-container">
    <div class="page-header no-print mb-8">
      <div class="header-top">
        <button
          class="btn btn-secondary"
          @click="router.push(`/camps/${campId}`)"
        >
          &larr; {{ t("back") }}
        </button>
        <h2 v-if="camp" class="page-title">
          {{ camp.name }} -
          {{
            new Date(dateStr).toLocaleDateString(undefined, {
              weekday: "long",
              day: "numeric",
              month: "long",
            })
          }}
        </h2>
      </div>
      <div class="header-actions">
        <button
          v-if="groupedMeals.length > 0"
          class="btn btn-secondary quick-nav-toggle"
          @click="isNavOpen = true"
        >
          🕐 {{ t("slots") }}
        </button>
        <button class="btn btn-primary" @click="exportPDF">
          🖨 {{ t("btn.export_pdf") }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-8">
      <div class="text-mute">Loading daily details...</div>
    </div>

    <div v-else>
      <div
        v-if="groupedMeals.length > 0"
        class="drawer-backdrop no-print"
        :class="{ open: isNavOpen }"
        @click="closeNav"
      />

      <aside
        v-if="groupedMeals.length > 0"
        class="quick-nav-drawer no-print"
        :class="{ open: isNavOpen }"
      >
        <div class="drawer-header">
          <h3 class="mb-0">Quick Nav</h3>
          <button class="btn btn-secondary btn-sm" @click="closeNav">
            Close
          </button>
        </div>
        <nav>
          <ul class="quick-nav-list">
            <li v-for="group in groupedMeals" :key="`drawer-${group.type}`">
              <a
                class="quick-nav-link"
                :href="`#${getSlotAnchor(group.type)}`"
                @click="closeNav"
              >
                <span>{{ group.label }}</span>
                <span class="text-mute">{{ group.meals.length }}</span>
              </a>
            </li>
          </ul>
        </nav>
      </aside>

      <div class="day-layout">
        <div id="printable-content" class="flex-col gap-8 print-container">
          <div
            v-if="groupedMeals.length === 0"
            class="card text-center py-8 text-mute"
          >
            No meals scheduled for this day.
          </div>

          <section
            v-for="group in groupedMeals"
            :id="getSlotAnchor(group.type)"
            :key="group.type"
            class="slot-group"
          >
            <h2 class="slot-heading no-print">{{ group.label }}</h2>

            <div
              v-for="meal in group.meals"
              :key="meal.id as string"
              class="meal-section card"
              :class="{ 'meal-done': meal.is_done }"
            >
              <div class="flex justify-between items-end meal-header">
                <div>
                  <div class="flex items-center gap-2 no-print mb-2">
                    <div v-if="meal.is_done" class="badge badge-success">
                      ✓ {{ t("meal.cooked") }}
                    </div>
                  </div>
                  <div class="pt-2 mb-2 only-print d-inline">
                    {{ group.label }}
                  </div>
                  <h1 class="meal-title">{{ getRecipe(meal.recipe)?.name }}</h1>
                </div>
                <div class="flex flex-col items-end gap-2">
                  <button
                    class="btn btn-secondary no-print"
                    @click="toggleMealDone(meal)"
                  >
                    {{
                      meal.is_done
                        ? t("meal.mark_not_cooked")
                        : t("meal.mark_cooked")
                    }}
                  </button>
                  <div class="text-right">
                    <div class="meal-people-count">
                      {{
                        meal.override_people_count || camp?.default_people_count
                      }}
                      {{ t("dashboard.people") }}
                    </div>
                    <div v-if="meal.serves_preference" class="meal-preference">
                      {{ t("meal.serves_preference") }}:
                      {{ meal.serves_preference.name }}
                    </div>
                  </div>
                </div>
              </div>

              <div class="grid grid-cols-2 gap-8">
                <div>
                  <h3 class="section-heading">{{ t("recipe.ingredients") }}</h3>
                  <ul class="list-reset">
                    <li
                      v-for="ri in ingredientsMap[meal.recipe]"
                      :key="ri.id as number"
                      class="flex justify-between py-2 ingredient-row"
                    >
                      <span class="font-bold">{{ ri.ingredient.name }}</span>
                      <span class="text-mute"
                        >{{ Math.round(getScaledAmount(ri, meal) * 100) / 100 }}
                        {{ ri.unit }}</span
                      >
                    </li>
                    <li v-if="!ingredientsMap[meal.recipe]" class="text-mute">
                      No ingredients found.
                    </li>
                  </ul>
                </div>
                <div>
                  <h3 class="section-heading">
                    {{ t("recipe.instructions") }}
                  </h3>
                  <div class="instructions-text">
                    <MarkdownView
                      v-if="getRecipe(meal.recipe)?.instructions"
                      :content="getRecipe(meal.recipe)?.instructions"
                    />
                    <div v-else class="text-mute">
                      No instructions provided.
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </section>
        </div>

        <aside v-if="groupedMeals.length > 0" class="quick-nav card no-print">
          <h3 class="mb-2">Quick Nav</h3>
          <nav>
            <ul class="quick-nav-list">
              <li v-for="group in groupedMeals" :key="`desktop-${group.type}`">
                <a
                  class="quick-nav-link"
                  :href="`#${getSlotAnchor(group.type)}`"
                >
                  <span>{{ group.label }}</span>
                  <span class="text-mute">{{ group.meals.length }}</span>
                </a>
              </li>
            </ul>
          </nav>
        </aside>
      </div>
    </div>
  </div>
</template>

<style scoped>
.day-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 260px;
  gap: 1.5rem;
  align-items: start;
}

.print-container {
  width: 100%;
}

.header-top {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
  flex-wrap: wrap;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-top: 0.75rem;
}

.meal-section {
  page-break-inside: avoid;
  break-after: always;
  margin-bottom: 2rem;
  box-shadow: none;
  border: 1px solid var(--color-border);
}

.slot-group {
  margin-bottom: 2.5rem;
}

.slot-group:last-child .meal-section:last-child {
  break-after: auto;
}

.slot-heading {
  margin: 0 0 1rem;
  color: var(--color-text);
  border-bottom: 1px solid var(--color-border);
  padding-bottom: 0.5rem;
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

.exporting .only-print {
  display: inherit !important;
}

.exporting .no-print {
  display: none !important;
}

.exporting .meal-section {
  page-break-inside: avoid;
  border: none;
  padding: 0;
  margin: 0;
}

.exporting .meal-section:not(:last-child) {
  break-after: always;
}

@media print {
  .no-print {
    display: none;
  }
}

@media (max-width: 900px) {
  .day-layout {
    display: block;
  }

  .header-top {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.5rem;
  }

  .header-actions {
    margin-top: 0.5rem;
  }

  .grid-cols-2 {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .meal-header {
    align-items: flex-start;
    gap: 1rem;
  }

  .meal-header .text-right {
    text-align: left;
  }
}
</style>
