/**
 * @typedef {Object} AssetSummary
 * @property {string} id
 * @property {string} project_id
 * @property {string} name
 * @property {string|null} identifier
 * @property {'host'|'domain'|'ip'|'application'} type
 * @property {'active'|'inactive'|'archived'} status
 * @property {string|null} created_by
 */

/** @type {import('./types.js').AssetType[]} */
export const ASSET_TYPES = ["host", "domain", "ip", "application"];

/** @type {import('./types.js').AssetStatus[]} */
export const ASSET_STATUSES = ["active", "inactive", "archived"];
