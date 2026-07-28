const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const PASSWORD_MIN_LENGTH = 8;
const PASSWORD_PATTERN = /^(?=.*[a-zA-Z])(?=.*\d).+$/;

export function validateEmail(email) {
  if (!email?.trim()) return "Email is required";
  if (!EMAIL_PATTERN.test(email.trim())) return "Enter a valid email address";
  return null;
}

export function validatePassword(password) {
  if (!password) return "Password is required";
  if (password.length < PASSWORD_MIN_LENGTH) {
    return `Password must be at least ${PASSWORD_MIN_LENGTH} characters`;
  }
  if (!PASSWORD_PATTERN.test(password)) {
    return "Password must contain at least one letter and one number";
  }
  return null;
}

export function validateLoginForm({ email, password }) {
  const errors = {};
  const emailError = validateEmail(email);
  const passwordError = validatePassword(password);
  if (emailError) errors.email = emailError;
  if (passwordError) errors.password = passwordError;
  return errors;
}

export function validateRegisterForm({ fullName, email, password, confirmPassword }) {
  const errors = {};
  if (!fullName?.trim()) errors.fullName = "Name is required";
  const emailError = validateEmail(email);
  const passwordError = validatePassword(password);
  if (emailError) errors.email = emailError;
  if (passwordError) errors.password = passwordError;
  if (password && confirmPassword && password !== confirmPassword) {
    errors.confirmPassword = "Passwords do not match";
  }
  return errors;
}

export function validateForgotPasswordForm({ email }) {
  const errors = {};
  const emailError = validateEmail(email);
  if (emailError) errors.email = emailError;
  return errors;
}
