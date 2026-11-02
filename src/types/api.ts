export type TransactionType = 'expense' | 'income';

export interface ApiEnvelope<T> {
  statusCode: number;
  data: T;
  message: string;
  success: boolean;
}

export interface Transaction {
  id: string;
  userId: string;
  categoryId: string;
  categoryName?: string;
  type: TransactionType;
  amount: number;
  date: string;
  note: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface PeriodSummary {
  from?: string;
  to?: string;
  type?: TransactionType;
  totalIncome: number;
  totalExpense: number;
  net: number;
  count: number;
}

export interface Category {
  id: string;
  userId: string;
  name: string;
  createdAt: string;
  updatedAt: string;
}

export interface CreateTransactionBody {
  categoryId: string;
  type: TransactionType;
  amount: number;
  date: string;
  note?: string | null;
}

export type DraftKind = 'transaction' | 'category';
export type DraftStatus = 'pending' | 'confirmed' | 'rejected';

export interface TransactionDraftPayload {
  categoryId?: string;
  categoryName?: string;
  type: TransactionType;
  amount: number;
  date: string;
  note?: string | null;
}

export interface CategoryDraftPayload {
  name: string;
}

export type DraftPayload = TransactionDraftPayload | CategoryDraftPayload;

export interface Draft {
  id: string;
  userId: string;
  kind: DraftKind;
  status: DraftStatus;
  payload: DraftPayload;
  source: string;
  confirmedAt: string | null;
  rejectedAt: string | null;
  createdAt: string;
  updatedAt: string;
}

export interface CreateDraftBody {
  kind: DraftKind;
  payload: DraftPayload;
  source?: string;
}

export interface ParsedTransaction {
  amount: number;
  description: string;
  type: TransactionType;
  /** Last token after amount — used as category name. */
  categoryHint: string;
  /** Remaining words before the category hint; empty when only one token. */
  note: string | null;
}

export interface LoginResponse {
  token: string;
  user: {
    id: string;
    email: string;
    name: string;
  };
}

export type ApiErrorKind = 'network' | 'http' | 'auth';
