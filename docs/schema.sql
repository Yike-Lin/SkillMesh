PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sources (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL CHECK (type IN ('local_dir', 'github_repo', 'marketplace', 'plugin_bundle')),
  name TEXT NOT NULL,
  uri TEXT NOT NULL,
  auth_mode TEXT NOT NULL DEFAULT 'none',
  sync_policy TEXT NOT NULL DEFAULT 'manual',
  last_synced_at TEXT
);

CREATE TABLE IF NOT EXISTS skills (
  id TEXT PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  summary TEXT NOT NULL DEFAULT '',
  description TEXT NOT NULL DEFAULT '',
  status TEXT NOT NULL CHECK (status IN ('draft', 'active', 'deprecated')),
  source_id TEXT REFERENCES sources(id),
  canonical_uri TEXT NOT NULL DEFAULT '',
  author TEXT NOT NULL DEFAULT '',
  tags_json TEXT NOT NULL DEFAULT '[]',
  agent_targets_json TEXT NOT NULL DEFAULT '[]',
  visibility TEXT NOT NULL CHECK (visibility IN ('local', 'team', 'public')),
  trust_level TEXT NOT NULL CHECK (trust_level IN ('official', 'verified', 'unverified')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS skill_versions (
  id TEXT PRIMARY KEY,
  skill_id TEXT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
  version TEXT NOT NULL,
  manifest_hash TEXT NOT NULL DEFAULT '',
  skill_md_path TEXT NOT NULL DEFAULT '',
  compatibility_json TEXT NOT NULL DEFAULT '{}',
  published_at TEXT,
  UNIQUE (skill_id, version)
);

CREATE TABLE IF NOT EXISTS dependencies (
  id TEXT PRIMARY KEY,
  from_node_type TEXT NOT NULL CHECK (from_node_type IN ('skill', 'plugin', 'tool', 'mcp', 'workspace', 'flow_template')),
  from_node_id TEXT NOT NULL,
  to_node_type TEXT NOT NULL CHECK (to_node_type IN ('skill', 'plugin', 'tool', 'mcp', 'workspace', 'flow_template')),
  to_node_id TEXT NOT NULL,
  relation_type TEXT NOT NULL CHECK (relation_type IN ('requires', 'optional', 'recommends', 'conflicts_with', 'extends', 'used_in', 'triggered_by')),
  constraint_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trigger_rules (
  id TEXT PRIMARY KEY,
  skill_id TEXT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
  rule_type TEXT NOT NULL CHECK (rule_type IN ('keyword', 'intent', 'repo_signal', 'file_pattern', 'agent_context', 'manual')),
  pattern TEXT NOT NULL,
  weight REAL NOT NULL DEFAULT 1.0,
  example TEXT NOT NULL DEFAULT '',
  negative_pattern TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS capabilities (
  id TEXT PRIMARY KEY,
  skill_id TEXT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
  kind TEXT NOT NULL,
  label TEXT NOT NULL,
  risk_level TEXT NOT NULL CHECK (risk_level IN ('low', 'medium', 'high')),
  metadata_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS install_targets (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL CHECK (type IN ('global', 'workspace', 'project', 'plugin_runtime')),
  path TEXT NOT NULL,
  agent TEXT NOT NULL DEFAULT 'codex',
  platform TEXT NOT NULL DEFAULT 'any',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS installations (
  id TEXT PRIMARY KEY,
  skill_version_id TEXT NOT NULL REFERENCES skill_versions(id) ON DELETE CASCADE,
  install_target_id TEXT NOT NULL REFERENCES install_targets(id) ON DELETE CASCADE,
  enabled INTEGER NOT NULL DEFAULT 0 CHECK (enabled IN (0, 1)),
  pinned INTEGER NOT NULL DEFAULT 0 CHECK (pinned IN (0, 1)),
  config_json TEXT NOT NULL DEFAULT '{}',
  installed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS workspaces (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  root_path TEXT NOT NULL UNIQUE,
  language_stack_json TEXT NOT NULL DEFAULT '[]',
  frameworks_json TEXT NOT NULL DEFAULT '[]',
  repo_remote TEXT NOT NULL DEFAULT '',
  signals_json TEXT NOT NULL DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS recommendations (
  id TEXT PRIMARY KEY,
  workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  prompt_excerpt TEXT NOT NULL DEFAULT '',
  context_json TEXT NOT NULL DEFAULT '{}',
  generated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS recommendation_items (
  id TEXT PRIMARY KEY,
  recommendation_id TEXT NOT NULL REFERENCES recommendations(id) ON DELETE CASCADE,
  skill_id TEXT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
  score REAL NOT NULL,
  reason_json TEXT NOT NULL DEFAULT '{}',
  accepted INTEGER NOT NULL DEFAULT 0 CHECK (accepted IN (0, 1)),
  rejected_reason TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS runs (
  id TEXT PRIMARY KEY,
  skill_id TEXT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
  workspace_id TEXT NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  outcome TEXT NOT NULL CHECK (outcome IN ('success', 'warning', 'failed', 'abandoned')),
  feedback TEXT NOT NULL DEFAULT 'unrated' CHECK (feedback IN ('helpful', 'unrated', 'misfire')),
  cost_json TEXT NOT NULL DEFAULT '{}',
  error_summary TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS flow_templates (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  scenario TEXT NOT NULL DEFAULT '',
  nodes_json TEXT NOT NULL DEFAULT '[]',
  edges_json TEXT NOT NULL DEFAULT '[]',
  version TEXT NOT NULL DEFAULT '0.1.0',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS collections (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  scope TEXT NOT NULL CHECK (scope IN ('personal', 'team', 'project')),
  description TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS collection_items (
  collection_id TEXT NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
  skill_id TEXT NOT NULL REFERENCES skills(id) ON DELETE CASCADE,
  sort_order INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (collection_id, skill_id)
);

CREATE VIRTUAL TABLE IF NOT EXISTS skill_search USING fts5(
  skill_id UNINDEXED,
  name,
  summary,
  tags,
  source
);

CREATE INDEX IF NOT EXISTS idx_skills_source_id ON skills(source_id);
CREATE INDEX IF NOT EXISTS idx_skill_versions_skill_id ON skill_versions(skill_id);
CREATE INDEX IF NOT EXISTS idx_dependencies_from_node ON dependencies(from_node_type, from_node_id);
CREATE INDEX IF NOT EXISTS idx_dependencies_to_node ON dependencies(to_node_type, to_node_id);
CREATE INDEX IF NOT EXISTS idx_trigger_rules_skill_id ON trigger_rules(skill_id);
CREATE INDEX IF NOT EXISTS idx_capabilities_skill_id ON capabilities(skill_id);
CREATE INDEX IF NOT EXISTS idx_installations_skill_version_id ON installations(skill_version_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_workspace_id ON recommendations(workspace_id);
CREATE INDEX IF NOT EXISTS idx_recommendation_items_recommendation_id ON recommendation_items(recommendation_id);
CREATE INDEX IF NOT EXISTS idx_runs_workspace_id ON runs(workspace_id);
CREATE INDEX IF NOT EXISTS idx_runs_skill_id ON runs(skill_id);
