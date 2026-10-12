# DEVA v1.0 maintenance and release rules

Canonical source repository: https://github.com/Debbybaks/DEVA

Canonical production application: https://deva-vert.vercel.app

## Scientific integrity

Keep maintenance within DEVA v1.0 unless the owner explicitly authorizes a new
scientific scope. Preserve canonical evidence, exact replay payloads and hashes,
historical experiments and results, scientific limitations, release manifests,
tags and existing release history. Do not rewrite deployed commits for attribution.

## Commit attribution

Configure this repository's local Git identity as:

```
git config --local user.name "Deborah Bakare"
git config --local user.email "debbybakare98@gmail.com"
```

Before relying on this identity for attribution, verify through authenticated
GitHub access that this email is verified for the account `Debbybaks`. If that
cannot be verified, stop before committing and report the verification blocker.
Use this identity only for legitimate, completed changes requested by the owner.
Do not create empty commits to manipulate Contributors. Do not use ChatGPT,
OpenAI, Codex or bot author identities, or add them as co-authors.

## GitHub is the source of truth

For every update, maintenance change, fix, feature, release or deployment:

1. Make the change in the existing DEVA source repository.
2. Run all required tests, validation, exact replay and production build checks.
3. Commit the completed, validated change as Deborah Bakare.
4. Push successfully to `Debbybaks/DEVA` on the intended branch.
5. Verify on GitHub that the commit exists and the branch points to that exact SHA.
6. Only then, when deployment is authorized and needed, deploy that exact GitHub
   commit to the existing DEVA Vercel project.
7. Verify that the production deployment corresponds to the same GitHub SHA,
   and smoke-test the actual public application.

Never deploy unpublished local code, publish a hidden divergent source copy,
leave GitHub behind Vercel, bypass source history, or create another repository
without explicit authorization. If deployment fails after a verified push, keep
the GitHub commit intact and repair deployment separately. A documentation-only
commit does not require a production deployment.

## Validation commands

Preserve existing tests and use the repository's documented environment:

```
.venv/bin/python -m unittest discover -s tests -q
npm --prefix apps/command run build
npm --prefix apps/command test
npm --prefix apps/command run test:e2e
.venv/bin/python scripts/replay_history.py
.venv/bin/python scripts/replay_twin.py
.venv/bin/python scripts/replay_phase5.py
.venv/bin/python scripts/replay_phase5_extensions.py
```

These replay commands cover the seven immutable scientific checks. Browser
tests require Chromium and the documented local Python/frontend services.
For production releases, also run the landing/presentation regression tests
and release smoke script against the actual canonical URL, preserving hosted
read-only behavior. Keep immutable scientific release metadata separate from
new UI, documentation and deployment commit/build identifiers.
