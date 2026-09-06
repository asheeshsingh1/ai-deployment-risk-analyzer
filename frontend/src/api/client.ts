const API_BASE_URL =
    import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

    export class ApiError extends Error {
    status: number;

    constructor(message: string, status: number) {
        super(message);
        this.name = "ApiError";
        this.status = status;
    }
    }

    async function request<T>(
    path: string,
    options?: RequestInit,
    ): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${path}`, {
        ...options,
        headers: {
        "Content-Type": "application/json",
        ...(options?.headers ?? {}),
        },
    });

    if (!response.ok) {
        let message = `Request failed with status ${response.status}`;

        try {
        const body = (await response.json()) as {
            detail?: string;
        };

        if (body.detail) {
            message = body.detail;
        }
        } catch {
        // Keep the default error message when the response isn't JSON.
        }

        throw new ApiError(message, response.status);
    }

    return response.json() as Promise<T>;
    }

    export function getHealth(): Promise<{
    status: string;
    database?: string;
    }> {
    return request("/health");
}