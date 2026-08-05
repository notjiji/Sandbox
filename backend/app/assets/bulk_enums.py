"""Bulk asset action types."""

import enum


class AssetBulkAction(str, enum.Enum):
    ARCHIVE = "archive"
    DELETE = "delete"
    ASSIGN_TAGS = "assign_tags"
    CHANGE_OWNER = "change_owner"
    LAUNCH_SCAN = "launch_scan"
    EXPORT = "export"
