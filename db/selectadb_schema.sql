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
dcc_allison	\N	=clZ5Yja182d	datahub
dcc_beard	\N	=smchdHe0cWb	datahub
dcc_beethoven	\N	=IDUihHOQhDe	datahub
dcc_benoit	\N	=UWVkVmexZzS	datahub
dcc_blake	\N	=MkTwZFOptEV	datahub
dcc_bley	\N	=0Ud1QDNnh1V	datahub
dcc_bromhead	\N	=s2MyFWQ30UR	datahub
dcc_cole	\N	=EHUVJGZ0gVY	datahub
dcc_dvorak	\N	=cUeoN1VzEVS	datahub
dcc_handel	\N	=oHOWpXclhWW	datahub
dcc_schumann	\N	=ITQ3J3UtNVY	datahub
dcc_vivaldi	\N	=M1V2YUb5tWT	datahub
Webin-45433	\N	==gNxAjMzl2c5xWYuFUY0NWZsV2U	webin
\.


--
-- Data for Name: cv_pipelines; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cv_pipelines (pipeline_id, pipline_name, pipeline_desc, pipeline_properties) FROM stdin;
\.


--
-- Data for Name: process_selection; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.process_selection (selection_id, datahub, tax_id, study_accession, run_accession, pipeline_name, analysis_id, public, selection_provided_date, selection_to_attribute_start, selection_to_attribute_end, selection_to_attribute_error, audit_time, audit_user, webin, process_type, continuity) FROM stdin;
4	dcc_beethoven	\N	PRJEB11174	\N	DTU_CGE	\N	NO	2016-12-13 21:52:00+00	2018-09-06 13:48:35+01	\N	\N	2016-12-11 01:27:23	\N	Webin-45433	datahub	yes
5	dcc_beethoven	\N	PRJEB13610	\N	DTU_CGE	\N	NO	\N	2017-09-13 09:04:11+01	2016-12-15 15:44:57+00	\N	2016-12-15 15:37:38	\N	Webin-45433	\N	\N
7	dcc_vivaldi	\N	PRJEB15201	\N	DTU_CGE	\N	NO	2016-12-19 23:55:20+00	2017-09-13 09:04:11+01	2016-12-20 12:41:43+00	\N	2016-12-19 23:51:20	\N	Webin-45433	\N	\N
8	dcc_vivaldi	\N	PRJEB16326	\N	DTU_CGE	\N	NO	2016-12-19 23:55:20+00	2017-09-13 09:04:11+01	2016-12-20 12:41:52+00	\N	2016-12-19 23:51:33	\N	Webin-45433	\N	\N
9	dcc_vivaldi	\N	PRJEB18442	\N	DTU_CGE	\N	NO	2016-12-19 23:55:20+00	2017-09-13 09:04:11+01	2016-12-20 12:41:53+00	\N	2016-12-19 23:51:44	\N	Webin-45433	\N	\N
12	dcc_dvorak	\N	PRJEB14476	\N	DTU_CGE	\N	NO	2017-03-13 00:05:12+00	2017-09-13 09:04:11+01	2017-03-13 00:11:44+00	\N	2017-03-13 00:05:12	\N	Webin-45433	\N	\N
14	dcc_allison	\N	PRJEB15708	\N	DTU_CGE	\N	NO	2017-05-03 00:08:43+01	2017-09-13 09:04:11+01	2017-05-03 00:11:17+01	\N	2017-05-03 00:08:43	\N	Webin-45433	\N	\N
16	dcc_schumann	\N	PRJEB14042	\N	EMC_SLIM	\N	NO	2017-09-25 11:58:40+01	2017-09-25 12:20:03+01	2017-09-25 12:20:03+01	\N	2017-09-25 11:58:40	\N	Webin-45433	\N	\N
19	dcc_benoit	\N	PRJEB21631	ERR2023578	DTU_CGE	\N	NO	2018-03-20 14:38:41+00	2018-04-18 16:19:40+01	2018-04-18 16:20:13+01	\N	2018-03-20 14:38:41	\N	Webin-45433	study	yes
10	dcc_beethoven	\N	PRJEB2822	ERR233409	EMC_SLIM	\N	NO	2017-02-14 16:27:35+00	2019-05-16 13:28:05.374209+01	2019-05-16 13:28:17.828121+01	\N	2017-02-14 16:27:35	\N	Webin-45433	run	yes
20	dcc_benoit	\N	PRJEB21631	ERR2023514	DTU_CGE	\N	NO	2018-03-20 14:38:41+00	2019-05-16 13:29:04.311055+01	\N	\N	2018-03-20 14:38:41	\N	Webin-45433	run	yes
13	dcc_allison	\N	PRJEB2059	\N	DTU_CGE	\N	NO	2017-05-03 00:08:28+01	\N	\N	\N	2017-05-03 00:08:28	\N	Webin-45433	datahub	yes
27	dcc_allison	\N		\N	UAntwerp_bacpipe	\N	NO	2018-12-20 15:59:32+00	\N	\N	\N	2018-12-20 15:59:32	\N	Webin-45433	datahub	yes
17	dcc_beard	\N	PRJEB23496	\N	EMC_SLIM	\N	NO	2017-11-27 01:33:32+00	\N	\N	\N	2017-11-27 01:33:32	\N	Webin-45433	datahub	yes
21	dcc_benoit	\N	PRJNA183850	SRR1002804	DTU_CGE	\N	NO	2018-03-20 14:38:41+00	\N	\N	\N	2018-03-20 14:38:41	\N	Webin-45433	datahub	yes
28	dcc_benoit	\N		\N	UAntwerp_bacpipe	\N	NO	2018-12-20 15:59:32+00	\N	\N	\N	2018-12-20 15:59:32	\N	Webin-45433	datahub	yes
22	dcc_blake	\N	PRJEB27692	\N	DTU_CGE	\N	NO	2018-04-19 16:42:14+01	\N	\N	\N	2018-04-19 15:42:14	\N	Webin-45433	datahub	yes
29	dcc_blake	\N		\N	UAntwerp_bacpipe	\N	NO	2018-12-20 15:59:32+00	\N	\N	\N	2018-12-20 15:59:32	\N	Webin-45433	datahub	yes
23	dcc_bley	\N	\N	\N	DTU_CGE	\N	NO	2018-04-19 16:42:17+01	\N	\N	\N	2018-04-19 15:42:17	\N	Webin-45433	datahub	yes
30	dcc_bley	\N		\N	UAntwerp_bacpipe	\N	NO	2018-12-20 15:59:32+00	\N	\N	\N	2018-12-20 15:59:32	\N	Webin-45433	datahub	yes
24	dcc_bromhead	\N		\N	DTU_CGE	\N	NO	2018-11-27 15:50:06+00	\N	\N	\N	2018-11-27 15:50:06	\N	Webin-45433	datahub	yes
31	dcc_bromhead	\N		\N	UAntwerp_bacpipe	\N	NO	2018-12-20 15:59:32+00	\N	\N	\N	2018-12-20 15:59:32	\N	Webin-45433	datahub	yes
32	dcc_cole	\N	\N	\N	EMC_SLIM	\N	NO	2019-03-13 13:52:03+00	\N	\N	\N	2019-03-13 13:52:03	\N	Webin-45433	datahub	yes
11	dcc_dvorak	\N	PRJEB11543	\N	DTU_CGE	\N	NO	2017-03-13 00:05:02+00	\N	\N	\N	2017-03-13 00:05:02	\N	Webin-45433	datahub	yes
26	dcc_dvorak	\N		ERR2023578	UAntwerp_bacpipe	\N	NO	2018-12-20 15:59:32+00	\N	\N	\N	2018-12-20 15:59:32	\N	Webin-45433	datahub	yes
18	dcc_handel	\N	PRJEB23606	\N	EMC_SLIM	\N	NO	2017-12-01 12:47:44+00	\N	\N	\N	2017-12-01 12:47:44	\N	Webin-45433	datahub	yes
15	dcc_schumann	\N	PRJEB20879	\N	EMC_SLIM	\N	NO	2017-09-25 11:58:17+01	\N	\N	\N	2017-09-25 11:58:17	\N	Webin-45433	datahub	yes
6	dcc_vivaldi	\N	PRJEB15081	\N	DTU_CGE	\N	NO	2016-12-19 23:55:20+00	\N	\N	\N	2016-12-19 23:51:05	\N	Webin-45433	datahub	yes
25	dcc_vivaldi	\N	PRJEB21880	ERR2044142	UAntwerp_bacpipe	\N	NO	2018-12-20 15:59:32+00	\N	\N	\N	2018-12-20 15:59:32	\N	Webin-45433	datahub	yes
\.


--
-- Data for Name: selecta_rule_templates; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.selecta_rule_templates (template_id, pipeline_id, template, master_attributes, all_attributes) FROM stdin;
\.


--
-- Name: process_report_process_report_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.process_report_process_report_id_seq', 163, true);


--
-- Name: process_selection_selection_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.process_selection_selection_id_seq', 1, false);


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

