import type {
    HistoricalIntelligence as HistoricalIntelligenceData,
    } from "../types/analysis";

    interface HistoricalIntelligenceProps {
    intelligence: HistoricalIntelligenceData | null;
    }

    function HistoricalIntelligence({
    intelligence,
    }: HistoricalIntelligenceProps) {
    if (!intelligence) {
        return (
        <section className="dashboard-card">
            <p className="card-label">
            Historical Intelligence
            </p>

            <h3>No historical data</h3>

            <p className="muted-text">
            No deployment or incident history was available
            for the affected service.
            </p>
        </section>
        );
    }

    const { deployments, incidents } = intelligence;

    return (
        <section className="dashboard-card wide-card">
        <div className="section-heading compact-heading">
            <div>
            <p className="card-label">
                Historical Intelligence
            </p>

            <h3>{intelligence.service}</h3>
            </div>

            <span className="history-window">
            Last {intelligence.window_days} days
            </span>
        </div>

        <div className="history-metrics">
            <div className="history-metric">
            <strong>{deployments.total_deployments}</strong>
            <span>Deployments</span>
            </div>

            <div className="history-metric">
            <strong>{deployments.successful_deployments}</strong>
            <span>Successful</span>
            </div>

            <div className="history-metric">
            <strong>{deployments.failed_deployments}</strong>
            <span>Failed</span>
            </div>

            <div className="history-metric">
            <strong>{deployments.rolled_back_deployments}</strong>
            <span>Rollbacks</span>
            </div>

            <div className="history-metric">
            <strong>{incidents.total_incidents}</strong>
            <span>Incidents</span>
            </div>

            <div className="history-metric">
            <strong>{incidents.high_severity}</strong>
            <span>High severity</span>
            </div>
        </div>

        <div className="history-details">
            <div>
            <span>Failure rate</span>
            <strong>
                {(deployments.failure_rate * 100).toFixed(1)}%
            </strong>
            </div>

            <div>
            <span>Rollback rate</span>
            <strong>
                {(deployments.rollback_rate * 100).toFixed(1)}%
            </strong>
            </div>

            <div>
            <span>Recent incidents</span>
            <strong>{incidents.recent_incidents}</strong>
            </div>
        </div>

        {intelligence.evidence.length > 0 && (
            <div className="evidence-section">
            <p className="card-label">Evidence</p>

            <ul>
                {intelligence.evidence.map((item) => (
                <li key={item}>{item}</li>
                ))}
            </ul>
            </div>
        )}
        </section>
    );
}

export default HistoricalIntelligence;