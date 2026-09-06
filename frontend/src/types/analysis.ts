export type SCMProvider = "github" | "gitlab";

export interface AnalysisRequest {
    provider: SCMProvider;
    owner: string;
    repository: string;
    change_number: number;
}

export interface RiskFactor {
    name: string;
    description: string;
    score: number;
}

export interface HistoricalDeploymentHistory {
    total_deployments: number;
    successful_deployments: number;
    failed_deployments: number;
    rolled_back_deployments: number;
    failure_rate: number;
    rollback_rate: number;
    recent_deployments: number;
}

export interface HistoricalIncidentHistory {
    total_incidents: number;
    low_severity: number;
    medium_severity: number;
    high_severity: number;
    critical_severity: number;
    recent_incidents: number;
}

export interface HistoricalIntelligence {
    service: string;
    window_days: number;
    deployments: HistoricalDeploymentHistory;
    incidents: HistoricalIncidentHistory;
    evidence: string[];
}

export interface ChangedFile {
    filename: string;
    status: string;
    additions: number;
    deletions: number;
    changes: number;
    patch: string | null;
}

export interface ServiceAssessment {
    service: string;
    score: number;
    level: string;
    factors: RiskFactor[];
    recommendation: string;
    historical_intelligence: HistoricalIntelligence | null;
}

export interface AnalysisResponse {
    repository: string;
    change_request_number: number;
    change_request_title: string;
    affected_services: string[];
    change_types: string[];
    risk_signals: string[];
    files_changed: number;
    lines_added: number;
    lines_deleted: number;
    changed_files: ChangedFile[];
    service_assessments: ServiceAssessment[];
    overall_score: number;
    overall_level: string;
    recommendation: string;
    ai_explanation: string | null;
    ai_recommendation: string | null;
}