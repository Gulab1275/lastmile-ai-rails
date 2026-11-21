"use client";

import { useState } from "react";
import { login, type ApiError } from "@/lib/api";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [role, setRole] = useState("");

  async function handleLogin() {
    setError("");
    setLoading(true);
    try {
      const data = await login(username, password);
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("role", data.role);
      setRole(data.role);
    } catch (e) {
      const err = e as ApiError;
      setError(
        err?.message_ur ?? err?.message_en ?? "Could not connect to server"
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="min-h-screen flex items-center justify-center bg-emerald-50 p-4">
      <div className="w-full max-w-md bg-white rounded-3xl shadow-lg p-8 space-y-6">
        <h1 className="text-4xl font-bold text-center text-emerald-700">
          رہبر
        </h1>
        <p className="text-center text-gray-600">Rahbar — Relief Support</p>

        <input
          className="w-full h-14 border-2 rounded-2xl px-4 text-lg"
          placeholder="صارف کا نام / Username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
        />
        <input
          className="w-full h-14 border-2 rounded-2xl px-4 text-lg"
          type="password"
          placeholder="پاس ورڈ / Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />

        {error && <p className="text-red-600 text-center">{error}</p>}
        {role && (
          <p className="text-emerald-700 text-center">Logged in as: {role}</p>
        )}

        <button
          onClick={handleLogin}
          disabled={loading}
          className="w-full h-14 rounded-2xl bg-emerald-600 text-white text-xl font-bold disabled:opacity-50"
        >
          {loading ? "..." : "لاگ ان / Login"}
        </button>
      </div>
    </main>
  );
}