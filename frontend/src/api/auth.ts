import { api } from "./client";
import type { User } from "../types";

export const authApi = {
  register: (email: string, password: string) => api.post<User>("/api/auth/register", { email, password }),
  login: (email: string, password: string) => api.post<User>("/api/auth/login", { email, password }),
  logout: () => api.post<void>("/api/auth/logout"),
  me: () => api.get<User>("/api/auth/me"),
  requestPasswordReset: (email: string) => api.post<{ detail: string }>("/api/auth/password-reset/request", { email }),
  confirmPasswordReset: (token: string, new_password: string) =>
    api.post<void>("/api/auth/password-reset/confirm", { token, new_password }),
};
