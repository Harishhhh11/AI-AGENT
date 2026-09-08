interface EmptyStateProps {
  title: string;
  description: string;
  action?: { label: string; onClick: () => void };
}

export default function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="flex min-h-52 items-center justify-center p-8 text-center">
      <div className="max-w-md">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-sm font-black text-indigo-600">AI</div>
        <h3 className="mt-4 text-sm font-semibold text-slate-900">{title}</h3>
        <p className="mt-2 text-sm leading-6 text-slate-500">{description}</p>
        {action && <button type="button" onClick={action.onClick} className="mt-4 rounded-xl bg-indigo-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-indigo-700">{action.label}</button>}
      </div>
    </div>
  );
}
