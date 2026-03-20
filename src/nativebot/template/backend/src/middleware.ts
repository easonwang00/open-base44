import { getUserFromToken } from "./auth";
import { createUserClient } from "./db";
import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "./types";

export interface AuthContext {
  userId: string;
  email: string;
  client: SupabaseClient<Database>;
}

/**
 * Extract the Bearer token from an Authorization header.
 */
export function extractToken(authHeader: string | null): string | null {
  if (!authHeader?.startsWith("Bearer ")) return null;
  return authHeader.slice(7);
}

/**
 * Authenticate a request using the Supabase JWT from the Authorization header.
 * Returns an AuthContext with the user's ID, email, and a scoped Supabase client.
 */
export async function authenticate(
  authHeader: string | null
): Promise<AuthContext | null> {
  const token = extractToken(authHeader);
  if (!token) return null;

  const user = await getUserFromToken(token);
  if (!user || !user.email) return null;

  return {
    userId: user.id,
    email: user.email,
    client: createUserClient(token),
  };
}

/**
 * Verify that a user owns a specific app.
 * Uses the user's scoped client so RLS applies.
 */
export async function verifyAppOwnership(
  client: SupabaseClient<Database>,
  appId: string
): Promise<boolean> {
  const { data, error } = await client
    .from("apps")
    .select("id")
    .eq("id", appId)
    .single();

  return !error && !!data;
}
