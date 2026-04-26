-- Create ai_reader user with readonly access.
-- Password OqywPPt0uQsWRz8yMfXili1FAaTJiuxG4KdTOaqBPqQ will be replaced by startup script.
DROP USER IF EXISTS ai_reader;

CREATE USER ai_reader
    IDENTIFIED BY 'OqywPPt0uQsWRz8yMfXili1FAaTJiuxG4KdTOaqBPqQ'
    SETTINGS PROFILE 'ai_reader_profile';

GRANT SELECT ON tushare.* TO ai_reader;
GRANT SELECT ON _meta.* TO ai_reader;

-- Required for describe_table (N6: system.parts for row count estimation)
GRANT SELECT(rows, database, `table`, active) ON system.parts TO ai_reader;
GRANT SELECT ON system.columns TO ai_reader;
GRANT SELECT ON `system`.`tables` TO ai_reader;
