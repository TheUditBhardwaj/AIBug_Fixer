import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import styles from './Results.module.css';
import BugList from './BugList';

function SectionLabel({ children }) {
  return <p className={styles.sectionLabel}>{children}</p>;
}

function MonoTag({ children }) {
  return <code className={styles.monoTag}>{children}</code>;
}

export default function Results({ result, originalCode, language = 'python' }) {
  if (!result) return null;

  const bugs        = result.bugs || [];
  const explanation = result.explanation;
  const suggestions = result.suggestions || [];
  const fixedCode   = result.fixed_code;
  const lang        = result.language || language;

  return (
    <div className={styles.wrap}>
      {/* Language tag */}
      {lang && lang !== 'auto-detect' && (
        <div className={styles.langRow}>
          <MonoTag>Detected: {lang}</MonoTag>
        </div>
      )}

      {/* Bugs */}
      <BugList bugs={bugs} />

      {/* Explanation */}
      {explanation && (
        <section className={styles.section}>
          <SectionLabel>Analysis Summary</SectionLabel>
          <p className={styles.explanationText}>{explanation}</p>
        </section>
      )}

      {/* Code comparison — single file */}
      {fixedCode && typeof fixedCode === 'string' && originalCode && (
        <section className={styles.section}>
          <SectionLabel>Code Comparison</SectionLabel>
          <div className={styles.diffGrid}>
            <div>
              <p className={styles.diffLabel}>Original</p>
              <SyntaxHighlighter
                language={lang}
                style={vscDarkPlus}
                customStyle={codeStyle}
                showLineNumbers
              >
                {originalCode}
              </SyntaxHighlighter>
            </div>
            <div>
              <p className={styles.diffLabel}>Fixed</p>
              <SyntaxHighlighter
                language={lang}
                style={vscDarkPlus}
                customStyle={codeStyle}
                showLineNumbers
              >
                {fixedCode}
              </SyntaxHighlighter>
            </div>
          </div>
        </section>
      )}

      {/* Fixed files — repo mode */}
      {fixedCode && typeof fixedCode === 'object' && Object.keys(fixedCode).length > 0 && (
        <FixedFiles files={fixedCode} />
      )}

      {/* Suggestions */}
      {suggestions.length > 0 && (
        <section className={styles.section}>
          <SectionLabel>Recommendations</SectionLabel>
          <ul className={styles.suggList}>
            {suggestions.map((s, i) => (
              <li key={i} className={styles.suggItem}>
                <span className={styles.dash}>—</span>
                <span>{s}</span>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}

function FixedFiles({ files }) {
  const [selected, setSelected] = React.useState(Object.keys(files)[0]);
  return (
    <section className={Results.section}>
      <p className={styles.sectionLabel}>Fixed Files</p>
      <div className={styles.fileTabBar}>
        {Object.keys(files).map(f => (
          <button
            key={f}
            className={`${styles.fileTab} ${selected === f ? styles.fileTabActive : ''}`}
            onClick={() => setSelected(f)}
          >
            {f}
          </button>
        ))}
      </div>
      {selected && (
        <SyntaxHighlighter
          language="python"
          style={vscDarkPlus}
          customStyle={codeStyle}
          showLineNumbers
        >
          {files[selected]}
        </SyntaxHighlighter>
      )}
    </section>
  );
}

// need React for useState in FixedFiles
import React from 'react';

const codeStyle = {
  borderRadius: '8px',
  fontSize: '0.8rem',
  lineHeight: '1.6',
  border: '1px solid rgba(255,255,255,0.07)',
  background: '#0d1117',
};
