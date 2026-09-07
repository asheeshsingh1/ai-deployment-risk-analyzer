import { useState } from "react";

import AIInsights from "./components/AIInsights";
import AnalysisForm from "./components/AnalysisForm";
import ChangedFiles from "./components/ChangedFiles";
import Header from "./components/Header";
import HistoricalIntelligence from "./components/HistoricalIntelligence";
import PageContainer from "./components/PageContainer";
import RiskFactors from "./components/RiskFactors";
import RiskSummary from "./components/RiskSummary";
import type { AnalysisResponse } from "./types/analysis";

function App() {
    const [analysis, setAnalysis] =
        useState<AnalysisResponse | null>(null);

    function handleAnalysisComplete(
        result: AnalysisResponse,
    ) {
        setAnalysis(result);

        window.setTimeout(() => {
            document
                .getElementById("analysis-results")
                ?.scrollIntoView({
                    behavior: "smooth",
                    block: "start",
                });
        }, 50);
    }

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

                            <h3>
                                Analyze a pull or merge request
                            </h3>

                            <p className="section-description">
                                Paste a GitHub Pull Request or GitLab
                                Merge Request URL. The analyzer will
                                automatically identify the repository,
                                service, and change request.
                            </p>
                        </div>
                    </div>

                    <AnalysisForm
                        onAnalysisComplete={
                            handleAnalysisComplete
                        }
                    />
                </section>

                {analysis ? (
                    <section
                        id="analysis-results"
                        className="results-section"
                    >
                        <div className="results-header">
                            <div>
                                <p className="section-label">
                                    Analysis Results
                                </p>

                                <h2>
                                    Deployment risk assessment
                                </h2>

                                <p>
                                    Deterministic risk scoring enriched
                                    with historical intelligence and AI
                                    analysis.
                                </p>
                            </div>

                            <div className="results-change-types">
                                {analysis.change_types.map((type) => (
                                    <span key={type}>
                                        {type.replaceAll("_", " ")}
                                    </span>
                                ))}
                            </div>
                        </div>

                        <RiskSummary analysis={analysis} />

                        <div className="results-grid">
                            {analysis.service_assessments.length > 0 ? (
                                <RiskFactors
                                    factors={
                                        analysis
                                            .service_assessments[0]
                                            .factors
                                    }
                                />
                            ) : (
                                <RiskFactors factors={[]} />
                            )}

                            <section className="dashboard-card">
                                <p className="card-label">
                                    Change Summary
                                </p>

                                <h3>Change surface</h3>

                                <div className="summary-metrics">
                                    <div>
                                        <strong>
                                            {analysis.files_changed}
                                        </strong>

                                        <span>
                                            Files changed
                                        </span>
                                    </div>

                                    <div>
                                        <strong>
                                            +{analysis.lines_added}
                                        </strong>

                                        <span>
                                            Lines added
                                        </span>
                                    </div>

                                    <div>
                                        <strong>
                                            -{analysis.lines_deleted}
                                        </strong>

                                        <span>
                                            Lines deleted
                                        </span>
                                    </div>
                                </div>

                                <div className="signal-list">
                                    {analysis.risk_signals.map(
                                        (signal) => (
                                            <span key={signal}>
                                                {signal.replaceAll(
                                                    "_",
                                                    " ",
                                                )}
                                            </span>
                                        ),
                                    )}
                                </div>
                            </section>
                        </div>

                        <ChangedFiles
                            files={analysis.changed_files}
                        />

                        {analysis.service_assessments.map(
                            (assessment) => (
                                <HistoricalIntelligence
                                    key={assessment.service}
                                    intelligence={
                                        assessment.historical_intelligence
                                    }
                                />
                            ),
                        )}

                        <AIInsights
                            explanation={
                                analysis.ai_explanation
                            }
                            recommendation={
                                analysis.ai_recommendation
                            }
                        />
                    </section>
                ) : (
                    <section className="dashboard-grid">
                        <article className="dashboard-card risk-engine-card">
                            <div className="risk-engine-info">
                                <button
                                    type="button"
                                    className="risk-info-button"
                                    aria-label="Show risk level definitions"
                                >
                                    i
                                </button>

                                <div className="risk-level-tooltip">
                                    <p className="risk-level-tooltip-title">
                                        Risk levels
                                    </p>

                                    <div className="risk-level-tooltip-row">
                                        <span>0–24</span>
                                        <strong className="risk-low">Low</strong>
                                    </div>

                                    <div className="risk-level-tooltip-row">
                                        <span>25–49</span>
                                        <strong className="risk-medium">Medium</strong>
                                    </div>

                                    <div className="risk-level-tooltip-row">
                                        <span>50–74</span>
                                        <strong className="risk-high">High</strong>
                                    </div>

                                    <div className="risk-level-tooltip-row">
                                        <span>75–100</span>
                                        <strong className="risk-critical">Critical</strong>
                                    </div>
                                </div>
                            </div>

                            <p className="card-label">
                                Risk Engine
                            </p>

                            <h3>
                                Deterministic scoring
                            </h3>

                            <p>
                                Risk scores are calculated from
                                explicit engineering signals
                                rather than being determined by
                                the language model.
                            </p>

                            <div className="metric-row">
                                <div>
                                    <strong>100</strong>
                                    <span>
                                        Maximum score
                                    </span>
                                </div>

                                <div>
                                    <strong>4</strong>
                                    <span>
                                        Risk levels
                                    </span>
                                </div>
                            </div>
                        </article>

                        <article className="dashboard-card">
                            <p className="card-label">
                                Historical Intelligence
                            </p>

                            <h3>
                                Learn from deployment history
                            </h3>

                            <p>
                                Deployment outcomes and incidents
                                provide additional context for
                                current change risk.
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

                            <h3>
                                Context-aware recommendations
                            </h3>

                            <p>
                                Gemini explains the evidence behind
                                the deterministic risk assessment
                                and provides actionable deployment
                                recommendations.
                            </p>
                        </article>
                    </section>
                )}
            </PageContainer>
        </div>
    );
}

export default App;