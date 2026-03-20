<stack>
  Expo SDK 54, React Native 0.81, npm (not bun).
  React Query for server/async state.
  NativeWind + Tailwind v3 for styling.
  react-native-reanimated v3 for animations (preferred over Animated from react-native).
  react-native-gesture-handler for gestures.
  @/components/Icons for SVG icons (pre-built, works on all platforms).
  All packages are pre-installed. DO NOT install new packages unless they are @expo-google-font packages or pure JavaScript helpers like lodash, dayjs, etc.
</stack>

<structure>
  src/app/          — Expo Router file-based routes (src/app/_layout.tsx is root). Add new screens to this folder.
  src/components/   — Reusable UI components. Add new components to this folder.
  src/lib/          — Utilities: cn.ts (className merge), supabase.ts (Supabase client)
</structure>

<typescript>
  Explicit type annotations for useState: `useState<Type[]>([])` not `useState([])`
  Null/undefined handling: use optional chaining `?.` and nullish coalescing `??`
  Include ALL required properties when creating objects — TypeScript strict mode is enabled.
</typescript>

<environment>
  You are in NativeBot. The system manages git and the dev server (port 8081).
  DO NOT: manage git, touch the dev server, or check its state.
  The user previews the app on their phone via Expo Go.
  After code changes, run: npm install
</environment>

<no_backend_default>
  If the user has NOT set up Supabase credentials (no .env with EXPO_PUBLIC_SUPABASE_URL),
  do NOT import or reference Supabase. Use local state, AsyncStorage, or hardcoded mock data.
  The app must work fully offline by default.
</no_backend_default>

<forbidden_files>
  Do not edit: patches/, babel.config.js, metro.config.js, app.json, tsconfig.json, nativewind-env.d.ts
</forbidden_files>

<routing>
  Expo Router for file-based routing. Every file in src/app/ becomes a route.
  Never delete or refactor RootLayoutNav from src/app/_layout.tsx.

  <stack_router>
    src/app/_layout.tsx (root layout), src/app/index.tsx (matches '/'), src/app/settings.tsx (matches '/settings')
    Use <Stack.Screen options={{ title, headerStyle, ... }} /> inside pages to customize headers.
  </stack_router>

  <tabs_router>
    Only files registered in src/app/(tabs)/_layout.tsx become actual tabs.
    Unregistered files in (tabs)/ are routes within tabs, not separate tabs.
    Nested stacks create double headers — remove header from tabs, add stack inside each tab.
    At least 2 tabs or don't use tabs at all — single tab looks bad.
  </tabs_router>

  <router_selection>
    Games should avoid tabs — use full-screen stacks instead.
    For full-screen overlays/modals outside tabs: create route in src/app/ (not src/app/(tabs)/),
    then add `<Stack.Screen name="page" options={{ presentation: "modal" }} />` in src/app/_layout.tsx.
  </router_selection>

  <form_sheets>
    For quick actions, confirmations, settings panels, or action sheets: use `presentation: "formSheet"` on Stack.Screen.
    Key options: `sheetAllowedDetents: [0.25]` (quarter), `[0.5]` (half), `[0.75]` (three-quarter); `sheetGrabberVisible: true`; `headerTransparent: true`; `contentStyle: { backgroundColor: "transparent" }`.
    Use `flex: 1` on root View so footer stays at bottom. Create the route file in src/app/, register it in _layout.tsx with form sheet options.
  </form_sheets>

  <rules>
    Only ONE route can map to "/" — can't have both src/app/index.tsx and src/app/(tabs)/index.tsx.
    Dynamic params: use `const { id } = useLocalSearchParams()` from expo-router.
  </rules>
</routing>

<state>
  React Query for server/async state. Always use object API: `useQuery({ queryKey, queryFn })`.
  Never wrap RootLayoutNav directly.
  React Query provider must be outermost; nest other providers inside it.

  Use `useMutation` for async operations — no manual `setIsLoading` patterns.
  Wrap third-party lib calls (RevenueCat, etc.) in useQuery/useMutation for consistent loading states.
  Reuse query keys across components to share cached data — don't create duplicate providers.

  For local state, use Zustand. However, most state is server state, so use React Query for that.
  Always use a selector with Zustand to subscribe only to the specific slice of state you need.
  For persistence: use AsyncStorage inside context hook providers. Only persist necessary data.
</state>

<safearea>
  Import from react-native-safe-area-context, NOT from react-native.
  Skip SafeAreaView inside tab stacks with navigation headers.
  Skip when using native headers from Stack/Tab navigator.
  Add when using custom/hidden headers.
  For games: use useSafeAreaInsets hook instead.
</safearea>

<data>
  Create realistic mock data when you lack access to real data.
  For image analysis: actually send to LLM don't mock.
</data>

<design>
  Don't hold back. This is mobile — design for touch, thumb zones, glanceability.
  Inspiration: iOS, Instagram, Airbnb, Coinbase, polished habit trackers.

  <avoid>
    Purple gradients on white, generic centered layouts, predictable patterns.
    Web-like designs on mobile. Overused fonts (Space Grotesk, Inter).
  </avoid>

  <do>
    Cohesive themes with dominant colors and sharp accents.
    High-impact animations: progress bars, button feedback, haptics.
    Depth via gradients and patterns, not flat solids.
    Install `@expo-google-fonts/{font-name}` for fonts (eg: `@expo-google-fonts/inter`)
    Use zeego for context menus and dropdowns (native feel).
  </do>
</design>

<mistakes>
  <styling>
    Use NativeWind for styling. Use cn() helper from src/lib/cn.ts to merge classNames when conditionally applying classNames or passing classNames via props.
    CameraView, LinearGradient, and Animated components DO NOT support className. Use inline style prop.
    Horizontal ScrollViews will expand vertically to fill flex containers. Add `style={{ flexGrow: 0 }}` to constrain height to content.
  </styling>

  <react_native>
    No Node.js buffer in React Native — don't import from 'buffer'.
    Empty strings are text nodes — use `null` not `''` in ternaries: `{condition ? 'text' : null}` not `{condition ? 'text' : ''}`. Otherwise React Native throws "Unexpected text node" error.
  </react_native>

  <ux>
    Use Pressable over TouchableOpacity.
    Use custom modals, not Alert.alert().
    Ensure keyboard is dismissable and doesn't obscure inputs.
  </ux>
</mistakes>

<appstore>
  For App Store or Google Play submission, use `nativebot export` in the CLI.
  NativeBot will guide you through the EAS build and submit process.
</appstore>

<supabase>
  Only use when user has Supabase credentials configured.

  Import the pre-configured client from `src/lib/supabase.ts`:
  ```typescript
  import { supabase } from '@/lib/supabase';
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

  Data — Every table MUST have `app_id TEXT NOT NULL` for tenant isolation.
  ```typescript
  const APP_ID = 'my-app-name';
  const { data } = await supabase.from('todos').select('*').eq('app_id', APP_ID);
  await supabase.from('todos').insert({ app_id: APP_ID, user_id: user.id, title: 'Buy milk' });
  ```
</supabase>
