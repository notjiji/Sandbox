export interface NotificationSettings {
  email_enabled: boolean;
  weekly_reports: boolean;
  scan_complete: boolean;
  critical_findings: boolean;
}

export interface SecuritySettings {
  mfa_policy: string;
  password_min_length: number;
  session_timeout_minutes: number;
}

export interface OrganizationSettings {
  language: string;
  notifications: NotificationSettings;
  security: SecuritySettings;
}

export interface UpdateOrganizationSettings {
  language?: string;
  notifications?: Partial<NotificationSettings>;
  security?: Partial<SecuritySettings>;
}

export const LANGUAGE_OPTIONS = [
  { value: "en", label: "English" },
  { value: "es", label: "Spanish" },
  { value: "fr", label: "French" },
  { value: "de", label: "German" },
  { value: "pt", label: "Portuguese" },
] as const;

export const TIMEZONE_OPTIONS = [
  "UTC",
  "America/New_York",
  "America/Chicago",
  "America/Denver",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Paris",
  "Europe/Berlin",
  "Asia/Tokyo",
  "Asia/Singapore",
  "Australia/Sydney",
] as const;

export const SESSION_TIMEOUT_OPTIONS = [
  { value: 60, label: "1 hour" },
  { value: 240, label: "4 hours" },
  { value: 480, label: "8 hours" },
  { value: 720, label: "12 hours" },
  { value: 1440, label: "24 hours" },
] as const;
