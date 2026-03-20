# API Contract Patterns

Shared conventions for API communication between backend and frontend.

<api_contracts>
  ALL app routes return { data: ... }. Client auto-unwraps.

  Backend: c.json({ data: posts })
  Frontend: api.get<Post[]>()  // Returns Post[], not { data: Post[] }

  Exceptions (no envelope):
  - /api/auth/* (Supabase Auth owns response)
  - 204 No Content
  - Non-JSON (use api.raw())
</api_contracts>

<response_envelope>
  All app routes: c.json({ data: value })
  Errors: c.json({ error: { message, code } }, 4xx)
</response_envelope>

<api_typing>
  Type inner value only:
  ✅ api.get<Post[]>('/api/posts')
  ❌ api.get<{ data: Post[] }>()
  ❌ api.get<{ posts: Post[] }>()

  "Cannot read properties of undefined" = wrong type shape.
</api_typing>
