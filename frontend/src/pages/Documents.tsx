import { useEffect, useRef, useState } from "react";
import type { ChangeEvent, DragEvent } from "react";
import { getAgents } from "../api/agents";
import type { Agent } from "../api/agents";
import { uploadDocument } from "../api/documents";
import type { DocumentUploadResponse } from "../api/documents";

const ALLOWED_EXTENSIONS = [".pdf", ".docx", ".txt"];

interface UploadedDocument {
  title: string;
  category: string;
  source: string;
  chunks_created: number;
  agent_id?: number | null;
}

export default function Documents() {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [category, setCategory] = useState("general");
  const [agentId, setAgentId] = useState<number | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [uploading, setUploading] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [uploadedDocuments, setUploadedDocuments] = useState<UploadedDocument[]>([]);
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    void getAgents().then(setAgents).catch(() => setAgents([]));
  }, []);

  function selectFile(file?: File) {
    setSuccessMessage(null);
    setErrorMessage(null);
    if (!file) { setSelectedFile(null); return; }
    const filename = file.name.toLowerCase();
    if (!ALLOWED_EXTENSIONS.some((extension) => filename.endsWith(extension))) {
      setSelectedFile(null);
      setErrorMessage("Only PDF, DOCX and TXT files are allowed.");
      return;
    }
    setSelectedFile(file);
  }

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) { selectFile(event.target.files?.[0]); }
  function handleDrop(event: DragEvent<HTMLDivElement>) {
    event.preventDefault();
    setIsDragging(false);
    selectFile(event.dataTransfer.files?.[0]);
  }

  async function handleUpload() {
    if (!selectedFile) { setErrorMessage("Please select a document first."); return; }
    setUploading(true); setSuccessMessage(null); setErrorMessage(null);
    try {
      const result: DocumentUploadResponse = await uploadDocument(selectedFile, category, agentId);
      setUploadedDocuments((previous) => [
        {
          title: result.data.title,
          category: result.data.category,
          source: result.data.source,
          chunks_created: result.data.chunks_created,
          agent_id: result.data.agent_id ?? agentId,
        },
        ...previous,
      ]);
      setSuccessMessage(`${result.message} ${result.data.chunks_created} chunks were created and indexed.`);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = "";
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : "Document upload failed.");
    } finally {
      setUploading(false);
    }
  }

  function formatFileSize(size: number): string {
    if (size < 1024) return `${size} B`;
    if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  }

  const selectedAgentName = agents.find((item) => item.id === agentId)?.name;

  return (
    <div className="space-y-7">
      <div>
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-indigo-600">Knowledge ingestion</p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">Documents</h1>
        <p className="mt-1 text-sm text-slate-500">Upload verified documents and choose exactly which receptionist can use them.</p>
      </div>

      <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-[0_12px_40px_rgba(15,23,42,0.06)] sm:p-6">
        <h2 className="text-lg font-semibold text-slate-900">Upload document</h2>
        <p className="mt-1 text-sm text-slate-500">PDF, DOCX and TXT files are extracted, embedded, and available to the selected scope.</p>

        <div className="mt-6 grid gap-5 md:grid-cols-[1.2fr_0.8fr]">
          <div>
            <label className="mb-2 block text-sm font-semibold text-slate-700">Document</label>
            <div onDragOver={(event) => { event.preventDefault(); setIsDragging(true); }} onDragLeave={() => setIsDragging(false)} onDrop={handleDrop} className={`rounded-2xl border-2 border-dashed p-5 text-center transition ${isDragging ? "border-indigo-500 bg-indigo-50" : "border-slate-200 bg-slate-50/70 hover:border-indigo-300 hover:bg-indigo-50/40"}`}>
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-xl bg-white text-lg shadow-sm">↑</div>
              <p className="mt-3 text-sm font-semibold text-slate-700">Drop a document here</p>
              <p className="mt-1 text-xs text-slate-500">or select a PDF, DOCX, or TXT file</p>
              <button type="button" disabled={uploading} onClick={() => fileInputRef.current?.click()} className="mt-4 rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-semibold text-slate-700 shadow-sm hover:border-indigo-200 hover:text-indigo-700 disabled:opacity-50">Choose file</button>
              <input ref={fileInputRef} type="file" accept=".pdf,.docx,.txt" onChange={handleFileChange} disabled={uploading} className="sr-only" />
            </div>
            {selectedFile && <div className="mt-4 rounded-xl border border-indigo-100 bg-indigo-50/60 p-4"><p className="text-sm font-medium text-slate-900">{selectedFile.name}</p><p className="mt-1 text-xs text-slate-500">{formatFileSize(selectedFile.size)}</p></div>}
          </div>

          <div className="space-y-5">
            <div>
              <label className="mb-2 block text-sm font-semibold text-slate-700">Category</label>
              <select value={category} onChange={(event) => setCategory(event.target.value)} disabled={uploading} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 outline-none focus:border-indigo-500 focus:bg-white">
                <option value="general">General</option><option value="courses">Courses</option><option value="admissions">Admissions</option><option value="pricing">Pricing</option><option value="services">Services</option><option value="policies">Policies</option><option value="company">Company</option>
              </select>
            </div>
            <div>
              <label className="mb-2 block text-sm font-semibold text-slate-700">Knowledge scope</label>
              <select value={agentId ?? ""} onChange={(event) => setAgentId(event.target.value ? Number(event.target.value) : null)} disabled={uploading} className="w-full rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm text-slate-700 outline-none focus:border-indigo-500 focus:bg-white">
                <option value="">Shared with all receptionists</option>
                {agents.map((agent) => <option key={agent.id} value={agent.id}>{agent.name} only</option>)}
              </select>
              <p className="mt-2 text-xs leading-5 text-slate-500">{selectedAgentName ? `Only ${selectedAgentName} can retrieve this private document.` : "Shared documents can be retrieved by every active receptionist in this organization."}</p>
            </div>
          </div>
        </div>

        {successMessage && <div className="mt-5 rounded-2xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">{successMessage}</div>}
        {errorMessage && <div className="mt-5 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">{errorMessage}</div>}
        <div className="mt-6"><button type="button" onClick={handleUpload} disabled={uploading || !selectedFile} className="rounded-xl bg-indigo-600 px-5 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50">{uploading ? "Processing & indexing…" : "Upload & index"}</button></div>
      </div>

      {uploadedDocuments.length > 0 && <div className="overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-sm"><div className="border-b border-slate-200 p-6"><h2 className="font-semibold text-slate-900">Recently uploaded</h2><p className="mt-1 text-sm text-slate-500">Documents uploaded during this session.</p></div><div className="divide-y divide-slate-100">{uploadedDocuments.map((document, index) => <div key={`${document.title}-${index}`} className="flex items-center justify-between gap-4 p-5"><div><p className="text-sm font-medium text-slate-900">{document.title}</p><div className="mt-1 flex flex-wrap gap-3 text-xs text-slate-500"><span>{document.category}</span><span>{document.source}</span><span>{document.chunks_created} chunks</span><span>{document.agent_id ? agents.find((agent) => agent.id === document.agent_id)?.name ?? "Private receptionist" : "Shared"}</span></div></div><span className="rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-700">Indexed</span></div>)}</div></div>}
    </div>
  );
}
