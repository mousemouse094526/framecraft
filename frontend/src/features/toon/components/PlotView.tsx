import { PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";
import chevronDownIcon from "../../../components/ui/assets/chevron-down.svg";
import checkIcon from "../assets/check.svg";
import mountainIcon from "../assets/mountain.svg";
import usersIcon from "../assets/users.svg";
import wandWhiteIcon from "../assets/wand-white.svg";
import { actsToSplit, SUMMARY_MAX, TITLE_MAX, type Ep, type LostCards, type PlotItem } from "../lib/episodes";
import type { ItemKind, Series } from "../lib/series";
import { CommitField } from "./CommitField";
import { ToonDialog } from "./ToonDialog";

type Edit = (method: string, path: string, body: unknown) => Promise<boolean>;

type Props = {
  ep: Ep;
  series: Series;
  /** A Plot or Cards job writes this EP: every field is closed. */
  locked: boolean;
  /** Any Toon job runs: no new one starts. */
  busy: boolean;
  lost: LostCards[] | null;
  edit: Edit;
  onDraft: () => void;
  onSplit: (confirmLoss: boolean) => void;
  onCloseLost: () => void;
};

/** พล็อต: the title, a summary per act, the cast it uses (new or of the Series), and the
 * confirm that splits it into cards, or splits again the acts whose summary changed (D12–D15, D24, D43). */
export function PlotView({ ep, series, locked, busy, lost, edit, onDraft, onSplit, onCloseLost }: Props) {
  const written = ep.title !== "" || ep.acts.some((act) => act.summary !== "");
  if (!written && !locked) {
    return (
      <div className="flex flex-col items-center gap-3 rounded-2xl border border-border bg-card p-10 text-center">
        <p className="text-base leading-[1.5] font-medium text-foreground">ยังไม่มีพล็อต</p>
        <p className="text-[13px] leading-[1.5] text-mid">ไอเดีย: {ep.idea}</p>
        <button type="button" disabled={busy} onClick={onDraft} className={`flex h-9 items-center gap-2 px-4 ${PRIMARY_BUTTON}`}>
          <img src={wandWhiteIcon} alt="" width={16} height={16} />
          ให้ AI ร่างพล็อต
        </button>
      </div>
    );
  }

  const toSplit = actsToSplit(ep);
  const confirmed = ep.stage === "cards";

  return (
    <section aria-label="พล็อต" aria-busy={locked} className="flex flex-col gap-5 rounded-2xl border border-border bg-card p-6">
      <label className="flex flex-col gap-2">
        <span className="font-button text-sm leading-5 font-medium text-foreground">ชื่อตอน</span>
        <CommitField
          value={ep.title}
          maxLength={TITLE_MAX}
          disabled={locked}
          onCommit={(title) => edit("PATCH", "", { title })}
          className="h-10 rounded-lg border border-border bg-card px-3 text-sm text-foreground"
        />
      </label>
      <div className="flex flex-col gap-4">
        {ep.acts.map((act, index) => (
          <label key={act.id} className="flex flex-col gap-1.5">
            <span className="flex items-center gap-2 leading-[1.5]">
              <span className="font-mono text-xs font-medium text-mid">องก์ {index + 1}</span>
              <span className="text-sm font-medium text-foreground">{act.name}</span>
            </span>
            <CommitField
              multiline
              value={act.summary}
              maxLength={SUMMARY_MAX}
              disabled={locked}
              onCommit={(summary) => edit("PATCH", `/acts/${act.id}`, { summary })}
              className="rounded-lg border border-border bg-card px-3 py-2.5 text-sm leading-[1.5] text-foreground"
            />
          </label>
        ))}
      </div>
      <PlotCast ep={ep} series={series} locked={locked} edit={edit} />
      <hr className="border-border" />
      {confirmed && toSplit.length > 0 && (
        <div className="flex flex-col gap-1.5 rounded-xl bg-warning-surface px-3 py-2.5 leading-[1.5]">
          <p className="text-sm font-medium text-foreground">องก์ที่จะแตกการ์ดใหม่</p>
          {toSplit.map((act) => (
            <p key={act.id} className="text-[13px] text-mid">
              • องก์ {ep.acts.indexOf(act) + 1} {act.name}
            </p>
          ))}
        </div>
      )}
      <div className="flex justify-end">
        <button
          type="button"
          disabled={locked || busy || (confirmed && toSplit.length === 0)}
          onClick={() => onSplit(false)}
          className={`flex h-9 items-center gap-2 px-4 ${PRIMARY_BUTTON}`}
        >
          <img src={checkIcon} alt="" width={16} height={16} />
          {confirmed ? "แตกการ์ดใหม่" : "ยืนยันพล็อต"}
        </button>
      </div>
      {lost && (
        <ToonDialog
          title={`แตกการ์ดใหม่ ${lost.length} องก์?`}
          message={lostLines(ep, lost)}
          confirmLabel="แตกการ์ดใหม่"
          destructive
          onClose={onCloseLost}
          onConfirm={() => onSplit(true)}
        />
      )}
    </section>
  );
}

/** One line per act to split with what it loses, then the acts that stay (D43). */
function lostLines(ep: Ep, lost: LostCards[]): string[] {
  const number = (id: string) => ep.acts.findIndex((act) => act.id === id) + 1;
  const lines = lost.map(
    (act) => `องก์ ${number(act.id)} ${act.name}: การ์ดแก้เอง ${act.edited} ใบ ภาพ ${act.images} ภาพ เสียง ${act.audio} เสียง จะหาย`,
  );
  const kept = ep.acts.filter((act) => !lost.some((l) => l.id === act.id)).map((act) => number(act.id));
  if (kept.length > 0) lines.push(`องก์ ${kept.join(", ")} ไม่เปลี่ยน`);
  return lines;
}

/** ตัวละครและฉากหลังที่พล็อตใช้: a new one can switch to one of the Series' instead (D13). */
function PlotCast({ ep, series, locked, edit }: { ep: Ep; series: Series; locked: boolean; edit: Edit }) {
  const switchTo = (kind: ItemKind, index: number, id: string) => {
    const items = ep.plot[kind].map((item, i) => (i === index ? { id } : asBody(item)));
    void edit("PATCH", "", { plot: { ...plotBody(ep), [kind]: items } });
  };
  return (
    <div className="flex flex-col gap-2">
      <p className="text-sm leading-[1.5] font-medium text-foreground">ตัวละครและฉากหลังที่พล็อตใช้</p>
      {(["characters", "backgrounds"] as const).map((kind) =>
        ep.plot[kind].map((item, index) => {
          const own = item.id ? series[kind].find((s) => s.id === item.id) : undefined;
          const name = own?.name ?? item.name;
          const others = series[kind].filter((s) => !ep.plot[kind].some((p) => p.id === s.id));
          return (
            <div key={`${kind}-${item.id ?? index}`} className="flex flex-wrap items-center gap-3 rounded-xl bg-muted px-3 py-2.5">
              <img src={kind === "characters" ? usersIcon : mountainIcon} alt="" width={18} height={18} />
              <span className="text-sm leading-[1.5] font-medium text-foreground">{name}</span>
              {item.new ? (
                <span className="rounded-full bg-accent-subtle px-2 py-0.5 font-button text-xs leading-4 font-medium text-link">ใหม่</span>
              ) : (
                <span className="rounded-full bg-card px-2 py-0.5 font-button text-xs leading-4 font-medium text-brand">ในชุด</span>
              )}
              <span className="flex-1" />
              {item.new && others.length > 0 && (
                <span className="relative flex h-9 w-60 items-center">
                  <select
                    aria-label={`ใช้ของในชุดแทน ${name}`}
                    value=""
                    disabled={locked}
                    onChange={(event) => switchTo(kind, index, event.target.value)}
                    className="h-9 w-full appearance-none rounded-lg border border-border bg-card px-3 pr-8 text-sm text-foreground"
                  >
                    <option value="">สร้างใหม่ในชุด</option>
                    {others.map((other) => (
                      <option key={other.id} value={other.id}>
                        ใช้ {other.name} แทน
                      </option>
                    ))}
                  </select>
                  <img src={chevronDownIcon} alt="" width={16} height={16} className="pointer-events-none absolute right-3" />
                </span>
              )}
            </div>
          );
        }),
      )}
    </div>
  );
}

function asBody(item: PlotItem) {
  return item.id ? { id: item.id } : { name: item.name, tag: item.tag, description: item.description };
}

function plotBody(ep: Ep) {
  return { characters: ep.plot.characters.map(asBody), backgrounds: ep.plot.backgrounds.map(asBody) };
}
