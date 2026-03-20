import { supabase } from "../db";

/**
 * Health check — verifies Supabase connection is alive.
 * Returns { data: { status, timestamp } }
 */
export async function healthCheck(): Promise<{
  status: "ok" | "error";
  timestamp: string;
  error?: string;
}> {
  try {
    // Simple query to verify the connection
    const { error } = await supabase.from("apps").select("id").limit(1);

    if (error) {
      return {
        status: "error",
        timestamp: new Date().toISOString(),
        error: error.message,
      };
    }

    return {
      status: "ok",
      timestamp: new Date().toISOString(),
    };
  } catch (err) {
    return {
      status: "error",
      timestamp: new Date().toISOString(),
      error: err instanceof Error ? err.message : "Unknown error",
    };
  }
}
