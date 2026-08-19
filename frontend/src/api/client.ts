const API_BASE_URL =
  "http://127.0.0.1:8000/api/v1";


function getAccessToken(): string | null {
  return localStorage.getItem(
    "access_token"
  );
}


async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {

  const token =
    getAccessToken();

  const headers = new Headers(
    options.headers
  );

  headers.set(
    "Content-Type",
    "application/json"
  );

  headers.set(
    "Accept",
    "application/json"
  );

  if (token) {
    headers.set(
      "Authorization",
      `Bearer ${token}`
    );
  }

  const response =
    await fetch(
      `${API_BASE_URL}${endpoint}`,
      {
        ...options,
        headers,
      }
    );

  if (
    response.status === 401
  ) {
    localStorage.removeItem(
      "access_token"
    );

    localStorage.removeItem(
      "user"
    );

    window.location.href =
      "/login";

    throw new Error(
      "Authentication required."
    );
  }

  if (!response.ok) {

    let message =
      `Request failed with status ${response.status}.`;

    const contentType =
      response.headers.get(
        "content-type"
      );

    if (
      contentType?.includes(
        "application/json"
      )
    ) {
      const errorData =
        await response.json();

      if (
        typeof errorData ===
          "object" &&
        errorData !== null &&
        "detail" in errorData
      ) {
        message =
          String(
            (
              errorData as {
                detail: unknown;
              }
            ).detail
          );
      }
    } else {
      const errorText =
        await response.text();

      if (errorText) {
        message = errorText;
      }
    }

    throw new Error(message);
  }

  const contentType =
    response.headers.get(
      "content-type"
    );

  if (
    contentType?.includes(
      "application/json"
    )
  ) {
    return (
      await response.json()
    ) as T;
  }

  return (
    await response.text()
  ) as T;
}


export async function get<T>(
  endpoint: string
): Promise<T> {
  return request<T>(
    endpoint,
    {
      method: "GET",
    }
  );
}


export async function post<
  TResponse,
  TBody = unknown
>(
  endpoint: string,
  body: TBody
): Promise<TResponse> {
  return request<TResponse>(
    endpoint,
    {
      method: "POST",
      body: JSON.stringify(body),
    }
  );
}


export async function patch<
  TResponse,
  TBody = unknown
>(
  endpoint: string,
  body: TBody
): Promise<TResponse> {
  return request<TResponse>(
    endpoint,
    {
      method: "PATCH",
      body: JSON.stringify(body),
    }
  );
}


export async function put<
  TResponse,
  TBody = unknown
>(
  endpoint: string,
  body: TBody
): Promise<TResponse> {
  return request<TResponse>(
    endpoint,
    {
      method: "PUT",
      body: JSON.stringify(body),
    }
  );
}


export async function del<T>(
  endpoint: string
): Promise<T> {
  return request<T>(
    endpoint,
    {
      method: "DELETE",
    }
  );
}
export async function uploadFile<T>(
  endpoint: string,
  file: File,
  category: string
): Promise<T> {
  const token =
    getAccessToken();

  const formData =
    new FormData();

  formData.append(
    "file",
    file
  );

  const response =
    await fetch(
      `${API_BASE_URL}${endpoint}?category=${encodeURIComponent(category)}`,
      {
        method: "POST",

        headers: {
          Accept:
            "application/json",

          ...(token
            ? {
                Authorization:
                  `Bearer ${token}`,
              }
            : {}),
        },

        body: formData,
      }
    );

  if (
    response.status === 401
  ) {
    localStorage.removeItem(
      "access_token"
    );

    localStorage.removeItem(
      "user"
    );

    window.location.href =
      "/login";

    throw new Error(
      "Authentication required."
    );
  }

  if (!response.ok) {

    let message =
      `Upload failed with status ${response.status}.`;

    const contentType =
      response.headers.get(
        "content-type"
      );

    if (
      contentType?.includes(
        "application/json"
      )
    ) {
      const errorData =
        await response.json();

      if (
        typeof errorData ===
          "object" &&
        errorData !== null &&
        "detail" in errorData
      ) {
        message =
          String(
            (
              errorData as {
                detail: unknown;
              }
            ).detail
          );
      }
    } else {

      const errorText =
        await response.text();

      if (errorText) {
        message = errorText;
      }
    }

    throw new Error(message);
  }

  return (
    await response.json()
  ) as T;
}