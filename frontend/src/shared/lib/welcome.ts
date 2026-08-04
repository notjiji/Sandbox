interface WelcomeOrgParams {
  id: string;
  name: string;
  role: string;
  slug?: string;
}

export function buildWelcomePath({ id, name, role, slug }: WelcomeOrgParams): string {
  const params = new URLSearchParams({
    org: id,
    name,
    role,
  });
  if (slug) params.set("slug", slug);
  return `/welcome?${params.toString()}`;
}
