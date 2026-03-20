<stack>
  Expo SDK 54, React Native 0.81, npm.
  StyleSheet.create() for styling.
  @expo/vector-icons for icons.
  Only install new packages if absolutely necessary via: npm install <package>
</stack>

<structure>
  App.tsx        — Main app component (entry point)
  src/screens/   — Screen components (create this folder for new screens)
  src/components/ — Reusable UI components
  src/lib/       — Utilities and helpers
  src/lib/supabase.ts — Supabase client (created when user enables Supabase)
</structure>

<rules>
  Do NOT edit: index.ts, tsconfig.json, app.json
  Do NOT run expo start, expo export, expo build, or eas build.
  Do NOT manage git.
  After code changes, run: npm install
</rules>

<design>
  Dark mode by default: backgrounds #000 or #0A0A0A, light text, subtle borders.
  Use Pressable over TouchableOpacity.
  Seed with realistic mock data — 5-15 entries so the app looks polished.
  For images: use picsum.photos or unsplash URLs.
</design>

<supabase>
  When the user asks for auth, login, database, backend, or persistent data — use Supabase.
  The Supabase client SDK is pre-installed (@supabase/supabase-js).
  Environment variables are in .env: EXPO_PUBLIC_SUPABASE_URL and EXPO_PUBLIC_SUPABASE_ANON_KEY.

  Setup the client at src/lib/supabase.ts:
  ```typescript
  import { createClient } from '@supabase/supabase-js';
  import AsyncStorage from '@react-native-async-storage/async-storage';

  const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL!;
  const supabaseAnonKey = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY!;

  export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
    auth: {
      storage: AsyncStorage,
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: false,
    },
  });
  ```

  Auth — Use a SINGLE "Continue" button (not separate Sign In / Sign Up).
  Try signUp first; if user exists, fall back to signIn:
  ```typescript
  async function handleAuth(email: string, password: string) {
    const { data, error } = await supabase.auth.signUp({ email, password });
    if (!error && data.user) return { user: data.user, isNewUser: true };

    if (error?.message?.includes('already registered')) {
      const { data: signInData, error: signInError } = await supabase.auth.signInWithPassword({ email, password });
      if (signInError) throw new Error('Incorrect password');
      return { user: signInData.user, isNewUser: false };
    }
    throw new Error(error?.message ?? 'Auth failed');
  }
  ```

  Data — CRUD examples:
  ```typescript
  import { supabase } from '@/lib/supabase';

  // Read
  const { data } = await supabase.from('todos').select('*').eq('user_id', user.id);

  // Insert
  await supabase.from('todos').insert({ user_id: user.id, title: 'Buy milk' });

  // Update
  await supabase.from('todos').update({ done: true }).eq('id', todoId);

  // Delete
  await supabase.from('todos').delete().eq('id', todoId);
  ```

  Storage:
  ```typescript
  await supabase.storage.from('uploads').upload(`${user.id}/photo.jpg`, file);
  const { data } = supabase.storage.from('uploads').getPublicUrl(`${user.id}/photo.jpg`);
  ```

  SQL — When you need to create tables, write the SQL and tell the user to run it
  in the Supabase SQL Editor. Always include RLS:
  ```sql
  CREATE TABLE IF NOT EXISTS todos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    done BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT now()
  );
  ALTER TABLE todos ENABLE ROW LEVEL SECURITY;
  CREATE POLICY "Users manage own data" ON todos
    FOR ALL USING (auth.uid() = user_id);
  ```

  IMPORTANT:
  - Do NOT hardcode Supabase credentials. Always use process.env.
  - Do NOT add runtime checks that throw if env vars are empty.
  - If .env doesn't exist yet, create it with placeholder values and tell the user to fill them in.
</supabase>
