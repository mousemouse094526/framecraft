import type { Refused } from "../../lib/refused";
import { Alert } from "./Alert";
import { FixCommand } from "./FixCommand";

/** A request the API refused: its line and, for a `not_ready` or `model_broken`, the Setup commands that fix it (ADR 0009). */
export function RefusedAlert({ refused }: { refused: Refused }) {
  return (
    <Alert tone={refused.tone}>
      <div className="flex flex-col gap-2">
        <p>{refused.text}</p>
        {refused.fixes.map((fix) => (
          <FixCommand key={fix} command={fix} />
        ))}
      </div>
    </Alert>
  );
}
