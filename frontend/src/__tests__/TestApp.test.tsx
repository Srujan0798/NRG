import React, { useState } from 'react';

interface Researcher {
  researcher_id: string;
  name: string;
  institution_id: string;
  state: string;
  research_area: string | null;
  year_joined: number | null;
  email: string | null;
  phone: string | null;
  orcid: string | null;
  created_at: string;
  updated_at: string;
}

function TestApp() {
  const [researchers, setResearchers] = useState<Researcher[]>([]);
  const [loading, setLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const fetchResearchers = async () => {
    setLoading(true);
    setErrorMessage(null);
    try {
      const response = await fetch('/researchers', {
        headers: {
          'Authorization': 'Bearer dev-key-insecure-change-in-production'
        }
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setResearchers(data);
    } catch (error) {
      console.error('Error fetching researchers:', error);
      setErrorMessage('Failed to fetch researchers. Please try again.');
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>National Research Graph Test</h1>
      
      <button 
        onClick={fetchResearchers} 
        disabled={loading}
        aria-label="Fetch researchers from database"
        style={{ 
          padding: '10px 20px', 
          fontSize: '16px', 
          marginBottom: '20px',
          border: '1px solid #007acc',
          backgroundColor: loading ? '#ccc' : '#007acc',
          color: 'white',
          borderRadius: '4px',
          cursor: loading ? 'not-allowed' : 'pointer'
        }}
        onFocus={(e) => e.currentTarget.style.boxShadow = '0 0 0 2px #007acc'}
        onBlur={(e) => e.currentTarget.style.boxShadow = 'none'}
      >
        {loading ? 'Loading…' : 'Fetch Researchers'}
      </button>

      {errorMessage && (
        <p role="alert" style={{ color: '#b91c1c', marginBottom: '16px' }}>
          {errorMessage}
        </p>
      )}

      <h2>Researchers ({researchers.length})</h2>
      
      {researchers.length === 0 && !loading && (
        <p>No researchers found. Click the button above to fetch data.</p>
      )}

      <div style={{ display: 'grid', gap: '20px', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))' }}>
        {researchers.map((researcher) => (
          <article 
            key={researcher.researcher_id}
            style={{ 
              border: '1px solid #e1e4e8', 
              padding: '20px', 
              borderRadius: '8px',
              backgroundColor: '#fff',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
            }}
            aria-label={`Researcher: ${researcher.name}`}
          >
            <h3 style={{ margin: '0 0 12px 0', color: '#24292e', fontSize: '18px' }}>
              {researcher.name}
            </h3>
            
            <div style={{ display: 'grid', gap: '8px' }}>
              <p style={{ margin: 0 }}>
                <strong style={{ color: '#586069' }}>Research Area:</strong>{' '}
                <span>{researcher.research_area || 'Not specified'}</span>
              </p>
              
              <p style={{ margin: 0 }}>
                <strong style={{ color: '#586069' }}>Institution:</strong>{' '}
                <span>{researcher.institution_id}</span>
              </p>
              
              <p style={{ margin: 0 }}>
                <strong style={{ color: '#586069' }}>State:</strong>{' '}
                <span>{researcher.state}</span>
              </p>
              
              <p style={{ margin: 0 }}>
                <strong style={{ color: '#586069' }}>Joined:</strong>{' '}
                <span>{researcher.year_joined || 'Unknown'}</span>
              </p>
              
              {researcher.email && (
                <p style={{ margin: 0 }}>
                  <strong style={{ color: '#586069' }}>Email:</strong>{' '}
                  <a 
                    href={`mailto:${researcher.email}`}
                    style={{ color: '#0366d6', textDecoration: 'none' }}
                    onMouseEnter={(e) => e.currentTarget.style.textDecoration = 'underline'}
                    onMouseLeave={(e) => e.currentTarget.style.textDecoration = 'none'}
                  >
                    {researcher.email}
                  </a>
                </p>
              )}
            </div>
            
            <footer style={{ 
              marginTop: '16px', 
              paddingTop: '12px', 
              borderTop: '1px solid #e1e4e8',
              fontSize: '12px', 
              color: '#6a737d' 
            }}>
              <p style={{ margin: 0 }}>
                ID: {researcher.researcher_id}
              </p>
            </footer>
          </article>
        ))}
      </div>
    </div>
  );
}

export default TestApp;

test('exports the legacy test app harness', () => {
  expect(TestApp).toBeDefined();
});
