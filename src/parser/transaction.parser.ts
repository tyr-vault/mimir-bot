import type { ParsedTransaction, TransactionType } from '../types/api.js';

const AMOUNT_DESC = /^(\d+(?:[.,]\d{1,2})?)\s+(.+)$/;
const PLUS_AMOUNT_DESC = /^\+(\d+(?:[.,]\d{1,2})?)\s+(.+)$/;
const TYPED_AMOUNT_DESC = /^(income|expense)\s+(\d+(?:[.,]\d{1,2})?)\s+(.+)$/i;

function parseAmount(raw: string): number | null {
  const amount = Number(raw.replace(',', '.'));
  if (!Number.isFinite(amount) || amount <= 0) return null;
  return amount;
}

/** Split trailing category hint from optional note words. */
export function splitCategoryHint(text: string): { categoryHint: string; note: string | null } {
  const parts = text.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) {
    return { categoryHint: '', note: null };
  }
  if (parts.length === 1) {
    return { categoryHint: parts[0], note: null };
  }
  return {
    categoryHint: parts[parts.length - 1],
    note: parts.slice(0, -1).join(' '),
  };
}

function buildParsed(
  amount: number,
  description: string,
  type: TransactionType,
): ParsedTransaction {
  const { categoryHint, note } = splitCategoryHint(description);
  return { amount, description, type, categoryHint, note };
}

export function parseTransaction(text: string): ParsedTransaction | null {
  const trimmed = text.trim();
  if (!trimmed) return null;

  const typed = TYPED_AMOUNT_DESC.exec(trimmed);
  if (typed) {
    const type = typed[1].toLowerCase() as TransactionType;
    const amount = parseAmount(typed[2]);
    const description = typed[3].trim();
    if (amount === null || !description) return null;
    return buildParsed(amount, description, type);
  }

  const plus = PLUS_AMOUNT_DESC.exec(trimmed);
  if (plus) {
    const amount = parseAmount(plus[1]);
    const description = plus[2].trim();
    if (amount === null || !description) return null;
    return buildParsed(amount, description, 'income');
  }

  const match = AMOUNT_DESC.exec(trimmed);
  if (!match) return null;

  const amount = parseAmount(match[1]);
  const description = match[2].trim();
  if (amount === null || !description) return null;

  return buildParsed(amount, description, 'expense');
}

/** Parse `/expense` / `/income` command payload: `<amount> [note...] <category>`. */
export function parseCommandAmountNote(
  text: string,
  type: TransactionType,
): ParsedTransaction | null {
  return parseTransaction(
    type === 'income' ? `income ${text.trim()}` : `expense ${text.trim()}`,
  );
}
