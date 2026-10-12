# Reproducible container deployment

No hosting project or canonical URL was present at the Phase-5 checkpoint. Deploy the supplied Docker image to an authorised persistent Linux container service, with HTTP routed to port 8000 and health check `/api/health`. This preserves the existing process-worker architecture rather than pretending it is a stateless serverless function.

```
docker build -t deva:1.0.0-rc.1 .
docker run --rm -p 8000:8000 deva:1.0.0-rc.1
```

Open `http://localhost:8000/` for Engineering Worlds. Legacy capacity research remains at `/?model=capacity`; hydraulic and twin routes remain available. API and frontend are same-origin; no cross-origin credential requirement.

The public container is read-only: POST/PUT/PATCH/DELETE scientific requests receive 403. Stored experiments and their registered autonomous traces are available. Run new investigations in the trusted local research API using the documented development command; public multi-tenant live compute is outside v1.0. No infrastructure observations are bundled as field measurements. Runtime jobs remain local and are not a shared public data store.

Do not expose the development `deva.api:app` directly as a public service. TLS, resource limits and restart policy are hosting responsibilities. Recommended initial limit: 2 CPU, 1 GiB RAM; verify on the actual deployment rather than treating this as a benchmark guarantee.

After deployment record the stable URL and deployment ID, run production smoke tests on that actual URL, review every release gate and only then create immutable `v1.0.0`. Authentication/hosting ownership must be supplied by the owner; no project is created speculatively.
