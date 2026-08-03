interface FormErrorProps {
  message?: string | null;
}

export default function FormError({ message }: FormErrorProps) {
  if (!message) return null;
  return (
    <p className="mt-1 text-xs text-red-400" role="alert">
      {message}
    </p>
  );
}
