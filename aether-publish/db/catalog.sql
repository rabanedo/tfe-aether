-- =============================================================================
-- CONFIGURACIÓN DE SESIÓN (opcional, puede ayudar)
SET statement_timeout = 0;
SET lock_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

-- =============================================================================
-- EXTENSIONES (ya la tienes, pero por si acaso)
CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;
COMMENT ON EXTENSION postgis IS 'PostGIS geometry, geography, and raster spatial types and functions';

-- =============================================================================
-- TABLAS
SET default_tablespace = '';
SET default_table_access_method = heap;

-- Tabla s2ndvi
CREATE TABLE public.s2ndvi (
    fid       integer                          NOT NULL,
    the_geom  public.geometry(Polygon, 25830),
    location  character varying(255),
    ingestion timestamp without time zone,
    elevation integer
);
ALTER TABLE public.s2ndvi OWNER TO postgres;
CREATE SEQUENCE public.s2ndvi_fid_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
ALTER TABLE public.s2ndvi_fid_seq OWNER TO postgres;
ALTER SEQUENCE public.s2ndvi_fid_seq OWNED BY public.s2ndvi.fid;
ALTER TABLE ONLY public.s2ndvi ALTER COLUMN fid SET DEFAULT nextval('public.s2ndvi_fid_seq'::regclass);

-- Tabla s2rgb
CREATE TABLE public.s2rgb (
    fid       integer                          NOT NULL,
    the_geom  public.geometry(Polygon, 25830),
    location  character varying(255),
    ingestion timestamp without time zone,
    elevation integer
);
ALTER TABLE public.s2rgb OWNER TO postgres;
CREATE SEQUENCE public.s2rgb_fid_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
ALTER TABLE public.s2rgb_fid_seq OWNER TO postgres;
ALTER SEQUENCE public.s2rgb_fid_seq OWNED BY public.s2rgb.fid;
ALTER TABLE ONLY public.s2rgb ALTER COLUMN fid SET DEFAULT nextval('public.s2rgb_fid_seq'::regclass);

-- Tabla s2ndvi_mosaic
CREATE TABLE public.s2ndvi_mosaic (
    fid       integer                          NOT NULL,
    the_geom  public.geometry(Polygon, 25830),
    location  character varying(255),
    ingestion timestamp without time zone,
    elevation integer
);
ALTER TABLE public.s2ndvi_mosaic OWNER TO postgres;
CREATE SEQUENCE public.s2ndvi_mosaic_fid_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
ALTER TABLE public.s2ndvi_mosaic_fid_seq OWNER TO postgres;
ALTER SEQUENCE public.s2ndvi_mosaic_fid_seq OWNED BY public.s2ndvi_mosaic.fid;
ALTER TABLE ONLY public.s2ndvi_mosaic ALTER COLUMN fid SET DEFAULT nextval('public.s2ndvi_mosaic_fid_seq'::regclass);

-- Tabla s2rgb_mosaic
CREATE TABLE public.s2rgb_mosaic (
    fid       integer                          NOT NULL,
    the_geom  public.geometry(Polygon, 25830),
    location  character varying(255),
    ingestion timestamp without time zone,
    elevation integer
);
ALTER TABLE public.s2rgb_mosaic OWNER TO postgres;
CREATE SEQUENCE public.s2rgb_mosaic_fid_seq START WITH 1 INCREMENT BY 1 NO MINVALUE NO MAXVALUE CACHE 1;
ALTER TABLE public.s2rgb_mosaic_fid_seq OWNER TO postgres;
ALTER SEQUENCE public.s2rgb_mosaic_fid_seq OWNED BY public.s2rgb_mosaic.fid;
ALTER TABLE ONLY public.s2rgb_mosaic ALTER COLUMN fid SET DEFAULT nextval('public.s2rgb_mosaic_fid_seq'::regclass);

-- =============================================================================
-- CLAVES PRIMARIAS
ALTER TABLE ONLY public.s2ndvi ADD CONSTRAINT s2ndvi_pkey PRIMARY KEY (fid);
ALTER TABLE ONLY public.s2rgb ADD CONSTRAINT s2rgb_pkey PRIMARY KEY (fid);
ALTER TABLE ONLY public.s2ndvi_mosaic ADD CONSTRAINT s2ndvi_mosaic_pkey PRIMARY KEY (fid);
ALTER TABLE ONLY public.s2rgb_mosaic ADD CONSTRAINT s2rgb_mosaic_pkey PRIMARY KEY (fid);

-- =============================================================================
-- ÍNDICES ESPACIALES
CREATE INDEX spatial_s2ndvi_the_geom ON public.s2ndvi USING gist (the_geom);
CREATE INDEX spatial_s2rgb_the_geom ON public.s2rgb USING gist (the_geom);
CREATE INDEX spatial_s2ndvi_mosaic_the_geom ON public.s2ndvi_mosaic USING gist (the_geom);
CREATE INDEX spatial_s2rgb_mosaic_the_geom ON public.s2rgb_mosaic USING gist (the_geom);

-- Índices por fecha de ingesta
CREATE INDEX idx_s2ndvi_ingestion ON public.s2ndvi (ingestion);
CREATE INDEX idx_s2rgb_ingestion ON public.s2rgb (ingestion);
CREATE INDEX idx_s2ndvi_mosaic_ingestion ON public.s2ndvi_mosaic (ingestion);
CREATE INDEX idx_s2rgb_mosaic_ingestion ON public.s2rgb_mosaic (ingestion);

-- =============================================================================
-- PROPIEDAD DE LAS TABLAS Y SECUENCIAS
-- =============================================================================

-- Dar acceso al esquema
GRANT USAGE ON SCHEMA public TO aether_user;

-- Traspasar propiedad de las tablas a aether_user
ALTER TABLE public.s2ndvi OWNER TO aether_user;
ALTER TABLE public.s2rgb OWNER TO aether_user;
ALTER TABLE public.s2ndvi_mosaic OWNER TO aether_user;
ALTER TABLE public.s2rgb_mosaic OWNER TO aether_user;

-- Traspasar propiedad de las secuencias a aether_user
ALTER SEQUENCE public.s2ndvi_fid_seq OWNER TO aether_user;
ALTER SEQUENCE public.s2rgb_fid_seq OWNER TO aether_user;
ALTER SEQUENCE public.s2ndvi_mosaic_fid_seq OWNER TO aether_user;
ALTER SEQUENCE public.s2rgb_mosaic_fid_seq OWNER TO aether_user;