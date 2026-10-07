export class ResumeReaderError extends Error {
  status: number;
  body?: unknown;
}
export interface ParseOptions {
  fieldNames?: 'en' | 'fr';
  excludeSensitive?: boolean;
  anonymize?: boolean;
  maxPages?: number;
  sections?: string[];
  language?: string;
}
export interface ParseResult {
  status: number;
  resume: Record<string, any>;
  meta?: Record<string, any>;
  credits_used?: number;
  remaining_credits?: number;
  [key: string]: any;
}
export interface NormalizeResult<T = Record<string, any>> {
  results: T[];
  credits_used: number;
  remaining_credits?: number;
}
export class ResumeReader {
  constructor(apiKey: string, options?: { timeout?: number; schemaVersion?: 1 | 2 });
  parseText(text: string, options?: ParseOptions): Promise<ParseResult>;
  parseFile(filePath: string, options?: ParseOptions): Promise<ParseResult>;
  parseUrl(fileUrl: string, options?: ParseOptions): Promise<ParseResult>;
  normalizeTitles(titles: string | string[]): Promise<NormalizeResult>;
  normalizeSkills(skills: string | string[]): Promise<NormalizeResult>;
  normalizeLocations(locations: string | string[]): Promise<NormalizeResult>;
}
export default ResumeReader;
