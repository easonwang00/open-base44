-- NativeBot Multi-Tenant Schema
-- All data tables use app_id for tenant isolation with RLS

-- =============================================================================
-- Apps table — tracks each user's projects
-- =============================================================================
CREATE TABLE IF NOT EXISTS apps (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name        TEXT NOT NULL,
  description TEXT,
  owner_id    UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE apps ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view own apps"
  ON apps FOR SELECT
  USING (owner_id = auth.uid());

CREATE POLICY "Users can create own apps"
  ON apps FOR INSERT
  WITH CHECK (owner_id = auth.uid());

CREATE POLICY "Users can update own apps"
  ON apps FOR UPDATE
  USING (owner_id = auth.uid());

CREATE POLICY "Users can delete own apps"
  ON apps FOR DELETE
  USING (owner_id = auth.uid());

-- =============================================================================
-- App members — shared access (future)
-- =============================================================================
CREATE TABLE IF NOT EXISTS app_members (
  id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  app_id   UUID NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
  user_id  UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  role     TEXT NOT NULL DEFAULT 'member' CHECK (role IN ('owner', 'editor', 'viewer', 'member')),
  joined_at TIMESTAMPTZ NOT NULL DEFAULT now(),

  UNIQUE(app_id, user_id)
);

ALTER TABLE app_members ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Members can view app memberships"
  ON app_members FOR SELECT
  USING (
    user_id = auth.uid()
    OR app_id IN (SELECT id FROM apps WHERE owner_id = auth.uid())
  );

CREATE POLICY "Owners can add members"
  ON app_members FOR INSERT
  WITH CHECK (
    app_id IN (SELECT id FROM apps WHERE owner_id = auth.uid())
  );

CREATE POLICY "Owners can remove members"
  ON app_members FOR DELETE
  USING (
    app_id IN (SELECT id FROM apps WHERE owner_id = auth.uid())
  );

-- =============================================================================
-- Profiles — public user profile data
-- =============================================================================
CREATE TABLE IF NOT EXISTS profiles (
  id         UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  username   TEXT UNIQUE,
  full_name  TEXT,
  avatar_url TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Profiles are publicly viewable" ON profiles;
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
CREATE POLICY "Users can view own profile"
  ON profiles FOR SELECT
  USING (id = auth.uid());

CREATE POLICY "Users can update own profile"
  ON profiles FOR UPDATE
  USING (id = auth.uid());

CREATE POLICY "Users can insert own profile"
  ON profiles FOR INSERT
  WITH CHECK (id = auth.uid());

-- =============================================================================
-- Posts — example data table with app_id isolation
-- =============================================================================
CREATE TABLE IF NOT EXISTS posts (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  app_id     UUID NOT NULL REFERENCES apps(id) ON DELETE CASCADE,
  author_id  UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  title      TEXT NOT NULL,
  content    TEXT,
  published  BOOLEAN NOT NULL DEFAULT false,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

ALTER TABLE posts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view posts in their apps"
  ON posts FOR SELECT
  USING (
    app_id IN (SELECT id FROM apps WHERE owner_id = auth.uid())
    OR app_id IN (SELECT app_id FROM app_members WHERE user_id = auth.uid())
  );

CREATE POLICY "Users can create posts in own apps"
  ON posts FOR INSERT
  WITH CHECK (
    author_id = auth.uid()
    AND (
      app_id IN (SELECT id FROM apps WHERE owner_id = auth.uid())
      OR app_id IN (SELECT app_id FROM app_members WHERE user_id = auth.uid() AND role IN ('owner', 'editor'))
    )
  );

CREATE POLICY "Authors can update own posts"
  ON posts FOR UPDATE
  USING (
    author_id = auth.uid()
    AND (
      app_id IN (SELECT id FROM apps WHERE owner_id = auth.uid())
      OR app_id IN (SELECT app_id FROM app_members WHERE user_id = auth.uid() AND role IN ('owner', 'editor'))
    )
  );

CREATE POLICY "Authors and owners can delete posts"
  ON posts FOR DELETE
  USING (
    author_id = auth.uid()
    OR app_id IN (SELECT id FROM apps WHERE owner_id = auth.uid())
  );

-- =============================================================================
-- Indexes
-- =============================================================================
CREATE INDEX IF NOT EXISTS idx_apps_owner ON apps(owner_id);
CREATE INDEX IF NOT EXISTS idx_app_members_app ON app_members(app_id);
CREATE INDEX IF NOT EXISTS idx_app_members_user ON app_members(user_id);
CREATE INDEX IF NOT EXISTS idx_posts_app ON posts(app_id);
CREATE INDEX IF NOT EXISTS idx_posts_author ON posts(author_id);

-- =============================================================================
-- Updated_at trigger function
-- =============================================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = now();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER apps_updated_at
  BEFORE UPDATE ON apps
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER profiles_updated_at
  BEFORE UPDATE ON profiles
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER posts_updated_at
  BEFORE UPDATE ON posts
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- =============================================================================
-- Storage bucket + policies
-- =============================================================================
INSERT INTO storage.buckets (id, name, public)
VALUES ('app-assets', 'app-assets', false)
ON CONFLICT (id) DO NOTHING;

CREATE POLICY "Users can upload to own app folders"
  ON storage.objects FOR INSERT
  WITH CHECK (
    bucket_id = 'app-assets'
    AND (storage.foldername(name))[1]::UUID IN (
      SELECT id FROM public.apps WHERE owner_id = auth.uid()
    )
  );

CREATE POLICY "Users can view files in their app folders"
  ON storage.objects FOR SELECT
  USING (
    bucket_id = 'app-assets'
    AND (
      (storage.foldername(name))[1]::UUID IN (
        SELECT id FROM public.apps WHERE owner_id = auth.uid()
      )
      OR (storage.foldername(name))[1]::UUID IN (
        SELECT app_id FROM public.app_members WHERE user_id = auth.uid()
      )
    )
  );

-- Optional stricter model for user uploads (if app uses user-uploads bucket):
INSERT INTO storage.buckets (id, name, public)
VALUES ('user-uploads', 'user-uploads', false)
ON CONFLICT (id) DO NOTHING;

DROP POLICY IF EXISTS "Public read access" ON storage.objects;
DROP POLICY IF EXISTS "Users can view own files" ON storage.objects;
CREATE POLICY "Users can view own files"
  ON storage.objects FOR SELECT
  TO authenticated
  USING (
    bucket_id = 'user-uploads'
    AND (storage.foldername(name))[2] = auth.uid()::TEXT
  );

CREATE POLICY "Users can update files in own app folders"
  ON storage.objects FOR UPDATE
  USING (
    bucket_id = 'app-assets'
    AND (storage.foldername(name))[1]::UUID IN (
      SELECT id FROM public.apps WHERE owner_id = auth.uid()
    )
  );

CREATE POLICY "Users can delete files in own app folders"
  ON storage.objects FOR DELETE
  USING (
    bucket_id = 'app-assets'
    AND (storage.foldername(name))[1]::UUID IN (
      SELECT id FROM public.apps WHERE owner_id = auth.uid()
    )
  );
