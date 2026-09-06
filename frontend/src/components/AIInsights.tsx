interface AIInsightsProps {
    explanation: string | null;
    recommendation: string | null;
    }

    function formatRecommendation(text: string) {
    return text
        .split("\n")
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => line.replace(/^\d+\.\s*/, ""));
    }

    function AIInsights({
    explanation,
    recommendation,
    }: AIInsightsProps) {
    if (!explanation && !recommendation) {
        return (
        <section className="dashboard-card wide-card">
            <p className="card-label">AI Assistance</p>

            <h3>No AI assessment available</h3>

            <p className="muted-text">
            The deterministic risk assessment is available,
            but no AI explanation or recommendation was
            generated.
            </p>
        </section>
        );
    }

    const recommendations = recommendation
        ? formatRecommendation(recommendation)
        : [];

    return (
        <section className="dashboard-card wide-card ai-card">
        <div className="section-heading compact-heading">
            <div>
            <p className="card-label">AI Assistance</p>

            <h3>Context-aware assessment</h3>
            </div>

            <span className="ai-badge">Gemini</span>
        </div>

        {explanation && (
            <div className="ai-section">
            <p className="ai-section-label">Explanation</p>

            <div className="ai-explanation">
                {explanation.split("\n\n").map((paragraph) => (
                <p key={paragraph}>{paragraph}</p>
                ))}
            </div>
            </div>
        )}

        {recommendations.length > 0 && (
            <div className="ai-section">
            <p className="ai-section-label">
                Recommended actions
            </p>

            <ol className="recommendation-list">
                {recommendations.map((item) => (
                <li key={item}>{item}</li>
                ))}
            </ol>
            </div>
        )}
        </section>
    );
}

export default AIInsights;