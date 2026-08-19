/**
 * Document upload API.
 *
 * Documents use multipart/form-data, so this endpoint
 * intentionally uses fetch() instead of the normal JSON
 * post() helper from client.ts.
 */

export interface DocumentChunk {
  id: number;
  title: string;
  uuid: string;
}

export interface DocumentUploadResponse {
  success: boolean;

  message: string;

  data: {
    title: string;
    category: string;
    source: string;

    chunks_created: number;

    chunks: DocumentChunk[];
  };
}


const DOCUMENT_UPLOAD_URL =
  "http://127.0.0.1:8000/api/v1/documents/upload";


export async function uploadDocument(
  file: File,
  category: string
): Promise<DocumentUploadResponse> {

  const token =
    localStorage.getItem(
      "access_token"
    );


  const formData =
    new FormData();


  formData.append(
    "file",
    file
  );


  formData.append(
    "category",
    category
  );


  const headers: HeadersInit = {
    Accept:
      "application/json",
  };


  if (token) {

    headers.Authorization =
      `Bearer ${token}`;

  }


  const response =
    await fetch(
      DOCUMENT_UPLOAD_URL,
      {
        method: "POST",
        headers,
        body: formData,
      }
    );


  /*
   * Authentication expired.
   */

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


  /*
   * Handle API errors.
   */

  if (!response.ok) {

    let message =
      `Document upload failed with status ${response.status}.`;


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

        message =
          errorText;
      }

    }


    throw new Error(
      message
    );
  }


  /*
   * Parse successful response.
   */

  return (
    await response.json()
  ) as DocumentUploadResponse;
}