import { createClient, SupabaseClient } from "@supabase/supabase-js";
import { env } from "./env";
import type { Database } from "./types";

/**
 * Public client — uses anon key, respects RLS.
 * Safe for use in frontend or when acting on behalf of a user.
 */
export const supabase: SupabaseClient<Database> = createClient<Database>(
  env.SUPABASE_URL,
  env.SUPABASE_ANON_KEY
);

/**
 * Admin client — uses service role key, bypasses RLS.
 * Use ONLY in server-side code (Edge Functions, scripts).
 * Never expose to the frontend.
 */
export const supabaseAdmin: SupabaseClient<Database> = createClient<Database>(
  env.SUPABASE_URL,
  env.SUPABASE_SERVICE_ROLE_KEY
);

/**
 * Create a Supabase client authenticated as a specific user.
 * Pass the user's JWT access token to scope queries to their RLS policies.
 */
export function createUserClient(accessToken: string): SupabaseClient<Database> {
  return createClient<Database>(env.SUPABASE_URL, env.SUPABASE_ANON_KEY, {
    global: {
      headers: {
        Authorization: `Bearer ${accessToken}`,
      },
    },
  });
}
