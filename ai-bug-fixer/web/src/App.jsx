import { useState, useRef } from 'react';
import { analyzeCode, analyzeFile, analyzeRepo, checkHealth } from './api';
import Results from './components/Results';
import styles from './App.module.css';

// ── tiny shared UI ──────────────────────────────────────────────
function Label({ children }) {
  return <p className={styles.label}>{children}</p>;
}

function Input({ id, ...props }) {
  return <input id={id} className={styles.input} {...props} />;
}

function Textarea({ id, ...props }) {
  return <textarea id={id} className={styles.textarea} {...props} />;
}

function Select({ id, options, value, onChange }) {
  return (
    <select id={id} className={styles.select} value={value} onChange={onChange}>
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  );
}

function Btn({ children, loading, variant = 'primary', ...props }) {
  return (
    <button className={`${styles.btn} ${styles[variant]}`} disabled={loading} {...props}>
      {loading
        ? <><span className={styles.spinner} /> Analyzing…</>
        : children}
    </button>
  );
}

function Divider() { return <hr className={styles.divider} />; }

function SectionHead({ children }) {
  return <p className={styles.sectionHead}>{children}</p>;
}

function ErrorBox({ msg }) {
  if (!msg) return null;
  return <div className={styles.errorBox}>{msg}</div>;
}

// ── TABS ────────────────────────────────────────────────────────
const TABS = ['Code Input', 'File Upload', 'GitHub Repository'];

// ── APP ─────────────────────────────────────────────────────────
export default function App() {
  const [activeTab, setActiveTab] = useState(0);
  const [results, setResults]     = useState({});   // keyed by tab index
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState('');
  const [healthy, setHealthy]     = useState(null); // null | true | false

  // code tab
  const [code, setCode]       = useState('');
  const [filename, setFn]     = useState('');
  const [language, setLang]   = useState('Auto-detect');

  // file tab
  const [file, setFile]       = useState(null);
  const fileRef               = useRef();

  // repo tab
  const [repoUrl, setRepo]    = useState('');
  const [branch, setBranch]   = useState('main');
  const [progress, setProgress] = useState(0);
  const [progText, setProgText] = useState('');

  const LANGS = ['Auto-detect','Python','JavaScript','TypeScript','Java','C++','Go','Rust','Ruby','PHP'];

  function clearTab(tab) {
    setResults(r => { const n = {...r}; delete n[tab]; return n; });
    setError('');
  }

  async function runCodeAnalysis() {
    if (!code.trim()) { setError('Please enter some code.'); return; }
    setError(''); setLoading(true);
    try {
      const r = await analyzeCode(code, filename || null);
      setResults(rv => ({...rv, [0]: { result: r, original: code } }));
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  }

  async function runFileAnalysis() {
    if (!file) { setError('Please select a file.'); return; }
    setError(''); setLoading(true);
    try {
      const r = await analyzeFile(file);
      const text = await file.text();
      setResults(rv => ({...rv, [1]: { result: r, original: text } }));
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally { setLoading(false); }
  }

  async function runRepoAnalysis() {
    if (!repoUrl.trim())             { setError('Please enter a repository URL.'); return; }
    if (!repoUrl.includes('github.com')) { setError('Please enter a valid GitHub URL.'); return; }
    setError(''); setLoading(true); setProgress(10); setProgText('Cloning repository…');
    const tick = setInterval(() => {
      setProgress(p => { if (p >= 80) return p; return p + 5; });
    }, 2000);
    try {
      setProgText('Indexing files…');
      const r = await analyzeRepo(repoUrl, branch);
      setProgress(100); setProgText('Complete');
      setResults(rv => ({...rv, [2]: { result: r, repoUrl } }));
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally { clearInterval(tick); setLoading(false); }
  }

  async function testHealth() {
    try { await checkHealth(); setHealthy(true); } catch { setHealthy(false); }
  }

  const current = results[activeTab];

  return (
    <div className={styles.layout}>
      {/* ── Sidebar ── */}
      <aside className={styles.sidebar}>
        <p className={styles.sideTitle}>Configuration</p>

        <Label>Backend URL</Label>
        <Input
          defaultValue={import.meta.env.VITE_API_URL || 'http://localhost:8000'}
          placeholder="http://localhost:8000"
        />

        <div className={styles.sideRow}>
          <button className={`${styles.sideBtn}`} onClick={testHealth}>Test</button>
          <button className={`${styles.sideBtn}`} onClick={() => {
            setResults({}); setError(''); setCode(''); setFn(''); setFile(null); setRepo(''); 
          }}>Clear</button>
        </div>

        {healthy === true  && <p className={styles.connected}>Connected</p>}
        {healthy === false && <p className={styles.disconnected}>Unreachable</p>}

        <hr className={styles.sideDivider} />

        <p className={styles.sideSection}>Detection</p>
        {['Syntax errors','Logic bugs','Performance issues','Security vulnerabilities','Code quality'].map(f => (
          <div key={f} className={styles.feature}>
            <span className={styles.dot} />
            <span>{f}</span>
          </div>
        ))}

        <hr className={styles.sideDivider} />

        <p className={styles.sideSection}>Usage</p>
        <p className={styles.sideHint}><strong>Code Input</strong> — paste source code</p>
        <p className={styles.sideHint}><strong>File Upload</strong> — upload a source file</p>
        <p className={styles.sideHint}><strong>GitHub Repo</strong> — analyze a repository</p>
      </aside>

      {/* ── Main ── */}
      <main className={styles.main}>
        {/* Hero */}
        <header className={styles.hero}>
          <div className={styles.heroBadge}>
            <span className={styles.heroDot} />
            AI-Powered
          </div>
          <h1 className={styles.heroTitle}>AI Bug Fixer</h1>
          <p className={styles.heroSub}>
            Detect bugs, vulnerabilities and performance issues. Get structured AI-generated fixes
            with clear, actionable explanations.
          </p>
          <div className={styles.heroFeatures}>
            {['Semantic code indexing','Cross-file analysis','GitHub repository support','Parallel file processing']
              .map(f => (
                <span key={f} className={styles.heroFeature}>
                  <span className={styles.greenDot} />
                  {f}
                </span>
              ))}
          </div>
        </header>

        {/* Tabs */}
        <div className={styles.tabBar}>
          {TABS.map((t, i) => (
            <button
              key={t}
              className={`${styles.tab} ${activeTab === i ? styles.tabActive : ''}`}
              onClick={() => { setActiveTab(i); setError(''); }}
            >
              {t}
            </button>
          ))}
        </div>

        <div className={styles.panel}>
          <ErrorBox msg={error} />

          {/* ── Tab 0: Code Input ── */}
          {activeTab === 0 && (
            <>
              <SectionHead>Paste Code</SectionHead>
              <div className={styles.row2}>
                <div>
                  <Label>Language</Label>
                  <Select
                    id="language"
                    options={LANGS}
                    value={language}
                    onChange={e => setLang(e.target.value)}
                  />
                </div>
                <div>
                  <Label>Filename (optional)</Label>
                  <Input
                    id="filename"
                    value={filename}
                    onChange={e => setFn(e.target.value)}
                    placeholder="example.py"
                  />
                </div>
              </div>
              <div>
                <Label>Source Code</Label>
                <Textarea
                  id="code"
                  rows={16}
                  value={code}
                  onChange={e => setCode(e.target.value)}
                  placeholder="Paste your source code here…"
                />
              </div>
              <div className={styles.actionRow}>
                <Btn loading={loading} onClick={runCodeAnalysis} id="btn-analyze-code">
                  Analyze Code
                </Btn>
                {current && (
                  <Btn variant="ghost" onClick={() => clearTab(0)}>Clear Results</Btn>
                )}
              </div>
              {current && (
                <>
                  <Divider />
                  <Results result={current.result} originalCode={current.original} />
                </>
              )}
            </>
          )}

          {/* ── Tab 1: File Upload ── */}
          {activeTab === 1 && (
            <>
              <SectionHead>Upload Source File</SectionHead>
              <div
                className={styles.dropZone}
                onClick={() => fileRef.current?.click()}
                onDragOver={e => e.preventDefault()}
                onDrop={e => { e.preventDefault(); setFile(e.dataTransfer.files[0]); }}
              >
                <input
                  ref={fileRef}
                  type="file"
                  accept=".py,.js,.ts,.jsx,.tsx,.java,.cpp,.c,.go,.rs,.rb,.php,.swift,.kt"
                  style={{ display: 'none' }}
                  onChange={e => setFile(e.target.files[0])}
                />
                {file ? (
                  <div className={styles.fileInfo}>
                    <div className={styles.fileIcon}>
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                           stroke="#a5b4fc" strokeWidth="2">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                        <polyline points="14 2 14 8 20 8"/>
                      </svg>
                    </div>
                    <div>
                      <p className={styles.fileName}>{file.name}</p>
                      <p className={styles.fileSize}>{(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                  </div>
                ) : (
                  <div className={styles.dropHint}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
                         stroke="currentColor" strokeWidth="1.5" style={{ color: 'var(--text3)', marginBottom: 8 }}>
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
                      <polyline points="17 8 12 3 7 8"/>
                      <line x1="12" y1="3" x2="12" y2="15"/>
                    </svg>
                    <p>Drag &amp; drop or click to browse</p>
                    <p className={styles.dropSub}>Python, JS/TS, Java, C/C++, Go, Rust, PHP …</p>
                  </div>
                )}
              </div>
              <div className={styles.actionRow}>
                <Btn loading={loading} onClick={runFileAnalysis} id="btn-analyze-file" disabled={!file || loading}>
                  Analyze File
                </Btn>
                {file && <Btn variant="ghost" onClick={() => { setFile(null); clearTab(1); }}>Remove File</Btn>}
              </div>
              {current && (
                <>
                  <Divider />
                  <Results result={current.result} originalCode={current.original} />
                </>
              )}
            </>
          )}

          {/* ── Tab 2: GitHub Repo ── */}
          {activeTab === 2 && (
            <>
              <SectionHead>Repository Analysis</SectionHead>
              <div className={styles.row2}>
                <div style={{ flex: 4 }}>
                  <Label>Repository URL</Label>
                  <Input
                    id="repo-url"
                    value={repoUrl}
                    onChange={e => setRepo(e.target.value)}
                    placeholder="https://github.com/owner/repository"
                  />
                </div>
                <div style={{ flex: 1 }}>
                  <Label>Branch</Label>
                  <Input
                    id="branch"
                    value={branch}
                    onChange={e => setBranch(e.target.value)}
                  />
                </div>
              </div>

              {loading && progress > 0 && (
                <div className={styles.progressWrap}>
                  <div className={styles.progressBar}>
                    <div className={styles.progressFill} style={{ width: `${progress}%` }} />
                  </div>
                  <p className={styles.progressText}>{progText}</p>
                </div>
              )}

              <div className={styles.actionRow}>
                <Btn loading={loading} onClick={runRepoAnalysis} id="btn-analyze-repo">
                  Analyze Repository
                </Btn>
                {current && <Btn variant="ghost" onClick={() => clearTab(2)}>Clear Results</Btn>}
              </div>

              {current && (
                <>
                  <Divider />
                  <div className={styles.repoTag}>
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none"
                         stroke="currentColor" strokeWidth="2" style={{ color: 'var(--text3)' }}>
                      <path d="M9 19c-5 1.5-5-2.5-7-3m14 6v-3.87a3.37 3.37 0 0 0-.94-2.61
                               c3.14-.35 6.44-1.54 6.44-7A5.44 5.44 0 0 0 20 4.77
                               5.07 5.07 0 0 0 19.91 1S18.73.65 16 2.48a13.38 13.38 0 0 0-7 0
                               C6.27.65 5.09 1 5.09 1A5.07 5.07 0 0 0 5 4.77a5.44 5.44 0 0 0-1.5 3.78
                               c0 5.42 3.3 6.61 6.44 7A3.37 3.37 0 0 0 9 18.13V22"/>
                    </svg>
                    <code className={styles.repoUrl}>{current.repoUrl}</code>
                  </div>
                  <Results result={current.result} />
                </>
              )}
            </>
          )}
        </div>
      </main>
    </div>
  );
}
