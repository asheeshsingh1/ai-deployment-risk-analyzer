import type { ChangedFile } from "../types/analysis";

interface ChangedFilesProps {
    files: ChangedFile[];
    }

    function ChangedFiles({ files }: ChangedFilesProps) {
    return (
        <section className="dashboard-card wide-card">
        <div className="section-heading compact-heading">
            <div>
            <p className="card-label">Change Surface</p>
            <h3>Changed files</h3>
            </div>

            <span className="factor-count">
            {files.length} {files.length === 1 ? "file" : "files"}
            </span>
        </div>

        <div className="changed-files">
            {files.map((file) => (
            <details className="changed-file" key={file.filename}>
                <summary>
                <div className="file-name">
                    <span className="file-status">
                    {file.status}
                    </span>

                    <strong>{file.filename}</strong>
                </div>

                <div className="file-stats">
                    <span className="additions">
                    +{file.additions}
                    </span>

                    <span className="deletions">
                    -{file.deletions}
                    </span>

                    <span>{file.changes} changes</span>
                </div>
                </summary>

                {file.patch && (
                <pre className="code-diff">
                    {file.patch}
                </pre>
                )}
            </details>
            ))}
        </div>
        </section>
    );
}

export default ChangedFiles;