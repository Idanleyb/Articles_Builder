'use client';
import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabaseBrowser } from '@/lib/supabaseClient';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mode, setMode] = useState<'signin' | 'signup'>('signin');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();
  const supabase = supabaseBrowser();

  async function handleEmailAuth(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    const { error } =
      mode === 'signin'
        ? await supabase.auth.signInWithPassword({ email, password })
        : await supabase.auth.signUp({ email, password });
    setLoading(false);
    if (error) {
      setError(error.message);
      return;
    }
    router.push('/dashboard');
    router.refresh();
  }

  async function handleGoogleAuth() {
    await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: { redirectTo: `${window.location.origin}/dashboard` },
    });
  }

  return (
    <div style={{ maxWidth: 400, margin: '110px auto', padding: '0 24px' }}>
      <p className="eyebrow" style={{ marginBottom: 10 }}>ARTICLES BUILDER</p>
      <h1
        className="aurora-text"
        style={{ fontFamily: 'var(--font-display)', fontSize: 30, margin: '0 0 6px', lineHeight: 1.15 }}
      >
        {mode === 'signin' ? 'Welcome back' : 'Start writing smarter'}
      </h1>
      <p style={{ color: 'var(--text-mid)', fontSize: 14, marginBottom: 28 }}>
        {mode === 'signin' ? 'Sign in to your dashboard' : 'Topics in, articles out — twice a week or however often you want.'}
      </p>

      <div className="glass-card">
        <form onSubmit={handleEmailAuth}>
          <label className="field-label">Email</label>
          <input
            className="field-input"
            style={{ marginBottom: 14 }}
            type="email"
            placeholder="you@company.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <label className="field-label">Password</label>
          <input
            className="field-input"
            style={{ marginBottom: 16 }}
            type="password"
            placeholder="••••••••"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={6}
          />
          {error && <p style={{ color: 'var(--danger)', fontSize: 13, marginBottom: 12 }}>{error}</p>}
          <button type="submit" className="btn-primary" style={{ width: '100%' }} disabled={loading}>
            {loading ? 'Working…' : mode === 'signin' ? 'Sign in' : 'Create account'}
          </button>
        </form>

        <div style={{ display: 'flex', alignItems: 'center', gap: 10, margin: '18px 0' }}>
          <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
          <span style={{ fontSize: 11, color: 'var(--text-low)' }}>OR</span>
          <div style={{ flex: 1, height: 1, background: 'var(--border)' }} />
        </div>

        <button onClick={handleGoogleAuth} className="btn-secondary" style={{ width: '100%' }}>
          Continue with Google
        </button>
      </div>

      <p style={{ fontSize: 13, marginTop: 20, color: 'var(--text-mid)', textAlign: 'center' }}>
        {mode === 'signin' ? "Don't have an account? " : 'Already have an account? '}
        <a onClick={() => setMode(mode === 'signin' ? 'signup' : 'signin')} style={{ cursor: 'pointer' }}>
          {mode === 'signin' ? 'Sign up' : 'Sign in'}
        </a>
      </p>
    </div>
  );
}
