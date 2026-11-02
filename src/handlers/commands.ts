import type { Bot } from 'grammy';
import {
  ApiClientError,
  createCategoryDraft,
  createTransactionDraft,
  getRecentTransactions,
  getSummary,
  getTodayTransactions,
  listCategories,
  shiftDate,
  todayLocal,
} from '../api/client.js';
import {
  formatApiError,
  formatCategoryDraftSaved,
  formatCategoryList,
  formatCategoryUsage,
  formatDraftSaved,
  formatHelp,
  formatPeriodSummary,
  formatTodayList,
  formatTransactionCommandUsage,
  formatWeekSummary,
} from '../formatters/transaction.formatter.js';
import { parseCommandAmountNote } from '../parser/transaction.parser.js';
import type { ApiErrorKind, TransactionType } from '../types/api.js';

function errorKind(err: unknown): ApiErrorKind {
  if (err instanceof ApiClientError) return err.kind;
  return 'http';
}

function logError(context: string, err: unknown): void {
  const message = err instanceof Error ? err.message : String(err);
  console.error(`[${context}] ${message}`);
}

async function handleCreateTransactionCommand(
  ctx: { reply: (text: string) => Promise<unknown>; match?: string },
  type: TransactionType,
): Promise<void> {
  const payload = (ctx.match ?? '').trim();
  const parsed = parseCommandAmountNote(payload, type);
  if (!parsed) {
    await ctx.reply(formatTransactionCommandUsage(type));
    return;
  }

  try {
    const result = await createTransactionDraft(parsed);
    await ctx.reply(
      formatDraftSaved(
        parsed.amount,
        parsed.categoryHint,
        parsed.type,
        parsed.note,
        Boolean(result.category),
      ),
    );
  } catch (err) {
    logError(type, err);
    await ctx.reply(formatApiError(errorKind(err)));
  }
}

export function registerCommands(bot: Bot): void {
  bot.command('start', async (ctx) => {
    await ctx.reply(formatHelp());
  });

  bot.command('expense', async (ctx) => {
    await handleCreateTransactionCommand(ctx, 'expense');
  });

  bot.command('income', async (ctx) => {
    await handleCreateTransactionCommand(ctx, 'income');
  });

  bot.command('category', async (ctx) => {
    const name = (ctx.match ?? '').trim();
    if (!name) {
      await ctx.reply(formatCategoryUsage());
      return;
    }

    try {
      const draft = await createCategoryDraft(name);
      const draftName =
        'name' in draft.payload ? draft.payload.name : name;
      await ctx.reply(formatCategoryDraftSaved(draftName));
    } catch (err) {
      logError('category', err);
      await ctx.reply(formatApiError(errorKind(err)));
    }
  });

  bot.command('categories', async (ctx) => {
    try {
      const categories = await listCategories();
      const names = categories.map((c) => c.name).sort((a, b) => a.localeCompare(b));
      await ctx.reply(formatCategoryList(names));
    } catch (err) {
      logError('categories', err);
      await ctx.reply(formatApiError(errorKind(err)));
    }
  });

  bot.command('today', async (ctx) => {
    try {
      const transactions = await getTodayTransactions();
      await ctx.reply(formatTodayList(transactions));
    } catch (err) {
      logError('today', err);
      await ctx.reply(formatApiError(errorKind(err)));
    }
  });

  bot.command('week', async (ctx) => {
    try {
      const to = todayLocal();
      const from = shiftDate(to, -6);
      const transactions = await getRecentTransactions(7);
      await ctx.reply(formatWeekSummary(transactions, from, to));
    } catch (err) {
      logError('week', err);
      await ctx.reply(formatApiError(errorKind(err)));
    }
  });

  bot.command('summary', async (ctx) => {
    try {
      const summary = await getSummary();
      await ctx.reply(formatPeriodSummary(summary));
    } catch (err) {
      logError('summary', err);
      await ctx.reply(formatApiError(errorKind(err)));
    }
  });
}
