<script setup lang="ts">
import { computed } from "vue";
import { marked } from "marked";
import DOMPurify from "dompurify";

const props = defineProps<{
  content?: string | null;
}>();

const sanitizedHtml = computed(() => {
  if (!props.content) return "";

  // Configure marked for safe links and other options if needed
  const rawHtml = marked.parse(props.content) as string;

  // Sanitize the HTML to prevent XSS
  return DOMPurify.sanitize(rawHtml);
});
</script>

<template>
  <div class="markdown-body" v-html="sanitizedHtml"></div>
</template>

<style scoped>
.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  margin-top: 1.5rem;
  margin-bottom: 1rem;
  font-weight: 600;
  line-height: 1.25;
}

.markdown-body :deep(h1) {
  font-size: 1.5rem;
}
.markdown-body :deep(h2) {
  font-size: 1.25rem;
}
.markdown-body :deep(h3) {
  font-size: 1.1rem;
}

.markdown-body :deep(p) {
  margin-bottom: 1rem;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  margin-bottom: 1rem;
  padding-left: 2rem;
}

.markdown-body :deep(li) {
  margin-bottom: 0.25rem;
}

.markdown-body :deep(code) {
  background-color: var(--color-bg-mute);
  padding: 0.2rem 0.4rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9em;
}

.markdown-body :deep(pre) {
  background-color: var(--color-bg-mute);
  padding: 1rem;
  border-radius: 8px;
  overflow-x: auto;
  margin-bottom: 1rem;
}

.markdown-body :deep(blockquote) {
  border-left: 4px solid var(--color-border);
  padding-left: 1rem;
  color: var(--color-text-mute);
  font-style: italic;
  margin-bottom: 1rem;
}

.markdown-body :deep(a) {
  color: var(--color-primary);
  text-decoration: underline;
}

.markdown-body :deep(img) {
  max-width: 100%;
}
</style>
