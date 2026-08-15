import { useState } from "react";
import { DocumentForm } from "@/components/DocumentForm";
import { DocumentHistory } from "@/components/DocumentHistory";
import { DocumentPreview } from "@/components/DocumentPreview";
import { Navbar } from "@/components/Navbar";
import { NotificationCenter } from "@/components/NotificationCenter";
import { useDocumentHistory } from "@/hooks/useDocumentHistory";
import { useMCPClient } from "@/hooks/useMCPClient";
import { useTheme } from "@/hooks/useTheme";
import type { DocumentHistoryEntry } from "@/types";

export default function App() {
  const { status, lastError, tools, callTool, reconnect } = useMCPClient();
  const history = useDocumentHistory();
  const { preference, setPreference } = useTheme();
  const [previewEntry, setPreviewEntry] = useState<DocumentHistoryEntry | null>(null);

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 transition-colors dark:bg-slate-950 dark:text-slate-100">
      <Navbar
        connectionStatus={status}
        connectionError={lastError}
        onReconnect={reconnect}
        themePreference={preference}
        onThemeChange={setPreference}
      />

      <main className="mx-auto max-w-6xl space-y-8 px-4 py-6 sm:px-6 sm:py-8">
        <section>
          <h1 className="text-xl font-semibold text-slate-900 dark:text-slate-100 sm:text-2xl">
            Generador de Documentos
          </h1>
          <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">
            Completa un formulario y genera un PDF a través del servidor MCP. Las herramientas
            disponibles se sincronizan automáticamente al conectar.
          </p>
        </section>

        <DocumentForm
          connectionStatus={status}
          discoveredTools={tools}
          callTool={callTool}
          history={history}
        />

        <DocumentHistory
          entries={history.entries}
          onRemove={history.removeEntry}
          onPreview={setPreviewEntry}
          onRefresh={() => void history.refreshRemote()}
          remoteAvailable={history.remoteAvailable}
          isRefreshing={history.isRefreshing}
        />
      </main>

      <DocumentPreview entry={previewEntry} onClose={() => setPreviewEntry(null)} />
      <NotificationCenter />

      <footer className="mx-auto max-w-6xl px-4 py-8 text-center text-xs text-slate-400 sm:px-6">
        MCP Tools Server · Frontend
      </footer>
    </div>
  );
}
