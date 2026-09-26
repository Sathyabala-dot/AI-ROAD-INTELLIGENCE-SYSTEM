import "./style.css";

function App() {
  return (
    <div className="app">

      {/* SIDEBAR */}
      <aside className="sidebar">

        <div className="brand">
          <div className="brand-icon">🚧</div>

          <div>
            <h2>RoadSense</h2>
            <span>AI Intelligence</span>
          </div>
        </div>

        <nav className="nav-menu">

          <a href="#dashboard" className="nav-link active">
            📊
            <span>Dashboard</span>
          </a>

          <a href="#map-section" className="nav-link">
            🗺️
            <span>Road Map</span>
          </a>

          <a href="#analytics" className="nav-link">
            📈
            <span>Analytics</span>
          </a>

          <a href="#maintenance" className="nav-link">
            🔧
            <span>Maintenance</span>
          </a>

        </nav>

        <div className="sidebar-bottom">

          <div className="system-status">
            <span className="status-dot"></span>

            <div>
              <strong>System Online</strong>
              <small>AI Engine Connected</small>
            </div>
          </div>

          <p>© 2026 Team 07</p>

        </div>

      </aside>


      {/* MAIN CONTENT */}
      <main className="main-content">

        {/* HEADER */}
        <header className="topbar" id="dashboard">

          <div>
            <p className="breadcrumb">
              Tamil Nadu / Road Intelligence
            </p>

            <h1>Road Health Overview</h1>

            <p className="subtitle">
              AI-powered monitoring and predictive intelligence for safer roads.
            </p>
          </div>

          <div className="header-actions">

            <div className="date-box">
              📅
              <span>26 Sep 2026</span>
            </div>

            <button className="icon-button">
              🔄
            </button>

            <div className="profile">

              <div className="avatar">
                👤
              </div>

              <div className="profile-info">
                <strong>Administrator</strong>
                <span>Logged In</span>
              </div>

            </div>

          </div>

        </header>


        {/* KPI CARDS */}
        <section className="stats-grid">

          <div className="stat-card">

            <div className="stat-icon blue">
              🚧
            </div>

            <div className="stat-info">
              <p>Roads Monitored</p>
              <h2>0</h2>

              <span className="positive">
                ↑ 12.5%
              </span>
            </div>

          </div>


          <div className="stat-card">

            <div className="stat-icon green">
              ❤️
            </div>

            <div className="stat-info">

              <p>Average Health Score</p>

              <h2>
                0 <small>/100</small>
              </h2>

              <span className="positive">
                Healthy Network
              </span>

            </div>

          </div>


          <div className="stat-card">

            <div className="stat-icon orange">
              ⚠️
            </div>

            <div className="stat-info">

              <p>Critical Issues</p>

              <h2>0</h2>

              <span className="negative">
                Requires Attention
              </span>

            </div>

          </div>


          <div className="stat-card">

            <div className="stat-icon purple">
              🔧
            </div>

            <div className="stat-info">

              <p>Maintenance Priority</p>

              <h2>0</h2>

              <span className="warning">
                High Priority
              </span>

            </div>

          </div>

        </section>


        {/* MAP + ALERTS */}
        <section className="dashboard-grid" id="map-section">

          <div className="map-card card">

            <div className="section-header">

              <div>
                <h2>Live Road Intelligence Map</h2>

                <p>
                  Interactive GIS visualization of road conditions
                </p>
              </div>

              <div className="map-controls">

                <button className="filter-btn active">
                  All Roads
                </button>

                <button className="filter-btn">
                  Critical
                </button>

                <button className="filter-btn">
                  Medium
                </button>

                <button className="filter-btn">
                  Healthy
                </button>

              </div>

            </div>

            {/* MAP WILL COME HERE */}
            <div id="map">
              Map Loading...
            </div>

            <div className="map-legend">

              <span>
                <i className="legend good"></i>
                Healthy
              </span>

              <span>
                <i className="legend moderate"></i>
                Moderate
              </span>

              <span>
                <i className="legend critical"></i>
                Critical
              </span>

            </div>

          </div>


          {/* ALERTS */}
          <div className="alert-card card">

            <div className="section-header">

              <div>
                <h2>Priority Alerts</h2>
                <p>AI detected issues</p>
              </div>

              <span>🔔</span>

            </div>

            <div className="alerts-list">

              <p>No data available yet.</p>

            </div>

          </div>

        </section>


        {/* ANALYTICS */}
        <section
          className="analytics-section"
          id="analytics"
        >

          <div className="section-title">

            <div>
              <p className="eyebrow">
                INTELLIGENCE ANALYTICS
              </p>

              <h2>Road Network Insights</h2>
            </div>

          </div>


          <div className="charts-grid">

            <div className="chart-card card">

              <div className="chart-heading">

                <h3>Condition Distribution</h3>

                <p>
                  Roads by predicted condition, right now
                </p>

              </div>

              <div className="chart-placeholder">
                Chart will appear here
              </div>

            </div>


            <div className="chart-card card">

              <div className="chart-heading">

                <h3>Maintenance Priority Breakdown</h3>

                <p>
                  Roads by maintenance priority, right now
                </p>

              </div>

              <div className="chart-placeholder">
                Chart will appear here
              </div>

            </div>

          </div>

        </section>


        {/* MAINTENANCE */}
        <section
          className="maintenance-section"
          id="maintenance"
        >

          <div className="section-title">

            <div>

              <p className="eyebrow">
                ACTION CENTER
              </p>

              <h2>Maintenance Priority</h2>

              <p className="section-description">
                AI-ranked road segments requiring maintenance attention.
              </p>

            </div>

            <button className="primary-btn">
              📄 Download Report
            </button>

          </div>


          <div className="table-card card">

            <div className="table-responsive">

              <table>

                <thead>

                  <tr>
                    <th>Road ID</th>
                    <th>Location</th>
                    <th>Health Score</th>
                    <th>Detected Issue</th>
                    <th>Risk Level</th>
                    <th>Priority</th>
                    <th>Action</th>
                  </tr>

                </thead>

                <tbody>

                  <tr>
                    <td colSpan="7">
                      No maintenance data available.
                    </td>
                  </tr>

                </tbody>

              </table>

            </div>

          </div>

        </section>

      </main>

    </div>
  );
}

export default App;