import { Alert } from "./Alert";
import { FixCommand } from "./FixCommand";

type Props = { tone?: "error" | "warning"; text: string; fixes: string[] };

/** A request the API refused: its line and, for a `not_ready` or `model_broken`, the Setup commands that fix it (ADR 0009). */
export function RefusedAlert({ tone = "error", text, fixes }: Props) {
  return (
    <Alert tone={tone}>
      <div className="flex flex-col gap-2">
        <p>{text}</p>
        {fixes.map((fix) => (
          <FixCommand key={fix} command={fix} />
        ))}
      </div>
    </Alert>
  );
}
