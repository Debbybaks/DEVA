"""Same-origin, read-only public research release. Local scientific API is unchanged."""
import os
from pathlib import Path
from fastapi.responses import JSONResponse, FileResponse, RedirectResponse
from .api import create_app, ROOT

app = create_app(directory=Path(os.getenv("DEVA_RUNTIME_DIR", str(ROOT / ".runtime"))) / "public-archive")
app.version = "1.0.0"

@app.middleware("http")
async def public_boundary(request, call_next):
    if request.url.path == "/api/health":
        return JSONResponse({"status": "ready", "science": "Python", "version": app.version, "public_read_only": True, "formal_verification": False}, headers={"X-Content-Type-Options": "nosniff"})
    if request.url.path == "/" and not request.url.query:
        return RedirectResponse("/?model=worlds", status_code=307)
    if request.method not in {"GET", "HEAD", "OPTIONS"}:
        return JSONResponse({"detail": "Public research archive is read-only. Run new investigations in the trusted local research environment."}, status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; worker-src 'self' blob:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'"
    return response

@app.get("/{asset:path}", include_in_schema=False)
def frontend(asset: str):
    if asset.startswith("api/"):
        return JSONResponse({"detail": "Unknown API route"}, status_code=404)
    dist = (ROOT / "apps/command/dist").resolve()
    target = (dist / (asset or "index.html")).resolve()
    if not target.is_relative_to(dist):
        return JSONResponse({"detail": "Invalid asset path"}, status_code=404)
    if not target.is_file():
        return JSONResponse({"detail": "Build missing or unknown asset"}, status_code=404)
    return FileResponse(target)
