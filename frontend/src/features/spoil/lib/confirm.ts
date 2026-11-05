/**
 * How posting a job ended: a refusal that asks the user to agree to a loss, its `kind` the
 * API's code and its `message` the question to show verbatim; or `handled` by the hook.
 */
export type StartResult<Loss extends string> = { kind: Loss; message: string } | { kind: "handled" };

export const HANDLED = { kind: "handled" } as const;

/**
 * Posts; while the API refuses with a loss to agree to, asks its message and posts again
 * with every loss agreed so far (spoil-maker D54, D49; spoil D37). Resolves false when the
 * user says no, true once the hook handled the answer.
 */
export async function postConfirming<Loss extends string>(
  post: (agreed: Loss[]) => Promise<StartResult<Loss>>,
): Promise<boolean> {
  const agreed: Loss[] = [];
  for (;;) {
    const result = await post(agreed);
    if (!("message" in result)) return true;
    if (!window.confirm(result.message)) return false;
    agreed.push(result.kind);
  }
}
