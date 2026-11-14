# Testbench Configuration (testbench.yaml)

Location: project root directory (alongside composer.json)

## Schema

| Key              | Type   | Description                                        |
|------------------|--------|----------------------------------------------------|
| `laravel`        | string | Path to custom Laravel skeleton                    |
| `providers`      | array  | Service Provider classes to load                   |
| `migrations`     | array  | Migration paths to load                            |
| `seeders`        | array  | Seeder classes for `migrate:fresh` / `migrate:refresh` |
| `dont-discover`  | array  | Packages to ignore from auto-discovery             |
| `bootstrappers`  | array  | Bootstrapper classes to load                       |
| `env`            | array  | Environment variables (CLI only, not tests)        |
| `purge`          | object | Files/dirs to prune via `package:purge-skeleton`   |
| `workbench`      | object | Workbench integration configuration                |

### Workbench Sub-schema

| Key          | Type          | Description                                                    |
|--------------|---------------|----------------------------------------------------------------|
| `welcome`    | bool          | Show default Laravel welcome page at `/` on `serve`            |
| `install`    | bool          | Run default Laravel migrations                                 |
| `start`      | string        | Default route path on `serve`                                  |
| `user`       | string\|int   | User ID or email for auto-login (guest access)                 |
| `auth`       | bool          | Generate auth routes via Laravel Breeze (default: false)       |
| `guard`      | string        | Default Auth Guard for auto-login                              |
| `sync`       | array         | Symlink collections (`from` → `to`), `reverse: true` for inverse |
| `build`      | array         | Build recipes for `workbench:build` command                    |
| `assets`     | array         | Tags used in `vendor:publish` with `asset-publish` recipe      |
| `discovers`  | object        | Route/factory/view discovery config                            |

### Workbench Discovers Sub-schema

| Key        | Type | Description                                                  |
|------------|------|--------------------------------------------------------------|
| `config`   | bool | Load config from `workbench/config` directory                |
| `factories`| bool | Map models in `workbench/app/Models` to `workbench/database/factories` |
| `web`      | bool | Register routes from `workbench/routes/web.php`              |
| `api`      | bool | Register routes from `workbench/routes/api.php`              |
| `commands` | bool | Register console commands from `workbench/routes/console.php`|

## Example testbench.yaml

```yaml
providers:
  - Laravel\Sanctum\SanctumServiceProvider
  - Workbench\App\Providers\WorkbenchServiceProvider

dont-discover:
  - laravel/html

env:
  - SEND_QUERIES_TO_RAY=(false)

workbench:
  welcome: true
  install: true
  start: /nova
  user: taylor@laravel.com
  guard: web
  sync:
    - from: public
      to: public/vendor/nova
    - from: storage
      to: workbench/storage
      reverse: true
  build:
    - asset-publish
    - create-sqlite-db
    - migrate:refresh
  assets:
    - nova-assets
  discovers:
    web: true
    api: false
    commands: false
    views: true
```

Note: `env` variables are only applied when using the CLI, NOT when running tests.
