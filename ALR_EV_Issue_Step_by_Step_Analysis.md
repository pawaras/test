# ALR RS1EV FPLNW Issue - Step-by-Step Root Cause Analysis

## Executive Summary

After analyzing the error table and FPLNW customer data, I've identified **TWO DISTINCT ISSUES**:

| Issue | Description | Affected Premises |
|-------|-------------|-------------------|
| **Issue A** | EV meters that stopped (changed) mid-billing cycle cause INCOMPINTVS errors | 70002132, 70002972, 70005262, etc. |
| **Issue B** | Channel 1000 (EV interval) data never being fetched for some premises | 70674364, 70670026, 70669597, 70664193, 70663090, 70593045 |

**The ChatGPT solution (validation change) only addresses Issue A, NOT Issue B.**

---

## STEP 1: Understanding the Two Categories of Problems

### Category A: "Data was received until meter change" (Validation Problem)

These premises have this pattern in the error table:
- **METERCHANGE**: "Meter X (type evmeter) stopped on DATE"
- **INCOMPINTVS**: "The last meter fetched stops at DATE, but the bill runs until LATER_DATE"

**Example Premises**: 70002132, 70002972, 70005262

### Category B: "No Data has been received for Ch 1000" (Data Fetch Problem)

These premises have **NO INCOMPINTVS or METERCHANGE errors** - only AUMONTH errors or nothing at all.
The interval data for channel 1000 (EV charger) was **never fetched**.

**Example Premises**: 70674364, 70670026, 70669597, 70664193, 70663090, 70593045

---

## STEP 2: Detailed Analysis of Specific Premises

### Issue A Examples: Meter Changed Mid-Cycle

#### Premise 70002132

| Field | Value |
|-------|-------|
| **Meter Change Date** (from spreadsheet) | 2025-04-14 |
| **Data Received Until** (from spreadsheet) | 2025-04-15 |
| **METERCHANGE Error** | Meter stopped on 2025-04-15 |
| **INCOMPINTVS Error** | Last meter stops at 2025-04-15, bill runs until 2025-04-28 |

**What happened**: The EV charger was physically changed/removed on April 14-15, 2025. The validation process sees that interval data ends on 04-15 but the billing period runs until 04-28, so it flags this as incomplete intervals (INCOMPINTVS error).

**The ChatGPT solution is CORRECT for this case**: Skip INCOMPINTVS check for evmeter on channel 1000.

#### Premise 70002972

| Field | Value |
|-------|-------|
| **Meter Change Date** (from spreadsheet) | 2025-04-16 |
| **Data Received Until** (from spreadsheet) | 2025-04-16 |
| **METERCHANGE Error** | Meter stopped on 2025-04-16 |
| **INCOMPINTVS Error** | Last meter stops at 2025-04-16, bill runs until 2025-05-07 |

**Same pattern** - the validation is incorrectly flagging expected EV charger removal as a data quality issue.

#### Premise 70005262

| Field | Value |
|-------|-------|
| **Meter Change Date** (from spreadsheet) | 2025-04-09 |
| **Data Received Until** (from spreadsheet) | 2025-04-11 |
| **METERCHANGE Error** | Meter stopped on 2025-04-11 |
| **INCOMPINTVS Error** | Last meter stops at 2025-04-11, bill runs until 2025-05-02 |

**Same pattern** - EV charger removed, validation flags it as error.

---

### Issue B Examples: Channel 1000 Data Never Fetched

#### Premise 70674364

| Field | Value |
|-------|-------|
| **Notes** (from spreadsheet) | "No Data has been received, for Ch 1000" |
| **EV Usage Data** | "February - June and August" (per CAMS - billing system) |
| **Errors in Error Table** | **NONE** |

**What happened**: This premise has EV usage according to the billing system (CAMS), but **no interval data (channel 1000) was ever fetched by the ALR system**. This is NOT a validation problem - this is a **data fetch problem**.

#### Premise 70670026

| Field | Value |
|-------|-------|
| **Notes** (from spreadsheet) | "No Data has been received, for Ch 1000" |
| **EV Usage Data** | "All months" (per CAMS) |
| **Errors in Error Table** | Only AUMONTH errors (not enough months for average usage) |

**What happened**: Same issue - CAMS shows EV usage for all months, but channel 1000 interval data was never fetched.

#### Premise 70664193

| Field | Value |
|-------|-------|
| **Notes** (from spreadsheet) | "No Data has been received, for Ch 1000" |
| **EV Usage Data** | "January - April 2025" (per CAMS) |
| **Errors in Error Table** | Only AUMONTH errors |

**Same pattern** - no channel 1000 data was fetched, only validation errors for not having enough months of history.

---

## STEP 3: Root Cause Identification

### Root Cause for Issue A (Validation Problem)

**Location**: `validations.py` lines 1548-1557

```python
# Current Code (problematic)
error_df_append = df2_grouped1[df2_grouped1.meterstop_dt < df2_grouped1.billstop][
    ['studyid', 'premiseid', 'rltv_mo', 'studypoint', 'meterstop_dt', 'billstop']]
```

**Problem**: This check applies to ALL meters, including EV meters (channel 1000). When an EV charger is physically removed mid-billing cycle, this is EXPECTED behavior, not a data quality issue.

### Root Cause for Issue B (Data Fetch Problem)

**Location**: `gulf_daily.json` - Process Order 8 (`mass_market_gulf` query)

The EV interval data query has restrictive join conditions:

```sql
JOIN billing_fpl_fplnw_consolidated.ev_charge_box CB 
  ON RH.charge_box_id = CB.charge_box_id 
  AND CB.connector_id = RH.connector_id 
  AND CB.site_pk = RH.site_pk 
  AND RH.read_strt_dttm BETWEEN CB.efct_strt_dttm AND CB.efct_end_dttm
```

**Possible causes for no data**:
1. The `charge_box_id` in `ev_read_hist` doesn't match any active record in `ev_charge_box`
2. The `efct_strt_dttm` / `efct_end_dttm` time bounds don't overlap with reading timestamps
3. The `asset_status = 'Asset In-Service'` filter in the meters query excludes the device
4. The `sub_comp_cd = 1600` filter may not match some FPLNW devices

---

## STEP 4: Recommended Solutions

### Solution for Issue A: Validation Fix (ChatGPT's suggestion is CORRECT)

**Modify `validations.py`** to skip INCOMPINTVS check for EV meters:

```python
# Updated Code
# At premise/bill level - but exclude EV meters (channel 1000, metertype evmeter)
df2_grouped1 = df2_grouped[~df2_grouped.meterstop_dt.isna()].copy()

# Filter out EV meters from INCOMPINTVS check
# EV chargers can legitimately stop mid-cycle when removed
non_ev_data = df2_grouped1[
    ~((df2_grouped1.channel == 1000) & 
      (df2_grouped1.metertype.isin(['evmeter', 'uevmeter'])))
]

error_df_append = non_ev_data[non_ev_data.meterstop_dt < non_ev_data.billstop][
    ['studyid', 'premiseid', 'rltv_mo', 'studypoint', 'meterstop_dt', 'billstop']]
```

### Solution for Issue B: Data Fetch Fix (Requires Investigation)

**This is NOT solved by the validation fix!**

Need to investigate why channel 1000 data isn't being fetched for premises like 70674364, 70670026, etc.

Possible fixes for `gulf_daily.json`:

1. **Relax the time-bounded join**:
```sql
-- Instead of:
AND RH.read_strt_dttm BETWEEN CB.efct_strt_dttm AND CB.efct_end_dttm

-- Consider:
AND CB.site_pk = RH.site_pk  -- Join by site, not by exact charge_box_id match
```

2. **Check if these premises have charge_box records** in `ev_charge_box` table with correct `sub_comp_cd = 1600`

3. **Verify the meter definition query** (Process Order 5) includes these devices

---

## STEP 5: Verification Steps

### For Issue A (Validation Fix)
After implementing the validation fix:
- Premises 70002132, 70002972, 70005262 should NO LONGER have INCOMPINTVS errors
- Their EV interval data up to the meter stop date should be preserved

### For Issue B (Data Fetch Fix)
Need to run diagnostic queries on the source database:

```sql
-- Check if charge_box records exist for "No Data" premises
SELECT s.site_id, cb.charge_box_id, cb.efct_strt_dttm, cb.efct_end_dttm, 
       cb.asset_status, cb.sub_comp_cd
FROM billing_fpl_fplnw_consolidated.ev_charge_box cb
JOIN billing_fpl_fplnw_consolidated.ev_site s ON cb.site_pk = s.site_pk
WHERE s.site_id IN ('70674364', '70670026', '70669597', '70664193', '70663090', '70593045')
ORDER BY s.site_id, cb.efct_strt_dttm;

-- Check if interval readings exist but aren't being joined
SELECT DISTINCT RH.site_pk, COUNT(*) as reading_count
FROM billing_fpl_fplnw_consolidated.ev_read_hist RH
JOIN billing_fpl_fplnw_consolidated.ev_site S ON RH.site_pk = S.site_pk
WHERE S.site_id IN ('70674364', '70670026', '70669597', '70664193', '70663090', '70593045')
GROUP BY RH.site_pk;
```

---

## Summary Table

| Premise ID | Issue Type | Error Code | Root Cause | Solution |
|------------|------------|------------|------------|----------|
| 70002132 | A (Validation) | INCOMPINTVS + METERCHANGE | Validation flags expected EV removal | Modify validations.py |
| 70002972 | A (Validation) | INCOMPINTVS + METERCHANGE | Validation flags expected EV removal | Modify validations.py |
| 70005262 | A (Validation) | INCOMPINTVS + METERCHANGE | Validation flags expected EV removal | Modify validations.py |
| 70674364 | B (Data Fetch) | NONE | Channel 1000 never fetched | Fix gulf_daily.json query |
| 70670026 | B (Data Fetch) | AUMONTH only | Channel 1000 never fetched | Fix gulf_daily.json query |
| 70669597 | B (Data Fetch) | AUMONTH only | Channel 1000 never fetched | Fix gulf_daily.json query |
| 70664193 | B (Data Fetch) | AUMONTH only | Channel 1000 never fetched | Fix gulf_daily.json query |
| 70663090 | B (Data Fetch) | NONE | Channel 1000 never fetched | Fix gulf_daily.json query |
| 70593045 | B (Data Fetch) | NONE | Channel 1000 never fetched | Fix gulf_daily.json query |

---

## Conclusion

**The ChatGPT solution is PARTIALLY correct** - it addresses Issue A (validation problem) but does NOT address Issue B (data fetch problem).

To fully resolve the RS1EV FPLNW issues, you need:
1. ✅ Implement the validation fix for INCOMPINTVS on EV meters
2. ⚠️ ALSO investigate and fix why channel 1000 data isn't being fetched for some premises
