--
-- PostgreSQL database dump
--

-- Dumped from database version 14.20 (Ubuntu 14.20-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 17.5

-- Started on 2026-01-09 10:51:32

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 6 (class 2615 OID 2200)
-- Name: public; Type: SCHEMA; Schema: -; Owner: postgres
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO postgres;

--
-- TOC entry 2 (class 3079 OID 1491963)
-- Name: tablefunc; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS tablefunc WITH SCHEMA public;


--
-- TOC entry 3818 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION tablefunc; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION tablefunc IS 'functions that manipulate whole tables, including crosstab';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 213 (class 1259 OID 1492069)
-- Name: academic_courses_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.academic_courses_details (
    financial_year text,
    title_of_course text,
    course_code text,
    type_of_course text,
    level_of_course text,
    course_offering_department text,
    total_credit_score text,
    institute text,
    as_on_year text,
    id integer NOT NULL
);


ALTER TABLE public.academic_courses_details OWNER TO postgres;

--
-- TOC entry 3819 (class 0 OID 0)
-- Dependencies: 213
-- Name: TABLE academic_courses_details; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.academic_courses_details IS 'This is student details';


--
-- TOC entry 214 (class 1259 OID 1492159)
-- Name: academic_courses_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.academic_courses_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.academic_courses_details_id_seq OWNER TO postgres;

--
-- TOC entry 3820 (class 0 OID 0)
-- Dependencies: 214
-- Name: academic_courses_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.academic_courses_details_id_seq OWNED BY public.academic_courses_details.id;


--
-- TOC entry 215 (class 1259 OID 1492233)
-- Name: actual_student_strength; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.actual_student_strength (
    id integer NOT NULL,
    program text,
    male_students integer,
    female_students integer,
    total_students integer,
    within_state integer,
    outside_state integer,
    outside_country integer,
    economically_backward integer,
    socially_challenged integer,
    reimbursed_by_government integer,
    reimbursed_by_institution integer,
    reimbursed_by_private integer,
    not_reimbursed integer,
    institute text,
    as_on_year text
);


ALTER TABLE public.actual_student_strength OWNER TO postgres;

--
-- TOC entry 216 (class 1259 OID 1492292)
-- Name: actual_student_strength_new_id_seq1; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.actual_student_strength_new_id_seq1
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.actual_student_strength_new_id_seq1 OWNER TO postgres;

--
-- TOC entry 3821 (class 0 OID 0)
-- Dependencies: 216
-- Name: actual_student_strength_new_id_seq1; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.actual_student_strength_new_id_seq1 OWNED BY public.actual_student_strength.id;


--
-- TOC entry 217 (class 1259 OID 1492336)
-- Name: adv_se; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.adv_se (
);


ALTER TABLE public.adv_se OWNER TO postgres;

--
-- TOC entry 322 (class 1259 OID 1613092)
-- Name: advance_search_data; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.advance_search_data (
    id integer NOT NULL,
    title text,
    authors text,
    guide text,
    domain text,
    subdomain text,
    institute text,
    year text,
    url text,
    abstract text,
    type text,
    collaboration text,
    metadata text,
    citation_id text,
    total_citations text,
    recent_citations text,
    fcr text,
    rcr text,
    altmetrics_details text,
    altmetrics_counts text,
    document_type text,
    source text,
    open_access_status text,
    sustainable_development_goal text,
    fwci text,
    citation_percentile text,
    cited_by text,
    related_to text,
    doi text,
    orcid text,
    issn text,
    topic text,
    field text,
    subfield text,
    fetched_from text,
    title_backup text,
    abstract_backup text
);


ALTER TABLE public.advance_search_data OWNER TO postgres;

--
-- TOC entry 219 (class 1259 OID 1492418)
-- Name: advance_search_data_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.advance_search_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.advance_search_data_id_seq OWNER TO postgres;

--
-- TOC entry 3822 (class 0 OID 0)
-- Dependencies: 219
-- Name: advance_search_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.advance_search_data_id_seq OWNED BY public.advance_search_data.id;


--
-- TOC entry 321 (class 1259 OID 1554577)
-- Name: advance_search_data_15_12; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.advance_search_data_15_12 (
    id integer DEFAULT nextval('public.advance_search_data_id_seq'::regclass) NOT NULL,
    title text,
    authors text,
    guide text,
    domain text,
    subdomain text,
    institute text,
    year text,
    url text,
    abstract text,
    type text,
    collaboration text,
    metadata text,
    citation_id text,
    total_citations text,
    recent_citations text,
    fcr text,
    rcr text,
    altmetrics_details text,
    altmetrics_counts text,
    document_type text,
    source text,
    open_access_status text,
    sustainable_development_goal text,
    fwci text,
    citation_percentile text,
    cited_by text,
    related_to text,
    doi text,
    orcid text,
    issn text,
    topic text,
    field text,
    subfield text,
    fetched_from text
);


ALTER TABLE public.advance_search_data_15_12 OWNER TO postgres;

--
-- TOC entry 218 (class 1259 OID 1492368)
-- Name: advance_search_data_old; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.advance_search_data_old (
    id integer DEFAULT nextval('public.advance_search_data_id_seq'::regclass) NOT NULL,
    title text,
    authors text,
    guide text,
    domain text,
    subdomain text,
    institute text,
    year text,
    url text,
    abstract text,
    type text,
    collaboration text,
    metadata text,
    citation_id text,
    total_citations text,
    recent_citations text,
    fcr text,
    rcr text,
    altmetrics_details text,
    altmetrics_counts text,
    document_type text,
    source text,
    open_access_status text,
    sustainable_development_goal text,
    fwci text,
    citation_percentile text,
    cited_by text,
    related_to text,
    doi text,
    orcid text,
    issn text,
    topic text,
    field text,
    subfield text,
    fetched_from text
);


ALTER TABLE public.advance_search_data_old OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 1492490)
-- Name: auth_group; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_group (
    id integer NOT NULL,
    name character varying(150) NOT NULL
);


ALTER TABLE public.auth_group OWNER TO postgres;

--
-- TOC entry 221 (class 1259 OID 1492519)
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_group ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 222 (class 1259 OID 1492530)
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_group_permissions (
    id bigint NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_group_permissions OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 1492558)
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_group_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 224 (class 1259 OID 1492579)
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


ALTER TABLE public.auth_permission OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 1492621)
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_permission ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 226 (class 1259 OID 1492657)
-- Name: auth_user; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_user (
    id integer NOT NULL,
    password character varying(128) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username character varying(150) NOT NULL,
    first_name character varying(150) NOT NULL,
    last_name character varying(150) NOT NULL,
    email character varying(254) NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL
);


ALTER TABLE public.auth_user OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 1492872)
-- Name: auth_user_groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_user_groups (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.auth_user_groups OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 1492968)
-- Name: auth_user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_user_groups ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 229 (class 1259 OID 1492997)
-- Name: auth_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_user ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 230 (class 1259 OID 1493036)
-- Name: auth_user_user_permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_user_user_permissions (
    id bigint NOT NULL,
    user_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_user_user_permissions OWNER TO postgres;

--
-- TOC entry 231 (class 1259 OID 1493111)
-- Name: auth_user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_user_user_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_user_user_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 232 (class 1259 OID 1493120)
-- Name: combined_ipo_patent_data; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.combined_ipo_patent_data (
    id integer NOT NULL,
    oid text,
    application_number text,
    inserted_at timestamp without time zone,
    source_collection text,
    invention_title text,
    publication_number text,
    publication_date text,
    publication_type text,
    application_filing_date text,
    field_of_invention text,
    inventors text,
    applicants text,
    abstract text,
    email_record text,
    additional_email text,
    application_type text,
    examination_request_date text,
    first_examination_report_date text,
    certificate_issue_date text,
    post_grant_journal_date text,
    reply_to_fer_date text,
    status text,
    patent_number text,
    date_of_grant text,
    legal_status text,
    due_date_next_renewal text,
    renewal_history jsonb,
    aishe_code text,
    fetched_at timestamp without time zone,
    granted_patent_title text,
    patent_grant_number text,
    university_name text,
    fetched_from text
);


ALTER TABLE public.combined_ipo_patent_data OWNER TO postgres;

--
-- TOC entry 233 (class 1259 OID 1493163)
-- Name: combined_ipo_patent_data_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.combined_ipo_patent_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.combined_ipo_patent_data_id_seq OWNER TO postgres;

--
-- TOC entry 3823 (class 0 OID 0)
-- Dependencies: 233
-- Name: combined_ipo_patent_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.combined_ipo_patent_data_id_seq OWNED BY public.combined_ipo_patent_data.id;


--
-- TOC entry 234 (class 1259 OID 1493201)
-- Name: combined_ipo_patent_data_old; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.combined_ipo_patent_data_old (
    id integer DEFAULT nextval('public.combined_ipo_patent_data_id_seq'::regclass) NOT NULL,
    oid text,
    application_number text,
    inserted_at timestamp without time zone,
    source_collection text,
    invention_title text,
    publication_number text,
    publication_date text,
    publication_type text,
    application_filing_date text,
    field_of_invention text,
    inventors text,
    applicants text,
    abstract text,
    email_record text,
    additional_email text,
    application_type text,
    examination_request_date text,
    first_examination_report_date text,
    certificate_issue_date text,
    post_grant_journal_date text,
    reply_to_fer_date text,
    status text,
    patent_number text,
    date_of_grant text,
    legal_status text,
    due_date_next_renewal text,
    renewal_history jsonb,
    aishe_code text,
    fetched_at timestamp without time zone,
    granted_patent_title text,
    patent_grant_number text,
    university_name text,
    fetched_from text
);


ALTER TABLE public.combined_ipo_patent_data_old OWNER TO postgres;

--
-- TOC entry 235 (class 1259 OID 1493269)
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id integer NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


ALTER TABLE public.django_admin_log OWNER TO postgres;

--
-- TOC entry 236 (class 1259 OID 1493351)
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_admin_log ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_admin_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 237 (class 1259 OID 1493388)
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


ALTER TABLE public.django_content_type OWNER TO postgres;

--
-- TOC entry 238 (class 1259 OID 1493431)
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_content_type ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_content_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 239 (class 1259 OID 1493449)
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_migrations (
    id bigint NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


ALTER TABLE public.django_migrations OWNER TO postgres;

--
-- TOC entry 240 (class 1259 OID 1493489)
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_migrations ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- TOC entry 241 (class 1259 OID 1493497)
-- Name: django_session; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE public.django_session OWNER TO postgres;

--
-- TOC entry 242 (class 1259 OID 1493558)
-- Name: expertise; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.expertise (
    id integer NOT NULL,
    name character varying,
    designation character varying,
    email character varying,
    phone character varying,
    phd character varying,
    research character varying,
    image character varying,
    department character varying,
    institute character varying
);


ALTER TABLE public.expertise OWNER TO postgres;

--
-- TOC entry 243 (class 1259 OID 1493604)
-- Name: expertise_16_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.expertise_16_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.expertise_16_id_seq OWNER TO postgres;

--
-- TOC entry 3824 (class 0 OID 0)
-- Dependencies: 243
-- Name: expertise_16_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.expertise_16_id_seq OWNED BY public.expertise.id;


--
-- TOC entry 244 (class 1259 OID 1493656)
-- Name: faculty_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.faculty_details (
    num_faculties integer,
    institute text,
    as_on_year text,
    id integer NOT NULL
);


ALTER TABLE public.faculty_details OWNER TO postgres;

--
-- TOC entry 245 (class 1259 OID 1493737)
-- Name: faculty_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.faculty_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.faculty_details_id_seq OWNER TO postgres;

--
-- TOC entry 3825 (class 0 OID 0)
-- Dependencies: 245
-- Name: faculty_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.faculty_details_id_seq OWNED BY public.faculty_details.id;


--
-- TOC entry 246 (class 1259 OID 1493875)
-- Name: faculty_strength; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.faculty_strength (
    id integer NOT NULL,
    institute character varying(100),
    academic_year character varying(10),
    as_on character varying(20),
    male_strength character varying(100),
    female_strength character varying(100),
    total_strength character varying(100),
    total_sanctioned_strength character varying(100),
    uploaded_on character varying(100),
    url character varying(100),
    types character varying(100)
);


ALTER TABLE public.faculty_strength OWNER TO postgres;

--
-- TOC entry 247 (class 1259 OID 1493961)
-- Name: faculty_strength_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.faculty_strength_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.faculty_strength_id_seq OWNER TO postgres;

--
-- TOC entry 3826 (class 0 OID 0)
-- Dependencies: 247
-- Name: faculty_strength_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.faculty_strength_id_seq OWNED BY public.faculty_strength.id;


--
-- TOC entry 248 (class 1259 OID 1494004)
-- Name: fdi_investment; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fdi_investment (
    startup_name text,
    investment_received bigint,
    year_of_receiving text,
    institute text,
    as_on_year text,
    id integer NOT NULL
);


ALTER TABLE public.fdi_investment OWNER TO postgres;

--
-- TOC entry 249 (class 1259 OID 1494036)
-- Name: fdi_investment_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fdi_investment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fdi_investment_id_seq OWNER TO postgres;

--
-- TOC entry 3827 (class 0 OID 0)
-- Dependencies: 249
-- Name: fdi_investment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fdi_investment_id_seq OWNED BY public.fdi_investment.id;


--
-- TOC entry 250 (class 1259 OID 1494055)
-- Name: fdp_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.fdp_details (
    financial_year text,
    title_of_course text,
    fdp_sponsered text,
    certificate_offering_department text,
    program_start_date text,
    program_end_date text,
    institute text,
    as_on_year text,
    id integer NOT NULL
);


ALTER TABLE public.fdp_details OWNER TO postgres;

--
-- TOC entry 251 (class 1259 OID 1494106)
-- Name: fdp_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.fdp_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.fdp_details_id_seq OWNER TO postgres;

--
-- TOC entry 3828 (class 0 OID 0)
-- Dependencies: 251
-- Name: fdp_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.fdp_details_id_seq OWNED BY public.fdp_details.id;


--
-- TOC entry 252 (class 1259 OID 1494136)
-- Name: financial_expenses_capital; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.financial_expenses_capital (
    id integer NOT NULL,
    financial_year text,
    library bigint,
    equipment bigint,
    workshops bigint,
    capital_assets bigint,
    institute text,
    as_on_year text
);


ALTER TABLE public.financial_expenses_capital OWNER TO postgres;

--
-- TOC entry 253 (class 1259 OID 1494193)
-- Name: financial_expenses_capital_new_id_seq1; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.financial_expenses_capital_new_id_seq1
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.financial_expenses_capital_new_id_seq1 OWNER TO postgres;

--
-- TOC entry 3829 (class 0 OID 0)
-- Dependencies: 253
-- Name: financial_expenses_capital_new_id_seq1; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.financial_expenses_capital_new_id_seq1 OWNED BY public.financial_expenses_capital.id;


--
-- TOC entry 254 (class 1259 OID 1494281)
-- Name: financial_expenses_operational; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.financial_expenses_operational (
    id integer NOT NULL,
    financial_year text,
    salaries bigint,
    maintenance bigint,
    seminars bigint,
    institute text,
    as_on_year text
);


ALTER TABLE public.financial_expenses_operational OWNER TO postgres;

--
-- TOC entry 255 (class 1259 OID 1494382)
-- Name: financial_expenses_operational_new_id_seq1; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.financial_expenses_operational_new_id_seq1
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.financial_expenses_operational_new_id_seq1 OWNER TO postgres;

--
-- TOC entry 3830 (class 0 OID 0)
-- Dependencies: 255
-- Name: financial_expenses_operational_new_id_seq1; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.financial_expenses_operational_new_id_seq1 OWNED BY public.financial_expenses_operational.id;


--
-- TOC entry 256 (class 1259 OID 1494476)
-- Name: founders_of_fortune_500_companies; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.founders_of_fortune_500_companies (
    name_of_alumni text,
    program_passed_from text,
    year_of_passing text,
    comapny_name text,
    year_of_appearence text,
    institute text,
    as_on_year text,
    id integer NOT NULL
);


ALTER TABLE public.founders_of_fortune_500_companies OWNER TO postgres;

--
-- TOC entry 257 (class 1259 OID 1494500)
-- Name: founders_of_fortune_500_companies_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.founders_of_fortune_500_companies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.founders_of_fortune_500_companies_id_seq OWNER TO postgres;

--
-- TOC entry 3831 (class 0 OID 0)
-- Dependencies: 257
-- Name: founders_of_fortune_500_companies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.founders_of_fortune_500_companies_id_seq OWNED BY public.founders_of_fortune_500_companies.id;


--
-- TOC entry 258 (class 1259 OID 1494510)
-- Name: incubation_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.incubation_details (
    financial_year text,
    no_of_pre_incubation_units integer,
    expenditure_on_pre_incubation_activities bigint,
    income_generated_pre_incubation bigint,
    no_of_incubation_units integer,
    expenditure_on_incubation_activities bigint,
    income_generated_incubation bigint,
    institute text,
    as_on_year text,
    id integer NOT NULL
);


ALTER TABLE public.incubation_details OWNER TO postgres;

--
-- TOC entry 259 (class 1259 OID 1494540)
-- Name: incubation_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.incubation_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.incubation_details_id_seq OWNER TO postgres;

--
-- TOC entry 3832 (class 0 OID 0)
-- Dependencies: 259
-- Name: incubation_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.incubation_details_id_seq OWNED BY public.incubation_details.id;


--
-- TOC entry 260 (class 1259 OID 1494624)
-- Name: innovation_grant_from_govt; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.innovation_grant_from_govt (
    gov_organisation_name text,
    grant_received bigint,
    year_of_receiving text,
    institute text,
    as_on_year text,
    id integer NOT NULL
);


ALTER TABLE public.innovation_grant_from_govt OWNER TO postgres;

--
-- TOC entry 261 (class 1259 OID 1494755)
-- Name: innovation_grant_from_govt_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.innovation_grant_from_govt_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.innovation_grant_from_govt_id_seq OWNER TO postgres;

--
-- TOC entry 3833 (class 0 OID 0)
-- Dependencies: 261
-- Name: innovation_grant_from_govt_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.innovation_grant_from_govt_id_seq OWNED BY public.innovation_grant_from_govt.id;


--
-- TOC entry 262 (class 1259 OID 1494790)
-- Name: innovations_at_various_stages_of_technology_readiness_level; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.innovations_at_various_stages_of_technology_readiness_level (
    innovation_name text,
    stage_of_technology text,
    financial_year text,
    institute text,
    as_on_year text,
    id integer NOT NULL
);


ALTER TABLE public.innovations_at_various_stages_of_technology_readiness_level OWNER TO postgres;

--
-- TOC entry 263 (class 1259 OID 1494846)
-- Name: innovations_at_various_stages_of_technology_readiness_l_id_seq1; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.innovations_at_various_stages_of_technology_readiness_l_id_seq1
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.innovations_at_various_stages_of_technology_readiness_l_id_seq1 OWNER TO postgres;

--
-- TOC entry 3834 (class 0 OID 0)
-- Dependencies: 263
-- Name: innovations_at_various_stages_of_technology_readiness_l_id_seq1; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.innovations_at_various_stages_of_technology_readiness_l_id_seq1 OWNED BY public.innovations_at_various_stages_of_technology_readiness_level.id;


--
-- TOC entry 264 (class 1259 OID 1494862)
-- Name: ipo_patent_details_flat; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ipo_patent_details_flat (
    id integer NOT NULL,
    oid text,
    application_number text,
    inserted_at timestamp without time zone,
    source_collection text,
    invention_title text,
    publication_number text,
    publication_date text,
    publication_type text,
    application_filing_date text,
    field_of_invention text,
    inventors text,
    applicants text,
    abstract text,
    email_record text,
    additional_email text,
    application_type text,
    examination_request_date text,
    first_examination_report_date text,
    certificate_issue_date text,
    post_grant_journal_date text,
    reply_to_fer_date text,
    status text,
    patent_number text,
    date_of_grant text,
    legal_status text,
    due_date_next_renewal text,
    renewal_history jsonb
);


ALTER TABLE public.ipo_patent_details_flat OWNER TO postgres;

--
-- TOC entry 265 (class 1259 OID 1494867)
-- Name: ipo_patent_details_flat_old; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.ipo_patent_details_flat_old (
    id integer NOT NULL,
    oid text,
    application_number text,
    inserted_at timestamp without time zone,
    source_collection text,
    invention_title text,
    publication_number text,
    publication_date text,
    publication_type text,
    application_filing_date text,
    field_of_invention text,
    inventors text,
    applicants text,
    abstract text,
    email_record text,
    additional_email text,
    application_type text,
    examination_request_date text,
    first_examination_report_date text,
    certificate_issue_date text,
    post_grant_journal_date text,
    reply_to_fer_date text,
    status text,
    patent_number text,
    date_of_grant text,
    legal_status text,
    due_date_next_renewal text,
    renewal_history jsonb
);


ALTER TABLE public.ipo_patent_details_flat_old OWNER TO postgres;

--
-- TOC entry 266 (class 1259 OID 1494872)
-- Name: ipo_patent_details_flat_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ipo_patent_details_flat_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ipo_patent_details_flat_id_seq OWNER TO postgres;

--
-- TOC entry 3835 (class 0 OID 0)
-- Dependencies: 266
-- Name: ipo_patent_details_flat_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ipo_patent_details_flat_id_seq OWNED BY public.ipo_patent_details_flat_old.id;


--
-- TOC entry 267 (class 1259 OID 1494873)
-- Name: ipo_patent_details_flat_id_seq1; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.ipo_patent_details_flat_id_seq1
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.ipo_patent_details_flat_id_seq1 OWNER TO postgres;

--
-- TOC entry 3836 (class 0 OID 0)
-- Dependencies: 267
-- Name: ipo_patent_details_flat_id_seq1; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.ipo_patent_details_flat_id_seq1 OWNED BY public.ipo_patent_details_flat.id;


--
-- TOC entry 268 (class 1259 OID 1495023)
-- Name: master_expertise; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.master_expertise (
    id integer NOT NULL,
    institute character varying,
    department character varying
);


ALTER TABLE public.master_expertise OWNER TO postgres;

--
-- TOC entry 269 (class 1259 OID 1495088)
-- Name: master_expertise_id_seq2; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.master_expertise_id_seq2
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.master_expertise_id_seq2 OWNER TO postgres;

--
-- TOC entry 3837 (class 0 OID 0)
-- Dependencies: 269
-- Name: master_expertise_id_seq2; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.master_expertise_id_seq2 OWNED BY public.master_expertise.id;


--
-- TOC entry 270 (class 1259 OID 1495125)
-- Name: nirf_extracted_table; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.nirf_extracted_table (
    id integer NOT NULL,
    pdf_record_id integer NOT NULL,
    title character varying(255) NOT NULL,
    header jsonb,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.nirf_extracted_table OWNER TO postgres;

--
-- TOC entry 271 (class 1259 OID 1495163)
-- Name: nirf_extracted_table_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.nirf_extracted_table_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.nirf_extracted_table_id_seq OWNER TO postgres;

--
-- TOC entry 3838 (class 0 OID 0)
-- Dependencies: 271
-- Name: nirf_extracted_table_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.nirf_extracted_table_id_seq OWNED BY public.nirf_extracted_table.id;


--
-- TOC entry 272 (class 1259 OID 1495232)
-- Name: nirf_pdf_record; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.nirf_pdf_record (
    id integer NOT NULL,
    institute character varying(255) NOT NULL,
    year character varying(10) NOT NULL,
    uploaded_by character varying(255),
    uploaded_at timestamp with time zone DEFAULT now(),
    pdf_name character varying(255)
);


ALTER TABLE public.nirf_pdf_record OWNER TO postgres;

--
-- TOC entry 273 (class 1259 OID 1495318)
-- Name: nirf_pdf_record_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.nirf_pdf_record_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.nirf_pdf_record_id_seq OWNER TO postgres;

--
-- TOC entry 3839 (class 0 OID 0)
-- Dependencies: 273
-- Name: nirf_pdf_record_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.nirf_pdf_record_id_seq OWNED BY public.nirf_pdf_record.id;


--
-- TOC entry 274 (class 1259 OID 1495375)
-- Name: nirf_table_row; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.nirf_table_row (
    id integer NOT NULL,
    table_id integer NOT NULL,
    data jsonb NOT NULL
);


ALTER TABLE public.nirf_table_row OWNER TO postgres;

--
-- TOC entry 275 (class 1259 OID 1495409)
-- Name: nirf_table_row_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.nirf_table_row_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.nirf_table_row_id_seq OWNER TO postgres;

--
-- TOC entry 3840 (class 0 OID 0)
-- Dependencies: 275
-- Name: nirf_table_row_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.nirf_table_row_id_seq OWNED BY public.nirf_table_row.id;


--
-- TOC entry 276 (class 1259 OID 1495464)
-- Name: package_data; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.package_data (
    id integer NOT NULL,
    name character varying,
    package character varying,
    status character varying
);


ALTER TABLE public.package_data OWNER TO postgres;

--
-- TOC entry 277 (class 1259 OID 1495524)
-- Name: package_data_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.package_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.package_data_id_seq OWNER TO postgres;

--
-- TOC entry 3841 (class 0 OID 0)
-- Dependencies: 277
-- Name: package_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.package_data_id_seq OWNED BY public.package_data.id;


--
-- TOC entry 278 (class 1259 OID 1495569)
-- Name: patents_details; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.patents_details (
    financial_year text,
    patents_published integer,
    patents_granted integer,
    patents_commercialized integer,
    institute text,
    as_on_year text,
    id integer NOT NULL
);


ALTER TABLE public.patents_details OWNER TO postgres;

--
-- TOC entry 279 (class 1259 OID 1495710)
-- Name: patents_details_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.patents_details_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.patents_details_id_seq OWNER TO postgres;

--
-- TOC entry 3842 (class 0 OID 0)
-- Dependencies: 279
-- Name: patents_details_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.patents_details_id_seq OWNED BY public.patents_details.id;


--
-- TOC entry 280 (class 1259 OID 1495884)
-- Name: phd_students; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.phd_students (
    id integer NOT NULL,
    financial_year text,
    program_type text,
    total integer,
    graduate integer,
    institute text,
    as_on_year text
);


ALTER TABLE public.phd_students OWNER TO postgres;

--
-- TOC entry 281 (class 1259 OID 1496027)
-- Name: phd_students_new_id_seq1; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.phd_students_new_id_seq1
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.phd_students_new_id_seq1 OWNER TO postgres;

--
-- TOC entry 3843 (class 0 OID 0)
-- Dependencies: 281
-- Name: phd_students_new_id_seq1; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.phd_students_new_id_seq1 OWNED BY public.phd_students.id;


--
-- TOC entry 282 (class 1259 OID 1496167)
-- Name: placements_and_higher_studies; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.placements_and_higher_studies (
    id integer NOT NULL,
    program text,
    year_of_intake text,
    students_intaken integer,
    students_admitted integer,
    year_of_lateral_entry text,
    students_admitted_lateral_entry integer,
    year_of_graduation text,
    graduated_students integer,
    placed_students integer,
    median_salary_per_annum bigint,
    higher_studies_students integer,
    institute text,
    as_on_year text
);


ALTER TABLE public.placements_and_higher_studies OWNER TO postgres;

--
-- TOC entry 283 (class 1259 OID 1496248)
-- Name: placements_and_higher_studies_new_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.placements_and_higher_studies_new_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.placements_and_higher_studies_new_id_seq OWNER TO postgres;

--
-- TOC entry 3844 (class 0 OID 0)
-- Dependencies: 283
-- Name: placements_and_higher_studies_new_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.placements_and_higher_studies_new_id_seq OWNED BY public.placements_and_higher_studies.id;


--
-- TOC entry 284 (class 1259 OID 1496370)
-- Name: research_consultancy_details_consultancy; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.research_consultancy_details_consultancy (
    id integer NOT NULL,
    financial_year text,
    consultancy_projects integer,
    client_organisations integer,
    amount_recieved_consultancy_projects bigint,
    institute text,
    as_on_year text
);


ALTER TABLE public.research_consultancy_details_consultancy OWNER TO postgres;

--
-- TOC entry 285 (class 1259 OID 1496507)
-- Name: research_consultancy_details_consultancy_new_id_seq1; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.research_consultancy_details_consultancy_new_id_seq1
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.research_consultancy_details_consultancy_new_id_seq1 OWNER TO postgres;

--
-- TOC entry 3845 (class 0 OID 0)
-- Dependencies: 285
-- Name: research_consultancy_details_consultancy_new_id_seq1; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.research_consultancy_details_consultancy_new_id_seq1 OWNED BY public.research_consultancy_details_consultancy.id;


--
-- TOC entry 286 (class 1259 OID 1496667)
-- Name: research_consultancy_details_sponsered; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.research_consultancy_details_sponsered (
    id integer NOT NULL,
    financial_year text,
    sponsered_projects integer,
    funding_agencies integer,
    amount_recieved_sponsered_research bigint,
    institute text,
    as_on_year text
);


ALTER TABLE public.research_consultancy_details_sponsered OWNER TO postgres;

--
-- TOC entry 287 (class 1259 OID 1496795)
-- Name: research_consultancy_details_sponsered_new_id_seq1; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.research_consultancy_details_sponsered_new_id_seq1
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.research_consultancy_details_sponsered_new_id_seq1 OWNER TO postgres;

--
-- TOC entry 3846 (class 0 OID 0)
-- Dependencies: 287
-- Name: research_consultancy_details_sponsered_new_id_seq1; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.research_consultancy_details_sponsered_new_id_seq1 OWNED BY public.research_consultancy_details_sponsered.id;


--
-- TOC entry 288 (class 1259 OID 1496842)
-- Name: role_data; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.role_data (
    id integer NOT NULL,
    name character varying,
    status character varying
);


ALTER TABLE public.role_data OWNER TO postgres;

--
-- TOC entry 289 (class 1259 OID 1496890)
-- Name: role_data_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.role_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.role_data_id_seq OWNER TO postgres;

--
-- TOC entry 3847 (class 0 OID 0)
-- Dependencies: 289
-- Name: role_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.role_data_id_seq OWNED BY public.role_data.id;


--
-- TOC entry 290 (class 1259 OID 1496970)
-- Name: sanctioned_intake; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.sanctioned_intake (
    id integer NOT NULL,
    program text,
    financial_year text,
    seats integer,
    institute text,
    as_on_year text
);


ALTER TABLE public.sanctioned_intake OWNER TO postgres;

--
-- TOC entry 291 (class 1259 OID 1497041)
-- Name: sanctioned_intake_new_id_seq1; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.sanctioned_intake_new_id_seq1
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sanctioned_intake_new_id_seq1 OWNER TO postgres;

--
-- TOC entry 3848 (class 0 OID 0)
-- Dependencies: 291
-- Name: sanctioned_intake_new_id_seq1; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.sanctioned_intake_new_id_seq1 OWNED BY public.sanctioned_intake.id;


--
-- TOC entry 292 (class 1259 OID 1497095)
-- Name: scraped_data; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.scraped_data (
    id integer NOT NULL,
    title text,
    authors text,
    guide text,
    domain text,
    subdomain text,
    institute text,
    year text,
    url text,
    abstract text,
    type text,
    collaboration text,
    metadata text,
    citation_id text,
    total_citations text,
    recent_citations text,
    fcr text,
    rcr text,
    altmetrics_details text,
    altmetrics_counts text,
    document_type text,
    source text,
    open_access_status text,
    sustainable_development_goal text,
    fwci text,
    citation_percentile text,
    cited_by text,
    related_to text,
    doi text,
    orcid text,
    issn text,
    topic text,
    field text,
    subfield text,
    fetched_from text,
    upload_date date
);


ALTER TABLE public.scraped_data OWNER TO postgres;

--
-- TOC entry 293 (class 1259 OID 1497169)
-- Name: scraped_data_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.scraped_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.scraped_data_id_seq OWNER TO postgres;

--
-- TOC entry 3849 (class 0 OID 0)
-- Dependencies: 293
-- Name: scraped_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.scraped_data_id_seq OWNED BY public.scraped_data.id;


--
-- TOC entry 294 (class 1259 OID 1497281)
-- Name: scraped_data_save; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.scraped_data_save (
    id integer NOT NULL,
    title text,
    authors text,
    guide text,
    domain text,
    subdomain text,
    institute text,
    year text,
    url text,
    abstract text,
    type text,
    collaboration text,
    metadata text,
    citation_id text,
    total_citations text,
    recent_citations text,
    fcr text,
    rcr text,
    altmetrics_details text,
    altmetrics_counts text,
    document_type text,
    source text,
    open_access_status text,
    sustainable_development_goal text,
    fwci text,
    citation_percentile text,
    cited_by text,
    related_to text,
    doi text,
    orcid text,
    issn text,
    topic text,
    field text,
    subfield text,
    fetched_from text,
    upload_date date
);


ALTER TABLE public.scraped_data_save OWNER TO postgres;

--
-- TOC entry 295 (class 1259 OID 1497391)
-- Name: scraped_data_save_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.scraped_data_save_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.scraped_data_save_id_seq OWNER TO postgres;

--
-- TOC entry 3850 (class 0 OID 0)
-- Dependencies: 295
-- Name: scraped_data_save_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.scraped_data_save_id_seq OWNED BY public.scraped_data_save.id;


--
-- TOC entry 296 (class 1259 OID 1497478)
-- Name: scraped_raw_data; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.scraped_raw_data (
    id integer NOT NULL,
    title text,
    authors text,
    guide text,
    domain text,
    subdomain text,
    institute text,
    year text,
    url text,
    abstract text,
    type text,
    collaboration text,
    metadata text,
    citation_id text,
    total_citations text,
    recent_citations text,
    fcr text,
    rcr text,
    altmetrics_details text,
    altmetrics_counts text,
    document_type text,
    source text,
    open_access_status text,
    sustainable_development_goal text,
    fwci text,
    citation_percentile text,
    cited_by text,
    related_to text,
    doi text,
    orcid text,
    issn text,
    topic text,
    field text,
    subfield text,
    fetched_from text,
    upload_date date
);


ALTER TABLE public.scraped_raw_data OWNER TO postgres;

--
-- TOC entry 297 (class 1259 OID 1497758)
-- Name: scraped_raw_data_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.scraped_raw_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.scraped_raw_data_id_seq OWNER TO postgres;

--
-- TOC entry 3851 (class 0 OID 0)
-- Dependencies: 297
-- Name: scraped_raw_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.scraped_raw_data_id_seq OWNED BY public.scraped_raw_data.id;


--
-- TOC entry 298 (class 1259 OID 1497967)
-- Name: seed_funding; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.seed_funding (
    id integer NOT NULL,
    startup_name character varying(255),
    dpiit_no character varying(100),
    seed_funding_received bigint,
    govt_org character varying(255),
    year_of_receiving_fund character varying(10),
    achievement_level character varying(255),
    type_of_investment character varying(255),
    institute character varying(255),
    as_on_year character varying(10)
);


ALTER TABLE public.seed_funding OWNER TO postgres;

--
-- TOC entry 299 (class 1259 OID 1498068)
-- Name: seed_funding_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.seed_funding_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.seed_funding_id_seq OWNER TO postgres;

--
-- TOC entry 3852 (class 0 OID 0)
-- Dependencies: 299
-- Name: seed_funding_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.seed_funding_id_seq OWNED BY public.seed_funding.id;


--
-- TOC entry 300 (class 1259 OID 1498197)
-- Name: startup_receiving_vc_investment; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.startup_receiving_vc_investment (
    startup_name text,
    amount_received bigint,
    organisation_name text,
    year_of_receiving text,
    institute text,
    as_on_year text,
    id integer NOT NULL
);


ALTER TABLE public.startup_receiving_vc_investment OWNER TO postgres;

--
-- TOC entry 301 (class 1259 OID 1498316)
-- Name: startup_receiving_vc_investment_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.startup_receiving_vc_investment_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.startup_receiving_vc_investment_id_seq OWNER TO postgres;

--
-- TOC entry 3853 (class 0 OID 0)
-- Dependencies: 301
-- Name: startup_receiving_vc_investment_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.startup_receiving_vc_investment_id_seq OWNED BY public.startup_receiving_vc_investment.id;


--
-- TOC entry 302 (class 1259 OID 1498456)
-- Name: startup_recognition_old; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.startup_recognition_old (
    startup_name text,
    year_of_recognition text,
    registration_no text,
    institute text,
    as_on_year text,
    id integer NOT NULL
);


ALTER TABLE public.startup_recognition_old OWNER TO postgres;

--
-- TOC entry 303 (class 1259 OID 1498516)
-- Name: startup_recognition_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.startup_recognition_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.startup_recognition_id_seq OWNER TO postgres;

--
-- TOC entry 3854 (class 0 OID 0)
-- Dependencies: 303
-- Name: startup_recognition_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.startup_recognition_id_seq OWNED BY public.startup_recognition_old.id;


--
-- TOC entry 304 (class 1259 OID 1498731)
-- Name: startup_recognition; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.startup_recognition (
    startup_name text,
    year_of_recognition text,
    registration_no text,
    institute text,
    as_on_year text,
    id integer DEFAULT nextval('public.startup_recognition_id_seq'::regclass) NOT NULL
);


ALTER TABLE public.startup_recognition OWNER TO postgres;

--
-- TOC entry 305 (class 1259 OID 1498941)
-- Name: startups_turnover_50_lacs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.startups_turnover_50_lacs (
    startup_name text,
    company_turnover bigint,
    financial_year text,
    institute text,
    as_on_year text,
    id integer NOT NULL
);


ALTER TABLE public.startups_turnover_50_lacs OWNER TO postgres;

--
-- TOC entry 306 (class 1259 OID 1498993)
-- Name: startups_turnover_50_lacs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.startups_turnover_50_lacs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.startups_turnover_50_lacs_id_seq OWNER TO postgres;

--
-- TOC entry 3855 (class 0 OID 0)
-- Dependencies: 306
-- Name: startups_turnover_50_lacs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.startups_turnover_50_lacs_id_seq OWNED BY public.startups_turnover_50_lacs.id;


--
-- TOC entry 307 (class 1259 OID 1499035)
-- Name: tb_academic_year_mstr; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tb_academic_year_mstr (
    id integer NOT NULL,
    year integer,
    academic_year character varying
);


ALTER TABLE public.tb_academic_year_mstr OWNER TO postgres;

--
-- TOC entry 308 (class 1259 OID 1499089)
-- Name: tb_academic_year_mstr_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tb_academic_year_mstr_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tb_academic_year_mstr_id_seq OWNER TO postgres;

--
-- TOC entry 3856 (class 0 OID 0)
-- Dependencies: 308
-- Name: tb_academic_year_mstr_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tb_academic_year_mstr_id_seq OWNED BY public.tb_academic_year_mstr.id;


--
-- TOC entry 309 (class 1259 OID 1499105)
-- Name: tb_course_program_types; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tb_course_program_types (
    id integer NOT NULL,
    program_name character varying
);


ALTER TABLE public.tb_course_program_types OWNER TO postgres;

--
-- TOC entry 310 (class 1259 OID 1499212)
-- Name: tb_course_program_types_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tb_course_program_types_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tb_course_program_types_id_seq OWNER TO postgres;

--
-- TOC entry 3857 (class 0 OID 0)
-- Dependencies: 310
-- Name: tb_course_program_types_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tb_course_program_types_id_seq OWNED BY public.tb_course_program_types.id;


--
-- TOC entry 311 (class 1259 OID 1499349)
-- Name: tb_goi_ministries_mstr; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tb_goi_ministries_mstr (
    id integer NOT NULL,
    name character varying,
    short_name character varying,
    address character varying,
    phone_no character varying,
    email character varying,
    website character varying
);


ALTER TABLE public.tb_goi_ministries_mstr OWNER TO postgres;

--
-- TOC entry 312 (class 1259 OID 1499485)
-- Name: tb_goi_ministries_mstr_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tb_goi_ministries_mstr_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tb_goi_ministries_mstr_id_seq OWNER TO postgres;

--
-- TOC entry 3858 (class 0 OID 0)
-- Dependencies: 312
-- Name: tb_goi_ministries_mstr_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tb_goi_ministries_mstr_id_seq OWNED BY public.tb_goi_ministries_mstr.id;


--
-- TOC entry 313 (class 1259 OID 1499556)
-- Name: tb_institute_mstr; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tb_institute_mstr (
    id integer NOT NULL,
    institute_name character varying,
    short_name character varying,
    institute_type character varying,
    city character varying,
    state character varying,
    address character varying,
    established_year integer,
    website_url character varying
);


ALTER TABLE public.tb_institute_mstr OWNER TO postgres;

--
-- TOC entry 314 (class 1259 OID 1499620)
-- Name: tb_institute_mstr_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tb_institute_mstr_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tb_institute_mstr_id_seq OWNER TO postgres;

--
-- TOC entry 3859 (class 0 OID 0)
-- Dependencies: 314
-- Name: tb_institute_mstr_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tb_institute_mstr_id_seq OWNED BY public.tb_institute_mstr.id;


--
-- TOC entry 315 (class 1259 OID 1499652)
-- Name: tb_institute_scrap_data_url; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.tb_institute_scrap_data_url (
    id integer NOT NULL,
    institute_name character varying(255),
    short_name character varying(100),
    institute_type character varying(100),
    city character varying(100),
    state character varying(100),
    established_year integer,
    address text,
    website_url text,
    scrap_data_url text
);


ALTER TABLE public.tb_institute_scrap_data_url OWNER TO postgres;

--
-- TOC entry 316 (class 1259 OID 1499700)
-- Name: tb_institute_scrap_data_url_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.tb_institute_scrap_data_url_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.tb_institute_scrap_data_url_id_seq OWNER TO postgres;

--
-- TOC entry 3860 (class 0 OID 0)
-- Dependencies: 316
-- Name: tb_institute_scrap_data_url_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.tb_institute_scrap_data_url_id_seq OWNED BY public.tb_institute_scrap_data_url.id;


--
-- TOC entry 317 (class 1259 OID 1499736)
-- Name: user_registration; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_registration (
    id integer NOT NULL,
    username character varying(50),
    email character varying(254),
    password character varying(128),
    confirm_password character varying(128),
    phone_number character varying(15),
    role character varying(20),
    is_approved boolean DEFAULT false NOT NULL,
    user_info character varying,
    status character varying,
    deleted_by character varying,
    is_email_verified boolean,
    email_otp character varying,
    is_otp_verified boolean,
    first_password character varying,
    first_login boolean,
    email_status character varying
);


ALTER TABLE public.user_registration OWNER TO postgres;

--
-- TOC entry 318 (class 1259 OID 1499818)
-- Name: user_registration_old; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_registration_old (
    id integer NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(254) NOT NULL,
    password character varying(128) NOT NULL,
    confirm_password character varying(128),
    phone_number character varying(15),
    role character varying(20) NOT NULL,
    is_approved boolean DEFAULT false NOT NULL,
    user_info character varying,
    CONSTRAINT user_registration_role_check CHECK (((role)::text = ANY (ARRAY[('GOI_ministries'::character varying)::text, ('CFTIs_users'::character varying)::text, ('Industry'::character varying)::text, ('CRC_repa'::character varying)::text, ('Researchers'::character varying)::text])))
);


ALTER TABLE public.user_registration_old OWNER TO postgres;

--
-- TOC entry 319 (class 1259 OID 1499854)
-- Name: user_registration_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_registration_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_registration_id_seq OWNER TO postgres;

--
-- TOC entry 3861 (class 0 OID 0)
-- Dependencies: 319
-- Name: user_registration_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_registration_id_seq OWNED BY public.user_registration_old.id;


--
-- TOC entry 320 (class 1259 OID 1499898)
-- Name: user_registration_id_seq1; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_registration_id_seq1
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_registration_id_seq1 OWNER TO postgres;

--
-- TOC entry 3862 (class 0 OID 0)
-- Dependencies: 320
-- Name: user_registration_id_seq1; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_registration_id_seq1 OWNED BY public.user_registration.id;


--
-- TOC entry 3474 (class 2604 OID 1499949)
-- Name: academic_courses_details id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.academic_courses_details ALTER COLUMN id SET DEFAULT nextval('public.academic_courses_details_id_seq'::regclass);


--
-- TOC entry 3475 (class 2604 OID 1499969)
-- Name: actual_student_strength id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.actual_student_strength ALTER COLUMN id SET DEFAULT nextval('public.actual_student_strength_new_id_seq1'::regclass);


--
-- TOC entry 3524 (class 2604 OID 1613097)
-- Name: advance_search_data id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.advance_search_data ALTER COLUMN id SET DEFAULT nextval('public.advance_search_data_id_seq'::regclass);


--
-- TOC entry 3477 (class 2604 OID 1500002)
-- Name: combined_ipo_patent_data id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.combined_ipo_patent_data ALTER COLUMN id SET DEFAULT nextval('public.combined_ipo_patent_data_id_seq'::regclass);


--
-- TOC entry 3479 (class 2604 OID 1500164)
-- Name: expertise id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expertise ALTER COLUMN id SET DEFAULT nextval('public.expertise_16_id_seq'::regclass);


--
-- TOC entry 3480 (class 2604 OID 1500213)
-- Name: faculty_details id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.faculty_details ALTER COLUMN id SET DEFAULT nextval('public.faculty_details_id_seq'::regclass);


--
-- TOC entry 3481 (class 2604 OID 1500262)
-- Name: faculty_strength id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.faculty_strength ALTER COLUMN id SET DEFAULT nextval('public.faculty_strength_id_seq'::regclass);


--
-- TOC entry 3482 (class 2604 OID 1500277)
-- Name: fdi_investment id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fdi_investment ALTER COLUMN id SET DEFAULT nextval('public.fdi_investment_id_seq'::regclass);


--
-- TOC entry 3483 (class 2604 OID 1500298)
-- Name: fdp_details id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fdp_details ALTER COLUMN id SET DEFAULT nextval('public.fdp_details_id_seq'::regclass);


--
-- TOC entry 3484 (class 2604 OID 1500311)
-- Name: financial_expenses_capital id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.financial_expenses_capital ALTER COLUMN id SET DEFAULT nextval('public.financial_expenses_capital_new_id_seq1'::regclass);


--
-- TOC entry 3485 (class 2604 OID 1500336)
-- Name: financial_expenses_operational id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.financial_expenses_operational ALTER COLUMN id SET DEFAULT nextval('public.financial_expenses_operational_new_id_seq1'::regclass);


--
-- TOC entry 3486 (class 2604 OID 1500357)
-- Name: founders_of_fortune_500_companies id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.founders_of_fortune_500_companies ALTER COLUMN id SET DEFAULT nextval('public.founders_of_fortune_500_companies_id_seq'::regclass);


--
-- TOC entry 3487 (class 2604 OID 1500370)
-- Name: incubation_details id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.incubation_details ALTER COLUMN id SET DEFAULT nextval('public.incubation_details_id_seq'::regclass);


--
-- TOC entry 3488 (class 2604 OID 1500383)
-- Name: innovation_grant_from_govt id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.innovation_grant_from_govt ALTER COLUMN id SET DEFAULT nextval('public.innovation_grant_from_govt_id_seq'::regclass);


--
-- TOC entry 3489 (class 2604 OID 1500396)
-- Name: innovations_at_various_stages_of_technology_readiness_level id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.innovations_at_various_stages_of_technology_readiness_level ALTER COLUMN id SET DEFAULT nextval('public.innovations_at_various_stages_of_technology_readiness_l_id_seq1'::regclass);


--
-- TOC entry 3490 (class 2604 OID 1500408)
-- Name: ipo_patent_details_flat id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ipo_patent_details_flat ALTER COLUMN id SET DEFAULT nextval('public.ipo_patent_details_flat_id_seq1'::regclass);


--
-- TOC entry 3491 (class 2604 OID 1500415)
-- Name: ipo_patent_details_flat_old id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ipo_patent_details_flat_old ALTER COLUMN id SET DEFAULT nextval('public.ipo_patent_details_flat_id_seq'::regclass);


--
-- TOC entry 3492 (class 2604 OID 1500427)
-- Name: master_expertise id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.master_expertise ALTER COLUMN id SET DEFAULT nextval('public.master_expertise_id_seq2'::regclass);


--
-- TOC entry 3493 (class 2604 OID 1500438)
-- Name: nirf_extracted_table id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nirf_extracted_table ALTER COLUMN id SET DEFAULT nextval('public.nirf_extracted_table_id_seq'::regclass);


--
-- TOC entry 3495 (class 2604 OID 1500451)
-- Name: nirf_pdf_record id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nirf_pdf_record ALTER COLUMN id SET DEFAULT nextval('public.nirf_pdf_record_id_seq'::regclass);


--
-- TOC entry 3497 (class 2604 OID 1500459)
-- Name: nirf_table_row id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nirf_table_row ALTER COLUMN id SET DEFAULT nextval('public.nirf_table_row_id_seq'::regclass);


--
-- TOC entry 3498 (class 2604 OID 1500472)
-- Name: package_data id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_data ALTER COLUMN id SET DEFAULT nextval('public.package_data_id_seq'::regclass);


--
-- TOC entry 3499 (class 2604 OID 1500487)
-- Name: patents_details id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patents_details ALTER COLUMN id SET DEFAULT nextval('public.patents_details_id_seq'::regclass);


--
-- TOC entry 3500 (class 2604 OID 1500525)
-- Name: phd_students id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.phd_students ALTER COLUMN id SET DEFAULT nextval('public.phd_students_new_id_seq1'::regclass);


--
-- TOC entry 3501 (class 2604 OID 1500591)
-- Name: placements_and_higher_studies id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.placements_and_higher_studies ALTER COLUMN id SET DEFAULT nextval('public.placements_and_higher_studies_new_id_seq'::regclass);


--
-- TOC entry 3502 (class 2604 OID 1500631)
-- Name: research_consultancy_details_consultancy id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.research_consultancy_details_consultancy ALTER COLUMN id SET DEFAULT nextval('public.research_consultancy_details_consultancy_new_id_seq1'::regclass);


--
-- TOC entry 3503 (class 2604 OID 1500688)
-- Name: research_consultancy_details_sponsered id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.research_consultancy_details_sponsered ALTER COLUMN id SET DEFAULT nextval('public.research_consultancy_details_sponsered_new_id_seq1'::regclass);


--
-- TOC entry 3504 (class 2604 OID 1500737)
-- Name: role_data id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_data ALTER COLUMN id SET DEFAULT nextval('public.role_data_id_seq'::regclass);


--
-- TOC entry 3505 (class 2604 OID 1500765)
-- Name: sanctioned_intake id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sanctioned_intake ALTER COLUMN id SET DEFAULT nextval('public.sanctioned_intake_new_id_seq1'::regclass);


--
-- TOC entry 3506 (class 2604 OID 1500783)
-- Name: scraped_data id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scraped_data ALTER COLUMN id SET DEFAULT nextval('public.scraped_data_id_seq'::regclass);


--
-- TOC entry 3507 (class 2604 OID 1500787)
-- Name: scraped_data_save id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scraped_data_save ALTER COLUMN id SET DEFAULT nextval('public.scraped_data_save_id_seq'::regclass);


--
-- TOC entry 3508 (class 2604 OID 1500797)
-- Name: scraped_raw_data id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scraped_raw_data ALTER COLUMN id SET DEFAULT nextval('public.scraped_raw_data_id_seq'::regclass);


--
-- TOC entry 3509 (class 2604 OID 1500805)
-- Name: seed_funding id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seed_funding ALTER COLUMN id SET DEFAULT nextval('public.seed_funding_id_seq'::regclass);


--
-- TOC entry 3510 (class 2604 OID 1500816)
-- Name: startup_receiving_vc_investment id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.startup_receiving_vc_investment ALTER COLUMN id SET DEFAULT nextval('public.startup_receiving_vc_investment_id_seq'::regclass);


--
-- TOC entry 3511 (class 2604 OID 1500825)
-- Name: startup_recognition_old id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.startup_recognition_old ALTER COLUMN id SET DEFAULT nextval('public.startup_recognition_id_seq'::regclass);


--
-- TOC entry 3513 (class 2604 OID 1500837)
-- Name: startups_turnover_50_lacs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.startups_turnover_50_lacs ALTER COLUMN id SET DEFAULT nextval('public.startups_turnover_50_lacs_id_seq'::regclass);


--
-- TOC entry 3514 (class 2604 OID 1500845)
-- Name: tb_academic_year_mstr id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tb_academic_year_mstr ALTER COLUMN id SET DEFAULT nextval('public.tb_academic_year_mstr_id_seq'::regclass);


--
-- TOC entry 3515 (class 2604 OID 1500853)
-- Name: tb_course_program_types id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tb_course_program_types ALTER COLUMN id SET DEFAULT nextval('public.tb_course_program_types_id_seq'::regclass);


--
-- TOC entry 3516 (class 2604 OID 1500860)
-- Name: tb_goi_ministries_mstr id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tb_goi_ministries_mstr ALTER COLUMN id SET DEFAULT nextval('public.tb_goi_ministries_mstr_id_seq'::regclass);


--
-- TOC entry 3517 (class 2604 OID 1500866)
-- Name: tb_institute_mstr id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tb_institute_mstr ALTER COLUMN id SET DEFAULT nextval('public.tb_institute_mstr_id_seq'::regclass);


--
-- TOC entry 3518 (class 2604 OID 1500870)
-- Name: tb_institute_scrap_data_url id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tb_institute_scrap_data_url ALTER COLUMN id SET DEFAULT nextval('public.tb_institute_scrap_data_url_id_seq'::regclass);


--
-- TOC entry 3519 (class 2604 OID 1500874)
-- Name: user_registration id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_registration ALTER COLUMN id SET DEFAULT nextval('public.user_registration_id_seq1'::regclass);


--
-- TOC entry 3521 (class 2604 OID 1500879)
-- Name: user_registration_old id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_registration_old ALTER COLUMN id SET DEFAULT nextval('public.user_registration_id_seq'::regclass);


--
-- TOC entry 3528 (class 2606 OID 1554269)
-- Name: academic_courses_details academic_courses_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.academic_courses_details
    ADD CONSTRAINT academic_courses_details_pkey PRIMARY KEY (id);


--
-- TOC entry 3530 (class 2606 OID 1554271)
-- Name: actual_student_strength actual_student_strength_new_pkey1; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.actual_student_strength
    ADD CONSTRAINT actual_student_strength_new_pkey1 PRIMARY KEY (id);


--
-- TOC entry 3659 (class 2606 OID 1582380)
-- Name: advance_search_data_15_12 advance_search_data_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.advance_search_data_15_12
    ADD CONSTRAINT advance_search_data_pkey PRIMARY KEY (id);


--
-- TOC entry 3532 (class 2606 OID 1554273)
-- Name: advance_search_data_old advance_search_data_pkey1; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.advance_search_data_old
    ADD CONSTRAINT advance_search_data_pkey1 PRIMARY KEY (id);


--
-- TOC entry 3661 (class 2606 OID 1885993)
-- Name: advance_search_data advance_search_data_pkey2; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.advance_search_data
    ADD CONSTRAINT advance_search_data_pkey2 PRIMARY KEY (id);


--
-- TOC entry 3535 (class 2606 OID 1554275)
-- Name: auth_group auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- TOC entry 3540 (class 2606 OID 1554277)
-- Name: auth_group_permissions auth_group_permissions_group_id_permission_id_0cd325b0_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq UNIQUE (group_id, permission_id);


--
-- TOC entry 3543 (class 2606 OID 1554279)
-- Name: auth_group_permissions auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 3537 (class 2606 OID 1554281)
-- Name: auth_group auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- TOC entry 3546 (class 2606 OID 1554283)
-- Name: auth_permission auth_permission_content_type_id_codename_01ab375a_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq UNIQUE (content_type_id, codename);


--
-- TOC entry 3548 (class 2606 OID 1554285)
-- Name: auth_permission auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- TOC entry 3556 (class 2606 OID 1554287)
-- Name: auth_user_groups auth_user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_pkey PRIMARY KEY (id);


--
-- TOC entry 3559 (class 2606 OID 1554289)
-- Name: auth_user_groups auth_user_groups_user_id_group_id_94350c0c_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_group_id_94350c0c_uniq UNIQUE (user_id, group_id);


--
-- TOC entry 3550 (class 2606 OID 1554291)
-- Name: auth_user auth_user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_pkey PRIMARY KEY (id);


--
-- TOC entry 3562 (class 2606 OID 1554293)
-- Name: auth_user_user_permissions auth_user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_pkey PRIMARY KEY (id);


--
-- TOC entry 3565 (class 2606 OID 1554295)
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_permission_id_14a6b632_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_permission_id_14a6b632_uniq UNIQUE (user_id, permission_id);


--
-- TOC entry 3553 (class 2606 OID 1554297)
-- Name: auth_user auth_user_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user
    ADD CONSTRAINT auth_user_username_key UNIQUE (username);


--
-- TOC entry 3569 (class 2606 OID 1554299)
-- Name: combined_ipo_patent_data_old combined_ipo_patent_data_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.combined_ipo_patent_data_old
    ADD CONSTRAINT combined_ipo_patent_data_pkey PRIMARY KEY (id);


--
-- TOC entry 3567 (class 2606 OID 1554301)
-- Name: combined_ipo_patent_data combined_ipo_patent_data_pkey1; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.combined_ipo_patent_data
    ADD CONSTRAINT combined_ipo_patent_data_pkey1 PRIMARY KEY (id);


--
-- TOC entry 3572 (class 2606 OID 1554303)
-- Name: django_admin_log django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- TOC entry 3575 (class 2606 OID 1554305)
-- Name: django_content_type django_content_type_app_label_model_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- TOC entry 3577 (class 2606 OID 1554307)
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- TOC entry 3579 (class 2606 OID 1554309)
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- TOC entry 3582 (class 2606 OID 1554321)
-- Name: django_session django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- TOC entry 3585 (class 2606 OID 1554323)
-- Name: expertise expertise_16_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.expertise
    ADD CONSTRAINT expertise_16_pkey PRIMARY KEY (id);


--
-- TOC entry 3587 (class 2606 OID 1554325)
-- Name: faculty_details faculty_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.faculty_details
    ADD CONSTRAINT faculty_details_pkey PRIMARY KEY (id);


--
-- TOC entry 3589 (class 2606 OID 1554327)
-- Name: faculty_strength faculty_strength_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.faculty_strength
    ADD CONSTRAINT faculty_strength_pkey PRIMARY KEY (id);


--
-- TOC entry 3591 (class 2606 OID 1554329)
-- Name: fdi_investment fdi_investment_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fdi_investment
    ADD CONSTRAINT fdi_investment_pkey PRIMARY KEY (id);


--
-- TOC entry 3593 (class 2606 OID 1554331)
-- Name: fdp_details fdp_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.fdp_details
    ADD CONSTRAINT fdp_details_pkey PRIMARY KEY (id);


--
-- TOC entry 3595 (class 2606 OID 1554333)
-- Name: financial_expenses_capital financial_expenses_capital_new_pkey1; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.financial_expenses_capital
    ADD CONSTRAINT financial_expenses_capital_new_pkey1 PRIMARY KEY (id);


--
-- TOC entry 3597 (class 2606 OID 1554335)
-- Name: financial_expenses_operational financial_expenses_operational_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.financial_expenses_operational
    ADD CONSTRAINT financial_expenses_operational_pkey PRIMARY KEY (id);


--
-- TOC entry 3599 (class 2606 OID 1554337)
-- Name: founders_of_fortune_500_companies founders_of_fortune_500_companies_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.founders_of_fortune_500_companies
    ADD CONSTRAINT founders_of_fortune_500_companies_pkey PRIMARY KEY (id);


--
-- TOC entry 3601 (class 2606 OID 1554339)
-- Name: incubation_details incubation_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.incubation_details
    ADD CONSTRAINT incubation_details_pkey PRIMARY KEY (id);


--
-- TOC entry 3603 (class 2606 OID 1554356)
-- Name: innovation_grant_from_govt innovation_grant_from_govt_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.innovation_grant_from_govt
    ADD CONSTRAINT innovation_grant_from_govt_pkey PRIMARY KEY (id);


--
-- TOC entry 3605 (class 2606 OID 1554367)
-- Name: innovations_at_various_stages_of_technology_readiness_level innovations_at_various_stages_of_technology_readiness_lev_pkey1; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.innovations_at_various_stages_of_technology_readiness_level
    ADD CONSTRAINT innovations_at_various_stages_of_technology_readiness_lev_pkey1 PRIMARY KEY (id);


--
-- TOC entry 3607 (class 2606 OID 1554370)
-- Name: ipo_patent_details_flat_old ipo_patent_details_flat_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.ipo_patent_details_flat_old
    ADD CONSTRAINT ipo_patent_details_flat_pkey PRIMARY KEY (id);


--
-- TOC entry 3609 (class 2606 OID 1554375)
-- Name: master_expertise master_expertise_pkey1; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.master_expertise
    ADD CONSTRAINT master_expertise_pkey1 PRIMARY KEY (id);


--
-- TOC entry 3611 (class 2606 OID 1554381)
-- Name: nirf_extracted_table nirf_extracted_table_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nirf_extracted_table
    ADD CONSTRAINT nirf_extracted_table_pkey PRIMARY KEY (id);


--
-- TOC entry 3613 (class 2606 OID 1554383)
-- Name: nirf_pdf_record nirf_pdf_record_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nirf_pdf_record
    ADD CONSTRAINT nirf_pdf_record_pkey PRIMARY KEY (id);


--
-- TOC entry 3615 (class 2606 OID 1554387)
-- Name: nirf_table_row nirf_table_row_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nirf_table_row
    ADD CONSTRAINT nirf_table_row_pkey PRIMARY KEY (id);


--
-- TOC entry 3617 (class 2606 OID 1554389)
-- Name: package_data package_data_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.package_data
    ADD CONSTRAINT package_data_pkey PRIMARY KEY (id);


--
-- TOC entry 3619 (class 2606 OID 1554391)
-- Name: patents_details patents_details_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.patents_details
    ADD CONSTRAINT patents_details_pkey PRIMARY KEY (id);


--
-- TOC entry 3621 (class 2606 OID 1554393)
-- Name: phd_students phd_students_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.phd_students
    ADD CONSTRAINT phd_students_pkey PRIMARY KEY (id);


--
-- TOC entry 3623 (class 2606 OID 1554395)
-- Name: placements_and_higher_studies placements_and_higher_studies_new_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.placements_and_higher_studies
    ADD CONSTRAINT placements_and_higher_studies_new_pkey PRIMARY KEY (id);


--
-- TOC entry 3625 (class 2606 OID 1554397)
-- Name: research_consultancy_details_consultancy research_consultancy_details_consultancy_new_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.research_consultancy_details_consultancy
    ADD CONSTRAINT research_consultancy_details_consultancy_new_pkey PRIMARY KEY (id);


--
-- TOC entry 3627 (class 2606 OID 1554399)
-- Name: research_consultancy_details_sponsered research_consultancy_details_sponsered_new_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.research_consultancy_details_sponsered
    ADD CONSTRAINT research_consultancy_details_sponsered_new_pkey PRIMARY KEY (id);


--
-- TOC entry 3629 (class 2606 OID 1554401)
-- Name: role_data role_data_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_data
    ADD CONSTRAINT role_data_pkey PRIMARY KEY (id);


--
-- TOC entry 3631 (class 2606 OID 1554403)
-- Name: sanctioned_intake sanctioned_intake_new_pkey1; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.sanctioned_intake
    ADD CONSTRAINT sanctioned_intake_new_pkey1 PRIMARY KEY (id);


--
-- TOC entry 3633 (class 2606 OID 1554405)
-- Name: scraped_data scraped_data_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.scraped_data
    ADD CONSTRAINT scraped_data_pkey PRIMARY KEY (id);


--
-- TOC entry 3635 (class 2606 OID 1554407)
-- Name: seed_funding seed_funding_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.seed_funding
    ADD CONSTRAINT seed_funding_pkey PRIMARY KEY (id);


--
-- TOC entry 3637 (class 2606 OID 1554409)
-- Name: startup_receiving_vc_investment startup_receiving_vc_investment_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.startup_receiving_vc_investment
    ADD CONSTRAINT startup_receiving_vc_investment_pkey PRIMARY KEY (id);


--
-- TOC entry 3639 (class 2606 OID 1554411)
-- Name: startup_recognition_old startup_recognition_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.startup_recognition_old
    ADD CONSTRAINT startup_recognition_pkey PRIMARY KEY (id);


--
-- TOC entry 3641 (class 2606 OID 1554413)
-- Name: startup_recognition startup_recognition_pkey1; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.startup_recognition
    ADD CONSTRAINT startup_recognition_pkey1 PRIMARY KEY (id);


--
-- TOC entry 3643 (class 2606 OID 1554415)
-- Name: startups_turnover_50_lacs startups_turnover_50_lacs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.startups_turnover_50_lacs
    ADD CONSTRAINT startups_turnover_50_lacs_pkey PRIMARY KEY (id);


--
-- TOC entry 3645 (class 2606 OID 1554417)
-- Name: tb_goi_ministries_mstr tb_goi_ministries_mstr_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tb_goi_ministries_mstr
    ADD CONSTRAINT tb_goi_ministries_mstr_pkey PRIMARY KEY (id);


--
-- TOC entry 3647 (class 2606 OID 1554419)
-- Name: tb_institute_mstr tb_institute_mstr_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tb_institute_mstr
    ADD CONSTRAINT tb_institute_mstr_pkey PRIMARY KEY (id);


--
-- TOC entry 3649 (class 2606 OID 1554421)
-- Name: tb_institute_scrap_data_url tb_institute_scrap_data_url_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.tb_institute_scrap_data_url
    ADD CONSTRAINT tb_institute_scrap_data_url_pkey PRIMARY KEY (id);


--
-- TOC entry 3653 (class 2606 OID 1554423)
-- Name: user_registration_old user_registration_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_registration_old
    ADD CONSTRAINT user_registration_email_key UNIQUE (email);


--
-- TOC entry 3655 (class 2606 OID 1554425)
-- Name: user_registration_old user_registration_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_registration_old
    ADD CONSTRAINT user_registration_pkey PRIMARY KEY (id);


--
-- TOC entry 3651 (class 2606 OID 1554427)
-- Name: user_registration user_registration_pkey1; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_registration
    ADD CONSTRAINT user_registration_pkey1 PRIMARY KEY (id);


--
-- TOC entry 3657 (class 2606 OID 1554429)
-- Name: user_registration_old user_registration_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_registration_old
    ADD CONSTRAINT user_registration_username_key UNIQUE (username);


--
-- TOC entry 3533 (class 1259 OID 1554430)
-- Name: auth_group_name_a6ea08ec_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);


--
-- TOC entry 3538 (class 1259 OID 1554431)
-- Name: auth_group_permissions_group_id_b120cbf9; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);


--
-- TOC entry 3541 (class 1259 OID 1554432)
-- Name: auth_group_permissions_permission_id_84c5c92e; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);


--
-- TOC entry 3544 (class 1259 OID 1554433)
-- Name: auth_permission_content_type_id_2f476e4b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);


--
-- TOC entry 3554 (class 1259 OID 1554434)
-- Name: auth_user_groups_group_id_97559544; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_groups_group_id_97559544 ON public.auth_user_groups USING btree (group_id);


--
-- TOC entry 3557 (class 1259 OID 1554435)
-- Name: auth_user_groups_user_id_6a12ed8b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_groups_user_id_6a12ed8b ON public.auth_user_groups USING btree (user_id);


--
-- TOC entry 3560 (class 1259 OID 1554436)
-- Name: auth_user_user_permissions_permission_id_1fbb5f2c; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_user_permissions_permission_id_1fbb5f2c ON public.auth_user_user_permissions USING btree (permission_id);


--
-- TOC entry 3563 (class 1259 OID 1554437)
-- Name: auth_user_user_permissions_user_id_a95ead1b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_user_permissions_user_id_a95ead1b ON public.auth_user_user_permissions USING btree (user_id);


--
-- TOC entry 3551 (class 1259 OID 1554438)
-- Name: auth_user_username_6821ab7c_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_user_username_6821ab7c_like ON public.auth_user USING btree (username varchar_pattern_ops);


--
-- TOC entry 3570 (class 1259 OID 1554439)
-- Name: django_admin_log_content_type_id_c4bce8eb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);


--
-- TOC entry 3573 (class 1259 OID 1554440)
-- Name: django_admin_log_user_id_c564eba6; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);


--
-- TOC entry 3580 (class 1259 OID 1554441)
-- Name: django_session_expire_date_a5c62663; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);


--
-- TOC entry 3583 (class 1259 OID 1554442)
-- Name: django_session_session_key_c0390e0f_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);


--
-- TOC entry 3662 (class 2606 OID 1554443)
-- Name: auth_group_permissions auth_group_permissio_permission_id_84c5c92e_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3663 (class 2606 OID 1554448)
-- Name: auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3664 (class 2606 OID 1554453)
-- Name: auth_permission auth_permission_content_type_id_2f476e4b_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3665 (class 2606 OID 1554458)
-- Name: auth_user_groups auth_user_groups_group_id_97559544_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_group_id_97559544_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3666 (class 2606 OID 1554463)
-- Name: auth_user_groups auth_user_groups_user_id_6a12ed8b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_groups
    ADD CONSTRAINT auth_user_groups_user_id_6a12ed8b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3667 (class 2606 OID 1554468)
-- Name: auth_user_user_permissions auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permi_permission_id_1fbb5f2c_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3668 (class 2606 OID 1554473)
-- Name: auth_user_user_permissions auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_user_user_permissions
    ADD CONSTRAINT auth_user_user_permissions_user_id_a95ead1b_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3669 (class 2606 OID 1554478)
-- Name: django_admin_log django_admin_log_content_type_id_c4bce8eb_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3670 (class 2606 OID 1554483)
-- Name: django_admin_log django_admin_log_user_id_c564eba6_fk_auth_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_user_id_c564eba6_fk_auth_user_id FOREIGN KEY (user_id) REFERENCES public.auth_user(id) DEFERRABLE INITIALLY DEFERRED;


--
-- TOC entry 3671 (class 2606 OID 1554488)
-- Name: nirf_extracted_table nirf_extracted_table_pdf_record_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nirf_extracted_table
    ADD CONSTRAINT nirf_extracted_table_pdf_record_id_fkey FOREIGN KEY (pdf_record_id) REFERENCES public.nirf_pdf_record(id) ON DELETE CASCADE;


--
-- TOC entry 3672 (class 2606 OID 1554493)
-- Name: nirf_table_row nirf_table_row_table_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.nirf_table_row
    ADD CONSTRAINT nirf_table_row_table_id_fkey FOREIGN KEY (table_id) REFERENCES public.nirf_extracted_table(id) ON DELETE CASCADE;


--
-- TOC entry 3817 (class 0 OID 0)
-- Dependencies: 6
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: postgres
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO PUBLIC;


-- Completed on 2026-01-09 10:51:32

--
-- PostgreSQL database dump complete
--

