import { useRef, useState } from "react";
import { ApiError, ask, login } from "./api.js";

// The JWT lives ONLY in React state — never localStorage/sessionStorage.
// localStorage is readable by any script that gets to run on the page
// (XSS), which makes it a poor home for bearer tokens. The tradeoff:
// refreshing the page drops the token and you log in again. For a
// single-user personal tool with 45-minute tokens, that is an acceptable,
// honestly-documented limitation (see README); the "proper" fix would be
// httpOnly cookie sessions, which is deliberately out of scope here.

function LoginForm({ onLogin, notice }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const data = await login(username, password);
      onLogin(data.access_token, data.expires_in_minutes);
    } catch (err) {
      setError(err instanceof ApiError ? err.detail : "Login failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="card login-card">
      <h2>Sign in</h2>
      {notice && <p className="notice">{notice}</p>}
      <form onSubmit={submit}>
        <label>
          Username
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
            required
          />
        </label>
        {error && <p className="error">{error}</p>}
        <button type="submit" disabled={busy}>
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}

function Sources({ sources }) {
  if (!sources.length) return null;
  return (
    <ul className="sources">
      {sources.map((s) => (
        <li key={s.citation}>
          <span className="citation">{s.citation}</span>
          <span className="score">similarity {s.score.toFixed(3)}</span>
        </li>
      ))}
    </ul>
  );
}

function Message({ msg }) {
  return (
    <div className="exchange">
      <div className="bubble question">{msg.question}</div>
      <div className={`bubble answer ${msg.grounded ? "grounded" : "refused"}`}>
        <span className={`badge ${msg.grounded ? "badge-grounded" : "badge-refused"}`}>
          {msg.grounded ? "Grounded in project docs" : "Refused — not in the docs"}
        </span>
        <p>{msg.answer}</p>
        <Sources sources={msg.sources} />
      </div>
    </div>
  );
}

function Chat({ token, onSessionExpired }) {
  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);
  const listRef = useRef(null);

  async function submit(e) {
    e.preventDefault();
    const q = question.trim();
    if (!q || busy) return;
    setBusy(true);
    setError(null);
    try {
      const data = await ask(token, q);
      setMessages((prev) => [...prev, data]);
      setQuestion("");
      requestAnimationFrame(() => {
        listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
      });
    } catch (err) {
      if (err instanceof ApiError && err.status === 401) {
        onSessionExpired();
      } else if (err instanceof ApiError && err.status === 429) {
        setError("Rate limit reached (10 questions/minute) — wait a moment and try again.");
      } else if (err instanceof ApiError && err.status === 502) {
        setError("The answer service is temporarily unavailable (LLM backend error). Try again shortly.");
      } else {
        setError(err instanceof ApiError ? err.detail : "Something went wrong.");
      }
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="chat">
      <div className="message-list" ref={listRef}>
        {messages.length === 0 && (
          <p className="placeholder">
            Ask about the indexed projects — e.g. “What was the BigQuery
            bytes-scanned reduction?” or “Why does the Kafka setup use KRaft?”
          </p>
        )}
        {messages.map((m, i) => (
          <Message key={i} msg={m} />
        ))}
        {busy && <div className="bubble answer pending">Retrieving &amp; generating…</div>}
      </div>
      {error && <p className="error">{error}</p>}
      <form className="ask-bar" onSubmit={submit}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a question about the projects…"
          disabled={busy}
        />
        <button type="submit" disabled={busy || question.trim().length < 3}>
          {busy ? "…" : "Ask"}
        </button>
      </form>
    </div>
  );
}

export default function App() {
  const [token, setToken] = useState(null);
  const [notice, setNotice] = useState(null);

  return (
    <div className="app">
      <header>
        <h1>AI Interview Prep Assistant</h1>
        <p className="subtitle">RAG over my real project documentation — grounded, cited, honest about gaps</p>
        {token && (
          <button className="logout" onClick={() => { setToken(null); setNotice(null); }}>
            Log out
          </button>
        )}
      </header>
      {token ? (
        <Chat
          token={token}
          onSessionExpired={() => {
            setToken(null);
            setNotice("Session expired — please sign in again.");
          }}
        />
      ) : (
        <LoginForm notice={notice} onLogin={(t) => { setToken(t); setNotice(null); }} />
      )}
      <footer>
        Token is held in memory only (cleared on refresh) — see README for the security tradeoff.
      </footer>
    </div>
  );
}
