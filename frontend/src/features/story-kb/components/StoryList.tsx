import { OUTLINE_BUTTON, PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import { OfflinePanel } from "../../../components/ui/OfflinePanel";
import { PageLayout } from "../../../components/ui/PageLayout";
import { RefreshButton } from "../../../components/ui/RefreshButton";
import plusIcon from "../../../components/ui/assets/plus.svg";
import bookOpenIcon from "../assets/book-open.svg";
import chevronRightIcon from "../assets/chevron-right.svg";
import plusWhiteIcon from "../assets/plus-white.svg";
import { useStories } from "../hooks/useStories";
import { editedAt } from "../lib/story";
import { NEW_STORY_HASH, storyHash, type StoryRow } from "../../../lib/stories";

/** Figma `คลังความรู้`: every Story, latest edit first, each a link to แก้ Story (D9). */
export function StoryList() {
  const { state, reload } = useStories();

  if (state.kind === "offline") {
    return (
      <PageLayout tab="stories" action={<RefreshButton onClick={reload} />}>
        <OfflinePanel />
      </PageLayout>
    );
  }

  return (
    <PageLayout tab="stories">
      <div className="flex items-center gap-3">
        <h2 className="min-w-0 flex-1 text-xl leading-[1.5] font-semibold text-foreground">คลังความรู้</h2>
        <a href={NEW_STORY_HASH} className={`flex h-11 items-center gap-2 px-4 sm:h-9 ${PRIMARY_BUTTON}`}>
          <img src={plusWhiteIcon} alt="" width={16} height={16} />
          เพิ่มเรื่อง
        </a>
      </div>
      <section
        aria-label="เรื่องทั้งหมด"
        aria-busy={state.kind === "loading"}
        className="flex flex-col overflow-hidden rounded-2xl border border-border bg-card"
      >
        <div className="flex items-center gap-2 px-4 py-3 leading-[1.5]">
          <h3 className="text-sm font-medium text-foreground">เรื่องทั้งหมด</h3>
          {state.kind === "result" && <span className="text-[13px] text-muted-foreground">{state.stories.length}</span>}
        </div>
        <div className="h-px bg-border" />
        {state.kind === "loading" ? (
          <Skeleton />
        ) : state.stories.length === 0 ? (
          <div className="flex flex-col items-center gap-3 px-4 py-12">
            <img src={bookOpenIcon} alt="" width={32} height={32} />
            <p className="text-sm leading-[1.5] text-mid">ยังไม่มีเรื่องในคลังความรู้</p>
            <a href={NEW_STORY_HASH} className={`h-11 px-4 sm:h-9 ${OUTLINE_BUTTON}`}>
              <img src={plusIcon} alt="" width={16} height={16} />
              เพิ่มเรื่อง
            </a>
          </div>
        ) : (
          <ul className="divide-y divide-border">
            {state.stories.map((story) => (
              <Row key={story.id} story={story} />
            ))}
          </ul>
        )}
      </section>
    </PageLayout>
  );
}

/** Figma `Story row`: the whole row opens the Story; "ใช้อยู่ {n} คลิป" only when a clip remembers it. */
function Row({ story }: { story: StoryRow }) {
  return (
    <li>
      <a href={storyHash(story.id)} className="flex items-center gap-3 py-3 pr-3 pl-4 hover:bg-muted">
        <div className="flex min-w-0 flex-1 flex-col gap-0.5 leading-[1.5]">
          <p className="truncate text-sm font-medium text-foreground">{story.title}</p>
          <p className="flex gap-1.5 truncate text-[13px] text-mid">
            <span>{story.characters} ตัวละคร</span>
            <span className="text-muted-foreground">·</span>
            <span>แก้ล่าสุด {editedAt(story.updated_at)}</span>
          </p>
        </div>
        {story.clips > 0 && (
          <span className="shrink-0 rounded-full bg-muted px-2 py-0.5 font-button text-xs leading-4 font-medium whitespace-nowrap text-brand">
            ใช้อยู่ {story.clips} คลิป
          </span>
        )}
        <img src={chevronRightIcon} alt="" width={20} height={20} className="shrink-0" />
      </a>
    </li>
  );
}

/** Figma `Story list (aria-busy)`: three grey bars of rows while the list loads. */
function Skeleton() {
  return (
    <div className="divide-y divide-border">
      {["w-[200px]", "w-[140px]", "w-[200px]"].map((width, index) => (
        <div key={index} className="flex h-[60px] flex-col justify-center gap-2 px-4">
          <div className={`h-3.5 rounded-full bg-muted ${width}`} />
          <div className="h-2.5 w-[120px] rounded-full bg-muted" />
        </div>
      ))}
    </div>
  );
}
