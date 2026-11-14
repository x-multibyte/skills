# Worked example: tsonline-server AGENTS.md

Full walk-through of authoring AGENTS.md for `/Users/roy/tsonline-server` (legacy C# WinForms game server, .NET Framework 4.5, VS2013-era).

## Repo shape discovered

- Non-SDK-style csproj: `TS Server v.2/TS Server v.2.csproj`, `ToolsVersion="12.0"`, `TargetFrameworkVersion v4.5`, output `TS Server v.2/bin/Debug/TS Server v.2.exe`.
- Solution `TS Server v.2.sln` (Format Version 12.00, VS 2013). Only Debug|Any CPU and Release|Any CPU configs, both forced `<PlatformTarget>x86</PlatformTarget>` (recent fix f2fcfbc — x86 required for 32-bit Access OLEDB 12.0).
- No tests, no CI, no lint config anywhere in the repo.
- Docker/Wine run path: `docker compose up --build` — Dockerfile base `scottyhardy/docker-wine:stable-10.0`, platform `linux/amd64`, installs Xvfb + winetricks dotnet45, `COPY ["TS Server v.2/bin/Debug/", "/app/"]`, exposes 6414, `docker-compose.yml` mounts `./server-data:/app/Data`.
- Data layer: `.accdb` files via OleDb. `Data/Taofile.cs` bootstraps Data/ dirs from embedded templates (`DL/Account.accdb`, `DL/NewChar.accdb`, both `CopyToOutputDirectory=Always`).

## Host toolchain check (the key move)

`which msbuild xbuild mono wine dotnet` → only `/opt/homebrew/bin/dotnet`. Conclusion: no working local build on this Mac; `dotnet build` cannot build a non-SDK .NET Framework csproj. Documented Windows command: `msbuild "TS Server v.2.sln" /p:Configuration=Debug`.

## Cross-checking docs vs code

`vm-setup-guide.html` claimed the server binds `127.0.0.1:6414`, but `Data/Senddt.cs:20` reads `new TcpListener(IPAddress.Parse("0.0.0.0"), 6414)` — the guide was stale; AGENTS.md records the real bind.

## Git-interplay pitfall (the top find)

`bin/` and `obj/` are gitignored, but the Dockerfile `COPY`s from `TS Server v.2/bin/Debug/`. Fresh clone + `docker compose up --build` fails at COPY. AGENTS.md Pitfalls section warns: produce the exe elsewhere first.

## Conventions observed by grep

- Vietnamese identifiers/comments throughout; `po*` prefix for send-to-client methods in `Data/DocCSDL.cs` (`po3` char info, `po5` stats, `po23` inventory, `po15` pets, `po26` gold).
- `Form1.cs:41` `CheckForIllegalCrossThreadCalls = false` — intentional, UI touched from threads.
- SQL string concatenation, not parameterized.
- Packet format: header `0xE959`, 2-byte length, opcode XOR `0xAD` (`Game/WorldPacket.cs`, `Game/Encoding.cs`).
- Commit messages: lowercase conventional prefixes (`feat:`, `fix:`) per `git log --oneline`.

## Final shape

34 lines: overview / Dev environment / Build & test / Conventions / Pitfalls. CLAUDE.md existed and carried the architecture narrative — AGENTS.md was kept to the operational layer and pointed at it.
