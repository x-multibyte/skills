# Orchestra Testbench Version Compatibility

| Laravel | Testbench |
|---------|-----------|
| 5.x     | 3.x       |
| 6.x     | 4.x       |
| 7.x     | 5.x       |
| 8.x     | 6.x       |
| 9.x     | 7.x       |
| 10.x    | 8.x       |
| 11.x    | 9.x       |
| 12.x    | 10.x      |

## Legacy Factory Support Minimum Versions

When using `laravel/legacy-factories` for Laravel 8 backward compatibility:

| Laravel | Minimum Testbench |
|---------|-------------------|
| 5.5     | 3.5.6             |
| 5.6     | 3.6.7             |
| 5.7     | 3.7.8             |
| 5.8     | 3.8.6             |
| 6.x     | 4.8.0             |
| 7.x     | 5.2.0             |
| 8.x     | ^6.0              |

Example composer.json constraint for minimum Laravel 5.6 support:

```json
{
  "require-dev": {
    "orchestra/testbench": "~3.6.7 || ~3.7.8 || ~3.8.6 || ^4.8 || ^5.2 || ^6.0"
  }
}
```
