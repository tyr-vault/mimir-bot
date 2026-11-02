import { Bot } from 'grammy';
import { initApiClient } from './api/client.js';
import { loadEnv } from './config/env.js';
import { registerCommands } from './handlers/commands.js';
import { registerMessages } from './handlers/messages.js';

async function main(): Promise<void> {
  const env = loadEnv();

  try {
    await initApiClient(env);
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    console.error(`Failed to initialize API client: ${message}`);
    process.exit(1);
  }

  const bot = new Bot(env.TELEGRAM_BOT_TOKEN);
  const allowedUserId = env.TELEGRAM_ALLOWED_USER_ID;

  bot.use(async (ctx, next) => {
    if (ctx.from?.id !== allowedUserId) {
      return;
    }
    await next();
  });

  registerCommands(bot);
  registerMessages(bot);

  bot.catch((err) => {
    console.error('Telegram error:', err.error);
  });

  console.log('Starting Mimir bot…');
  await bot.start();
}

main().catch((err) => {
  console.error('Fatal error:', err instanceof Error ? err.message : err);
  process.exit(1);
});
