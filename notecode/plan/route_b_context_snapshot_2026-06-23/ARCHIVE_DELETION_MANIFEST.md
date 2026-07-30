# Archive Deletion Manifest

## Policy

This docs slice deletes only existing archive directories dated 2026-05 or earlier.

Kept:

- `notecode/logs/**`
- `notecode/plan/**`
- current runtime code
- June 2026 archives

Deleted directories will be listed below after deletion.

## Deleted

- `archive/20260207`
- `archive/20260308`
- `notecode/archive/non_0506_route_records_20260509`
- `notecode/archive/persona_rebuild_20260422_retired_records_20260423`
- `notecode/archive/pre_2026-04-02_work_records_2026-04-06`
- `notecode/archive/route_0506_archive_move_backups_only_20260512`
- `notecode/archive/route_0506_archive_move_docs_new_folder_5_20260512`
- `notecode/archive/route_experiments_rejected_2026-05-08`
- `notecode/archive/simple_note_refactor_prestart_2026-03-22`
- `notecode/archive/simple_note_reset_2026-03-22`
- `notecode/archive/wrong_direction_20260422_source_per_type_retry`
- `notecode/archive/zero_base_rebuild_2026-03-04`

## Kept Archive Directories

- `archive/algorithm`: undated root archive, not classified in this slice.
- `archive/worklog`: undated root archive, not classified in this slice.
- `notecode/archive/pre_article_brief_source_shape_migration_20260620_110900`: June 2026 archive.
- `notecode/archive/writer_only_deadcode_archive_20260602`: June 2026 archive and still referenced as old writer-only deadcode boundary.

## Notes

- `notecode/archive/non_0506_route_records_20260509` required a second deletion pass with PowerShell/.NET long-path handling because normal `Remove-Item -Recurse` hit deep path errors.
- No `notecode/logs`, `notecode/plan`, or runtime code directories were deleted.
