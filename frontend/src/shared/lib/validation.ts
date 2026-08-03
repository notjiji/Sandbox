import type { ValidationErrors } from "@/shared/types/api";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PASSWORD_MIN_LENGTH = 12;
const PASSWORD_MAX_LENGTH = 128;
const PASSWORD_PATTERN =
  /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?":{}|[\]<>/_+=\-]).+$/;

export const PASSWORD_REQUIREMENTS =
  "At least 12 characters with uppercase, lowercase, number, and special character";

export function validateEmail(email: string | undefined): string | null {
  if (!email?.trim()) return "Email is required";
  if (!EMAIL_PATTERN.test(email.trim())) return "Enter a valid email address";
  return null;
}

export function validatePassword(password: string | undefined): string | null {
  if (!password) return "Password is required";
  if (password.length < PASSWORD_MIN_LENGTH) {
    return `Password must be at least ${PASSWORD_MIN_LENGTH} characters`;
  }
  if (password.length > PASSWORD_MAX_LENGTH) {
    return `Password must be at most ${PASSWORD_MAX_LENGTH} characters`;
  }
  if (!PASSWORD_PATTERN.test(password)) {
    return PASSWORD_REQUIREMENTS;
  }
  return null;
}

export function validateLoginPassword(password: string | undefined): string | null {
  if (!password) return "Password is required";
  return null;
}

export function validateLoginForm({
  email,
  password,
}: {
  email: string;
  password: string;
}): ValidationErrors {
  const errors: ValidationErrors = {};
  const emailError = validateEmail(email);
  const passwordError = validateLoginPassword(password);
  if (emailError) errors.email = emailError;
  if (passwordError) errors.password = passwordError;
  return errors;
}

export function validateRegisterForm({
  firstName,
  lastName,
  email,
  password,
  confirmPassword,
}: {
  firstName: string;
  lastName: string;
  email: string;
  password: string;
  confirmPassword: string;
}): ValidationErrors {
  const errors: ValidationErrors = {};
  if (!firstName?.trim()) errors.firstName = "First name is required";
  if (!lastName?.trim()) errors.lastName = "Last name is required";
  const emailError = validateEmail(email);
  const passwordError = validatePassword(password);
  if (emailError) errors.email = emailError;
  if (passwordError) errors.password = passwordError;
  if (password && confirmPassword && password !== confirmPassword) {
    errors.confirmPassword = "Passwords do not match";
  }
  return errors;
}

export function validateResetPasswordForm({
  password,
  confirmPassword,
}: {
  password: string;
  confirmPassword: string;
}): ValidationErrors {
  const errors: ValidationErrors = {};
  const passwordError = validatePassword(password);
  if (passwordError) errors.password = passwordError;
  if (password && confirmPassword && password !== confirmPassword) {
    errors.confirmPassword = "Passwords do not match";
  }
  return errors;
}

export function validateForgotPasswordForm({ email }: { email: string }): ValidationErrors {
  const errors: ValidationErrors = {};
  const emailError = validateEmail(email);
  if (emailError) errors.email = emailError;
  return errors;
}

export function validateOtpForm({
  email,
  otp,
}: {
  email: string;
  otp: string;
}): ValidationErrors {
  const errors: ValidationErrors = {};
  const emailError = validateEmail(email);
  if (emailError) errors.email = emailError;
  if (!otp?.trim()) {
    errors.otp = "Verification code is required";
  } else if (!/^\d{6}$/.test(otp.trim())) {
    errors.otp = "Enter the 6-digit code from your email";
  }
  return errors;
}

export function validateResendVerificationForm({ email }: { email: string }): ValidationErrors {
  const errors: ValidationErrors = {};
  const emailError = validateEmail(email);
  if (emailError) errors.email = emailError;
  return errors;
}

export function validateChangePasswordForm({
  currentPassword,
  newPassword,
  confirmPassword,
}: {
  currentPassword: string;
  newPassword: string;
  confirmPassword: string;
}): ValidationErrors {
  const errors: ValidationErrors = {};
  if (!currentPassword) errors.currentPassword = "Current password is required";
  const passwordError = validatePassword(newPassword);
  if (passwordError) errors.newPassword = passwordError;
  if (newPassword && confirmPassword && newPassword !== confirmPassword) {
    errors.confirmPassword = "Passwords do not match";
  }
  return errors;
}

export function validateProfileForm({
  firstName,
  lastName,
}: {
  firstName: string;
  lastName: string;
}): ValidationErrors {
  const errors: ValidationErrors = {};
  if (!firstName?.trim()) errors.firstName = "First name is required";
  if (!lastName?.trim()) errors.lastName = "Last name is required";
  return errors;
}
