# SpriteCut production viewer launcher
"""Serve the production folder beside this script using only the Python standard library."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
from urllib.parse import unquote, urlsplit
import webbrowser


HTML = "spritecut-viewer.html"
MEDIA = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".gif": "image/gif",
         ".webp": "image/webp", ".bmp": "image/bmp", ".avif": "image/avif"}


def project_index(root):
    paths = []
    documents = {}
    for directory, folders, files in os.walk(root):
        here = Path(directory)
        folders[:] = [name for name in folders if not name.startswith(".") and
                      (here/name).resolve() == here/name]
        for name in files:
            file = here/name
            if name.startswith(".") or file.is_symlink():
                continue
            path = file.relative_to(root).as_posix()
            if file.suffix.lower() in MEDIA or (path.startswith("motions/") and file.suffix == ".json"):
                paths.append(path)
            if path == "selection.json" or (path.startswith("motions/") and name == "clips.json"):
                try:
                    documents[path] = json.loads(file.read_text(encoding="utf-8-sig"))
                except (ValueError, OSError):
                    documents[path] = None
    return {"name": root.name, "paths": paths, "documents": documents}


def create_server(folder):
    root = Path(folder).resolve(strict=True)

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def headers_for(self, mime, size):
            self.send_response(200)
            self.send_header("Content-Type", mime)
            self.send_header("Content-Length", str(size))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()

        def do_GET(self):
            if self.headers.get("Host") != f"127.0.0.1:{self.server.server_port}":
                return self.send_error(403)
            route = urlsplit(self.path).path
            if route == "/project.json":
                data = json.dumps(project_index(root), ensure_ascii=True).encode()
                self.headers_for("application/json", len(data))
                self.wfile.write(data)
                return
            if route in ("/", "/"+HTML):
                file, mime = root/HTML, "text/html; charset=utf-8"
            elif route.startswith("/assets/"):
                parts = unquote(route[len("/assets/"):]).split("/")
                if any(not p or p.startswith(".") or "\\" in p or ":" in p for p in parts):
                    return self.send_error(404)
                file = root.joinpath(*parts)
                mime = MEDIA.get(file.suffix.lower())
            else:
                return self.send_error(404)
            try:
                if not mime or file.resolve() != file or not file.is_file():
                    return self.send_error(404)
                # Release the file before replying so an editor can replace it on Windows.
                data = file.read_bytes()
                self.headers_for(mime, len(data))
                self.wfile.write(data)
            except (FileNotFoundError, PermissionError):
                self.send_error(404)
            except (ConnectionResetError, BrokenPipeError):
                pass

    return ThreadingHTTPServer(("127.0.0.1", 0), Handler)


def serve(folder):
    with create_server(folder) as server:
        address = f"http://127.0.0.1:{server.server_port}/{HTML}?project"
        print(f"SpriteCut: {address}\nPress Ctrl+C or close this window to stop.", flush=True)
        webbrowser.open(address)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    serve(Path(__file__).resolve().parent)
