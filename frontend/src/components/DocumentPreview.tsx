import { Modal } from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";
import { getDownloadUrl } from "@/services/documentService";
import type { DocumentHistoryEntry } from "@/types";

interface DocumentPreviewProps {
  entry: DocumentHistoryEntry | null;
  onClose: () => void;
}

export function DocumentPreview({ entry, onClose }: DocumentPreviewProps) {
  const url = entry && entry.category !== "generic" ? getDownloadUrl(entry.category, entry.filename) : undefined;

  return (
    <Modal
      open={!!entry}
      title={entry ? `Vista previa · ${entry.filename}` : "Vista previa"}
      onClose={onClose}
      widthClassName="max-w-4xl"
      footer={
        <>
          <Button variant="ghost" onClick={onClose}>
            Cerrar
          </Button>
          {url && (
            <a href={url} download={entry?.filename}>
              <Button variant="success">Descargar PDF</Button>
            </a>
          )}
        </>
      }
    >
      {url ? (
        <iframe
          title={entry?.filename}
          src={url}
          className="h-[70vh] w-full rounded-lg border border-slate-200 dark:border-slate-800"
        />
      ) : (
        <p className="py-10 text-center text-sm text-slate-400">
          La vista previa no está disponible para este documento.
        </p>
      )}
    </Modal>
  );
}
