import { createServer } from "node:http";
import { readFile } from "node:fs/promises";
import { extname, resolve, sep } from "node:path";
import { fileURLToPath } from "node:url";

const frontendDirectory = resolve(fileURLToPath(new URL(".", import.meta.url)));
const port = Number(process.env.SUMNOTE_FRONTEND_PORT || 5173);
const host = process.env.SUMNOTE_FRONTEND_HOST || "127.0.0.1";
const contentTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".mjs": "text/javascript; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".ico": "image/x-icon",
};

const server = createServer(async (request, response) => {
  if (request.method !== "GET" && request.method !== "HEAD") {
    response.writeHead(405, { Allow: "GET, HEAD", "Cache-Control": "no-store" });
    response.end("Method not allowed");
    return;
  }

  try {
    const requestUrl = new URL(request.url || "/", `http://${request.headers.host || `${host}:${port}`}`);
    const requestPath = decodeURIComponent(requestUrl.pathname === "/" ? "/index.html" : requestUrl.pathname);
    const filePath = resolve(frontendDirectory, `.${requestPath}`);
    if (filePath !== frontendDirectory && !filePath.startsWith(frontendDirectory + sep)) {
      response.writeHead(403, { "Cache-Control": "no-store" });
      response.end("Forbidden");
      return;
    }

    const file = await readFile(filePath);
    response.writeHead(200, {
      "Content-Type": contentTypes[extname(filePath).toLowerCase()] || "application/octet-stream",
      "Content-Length": file.length,
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    });
    response.end(request.method === "HEAD" ? undefined : file);
  } catch (error) {
    const status = error.code === "ENOENT" ? 404 : 500;
    response.writeHead(status, { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" });
    response.end(status === 404 ? "Not found" : "Frontend server error");
  }
});

server.listen(port, host, () => {
  console.log(`sumnote frontend: http://${host}:${port}`);
  console.log("Backend API: http://127.0.0.1:8000");
});
