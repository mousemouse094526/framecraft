import mountain16Icon from "../assets/mountain-16.svg";
import mountainIcon from "../assets/mountain.svg";
import users16Icon from "../assets/users-16.svg";
import usersIcon from "../assets/users.svg";
import type { ItemKind } from "./series";

/** How a character or a background shows on every page: its name and its icon (24 px, 16 px). */
export const ITEM_KINDS: Record<ItemKind, { name: string; icon: string; icon16: string }> = {
  characters: { name: "ตัวละคร", icon: usersIcon, icon16: users16Icon },
  backgrounds: { name: "ฉากหลัง", icon: mountainIcon, icon16: mountain16Icon },
};
