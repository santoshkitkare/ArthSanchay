import { useEffect, useState } from "react";
import { useController, type Control, type FieldPath, type FieldValues } from "react-hook-form";
import { formatPercent, parsePercentInput } from "../../lib/money";

interface Props<T extends FieldValues> {
  control: Control<T>;
  name: FieldPath<T>;
  label: string;
  help?: string;
  error?: string;
}

/** Accepts "7" or "7%" and stores the decimal fraction ("0.07") in form state (PRD.md §8.2). */
export function PercentField<T extends FieldValues>({ control, name, label, help, error }: Props<T>) {
  const { field } = useController({ control, name });
  const [text, setText] = useState(() => formatPercent(field.value ?? "0", 2));

  useEffect(() => {
    setText(formatPercent(field.value ?? "0", 2));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [field.value]);

  return (
    <label className="field">
      <span className="field-label">{label}</span>
      <input
        type="text"
        inputMode="decimal"
        value={text}
        onChange={(e) => setText(e.target.value)}
        onBlur={() => {
          const parsed = parsePercentInput(text);
          if (parsed !== null) {
            field.onChange(parsed);
            setText(formatPercent(parsed, 2));
          } else {
            setText(formatPercent(field.value ?? "0", 2));
          }
        }}
      />
      {help && <span className="field-help">{help}</span>}
      {error && <span className="field-error">{error}</span>}
    </label>
  );
}
