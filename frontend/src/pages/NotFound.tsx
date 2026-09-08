import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <main className="grid min-h-screen place-items-center bg-slate-950 px-6 text-center text-white">
      <div className="max-w-md">
        <p className="text-sm font-bold uppercase tracking-[0.2em] text-indigo-300">Page not found</p>
        <h1 className="mt-4 text-4xl font-bold">This workspace page does not exist.</h1>
        <p className="mt-4 text-sm leading-6 text-slate-300">
          The link may be outdated or the page may have moved. Return to the workspace to continue.
        </p>
        <Link
          to="/"
          className="mt-8 inline-flex rounded-xl bg-indigo-500 px-5 py-3 text-sm font-bold text-white transition hover:bg-indigo-400"
        >
          Return to workspace
        </Link>
      </div>
    </main>
  );
}
