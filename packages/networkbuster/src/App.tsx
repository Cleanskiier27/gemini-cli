import { FormEvent, useState } from 'react';

function App() {
  const [url, setUrl] = useState('https://example.com');
  const [result, setResult] = useState<string>('Ready to test network requests.');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const trimmedUrl = url.trim();

    if (!trimmedUrl) {
      setResult('Please enter a valid URL.');
      return;
    }

    setLoading(true);
    setResult('Fetching...');

    try {
      const response = await fetch(trimmedUrl, { method: 'GET' });
      const text = await response.text();
      const body = text.slice(0, 2000);

      setResult(
        `Status: ${response.status} ${response.statusText}\n` +
        `Content-Type: ${response.headers.get('content-type') ?? 'unknown'}\n\n` +
        body +
        (text.length > 2000 ? '\n\n...output truncated...' : '')
      );
    } catch (error) {
      setResult(`Request failed: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <h1>NetworkBuster</h1>
      <p>Enter a URL to test connectivity and display response details.</p>
      <form onSubmit={handleSubmit}>
        <input
          type="url"
          value={url}
          onChange={(event) => setUrl(event.target.value)}
          placeholder="https://example.com"
          required
          autoFocus
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Fetching…' : 'Fetch'}
        </button>
      </form>
      <div className="result">{result}</div>
    </>
  );
}

export default App;
