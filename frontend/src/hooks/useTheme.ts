import { useCallback, useEffect, useState } from "react";
import { THEME_STORAGE_KEY } from "@/config";
import type { ThemePreference } from "@/types";

function systemPrefersDark(): boolean {
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

function applyThemeClass(preference: ThemePreference) {
  const isDark = preference === "dark" || (preference === "system" && systemPrefersDark());
  document.documentElement.classList.toggle("dark", isDark);
}

function readStoredPreference(): ThemePreference {
  const stored = localStorage.getItem(THEME_STORAGE_KEY);
  if (stored === "light" || stored === "dark" || stored === "system") return stored;
  return "system";
}

/**
 * Gestiona la preferencia de tema (light/dark/system), persistiendo en
 * localStorage y sincronizando con cambios del sistema operativo cuando la
 * preferencia es "system". El script inline en index.html evita el
 * "flash" de tema incorrecto antes de que React monte.
 */
export function useTheme() {
  const [preference, setPreferenceState] = useState<ThemePreference>(readStoredPreference);

  useEffect(() => {
    applyThemeClass(preference);
    localStorage.setItem(THEME_STORAGE_KEY, preference);
  }, [preference]);

  useEffect(() => {
    if (preference !== "system") return;
    const mql = window.matchMedia("(prefers-color-scheme: dark)");
    const handler = () => applyThemeClass("system");
    mql.addEventListener("change", handler);
    return () => mql.removeEventListener("change", handler);
  }, [preference]);

  const setPreference = useCallback((next: ThemePreference) => {
    setPreferenceState(next);
  }, []);

  const resolvedTheme: "light" | "dark" =
    preference === "dark" || (preference === "system" && systemPrefersDark())
      ? "dark"
      : "light";

  return { preference, setPreference, resolvedTheme };
}
