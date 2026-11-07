import { useEffect, useId, useRef, useState, type DragEvent, type ReactNode } from "react";
import fileVideoIcon from "../assets/file-video.svg";
import fileVideoOnDarkIcon from "../assets/file-video-on-dark.svg";
import uploadIcon from "../assets/upload.svg";
import uploadBrandIcon from "../assets/upload-brand.svg";

type Props = {
  /** The link form and what shows under it: a file dropped on them goes in too (spec › Frontend). */
  children: ReactNode;
  /** A download or an import is under way: one at a time (D52). */
  disabled: boolean;
  /** The message above says to pick the file yourself (D52): the box stands out. */
  emphasis: boolean;
  onFiles: (files: File[]) => void;
};

const HINT = "รับ mp4 (H.264, AAC) ไม่เกิน 1080p";

const isFileDrag = (event: DragEvent) => event.dataTransfer.types.includes("Files");

/**
 * The link form with Figma component `File drop` under it: เลือกไฟล์ในเครื่อง opens the file
 * dialog, and a file dragged onto any of it is imported the same way (D49, D50). The whole box
 * is one button, so the keyboard reaches it; its name is the words on it, the hint describes it (D58).
 */
export function FileDropArea({ children, disabled, emphasis, onFiles }: Props) {
  const input = useRef<HTMLInputElement>(null);
  const hintId = useId();
  // dragenter and dragleave fire for every child crossed: count them (docs/library-notes/web-platform.md).
  const [depth, setDepth] = useState(0);
  const look = lookOf(disabled, emphasis, depth > 0);

  // A file dropped beside the box would be opened by the browser, leaving the app mid-job.
  useEffect(() => {
    const blockStrayDrop = (event: globalThis.DragEvent) => {
      if (event.dataTransfer?.types.includes("Files")) event.preventDefault();
    };
    window.addEventListener("dragover", blockStrayDrop);
    window.addEventListener("drop", blockStrayDrop);
    return () => {
      window.removeEventListener("dragover", blockStrayDrop);
      window.removeEventListener("drop", blockStrayDrop);
    };
  }, []);

  const onDragOver = (event: DragEvent) => {
    if (!isFileDrag(event)) return;
    // Without this the drop never comes here.
    event.preventDefault();
    event.dataTransfer.dropEffect = disabled ? "none" : "copy";
  };
  const onDrop = (event: DragEvent) => {
    if (!isFileDrag(event)) return;
    event.preventDefault();
    setDepth(0);
    if (!disabled) onFiles(Array.from(event.dataTransfer.files));
  };

  return (
    <div
      className="flex flex-col gap-4"
      onDragEnter={(event) => isFileDrag(event) && setDepth((n) => n + 1)}
      onDragLeave={(event) => isFileDrag(event) && setDepth((n) => Math.max(0, n - 1))}
      onDragOver={onDragOver}
      onDrop={onDrop}
    >
      {children}
      <button
        type="button"
        onClick={() => input.current?.click()}
        disabled={disabled}
        aria-label="เลือกไฟล์ในเครื่อง"
        aria-describedby={hintId}
        data-emphasis={look === "emphasis" ? "true" : undefined}
        className={`flex w-full flex-col items-center gap-2 rounded-2xl px-4 py-5 ${BOX_LOOK[look]}`}
      >
        {look === "dragOver" ? (
          <>
            <img src={uploadBrandIcon} alt="" width={24} height={24} />
            <span className="text-sm leading-[1.5] font-medium text-brand">วางไฟล์ mp4 ที่นี่</span>
            <span id={hintId} className="text-center text-xs leading-[1.5] text-mid">
              {HINT}
            </span>
          </>
        ) : (
          <>
            <img src={uploadIcon} alt="" width={24} height={24} />
            <span className={`flex h-9 items-center justify-center gap-2 rounded-lg px-4 ${PICK_LOOK[look]}`}>
              <img src={look === "emphasis" ? fileVideoOnDarkIcon : fileVideoIcon} alt="" width={16} height={16} />
              <span className="font-button text-sm leading-5 font-medium">เลือกไฟล์ในเครื่อง</span>
            </span>
            <span
              id={hintId}
              className={`text-center text-xs leading-[1.5] ${look === "disabled" ? "text-muted-foreground" : "text-mid"}`}
            >
              หรือลากไฟล์ mp4 มาวาง · {HINT}
            </span>
          </>
        )}
      </button>
      <input
        ref={input}
        type="file"
        accept="video/mp4,.mp4"
        hidden
        tabIndex={-1}
        onChange={(event) => {
          const files = Array.from(event.target.files ?? []);
          // Empty again, so the same file can be picked once more after a refusal.
          event.target.value = "";
          if (files.length > 0) onFiles(files);
        }}
      />
    </div>
  );
}

/** The `File drop` states in Figma. */
type Look = "default" | "dragOver" | "disabled" | "emphasis";

function lookOf(disabled: boolean, emphasis: boolean, dragging: boolean): Look {
  if (disabled) return "disabled";
  if (dragging) return "dragOver";
  return emphasis ? "emphasis" : "default";
}

const BOX_LOOK: Record<Look, string> = {
  default: "border-[1.5px] border-dashed border-border bg-card hover:bg-muted",
  dragOver: "border-2 border-dashed border-brand-accent bg-accent-subtle",
  disabled: "border-[1.5px] border-dashed border-border-disabled bg-muted",
  emphasis: "border-2 border-brand-accent bg-card",
};

/** The `Pick file` button inside: outline, or primary while the box stands out. */
const PICK_LOOK: Record<Exclude<Look, "dragOver">, string> = {
  default: "border border-border bg-card text-foreground",
  disabled: "border border-border bg-card text-foreground opacity-50",
  emphasis: "bg-brand text-card",
};
