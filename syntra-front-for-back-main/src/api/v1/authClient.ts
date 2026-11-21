/**
 * SYNTRA Authentication API Client — v1.
 *
 * Handles HTTP requests for signup, OTP verification, login, guest access,
 * and user session management.
 *
 * When VITE_API_BASE_URL is configured, all calls hit the remote backend.
 * When not configured (development/preview mode), it runs a deterministic,
 * safe local mock provider so the complete user flow works out of the box.
 */
import {
  API_VERSION,
  type ApiErrorCode,
  type AuthUser,
  type SignUpRequestBody,
  type SignUpResponseBody,
  type VerifyOtpRequestBody,
  type VerifyOtpResponseBody,
  type ResendOtpRequestBody,
  type ResendOtpResponseBody,
  type LoginRequestBody,
  type LoginResponseBody,
  type AnonymousResponseBody,
  type MeResponseBody,
  type LogoutResponseBody,
} from "./contract";
import { ApiRequestError, isRemoteApiConfigured, setAuthToken } from "./client";
import { sendWelcomeNotification } from "@/services/notifications";

const BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/+$/, "");
const STORAGE_TOKEN_KEY = "syntra_auth_token";
const STORAGE_USER_KEY = "syntra_auth_user";

/* --------------------------- Token Persistence --------------------------- */

let memoryToken: string | null = null;
let memoryUser: AuthUser | null = null;

export function getStoredToken(): string | null {
  try {
    if (typeof window !== "undefined" && window.localStorage) {
      const val = window.localStorage.getItem(STORAGE_TOKEN_KEY);
      if (val !== null) return val;
    }
  } catch {
    // Local storage unavailable
  }
  return memoryToken;
}

export function getStoredUser(): AuthUser | null {
  try {
    if (typeof window !== "undefined" && window.localStorage) {
      const raw = window.localStorage.getItem(STORAGE_USER_KEY);
      if (raw) return JSON.parse(raw);
    }
  } catch {
    // Local storage unavailable
  }
  return memoryUser;
}

export function saveSession(token: string | null, user: AuthUser | null): void {
  memoryToken = token;
  memoryUser = user;
  setAuthToken(token);

  try {
    if (typeof window !== "undefined" && window.localStorage) {
      if (token) {
        window.localStorage.setItem(STORAGE_TOKEN_KEY, token);
      } else {
        window.localStorage.removeItem(STORAGE_TOKEN_KEY);
      }

      if (user) {
        window.localStorage.setItem(STORAGE_USER_KEY, JSON.stringify(user));
      } else {
        window.localStorage.removeItem(STORAGE_USER_KEY);
      }
    }
  } catch {
    // Local storage unavailable (private browsing fallback)
  }
}

export function clearSession(): void {
  saveSession(null, null);
}

/* ----------------------------- Remote Transport ----------------------------- */

async function authRequest<T>(path: string, options: { method: "GET" | "POST"; body?: unknown }): Promise<T> {
  const token = getStoredToken();
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const response = await fetch(`${BASE_URL}/api/${API_VERSION}${path}`, {
    method: options.method,
    headers,
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    credentials: "omit",
    mode: "cors",
  }).catch((err) => {
    throw new ApiRequestError("dependency_unavailable", "Failed to reach authentication server.", true);
  });

  if (!response.ok) {
    let payload: { code?: string; message?: string } = {};
    try {
      payload = await response.json();
    } catch {
      // Ignored
    }
    const message = payload.message || `Authentication failed (${response.status})`;
    const code: ApiErrorCode =
      response.status === 401
        ? "unauthorized"
        : response.status === 403
          ? "forbidden"
          : response.status === 429
            ? "rate_limited"
            : response.status === 404
              ? "not_found"
              : response.status >= 400 && response.status < 500
                ? "invalid_input"
                : "internal_error";
    throw new ApiRequestError(code, message, response.status >= 500 || response.status === 429);
  }

  return (await response.json()) as T;
}

/* ------------------------- Local Mock State ------------------------- */

interface PendingVerification {
  email: string;
  code: string;
  password?: string;
  expiresAt: number;
}

const mockPendingVerifications = new Map<string, PendingVerification>();

function generateMockCode(): string {
  // Always standard 6-digit code. In mock mode, we use "123456" for predictable testing
  return "123456";
}

/* ---------------------------- Public API Surface ---------------------------- */

/**
 * Step 1 of Signup: Register credentials and request email OTP verification code.
 */
export async function apiSignUp(body: SignUpRequestBody): Promise<SignUpResponseBody> {
  if (isRemoteApiConfigured()) {
    return authRequest<SignUpResponseBody>("/auth/signup", {
      method: "POST",
      body,
    });
  }

  // --- Local Fallback Mode ---
  const normalizedEmail = (body.email || body.phone || "").trim().toLowerCase();
  const demoCode = generateMockCode();
  mockPendingVerifications.set(normalizedEmail, {
    email: normalizedEmail,
    code: demoCode,
    password: body.password,
    expiresAt: Date.now() + 600_000, // 10 minutes
  });

  // Trigger optional welcome notification webhook if configured
  void sendWelcomeNotification(normalizedEmail);

  if (import.meta.env.DEV) {
    console.info(`[Auth Mock] Signup initiated for ${normalizedEmail}. Verification OTP code: ${demoCode}`);
  }

  return {
    status: "pending_verification",
    message: `Verification code sent to ${normalizedEmail}`,
    email: body.email,
    phone: body.phone,
    otp_channel: body.otp_channel || "email",
    expires_in_seconds: 600,
    demo_code: demoCode,
  };
}

/**
 * Step 2 of Signup / Login: Verify the 6-digit OTP code to activate account or session.
 */
export async function apiVerifyOtp(body: VerifyOtpRequestBody): Promise<VerifyOtpResponseBody> {
  if (isRemoteApiConfigured()) {
    const res = await authRequest<VerifyOtpResponseBody>("/auth/verify-otp", {
      method: "POST",
      body,
    });
    saveSession(res.token, res.user);
    return res;
  }

  // --- Local Fallback Mode ---
  const normalizedEmail = (body.email || body.phone || "").trim().toLowerCase();
  const pending = mockPendingVerifications.get(normalizedEmail);

  // Accept either matching code or standard demo code "123456"
  const isCodeValid =
    (pending && pending.code === body.code) ||
    body.code === "123456";

  if (!isCodeValid) {
    throw new ApiRequestError("invalid_input", "Invalid verification code. Please check your code and try again.", false);
  }

  mockPendingVerifications.delete(normalizedEmail);

  const user: AuthUser = {
    id: `usr_${Math.random().toString(36).slice(2, 10)}`,
    email: normalizedEmail,
    name: normalizedEmail.split("@")[0],
    role: "analyst",
    is_verified: true,
    created_at: new Date().toISOString(),
  };
  const token = `syn_jwt_${Math.random().toString(36).slice(2)}_${Date.now()}`;

  saveSession(token, user);

  return {
    status: "verified",
    message: "Identity verified successfully. Welcome to SYNTRA.",
    token,
    user,
    expires_in_seconds: 86400 * 7,
  };
}

/**
 * Resend OTP code if expired or lost.
 */
export async function apiResendOtp(body: ResendOtpRequestBody): Promise<ResendOtpResponseBody> {
  if (isRemoteApiConfigured()) {
    return authRequest<ResendOtpResponseBody>("/auth/resend-otp", {
      method: "POST",
      body,
    });
  }

  // --- Local Fallback Mode ---
  const normalizedEmail = (body.email || body.phone || "").trim().toLowerCase();
  const demoCode = generateMockCode();
  mockPendingVerifications.set(normalizedEmail, {
    email: normalizedEmail,
    code: demoCode,
    expiresAt: Date.now() + 600_000,
  });

  if (import.meta.env.DEV) {
    console.info(`[Auth Mock] Resent OTP code to ${normalizedEmail}: ${demoCode}`);
  }

  return {
    status: "sent",
    message: `A fresh verification code was sent to ${normalizedEmail}`,
    email: body.email,
    phone: body.phone,
    expires_in_seconds: 600,
    demo_code: demoCode,
  };
}

/**
 * Standard password login.
 */
export async function apiLogin(body: LoginRequestBody): Promise<LoginResponseBody> {
  if (isRemoteApiConfigured()) {
    const res = await authRequest<LoginResponseBody>("/auth/login", {
      method: "POST",
      body,
    });
    saveSession(res.token, res.user);
    return res;
  }

  // --- Local Fallback Mode ---
  const normalizedEmail = (body.email || body.phone || "").trim().toLowerCase();
  const user: AuthUser = {
    id: `usr_${Math.random().toString(36).slice(2, 10)}`,
    email: normalizedEmail,
    name: normalizedEmail.split("@")[0],
    role: "analyst",
    is_verified: true,
    created_at: new Date().toISOString(),
  };
  const token = `syn_jwt_${Math.random().toString(36).slice(2)}_${Date.now()}`;

  saveSession(token, user);

  return {
    status: "authenticated",
    message: "Signed in successfully",
    token,
    user,
    expires_in_seconds: 86400 * 7,
  };
}

/**
 * Anonymous / Guest login for immediate access.
 */
export async function apiAnonymousLogin(): Promise<AnonymousResponseBody> {
  if (isRemoteApiConfigured()) {
    const res = await authRequest<AnonymousResponseBody>("/auth/anonymous", {
      method: "POST",
    });
    saveSession(res.token, res.user);
    return res;
  }

  // --- Local Fallback Mode ---
  const user: AuthUser = {
    id: `guest_${Math.random().toString(36).slice(2, 8)}`,
    email: null,
    name: "Guest Analyst",
    role: "guest",
    is_verified: true,
  };
  const token = `syn_guest_${Date.now()}`;

  saveSession(token, user);

  return {
    status: "authenticated",
    token,
    user,
    expires_in_seconds: 86400,
  };
}

/**
 * Retrieve current user profile using the stored Bearer token.
 */
export async function apiGetMe(): Promise<MeResponseBody> {
  if (isRemoteApiConfigured()) {
    return authRequest<MeResponseBody>("/auth/me", { method: "GET" });
  }

  // --- Local Fallback Mode ---
  const stored = getStoredUser();
  if (!stored) {
    throw new ApiRequestError("unauthorized", "No active session found.", false);
  }
  return { user: stored };
}

/**
 * End current session.
 */
export async function apiLogout(): Promise<LogoutResponseBody> {
  if (isRemoteApiConfigured()) {
    try {
      await authRequest<LogoutResponseBody>("/auth/logout", { method: "POST" });
    } catch {
      // Ignored
    }
  }

  clearSession();
  return { success: true, message: "Logged out successfully" };
}
