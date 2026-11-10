import mountain16Icon from "../assets/mountain-16.svg";
import mountainIcon from "../assets/mountain.svg";
import users16Icon from "../assets/users-16.svg";
import usersIcon from "../assets/users.svg";
import type { ItemKind } from "./series";

/** The dialog เอาไฟล์เข้า shows before the file picker opens; null: the picker opens at once. */
type FileNotice = { title: string; message: string } | null;

type KindLook = {
  /** The kind's name, e.g. the list's heading. */
  name: string;
  /** 24 px and 16 px. */
  icon: string;
  icon16: string;
  /** The list's add button, its empty line, and the new item form's label. */
  add: string;
  empty: string;
  form: string;
  /** Only a character has a tag (spec › Series ตัวละคร ฉากหลัง). */
  tagged: boolean;
  /** The Tailwind classes of the reference image's box: on a tile of ตัวละครและฉากหลัง, and on เลือกภาพอ้างอิง. */
  tileSlot: string;
  pickSlot: string;
  fileNotice: FileNotice;
};

/** How a character or a background shows on every page: a character's picture box is square, a
 * background's 16:9 (Figma toon / 3, 4); a character's file asks first (legal item 2, spec › Frontend). */
export const ITEM_KINDS: Record<ItemKind, KindLook> = {
  characters: {
    name: "ตัวละคร",
    icon: usersIcon,
    icon16: users16Icon,
    add: "เพิ่มตัวละคร",
    empty: "ยังไม่มีตัวละคร",
    form: "ตัวละครใหม่",
    tagged: true,
    tileSlot: "size-[264px]",
    pickSlot: "aspect-square w-full sm:size-[300px]",
    fileNotice: {
      title: "ก่อนเอาไฟล์ภาพตัวละครเข้า",
      message: "ใช้ภาพหรือตัวละครที่คุณวาดเองหรือได้รับอนุญาต และอย่าใช้ภาพคนจริงในเรื่องที่ทำให้เขาเสียชื่อเสียง",
    },
  },
  backgrounds: {
    name: "ฉากหลัง",
    icon: mountainIcon,
    icon16: mountain16Icon,
    add: "เพิ่มฉากหลัง",
    empty: "ยังไม่มีฉากหลัง",
    form: "ฉากหลังใหม่",
    tagged: false,
    tileSlot: "h-[148px] w-[264px]",
    pickSlot: "aspect-video w-full sm:w-[300px]",
    fileNotice: null,
  },
};
