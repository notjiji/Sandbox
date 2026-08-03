export interface UserProfile {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  email_verified: boolean;
  created_at: string;
}

export interface UpdateUserProfileRequest {
  first_name?: string;
  last_name?: string;
}
