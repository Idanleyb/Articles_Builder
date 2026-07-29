'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { supabaseBrowser } from '@/lib/supabaseClient';

interface Article {
  id: string;
  title: string;
  body: string;
  hashtags: string[];
  source_topic: string;
  source_summary: string;
  platform: string;
  created_at: string;
}

interface UserConfig {
  topics: string[];
  tone_text: string | null;
  articles_per_week: number;
  platform: string;
}

export default function Dashboard() {
  const router = useRouter();
  const supabase = supabaseBrowser();

  const [articles, setArticles] = useState<Article[]>([]);
  const [config, setConfig] = useState<UserConfig>({
    topics: [], tone_text: null, articles_per_week: 2, platform: 'linkedin',
  });
  const [topicsInput, setTopicsInput] = useState('');
  const [saving, setSaving] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [freshId, setFreshId] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) { router.push('/login'); return; }

      const cfgRes = await fetch('/api/config');
      const cfgJson = await cfgRes.json();
      if (cfgJson.config) {
        setConfig(cfgJson.config);
        setTopicsInput((cfgJson.config.topics ?? []).join(', '));
      }

      const { data: articleRows } = await supabase
        .from('articles')
        .select('*')
        .order('created_at', { ascending: false });
      setArticles(articleRows ?? []);
    })();
  }, []);

  async function saveConfig() {
    setSaving(true);
    const topics = topicsInput.split(',').map((t) => t.trim()).filter(Boolean);
    await fetch('/api/config', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...config, topics }),
    });
    setSaving(false);
  }

  async function uploadTone(file: File) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch('/api/tone-upload', { method: 'POST', body: formData });
    const json = await res.json();
    if (json.preview) {
      setConfig((c) => ({ ...c, tone_text: json.preview }));
    }
  }

  async function generateNow() {
    setGenerating(true);
    const res = await fetch('/api/generate', { method: 'POST' });
    const json = await res.json();
    setGenerating(false);
    if (json.article) {
      setArticles((prev) => [json.article, ...prev]);
      setFreshId(json.article.id);
      setTimeout(() => setFreshId(null), 4000);
    }
  }

  function copyArticle(article: Article) {
    const text = `${article.title}\n\n${article.body}\n\n${article.hashtags.map((h) => '#' + h.replace(/^#/, '')).join(' ')}`;
    navigator.clipboard.writeText(text);
    setCopiedId(article.id);
    setTimeout(() => setCopiedId(null), 1500);
  }

  return (
    <div style={{ maxWidth: 880, margin: '0 auto', padding: '48px 24px 80px' }}>
      <header style={{ marginBottom: 36 }}>
        <p className="eyebrow" style={{ marginBottom: 8 }}>YOUR WORKSPACE</p>
        <h1
          className="aurora-text"
          style={{ fontFamily: 'var(--font-display)', fontSize: 32, margin: 0, lineHeight: 1.1 }}
        >
          Articles Builder
        </h1>
        <p style={{ color: 'var(--text-mid)', fontSize: 14, marginTop: 8 }}>
          Set your topics and tone once — new articles show up here, ready to publish.
        </p>
      </header>

      <div className="glass-card" style={{ marginBottom: 28 }}>
        <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 17, margin: '0 0 18px' }}>Settings</h2>

        <label className="field-label">Topics</label>
        <input
          className="field-input"
          style={{ marginBottom: 16 }}
          value={topicsInput}
          onChange={(e) => setTopicsInput(e.target.value)}
          placeholder="e.g. B2B SaaS growth, fintech UX, AI in music"
        />

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 4 }}>
          <div>
            <label className="field-label">Articles per week</label>
            <input
              className="field-input"
              type="number"
              min={1}
              max={7}
              value={config.articles_per_week}
              onChange={(e) => setConfig((c) => ({ ...c, articles_per_week: Number(e.target.value) }))}
            />
          </div>
          <div>
            <label className="field-label">Platform</label>
            <select
              className="field-input"
              value={config.platform}
              onChange={(e) => setConfig((c) => ({ ...c, platform: e.target.value }))}
            >
              <option value="linkedin">LinkedIn</option>
            </select>
          </div>
        </div>

        <label className="field-label" style={{ marginTop: 12 }}>
          Tone file (.docx or .txt) — optional, a sensible default is used if skipped
        </label>
        <input
          className="field-input"
          style={{ marginBottom: 6, padding: '9px 13px' }}
          type="file"
          accept=".docx,.txt"
          onChange={(e) => e.target.files?.[0] && uploadTone(e.target.files[0])}
        />
        {config.tone_text && (
          <p style={{ fontSize: 12, color: 'var(--success)', margin: '8px 0 4px' }}>
            Tone loaded: "{config.tone_text.slice(0, 120)}…"
          </p>
        )}

        <div style={{ display: 'flex', gap: 12, marginTop: 18 }}>
          <button className="btn-primary" onClick={saveConfig} disabled={saving}>
            {saving ? 'Saving…' : 'Save settings'}
          </button>
          <button
            className={`btn-secondary ${generating ? 'thinking' : ''}`}
            onClick={generateNow}
            disabled={generating}
          >
            {generating ? 'Researching + writing…' : 'Generate an article now'}
          </button>
        </div>
      </div>

      <h2 style={{ fontFamily: 'var(--font-display)', fontSize: 17, margin: '0 0 16px' }}>Your articles</h2>
      {articles.length === 0 && (
        <p style={{ color: 'var(--text-low)', fontSize: 13.5 }}>
          Nothing yet — save your settings, then try "Generate an article now."
        </p>
      )}
      {articles.map((article) => (
        <div
          key={article.id}
          className={`glass-card ${freshId === article.id ? 'fresh' : ''}`}
          style={{ marginBottom: 18 }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 12 }}>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 18, margin: 0 }}>{article.title}</h3>
            <span className="mono" style={{ fontSize: 11, color: 'var(--text-low)', whiteSpace: 'nowrap' }}>
              {new Date(article.created_at).toLocaleDateString()}
            </span>
          </div>
          <p style={{ fontSize: 11.5, color: 'var(--text-low)', margin: '8px 0 14px' }} className="mono">
            SOURCE — {article.source_topic}: {article.source_summary}
          </p>
          <p style={{ fontSize: 14.5, lineHeight: 1.65, whiteSpace: 'pre-wrap', color: 'var(--text-hi)', opacity: 0.92 }}>
            {article.body}
          </p>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 14 }}>
            {article.hashtags.map((h) => (
              <span key={h} className="pill">#{h.replace(/^#/, '')}</span>
            ))}
          </div>
          <button className="btn-secondary" style={{ marginTop: 16, fontSize: 13, padding: '8px 18px' }} onClick={() => copyArticle(article)}>
            {copiedId === article.id ? 'Copied ✓' : 'Copy for LinkedIn'}
          </button>
        </div>
      ))}
    </div>
  );
}
