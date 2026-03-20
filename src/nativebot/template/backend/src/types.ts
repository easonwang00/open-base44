// =============================================================================
// Database types — matches the SQL schema
// =============================================================================

export interface Database {
  public: {
    Tables: {
      apps: {
        Row: App;
        Insert: AppInsert;
        Update: AppUpdate;
      };
      app_members: {
        Row: AppMember;
        Insert: AppMemberInsert;
        Update: AppMemberUpdate;
      };
      profiles: {
        Row: Profile;
        Insert: ProfileInsert;
        Update: ProfileUpdate;
      };
      posts: {
        Row: Post;
        Insert: PostInsert;
        Update: PostUpdate;
      };
    };
    Views: Record<string, never>;
    Functions: Record<string, never>;
    Enums: {
      member_role: "owner" | "editor" | "viewer" | "member";
    };
  };
}

// =============================================================================
// App
// =============================================================================

export interface App {
  id: string;
  name: string;
  description: string | null;
  owner_id: string;
  created_at: string;
  updated_at: string;
}

export interface AppInsert {
  id?: string;
  name: string;
  description?: string | null;
  owner_id: string;
  created_at?: string;
  updated_at?: string;
}

export interface AppUpdate {
  name?: string;
  description?: string | null;
  updated_at?: string;
}

// =============================================================================
// App Member
// =============================================================================

export interface AppMember {
  id: string;
  app_id: string;
  user_id: string;
  role: "owner" | "editor" | "viewer" | "member";
  joined_at: string;
}

export interface AppMemberInsert {
  id?: string;
  app_id: string;
  user_id: string;
  role?: "owner" | "editor" | "viewer" | "member";
  joined_at?: string;
}

export interface AppMemberUpdate {
  role?: "owner" | "editor" | "viewer" | "member";
}

// =============================================================================
// Profile
// =============================================================================

export interface Profile {
  id: string;
  username: string | null;
  full_name: string | null;
  avatar_url: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProfileInsert {
  id: string;
  username?: string | null;
  full_name?: string | null;
  avatar_url?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ProfileUpdate {
  username?: string | null;
  full_name?: string | null;
  avatar_url?: string | null;
  updated_at?: string;
}

// =============================================================================
// Post
// =============================================================================

export interface Post {
  id: string;
  app_id: string;
  author_id: string;
  title: string;
  content: string | null;
  published: boolean;
  created_at: string;
  updated_at: string;
}

export interface PostInsert {
  id?: string;
  app_id: string;
  author_id: string;
  title: string;
  content?: string | null;
  published?: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface PostUpdate {
  title?: string;
  content?: string | null;
  published?: boolean;
  updated_at?: string;
}

// =============================================================================
// API response types
// =============================================================================

export interface ApiResponse<T> {
  data: T;
}

export interface ApiError {
  error: {
    message: string;
    code: string;
  };
}
