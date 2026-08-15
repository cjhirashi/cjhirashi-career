// Configuracion en tiempo de ejecucion del frontend.
//
// En produccion (contenedor Docker), este archivo es SOBRESCRITO por
// docker-entrypoint.sh al arrancar, con los valores de las variables de
// entorno del servicio (MCP_SSE_PATH, MCP_FILES_BASE_PATH, APP_NAME).
//
// En desarrollo (`npm run dev`) se usa tal cual: los valores vacios hacen que
// la app calcule defaults razonables (ver src/config.ts).
window.__MCP_CONFIG__ = {
  APP_NAME: "",
  SSE_PATH: "",
  FILES_BASE_PATH: "",
};
