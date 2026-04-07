<script setup lang="ts">
import { useI18n } from "@/composables/useI18n";
import { ref, watch } from "vue";

const props = defineProps<{
  show: boolean;
  campData: { name: string; default_people_count: number; notes: string };
}>();

const { t } = useI18n();

const emit = defineEmits<{
  (e: "update:show", val: boolean): void;
  (
    e: "save",
    data: { name: string; default_people_count: number; notes: string },
  ): void;
}>();

const localData = ref({ ...props.campData });

watch(
  () => props.campData,
  (newVal) => {
    localData.value = { ...newVal };
  },
  { deep: true },
);
</script>

<template>
  <div v-if="show" class="modal-backdrop" @click="$emit('update:show', false)">
    <div class="modal" @click.stop>
      <h3 class="modal-title">{{ t("btn.edit") }}</h3>

      <div class="flex-col gap-4 modal-body">
        <div class="form-group">
          <label class="label">{{ t("camp.name_label") }}</label>
          <input type="text" class="input" v-model="localData.name" />
        </div>
        <div class="form-group">
          <label class="label">{{ t("camp.people_count_label") }}</label>
          <input
            type="number"
            class="input"
            v-model="localData.default_people_count"
          />
        </div>
        <div class="form-group">
          <label class="label">{{ t("camp.notes_label") }}</label>
          <textarea
            class="input notes-area"
            v-model="localData.notes"
            rows="6"
            :placeholder="t('camp.notes_placeholder')"
          ></textarea>
        </div>

        <div class="flex justify-end gap-2 footer">
          <button
            class="btn btn-secondary"
            @click="$emit('update:show', false)"
          >
            {{ t("btn.cancel") }}
          </button>
          <button class="btn btn-primary" @click="$emit('save', localData)">
            {{ t("btn.save") }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.modal-title {
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

.notes-area {
  resize: vertical;
}

.footer {
  margin-top: 1rem;
}
</style>
