# n8n CLI Bug: publish:workflow / update:workflow --active

## Summary

`n8n publish:workflow` and `n8n update:workflow --active=true` fail on workflows imported via CLI.

## Error

```
$ docker exec p38-n8n n8n publish:workflow --id=7nYXJ6vmJrsC8do9

Publishing workflow with ID: 7nYXJ6vmJrsC8do9 (current version)
Error updating database. See log messages for details.

GOT ERROR
====================================
Version "v1-init" not found for workflow "7nYXJ6vmJrsC8do9".
```

## Root Cause

1. `n8n import:workflow` creates record in `workflow_entity` with `versionId`
2. BUT does NOT create corresponding record in `workflow_history`
3. `publish:workflow` tries to publish version from `workflow_history`
4. FK constraint fails because history record doesn't exist

## Affected Versions

- Confirmed in: n8n 2.0.2 (December 2025)
- Likely affects: All n8n 2.x with workflow versioning

## Official Issue

**Not found** in GitHub issues as of 2025-12-16.

Searched:
- https://github.com/n8n-io/n8n/issues?q=publish+workflow+cli
- https://github.com/n8n-io/n8n/issues?q=import+workflow+active

May be **intended behavior** — versioning appears to be Enterprise/UI feature.

## Workaround

See `deployment/n8n/scripts/n8n-activate.sh` — manually creates `workflow_history` record before activation.

## Recommendation

If deploying n8n headless in production:
1. Use provided script
2. OR contribute fix upstream to n8n
3. OR use n8n API (requires authentication setup)
