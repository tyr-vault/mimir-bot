import { config } from 'dotenv';

config();

export interface Env {
  TELEGRAM_BOT_TOKEN: string;
  API_URL: string;
  TELEGRAM_ALLOWED_USER_ID: number;
  API_EMAIL: string;
  API_PASSWORD: string;
}

function requireEnv(name: string): string {
  const value = process.env[name]?.trim();
  if (!value) {
    console.error(`Missing required environment variable: ${name}`);
    process.exit(1);
  }
  return value;
}

export function loadEnv(): Env {
  const token = requireEnv('TELEGRAM_BOT_TOKEN');
  const apiUrl = requireEnv('API_URL').replace(/\/$/, '');
  const allowedUserIdRaw = requireEnv('TELEGRAM_ALLOWED_USER_ID');
  const email = requireEnv('API_EMAIL');
  const password = requireEnv('API_PASSWORD');

  const allowedUserId = Number(allowedUserIdRaw);
  if (!Number.isInteger(allowedUserId) || allowedUserId <= 0) {
    console.error('TELEGRAM_ALLOWED_USER_ID must be a positive integer');
    process.exit(1);
  }

  return {
    TELEGRAM_BOT_TOKEN: token,
    API_URL: apiUrl,
    TELEGRAM_ALLOWED_USER_ID: allowedUserId,
    API_EMAIL: email,
    API_PASSWORD: password,
  };
}
