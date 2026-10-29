import { useId, useState, type FormEvent } from "react";
import { PRIMARY_BUTTON } from "../../../components/ui/buttonStyles";

type Props = {
  /** A job is unfinished: โหลด waits for it (D6). */
  busy: boolean;
  onSubmit: (url: string) => void;
};

export function LinkForm({ busy, onSubmit }: Props) {
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
          ลิงก์ YouTube
        </label>
        <input
          id={inputId}
          type="url"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          placeholder="https://www.youtube.com/watch?v=…"
          className="h-10 rounded-lg border border-border bg-card px-3 font-button text-sm leading-5 text-foreground placeholder:text-muted-foreground"
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
