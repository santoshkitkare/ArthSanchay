import { useState } from "react";
import { useSearchParams } from "react-router-dom";
import { authApi } from "../api/auth";
import { ApiError } from "../api/client";

/** FR-AUTH-6. Delivery is stubbed server-side (the reset link is logged, not emailed) for this
 * pass, so this page's "request" step won't produce a real email yet — the confirm step (with a
 * `?token=` from that log line) is fully functional.
 */
export function ResetPasswordPage() {
  const [params] = useSearchParams();
  const token = params.get("token");

  const [email, setEmail] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const requestReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const resp = await authApi.requestPasswordReset(email);
      setMessage(resp.detail);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong");
    }
  };

  const confirmReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!token) return;
    try {
      await authApi.confirmPasswordReset(token, newPassword);
      setMessage("Password updated. You can log in with your new password now.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Reset link is invalid or has expired");
    }
  };

  return (
    <div className="auth-page">
      <h1>Reset password</h1>
      {message && <div className="form-success">{message}</div>}
      {error && <div className="form-error">{error}</div>}
      {!token ? (
        <form onSubmit={requestReset}>
          <label className="field">
            <span className="field-label">Email</span>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          </label>
          <button type="submit">Send reset link</button>
        </form>
      ) : (
        <form onSubmit={confirmReset}>
          <label className="field">
            <span className="field-label">New password (min. 10 characters)</span>
            <input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required />
          </label>
          <button type="submit">Set new password</button>
        </form>
      )}
    </div>
  );
}
