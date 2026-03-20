export { supabase, supabaseAdmin, createUserClient } from "./db";
export { env } from "./env";
export { signUp, signIn, signOut, getSession, getUser, getUserFromToken } from "./auth";
export { authenticate, verifyAppOwnership, extractToken } from "./middleware";
export type { AuthContext } from "./middleware";
export type {
  Database,
  App,
  AppInsert,
  AppUpdate,
  AppMember,
  AppMemberInsert,
  Profile,
  ProfileInsert,
  ProfileUpdate,
  Post,
  PostInsert,
  PostUpdate,
  ApiResponse,
  ApiError,
} from "./types";
