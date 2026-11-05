import { useId } from "react";
import { Alert } from "../../../components/ui/Alert";
import { NEW_STORY_HASH, storyHash, type StoryRow } from "../../../lib/stories";
import chevronDownIcon from "../assets/chevron-down.svg";
import externalLinkIcon from "../assets/external-link.svg";

const NONE = "";
const LABEL = "เรื่องในคลังความรู้";
const NEW_TAB_LINK = "flex h-8 items-center gap-2 rounded-lg px-3 font-button text-sm leading-5 font-medium text-brand hover:underline";

type Props = {
  /** Sorted by title by the caller (`readStories`); "ไม่ใช้" comes first here (story-kb spec › Design). */
  stories: StoryRow[];
  /** The picked Story, null for ไม่ใช้. */
  storyId: string | null;
  /** While a draft runs: its order's Story title, or ไม่ใช้, as text (spoil-maker D82); null otherwise. */
  lockedText: string | null;
  /** The picked Story was gone when ร่างบท sent it (`story_not_found`). */
  gone: boolean;
  onChange: (storyId: string | null) => void;
};

/** Figma component `Story picker` of ตั้งค่าคลิปสปอย: the Story the clip's draft uses (story-kb D3, D15, D16). */
export function StoryPicker({ stories, storyId, lockedText, gone, onChange }: Props) {
  const fieldId = useId();
  return (
    <section aria-label={LABEL} className="flex flex-col gap-3 rounded-2xl border border-border bg-card p-4 lg:w-[560px] lg:shrink-0">
      {lockedText !== null ? (
        <div className="flex flex-col gap-1 text-sm leading-[1.5] text-foreground">
          <p className="font-medium">{LABEL}</p>
          <p>{lockedText}</p>
        </div>
      ) : (
        <>
          {gone && <Alert tone="error">ไม่พบเรื่องนี้ในคลังความรู้แล้ว</Alert>}
          <div className="flex flex-col gap-1.5">
            <div className="flex flex-col gap-2">
              <label htmlFor={fieldId} className="font-button text-sm leading-5 font-medium text-foreground">
                {LABEL}
              </label>
              <div className="relative">
                <select
                  id={fieldId}
                  value={storyId ?? NONE}
                  onChange={(event) => onChange(event.target.value === NONE ? null : event.target.value)}
                  className="h-10 w-full appearance-none rounded-lg border border-border bg-card px-3 pr-9 font-button text-sm leading-5 text-foreground"
                >
                  <option value={NONE}>ไม่ใช้</option>
                  {stories.map((story) => (
                    <option key={story.id} value={story.id}>
                      {story.title}
                    </option>
                  ))}
                </select>
                <img src={chevronDownIcon} alt="" width={16} height={16} className="pointer-events-none absolute top-3 right-3" />
              </div>
            </div>
            <p className="text-xs leading-[1.5] text-muted-foreground">จำให้คลิปนี้ทุก EP เมื่อกดร่างบท</p>
            <div className="flex flex-wrap gap-x-4">
              {storyId !== null && <NewTabLink href={storyHash(storyId)}>แก้เรื่องนี้</NewTabLink>}
              <NewTabLink href={NEW_STORY_HASH}>เพิ่มเรื่องในคลังความรู้</NewTabLink>
            </div>
          </div>
        </>
      )}
    </section>
  );
}

/** คลังความรู้ in a new browser tab: what is set here stays as it is (story-kb D16). */
function NewTabLink({ href, children }: { href: string; children: string }) {
  return (
    <a href={href} target="_blank" rel="noopener noreferrer" className={NEW_TAB_LINK}>
      <img src={externalLinkIcon} alt="" width={16} height={16} />
      {children}
    </a>
  );
}
