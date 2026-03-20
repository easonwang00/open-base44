// Supabase Edge Function — app-action
// Template for server-side logic that requires ownership verification.
//
// Deploy: npx supabase functions deploy app-action
// Test:   npx supabase functions serve

import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers":
    "authorization, x-client-info, apikey, content-type",
};

Deno.serve(async (req: Request) => {
  // Handle CORS preflight
  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  try {
    // Create Supabase client with the user's auth token
    const supabase = createClient(
      Deno.env.get("SUPABASE_URL") ?? "",
      Deno.env.get("SUPABASE_ANON_KEY") ?? "",
      {
        global: {
          headers: { Authorization: req.headers.get("Authorization")! },
        },
      }
    );

    // Verify the user is authenticated
    const {
      data: { user },
      error: authError,
    } = await supabase.auth.getUser();

    if (authError || !user) {
      return new Response(
        JSON.stringify({
          error: { message: "Unauthorized", code: "UNAUTHORIZED" },
        }),
        { status: 401, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Parse request body
    const { app_id, action, payload } = await req.json();

    if (!app_id || !action) {
      return new Response(
        JSON.stringify({
          error: { message: "app_id and action are required", code: "BAD_REQUEST" },
        }),
        { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Verify the user owns this app (RLS handles this, but explicit check is good practice)
    const { data: app, error: appError } = await supabase
      .from("apps")
      .select("id")
      .eq("id", app_id)
      .single();

    if (appError || !app) {
      return new Response(
        JSON.stringify({
          error: { message: "App not found or access denied", code: "NOT_FOUND" },
        }),
        { status: 404, headers: { ...corsHeaders, "Content-Type": "application/json" } }
      );
    }

    // Handle the action
    let result: unknown;

    switch (action) {
      case "ping":
        result = { message: "pong", app_id, user_id: user.id };
        break;

      // Add more actions here as needed
      // case "generate-report":
      //   result = await generateReport(supabase, app_id, payload);
      //   break;

      default:
        return new Response(
          JSON.stringify({
            error: { message: `Unknown action: ${action}`, code: "BAD_REQUEST" },
          }),
          { status: 400, headers: { ...corsHeaders, "Content-Type": "application/json" } }
        );
    }

    return new Response(JSON.stringify({ data: result }), {
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  } catch (err) {
    return new Response(
      JSON.stringify({
        error: {
          message: err instanceof Error ? err.message : "Internal error",
          code: "INTERNAL_ERROR",
        },
      }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }
});
