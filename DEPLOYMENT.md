# Reproducible container deployment

No DEVA hosting project, Git remote or canonical URL was present at the Phase-5 checkpoint. Deploy the supplied Docker image to an authorised persistent Linux container service, with HTTP routed to port 8000 and health check `/api/health`. This preserves the existing process-worker architecture rather than pretending it is a stateless serverless function.

```
docker build -t deva:1.0.0-rc.1 .
docker run --rm -p 8000:8000 deva:1.0.0-rc.1
```

Open `http://localhost:8000/` for Engineering Worlds. Legacy capacity research remains at `/archive` and `/?model=capacity`; hydraulic and twin routes remain available. API and frontend are same-origin; no cross-origin credential requirement.

The public container is read-only: POST/PUT/PATCH/DELETE scientific requests receive 403. Stored experiments and their registered autonomous traces are available. Run new investigations in the trusted local research API using the documented development command; public multi-tenant live compute is outside v1.0. No infrastructure observations are bundled as field measurements. Runtime jobs remain local and are not a shared public data store.

Do not expose the development `deva.api:app` directly as a public service. TLS, resource limits and restart policy are hosting responsibilities. Recommended initial limit: 2 CPU, 1 GiB RAM; verify on the actual deployment rather than treating this as a benchmark guarantee.

After deployment record the stable URL and deployment ID, run production smoke tests on that actual URL, review every release gate and only then create immutable `v1.0.0`. The connected Vercel account contains unrelated projects, which must not be repurposed. A suitable hosting target/runtime credential must be supplied by the owner; no project is created speculatively.

## Authorised Vercel target

Project deva (`prj_AaPigm7026IjUeJ96uWU0TVz8WXe`), team `team_WOGfgAM1EPvDjeZHQNcLvy1J`, verified through connected Vercel tools. Container Runtime beta is documented as available on all plans. Dockerfile.vercel is the required autodetection filename; the adapter preserves the validated RC's scientific source/build, listens on Vercel's default port 80 and uses ephemeral /tmp runtime storage. Public scientific writes remain denied, so no persistent scientific job state is promised by this scale-to-zero deployment.

Source RC: 5e2878297871f75e0596c9bb6e518dc3d5a02e00. Only hosting configuration is overlaid; no historical artifacts or scientific code changed. Compatibility is documentation-checked, not a successful provider build until deployment evidence exists. Connected ChatGPT authentication does not provide workspace CLI credentials. Do not claim gates L–M pass before actual deployment/smoke.

Deployment verified: https://deva-vert.vercel.app, dedicated project deva. Explicit services entrypoint was necessary; the autodetection-only deployment had no routes. Container provider build now passes. Actual public smoke and canonical evidence comparison pass. Final release resolves through v1.0.0; archive metadata contains its exact commit/deployment identifiers.
