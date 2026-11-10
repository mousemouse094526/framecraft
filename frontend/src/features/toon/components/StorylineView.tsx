import chevronDownIcon from "../../../components/ui/assets/chevron-down.svg";
import plusIcon from "../../../components/ui/assets/plus.svg";
import trashIcon from "../../../components/ui/assets/trash.svg";
import { GHOST_BUTTON, OUTLINE_BUTTON } from "../../../components/ui/buttonStyles";
import mountainIcon from "../assets/mountain.svg";
import type { Act, Ep } from "../lib/episodes";
import { ACT_NAME_MAX, type Series } from "../lib/series";
import { CardEditor } from "./CardEditor";
import { CommitField } from "./CommitField";
import { LengthMeter } from "./LengthMeter";

type Edit = (method: string, path: string, body: unknown) => Promise<boolean>;

const NEW_ACT_NAME = "องก์ใหม่"; // D53: renamed in its header

/** เส้นเรื่อง: acts → segments (their background) → cards, the edits of each, and the
 * EP's length against its target (D9, D10, D14, D21). Closed while a job locks the EP. */
export function StorylineView({ ep, series, locked, edit }: { ep: Ep; series: Series; locked: boolean; edit: Edit }) {
  let number = 0;
  return (
    <>
      <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-border bg-card p-4">
        <LengthMeter seconds={ep.duration_s} />
      </div>
      {ep.acts.map((act, index) => (
        <section key={act.id} aria-label={`องก์ ${index + 1} ${act.name}`} className="flex flex-col gap-3">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs leading-[1.5] font-medium text-mid">องก์ {index + 1}</span>
            <CommitField
              required
              aria-label={`ชื่อองก์ ${index + 1}`}
              value={act.name}
              maxLength={ACT_NAME_MAX}
              disabled={locked}
              onCommit={(name) => edit("PATCH", `/acts/${act.id}`, { name })}
              className="min-w-0 flex-1 rounded-lg bg-transparent px-1 text-base leading-[1.5] font-semibold text-foreground hover:bg-card focus:bg-card"
            />
            <button
              type="button"
              disabled={locked || series.backgrounds.length === 0}
              onClick={() => void addSegment(edit, ep, act, series)}
              className={`h-8 px-3 ${GHOST_BUTTON}`}
            >
              <img src={plusIcon} alt="" width={16} height={16} />
              เพิ่มช่วง
            </button>
            <button
              type="button"
              aria-label={`ลบองก์ ${index + 1}`}
              disabled={locked}
              onClick={() => void edit("DELETE", `/acts/${act.id}`, undefined)}
              className="flex size-9 items-center justify-center rounded-lg hover:bg-card disabled:opacity-45"
            >
              <img src={trashIcon} alt="" width={16} height={16} />
            </button>
          </div>
          {act.segments.length === 0 && (
            <p className="rounded-xl bg-muted px-3 py-2.5 text-[13px] leading-[1.5] text-mid">
              องก์นี้ยังไม่มีการ์ด: เขียนสรุปในพล็อตแล้วแตกการ์ดใหม่ หรือเพิ่มช่วงเอง
            </p>
          )}
          {act.segments.map((segment, s) => (
            <div key={segment.id} className="flex flex-col gap-3">
              <div className="flex flex-wrap items-center gap-3 rounded-xl bg-muted px-3 py-2.5">
                <img src={mountainIcon} alt="" width={18} height={18} />
                <div className="flex min-w-0 flex-1 flex-col leading-[1.5]">
                  <span className="text-xs text-mid">ช่วง {s + 1} · ฉากหลัง</span>
                  <span className="relative flex items-center">
                    <select
                      aria-label={`ฉากหลังของช่วง ${s + 1}`}
                      value={segment.background_id}
                      disabled={locked}
                      onChange={(event) => void edit("PATCH", `/segments/${segment.id}`, { background_id: event.target.value })}
                      className="appearance-none bg-transparent pr-6 text-sm font-semibold text-foreground"
                    >
                      {series.backgrounds.map((background) => (
                        <option key={background.id} value={background.id}>
                          {background.name}
                        </option>
                      ))}
                    </select>
                    <img src={chevronDownIcon} alt="" width={16} height={16} className="pointer-events-none -ml-5" />
                  </span>
                </div>
              </div>
              {segment.cards.map((card) => {
                number += 1;
                return (
                  <CardEditor
                    key={card.id}
                    card={card}
                    number={number}
                    series={series}
                    locked={locked}
                    onChange={(body) => void edit("PATCH", `/cards/${card.id}`, body)}
                    onDelete={() => void edit("DELETE", `/cards/${card.id}`, undefined)}
                  />
                );
              })}
              <button
                type="button"
                disabled={locked}
                onClick={() => void edit("POST", "/cards", { segment_id: segment.id, text: "" })}
                className={`h-8 self-start px-3 ${GHOST_BUTTON}`}
              >
                <img src={plusIcon} alt="" width={16} height={16} />
                เพิ่มการ์ด
              </button>
            </div>
          ))}
        </section>
      ))}
      <button
        type="button"
        disabled={locked}
        onClick={() => void edit("POST", "/acts", { name: NEW_ACT_NAME })}
        className={`h-9 self-start px-4 ${OUTLINE_BUTTON}`}
      >
        <img src={plusIcon} alt="" width={16} height={16} />
        เพิ่มองก์
      </button>
    </>
  );
}

/** A segment at the end of the act, on the background of the act's last segment, else the plot's
 * first, else the Series' first; the user changes it in the segment's header. */
function addSegment(edit: Edit, ep: Ep, act: Act, series: Series) {
  const background =
    act.segments.at(-1)?.background_id ?? ep.plot.backgrounds.find((b) => b.id)?.id ?? series.backgrounds[0].id;
  return edit("POST", "/segments", { act_id: act.id, background_id: background });
}
