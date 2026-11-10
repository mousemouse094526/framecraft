import { screen, within } from "@testing-library/react";

/** The `Alert` (role `status`) that shows `text`, once it shows: a test reads its tone or what else it holds. */
export async function findStatusWith(text: string): Promise<HTMLElement> {
  await screen.findByText(text);
  const box = screen.getAllByRole("status").find((status) => within(status).queryByText(text));
  if (!box) throw new Error(`no status box shows ${text}`);
  return box;
}
