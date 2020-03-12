-- assumes all input tables have been loaded into DB in Build Engine
-- input tables: sca_bluebook, doe_lcgms

-- create working tables
DROP TABLE IF EXISTS sca_bluebook_filtered;
DROP TABLE IF EXISTS doe_lcgms_filtered;
CREATE TABLE sca_bluebook_filtered AS (
SELECT * FROM sca_bluebook);
CREATE TABLE doe_lcgms_filtered AS (
SELECT * FROM doe_lcgms);
ALTER TABLE sca_bluebook_filtered
ADD COLUMN excluded text,
ADD COLUMN match text;
ALTER TABLE doe_lcgms_filtered
ADD COLUMN excluded text,
ADD COLUMN match text;

-- tag records with the reason they're being excluded
-- blue book
UPDATE sca_bluebook_filtered a
SET excluded = 'org_id IS NULL'
WHERE a.org_id IS NULL;

UPDATE sca_bluebook_filtered a
SET excluded = 'org_level IS NULL, SPED, or OTHER'
WHERE a.org_level IS NULL
OR a.org_level = 'SPED'
OR a.org_level = 'OTHER';

UPDATE sca_bluebook_filtered a
SET excluded = 'charter IS NOT NULL'
WHERE a.charter IS NOT NULL;

UPDATE sca_bluebook_filtered a
SET excluded = 'organization_name like ALC or ALTERNATIVE LEARNING or Restart org_id'
WHERE a.organization_name ~* 'ALC'
OR a.organization_name ~* 'ALTERNATIVE LEARNING'
OR a.org_id IN ('M973','Q950');

UPDATE sca_bluebook_filtered a
SET excluded = 'organization_name contains Adult OR PREK'
WHERE a.organization_name ~* 'Adult'
OR a.organization_name ~* 'pre-k';

UPDATE sca_bluebook_filtered a
SET excluded = 'competitive high schools'
WHERE a.org_id IN ('X445','K449','K430','M692','X696','Q687','R605','M475');

UPDATE sca_bluebook_filtered a
SET excluded = 'citywide gifted and talented schools'
WHERE a.org_id IN ('M539', 'M334', 'K686','Q300', 'M012', 'M485');

UPDATE sca_bluebook_filtered a
SET excluded = 'Orgid X695 OR M645'
WHERE a.org_id IN ('X695', 'M645');

-- lcgms
UPDATE doe_lcgms_filtered a
SET excluded = 'location_category_description is NULL or Ungraded'
WHERE a.location_category_description IS NULL
	OR a.location_category_description = 'Ungraded';

UPDATE doe_lcgms_filtered a
SET excluded = 'managed_by_name <> DOE (exclude charter)'
WHERE a.managed_by_name <> 'DOE';

UPDATE doe_lcgms_filtered a
SET excluded = 'location_type_description = Special Education or Home School'
WHERE a.location_type_description = 'Special Education'
OR a.location_type_description = 'Home School';

UPDATE doe_lcgms_filtered a
SET excluded = 'competitive high schools'
WHERE a.location_code IN ('X445','K449','K430','M692','X696','Q687','R605','M475');

UPDATE doe_lcgms_filtered a
SET excluded = 'citywide gifted and talented schools'
WHERE a.location_code IN ('M539', 'M334', 'K686','Q300', 'M012','M485');

UPDATE doe_lcgms_filtered a
SET excluded = 'building_name contains AF or GYM or FARM'
WHERE  a.building_name ~* ' AF'
OR a.building_name ~* 'GYM'
OR a.building_name ~* ' FARM ';

UPDATE doe_lcgms_filtered a
SET excluded = 'Orgid X695 OR M645'
WHERE a.location_code IN ('X695', 'M645');

-- populating match fields, 
-- which flags if the record is not in the sister dataset
UPDATE doe_lcgms_filtered a
SET match = 'not in blue book'
WHERE a.excluded IS NULL
AND a.location_code||a.building_code NOT IN (
	SELECT a.org_id||a.bldg_id FROM sca_bluebook_filtered a WHERE excluded IS NULL);
UPDATE sca_bluebook_filtered a
SET match = 'not in lcgms'
WHERE a.excluded IS NULL
AND a.org_id||a.bldg_id NOT IN (
	SELECT a.location_code||a.building_code FROM doe_lcgms_filtered a WHERE excluded IS NULL);

-- exlude mini and transportables that are not the only structure on the lot
WITH nonmini as (
SELECT a.*
FROM doe_lcgms_filtered a
WHERE a.building_name !~* 'PORTABLE'
AND a.building_name !~* 'MINI')
UPDATE doe_lcgms_filtered a 
SET excluded = 'Not Solo Mini or Portable'
WHERE a.location_code||a.borough_block_lot IN 
(SELECT b.location_code||b.borough_block_lot FROM nonmini b)
AND (a.building_name ~* 'PORTABLE'
OR a.building_name ~* 'MINI')
AND excluded IS NULL
AND match IS NOT NULL;

-- output lcgms records that are not in Blue Book
-- with the columns that need to be filled out by researcher
DROP TABLE IF EXISTS doe_lcgms_notinBB;
CREATE TABLE doe_lcgms_notinBB as (
SELECT a.*,
NULL as "district",
NULL as "subdistrict",
NULL as "org_level",
NULL as "org_e",
NULL as "pc",
NULL as "ic",
NULL as "hc",
NULL as "ps_per",
NULL as "ms_per",
NULL as "hs_per"
FROM doe_lcgms_filtered a
WHERE excluded IS NULL
AND match IS NOT NULL);

-- produce final output table 
DROP TABLE IF EXISTS ceqr_school_buildings;
CREATE TABLE ceqr_school_buildings as (
WITH doe_lcgms_filtered_included AS (
SELECT * FROM doe_lcgms_filtered WHERE excluded IS NULL AND match IS NULL),
sca_bluebook_filtered_included AS (
SELECT * FROM sca_bluebook_filtered WHERE excluded IS NULL)
SELECT b.district, 
	b.subdistrict, 
	LEFT(a.borough_block_lot,1) as borocode,
	a.building_name as bldg_name,
	b."bldg_excl." as excluded,
	a.building_code as bldg_id,
	a.location_code as org_id,
	b.org_level,
	a.location_name as name,
	a.address_line_1 as address,
	floor(b.pc::numeric) as pc,
	ceil(b.org_e::numeric*ROUND((REPLACE(b.ps_per,'%','')::numeric/100),5)) as pe,
	floor(b.ic::numeric) as ic,
	ceil(b.org_e::numeric*ROUND((REPLACE(b.ms_per,'%','')::numeric/100),5)) as ie,
	floor(b.hc::numeric) as hc,
	ceil(b.org_e::numeric*ROUND((REPLACE(b.hs_per,'%','')::numeric/100),5)) as he,
	ST_SetSRID(ST_MakePoint(REPLACE(a.longitude,'NULL', '0')::NUMERIC,REPLACE(a.latitude,'NULL', '0')::NUMERIC),4326) AS geom
FROM doe_lcgms_filtered_included a
LEFT JOIN sca_bluebook_filtered_included b
ON a.location_code=b.org_id
AND a.building_code = b.bldg_id
);