# Board data — shared rules for every Job Swipe skill

**Tools.** Board data (the `profile` and `jobs` collections) is read and written with the Artifact tool's
`read_db` / `write_db` actions (`url` = board URL, `db_op` get/list/query/set/update/batch). Older apps expose the
same operations as a separate ArtifactData tool; load whichever exists with ToolSearch if deferred. Stored files
(the CV PDFs) use the Artifact tool's `upload_asset` / `delete_asset` actions; there is no other tool for them.

**Never call Artifact `delete` on the board.** It deletes the whole board for good. Removing one stored file is
`delete_asset`; nothing else.

**Versions.** Every `update` / `set` on a doc you read passes the `version` you read as `if_version`. When a write
is refused because the doc changed (someone swiped, added a note or edited their brief meanwhile):
1. `get` the doc again.
2. Re-check that your change still makes sense on the new content (e.g. it hasn't gained a `cvAssetId`); if not,
   drop it.
3. Re-apply only your fields on top of the fresh doc and write again with the new `version`. For a `set` (which
   replaces the whole doc), start from the fresh doc, change only what you meant to change, and `set` that.

Try at most 3 times. Still refused → leave that doc alone, carry on with the rest, and mention it in the run's
notification if there is one. Never write without `if_version` to get past a conflict.
