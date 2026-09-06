import type { RiskFactor } from "../types/analysis";

interface RiskFactorsProps {
    factors: RiskFactor[];
    }

    function RiskFactors({ factors }: RiskFactorsProps) {
    if (factors.length === 0) {
        return (
        <section className="dashboard-card">
            <p className="card-label">Risk Factors</p>

            <h3>No elevated factors detected</h3>

            <p className="muted-text">
            The deterministic risk engine did not identify any
            additional risk factors for this change.
            </p>
        </section>
        );
    }

    return (
        <section className="dashboard-card">
        <div className="section-heading compact-heading">
            <div>
            <p className="card-label">Risk Factors</p>
            <h3>Why this change is risky</h3>
            </div>

            <span className="factor-count">
            {factors.length}{" "}
            {factors.length === 1 ? "factor" : "factors"}
            </span>
        </div>

        <div className="risk-factor-list">
            {factors.map((factor) => (
            <div className="risk-factor" key={factor.name}>
                <div className="risk-factor-score">
                +{factor.score}
                </div>

                <div className="risk-factor-content">
                <strong>
                    {factor.name.replaceAll("_", " ")}
                </strong>

                <p>{factor.description}</p>
                </div>
            </div>
            ))}
        </div>
        </section>
    );
}

export default RiskFactors;