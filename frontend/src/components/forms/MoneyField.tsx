import { useEffect, useState } from "react";
import { useController, type Control, type FieldPath, type FieldValues } from "react-hook-form";
import { formatINR, parseMoneyInput } from "../../lib/money";

interface Props<T extends FieldValues> {
  control: Control<T>;
  name: FieldPath<T>;
  label: string;
  help?: string;
  error?: string;
}

/** Accepts shorthand ("1.5cr", "15L", "1500000") and stores the parsed plain-decimal string in
 * form state, per PRD.md §8.2. Displays the formatted value once the field loses focus.
 */
export function MoneyField<T extends FieldValues>({ control, name, label, help, error }: Props<T>) {
  const { field } = useController({ control, name });
  const [text, setText] = useState(() => formatINR(field.value ?? "0"));

  useEffect(() => {
    setText(formatINR(field.value ?? "0"));
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
          const parsed = parseMoneyInput(text);
          if (parsed !== null) {
            field.onChange(parsed);
            setText(formatINR(parsed));
          } else {
            setText(formatINR(field.value ?? "0"));
          }
        }}
      />
      {help && <span className="field-help">{help}</span>}
      {error && <span className="field-error">{error}</span>}
    </label>
  );
}
