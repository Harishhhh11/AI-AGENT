import {
  useRef,
  useState,
} from "react";

import type {
  ChangeEvent,
  DragEvent,
} from "react";

import {
  uploadDocument,
} from "../api/documents";

import type {
  DocumentUploadResponse,
} from "../api/documents";


const ALLOWED_EXTENSIONS = [
  ".pdf",
  ".docx",
  ".txt",
];


interface UploadedDocument {
  title: string;
  category: string;
  source: string;
  chunks_created: number;
}


export default function Documents() {

  const fileInputRef =
    useRef<HTMLInputElement | null>(
      null
    );


  const [
    selectedFile,
    setSelectedFile,
  ] = useState<File | null>(
    null
  );


  const [
    category,
    setCategory,
  ] = useState(
    "general"
  );


  const [
    uploading,
    setUploading,
  ] = useState(false);


  const [
    successMessage,
    setSuccessMessage,
  ] = useState<
    string | null
  >(null);


  const [
    errorMessage,
    setErrorMessage,
  ] = useState<
    string | null
  >(null);


  const [
    uploadedDocuments,
    setUploadedDocuments,
  ] = useState<
    UploadedDocument[]
  >([]);

  const [
    isDragging,
    setIsDragging,
  ] = useState(false);


  // =============================================================
  // FILE SELECTION
  // =============================================================

  function selectFile(file?: File) {


    setSuccessMessage(
      null
    );

    setErrorMessage(
      null
    );


    if (!file) {

      setSelectedFile(
        null
      );

      return;
    }


    const filename =
      file.name.toLowerCase();


    const isAllowed =
      ALLOWED_EXTENSIONS.some(
        (extension) =>
          filename.endsWith(
            extension
          )
      );


    if (!isAllowed) {

      setSelectedFile(
        null
      );

      setErrorMessage(
        "Only PDF, DOCX and TXT files are allowed."
      );

      return;
    }


    setSelectedFile(
      file
    );
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    selectFile(event.target.files?.[0]);
  }

  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
    selectFile(event.dataTransfer.files?.[0]);
  }


  // =============================================================
  // UPLOAD
  // =============================================================

  async function handleUpload() {

    if (!selectedFile) {

      setErrorMessage(
        "Please select a document first."
      );

      return;
    }


    setUploading(
      true
    );

    setSuccessMessage(
      null
    );

    setErrorMessage(
      null
    );


    try {

      const result:
        DocumentUploadResponse =
        await uploadDocument(
          selectedFile,
          category
        );


      // ---------------------------------------------------------
      // Add document to recent uploads
      // ---------------------------------------------------------

      const uploadedDocument:
        UploadedDocument = {
          title:
            result.data.title,

          category:
            result.data.category,

          source:
            result.data.source,

          chunks_created:
            result.data.chunks_created,
        };


      setUploadedDocuments(
        (previous) => [
          uploadedDocument,
          ...previous,
        ]
      );


      // ---------------------------------------------------------
      // Success message
      // ---------------------------------------------------------

      setSuccessMessage(
        `${result.message} ${result.data.chunks_created} chunks were created and embedded.`
      );


      // ---------------------------------------------------------
      // Clear selected file
      // ---------------------------------------------------------

      setSelectedFile(
        null
      );


      if (
        fileInputRef.current
      ) {

        fileInputRef.current.value =
          "";
      }

    } catch (error) {

      console.error(
        "Document upload error:",
        error
      );


      setErrorMessage(
        error instanceof Error
          ? error.message
          : "Document upload failed."
      );

    } finally {

      setUploading(
        false
      );
    }
  }


  // =============================================================
  // FILE SIZE FORMATTER
  // =============================================================

  function formatFileSize(
    size: number
  ): string {

    if (
      size <
      1024
    ) {

      return `${size} B`;
    }


    if (
      size <
      1024 * 1024
    ) {

      return `${(
        size / 1024
      ).toFixed(1)} KB`;
    }


    return `${(
      size /
      (1024 * 1024)
    ).toFixed(1)} MB`;
  }


  // =============================================================
  // UI
  // =============================================================

  return (
    <div>

      {/* =======================================================
          HEADER
      ======================================================== */}

      <div className="mb-8">

        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">Knowledge ingestion</p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
          Documents
        </h1>

        <p className="mt-1 text-sm text-slate-500">
          Upload company documents to make them
          available to the AI receptionist.
        </p>

      </div>


      {/* =======================================================
          UPLOAD CARD
      ======================================================== */}

      <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_12px_40px_rgba(15,23,42,0.06)] sm:p-6">

        <h2 className="text-lg font-semibold text-slate-900">
          Upload Document
        </h2>

        <p className="mt-1 text-sm text-slate-500">
          Supported formats: PDF, DOCX and TXT.
        </p>


        {/* =====================================================
            FILE + CATEGORY
        ====================================================== */}

        <div className="mt-6 grid gap-5 md:grid-cols-[1.4fr_0.6fr]">

          {/* FILE */}

          <div>

            <label className="mb-2 block text-sm font-semibold text-slate-700">
              Document
            </label>

            <div
              onDragOver={(event) => { event.preventDefault(); setIsDragging(true); }}
              onDragLeave={() => setIsDragging(false)}
              onDrop={handleDrop}
              className={`rounded-2xl border-2 border-dashed p-5 text-center transition ${isDragging ? "border-indigo-500 bg-indigo-50" : "border-slate-200 bg-slate-50/70 hover:border-indigo-300 hover:bg-indigo-50/40"}`}
            >
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-white text-lg shadow-sm">↑</div>
              <p className="mt-3 text-sm font-semibold text-slate-700">Drop a document here</p>
              <p className="mt-1 text-xs text-slate-500">or select a PDF, DOCX, or TXT file</p>
              <button type="button" disabled={uploading} onClick={() => fileInputRef.current?.click()} className="mt-4 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:border-indigo-200 hover:text-indigo-700 disabled:opacity-50">Choose file</button>
              <input ref={fileInputRef} type="file" accept=".pdf,.docx,.txt" onChange={handleFileChange} disabled={uploading} className="sr-only" />
            </div>

          </div>


          {/* CATEGORY */}

          <div>

            <label className="mb-2 block text-sm font-semibold text-slate-700">
              Category
            </label>

            <select
              value={
                category
              }
              onChange={
                (event) =>
                  setCategory(
                    event.target.value
                  )
              }
              disabled={
                uploading
              }
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 outline-none transition focus:border-indigo-500 focus:bg-white focus:ring-4 focus:ring-indigo-500/10"
            >

              <option value="general">
                General
              </option>

              <option value="courses">
                Courses
              </option>

              <option value="admissions">
                Admissions
              </option>

              <option value="pricing">
                Pricing
              </option>

              <option value="services">
                Services
              </option>

              <option value="policies">
                Policies
              </option>

              <option value="company">
                Company
              </option>

            </select>

          </div>

        </div>


        {/* =====================================================
            SELECTED FILE
        ====================================================== */}

        {selectedFile && (

          <div className="mt-5 rounded-2xl border border-indigo-100 bg-indigo-50/60 p-4">

            <div className="flex items-center justify-between">

              <div>

                <p className="text-sm font-medium text-slate-900">
                  {selectedFile.name}
                </p>

                <p className="mt-1 text-xs text-slate-500">
                  {formatFileSize(
                    selectedFile.size
                  )}
                </p>

              </div>

              <span className="rounded-full bg-indigo-100 px-3 py-1 text-xs font-semibold text-indigo-700">
                Ready
              </span>

            </div>

          </div>

        )}


        {/* =====================================================
            SUCCESS
        ====================================================== */}

        {successMessage && (

          <div className="mt-5 rounded-2xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">

            {successMessage}

          </div>

        )}


        {/* =====================================================
            ERROR
        ====================================================== */}

        {errorMessage && (

          <div className="mt-5 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">

            {errorMessage}

          </div>

        )}


        {/* =====================================================
            UPLOAD BUTTON
        ====================================================== */}

        <div className="mt-6">

          <button
            type="button"
            onClick={
              handleUpload
            }
            disabled={
              uploading ||
              !selectedFile
            }
            className="rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
          >

            {uploading
              ? "Processing & Indexing..."
              : "Upload & Index"}

          </button>

        </div>

      </div>


      {/* =======================================================
          RECENT UPLOADS
      ======================================================== */}

      {uploadedDocuments.length > 0 && (

        <div className="mt-8 overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-[0_8px_30px_rgba(15,23,42,0.04)]">

          <div className="border-b border-slate-200 p-6">

            <h2 className="font-semibold text-slate-900">
              Recently Uploaded
            </h2>

            <p className="mt-1 text-sm text-slate-500">
              Documents uploaded during this session.
            </p>

          </div>


          <div className="divide-y divide-slate-100">

            {uploadedDocuments.map(
              (
                document,
                index
              ) => (

                <div
                  key={`${document.title}-${index}`}
                  className="flex items-center justify-between p-5"
                >

                  <div>

                    <p className="text-sm font-medium text-slate-900">
                      {document.title}
                    </p>

                    <div className="mt-1 flex flex-wrap gap-3 text-xs text-slate-500">

                      <span>
                        {document.category}
                      </span>

                      <span>
                        {document.source}
                      </span>

                      <span>
                        {document.chunks_created} chunks
                      </span>

                    </div>

                  </div>


                  <span className="rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-700">
                    Indexed
                  </span>

                </div>

              )
            )}

          </div>

        </div>

      )}


      {/* =======================================================
          HOW IT WORKS
      ======================================================== */}

      <div className="mt-8 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_8px_30px_rgba(15,23,42,0.04)] sm:p-6">

        <h2 className="font-semibold text-slate-900">
          How document indexing works
        </h2>


        <div className="mt-5 grid gap-4 md:grid-cols-4">

          <Step
            number="1"
            title="Upload"
            description="Select a PDF, DOCX or TXT file."
          />

          <Step
            number="2"
            title="Extract"
            description="The backend extracts readable text."
          />

          <Step
            number="3"
            title="Chunk & Embed"
            description="The text is split into chunks and converted into semantic vectors."
          />

          <Step
            number="4"
            title="Search"
            description="The AI retrieves relevant document chunks during conversations."
          />

        </div>

      </div>

    </div>
  );
}


// =============================================================
// STEP COMPONENT
// =============================================================

interface StepProps {
  number: string;
  title: string;
  description: string;
}


function Step({
  number,
  title,
  description,
}: StepProps) {

  return (
    <div className="rounded-2xl border border-slate-100 bg-slate-50 p-4">

      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-600 text-sm font-bold text-white">
        {number}
      </div>

      <h3 className="mt-4 text-sm font-semibold text-slate-900">
        {title}
      </h3>

      <p className="mt-1 text-xs leading-5 text-slate-500">
        {description}
      </p>

    </div>
  );
}
