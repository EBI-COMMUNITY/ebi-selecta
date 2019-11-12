--
-- PostgreSQL database dump
--

-- Dumped from database version 11.2 (Ubuntu 11.2-1.pgdg16.04+1)
-- Dumped by pg_dump version 11.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: selectadb_production; Type: DATABASE; Schema: -; Owner: postgres
--

-- CREATE DATABASE selectadb_production WITH TEMPLATE = template0 ENCODING = 'UTF8' LC_COLLATE = 'en_US.UTF-8' LC_CTYPE = 'en_US.UTF-8';


ALTER DATABASE selectadb_production OWNER TO postgres;

\connect selectadb_production

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_with_oids = false;

--
-- Name: account; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.account (
    account_id character varying(128) DEFAULT ''::character varying NOT NULL,
    email character varying(510) DEFAULT NULL::character varying,
    password character varying(128) NOT NULL,
    account_type character varying(128) NOT NULL
);


ALTER TABLE public.account OWNER TO postgres;

--
-- Name: cv_pipelines; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cv_pipelines (
    pipeline_id integer NOT NULL,
    pipline_name character varying(400) DEFAULT NULL::character varying,
    pipeline_desc character varying(2000) DEFAULT NULL::character varying,
    pipeline_properties character varying(1000) DEFAULT NULL::character varying
);


ALTER TABLE public.cv_pipelines OWNER TO postgres;

--
-- Name: process_attributes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.process_attributes (
    process_id character varying(200) DEFAULT NULL::character varying,
    attribute_key character varying(200) DEFAULT NULL::character varying,
    attribute_value character varying(400) DEFAULT NULL::character varying
);


ALTER TABLE public.process_attributes OWNER TO postgres;

--
-- Name: process_report; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.process_report (
    study_accession character varying(90) NOT NULL,
    datahub character varying(90) NOT NULL,
    run_accession character varying(90) DEFAULT NULL::character varying,
    process_id character varying(90) NOT NULL,
    selection_id integer NOT NULL,
    analysis_id character varying(90) DEFAULT NULL::character varying,
    process_report_start_time timestamp with time zone,
    process_report_end_time timestamp with time zone,
    process_report_id integer NOT NULL,
    submission_id character varying(90) DEFAULT NULL::character varying
);


ALTER TABLE public.process_report OWNER TO postgres;

--
-- Name: process_report_process_report_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.process_report_process_report_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.process_report_process_report_id_seq OWNER TO postgres;

--
-- Name: process_report_process_report_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.process_report_process_report_id_seq OWNED BY public.process_report.process_report_id;


--
-- Name: process_selection; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.process_selection (
    selection_id integer NOT NULL,
    datahub character varying(200) DEFAULT NULL::character varying,
    tax_id integer,
    study_accession character varying(90) DEFAULT NULL::character varying,
    run_accession character varying(90) DEFAULT NULL::character varying,
    pipeline_name character varying(400) NOT NULL,
    analysis_id character varying(90) DEFAULT NULL::character varying,
    public character varying(90) DEFAULT NULL::character varying,
    selection_provided_date timestamp with time zone,
    selection_to_attribute_start timestamp with time zone,
    selection_to_attribute_end timestamp with time zone,
    selection_to_attribute_error character varying(1000) DEFAULT NULL::character varying,
    audit_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    audit_user character varying(90) DEFAULT NULL::character varying,
    webin character varying(200) NOT NULL,
    process_type character varying(90) DEFAULT NULL::character varying,
    continuity character varying(90) DEFAULT NULL::character varying
);


ALTER TABLE public.process_selection OWNER TO postgres;

--
-- Name: process_selection_selection_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.process_selection_selection_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.process_selection_selection_id_seq OWNER TO postgres;

--
-- Name: process_selection_selection_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.process_selection_selection_id_seq OWNED BY public.process_selection.selection_id;


--
-- Name: process_stages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.process_stages (
    process_id character varying(200) NOT NULL,
    stage_name character varying(200) NOT NULL,
    selection_id integer NOT NULL,
    audit_time timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    audit_user character varying(200) DEFAULT NULL::character varying,
    stage_start timestamp with time zone,
    stage_end timestamp with time zone,
    stage_error text
);


ALTER TABLE public.process_stages OWNER TO postgres;

--
-- Name: selecta_rule_templates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.selecta_rule_templates (
    template_id integer NOT NULL,
    pipeline_id character varying(90) DEFAULT NULL::character varying,
    template character varying(90) DEFAULT NULL::character varying,
    master_attributes character varying(90) DEFAULT NULL::character varying,
    all_attributes character varying(90) DEFAULT NULL::character varying
);


ALTER TABLE public.selecta_rule_templates OWNER TO postgres;

--
-- Name: process_report process_report_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.process_report ALTER COLUMN process_report_id SET DEFAULT nextval('public.process_report_process_report_id_seq'::regclass);


--
-- Name: process_selection selection_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.process_selection ALTER COLUMN selection_id SET DEFAULT nextval('public.process_selection_selection_id_seq'::regclass);


--
-- Data for Name: account; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.account (account_id, email, password, account_type) FROM stdin;
Webin-45433	\N	==gNxAjMzl2c5xWYuFUY0NWZsV2U	webin
dcc_dvorak	\N	=cUeoN1VzEVS	datahub
\.


--
-- Data for Name: cv_pipelines; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cv_pipelines (pipeline_id, pipline_name, pipeline_desc, pipeline_properties) FROM stdin;
\.


--
-- Data for Name: selecta_rule_templates; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.selecta_rule_templates (template_id, pipeline_id, template, master_attributes, all_attributes) FROM stdin;
\.


--
-- Name: process_report_process_report_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.process_report_process_report_id_seq', 2090, true);


--
-- Name: process_selection_selection_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.process_selection_selection_id_seq', 2, true);


--
-- Name: account account_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account
    ADD CONSTRAINT account_pkey PRIMARY KEY (account_id);


--
-- Name: cv_pipelines cv_pipelines_pipline_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cv_pipelines
    ADD CONSTRAINT cv_pipelines_pipline_name_key UNIQUE (pipline_name);


--
-- Name: cv_pipelines cv_pipelines_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cv_pipelines
    ADD CONSTRAINT cv_pipelines_pkey PRIMARY KEY (pipeline_id);


--
-- Name: process_report process_report_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.process_report
    ADD CONSTRAINT process_report_pkey PRIMARY KEY (process_report_id);


--
-- Name: process_selection process_selection_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.process_selection
    ADD CONSTRAINT process_selection_pkey PRIMARY KEY (selection_id);


--
-- Name: process_stages process_stages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.process_stages
    ADD CONSTRAINT process_stages_pkey PRIMARY KEY (process_id, stage_name);


--
-- Name: selecta_rule_templates selecta_rule_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.selecta_rule_templates
    ADD CONSTRAINT selecta_rule_templates_pkey PRIMARY KEY (template_id);


--
-- PostgreSQL database dump complete
--

