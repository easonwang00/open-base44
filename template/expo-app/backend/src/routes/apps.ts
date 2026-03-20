import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database, App, AppInsert } from "../types";

/**
 * List all apps owned by the current user.
 * RLS ensures only the user's own apps are returned.
 */
export async function listApps(client: SupabaseClient<Database>) {
  const { data, error } = await client
    .from("apps")
    .select("*")
    .order("created_at", { ascending: false });

  if (error) throw error;
  return data as App[];
}

/**
 * Get a single app by ID.
 * RLS ensures the user can only see their own apps.
 */
export async function getApp(client: SupabaseClient<Database>, appId: string) {
  const { data, error } = await client
    .from("apps")
    .select("*")
    .eq("id", appId)
    .single();

  if (error) throw error;
  return data as App;
}

/**
 * Create a new app.
 */
export async function createApp(
  client: SupabaseClient<Database>,
  input: { name: string; description?: string },
  ownerId: string
) {
  const insert: AppInsert = {
    name: input.name,
    description: input.description ?? null,
    owner_id: ownerId,
  };

  const { data, error } = await client
    .from("apps")
    .insert(insert)
    .select()
    .single();

  if (error) throw error;
  return data as App;
}

/**
 * Update an existing app.
 * RLS ensures only the owner can update.
 */
export async function updateApp(
  client: SupabaseClient<Database>,
  appId: string,
  input: { name?: string; description?: string | null }
) {
  const { data, error } = await client
    .from("apps")
    .update(input)
    .eq("id", appId)
    .select()
    .single();

  if (error) throw error;
  return data as App;
}

/**
 * Delete an app.
 * RLS ensures only the owner can delete.
 * CASCADE will clean up posts, members, etc.
 */
export async function deleteApp(
  client: SupabaseClient<Database>,
  appId: string
) {
  const { error } = await client.from("apps").delete().eq("id", appId);

  if (error) throw error;
}
