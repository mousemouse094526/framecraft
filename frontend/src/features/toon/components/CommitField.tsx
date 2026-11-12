import { useEffect, useState } from "react";

type Props = {
  value: string;
  onCommit: (value: string) => unknown;
  maxLength: number;
  disabled?: boolean;
  multiline?: boolean;
  /** Left empty, the field goes back to `value` instead of sending. */
  required?: boolean;
  className: string;
  "aria-label"?: string;
};

/**
 * A text field that sends its value when the user leaves it, and only when it changed: every
 * EP edit is one `PATCH` whose answer is the EP (spec › API). A new `value` from that answer
 * replaces what is typed.
 */
export function CommitField({ value, onCommit, multiline = false, required = false, ...field }: Props) {
  const [text, setText] = useState(value);
  useEffect(() => setText(value), [value]);
  const props = {
    ...field,
    value: text,
    onChange: (event: { target: { value: string } }) => setText(event.target.value),
    onBlur: () => {
      if (required && !text.trim()) setText(value);
      else if (text.trim() !== value) void onCommit(text.trim());
    },
  };
  return multiline ? <textarea rows={2} {...props} /> : <input type="text" {...props} />;
}
