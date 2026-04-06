import { ref, readonly } from 'vue'

const texts = ref<Record<string, string>>({})
const locale = ref<string>(localStorage.getItem('locale') || 'de')
const loaded = ref(false)

export function useI18n() {
  function t(key: string, fallback?: string): string {
    return texts.value[key] || fallback || key
  }

  async function loadTexts() {
    try {
      const res = await fetch(`/api/content/texts/?lang=${locale.value}`)
      if (res.ok) {
        texts.value = await res.json()
      }
    } catch (err) {
      console.error('Failed to load UI texts:', err)
    }
    loaded.value = true
  }

  async function setLocale(lang: string) {
    locale.value = lang
    localStorage.setItem('locale', lang)
    // Set Django language cookie
    try {
      await fetch(`/api/set-language/?language=${lang}`)
    } catch (_) {}
    // Reload texts
    await loadTexts()
  }

  return {
    t,
    locale: readonly(locale),
    loaded: readonly(loaded),
    loadTexts,
    setLocale,
  }
}
