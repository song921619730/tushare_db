-- Clear stale sync_state records (updated 2026-04-29)
-- Part 1: Disabled interfaces (never need to run again)
-- Part 2: Fixed interfaces (strategy changed, old units are incompatible)
-- Part 3: Re-enabled interfaces (clear old state before fresh backfill)
-- Run AFTER create_missing_tables.sql to avoid orphaned state

-- =============================================================================
-- Part 1: Disabled interfaces
-- These interfaces were disabled in config and will not be backfilled.
-- =============================================================================

-- dc_member: disabled (exchange membership data, API times out)
ALTER TABLE _meta.sync_state DELETE WHERE interface = 'dc_member';

-- fut_trade_cal: disabled (futures trading calendar, duplicate of stock calendar)
ALTER TABLE _meta.sync_state DELETE WHERE interface = 'fut_trade_cal';

-- stk_auction: disabled (empty sample response from API)
ALTER TABLE _meta.sync_state DELETE WHERE interface = 'stk_auction';

-- stk_premarket: disabled (pre-market data not needed)
ALTER TABLE _meta.sync_state DELETE WHERE interface = 'stk_premarket';

-- =============================================================================
-- Part 2: Fixed interfaces (strategy changed)
-- Old sync_state records are incompatible with new strategy.
-- =============================================================================

-- fina_audit: was period_loop (25 units), now per_symbol_period (~137K units)
ALTER TABLE _meta.sync_state DELETE WHERE interface = 'fina_audit';

-- fund_manager: was date_loop (1531 units), now full_once (1 unit)
ALTER TABLE _meta.sync_state DELETE WHERE interface = 'fund_manager';

-- cb_share: was date_loop (1531 units), now per_symbol (~200 units)
ALTER TABLE _meta.sync_state DELETE WHERE interface = 'cb_share';

-- =============================================================================
-- Part 3: Re-enabled interfaces (clear old stale state before fresh backfill)
-- These were re-enabled after confirming API availability.
-- =============================================================================

-- stk_week_month_adj: was disabled, re-enabled with freq=W
ALTER TABLE _meta.sync_state DELETE WHERE interface = 'stk_week_month_adj';

-- cn_pmi: was disabled, re-enabled as full_once macro
ALTER TABLE _meta.sync_state DELETE WHERE interface = 'cn_pmi';

-- fut_weekly_monthly: was disabled, re-enabled with symbol_source=fut_basic
ALTER TABLE _meta.sync_state DELETE WHERE interface = 'fut_weekly_monthly';
