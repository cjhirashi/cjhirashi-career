import { ConnectionStatus } from "@/components/ConnectionStatus";
import { ThemeSwitcher } from "@/components/ThemeSwitcher";
import { APP_NAME } from "@/config";
import type { ConnectionStatus as Status, ThemePreference } from "@/types";

interface NavbarProps {
  connectionStatus: Status;
  connectionError?: string;
  onReconnect: () => void;
  themePreference: ThemePreference;
  onThemeChange: (preference: ThemePreference) => void;
}

export function Navbar({
  connectionStatus,
  connectionError,
  onReconnect,
  themePreference,
  onThemeChange,
}: NavbarProps) {
  return (
    <header className="sticky top-0 z-30 border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-slate-950/80">
      <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <div className="flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-brand-purple-500 via-brand-green-500 to-brand-cyan-500 text-sm font-bold text-white">
            M
          </div>
          <div>
            <p className="text-sm font-semibold leading-tight text-slate-900 dark:text-slate-100">
              {APP_NAME}
            </p>
            <p className="text-xs leading-tight text-slate-400">Generador de documentos PDF</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <ConnectionStatus status={connectionStatus} error={connectionError} onReconnect={onReconnect} />
          <ThemeSwitcher preference={themePreference} onChange={onThemeChange} />
        </div>
      </div>
    </header>
  );
}
