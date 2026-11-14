# Node + pnpm Docker Build Pitfalls

This reference covers the specific failure modes that arise when containerizing Node apps that use **pnpm v10+** in Docker. Each entry follows the pattern: **Symptom → Root cause → Fix**.

## Pin pnpm to v10 in the Dockerfile when the project was authored against v10

**Symptom**: Build fails with `ERR_PNPM_IGNORED_BUILDS: Ignored build scripts: esbuild, puppeteer` even after adding an `onlyBuiltDependencies` block to `pnpm-workspace.yaml`.

**Root cause**: `npm install -g pnpm` (no version) installs the **current latest**, which may be v11+ by now. pnpm v11 renamed `onlyBuiltDependencies` / `ignoredBuiltDependencies` / `neverBuiltDependencies` to a single `allowBuilds` map. Your v10-style config is silently ignored.

**Fix**: pin the global install to a version that matches the project's config schema. If the project has `pnpm@10.x` in its lockfile/manifest, install `pnpm@10.32.1`:

```dockerfile
RUN npm install -g pnpm@10.32.1
```

If you actually want v11+ semantics, rewrite the config to the new key:

```yaml
# pnpm-workspace.yaml (v11+)
allowBuilds:
  esbuild: true
  puppeteer: true
```

Pinning is the safer default — your CI and local builds will use the same major version.

## Corepack "packageManager" field blocks pnpm if Yarn 1 is the global fallback

**Symptom**: Container with `packageManager: "pnpm@10.x"` in `package.json` exits with:

```
error This project's package.json defines "packageManager": "yarn@pnpm@10.32.1".
However the current global version of Yarn is 1.22.22.
```

**Root cause**: Corepack reads the field, sees a non-yarn value, tries to fetch pnpm, but the resolver mangles it as `yarn@pnpm@10.32.1` (treating the whole string as a yarn version spec). It then complains that global Yarn is not the required version.

**Fix**: when you control the container image, don't rely on the `packageManager` field. Either remove it (and pin pnpm via `npm install -g pnpm@<ver>` in the Dockerfile as above), or explicitly enable Corepack + run `corepack prepare pnpm@10.32.1 --activate` before installing.

## pnpm v10+ blocks build scripts by default (ERR_PNPM_IGNORED_BUILDS)

**Symptom**: `pnpm install` exits with non-zero status and prints:

```
[ERR_PNPM_IGNORED_BUILDS] Ignored build scripts: esbuild@0.21.5, puppeteer@22.15.0
Run "pnpm approve-builds" to pick which dependencies should be allowed to run scripts.
```

**Root cause**: pnpm v10 added a supply-chain safeguard — by default, dependencies with `install`/`postinstall` scripts are NOT run unless explicitly allowed. The `pnpm approve-builds` command is interactive, so it cannot be used in non-interactive CI/Docker builds.

**Fix**: declare an allowlist in `pnpm-workspace.yaml` (NOT `package.json` for v10, NOT `.npmrc` — only `pnpm-workspace.yaml` is honored for this setting):

```yaml
onlyBuiltDependencies:
  - esbuild
  - puppeteer
  - "@tailwindcss/oxide"
  - core-js
```

Then `COPY pnpm-workspace.yaml /app/` BEFORE `RUN pnpm install` in the Dockerfile so the config is in place when install runs.

## pnpm-lock.yaml exists but Dockerfile copies yarn.lock (or vice versa)

**Symptom**: Build error `"/yarn.lock": not found` from the `COPY` line.

**Root cause**: Project uses pnpm but the Dockerfile was authored when the project used yarn (or the other way around). The build context only has the package manager's lockfile.

**Fix**: pick the actual package manager — check for `pnpm-lock.yaml`, `yarn.lock`, or `package-lock.json` in the project root. Then align **all four** Dockerfile references:

- `COPY package.json <lockfile> ...`
- `RUN npm install -g pnpm` / `yarn` (and use the matching install command)
- `RUN pnpm install` / `yarn install`
- `CMD ["pnpm", "dev", ...]` / `CMD ["yarn", "dev", ...]`

When in doubt, `ls /path/to/project/*.lock*` to see which lockfile(s) actually exist.

## Use `docker compose exec -T` for non-interactive test runs

**Symptom**: `docker compose exec frontend pnpm test` hangs or prints weird warnings.

**Fix**: pass `-T` to disable pseudo-TTY allocation for CI-style one-off commands:

```bash
docker compose exec -T frontend pnpm test
```

For interactive shells (debugging), drop `-T` and add `-u root` if you need to write outside the container user's home.

## Cached COPY layers hide new config files

**Symptom**: You add a new `pnpm-workspace.yaml`, rerun `docker-compose build --no-cache`, but pnpm still ignores it.

**Root cause**: A previous `COPY package.json pnpm-lock.yaml /app/` line cached. The `--no-cache` flag purges **layer cache**, but the build context tarball and the COPY step may still use stale content if the Dockerfile itself wasn't structurally different — or if BuildKit's content-addressable cache keyed on a file path that no longer exists.

**Fix**: use `docker builder prune -af` to fully purge BuildKit cache, then rebuild:

```bash
docker builder prune -af
docker compose build --no-cache frontend
```

If the file genuinely doesn't exist in the build context, verify with `ls frontend/pnpm-workspace.yaml` BEFORE rebuilding — Docker will silently skip the COPY with `not found` only if the file is genuinely missing.

## Verify the working stack with curl + docker compose ps

**Symptom**: Build succeeded but you don't know if the app actually works.

**Fix**: after `docker compose up -d`, always run:

```bash
docker compose ps -a                    # confirm both services "Up"
curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:PORT1/   # backend
curl -sS -o /dev/null -w "%{http_code}\n" http://localhost:PORT2/   # frontend
docker compose logs --tail=20 backend   # check for startup errors
```

A 200 on the frontend root and a 200 on the backend root (or a FastAPI default 404 on `/` if the backend has no root route) is a clean signal. Then run any project test suite inside the running container:

```bash
docker compose exec -T frontend pnpm test
```

Passing tests + two running containers + clean logs = done.