-- ccass_hold.shareholding: ensure Nullable(String) to match YAML schema_overrides
SELECT name, type FROM system.columns
WHERE database = 'tushare' AND table = 'tushare_ccass_hold' AND name = 'shareholding';

-- If type is Date / Nullable(Date), execute:
ALTER TABLE tushare.tushare_ccass_hold MODIFY COLUMN shareholding Nullable(String);

-- Verify after:
SELECT count(), countIf(shareholding IS NULL) AS null_count
FROM tushare.tushare_ccass_hold;

-- Clear failed sync_state so next backfill is clean:
ALTER TABLE _meta.sync_state DELETE WHERE interface = 'ccass_hold' AND status = 'failed';
