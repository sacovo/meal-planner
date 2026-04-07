import { afterEach, vi } from "vitest";

vi.mock("@/composables/useI18n", () => ({
  useI18n: () => ({
    t: (key: string, fallback?: string) => fallback || key,
    locale: { value: "de" },
    loaded: { value: true },
    loadTexts: vi.fn(),
    setLocale: vi.fn(),
  }),
}));

afterEach(() => {
  vi.clearAllMocks();
});
