import { useEffect, useRef, useState } from "react";
import { DRAFT_STORAGE_PREFIX } from "@/config";
import { readJSON, removeKey, writeJSON } from "@/utils/storage";

const AUTOSAVE_DEBOUNCE_MS = 600;

/**
 * Persiste un valor de formulario en localStorage con debouncing, para
 * recuperar borradores incompletos tras recargar la pagina o cerrar la
 * pestana por accidente.
 */
export function useDraft<T>(draftKey: string, initialValue: T) {
  const storageKey = `${DRAFT_STORAGE_PREFIX}${draftKey}`;
  const [value, setValue] = useState<T>(() => readJSON(storageKey, initialValue));
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [savedAt, setSavedAt] = useState<number | null>(null);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      writeJSON(storageKey, value);
      setSavedAt(Date.now());
    }, AUTOSAVE_DEBOUNCE_MS);
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, [value, storageKey]);

  const clearDraft = () => {
    removeKey(storageKey);
    setValue(initialValue);
    setSavedAt(null);
  };

  return { value, setValue, savedAt, clearDraft };
}
