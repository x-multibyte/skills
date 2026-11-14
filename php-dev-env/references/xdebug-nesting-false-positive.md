# Xdebug Nesting Limit False Positive — Reproduction Details

## Full Error

```
Xdebug has detected a possible infinite loop, and aborted your script
with a stack depth of '512' frames

at vendor/laravel/framework/src/Illuminate/Database/Grammar.php:256
    252▕      * @param  mixed  $value
    253▕      * @return bool
    254▕      */
  ➜ 256▕     public function isExpression($value)
    257▕     {
    258▕         return $value instanceof Expression;
    259▕     }

  +2 vendor frames

  3   [internal]:0
      Illuminate\Database\Grammar::{closure:Illuminate\Database\Grammar::wrapSegments():144}("adjustmentables")
      +6 vendor frames

  10  [internal]:0
      Illuminate\Database\Query\Grammars\Grammar::{closure:Illuminate\Database\Query\Grammars\Grammar::compileWheresToArray():254}(["Basic", "adjustmentables.adjustmentable_id", "=", "and"])
```

## Trigger

`php artisan migrate:fresh --seed` running `UserCompanySeeder`.

The seeder creates companies with factory states that chain:
- `withInvoices(30)` → `DocumentLineItemFactory::forInvoice()` → `afterCreating` callback
- Inside callback: `$lineItem->salesTaxes()->syncWithoutDetaching(...)`
- This triggers morphToMany sync → pivot query → SQL compilation
- `compileWheresToArray` → Collection map closure → `whereBasic` → `wrap` → `wrapSegments` → Collection map closure → `wrapTable` → `isExpression`
- Multiple Collection::map closures wrap each other, accumulating frames

## Verification

Before fix:
```
$ php -r 'echo ini_get("xdebug.max_nesting_level");'
512
```

After fix (set to 2048):
```
$ php -r 'echo ini_get("xdebug.max_nesting_level");'
2048
```

Both `php artisan migrate:fresh --seed` and the full test suite (`php artisan test --compact`) pass after the fix.

## Relevant Framework Code

**Illuminate\Database\Grammar::getValue()** (recursive unwrap, single call depth):
```php
public function getValue($expression)
{
    if ($this->isExpression($expression)) {
        return $this->getValue($expression->getValue($this));
    }
    return $expression;
}
```

**Illuminate\Database\Grammar::wrapSegments()** (Collection::map closure):
```php
protected function wrapSegments($segments)
{
    return (new Collection($segments))->map(function ($segment, $key) use ($segments) {
        return $key == 0 && count($segments) > 1
            ? $this->wrapTable($segment)
            : $this->wrapValue($segment);
    })->implode('.');
}
```

## Environment

- macOS with Homebrew PHP 8.4
- Xdebug mode: `develop`
- Default `max_nesting_level`: 512
- Laravel 12, filament v3
