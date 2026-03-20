import type { SupabaseClient } from "@supabase/supabase-js";
import type { Database } from "../types";

type TableName = keyof Database["public"]["Tables"];

/**
 * Generic data operations scoped to an app.
 * All queries filter by app_id. RLS provides the safety net.
 */

/**
 * List rows from a table, filtered by app_id.
 */
export async function listByApp(
  client: SupabaseClient<Database>,
  table: TableName,
  appId: string,
  options?: {
    orderBy?: string;
    ascending?: boolean;
    limit?: number;
    offset?: number;
  }
) {
  let query = client
    .from(table)
    .select("*")
    .eq("app_id" as string, appId);

  if (options?.orderBy) {
    query = query.order(options.orderBy, {
      ascending: options.ascending ?? false,
    });
  }

  if (options?.limit) {
    query = query.limit(options.limit);
  }

  if (options?.offset) {
    query = query.range(
      options.offset,
      options.offset + (options.limit ?? 20) - 1
    );
  }

  const { data, error } = await query;
  if (error) throw error;
  return data;
}

/**
 * Get a single row by ID, scoped to an app.
 */
export async function getByIdInApp(
  client: SupabaseClient<Database>,
  table: TableName,
  appId: string,
  rowId: string
) {
  const { data, error } = await client
    .from(table)
    .select("*")
    .eq("app_id" as string, appId)
    .eq("id", rowId)
    .single();

  if (error) throw error;
  return data;
}

/**
 * Insert a row into a table, automatically setting app_id.
 */
export async function insertInApp(
  client: SupabaseClient<Database>,
  table: TableName,
  appId: string,
  row: Record<string, unknown>
) {
  const { data, error } = await client
    .from(table)
    .insert({ ...row, app_id: appId })
    .select()
    .single();

  if (error) throw error;
  return data;
}

/**
 * Update a row by ID, scoped to an app.
 */
export async function updateInApp(
  client: SupabaseClient<Database>,
  table: TableName,
  appId: string,
  rowId: string,
  updates: Record<string, unknown>
) {
  const { data, error } = await client
    .from(table)
    .update(updates)
    .eq("app_id" as string, appId)
    .eq("id", rowId)
    .select()
    .single();

  if (error) throw error;
  return data;
}

/**
 * Delete a row by ID, scoped to an app.
 */
export async function deleteInApp(
  client: SupabaseClient<Database>,
  table: TableName,
  appId: string,
  rowId: string
) {
  const { error } = await client
    .from(table)
    .delete()
    .eq("app_id" as string, appId)
    .eq("id", rowId);

  if (error) throw error;
}
