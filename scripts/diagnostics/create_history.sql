-- Insert workflow history record
INSERT INTO workflow_history ("versionId", "workflowId", "authors", "createdAt", "updatedAt", "nodes", "connections", "name", "autosaved", "description")
SELECT 
  'v1-published',
  '7nYXJ6vmJrsC8do9',
  '[]',
  NOW(),
  NOW(),
  nodes::json,
  connections::json,
  name,
  false,
  description
FROM workflow_entity WHERE id = '7nYXJ6vmJrsC8do9';

-- Update versionId to match
UPDATE workflow_entity SET "versionId" = 'v1-published', "activeVersionId" = 'v1-published' WHERE id = '7nYXJ6vmJrsC8do9';

-- Verify
SELECT id, active, "versionId", "activeVersionId" FROM workflow_entity;
SELECT "versionId", "workflowId", "name" FROM workflow_history;
