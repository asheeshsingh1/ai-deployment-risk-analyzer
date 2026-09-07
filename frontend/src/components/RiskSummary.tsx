import type { AnalysisResponse } from "../types/analysis";

interface RiskSummaryProps {
    analysis: AnalysisResponse;
}

function getRiskClass(level: string): string {
    return `risk-${level.toLowerCase()}`;
}

function RiskSummary({ analysis }: RiskSummaryProps) {
    return (
        <section className="risk-summary">
            <div className="risk-summary-main">
                <div>
                    <p className="card-label">Deployment Risk</p>

                    <h3>
                        Title: {analysis.change_request_title}
                    </h3>

                    <p className="risk-summary-repository">
                        Owner: {analysis.repository} · Change #
                        {analysis.change_request_number}
                    </p>
                </div>

                <div
            className={`risk-score ${getRiskClass(analysis.overall_level)}`}
                >
                    <strong>{analysis.overall_score}</strong>
                    <span>/ 100</span>
                </div>
            </div>

            <div className="risk-summary-bottom">
                    <div
            className={`risk-level ${getRiskClass(analysis.overall_level)}`}
                    >
                        {analysis.overall_level}
                </div>

                <p>{analysis.recommendation}</p>
            </div>
        </section>
    );
}

export default RiskSummary;