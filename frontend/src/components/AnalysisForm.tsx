import { useState } from "react";

import { analyzeChange, ApiError } from "../api/client";
import type {
    AnalysisRequest,
    AnalysisResponse,
    } from "../types/analysis";

    interface AnalysisFormProps {
    onAnalysisComplete: (result: AnalysisResponse) => void;
    }

    function AnalysisForm({
    onAnalysisComplete,
    }: AnalysisFormProps) {
    const [changeRequestUrl, setChangeRequestUrl] =
        useState("");

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    async function handleSubmit(
        event: React.FormEvent<HTMLFormElement>,
    ) {
        event.preventDefault();

        setError("");

        const url = changeRequestUrl.trim();

        if (!url) {
        setError("Pull request or merge request URL is required.");
        return;
        }

        try {
        const parsedUrl = new URL(url);

        if (parsedUrl.protocol !== "http:" &&
            parsedUrl.protocol !== "https:") {
            setError(
            "Please enter a valid GitHub or GitLab URL.",
            );
            return;
        }
        } catch {
        setError(
            "Please enter a valid GitHub or GitLab URL.",
        );
        return;
        }

        const payload: AnalysisRequest = {
        change_request_url: url,
        };

        setLoading(true);

        try {
        const result = await analyzeChange(payload);

        onAnalysisComplete(result);
        } catch (err) {
        if (err instanceof ApiError) {
            setError(err.message);
        } else if (err instanceof TypeError) {
            setError(
            "Unable to connect to the API. Make sure the backend is running on http://localhost:8000.",
            );
        } else {
            setError(
            "Unable to analyze the change. Please try again.",
            );
        }
        } finally {
        setLoading(false);
        }
    }

    return (
        <form
        className="analysis-form"
        onSubmit={handleSubmit}
        >
        <div className="form-grid">
            <label className="form-field full-width">
            <span>Change Request</span>

            <input
                type="url"
                value={changeRequestUrl}
                onChange={(event) =>
                setChangeRequestUrl(event.target.value)
                }
                placeholder="https://github.com/owner/repository/pull/123"
                disabled={loading}
                autoComplete="off"
            />

            <small className="form-help">
                Paste a GitHub Pull Request or GitLab Merge Request URL.
            </small>
            </label>
        </div>

        {error && (
            <div
            className="form-error"
            role="alert"
            >
            {error}
            </div>
        )}

        <div className="form-actions">
            <button
            type="submit"
            className="primary-button"
            disabled={loading}
            >
            {loading ? (
                <>
                <span className="loading-spinner" />
                Analyzing...
                </>
            ) : (
                "Analyze Change"
            )}
            </button>
        </div>
        </form>
    );
}

export default AnalysisForm;