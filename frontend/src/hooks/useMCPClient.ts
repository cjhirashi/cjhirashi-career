import { useEffect, useMemo, useRef, useState, useCallback } from "react";
import { getSseUrl } from "@/config";
import { MCPClient } from "@/services/mcpClient";
import type { ConnectionStatus, MCPToolSummary, ToolCallResult } from "@/types";

export interface UseMCPClientResult {
  status: ConnectionStatus;
  lastError?: string;
  tools: MCPToolSummary[];
  callTool: (name: string, args: Record<string, unknown>) => Promise<ToolCallResult>;
  reconnect: () => void;
}

/**
 * Hook de alto nivel para consumir el servidor MCP desde componentes React.
 * Crea una unica instancia de MCPClient por ciclo de vida del componente
 * raiz, gestiona el estado de conexion y expone `callTool` con manejo de
 * errores homogeneo.
 */
export function useMCPClient(): UseMCPClientResult {
  const clientRef = useRef<MCPClient | null>(null);
  const [status, setStatus] = useState<ConnectionStatus>("idle");
  const [lastError, setLastError] = useState<string | undefined>();
  const [tools, setTools] = useState<MCPToolSummary[]>([]);

  if (!clientRef.current) {
    clientRef.current = new MCPClient(getSseUrl());
  }

  useEffect(() => {
    const client = clientRef.current;
    if (!client) return;

    const unsubscribe = client.onStatusChange((next, error) => {
      setStatus(next);
      setLastError(error);
    });

    client.connect();

    return () => {
      unsubscribe();
      client.disconnect();
    };
  }, []);

  useEffect(() => {
    if (status !== "connected" || !clientRef.current) return;
    let cancelled = false;
    clientRef.current
      .listTools()
      .then((list) => {
        if (!cancelled) setTools(list);
      })
      .catch(() => {
        // tools/list es una mejora opcional; si falla, la app sigue
        // funcionando con el registro estatico de herramientas conocidas.
      });
    return () => {
      cancelled = true;
    };
  }, [status]);

  const callTool = useCallback(
    async (name: string, args: Record<string, unknown>): Promise<ToolCallResult> => {
      if (!clientRef.current) throw new Error("Cliente MCP no disponible");
      return clientRef.current.callTool(name, args);
    },
    [],
  );

  const reconnect = useCallback(() => {
    clientRef.current?.disconnect();
    clientRef.current?.connect();
  }, []);

  return useMemo(
    () => ({ status, lastError, tools, callTool, reconnect }),
    [status, lastError, tools, callTool, reconnect],
  );
}
