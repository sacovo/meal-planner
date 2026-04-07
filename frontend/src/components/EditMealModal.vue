<script setup lang="ts">
import { ref, watch } from "vue";
import type { CampMealSchema, DietaryPreferenceSchema } from "../client";
import { useI18n } from "../composables/useI18n";

const { t } = useI18n();

const props = defineProps<{
  show: boolean;
  meal: CampMealSchema | null;
  preferences: DietaryPreferenceSchema[];
  recipeName: string;
}>();

const emit = defineEmits<{
  (e: "update:show", val: boolean): void;
  (
    e: "save",
    data: { overridePeopleCount: number | null; preferenceId: number | null },
  ): void;
}>();

const localPeopleCount = ref<number | null>(null);
const localPreferenceId = ref<number | null>(null);

watch(
  () => props.meal,
  (newMeal) => {
    if (newMeal) {
      localPeopleCount.value = newMeal.override_people_count || null;
      localPreferenceId.value = newMeal.serves_preference?.id || null;
    }
  },
  { immediate: true },
);
</script>

<template>
  <div
    v-if="show && meal"
    class="modal-backdrop"
    @click="$emit('update:show', false)"
  >
    <div class="modal" @click.stop>
      <h3 class="modal-title">{{ t("edit_meal.title") }}</h3>
      <p class="text-mute subtitle">{{ recipeName }}</p>

      <div class="flex-col gap-4 modal-body">
        <div class="form-group">
          <label class="label">{{ t("edit_meal.people_count") }}</label>
          <input
            type="number"
            class="input"
            v-model="localPeopleCount"
            :placeholder="t('edit_meal.use_default')"
          />
        </div>
        <div class="form-group">
          <label class="label">{{ t("edit_meal.serves_preference") }}</label>
          <select class="input" v-model="localPreferenceId">
            <option :value="null">
              -- {{ t("planner.no_preference") }} --
            </option>
            <option
              v-for="pref in preferences"
              :key="pref.id!"
              :value="pref.id"
            >
              {{ pref.name }}
            </option>
          </select>
        </div>
        <div class="flex justify-end gap-2 footer">
          <button
            class="btn btn-secondary"
            @click="$emit('update:show', false)"
          >
            {{ t("btn.cancel") }}
          </button>
          <button
            class="btn btn-primary"
            @click="
              $emit('save', {
                overridePeopleCount: localPeopleCount,
                preferenceId: localPreferenceId,
              })
            "
          >
            {{ t("btn.save") }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-title {
  margin-bottom: 0.5rem;
}

.subtitle {
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.modal-body {
  margin-top: 1rem;
}

.form-group {
  margin-bottom: 1rem;
}

.label {
  display: block;
  margin-bottom: 0.25rem;
  font-weight: 500;
}

.footer {
  margin-top: 1rem;
}
</style>
