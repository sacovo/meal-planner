import { mount } from "@vue/test-utils";
import { describe, it, expect } from "vitest";
import RecipeSidebar from "../components/RecipeSidebar.vue";
import { vi } from "vitest";

vi.mock("../client", () => ({
  mealsApiRecipesListRecipes: vi.fn((args) => {
    const query = args?.query?.q?.toLowerCase() || "";
    const allItems = [
      { id: "1", name: "Recipe 1", default_portions: 4, preferences: [] },
      {
        id: "2",
        name: "Recipe 2",
        default_portions: 2,
        preferences: [{ id: 1, name: "Vegan" }],
      },
    ];
    const items = allItems.filter((i) => i.name.toLowerCase().includes(query));
    return Promise.resolve({ data: { items, count: items.length } });
  }),
}));

describe("RecipeSidebar.vue", () => {
  it("renders recipes when not collapsed", async () => {
    const wrapper = mount(RecipeSidebar, {
      props: {
        searchQuery: "",
        isCollapsed: false,
        preferences: [],
        allTags: [],
      },
    });
    await vi.dynamicImportSettled();
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(wrapper.text()).toContain("Recipe 1");
    expect(wrapper.text()).toContain("Recipe 2");
    expect(wrapper.text()).toContain("Vegan");
  });

  it("filters recipes based on search query", async () => {
    const wrapper = mount(RecipeSidebar, {
      props: {
        searchQuery: "Recipe 1",
        isCollapsed: false,
        preferences: [],
        allTags: [],
      },
    });
    await vi.dynamicImportSettled();
    await new Promise((resolve) => setTimeout(resolve, 0));

    expect(wrapper.text()).toContain("Recipe 1");
    expect(wrapper.text()).not.toContain("Recipe 2");
  });

  it("emits update:isCollapsed when toggle button is clicked", async () => {
    const wrapper = mount(RecipeSidebar, {
      props: {
        searchQuery: "",
        isCollapsed: false,
        preferences: [],
        allTags: [],
      },
    });
    await wrapper.find(".toggle-sidebar-btn").trigger("click");
    expect(wrapper.emitted("update:isCollapsed")).toBeTruthy();
    expect(wrapper.emitted("update:isCollapsed")![0][0]).toBe(true);
  });

  it("emits dragstart when recipe is dragged", async () => {
    const wrapper = mount(RecipeSidebar, {
      props: {
        searchQuery: "",
        isCollapsed: false,
        preferences: [],
        allTags: [],
      },
    });
    await vi.dynamicImportSettled();
    await new Promise((resolve) => setTimeout(resolve, 0));

    const firstRecipe = wrapper.find(".recipe-draggable");
    await firstRecipe.trigger("dragstart");
    expect(wrapper.emitted("dragstart")).toBeTruthy();
  });

  it("shows vertical text when collapsed", () => {
    const wrapper = mount(RecipeSidebar, {
      props: {
        searchQuery: "",
        isCollapsed: true,
        preferences: [],
        allTags: [],
      },
    });
    expect(wrapper.find(".vertical-text").exists()).toBe(true);
    expect(wrapper.find(".content").isVisible()).toBe(false);
  });
});
