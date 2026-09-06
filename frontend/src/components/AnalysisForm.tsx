import { useState } from "react";
import { analyzeChange, ApiError } from "../api/client";
import type {
    AnalysisRequest,
    AnalysisResponse,
    SCMProvider,
    } from "../types/analysis";

    interface AnalysisFormProps {
    onAnalysisComplete: (result: AnalysisResponse) => void;
    }

    function AnalysisForm({
    onAnalysisComplete,
    }: AnalysisFormProps) {
    const [provider, setProvider] =
        useState<SCMProvider>("github");

    const [owner, setOwner] = useState("");
    const [repository, setRepository] = useState("");
    const [changeNumber, setChangeNumber] = useState("");

    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    async function handleSubmit(
        event: React.SubmitEvent<HTMLFormElement>,
    ) {
        event.preventDefault();

        setError("");

        const parsedChangeNumber = Number(changeNumber);

        if (!owner.trim()) {
        setError("Owner is required.");
        return;
        }

        if (!repository.trim()) {
        setError("Repository is required.");
        return;
        }

        if (
        !Number.isInteger(parsedChangeNumber) ||
        parsedChangeNumber <= 0
        ) {
        setError(
            "Change request number must be a positive integer.",
        );
        return;
        }

        const payload: AnalysisRequest = {
        provider,
        owner: owner.trim(),
        repository: repository.trim(),
        change_number: parsedChangeNumber,
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
            <label className="form-field">
            <span>Provider</span>

            <select
                value={provider}
                onChange={(event) =>
                setProvider(
                    event.target.value as SCMProvider,
                )
                }
                disabled={loading}
            >
                <option value="github">GitHub</option>
                <option value="gitlab">GitLab</option>
            </select>
            </label>

            <label className="form-field">
            <span>Owner / Group</span>

            <input
                type="text"
                value={owner}
                onChange={(event) =>
                setOwner(event.target.value)
                }
                placeholder="e.g. asheeshsingh0112"
                disabled={loading}
            />
            </label>

            <label className="form-field">
            <span>Repository</span>

            <input
                type="text"
                value={repository}
                onChange={(event) =>
                setRepository(event.target.value)
                }
                placeholder="e.g. ide"
                disabled={loading}
            />
            </label>

            <label className="form-field">
            <span>PR / MR Number</span>

            <input
                type="number"
                min="1"
                step="1"
                value={changeNumber}
                onChange={(event) =>
                setChangeNumber(event.target.value)
                }
                placeholder="e.g. 1"
                disabled={loading}
            />
            </label>
        </div>

        {error && (
            <div className="form-error" role="alert">
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