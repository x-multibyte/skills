---
name: orchestra-testbench-skill
description: >
  Create, configure, and run Laravel package tests using Orchestra Testbench.
  Covers Testbench TestCase setup, testbench.yaml configuration, environment
  definition, database migrations, route testing, CLI commands, Workbench
  integration, and troubleshooting common issues.
license: MIT

metadata:
  author: agentskills-creator
  version: "1.0"
  source: https://packages.tools/testbench

compatibility: |
  Requires PHP 8.0+ and Composer
  Laravel package project with composer.json
  vendor/bin/testbench CLI available after composer install

allowed-tools: |
  Bash(composer:*) Bash(php:*) Bash(vendor/bin/testbench:*)
  Bash(phpunit:*) Read Write Patch
---

# Orchestra Testbench Skill

## When to use

Use this skill when the user asks about:
- Setting up Orchestra Testbench for Laravel package testing
- Configuring testbench.yaml
- Writing feature/integration tests for Laravel packages
- Extending Testbench TestCase instead of PHPUnit TestCase
- Defining environment variables, databases, or routes for tests
- Running Testbench CLI commands (migrate, package:create-sqlite-db, etc.)
- Troubleshooting common Testbench errors (encrypter, Guzzle, legacy factories)
- Setting up Workbench for package development
- Integrating with Spatie Ray or Collision

## Installation

```bash
composer require --dev "orchestra/testbench"
```

### Version Selection

Match Testbench version to your Laravel version. See `references/version-compatibility.md` for the full matrix.

After install, scaffold the recommended setup:

```bash
vendor/bin/testbench workbench:install
```

## Setting Up the TestCase

Extend `Orchestra\Testbench\TestCase` instead of `PHPUnit\Framework\TestCase`:

```php
class TestCase extends \Orchestra\Testbench\TestCase
{
    // ...
}
```

The fixture app booted by Testbench follows the base Laravel application skeleton.

### PHPUnit Configuration

Separate test suites in `phpunit.xml`:

```xml
<testsuites>
    <testsuite name="Feature">
        <directory suffix="Test.php">./tests/Feature</directory>
    </testsuite>
    <testsuite name="Unit">
        <directory suffix="Test.php">./tests/Unit</directory>
    </testsuite>
</testsuites>
```

Run only feature tests:

```bash
vendor/bin/phpunit --testsuite=Feature
```

### Using testbench.yaml with WithWorkbench

Add the `WithWorkbench` trait to auto-load configuration from `testbench.yaml`:

```php
use Orchestra\Testbench\Concerns\WithWorkbench;

class TestCase extends \Orchestra\Testbench\TestCase
{
    use WithWorkbench;
}
```

## Configuration (testbench.yaml)

Full schema documented in `references/config-schema.md`.

### Basic Usage

Create `testbench.yaml` in your project root:

```yaml
providers:
  - Laravel\Passport\PassportServiceProvider

dont-discover:
  - laravel/sanctum
```

### Custom Laravel Skeleton

```yaml
laravel: ./skeleton
```

### Service Providers

```yaml
providers:
  - Laravel\Sanctum\SanctumServiceProvider
  - Workbench\App\Providers\WorkbenchServiceProvider
```

### Exclude Packages from Discovery

```yaml
dont-discover:
  - laravel/html
```

### Environment Variables (CLI Only)

```yaml
env:
  - SEND_QUERIES_TO_RAY=(false)
```

> **Gotcha**: `env` variables only apply to CLI commands, NOT to PHPUnit tests.

## Package Service Providers, Aliases, and Discovery

These methods are overridden in your TestCase class.

### Service Providers

```php
protected function getPackageProviders($app)
{
    return [
        'Acme\AcmeServiceProvider',
    ];
}
```

### Aliases

```php
protected function getPackageAliases($app)
{
    return [
        'Acme' => 'Acme\Facade',
    ];
}
```

### Auto-Discovery

Disable selected packages:

```php
public function ignorePackageDiscoveriesFrom()
{
    return [
        'laravel/passport',
    ];
}
```

Enable all discoveries:

```php
public function ignorePackageDiscoveriesFrom()
{
    return [];  // empty = no ignores = all discovered
}
```

Or set property:

```php
protected $enablesPackageDiscoveries = true;
```

> Gotcha: Root package discovery is NOT automated below Testbench v7.11. Use
> `getPackageProviders()` or run `vendor/bin/testbench package:discover` manually.

## Defining the Environment

### defineEnvironment() Method

Set environment during bootstrapping (between registering and booting service providers):

```php
use Illuminate\Contracts\Config\Repository;

protected function defineEnvironment($app)
{
    tap($app['config'], function (Repository $config) {
        $config->set('database.default', 'testbench');
        $config->set('database.connections.testbench', [
            'driver'   => 'sqlite',
            'database' => ':memory:',
            'prefix'   => '',
        ]);
    });
}
```

### Per-Test Environment via Attribute

```php
use Orchestra\Testbench\Attributes\DefineEnvironment;
use PHPUnit\Framework\Attributes\Test;

#[Test]
#[DefineEnvironment('usesMySqlConnection')]
public function it_can_be_connected_with_mysql()
{
    // ...
}
```

Where `usesMySqlConnection` is a method on your TestCase class:

```php
protected function usesMySqlConnection($app)
{
    $app['config']->set('database.default', 'mysql');
}
```

### Using Attributes for Config/Env

```php
use Orchestra\Testbench\Attributes\WithConfig;
use Orchestra\Testbench\Attributes\WithEnv;

#[WithConfig('database.default', 'testing')]
#[WithEnv('DB_CONNECTION', 'testing')]
class TestCase extends \Orchestra\Testbench\TestCase
{
    // ...
}
```

### Application Key

Add to `phpunit.xml` if tests need encryption:

```xml
<php>
    <env name="APP_KEY" value="AckfSECXIvnK5r28GVIWUAxmbBSjTsmF"/>
</php>
```

### Application Timezone

```php
protected function getApplicationTimezone($app)
{
    return 'Asia/Kuala_Lumpur';
}
```

### Loading .env

By default Testbench loads `.env` if it exists. Disable with:

```php
protected $loadEnvironmentVariables = false;
```

## Defining Databases

### In-Memory SQLite (Recommended)

Set in `phpunit.xml`:

```xml
<env name="DB_CONNECTION" value="testing"/>
```

Or in `defineEnvironment()`:

```php
$app['config']->set('database.default', 'testing');
```

### Auto-Migrate with RefreshDatabase

```php
use Illuminate\Foundation\Testing\RefreshDatabase;

class TestCase extends \Orchestra\Testbench\TestCase
{
    use RefreshDatabase;
}
```

### Manual Migrations

```php
use function Orchestra\Testbench\artisan;

protected function defineDatabaseMigrations()
{
    artisan($this, 'migrate', ['--database' => 'testbench']);

    $this->beforeApplicationDestroyed(
        fn () => artisan($this, 'migrate:rollback', ['--database' => 'testbench'])
    );
}
```

### Run Laravel's Default Migrations (users table, etc.)

```php
use Orchestra\Testbench\Attributes\WithMigration;

#[WithMigration]
class TestCase extends \Orchestra\Testbench\TestCase
{
    // ...
}
```

Select specific migrations:

```php
#[WithMigration('laravel', 'cache', 'queue')]
#[WithMigration('session')]
```

### Testing-Only Migrations

```php
use function Orchestra\Testbench\workbench_path;

protected function defineDatabaseMigrations()
{
    $this->loadMigrationsFrom(workbench_path('database/migrations'));
}
```

### Database Transactions

```php
use Illuminate\Foundation\Testing\DatabaseTransactions;

class TestCase extends \Orchestra\Testbench\TestCase
{
    use DatabaseTransactions;
}
```

> Gotcha: Migration files must follow Laravel convention, e.g., `0000_00_00_000000_create_package_test_tables.php`.

## Defining Routes

### Override Route Providers

```php
use Illuminate\Support\Facades\Route;

protected function defineRoutes($app)
{
    Route::middleware('web')->group(function () {
        Route::get('/test-route', function () {
            return 'hello';
        });
    });
}
```

### Define Cached Routes

```php
protected function defineCachedRoutes($app)
{
    // Routes cached via artisan route:cache
}
```

### Per-Test Route Definition

```php
use Orchestra\Testbench\Attributes\DefineRoute;

#[Test]
#[DefineRoute('customRouteDefinition')]
public function it_can_resolve_web_route()
{
    $this->get('/custom-route')
         ->assertSee('custom response');
}
```

## Overriding Application Kernels

### Console Kernel

```php
use Illuminate\Contracts\Console\Kernel as ConsoleKernel;

protected function resolveApplicationConsoleKernel($app)
{
    $app->singleton(ConsoleKernel::class, 'Tests\Console\Kernel');
}
```

### HTTP Kernel

```php
use Illuminate\Contracts\Http\Kernel as HttpKernel;

protected function resolveApplicationHttpKernel($app)
{
    $app->singleton(HttpKernel::class, 'Tests\Http\Kernel');
}
```

## Custom Laravel Skeleton

Override the base skeleton path:

```php
use function Orchestra\Testbench\package_path;

public static function applicationBasePath()
{
    return package_path('skeleton');
}
```

Fallback method (pre-v6.22.0):

```php
protected function getBasePath()
{
    return __DIR__ . '/../skeleton';
}
```

## Testing Blade Components

```php
use Illuminate\Foundation\Testing\Concerns\InteractsWithViews;

class TestCase extends \Orchestra\Testbench\TestCase
{
    use InteractsWithViews;
}
```

## CLI Commands

Testbench provides artisan-equivalent CLI for interacting with the stub Laravel application.
Any artisan command works — `vendor/bin/testbench <command>` runs it against the skeleton app.

### Workbench Commands

```bash
# Setup Workbench for package development (scaffold structure)
vendor/bin/testbench workbench:install

# Run builds for workbench (asset-publish, migrate:refresh, etc.)
vendor/bin/testbench workbench:build

# Configure Workbench for package development
vendor/bin/testbench workbench:devtool

# Create sqlite database file in workbench skeleton
vendor/bin/testbench workbench:create-sqlite-db

# Drop sqlite database file from workbench skeleton
vendor/bin/testbench workbench:drop-sqlite-db

# Purge skeleton folder to original state
vendor/bin/testbench workbench:purge-skeleton

# Sync skeleton folder to be served externally
vendor/bin/testbench workbench:sync-skeleton
```

### Package Utility Commands

```bash
# Run package tests (requires Collision: nunomaduro/collision)
vendor/bin/testbench package:test

# Parallel testing
vendor/bin/testbench package:test --parallel

# Run package auto-discovery
vendor/bin/testbench package:discover

# Create SQLite database on the Laravel skeleton
vendor/bin/testbench package:create-sqlite-db

# Drop SQLite database from the Laravel skeleton
vendor/bin/testbench package:drop-sqlite-db

# Purge skeleton and reset to defaults (configure purge in testbench.yaml)
vendor/bin/testbench package:purge-skeleton
```

### General Artisan Commands

```bash
# Run migrations on the test skeleton
vendor/bin/testbench migrate

# Interact with package services (e.g., Passport)
vendor/bin/testbench passport:install

# Any other artisan command works
vendor/bin/testbench <artisan-command>
```

Configure purge paths in `testbench.yaml`:

```yaml
purge:
  directories:
    - public/vendor/*
  files:
    - lang/*.json
```

## Integrations

### Spatie Ray (Debugging)

Usage in tests:

```php
use PHPUnit\Framework\Attributes\Test;

#[Test]
public function it_can_resolve_domain_route()
{
    $response = $this->get('http://api.localhost/hello');
    ray($response);
}
```

Configure via `phpunit.xml`:

```xml
<env name="RAY_ENABLED" value="(true)"/>
<env name="SEND_QUERIES_TO_RAY" value="(false)"/>
<env name="SEND_DUMPS_TO_RAY" value="(true)"/>
```

### Collision (Artisan Test Command)

Install:

```bash
composer require --dev "nunomaduro/collision"
```

After `package:discover`, use:

```bash
vendor/bin/testbench package:test
vendor/bin/testbench package:test --parallel   # parallel testing
```

## Troubleshooting

### "No supported encrypter found"

Add APP_KEY to `phpunit.xml`:

```xml
<env name="APP_KEY" value="AckfSECXIvnK5r28GVIWUAxmbBSjTsmF"/>
```

### Why no App classes (Controller, User)?

Testbench removes all App classes to prevent package developers from depending
on them. These classes can be renamed, moved, or removed between Laravel versions.

### "Class GuzzleHttp\\Client not found"

Install guzzle if using Laravel's HTTP Client:

```bash
composer require "guzzlehttp/guzzle"
```

### "Class Illuminate\\Database\\Eloquent\\Factory not found"

Laravel 8 moved factories to `laravel/legacy-factories`. To support Laravel 8
without splitting releases:

```bash
composer require --dev "laravel/legacy-factories:^1.0.4"
```

Ensure Testbench minimum versions — see `references/version-compatibility.md`.

### Legacy factories still erroring after migration to class-based

Check all TestCase classes — remove any calls to `$this->withFactories()`.
Class-based factories are autoloaded by Composer; `withFactories()` is only for
legacy factories.

### "Missing Browser Kit support"

Replace with:

```bash
composer require --dev "orchestra/testbench-browser-kit"
```

## Gotchas

- `env` in `testbench.yaml` only applies to CLI commands, not to PHPUnit tests.
  Use `phpunit.xml` or `defineEnvironment()` for test environment variables.
- Root package auto-discovery is NOT automatic below Testbench v7.11. Use
  `getPackageProviders()` or run `vendor/bin/testbench package:discover`.
- Migration files must follow Laravel convention: `YYYY_MM_DD_HHMMSS_create_<table>_table.php`.
- The CLI command `vendor/bin/testbench <command>` works for database/setup
  operations but NOT for file stubbing — generated files are based on the booted
  Laravel application, not your package directory.
- Testbench does NOT run default Laravel migrations (users, password_resets)
  unless you use `#[WithMigration]` attribute or manually load them.
- `vendor/bin/phpunit --testsuite=Feature` to run only feature tests.
- When using `#[DefineEnvironment]` attribute, the referenced method receives
  `$app` (Illuminate\Foundation\Application) as its parameter.

## Directory Structure

```
your-package/
├── testbench.yaml              # Testbench configuration
├── phpunit.xml                 # PHPUnit configuration
├── src/                        # Package source code
├── tests/
│   ├── TestCase.php            # Base Testbench TestCase
│   ├── Feature/                # Feature tests
│   └── Unit/                   # Unit tests
├── workbench/                  # Workbench (scaffolded)
│   ├── app/
│   ├── database/
│   │   └── migrations/
│   ├── routes/
│   │   ├── web.php
│   │   └── api.php
│   └── config/
└── vendor/
```

## Quick Reference

| Action | Command / Code |
|--------|---------------|
| Install | `composer require --dev "orchestra/testbench"` |
| Scaffold workbench | `vendor/bin/testbench workbench:install` |
| Configure workbench | `vendor/bin/testbench workbench:devtool` |
| Run workbench builds | `vendor/bin/testbench workbench:build` |
| Sync skeleton externally | `vendor/bin/testbench workbench:sync-skeleton` |
| Create SQLite DB (workbench) | `vendor/bin/testbench workbench:create-sqlite-db` |
| Drop SQLite DB (workbench) | `vendor/bin/testbench workbench:drop-sqlite-db` |
| Purge skeleton (workbench) | `vendor/bin/testbench workbench:purge-skeleton` |
| Run package tests (Collision) | `vendor/bin/testbench package:test` |
| Parallel testing | `vendor/bin/testbench package:test --parallel` |
| Package discovery | `vendor/bin/testbench package:discover` |
| Create SQLite DB (package) | `vendor/bin/testbench package:create-sqlite-db` |
| Drop SQLite DB (package) | `vendor/bin/testbench package:drop-sqlite-db` |
| Purge skeleton (package) | `vendor/bin/testbench package:purge-skeleton` |
| Run artisan on skeleton | `vendor/bin/testbench <command>` |
| Run tests | `vendor/bin/phpunit` |
| Run feature tests only | `vendor/bin/phpunit --testsuite=Feature` |

[Skill directory: /Users/roy/.hermes/skills/orchestra-testbench-skill]
Relative paths in this skill are relative to that directory.
