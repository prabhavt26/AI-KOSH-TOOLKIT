const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_URL}${path}`;
  const headers = new Headers(options.headers);

  if (!(options.body instanceof FormData) && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  // Include session cookies for browser authentication
  options.credentials = "include";
  options.headers = headers;

  const response = await fetch(url, options);

  if (!response.ok) {
    if (response.status === 401) {
      throw new Error("Unauthorized: Authentication required.");
    }
    if (response.status === 429) {
      throw new Error("Too Many Requests: Rate limit exceeded. Please try again later.");
    }
    let errorMessage = `HTTP error! status: ${response.status}`;
    try {
      const errorData = await response.json();
      if (errorData.detail) {
        if (typeof errorData.detail === "string") {
          errorMessage = errorData.detail;
        } else if (Array.isArray(errorData.detail)) {
          errorMessage = errorData.detail
            .map((err: { loc: (string | number)[]; msg?: string }) => {
              const field = Array.isArray(err.loc) ? err.loc.filter((x: string | number) => x !== "body" && x !== "metadata").join(" -> ") : err.loc;
              return `${field ? field + ": " : ""}${err.msg || JSON.stringify(err)}`;
            })
            .join("; ");
        } else {
          errorMessage = JSON.stringify(errorData.detail);
        }
      }
    } catch {
      // ignore
    }
    throw new Error(errorMessage);
  }

  if (response.status === 204) {
    return {} as T;
  }

  return response.json();
}

export const api = {
  get<T>(path: string, options?: RequestInit) {
    return request<T>(path, { ...options, method: "GET" });
  },
  post<T>(path: string, body?: unknown, options?: RequestInit) {
    const isFormData = body instanceof FormData;
    return request<T>(path, {
      ...options,
      method: "POST",
      body: isFormData ? body : JSON.stringify(body),
    });
  },
  put<T>(path: string, body?: unknown, options?: RequestInit) {
    const isFormData = body instanceof FormData;
    return request<T>(path, {
      ...options,
      method: "PUT",
      body: isFormData ? body : JSON.stringify(body),
    });
  },
  delete<T>(path: string, options?: RequestInit) {
    return request<T>(path, { ...options, method: "DELETE" });
  },
};
