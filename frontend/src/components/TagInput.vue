<script setup lang="ts">
import { ref, computed } from "vue";

const props = defineProps<{
  modelValue: string[];
  suggestions: string[];
  placeholder?: string;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", value: string[]): void;
}>();

const query = ref("");
const showDropdown = ref(false);

const filteredSuggestions = computed(() => {
  const q = query.value.toLowerCase().trim();
  if (!q) return props.suggestions.filter((s) => !props.modelValue.includes(s));
  return props.suggestions.filter(
    (s) => s.toLowerCase().includes(q) && !props.modelValue.includes(s),
  );
});

function addTag(tag: string) {
  const trimmed = tag.trim();
  if (trimmed && !props.modelValue.includes(trimmed)) {
    emit("update:modelValue", [...props.modelValue, trimmed]);
  }
  query.value = "";
  showDropdown.value = false;
}

function removeTag(tag: string) {
  emit(
    "update:modelValue",
    props.modelValue.filter((t) => t !== tag),
  );
}

function onKeyDown(e: KeyboardEvent) {
  if (e.key === "Enter" || e.key === ",") {
    e.preventDefault();
    if (query.value) {
      addTag(query.value);
    }
  } else if (
    e.key === "Backspace" &&
    !query.value &&
    props.modelValue.length > 0
  ) {
    removeTag(props.modelValue[props.modelValue.length - 1]);
  }
}
function handleBlur() {
  setTimeout(() => {
    showDropdown.value = false;
  }, 200);
}
</script>

<template>
  <div class="tag-input-container">
    <div class="tag-input-box flex flex-wrap gap-1 items-center">
      <span v-for="tag in modelValue" :key="tag" class="tag-badge">
        {{ tag }}
        <button class="remove-btn" @click="removeTag(tag)">×</button>
      </span>
      <input
        type="text"
        class="tag-input-field"
        v-model="query"
        :placeholder="modelValue.length === 0 ? placeholder : ''"
        @focus="showDropdown = true"
        @blur="handleBlur"
        @keydown="onKeyDown"
        autocomplete="off"
      />
    </div>

    <ul
      v-if="showDropdown && filteredSuggestions.length > 0"
      class="tag-dropdown"
    >
      <li v-for="s in filteredSuggestions" :key="s" @click="addTag(s)">
        {{ s }}
      </li>
    </ul>
  </div>
</template>

<style scoped>
.tag-input-container {
  position: relative;
  width: 100%;
}
.tag-input-box {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 0.25rem 0.6rem;
  background: var(--color-bg-surface);
  min-height: 38px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
}
.tag-input-box:focus-within {
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-light);
}
.tag-badge {
  background: var(--color-primary);
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 0.8rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 4px;
}
.remove-btn {
  background: none;
  border: none;
  color: white;
  cursor: pointer;
  font-weight: bold;
  font-size: 1.1rem;
  padding: 0;
  line-height: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
.tag-input-field {
  border: none;
  outline: none;
  flex-grow: 1;
  background: transparent;
  min-width: 80px;
  font-size: 0.875rem;
  padding: 4px 0;
  color: var(--color-text-main);
}
.tag-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  width: 100%;
  background: var(--color-bg-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  margin-top: 4px;
  padding: 4px 0;
  list-style: none;
  z-index: 100;
  box-shadow: var(--shadow-lg);
  max-height: 200px;
  overflow-y: auto;
}
.tag-dropdown li {
  padding: 8px 12px;
  cursor: pointer;
  font-size: 0.875rem;
}
.tag-dropdown li:hover {
  background: var(--color-bg-mute);
  color: var(--color-primary);
}
</style>
