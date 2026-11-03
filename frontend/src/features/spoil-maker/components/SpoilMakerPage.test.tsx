import { render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it } from "vitest";
import { SpoilMakerPage } from "./SpoilMakerPage";

afterEach(() => {
  window.location.hash = "";
});

function steps() {
  return screen.getByRole("navigation", { name: "ขั้นของสปอย" });
}

function current() {
  return within(steps()).getByText((_, element) => element?.getAttribute("aria-current") === "step");
}

describe("Spoil steps (spoil-maker D53)", () => {
  it.each([
    ["#/spoil", "1", "เลือกคลิป"],
    ["#/spoil/review", "2", "ตรวจแก้บท"],
    ["#/spoil/renders", "3", "ผล render"],
  ])("%s highlights step %s %s", (hash, number, name) => {
    window.location.hash = hash;
    render(<SpoilMakerPage />);

    expect(current()).toHaveTextContent(`${number}${name}`);
  });

  it("opens step 1 on a #/spoil/ hash it doesn't know", () => {
    window.location.hash = "#/spoil/nope";
    render(<SpoilMakerPage />);

    expect(current()).toHaveTextContent("เลือกคลิป");
  });

  it("marks the steps before the current one as passed", () => {
    window.location.hash = "#/spoil/renders";
    render(<SpoilMakerPage />);

    expect(within(steps()).getAllByRole("img", { name: "ผ่านแล้ว" })).toHaveLength(2);
  });

  it("moves to a step by its link, which changes the hash", async () => {
    window.location.hash = "#/spoil";
    const user = userEvent.setup();
    render(<SpoilMakerPage />);

    await user.click(within(steps()).getByRole("link", { name: /ตรวจแก้บท/ }));

    expect(window.location.hash).toBe("#/spoil/review");
    await waitFor(() => expect(current()).toHaveTextContent("ตรวจแก้บท"));
    expect(within(steps()).getByRole("link", { name: /เลือกคลิป/ })).toHaveAttribute("href", "#/spoil");
    expect(within(steps()).getByRole("link", { name: /ผล render/ })).toHaveAttribute("href", "#/spoil/renders");
  });
});
