-- ----------------------------
-- Schema structure
-- ----------------------------
CREATE SCHEMA IF NOT EXISTS "catalog";
SET search_path = "catalog", public;

-- ----------------------------
-- Sequence structure for derived_products_id_seq
-- ----------------------------
DROP SEQUENCE IF EXISTS "catalog"."derived_products_id_seq" CASCADE;
CREATE SEQUENCE "catalog"."derived_products_id_seq" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for download_queue_id_seq
-- ----------------------------
DROP SEQUENCE IF EXISTS "catalog"."download_queue_id_seq" CASCADE;
CREATE SEQUENCE "catalog"."download_queue_id_seq" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for mosaic_queue_id_seq
-- ----------------------------
DROP SEQUENCE IF EXISTS "catalog"."mosaic_queue_id_seq" CASCADE;
CREATE SEQUENCE "catalog"."mosaic_queue_id_seq" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for original_products_id_seq
-- ----------------------------
DROP SEQUENCE IF EXISTS "catalog"."original_products_id_seq" CASCADE;
CREATE SEQUENCE "catalog"."original_products_id_seq" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for process_queue_id_seq
-- ----------------------------
DROP SEQUENCE IF EXISTS "catalog"."process_queue_id_seq" CASCADE;
CREATE SEQUENCE "catalog"."process_queue_id_seq" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for system_settings_id_seq
-- ----------------------------
DROP SEQUENCE IF EXISTS "catalog"."system_settings_id_seq" CASCADE;
CREATE SEQUENCE "catalog"."system_settings_id_seq" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Sequence structure for workspaces_id_seq
-- ----------------------------
DROP SEQUENCE IF EXISTS "catalog"."workspaces_id_seq" CASCADE;
CREATE SEQUENCE "catalog"."workspaces_id_seq" 
INCREMENT 1
MINVALUE  1
MAXVALUE 9223372036854775807
START 1
CACHE 1;

-- ----------------------------
-- Table structure for derived_products
-- ----------------------------
DROP TABLE IF EXISTS "catalog"."derived_products";
CREATE TABLE "catalog"."derived_products" (
  "id" int4 NOT NULL DEFAULT nextval('derived_products_id_seq'::regclass),
  "product_type" varchar COLLATE "pg_catalog"."default",
  "original_product_id" int4,
  "ingestion_date" date,
  "url" varchar COLLATE "pg_catalog"."default",
  "workspace_id" int4,
  "derived_from_uuid" varchar COLLATE "pg_catalog"."default"
)
;

-- ----------------------------
-- Table structure for download_queue
-- ----------------------------
DROP TABLE IF EXISTS "catalog"."download_queue";
CREATE TABLE "catalog"."download_queue" (
  "id" int4 NOT NULL DEFAULT nextval('download_queue_id_seq'::regclass),
  "uuid" varchar(50) COLLATE "pg_catalog"."default" NOT NULL,
  "priority" int2 NOT NULL DEFAULT 1,
  "workspace_id" int4,
  "creation_time" timestamp(6) NOT NULL DEFAULT now(),
  "status" varchar(20) COLLATE "pg_catalog"."default",
  "init_time" timestamp(6),
  "product_id" varchar COLLATE "pg_catalog"."default",
  "path" varchar COLLATE "pg_catalog"."default",
  "ingestion_date" timestamp(6),
  "sensing_date" date,
  "cloud_coverage" float4,
  "sensor" varchar COLLATE "pg_catalog"."default",
  "orbit_number" int4,
  "tile_id" varchar COLLATE "pg_catalog"."default",
  "tile_data_geometry" geometry(POLYGON, 4326)
)
;

-- ----------------------------
-- Table structure for mosaic_definitions
-- ----------------------------
DROP TABLE IF EXISTS "catalog"."mosaic_definitions";
CREATE TABLE "catalog"."mosaic_definitions" (
  "workspace_id" int4 NOT NULL,
  "granules_list" varchar COLLATE "pg_catalog"."default" NOT NULL,
  "source_products_names" varchar COLLATE "pg_catalog"."default",
  "mosaic_names" varchar COLLATE "pg_catalog"."default",
  "mosaic_paths" varchar COLLATE "pg_catalog"."default",
  "source_products_paths" varchar COLLATE "pg_catalog"."default",
  "orbit_id" int4 NOT NULL
)
;

-- ----------------------------
-- Table structure for mosaic_queue
-- ----------------------------
DROP TABLE IF EXISTS "catalog"."mosaic_queue";
CREATE TABLE "catalog"."mosaic_queue" (
  "id" int4 NOT NULL DEFAULT nextval('mosaic_queue_id_seq'::regclass),
  "first_date" date NOT NULL,
  "workspace_id" int4,
  "status" varchar(10) COLLATE "pg_catalog"."default" NOT NULL,
  "sensing_date" date,
  "orbit_id" int4,
  "init_time" timestamp(6),
  "creation_time" timestamp(6) DEFAULT now(),
  "priority" int4
)
;

-- ----------------------------
-- Table structure for original_products
-- ----------------------------
DROP TABLE IF EXISTS "catalog"."original_products";
CREATE TABLE "catalog"."original_products" (
  "id" int4 NOT NULL DEFAULT nextval('original_products_id_seq'::regclass),
  "url" varchar COLLATE "pg_catalog"."default",
  "ingestion_date" date,
  "sensing_date" date,
  "tile_data_geometry" geometry(POLYGON, 4326),
  "cloud_coverage" float4,
  "sensor" varchar COLLATE "pg_catalog"."default",
  "orbit_number" int4,
  "tile_id" varchar COLLATE "pg_catalog"."default",
  "product_id" varchar COLLATE "pg_catalog"."default",
  "processed" bool,
  "used" bool,
  "workspace_id" int4
)
;

-- ----------------------------
-- Table structure for process_queue
-- ----------------------------
DROP TABLE IF EXISTS "catalog"."process_queue";
CREATE TABLE "catalog"."process_queue" (
  "id" int4 NOT NULL DEFAULT nextval('process_queue_id_seq'::regclass),
  "status" varchar(15) COLLATE "pg_catalog"."default",
  "process_params" varchar COLLATE "pg_catalog"."default",
  "process_command" varchar COLLATE "pg_catalog"."default",
  "init_time" timestamp(6),
  "finish_time" timestamp(6),
  "input_file_path" varchar COLLATE "pg_catalog"."default" NOT NULL,
  "workspace_id" int4,
  "priority" int4,
  "creation_time" timestamp(6) DEFAULT now(),
  "product_id" varchar COLLATE "pg_catalog"."default",
  "uuid" varchar COLLATE "pg_catalog"."default",
  "orbit_number" int4,
  "sensing_date" date
)
;

-- ----------------------------
-- Table structure for system_settings
-- ----------------------------
DROP TABLE IF EXISTS "catalog"."system_settings";
CREATE TABLE "catalog"."system_settings" (
  "id" int4 NOT NULL DEFAULT nextval('system_settings_id_seq'::regclass),
  "param_name" varchar(30) COLLATE "pg_catalog"."default" NOT NULL,
  "value" varchar COLLATE "pg_catalog"."default" NOT NULL,
  "units" varchar(20) COLLATE "pg_catalog"."default"
)
;

-- ----------------------------
-- Table structure for workspaces
-- ----------------------------
DROP TABLE IF EXISTS "catalog"."workspaces";
CREATE TABLE "catalog"."workspaces" (
  "id" int4 NOT NULL DEFAULT nextval('workspaces_id_seq'::regclass),
  "name" varchar COLLATE "pg_catalog"."default",
  "description" varchar COLLATE "pg_catalog"."default",
  "geom" geometry(POLYGON, 4326),
  "s2_user" varchar(70) COLLATE "pg_catalog"."default",
  "s2_pass" varchar(30) COLLATE "pg_catalog"."default",
  "s2_download_url" varchar COLLATE "pg_catalog"."default",
  "s2_product_type" varchar(20) COLLATE "pg_catalog"."default",
  "s2_time_range" int4,
  "s2_download_path" varchar COLLATE "pg_catalog"."default",
  "s2_process_command" varchar COLLATE "pg_catalog"."default",
  "s2_process_params" varchar COLLATE "pg_catalog"."default",
  "max_downloads_per_user" int4,
  "log_path" varchar COLLATE "pg_catalog"."default",
  "days_to_query_mosaic" int4,
  "s2_granules_list" varchar COLLATE "pg_catalog"."default",
  "active" bool,
  "s2_collection" varchar(25) COLLATE "pg_catalog"."default",
  "s2_max_cloud_cover" numeric DEFAULT 100
)
;

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"catalog"."derived_products_id_seq"', 1, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"catalog"."download_queue_id_seq"', 1, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"catalog"."mosaic_queue_id_seq"', 1, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"catalog"."original_products_id_seq"', 1, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"catalog"."process_queue_id_seq"', 1, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"catalog"."system_settings_id_seq"', 1, true);

-- ----------------------------
-- Alter sequences owned by
-- ----------------------------
SELECT setval('"catalog"."workspaces_id_seq"', 1, false);

-- ----------------------------
-- Indexes structure for table derived_products
-- ----------------------------
CREATE INDEX IF NOT EXISTS "derived_products_idx_derived_from_uuid" ON "catalog"."derived_products" USING btree (
  "derived_from_uuid" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX IF NOT EXISTS "derived_products_idx_original_product_id" ON "catalog"."derived_products" USING btree (
  "original_product_id" "pg_catalog"."int4_ops" ASC NULLS LAST
);
CREATE INDEX IF NOT EXISTS "derived_products_idx_workspace" ON "catalog"."derived_products" USING btree (
  "workspace_id" "pg_catalog"."int4_ops" ASC NULLS LAST
);

-- ----------------------------
-- Primary Key structure for table derived_products
-- ----------------------------
ALTER TABLE "catalog"."derived_products" ADD CONSTRAINT "derived_products_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table download_queue
-- ----------------------------
CREATE INDEX IF NOT EXISTS "download_queue_idx_orbit_number" ON "catalog"."download_queue" USING btree (
  "orbit_number" "pg_catalog"."int4_ops" ASC NULLS LAST
);
CREATE INDEX IF NOT EXISTS "download_queue_idx_sensing_date" ON "catalog"."download_queue" USING btree (
  "sensing_date" "pg_catalog"."date_ops" ASC NULLS LAST
);
CREATE INDEX IF NOT EXISTS "download_queue_idx_status_priority_creation" ON "catalog"."download_queue" USING btree (
  "status" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST,
  "priority" "pg_catalog"."int2_ops" DESC NULLS FIRST,
  "creation_time" "pg_catalog"."timestamp_ops" ASC NULLS LAST
);
CREATE INDEX IF NOT EXISTS "download_queue_idx_workspace_status" ON "catalog"."download_queue" USING btree (
  "workspace_id" "pg_catalog"."int4_ops" ASC NULLS LAST,
  "status" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

-- ----------------------------
-- Uniques structure for table download_queue
-- ----------------------------
ALTER TABLE "catalog"."download_queue" ADD CONSTRAINT "download_queue_uuid_key" UNIQUE ("uuid");

-- ----------------------------
-- Checks structure for table download_queue
-- ----------------------------
ALTER TABLE "catalog"."download_queue" ADD CONSTRAINT "download_queue_status_chk" CHECK (status IS NULL OR (status::text = ANY (ARRAY['waiting'::text, 'downloading'::text, 'completed'::text, 'skipped'::text, 'cancelled'::text, 'error'::text])));

-- ----------------------------
-- Primary Key structure for table download_queue
-- ----------------------------
ALTER TABLE "catalog"."download_queue" ADD CONSTRAINT "download_queue_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Primary Key structure for table mosaic_definitions
-- ----------------------------
ALTER TABLE "catalog"."mosaic_definitions" ADD CONSTRAINT "mosaic_definitions_pkey" PRIMARY KEY ("workspace_id", "orbit_id");

-- ----------------------------
-- Indexes structure for table mosaic_queue
-- ----------------------------
CREATE INDEX IF NOT EXISTS "mosaic_queue_idx_sensing_date_orbit" ON "catalog"."mosaic_queue" USING btree (
  "sensing_date" "pg_catalog"."date_ops" ASC NULLS LAST,
  "orbit_id" "pg_catalog"."int4_ops" ASC NULLS LAST
);
CREATE INDEX IF NOT EXISTS "mosaic_queue_idx_status_priority_creation" ON "catalog"."mosaic_queue" USING btree (
  "status" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST,
  "priority" "pg_catalog"."int4_ops" DESC NULLS FIRST,
  "creation_time" "pg_catalog"."timestamp_ops" ASC NULLS LAST
);
CREATE INDEX IF NOT EXISTS "mosaic_queue_idx_workspace_status" ON "catalog"."mosaic_queue" USING btree (
  "workspace_id" "pg_catalog"."int4_ops" ASC NULLS LAST,
  "status" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

-- ----------------------------
-- Uniques structure for table mosaic_queue
-- ----------------------------
ALTER TABLE "catalog"."mosaic_queue" ADD CONSTRAINT "mosaic_queue_uq_operational" UNIQUE ("workspace_id", "orbit_id", "sensing_date");

-- ----------------------------
-- Checks structure for table mosaic_queue
-- ----------------------------
ALTER TABLE "catalog"."mosaic_queue" ADD CONSTRAINT "mosaic_queue_status_chk" CHECK (status::text = ANY (ARRAY['waiting'::character varying, 'processing'::character varying, 'completed'::character varying, 'error'::character varying, 'cancelled'::character varying]::text[]));

-- ----------------------------
-- Primary Key structure for table mosaic_queue
-- ----------------------------
ALTER TABLE "catalog"."mosaic_queue" ADD CONSTRAINT "mosaic_queue_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table original_products
-- ----------------------------
CREATE INDEX IF NOT EXISTS "original_products_idx_orbit_tile" ON "catalog"."original_products" USING btree (
  "orbit_number" "pg_catalog"."int4_ops" ASC NULLS LAST,
  "tile_id" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX IF NOT EXISTS "original_products_idx_workspace_sensing_date" ON "catalog"."original_products" USING btree (
  "workspace_id" "pg_catalog"."int4_ops" ASC NULLS LAST,
  "sensing_date" "pg_catalog"."date_ops" ASC NULLS LAST
);
CREATE UNIQUE INDEX "original_products_uq_workspace_product_id" ON "catalog"."original_products" USING btree (
  "workspace_id" "pg_catalog"."int4_ops" ASC NULLS LAST,
  "product_id" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
) WHERE product_id IS NOT NULL;

-- ----------------------------
-- Primary Key structure for table original_products
-- ----------------------------
ALTER TABLE "catalog"."original_products" ADD CONSTRAINT "original_products_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Indexes structure for table process_queue
-- ----------------------------
CREATE INDEX IF NOT EXISTS "process_queue_idx_product_id" ON "catalog"."process_queue" USING btree (
  "product_id" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX IF NOT EXISTS "process_queue_idx_sensing_date_orbit" ON "catalog"."process_queue" USING btree (
  "sensing_date" "pg_catalog"."date_ops" ASC NULLS LAST,
  "orbit_number" "pg_catalog"."int4_ops" ASC NULLS LAST
);
CREATE INDEX IF NOT EXISTS "process_queue_idx_status_priority_creation" ON "catalog"."process_queue" USING btree (
  "status" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST,
  "priority" "pg_catalog"."int4_ops" DESC NULLS FIRST,
  "creation_time" "pg_catalog"."timestamp_ops" ASC NULLS LAST
);
CREATE INDEX IF NOT EXISTS "process_queue_idx_uuid" ON "catalog"."process_queue" USING btree (
  "uuid" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);
CREATE INDEX IF NOT EXISTS "process_queue_idx_workspace_status" ON "catalog"."process_queue" USING btree (
  "workspace_id" "pg_catalog"."int4_ops" ASC NULLS LAST,
  "status" COLLATE "pg_catalog"."default" "pg_catalog"."text_ops" ASC NULLS LAST
);

-- ----------------------------
-- Checks structure for table process_queue
-- ----------------------------
ALTER TABLE "catalog"."process_queue" ADD CONSTRAINT "process_queue_status_chk" CHECK (status IS NULL OR (status::text = ANY (ARRAY['waiting'::character varying::text, 'processing'::character varying::text, 'completed'::character varying::text, 'error'::character varying::text, 'cancelled'::character varying::text])));

-- ----------------------------
-- Primary Key structure for table process_queue
-- ----------------------------
ALTER TABLE "catalog"."process_queue" ADD CONSTRAINT "process_queue_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Uniques structure for table system_settings
-- ----------------------------
ALTER TABLE "catalog"."system_settings" ADD CONSTRAINT "system_settings_param_name_key" UNIQUE ("param_name");

-- ----------------------------
-- Primary Key structure for table system_settings
-- ----------------------------
ALTER TABLE "catalog"."system_settings" ADD CONSTRAINT "system_settings_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Primary Key structure for table workspaces
-- ----------------------------
ALTER TABLE "catalog"."workspaces" ADD CONSTRAINT "workspaces_pkey" PRIMARY KEY ("id");

-- ----------------------------
-- Foreign Keys structure for table derived_products
-- ----------------------------
ALTER TABLE "catalog"."derived_products" ADD CONSTRAINT "derived_products_original_product_id_fkey" FOREIGN KEY ("original_product_id") REFERENCES "catalog"."original_products" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;
ALTER TABLE "catalog"."derived_products" ADD CONSTRAINT "derived_products_workspace_id_fkey" FOREIGN KEY ("workspace_id") REFERENCES "catalog"."workspaces" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table download_queue
-- ----------------------------
ALTER TABLE "catalog"."download_queue" ADD CONSTRAINT "download_queue_workspace_id_fkey" FOREIGN KEY ("workspace_id") REFERENCES "catalog"."workspaces" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table mosaic_definitions
-- ----------------------------
ALTER TABLE "catalog"."mosaic_definitions" ADD CONSTRAINT "mosaic_definitions_workspace_id_fkey" FOREIGN KEY ("workspace_id") REFERENCES "catalog"."workspaces" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table mosaic_queue
-- ----------------------------
ALTER TABLE "catalog"."mosaic_queue" ADD CONSTRAINT "mosaic_queue_workspace_id_fkey" FOREIGN KEY ("workspace_id") REFERENCES "catalog"."workspaces" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table original_products
-- ----------------------------
ALTER TABLE "catalog"."original_products" ADD CONSTRAINT "original_products_workspace_id_fkey" FOREIGN KEY ("workspace_id") REFERENCES "catalog"."workspaces" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;

-- ----------------------------
-- Foreign Keys structure for table process_queue
-- ----------------------------
ALTER TABLE "catalog"."process_queue" ADD CONSTRAINT "process_queue_workspace_id_fkey" FOREIGN KEY ("workspace_id") REFERENCES "catalog"."workspaces" ("id") ON DELETE NO ACTION ON UPDATE NO ACTION;
