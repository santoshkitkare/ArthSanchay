// Indian digit-grouping (lakh/crore) formatting, and parsing of the shorthand users actually
// type ("1.5cr", "15L", "1500000") — PRD.md §8.2. Money is carried as strings end-to-end
// (see types/index.ts's comment) and only converted to `number` at the last moment for display
// arithmetic, which is fine for formatting (not accumulation).

const RUPEE = "₹";

/** Format a decimal string/number using Indian digit grouping: 150000000 -> "15,00,00,000". */
export function formatINR(value: string | number, decimals = 0): string {
  const n = typeof value === "string" ? parseFloat(value) : value;
  if (!isFinite(n)) return "—";
  const sign = n < 0 ? "-" : "";
  const abs = Math.abs(n);
  const fixed = abs.toFixed(decimals);
  const [intPart, fracPart] = fixed.split(".");
  let grouped: string;
  if (intPart.length <= 3) {
    grouped = intPart;
  } else {
    const last3 = intPart.slice(-3);
    let rest = intPart.slice(0, -3);
    const parts: string[] = [];
    while (rest.length > 2) {
      parts.unshift(rest.slice(-2));
      rest = rest.slice(0, -2);
    }
    if (rest) parts.unshift(rest);
    grouped = parts.join(",") + "," + last3;
  }
  const out = `${sign}${RUPEE}${grouped}`;
  return decimals ? `${out}.${fracPart}` : out;
}

/** Short form for tiles/charts: crore for >=1e7, lakh for >=1e5, else plain grouped rupees. */
export function formatINRShort(value: string | number): string {
  const n = typeof value === "string" ? parseFloat(value) : value;
  if (!isFinite(n)) return "—";
  const sign = n < 0 ? "-" : "";
  const abs = Math.abs(n);
  if (abs >= 1e7) return `${sign}${RUPEE}${(abs / 1e7).toFixed(2)} Cr`;
  if (abs >= 1e5) return `${sign}${RUPEE}${(abs / 1e5).toFixed(2)} L`;
  return formatINR(n);
}

/** Parse user-typed shorthand ("1.5cr", "15l", "1500000", "15,00,000") into a plain decimal
 * string suitable for the API. Returns null when the input cannot be parsed as a number.
 */
export function parseMoneyInput(raw: string): string | null {
  const cleaned = raw.trim().toLowerCase().replace(/[,₹\s]/g, "");
  if (cleaned === "") return null;
  const crMatch = cleaned.match(/^(-?\d*\.?\d+)cr$/);
  if (crMatch) return String(parseFloat(crMatch[1]) * 1e7);
  const lMatch = cleaned.match(/^(-?\d*\.?\d+)l$/);
  if (lMatch) return String(parseFloat(lMatch[1]) * 1e5);
  const kMatch = cleaned.match(/^(-?\d*\.?\d+)k$/);
  if (kMatch) return String(parseFloat(kMatch[1]) * 1e3);
  const plain = parseFloat(cleaned);
  return isFinite(plain) ? String(plain) : null;
}

/** Parse a percent field ("7", "7%", "0.07" when explicitly a fraction) into a decimal fraction
 * string for the API. Values are assumed entered as whole percent (7 -> 0.07) unless already
 * written with a leading "0." (0.07 -> 0.07), matching how a person actually types a rate.
 */
export function parsePercentInput(raw: string): string | null {
  const cleaned = raw.trim().replace(/%$/, "");
  if (cleaned === "") return null;
  const n = parseFloat(cleaned);
  if (!isFinite(n)) return null;
  if (cleaned.startsWith("0.") && n < 1) return String(n);
  return String(n / 100);
}

/** Format a decimal-fraction rate string ("0.07") as a percent for display ("7%"). */
export function formatPercent(value: string | number, decimals = 2): string {
  const n = typeof value === "string" ? parseFloat(value) : value;
  if (!isFinite(n)) return "—";
  return `${(n * 100).toFixed(decimals)}%`;
}
