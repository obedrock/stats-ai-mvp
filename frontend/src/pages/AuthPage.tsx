import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch, apiFormPost } from "@/lib/api";
import { useAuthStore } from "@/store/auth";

interface TokenResponse {
  access_token: string;
  token_type: string;
}

interface UserResponse {
  id: string;
  email: string;
}

export default function AuthPage() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [emailError, setEmailError] = useState("");
  const [passwordError, setPasswordError] = useState("");
  const [generalError, setGeneralError] = useState("");
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<string>("login");

  function clearErrors() {
    setEmailError("");
    setPasswordError("");
    setGeneralError("");
  }

  function handleTabChange(tab: string) {
    setActiveTab(tab);
    clearErrors();
  }

  async function handleLogin(e: React.FormEvent) {
    e.preventDefault();
    clearErrors();
    setLoading(true);
    try {
      const data = await apiFormPost<TokenResponse>("/auth/token", {
        username: email,
        password,
      });
      const user = await apiFetch<UserResponse>("/auth/me", {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });
      setAuth(data.access_token, user);
      navigate("/", { replace: true });
    } catch (err: unknown) {
      const error = err as { status?: number; detail?: string };
      if (error?.status === 401) {
        setPasswordError("Incorrect email or password. Please try again.");
      } else if (!error?.status) {
        setGeneralError("Could not reach the server. Check your connection and try again.");
      } else {
        setGeneralError("Something went wrong. Please try again in a moment.");
      }
    } finally {
      setLoading(false);
    }
  }

  async function handleRegister(e: React.FormEvent) {
    e.preventDefault();
    clearErrors();

    if (password.length < 8) {
      setPasswordError("Password must be at least 8 characters.");
      return;
    }

    setLoading(true);
    try {
      const data = await apiFetch<TokenResponse>("/auth/register", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      const user = await apiFetch<UserResponse>("/auth/me", {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });
      setAuth(data.access_token, user);
      navigate("/", { replace: true });
    } catch (err: unknown) {
      const error = err as { status?: number; detail?: string };
      if (error?.status === 409) {
        setEmailError("An account with this email already exists. Try logging in instead.");
      } else if (!error?.status) {
        setGeneralError("Could not reach the server. Check your connection and try again.");
      } else {
        setGeneralError("Something went wrong. Please try again in a moment.");
      }
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-4 py-16">
      <Card className="w-full max-w-[480px] bg-slate-800 border-slate-700 py-12 px-6">
        <Tabs value={activeTab} onValueChange={handleTabChange}>
          <TabsList className="w-full mb-6">
            <TabsTrigger value="login" className="flex-1">
              Log In
            </TabsTrigger>
            <TabsTrigger value="register" className="flex-1">
              Create Account
            </TabsTrigger>
          </TabsList>

          <TabsContent value="login">
            <CardHeader className="px-0 pb-6">
              <CardTitle className="text-xl font-semibold text-slate-100">
                Welcome back
              </CardTitle>
            </CardHeader>
            <CardContent className="px-0">
              <form onSubmit={handleLogin} className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="login-email" className="text-slate-400 text-xs">
                    Email address
                  </Label>
                  <Input
                    id="login-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    autoComplete="email"
                    className="bg-slate-800 border-slate-700 text-slate-100"
                  />
                  {emailError && (
                    <p className="text-xs text-red-500">{emailError}</p>
                  )}
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="login-password" className="text-slate-400 text-xs">
                    Password
                  </Label>
                  <Input
                    id="login-password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="current-password"
                    className="bg-slate-800 border-slate-700 text-slate-100"
                  />
                  {passwordError && (
                    <p className="text-xs text-red-500">{passwordError}</p>
                  )}
                </div>
                {generalError && (
                  <p className="text-xs text-red-500">{generalError}</p>
                )}
                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-indigo-500 hover:bg-indigo-600 text-white"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <svg
                        className="animate-spin h-4 w-4"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                        />
                      </svg>
                      Logging in…
                    </span>
                  ) : (
                    "Log In"
                  )}
                </Button>
              </form>
            </CardContent>
          </TabsContent>

          <TabsContent value="register">
            <CardHeader className="px-0 pb-6">
              <CardTitle className="text-xl font-semibold text-slate-100">
                Create your account
              </CardTitle>
            </CardHeader>
            <CardContent className="px-0">
              <form onSubmit={handleRegister} className="space-y-4">
                <div className="space-y-1.5">
                  <Label htmlFor="register-email" className="text-slate-400 text-xs">
                    Email address
                  </Label>
                  <Input
                    id="register-email"
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    autoComplete="email"
                    className="bg-slate-800 border-slate-700 text-slate-100"
                  />
                  {emailError && (
                    <p className="text-xs text-red-500">{emailError}</p>
                  )}
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="register-password" className="text-slate-400 text-xs">
                    Password
                  </Label>
                  <Input
                    id="register-password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    autoComplete="new-password"
                    className="bg-slate-800 border-slate-700 text-slate-100"
                  />
                  <p className="text-xs text-slate-400">Minimum 8 characters</p>
                  {passwordError && (
                    <p className="text-xs text-red-500">{passwordError}</p>
                  )}
                </div>
                {generalError && (
                  <p className="text-xs text-red-500">{generalError}</p>
                )}
                <Button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-indigo-500 hover:bg-indigo-600 text-white"
                >
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <svg
                        className="animate-spin h-4 w-4"
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                      >
                        <circle
                          className="opacity-25"
                          cx="12"
                          cy="12"
                          r="10"
                          stroke="currentColor"
                          strokeWidth="4"
                        />
                        <path
                          className="opacity-75"
                          fill="currentColor"
                          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                        />
                      </svg>
                      Creating account…
                    </span>
                  ) : (
                    "Create Account"
                  )}
                </Button>
              </form>
            </CardContent>
          </TabsContent>
        </Tabs>
      </Card>
    </div>
  );
}
