import { mount } from "@vue/test-utils";
import { describe, it, expect } from "vitest";
import GeneralItems from "../components/GeneralItems.vue";

describe("GeneralItems.vue", () => {
  const mockItems = [
    { id: "1", name: "Item 1", amount: "2x", category: "NON_FOOD" },
    { id: "2", name: "Item 2", amount: "1x", category: "NON_FOOD" },
  ];

  it("renders items when provided", () => {
    const wrapper = mount(GeneralItems, {
      props: { items: mockItems as any, canMove: true, isMoving: false },
    });
    expect(wrapper.text()).toContain("Item 1");
    expect(wrapper.text()).toContain("2x");
    expect(wrapper.text()).toContain("Item 2");
    expect(wrapper.text()).toContain("1x");
  });

  it("emits add event when add button is clicked with input", async () => {
    const wrapper = mount(GeneralItems, {
      props: { items: [], canMove: true, isMoving: false },
    });

    const inputs = wrapper.findAll("input");
    await inputs[0].setValue("New Item");
    await inputs[1].setValue("3x");
    await wrapper.find(".add-btn").trigger("click");

    expect(wrapper.emitted()).toHaveProperty("add");
    expect(wrapper.emitted("add")![0][0]).toEqual({
      name: "New Item",
      amount: "3x",
    });
  });

  it("emits delete event when delete button is clicked", async () => {
    const wrapper = mount(GeneralItems, {
      props: { items: mockItems as any, canMove: true, isMoving: false },
    });

    await wrapper.find(".delete-btn").trigger("click");
    expect(wrapper.emitted()).toHaveProperty("delete");
    expect(wrapper.emitted("delete")![0][0]).toBe("1");
  });

  it("renders empty message when no items", () => {
    const wrapper = mount(GeneralItems, {
      props: { items: [], canMove: true, isMoving: false },
    });
    expect(wrapper.text()).toContain("misc.no_data");
  });
});
