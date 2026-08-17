# Entity-relationship diagram (as built)

Simplified: UUID PKs and timestamp mixins omitted. Optional FKs shown with `o`.

```mermaid
erDiagram
  users ||--o{ organization_members : memberships
  users ||--o{ refresh_tokens : sessions
  users ||--o{ password_reset_tokens : resets
  users ||--o{ email_verification_otps : otps
  organizations ||--o{ organization_members : members
  organizations ||--o{ organization_invites : invites
  organizations ||--o{ projects : projects
  organizations ||--o{ audit_logs : audit
  organizations ||--o| organization_risk : current_risk
  organizations ||--o{ organization_risk_history : history
  organizations ||--o{ ai_conversations : chats
  organizations ||--o{ monitoring_agents : agents

  projects ||--o{ assets : assets
  projects ||--o{ scans : scans
  projects ||--o{ findings : findings
  projects ||--o{ reports : reports
  projects ||--o{ project_risk_metrics : metrics

  assets ||--o{ assets : parent_child
  assets ||--o{ asset_metadata : metadata
  assets ||--o{ asset_tags : tags
  assets ||--o{ asset_links : links
  assets ||--o{ asset_scan_schedules : schedules
  assets ||--o{ scans : scans
  assets ||--o{ findings : findings
  assets ||--o{ asset_risk : risk
  assets ||--o| monitoring_agents : agent

  scans ||--o{ scan_plugin_runs : plugin_runs
  scans ||--o{ findings : findings

  monitoring_agents ||--o{ monitoring_snapshots : snapshots
  monitoring_agents ||--o{ monitoring_metrics : metrics
  monitoring_agents ||--o{ monitoring_alerts : alerts

  ai_conversations ||--o{ ai_messages : messages
  users ||--o{ ai_conversations : user

  asset_saved_filters }o--|| projects : project
  asset_saved_filters }o--|| users : user
```

Standalone catalogs (not tenant-owned): `risk_rules`, `recommendations`, `ai_prompts`.

`audit_logs.user_id` and `organization_id` are nullable (SET NULL on delete) so history can survive user/org removal.
