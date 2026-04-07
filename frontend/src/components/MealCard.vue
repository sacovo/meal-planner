<script setup lang="ts">
import type { CampMealSchema, CampSchema } from "../client";
import { useI18n } from "../composables/useI18n";

const { t } = useI18n();

const props = defineProps<{
  meal: CampMealSchema;
  camp: CampSchema;
  recipeName: string;
  isSelected: boolean;
}>();

const emit = defineEmits<{
  (e: "update:isSelected", val: boolean): void;
  (e: "edit"): void;
  (e: "toggle-done"): void;
  (e: "remove"): void;
}>();
</script>

<template>
  <div
    class="allocated-meal flex-col"
    :class="{ 'meal-done': meal.is_done }"
    @click="$emit('edit')"
  >
    <div class="flex justify-between items-center w-full">
      <label class="flex items-center gap-1 selection-label" @click.stop>
        <input
          type="checkbox"
          :checked="isSelected"
          @change="
            $emit(
              'update:isSelected',
              ($event.target as HTMLInputElement).checked,
            )
          "
          class="checkbox"
        />
        <span class="recipe-name" :title="recipeName">
          {{ recipeName }}
        </span>
      </label>
      <div class="flex items-center gap-1 controls">
        <button
          class="btn-icon done-btn"
          @click.stop="$emit('toggle-done')"
          :title="
            meal.is_done ? t('meal.mark_not_cooked') : t('meal.mark_cooked')
          "
        >
          {{ meal.is_done ? "✅" : "🍳" }}
        </button>
        <button class="remove-btn" @click.stop="$emit('remove')">✕</button>
      </div>
    </div>

    <div class="flex justify-between items-center text-mute info-row">
      <span v-if="meal.override_people_count !== null"
        >{{ meal.override_people_count }} {{ t("misc.people") }}</span
      >
      <span v-else>{{ camp.default_people_count }} {{ t("misc.people") }}</span>

      <span v-if="meal.serves_preference" class="preference-tag">
        ({{ meal.serves_preference.name }})
      </span>
    </div>
  </div>
</template>

<style scoped>
.allocated-meal {
  background: var(--color-bg-mute);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 0.25rem 0.5rem;
  margin-bottom: 0.25rem;
  font-size: 0.9rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.02);
  cursor: pointer;
}

.allocated-meal:last-child {
  margin-bottom: 0;
}

.meal-done {
  opacity: 0.7;
}

.selection-label {
  font-size: 0.85rem;
  padding: 2px;
  cursor: pointer;
}

.checkbox {
  width: 12px;
  height: 12px;
}

.recipe-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  max-width: 130px;
}

.controls {
  gap: 0.25rem;
}

.btn-icon {
  background: none;
  border: none;
  cursor: pointer;
  padding: 0 2px;
  font-size: 0.7rem;
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

.info-row {
  font-size: 0.7rem;
  margin-top: 2px;
  padding-left: 18px;
}

.preference-tag {
  color: var(--color-primary);
  font-weight: bold;
}
</style>
