import type { Bot } from 'grammy';
import { ApiClientError, createTransactionDraft } from '../api/client.js';
import {
  formatApiError,
  formatDraftSaved,
  formatMalformedInput,
} from '../formatters/transaction.formatter.js';
import { parseTransaction } from '../parser/transaction.parser.js';
import type { ApiErrorKind } from '../types/api.js';

function errorKind(err: unknown): ApiErrorKind {
  if (err instanceof ApiClientError) return err.kind;
  return 'http';
}

export function registerMessages(bot: Bot): void {
  bot.on('message:text', async (ctx) => {
    const text = ctx.message.text;

    // Commands are handled separately.
    if (text.startsWith('/')) return;

    const parsed = parseTransaction(text);
    if (!parsed) {
      await ctx.reply(formatMalformedInput());
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
      const message = err instanceof Error ? err.message : String(err);
      console.error(`[create] ${message}`);
      await ctx.reply(formatApiError(errorKind(err)));
    }
  });
}
