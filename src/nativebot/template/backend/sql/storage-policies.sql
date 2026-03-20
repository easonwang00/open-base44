-- NativeBot Storage Policies
-- Files stored under: user-uploads/{app_id}/{user_id}/filename

-- =============================================================================
-- Create the user-uploads bucket (private)
-- =============================================================================
INSERT INTO storage.buckets (id, name, public)
VALUES ('user-uploads', 'user-uploads', false)
ON CONFLICT (id) DO NOTHING;

-- =============================================================================
-- Storage policies — scoped by authenticated user
-- =============================================================================

-- Authenticated users can upload files under their own path
CREATE POLICY "Authenticated users can upload"
  ON storage.objects FOR INSERT
  TO authenticated
  WITH CHECK (
    bucket_id = 'user-uploads'
    AND (storage.foldername(name))[2] = auth.uid()::TEXT
  );

-- Users can view only their own files
DROP POLICY IF EXISTS "Public read access" ON storage.objects;
DROP POLICY IF EXISTS "Users can view own files" ON storage.objects;
CREATE POLICY "Users can view own files"
  ON storage.objects FOR SELECT
  TO authenticated
  USING (
    bucket_id = 'user-uploads'
    AND (storage.foldername(name))[2] = auth.uid()::TEXT
  );

-- Users can update their own files
CREATE POLICY "Users can update own files"
  ON storage.objects FOR UPDATE
  TO authenticated
  USING (
    bucket_id = 'user-uploads'
    AND (storage.foldername(name))[2] = auth.uid()::TEXT
  );

-- Users can delete their own files
CREATE POLICY "Users can delete own files"
  ON storage.objects FOR DELETE
  TO authenticated
  USING (
    bucket_id = 'user-uploads'
    AND (storage.foldername(name))[2] = auth.uid()::TEXT
  );
