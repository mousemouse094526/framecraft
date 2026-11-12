import { useId, useState, type FormEvent } from "react";
import { PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";

type Props = {
  /** A job is unfinished: โหลด waits for it (D6). */
  busy: boolean;
  /**
   * A file is being imported: the field waits too (spec › Frontend, เอาไฟล์เข้า). While a link
   * downloads the field stays open, so the next link can be pasted ready (D6).
   */
  locked?: boolean;
  onSubmit: (url: string) => void;
};

export function LinkForm({ busy, locked = false, onSubmit }: Props) {
  const [url, setUrl] = useState("");
  const inputId = useId();

  const submit = (event: FormEvent) => {
    event.preventDefault();
    onSubmit(url);
  };

  return (
    <form onSubmit={submit} className="flex items-end gap-3">
      <div className="flex min-w-0 flex-1 flex-col gap-2">
        <label htmlFor={inputId} className="font-button text-sm leading-5 font-medium text-foreground">
          ลิงก์คลิป
        </label>
        <input
          id={inputId}
          type="url"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          disabled={locked}
          placeholder="วางลิงก์คลิป (YouTube, Facebook, TikTok …)"
          className="h-10 rounded-lg border border-border bg-card px-3 font-button text-sm leading-5 text-foreground placeholder:text-muted-foreground disabled:bg-muted"
        />
      </div>
      <button
        type="submit"
        disabled={busy}
        className={`h-10 px-6 ${PRIMARY_BUTTON}`}
      >
        โหลด
      </button>
    </form>
  );
}
