import { Component, type ErrorInfo, type ReactNode } from "react";
import { Button } from "@/components/ui/Button";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null };

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error("Error no controlado en la UI:", error, info.componentStack);
  }

  private handleReset = () => {
    this.setState({ error: null });
  };

  render() {
    if (this.state.error) {
      return (
        <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6 dark:bg-slate-950">
          <div className="card max-w-md p-6 text-center">
            <h1 className="text-lg font-semibold text-slate-900 dark:text-slate-100">
              Algo salió mal
            </h1>
            <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">
              Ocurrió un error inesperado en la interfaz. Puedes intentar continuar o recargar la
              página.
            </p>
            <pre className="mt-3 max-h-32 overflow-auto rounded-lg bg-slate-100 p-2 text-left text-xs text-slate-500 dark:bg-slate-800 dark:text-slate-400">
              {this.state.error.message}
            </pre>
            <div className="mt-4 flex justify-center gap-2">
              <Button variant="secondary" onClick={this.handleReset}>
                Continuar
              </Button>
              <Button onClick={() => window.location.reload()}>Recargar página</Button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
