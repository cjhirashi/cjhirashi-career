import { MCP_TIMEOUTS } from "@/config";
import type {
  ConnectionStatus,
  JsonRpcRequest,
  JsonRpcResponse,
  MCPToolSummary,
  ToolCallResult,
} from "@/types";

const PROTOCOL_VERSION = "2024-11-05";
const CLIENT_INFO = { name: "mcp-tools-frontend", version: "1.0.0" };

type StatusListener = (status: ConnectionStatus, error?: string) => void;

interface PendingRequest {
  resolve: (value: JsonRpcResponse) => void;
  reject: (reason: Error) => void;
  timer: ReturnType<typeof setTimeout>;
}

/**
 * Cliente MCP para el transporte "HTTP + SSE" (legacy, protocolVersion
 * 2024-11-05) implementado por el SDK oficial de Python (mcp / fastmcp):
 *
 *   1. GET  {sseUrl}          -> abre un EventSource. El servidor emite un
 *                                 evento nombrado "endpoint" con la URL (
 *                                 relativa) a la que deben enviarse los
 *                                 mensajes JSON-RPC de esta sesion.
 *   2. POST {endpoint}        -> cada mensaje JSON-RPC (request o
 *                                 notification) se envia como un POST con
 *                                 el cuerpo JSON. El servidor responde 202
 *                                 Accepted de forma inmediata.
 *   3. Evento "message"       -> las respuestas JSON-RPC reales llegan de
 *                                 forma asincrona por el mismo EventSource,
 *                                 correlacionadas por "id".
 *
 * El cliente expone una API de alto nivel (callTool, listTools) y gestiona
 * reconexion automatica con backoff exponencial.
 */
export class MCPClient {
  private eventSource: EventSource | null = null;
  private endpointUrl: string | null = null;
  private pending = new Map<number | string, PendingRequest>();
  private nextId = 1;
  private statusListeners = new Set<StatusListener>();
  private status: ConnectionStatus = "idle";
  private reconnectAttempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private manuallyClosed = false;
  private initialized = false;
  private endpointWaiters: Array<() => void> = [];

  constructor(private readonly sseUrl: string) {}

  onStatusChange(listener: StatusListener): () => void {
    this.statusListeners.add(listener);
    listener(this.status);
    return () => this.statusListeners.delete(listener);
  }

  getStatus(): ConnectionStatus {
    return this.status;
  }

  private setStatus(status: ConnectionStatus, error?: string) {
    this.status = status;
    this.statusListeners.forEach((l) => l(status, error));
  }

  connect(): void {
    this.manuallyClosed = false;
    this.openEventSource();
  }

  disconnect(): void {
    this.manuallyClosed = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.teardown();
    this.setStatus("disconnected");
  }

  private teardown() {
    this.eventSource?.close();
    this.eventSource = null;
    this.endpointUrl = null;
    this.initialized = false;
    this.pending.forEach((p) => {
      clearTimeout(p.timer);
      p.reject(new Error("Conexion MCP cerrada"));
    });
    this.pending.clear();
  }

  private openEventSource() {
    this.setStatus(this.reconnectAttempt > 0 ? "reconnecting" : "connecting");

    const es = new EventSource(this.sseUrl);
    this.eventSource = es;

    const connectTimeout = setTimeout(() => {
      if (this.status === "connecting" || this.status === "reconnecting") {
        es.close();
        this.handleDisconnect(
          "Tiempo de espera agotado conectando al servidor MCP",
        );
      }
    }, MCP_TIMEOUTS.connectMs);

    es.addEventListener("endpoint", (evt) => {
      clearTimeout(connectTimeout);
      const data = (evt as MessageEvent<string>).data;
      try {
        this.endpointUrl = new URL(data, this.sseUrl).toString();
      } catch {
        this.endpointUrl = new URL(data, window.location.origin).toString();
      }
      this.endpointWaiters.forEach((fn) => fn());
      this.endpointWaiters = [];
      void this.performHandshake();
    });

    es.addEventListener("message", (evt) => {
      const raw = (evt as MessageEvent<string>).data;
      this.handleMessage(raw);
    });

    es.onerror = () => {
      clearTimeout(connectTimeout);
      // EventSource reintenta solo de forma nativa, pero preferimos control
      // explicito (backoff) y visibilidad de estado en la UI.
      es.close();
      this.handleDisconnect("Conexion con el servidor MCP interrumpida");
    };
  }

  private async performHandshake() {
    try {
      await this.request("initialize", {
        protocolVersion: PROTOCOL_VERSION,
        capabilities: {},
        clientInfo: CLIENT_INFO,
      });
      this.notify("notifications/initialized", {});
      this.initialized = true;
      this.reconnectAttempt = 0;
      this.setStatus("connected");
    } catch (err) {
      this.handleDisconnect(
        err instanceof Error ? err.message : "Fallo el handshake MCP (initialize)",
      );
    }
  }

  private handleDisconnect(error: string) {
    this.teardown();
    if (this.manuallyClosed) {
      this.setStatus("disconnected");
      return;
    }
    this.setStatus("error", error);
    this.scheduleReconnect();
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    const attempt = this.reconnectAttempt++;
    const delay = Math.min(
      MCP_TIMEOUTS.reconnectBaseMs * 2 ** attempt,
      MCP_TIMEOUTS.reconnectMaxMs,
    );
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (!this.manuallyClosed) this.openEventSource();
    }, delay);
  }

  private handleMessage(raw: string) {
    let parsed: JsonRpcResponse | JsonRpcResponse[];
    try {
      parsed = JSON.parse(raw);
    } catch {
      return; // mensaje no-JSON (ping, comentario, etc.) - se ignora
    }
    const messages = Array.isArray(parsed) ? parsed : [parsed];
    for (const msg of messages) {
      if (msg.id === undefined || msg.id === null) continue; // notification, sin id
      const pending = this.pending.get(msg.id);
      if (!pending) continue;
      clearTimeout(pending.timer);
      this.pending.delete(msg.id);
      pending.resolve(msg);
    }
  }

  private async waitForEndpoint(timeoutMs: number): Promise<string> {
    if (this.endpointUrl) return this.endpointUrl;
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        reject(new Error("No se recibio el endpoint de sesion MCP a tiempo"));
      }, timeoutMs);
      this.endpointWaiters.push(() => {
        clearTimeout(timer);
        if (this.endpointUrl) resolve(this.endpointUrl);
        else reject(new Error("Endpoint MCP no disponible"));
      });
    });
  }

  private async request<TResult = unknown>(
    method: string,
    params?: Record<string, unknown>,
    timeoutMs: number = MCP_TIMEOUTS.initializeMs,
  ): Promise<TResult> {
    const endpoint = await this.waitForEndpoint(MCP_TIMEOUTS.connectMs);
    const id = this.nextId++;
    const body: JsonRpcRequest = { jsonrpc: "2.0", id, method, params };

    const responsePromise = new Promise<JsonRpcResponse>((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`Tiempo de espera agotado para "${method}"`));
      }, timeoutMs);
      this.pending.set(id, { resolve, reject, timer });
    });

    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).catch((err) => {
      this.pending.delete(id);
      throw new Error(
        `No se pudo enviar la solicitud MCP (${method}): ${
          err instanceof Error ? err.message : String(err)
        }`,
      );
    });

    if (!res.ok) {
      this.pending.delete(id);
      throw new Error(`El servidor MCP rechazo la solicitud "${method}" (HTTP ${res.status})`);
    }

    const response = await responsePromise;
    if (response.error) {
      throw new Error(response.error.message || `Error MCP en "${method}"`);
    }
    return response.result as TResult;
  }

  private notify(method: string, params?: Record<string, unknown>): void {
    if (!this.endpointUrl) return;
    const body: JsonRpcRequest = { jsonrpc: "2.0", method, params };
    void fetch(this.endpointUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }).catch(() => {
      /* las notificaciones son best-effort */
    });
  }

  async listTools(): Promise<MCPToolSummary[]> {
    if (!this.initialized) throw new Error("Cliente MCP no inicializado");
    const result = await this.request<{ tools: MCPToolSummary[] }>(
      "tools/list",
      {},
      MCP_TIMEOUTS.initializeMs,
    );
    return result?.tools ?? [];
  }

  async callTool(
    name: string,
    args: Record<string, unknown>,
  ): Promise<ToolCallResult> {
    if (!this.initialized) throw new Error("Cliente MCP no inicializado");
    const result = await this.request<{
      content?: Array<{ type: string; text?: string }>;
      isError?: boolean;
    }>(
      "tools/call",
      { name, arguments: args },
      MCP_TIMEOUTS.toolCallMs,
    );

    const text =
      result?.content
        ?.filter((c) => c.type === "text" && typeof c.text === "string")
        .map((c) => c.text as string)
        .join("\n") ?? "";

    return { ok: !result?.isError, text, raw: result };
  }
}
