import Header from "./components/Header";
import PageContainer from "./components/PageContainer";

function App() {
    return (
        <div className="app">
        <Header />

        <PageContainer>
            <section className="hero-section">
            <div>
                <p className="section-label">Deployment intelligence</p>

                <h2>
                Understand deployment risk before
                <span> shipping the change.</span>
                </h2>

                <p className="hero-description">
                Analyze GitHub and GitLab changes using deterministic risk
                signals, historical deployment outcomes, service ownership,
                and AI-assisted recommendations.
                </p>
            </div>
            </section>

            <section className="dashboard-grid">
            <article className="dashboard-card">
                <p className="card-label">Change Analysis</p>

                <h3>Analyze a change request</h3>

                <p>
                Connect a GitHub pull request or GitLab merge request to
                evaluate its deployment risk.
                </p>

                <button type="button" className="primary-button">
                Start Analysis
                </button>
            </article>

            <article className="dashboard-card">
                <p className="card-label">Risk Engine</p>

                <h3>Deterministic scoring</h3>

                <p>
                Risk scores are calculated from explicit engineering signals
                rather than being determined by the language model.
                </p>

                <div className="metric-row">
                <div>
                    <strong>100</strong>
                    <span>Maximum score</span>
                </div>

                <div>
                    <strong>4</strong>
                    <span>Risk levels</span>
                </div>
                </div>
            </article>

            <article className="dashboard-card wide-card">
                <p className="card-label">Historical Intelligence</p>

                <h3>Learn from deployment history</h3>

                <p>
                Historical deployments and incidents provide context for
                current change risk and help identify services that require
                additional validation.
                </p>

                <div className="feature-list">
                <span>Deployment outcomes</span>
                <span>Rollback history</span>
                <span>Incident severity</span>
                <span>Recent operational signals</span>
                </div>
            </article>
            </section>
        </PageContainer>
        </div>
    );
}

export default App;