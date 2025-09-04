import React, { useState, useEffect } from 'react';
import './App.css';

function App() {
  const [stats, setStats] = useState(null);
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedTab, setSelectedTab] = useState('dashboard');

  const API_BASE_URL = 'http://localhost:8000';

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      // Load statistics
      const statsResponse = await fetch(`${API_BASE_URL}/api/dashboard/statistics`);
      if (!statsResponse.ok) {
        throw new Error(`Stats API error: ${statsResponse.status}`);
      }
      const statsData = await statsResponse.json();
      setStats(statsData);
      
      // Load recent documents
      const docsResponse = await fetch(`${API_BASE_URL}/api/documents?size=10`);
      if (!docsResponse.ok) {
        throw new Error(`Documents API error: ${docsResponse.status}`);
      }
      const docsData = await docsResponse.json();
      setDocuments(docsData.documents || []);
      
    } catch (error) {
      console.error('Error loading dashboard data:', error);
      setError(`Failed to load data: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('client_name', 'Demo Client');
      formData.append('case_type', 'civil');

      const response = await fetch(`${API_BASE_URL}/api/documents/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`Upload failed: ${response.status}`);
      }

      const result = await response.json();
      alert(`Document uploaded successfully! ID: ${result.id}`);
      setUploadFile(null);
      loadDashboardData(); // Refresh data
      
    } catch (error) {
      console.error('Upload error:', error);
      alert(`Upload failed: ${error.message}`);
    } finally {
      setUploading(false);
    }
  };

  const searchDocuments = async () => {
    if (!searchQuery.trim()) {
      loadDashboardData();
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/documents?q=${encodeURIComponent(searchQuery)}`);
      if (!response.ok) {
        throw new Error(`Search failed: ${response.status}`);
      }
      const data = await response.json();
      setDocuments(data.documents || []);
    } catch (error) {
      console.error('Search error:', error);
      setError(`Search failed: ${error.message}`);
    }
  };

  const refreshData = () => {
    loadDashboardData();
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
        <h2>Loading DocuScan Dashboard...</h2>
        <p>Connecting to backend services...</p>
      </div>
    );
  }

  if (error && !stats) {
    return (
      <div className="error-screen">
        <div className="error-content">
          <h2>⚠️ Connection Error</h2>
          <p>{error}</p>
          <button onClick={refreshData} className="retry-button">
            🔄 Retry Connection
          </button>
          <div className="error-details">
            <p>Make sure the backend is running at {API_BASE_URL}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <h1>🏛️ DocuScan Legal Document Classifier</h1>
          <div className="header-info">
            <span className="version">Production v2.0.0</span>
            <span className="status online">● ONLINE</span>
          </div>
        </div>
        
        <nav className="nav-tabs">
          <button 
            className={selectedTab === 'dashboard' ? 'active' : ''}
            onClick={() => setSelectedTab('dashboard')}
          >
            📊 Dashboard
          </button>
          <button 
            className={selectedTab === 'documents' ? 'active' : ''}
            onClick={() => setSelectedTab('documents')}
          >
            📄 Documents
          </button>
          <button 
            className={selectedTab === 'upload' ? 'active' : ''}
            onClick={() => setSelectedTab('upload')}
          >
            📤 Upload
          </button>
        </nav>
      </header>
      
      <main className="main-content">
        {error && (
          <div className="error-banner">
            <span>⚠️ {error}</span>
            <button onClick={() => setError(null)}>✕</button>
          </div>
        )}

        {selectedTab === 'dashboard' && (
          <div className="dashboard-tab">
            <div className="stats-section">
              <h2>📈 System Statistics</h2>
              <div className="stats-grid">
                <div className="stat-card">
                  <h3>Total Documents</h3>
                  <div className="stat-number">{stats?.total_documents || 0}</div>
                  <div className="stat-label">Processed</div>
                </div>
                
                <div className="stat-card priority">
                  <h3>High Priority</h3>
                  <div className="stat-number">{stats?.high_priority_count || 0}</div>
                  <div className="stat-label">Urgent Review</div>
                </div>
                
                <div className="stat-card critical">
                  <h3>Critical Priority</h3>
                  <div className="stat-number">{stats?.critical_priority_count || 0}</div>
                  <div className="stat-label">Immediate Action</div>
                </div>
                
                <div className="stat-card">
                  <h3>Active Clients</h3>
                  <div className="stat-number">{stats?.active_clients || 0}</div>
                  <div className="stat-label">Unique Clients</div>
                </div>
              </div>
              
              <button onClick={refreshData} className="refresh-button">
                🔄 Refresh Data
              </button>
            </div>
            
            <div className="charts-section">
              <div className="chart-card">
                <h3>📊 Case Type Distribution</h3>
                <div className="case-types">
                  {stats?.case_type_distribution?.map((item, index) => (
                    <div key={index} className="case-type-item">
                      <span className="case-type-name">{item.case_type}</span>
                      <span className="case-type-count">{item.count}</span>
                      <span className="case-type-percentage">{item.percentage}%</span>
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="chart-card">
                <h3>🚨 Urgency Levels</h3>
                <div className="urgency-levels">
                  {stats?.urgency_distribution?.map((item, index) => (
                    <div key={index} className={`urgency-item ${item.urgency_level}`}>
                      <span className="urgency-name">{item.urgency_level}</span>
                      <span className="urgency-count">{item.count}</span>
                      <span className="urgency-percentage">{item.percentage}%</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {selectedTab === 'documents' && (
          <div className="documents-tab">
            <div className="search-section">
              <h2>🔍 Document Search</h2>
              <div className="search-bar">
                <input
                  type="text"
                  placeholder="Search documents, clients, or case types..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && searchDocuments()}
                />
                <button onClick={searchDocuments}>🔍 Search</button>
                <button onClick={() => { setSearchQuery(''); loadDashboardData(); }}>
                  🔄 Clear
                </button>
              </div>
            </div>
            
            <div className="documents-list">
              <h3>📄 Recent Documents ({documents.length})</h3>
              {documents.length === 0 ? (
                <div className="empty-state">
                  <p>No documents found. Try uploading some documents or check your search criteria.</p>
                </div>
              ) : (
                <div className="documents-grid">
                  {documents.map((doc, index) => (
                    <div key={index} className="document-card">
                      <div className="doc-header">
                        <h4>{doc.filename}</h4>
                        <span className={`status ${doc.status}`}>{doc.status}</span>
                      </div>
                      <div className="doc-details">
                        <p><strong>Client:</strong> {doc.client_name}</p>
                        <p><strong>Case Type:</strong> {doc.case_type}</p>
                        <p><strong>Urgency:</strong> 
                          <span className={`urgency ${doc.urgency_level}`}>
                            {doc.urgency_level}
                          </span>
                        </p>
                        <p><strong>Size:</strong> {Math.round(doc.file_size_bytes / 1024)} KB</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {selectedTab === 'upload' && (
          <div className="upload-tab">
            <div className="upload-section">
              <h2>📤 Upload Document</h2>
              <form onSubmit={handleFileUpload} className="upload-form">
                <div className="file-input-section">
                  <label htmlFor="file" className="file-label">
                    {uploadFile ? `📄 ${uploadFile.name}` : '📁 Choose File'}
                  </label>
                  <input
                    id="file"
                    type="file"
                    onChange={(e) => setUploadFile(e.target.files[0])}
                    accept=".pdf,.docx,.doc,.txt,.png,.jpg,.jpeg"
                    style={{ display: 'none' }}
                  />
                </div>
                
                {uploadFile && (
                  <div className="file-info">
                    <p><strong>Selected:</strong> {uploadFile.name}</p>
                    <p><strong>Size:</strong> {Math.round(uploadFile.size / 1024)} KB</p>
                    <p><strong>Type:</strong> {uploadFile.type}</p>
                  </div>
                )}
                
                <button 
                  type="submit" 
                  disabled={!uploadFile || uploading}
                  className="upload-button"
                >
                  {uploading ? '⏳ Uploading...' : '🚀 Upload & Process'}
                </button>
              </form>
              
              <div className="upload-info">
                <h3>📋 Supported Formats</h3>
                <div className="supported-formats">
                  <span>📄 PDF</span>
                  <span>📝 DOCX</span>
                  <span>📄 DOC</span>
                  <span>📰 TXT</span>
                  <span>🖼️ PNG</span>
                  <span>🖼️ JPG</span>
                </div>
              </div>
            </div>
          </div>
        )}
        
        <div className="features-section">
          <h2>🎯 System Features</h2>
          <div className="features-grid">
            <div className="feature">
              <h4>📄 OCR Processing</h4>
              <p>Tesseract-powered text extraction from PDFs and images</p>
            </div>
            <div className="feature">
              <h4>🧠 NLP Classification</h4>
              <p>spaCy-based legal document categorization and entity extraction</p>
            </div>
            <div className="feature">
              <h4>🔍 Advanced Search</h4>
              <p>Elasticsearch-powered full-text search with filtering</p>
            </div>
            <div className="feature">
              <h4>📊 Real-time Analytics</h4>
              <p>Live dashboard with comprehensive statistics and metrics</p>
            </div>
          </div>
        </div>
      </main>
      
      <footer className="App-footer">
        <div className="footer-content">
          <div className="system-status">
            <p>🔗 System Status: <span className="online">ONLINE</span></p>
            <p>🔗 API: Connected | 📊 Elasticsearch: Active | 💾 Redis: Connected</p>
          </div>
          <div className="tech-stack">
            <p>Built with React + FastAPI + Elasticsearch + Docker</p>
            <p>Last updated: {stats?.last_updated ? new Date(stats.last_updated).toLocaleString() : 'Loading...'}</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;