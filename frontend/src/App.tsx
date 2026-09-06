import { useState } from "react";

import AnalysisForm from "./components/AnalysisForm";
import Header from "./components/Header";
import PageContainer from "./components/PageContainer";
import type { AnalysisResponse } from "./types/analysis";

function App() {
    const [analysis, setAnalysis] =
        useState<AnalysisResponse | null>(null);

    return (
        <div className="app">
        <Header />

        <PageContainer>
            <section className="hero-section">
            <div>
                <p className="section-label">
                Deployment intelligence
                </p>

                <h2>
                Understand deployment risk before
                <span> shipping the change.</span>
                </h2>

                <p className="hero-description">
                Analyze GitHub and GitLab changes using
                deterministic risk signals, historical
                deployment outcomes, service ownership,
                and AI-assisted recommendations.
                </p>
            </div>
            </section>

            <section className="analysis-section">
            <div className="section-heading">
                <div>
                <p className="card-label">
                    Change Analysis
                </p>

                <h3>Analyze a pull or merge request</h3>
                </div>

                <span className="step-indicator">
                Step 1
                </span>
            </div>

            <AnalysisForm
                onAnalysisComplete={setAnalysis}
            />

            {analysis && (
                <div className="analysis-success">
                <div className="success-icon">✓</div>

                <div>
                    <strong>
                    Analysis completed
                    </strong>

                    <p>
                    {analysis.repository} ·{" "}
                    {analysis.change_request_title}
                    </p>
                </div>
                </div>
            )}
            </section>

            <section className="dashboard-grid">
            <article className="dashboard-card">
                <p className="card-label">Risk Engine</p>

                <h3>Deterministic scoring</h3>

                <p>
                Risk scores are calculated from explicit
                engineering signals rather than being
                determined by the language model.
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

            <article className="dashboard-card">
                <p className="card-label">
                Historical Intelligence
                </p>

                <h3>Learn from deployment history</h3>

                <p>
                Deployment outcomes and incidents provide
                additional context for current change risk.
                </p>

                <div className="feature-list">
                <span>Deployments</span>
                <span>Rollbacks</span>
                <span>Incidents</span>
                </div>
            </article>

            <article className="dashboard-card wide-card">
                <p className="card-label">
                AI Assistance
                </p>

                <h3>Context-aware recommendations</h3>

                <p>
                Gemini explains the evidence behind the
                deterministic risk assessment and provides
                actionable deployment recommendations.
                </p>
            </article>
            </section>
        </PageContainer>
        </div>
    );
}

export default App;