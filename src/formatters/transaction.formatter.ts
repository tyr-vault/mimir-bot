import type { ApiErrorKind, PeriodSummary, Transaction } from '../types/api.js';

const currencyFormatter = new Intl.NumberFormat('pt-BR', {
  style: 'currency',
  currency: 'BRL',
});

const WEEKDAY_SHORT = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'] as const;

export function formatCurrency(amount: number): string {
  return currencyFormatter.format(amount);
}

export function formatHelp(): string {
  return [
    '💰 Personal Finance',
    '',
    'Creates are saved as drafts — confirm in the dashboard (auto after 3 days).',
    '',
    'Format: <amount> [note...] <category>',
    'Last word is the category. Unknown categories also get a category draft.',
    '',
    'Add an expense:',
    '200 Groceries',
    '45 lunch Food',
    '',
    'Add income:',
    '+500 salary Income',
    'income 500 salary Income',
    '',
    'Commands:',
    '/expense 45 lunch Food',
    '/income 500 salary Income',
    '/category Food',
    '/categories',
    '/today',
    '/week',
    '/summary',
  ].join('\n');
}

export function formatDraftSaved(
  amount: number,
  categoryName: string,
  type: 'expense' | 'income' = 'expense',
  note?: string | null,
  alsoCategoryDraft = false,
): string {
  const prefix = type === 'income' ? '+' : '';
  const detail = note?.trim() ? `${note} · ${categoryName}` : categoryName;
  const lines = [
    `📝 Draft saved: ${prefix}${formatCurrency(amount)} — ${detail}`,
  ];
  if (alsoCategoryDraft) {
    lines.push(`📁 Category draft also saved: ${categoryName}`);
  }
  lines.push('Confirm or edit in the dashboard (auto-confirms in 3 days).');
  return lines.join('\n');
}

export function formatCategoryDraftSaved(name: string): string {
  return [
    `📝 Category draft saved: ${name}`,
    'Confirm or edit in the dashboard (auto-confirms in 3 days).',
  ].join('\n');
}

export function formatCategoryList(names: string[]): string {
  if (names.length === 0) {
    return 'No categories yet. Create one with /category Food';
  }
  return ['📁 Categories', '', ...names.map((n) => `• ${n}`)].join('\n');
}

export function formatCategoryUsage(): string {
  return ['Usage:', '/category Food'].join('\n');
}

export function formatTransactionCommandUsage(command: 'expense' | 'income'): string {
  return ['Usage:', `/${command} 45 lunch Food`].join('\n');
}

export function formatEmpty(label: string): string {
  return `No transactions ${label}.`;
}

export function formatMalformedInput(): string {
  return [
    "I couldn't understand that.",
    '',
    'Examples:',
    '200 Groceries',
    '45 lunch Food',
    '+500 salary Income',
  ].join('\n');
}

export function formatApiError(kind: ApiErrorKind): string {
  switch (kind) {
    case 'network':
      return "❌ Couldn't reach the finance API.";
    case 'auth':
      return '❌ Authentication with the finance API failed.';
    case 'http':
    default:
      return '❌ Finance API request failed.';
  }
}

function displayName(tx: Transaction): string {
  return tx.note?.trim() || tx.categoryName || '—';
}

function totalsFromTransactions(transactions: Transaction[]): {
  totalIncome: number;
  totalExpense: number;
  net: number;
} {
  let totalIncome = 0;
  let totalExpense = 0;
  for (const tx of transactions) {
    if (tx.type === 'income') totalIncome += tx.amount;
    else totalExpense += tx.amount;
  }
  return { totalIncome, totalExpense, net: totalIncome - totalExpense };
}

function formatTotalsBlock(totals: {
  totalIncome: number;
  totalExpense: number;
  net: number;
}): string[] {
  return [
    `Income:   ${formatCurrency(totals.totalIncome)}`,
    `Expenses: ${formatCurrency(totals.totalExpense)}`,
    `Balance:  ${formatCurrency(totals.net)}`,
  ];
}

export function formatTodayList(transactions: Transaction[]): string {
  if (transactions.length === 0) {
    return formatEmpty('today');
  }

  const lines = transactions.map((tx) => {
    const prefix = tx.type === 'income' ? '+' : '';
    return `${prefix}${formatCurrency(tx.amount)}  ${displayName(tx)}`;
  });

  return [
    '💸 Today',
    '',
    ...lines,
    '',
    ...formatTotalsBlock(totalsFromTransactions(transactions)),
  ].join('\n');
}

function weekdayLabel(isoDate: string): string {
  const [y, m, d] = isoDate.split('-').map(Number);
  const date = new Date(Date.UTC(y, m - 1, d));
  return WEEKDAY_SHORT[date.getUTCDay()];
}

export function formatWeekSummary(transactions: Transaction[], from: string, to: string): string {
  const expenses = transactions.filter((tx) => tx.type === 'expense');
  const byDate = new Map<string, number>();

  // Ensure every day in the range appears, even with zero.
  const [fy, fm, fd] = from.split('-').map(Number);
  const [ty, tm, td] = to.split('-').map(Number);
  const cursor = new Date(Date.UTC(fy, fm - 1, fd));
  const end = new Date(Date.UTC(ty, tm - 1, td));

  while (cursor <= end) {
    const key = cursor.toISOString().slice(0, 10);
    byDate.set(key, 0);
    cursor.setUTCDate(cursor.getUTCDate() + 1);
  }

  for (const tx of expenses) {
    const dateKey = tx.date.slice(0, 10);
    byDate.set(dateKey, (byDate.get(dateKey) ?? 0) + tx.amount);
  }

  const dayLines = [...byDate.entries()].map(([date, total]) => {
    const label = weekdayLabel(date).padEnd(3);
    return `${label}  ${formatCurrency(total)}`;
  });

  return [
    '📅 Last 7 days',
    '',
    ...dayLines,
    '',
    ...formatTotalsBlock(totalsFromTransactions(transactions)),
  ].join('\n');
}

export function formatPeriodSummary(summary: PeriodSummary): string {
  return [
    '📊 Summary',
    '',
    ...formatTotalsBlock({
      totalIncome: summary.totalIncome,
      totalExpense: summary.totalExpense,
      net: summary.net,
    }),
  ].join('\n');
}
