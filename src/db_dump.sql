--
-- PostgreSQL database dump
--

-- Dumped from database version 13.18 (Debian 13.18-0+deb11u1)
-- Dumped by pg_dump version 13.18 (Debian 13.18-0+deb11u1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: host_class; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.host_class AS ENUM (
    'GitHub',
    'local'
);


ALTER TYPE public.host_class OWNER TO postgres;

--
-- Name: message_class; Type: TYPE; Schema: public; Owner: postgres
--

CREATE TYPE public.message_class AS ENUM (
    'system',
    'info',
    'offer_created',
    'offer_cancelled',
    'contract_created',
    'position_covered',
    'contract_resolved',
    'new_account'
);


ALTER TYPE public.message_class OWNER TO postgres;

--
-- Name: check_contract_type_maturity(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.check_contract_type_maturity() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
	DECLARE
		not_after TIMESTAMP;
BEGIN
	SELECT maturity.matures INTO not_after FROM contract_type JOIN maturity ON contract_type.matures = maturity.id
		WHERE contract_type.id = NEW.contract_type;
	IF NOW() > not_after THEN
		RAISE EXCEPTION 'Contract type maturity date is in the past.';
	END IF;
	RETURN NEW;
END;
$$;


ALTER FUNCTION public.check_contract_type_maturity() OWNER TO postgres;

--
-- Name: update_modified_column(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_modified_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.modified = NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_modified_column() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: account; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.account (
    id integer NOT NULL,
    enabled boolean DEFAULT true NOT NULL,
    system boolean DEFAULT false NOT NULL,
    banker boolean DEFAULT false NOT NULL,
    oracle boolean DEFAULT false NOT NULL,
    balance bigint NOT NULL,
    min_balance bigint DEFAULT 0 NOT NULL,
    CONSTRAINT account_balance_check CHECK ((balance >= 0))
);


ALTER TABLE public.account OWNER TO postgres;

--
-- Name: account_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.account_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.account_id_seq OWNER TO postgres;

--
-- Name: account_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.account_id_seq OWNED BY public.account.id;


--
-- Name: contract_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.contract_type (
    id integer NOT NULL,
    issue integer,
    matures integer
);


ALTER TABLE public.contract_type OWNER TO postgres;

--
-- Name: contract_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.contract_type_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.contract_type_id_seq OWNER TO postgres;

--
-- Name: contract_type_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.contract_type_id_seq OWNED BY public.contract_type.id;


--
-- Name: issue; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.issue (
    id integer NOT NULL,
    project integer DEFAULT 1,
    url text NOT NULL,
    title text,
    created timestamp without time zone DEFAULT now() NOT NULL,
    modified timestamp without time zone DEFAULT now() NOT NULL,
    updated timestamp without time zone,
    tracker_status text,
    open boolean DEFAULT true NOT NULL,
    fixed boolean DEFAULT false NOT NULL
);


ALTER TABLE public.issue OWNER TO postgres;

--
-- Name: issue_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.issue_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.issue_id_seq OWNER TO postgres;

--
-- Name: issue_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.issue_id_seq OWNED BY public.issue.id;


--
-- Name: maturity; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.maturity (
    id integer NOT NULL,
    matures timestamp without time zone NOT NULL
);


ALTER TABLE public.maturity OWNER TO postgres;

--
-- Name: maturity_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.maturity_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.maturity_id_seq OWNER TO postgres;

--
-- Name: maturity_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.maturity_id_seq OWNED BY public.maturity.id;


--
-- Name: message; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.message (
    id integer NOT NULL,
    class public.message_class NOT NULL,
    created timestamp without time zone DEFAULT now() NOT NULL,
    delivered timestamp without time zone,
    recipient integer,
    contract_type integer,
    side boolean,
    price bigint,
    quantity bigint,
    message text NOT NULL,
    expires timestamp without time zone
);


ALTER TABLE public.message OWNER TO postgres;

--
-- Name: message_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.message_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.message_id_seq OWNER TO postgres;

--
-- Name: message_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.message_id_seq OWNED BY public.message.id;


--
-- Name: message_overview; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.message_overview AS
 SELECT maturity.id AS maturity,
    maturity.matures,
    issue.id AS issue,
    issue.url,
    issue.title,
    message.id,
    message.class,
    message.created,
    message.delivered,
    message.recipient,
    message.contract_type,
    message.side,
    message.price,
    message.quantity,
    message.expires,
    message.message
   FROM (((public.message
     LEFT JOIN public.contract_type ON ((contract_type.id = message.contract_type)))
     LEFT JOIN public.maturity ON ((maturity.id = contract_type.matures)))
     LEFT JOIN public.issue ON ((issue.id = contract_type.issue)));


ALTER TABLE public.message_overview OWNER TO postgres;

--
-- Name: offer; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.offer (
    id integer NOT NULL,
    account integer,
    created timestamp without time zone DEFAULT now() NOT NULL,
    contract_type integer,
    side boolean NOT NULL,
    price bigint NOT NULL,
    quantity bigint NOT NULL,
    all_or_nothing boolean DEFAULT false NOT NULL,
    expires timestamp without time zone,
    CONSTRAINT offer_price_check CHECK (((price >= 0) AND (price <= 1000))),
    CONSTRAINT offer_quantity_check CHECK ((quantity > 0))
);


ALTER TABLE public.offer OWNER TO postgres;

--
-- Name: offer_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.offer_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.offer_id_seq OWNER TO postgres;

--
-- Name: offer_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.offer_id_seq OWNED BY public.offer.id;


--
-- Name: offer_overview; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.offer_overview AS
 SELECT maturity.id AS maturity,
    maturity.matures,
    contract_type.id AS contract_type,
    issue.id AS issue,
    issue.url,
    issue.title,
    offer.id,
    offer.account,
    offer.side,
    offer.price,
    offer.quantity,
    offer.created,
    offer.all_or_nothing,
    offer.expires
   FROM (((public.maturity
     JOIN public.contract_type ON ((maturity.id = contract_type.matures)))
     JOIN public.issue ON ((issue.id = contract_type.issue)))
     JOIN public.offer ON ((contract_type.id = offer.contract_type)));


ALTER TABLE public.offer_overview OWNER TO postgres;

--
-- Name: position; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."position" (
    id integer NOT NULL,
    account integer,
    created timestamp without time zone DEFAULT now() NOT NULL,
    modified timestamp without time zone DEFAULT now() NOT NULL,
    contract_type integer,
    basis bigint NOT NULL,
    quantity bigint NOT NULL,
    CONSTRAINT position_basis_check CHECK ((basis >= 0)),
    CONSTRAINT position_quantity_check CHECK ((quantity <> 0))
);


ALTER TABLE public."position" OWNER TO postgres;

--
-- Name: position_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.position_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.position_id_seq OWNER TO postgres;

--
-- Name: position_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.position_id_seq OWNED BY public."position".id;


--
-- Name: project; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.project (
    id integer NOT NULL,
    url text NOT NULL,
    owner integer DEFAULT 1,
    webhook_secret text
);


ALTER TABLE public.project OWNER TO postgres;

--
-- Name: project_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.project_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.project_id_seq OWNER TO postgres;

--
-- Name: project_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.project_id_seq OWNED BY public.project.id;


--
-- Name: ticker; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.ticker AS
 SELECT DISTINCT maturity.id AS maturity,
    maturity.matures,
    contract_type.id AS contract_type,
    issue.id AS issue,
    issue.url,
    issue.title,
    message.id,
    message.class,
    message.side,
    message.price,
    message.quantity,
    message.expires,
    message.created
   FROM (((public.maturity
     JOIN public.contract_type ON ((maturity.id = contract_type.matures)))
     JOIN public.issue ON ((issue.id = contract_type.issue)))
     JOIN public.message ON ((contract_type.id = message.contract_type)))
  WHERE ((message.side IS NOT NULL) AND (message.price > 0));


ALTER TABLE public.ticker OWNER TO postgres;

--
-- Name: userid; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.userid (
    id integer NOT NULL,
    account integer,
    host public.host_class NOT NULL,
    sub text NOT NULL,
    username text NOT NULL,
    profile text NOT NULL
);


ALTER TABLE public.userid OWNER TO postgres;

--
-- Name: userid_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.userid_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER TABLE public.userid_id_seq OWNER TO postgres;

--
-- Name: userid_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.userid_id_seq OWNED BY public.userid.id;


--
-- Name: account id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account ALTER COLUMN id SET DEFAULT nextval('public.account_id_seq'::regclass);


--
-- Name: contract_type id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contract_type ALTER COLUMN id SET DEFAULT nextval('public.contract_type_id_seq'::regclass);


--
-- Name: issue id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issue ALTER COLUMN id SET DEFAULT nextval('public.issue_id_seq'::regclass);


--
-- Name: maturity id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.maturity ALTER COLUMN id SET DEFAULT nextval('public.maturity_id_seq'::regclass);


--
-- Name: message id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.message ALTER COLUMN id SET DEFAULT nextval('public.message_id_seq'::regclass);


--
-- Name: offer id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.offer ALTER COLUMN id SET DEFAULT nextval('public.offer_id_seq'::regclass);


--
-- Name: position id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."position" ALTER COLUMN id SET DEFAULT nextval('public.position_id_seq'::regclass);


--
-- Name: project id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project ALTER COLUMN id SET DEFAULT nextval('public.project_id_seq'::regclass);


--
-- Name: userid id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userid ALTER COLUMN id SET DEFAULT nextval('public.userid_id_seq'::regclass);


--
-- Data for Name: account; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.account (id, enabled, system, banker, oracle, balance, min_balance) FROM stdin;
1	t	t	f	f	0	0
3	t	f	f	f	1000000	0
5	t	f	f	f	1000000	0
10	t	f	f	f	0	0
11	t	f	f	f	950050	0
9	t	f	f	f	196000	0
12	t	f	f	f	0	0
2	t	f	t	t	1980650	0
6	t	f	f	f	1000000	0
7	t	f	f	f	1000000	0
4	t	f	f	f	980000	0
8	t	f	f	f	0	0
18	t	f	f	f	100000	0
19	t	f	f	f	100000	0
13	t	f	f	f	10000	0
\.


--
-- Data for Name: contract_type; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.contract_type (id, issue, matures) FROM stdin;
1	3	1
4	2	1
7	1	1
9	2	3
11	3	2
12	3	3
13	2	4
10	2	2
16	29	75
38	1	77
40	34	77
21	3	76
43	34	78
48	2	91
49	1	91
\.


--
-- Data for Name: issue; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.issue (id, project, url, title, created, modified, updated, tracker_status, open, fixed) FROM stdin;
1	1	https://github.com/pinfactory/pinfactory/issues/11	Security review.	2022-02-13 20:21:49.792553	2022-02-13 20:21:49.792553	\N	\N	t	f
2	1	https://github.com/pinfactory/pinfactory/issues/28	Microsoft Windows and VS Code instructions in README.md	2022-02-13 20:36:47.572127	2022-02-13 20:36:47.572127	\N	\N	t	f
3	1	https://github.com/pinfactory/pinfactory/issues/15	Add CSS to keep "Estimated fee" elements on the same line	2022-02-13 20:39:16.407295	2022-02-13 20:39:16.407295	\N	\N	t	f
29	1	https://github.com/pinfactory/pinfactory/issues/18	Fix webhook secrets handling	2024-12-23 00:33:39.375081	2024-12-26 16:12:21.591215	\N	\N	t	f
34	1	https://github.com/pinfactory/pinfactory/issues/26	FAQ	2024-12-28 14:42:40.774474	2024-12-28 14:42:40.774474	\N	\N	t	f
35	1	https://github.com/pinfactory/pinfactory/issues/42	Mplfinance charts	2025-09-26 00:30:50.965548	2025-09-26 00:30:50.965548	\N	\N	t	f
\.


--
-- Data for Name: maturity; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.maturity (id, matures) FROM stdin;
1	2022-02-26 00:00:00
2	2022-03-12 00:00:00
3	2022-03-26 00:00:00
4	2022-04-09 00:00:00
75	2024-12-28 00:00:00
76	2025-01-11 00:00:00
77	2025-01-25 00:00:00
78	2025-02-08 00:00:00
91	2025-08-09 00:00:00
96	2025-10-18 00:00:00
97	2025-11-01 00:00:00
98	2025-11-15 00:00:00
\.


--
-- Data for Name: message; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.message (id, class, created, delivered, recipient, contract_type, side, price, quantity, message, expires) FROM stdin;
1	system	2022-02-13 19:13:36.584059	\N	1	\N	\N	\N	\N	Database setup run.	\N
2	system	2022-02-13 19:17:41.683279	\N	1	\N	\N	\N	\N	Database setup run.	\N
3	system	2022-02-13 20:20:42.322189	\N	1	\N	\N	\N	\N	Database setup run.	\N
4	new_account	2022-02-13 20:21:43.843324	\N	1	\N	\N	\N	\N	New account 2 created: GitHub 48007	\N
5	system	2022-02-13 20:21:49.792553	\N	1	\N	\N	\N	\N	Issue created: https://github.com/pinfactory/pinfactory/issues/11	\N
6	system	2022-02-13 20:36:47.572127	\N	1	\N	\N	\N	\N	Issue created: https://github.com/pinfactory/pinfactory/issues/28	\N
7	system	2022-02-13 20:39:16.407295	\N	1	\N	\N	\N	\N	Issue created: https://github.com/pinfactory/pinfactory/issues/15	\N
8	system	2022-02-13 20:39:18.874566	\N	1	\N	\N	\N	\N	Issue created: https://github.com/pinfactory/pinfactory/issues/19	\N
9	system	2022-02-13 20:40:13.704383	\N	1	\N	\N	\N	\N	Issue updated: https://github.com/pinfactory/pinfactory/issues/19	\N
10	system	2022-02-13 20:40:23.68265	\N	1	\N	\N	\N	\N	Issue created: https://github.com/pinfactory/pinfactory/issues/21	\N
11	new_account	2022-02-14 10:43:49.742523	\N	1	\N	\N	\N	\N	New account 3 created: GitHub 63842643	\N
12	new_account	2022-02-15 05:39:45.838782	\N	1	\N	\N	\N	\N	New account 4 created: GitHub 68496788	\N
13	offer_created	2022-02-17 00:01:06.607371	\N	2	1	f	200	50	Offer made: 50 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 1 at 26 Feb at a (fixed) price of 0.200	\N
14	offer_created	2022-02-17 16:48:54.01689	\N	2	1	f	100	50	Offer made: 50 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 1 at 26 Feb at a (fixed) price of 0.100	\N
15	offer_created	2022-02-17 16:49:09.480314	\N	2	1	f	60	50	Offer made: 50 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 1 at 26 Feb at a (fixed) price of 0.060	\N
16	offer_created	2022-02-17 16:49:28.384832	\N	2	4	f	60	50	Offer made: 50 units of UNFIXED on Microsoft Windows and VS Code instructions in README.md (28) with maturity 1 at 26 Feb at a (fixed) price of 0.060	\N
17	offer_created	2022-02-17 16:49:49.683458	\N	2	4	f	100	50	Offer made: 50 units of UNFIXED on Microsoft Windows and VS Code instructions in README.md (28) with maturity 1 at 26 Feb at a (fixed) price of 0.100	\N
18	offer_created	2022-02-17 16:50:03.664406	\N	2	4	f	20	50	Offer made: 50 units of UNFIXED on Microsoft Windows and VS Code instructions in README.md (28) with maturity 1 at 26 Feb at a (fixed) price of 0.020	\N
19	system	2022-02-19 02:45:41.688098	\N	1	\N	\N	\N	\N	Database setup run.	\N
20	offer_created	2022-02-19 02:45:54.640536	\N	2	7	f	20	50	Offer made: 50 units of UNFIXED on Security review. (11) with maturity 1 at 26 Feb at a (fixed) price of 0.020	\N
21	system	2022-02-20 23:50:23.13859	\N	1	\N	\N	\N	\N	Database setup run.	\N
22	new_account	2022-02-25 00:03:50.530766	\N	1	\N	\N	\N	\N	New account 5 created: GitHub 41296318	\N
23	offer_cancelled	2022-02-26 06:25:02.888021	\N	2	1	f	200	50	Offer cancelled: 50 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 1 at 26 Feb at a (fixed) price of 0.200	\N
24	info	2022-02-26 06:25:02.888021	\N	2	\N	\N	\N	\N	An offer from you has been cancelled because the maturity date is in the past.	\N
25	offer_cancelled	2022-02-26 06:25:02.937847	\N	2	1	f	100	50	Offer cancelled: 50 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 1 at 26 Feb at a (fixed) price of 0.100	\N
26	info	2022-02-26 06:25:02.937847	\N	2	\N	\N	\N	\N	An offer from you has been cancelled because the maturity date is in the past.	\N
27	offer_cancelled	2022-02-26 06:25:02.940654	\N	2	1	f	60	50	Offer cancelled: 50 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 1 at 26 Feb at a (fixed) price of 0.060	\N
28	info	2022-02-26 06:25:02.940654	\N	2	\N	\N	\N	\N	An offer from you has been cancelled because the maturity date is in the past.	\N
29	offer_cancelled	2022-02-26 06:25:02.943109	\N	2	4	f	60	50	Offer cancelled: 50 units of UNFIXED on Microsoft Windows and VS Code instructions in README.md (28) with maturity 1 at 26 Feb at a (fixed) price of 0.060	\N
30	info	2022-02-26 06:25:02.943109	\N	2	\N	\N	\N	\N	An offer from you has been cancelled because the maturity date is in the past.	\N
31	offer_cancelled	2022-02-26 06:25:02.945489	\N	2	4	f	100	50	Offer cancelled: 50 units of UNFIXED on Microsoft Windows and VS Code instructions in README.md (28) with maturity 1 at 26 Feb at a (fixed) price of 0.100	\N
32	info	2022-02-26 06:25:02.945489	\N	2	\N	\N	\N	\N	An offer from you has been cancelled because the maturity date is in the past.	\N
33	offer_cancelled	2022-02-26 06:25:02.948166	\N	2	4	f	20	50	Offer cancelled: 50 units of UNFIXED on Microsoft Windows and VS Code instructions in README.md (28) with maturity 1 at 26 Feb at a (fixed) price of 0.020	\N
34	info	2022-02-26 06:25:02.948166	\N	2	\N	\N	\N	\N	An offer from you has been cancelled because the maturity date is in the past.	\N
35	offer_cancelled	2022-02-26 06:25:02.951061	\N	2	7	f	20	50	Offer cancelled: 50 units of UNFIXED on Security review. (11) with maturity 1 at 26 Feb at a (fixed) price of 0.020	\N
36	info	2022-02-26 06:25:02.951061	\N	2	\N	\N	\N	\N	An offer from you has been cancelled because the maturity date is in the past.	\N
37	offer_created	2022-02-26 18:17:37.621603	\N	2	9	f	200	50	Offer made: 50 units of UNFIXED on Microsoft Windows and VS Code instructions in README.md (28) with maturity 3 at 26 Mar at a (fixed) price of 0.200	\N
38	offer_created	2022-02-26 18:17:40.449962	\N	2	10	f	400	50	Offer made: 50 units of UNFIXED on Microsoft Windows and VS Code instructions in README.md (28) with maturity 2 at 12 Mar at a (fixed) price of 0.400	\N
39	offer_created	2022-02-26 18:18:22.940867	\N	2	11	f	400	50	Offer made: 50 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 2 at 12 Mar at a (fixed) price of 0.400	\N
40	offer_created	2022-02-26 18:18:53.474034	\N	2	12	f	600	50	Offer made: 50 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 3 at 26 Mar at a (fixed) price of 0.600	\N
41	system	2022-02-26 18:19:07.760021	\N	1	\N	\N	\N	\N	Issue created: https://github.com/pinfactory/pinfactory/issues/13	\N
42	system	2022-03-04 00:09:58.899524	\N	1	\N	\N	\N	\N	Issue created: https://github.com/nahmii-community/bridge/issues/25	\N
43	system	2022-03-04 12:21:26.465325	\N	1	\N	\N	\N	\N	Issue updated: https://github.com/nahmii-community/bridge/issues/25	\N
44	system	2022-03-04 15:49:45.736721	\N	1	\N	\N	\N	\N	Issue created: https://github.com/nahmii-community/bridge/issues/57	\N
45	system	2022-03-07 05:24:49.589757	\N	1	\N	\N	\N	\N	Issue created: https://github.com/nahmii-community/bridge/issues/12	\N
46	system	2022-03-07 10:53:04.354121	\N	1	\N	\N	\N	\N	Issue updated: https://github.com/nahmii-community/bridge/issues/25	\N
47	offer_created	2022-03-07 18:34:44.703949	\N	4	13	t	200	50	Offer made: 50 units of FIXED on Microsoft Windows and VS Code instructions in README.md (28) with maturity 4 at 09 Apr at a (fixed) price of 0.200	\N
48	contract_created	2022-03-07 18:46:33.491952	\N	4	10	t	400	50	Contract formed: 50 units of FIXED Microsoft Windows and VS Code instructions in README.md (28) with maturity 2 at 12 Mar at a (fixed) price of 0.400	\N
137	system	2024-12-27 16:16:08.816625	\N	1	\N	\N	\N	\N	Database setup run.	\N
49	contract_created	2022-03-07 18:46:33.491952	\N	2	10	f	400	50	Contract formed: 50 units of UNFIXED Microsoft Windows and VS Code instructions in README.md (28) with maturity 2 at 12 Mar at a (fixed) price of 0.400	\N
50	system	2022-03-10 00:04:28.12389	\N	1	\N	\N	\N	\N	Issue created: https://github.com/pinfactory/pinfactory/issues/35	\N
51	system	2022-03-11 02:48:45.964707	\N	1	\N	\N	\N	\N	Issue updated: https://github.com/nahmii-community/bridge/issues/57	\N
52	system	2022-03-11 10:10:17.114805	\N	1	\N	\N	\N	\N	Issue updated: https://github.com/nahmii-community/bridge/issues/57	\N
53	offer_cancelled	2022-03-12 06:25:01.915717	\N	2	11	f	400	50	Offer cancelled: 50 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 2 at 12 Mar at a (fixed) price of 0.400	\N
54	info	2022-03-12 06:25:01.915717	\N	2	\N	\N	\N	\N	An offer from you has been cancelled because the maturity date is in the past.	\N
55	system	2022-03-13 11:07:55.702341	\N	1	\N	\N	\N	\N	Issue created: https://github.com/nahmii-community/bridge/issues/50	\N
56	system	2022-03-13 20:08:24.245765	\N	1	\N	\N	\N	\N	Issue updated: https://github.com/nahmii-community/bridge/issues/50	\N
57	system	2022-03-14 00:05:42.954626	\N	1	\N	\N	\N	\N	Issue created: https://github.com/nahmii-community/bridge/issues/51	\N
58	system	2022-03-14 10:53:14.07129	\N	1	\N	\N	\N	\N	Issue updated: https://github.com/nahmii-community/bridge/issues/57	\N
59	system	2022-03-17 00:08:05.826589	\N	1	\N	\N	\N	\N	Issue created: https://github.com/nahmii-community/bridge/issues/48	\N
60	system	2022-03-17 08:36:50.308217	\N	1	\N	\N	\N	\N	Issue updated: https://github.com/nahmii-community/bridge/issues/48	\N
61	contract_resolved	2022-03-17 14:42:48.999631	\N	4	10	t	0	50	Contract resolved: Microsoft Windows and VS Code instructions in README.md (28) with maturity 2 at 12 Mar for a payout of 0 tokens	\N
62	contract_resolved	2022-03-17 14:42:48.999631	\N	2	10	f	1000	48	Contract resolved: Microsoft Windows and VS Code instructions in README.md (28) with maturity 2 at 12 Mar for a payout of 48 tokens	\N
63	new_account	2022-03-17 14:42:49.064554	\N	1	\N	\N	\N	\N	New account 6 created: GitHub 9271195	\N
64	system	2022-03-17 16:17:53.233273	\N	1	\N	\N	\N	\N	Issue updated: https://github.com/nahmii-community/bridge/issues/48	\N
65	system	2022-03-17 20:18:03.241202	\N	1	\N	\N	\N	\N	Issue updated: https://github.com/nahmii-community/bridge/issues/48	\N
66	system	2022-03-17 20:18:06.048613	\N	1	\N	\N	\N	\N	Issue updated: https://github.com/nahmii-community/bridge/issues/48	\N
67	system	2022-03-18 03:57:28.145856	\N	1	\N	\N	\N	\N	Issue updated: https://github.com/nahmii-community/bridge/issues/48	\N
68	system	2022-03-18 12:31:38.452543	\N	1	\N	\N	\N	\N	Issue updated: https://github.com/nahmii-community/bridge/issues/57	\N
69	system	2022-03-18 12:31:39.706129	\N	1	\N	\N	\N	\N	Issue updated: https://github.com/nahmii-community/bridge/issues/57	\N
70	system	2022-03-21 00:05:02.670709	\N	1	\N	\N	\N	\N	Issue created: https://github.com/nahmii-community/bridge/issues/67	\N
71	new_account	2022-03-24 04:21:35.931056	\N	1	\N	\N	\N	\N	New account 7 created: GitHub 7009200	\N
72	offer_cancelled	2022-03-26 06:25:04.374071	\N	2	9	f	200	50	Offer cancelled: 50 units of UNFIXED on Microsoft Windows and VS Code instructions in README.md (28) with maturity 3 at 26 Mar at a (fixed) price of 0.200	\N
73	info	2022-03-26 06:25:04.374071	\N	2	\N	\N	\N	\N	An offer from you has been cancelled because the maturity date is in the past.	\N
74	offer_cancelled	2022-03-26 06:25:04.450732	\N	2	12	f	600	50	Offer cancelled: 50 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 3 at 26 Mar at a (fixed) price of 0.600	\N
75	info	2022-03-26 06:25:04.450732	\N	2	\N	\N	\N	\N	An offer from you has been cancelled because the maturity date is in the past.	\N
76	offer_cancelled	2022-04-09 06:25:02.422659	\N	4	13	t	200	50	Offer cancelled: 50 units of FIXED on Microsoft Windows and VS Code instructions in README.md (28) with maturity 4 at 09 Apr at a (fixed) price of 0.200	\N
77	info	2022-04-09 06:25:02.422659	\N	4	\N	\N	\N	\N	An offer from you has been cancelled because the maturity date is in the past.	\N
78	system	2022-10-07 00:22:56.048185	\N	1	\N	\N	\N	\N	Database setup run.	\N
79	new_account	2023-02-04 00:36:09.345646	\N	1	\N	\N	\N	\N	New account 8 created: GitHub 124433287	\N
80	system	2024-12-21 17:08:34.028145	\N	1	\N	\N	\N	\N	Database setup run.	\N
81	system	2024-12-21 17:30:05.28723	\N	1	\N	\N	\N	\N	Database setup run.	\N
82	system	2024-12-21 17:32:37.963873	\N	1	\N	\N	\N	\N	Database setup run.	\N
83	system	2024-12-23 00:33:39.375081	\N	1	\N	\N	\N	\N	Issue created: https://github.com/pinfactory/pinfactory/issues/18	\N
84	system	2024-12-23 18:58:53.671664	\N	1	\N	\N	\N	\N	Issue updated: https://github.com/pinfactory/pinfactory/issues/18	\N
85	offer_created	2024-12-23 19:00:04.050463	\N	2	16	f	167	600	Offer made: 600 units of UNFIXED on Fix webhook secrets handling (18) with maturity 75 at 28 Dec at a (fixed) price of 0.167	\N
86	offer_cancelled	2024-12-23 19:02:43.568244	\N	2	16	\N	167	600	Offer cancelled: 600 units of UNFIXED on Fix webhook secrets handling (18) with maturity 75 at 28 Dec at a (fixed) price of 0.167	\N
87	offer_created	2024-12-23 19:03:16.841235	\N	2	16	f	167	600	Offer made: 600 units of UNFIXED on Fix webhook secrets handling (18) with maturity 75 at 28 Dec at a (fixed) price of 0.167	\N
88	system	2024-12-24 18:45:49.445369	\N	1	\N	\N	\N	\N	Database setup run.	\N
89	system	2024-12-24 18:47:23.431517	\N	1	\N	\N	\N	\N	Database setup run.	\N
90	system	2024-12-24 18:49:03.422873	\N	1	\N	\N	\N	\N	Database setup run.	\N
91	system	2024-12-24 18:52:25.821788	\N	1	\N	\N	\N	\N	Database setup run.	\N
92	system	2024-12-24 18:53:51.29213	\N	1	\N	\N	\N	\N	Database setup run.	\N
93	system	2024-12-24 18:58:33.197803	\N	1	\N	\N	\N	\N	Database setup run.	\N
94	new_account	2024-12-24 19:17:59.996449	\N	1	\N	\N	\N	\N	New account 9 created: local 1001	\N
95	new_account	2024-12-24 19:43:30.516071	\N	1	\N	\N	\N	\N	New account 9 created: local 1001	\N
96	offer_created	2024-12-24 19:43:30.520107	\N	9	21	f	900	10	Offer made: 10 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.900	\N
97	new_account	2024-12-24 19:44:32.769901	\N	1	\N	\N	\N	\N	New account 9 created: local 1001	\N
98	offer_created	2024-12-24 19:44:32.773893	\N	9	21	f	900	10	Offer made: 10 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.900	\N
99	new_account	2024-12-24 20:43:05.316348	\N	1	\N	\N	\N	\N	New account 9 created: local 1001	\N
100	offer_created	2024-12-24 20:43:05.321395	\N	9	21	f	900	10	Offer made: 10 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.900	\N
101	new_account	2024-12-24 20:43:39.405657	\N	1	\N	\N	\N	\N	New account 9 created: local 1001	\N
102	offer_created	2024-12-24 20:43:39.409965	\N	9	21	f	900	10	Offer made: 10 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.900	\N
103	new_account	2024-12-24 20:44:38.6163	\N	1	\N	\N	\N	\N	New account 9 created: local 1001	\N
104	offer_created	2024-12-24 20:44:38.620441	\N	9	21	f	900	11	Offer made: 11 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.900	\N
145	system	2024-12-28 14:50:17.013625	\N	1	\N	\N	\N	\N	Database setup run.	\N
172	system	2025-09-26 00:30:50.965548	\N	1	\N	\N	\N	\N	Issue created: https://github.com/pinfactory/pinfactory/issues/42	\N
105	contract_created	2024-12-24 19:04:21.931868	\N	2	21	t	900	10	Contract formed: 10 units of FIXED Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.900	\N
106	contract_created	2024-12-24 19:04:21.931868	\N	9	21	f	900	10	Contract formed: 10 units of UNFIXED Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.900	\N
107	contract_created	2024-12-24 19:04:21.931868	\N	2	21	t	900	1	Contract formed: 1 units of FIXED Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.900	\N
108	contract_created	2024-12-24 19:04:21.931868	\N	9	21	f	900	1	Contract formed: 1 units of UNFIXED Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.900	\N
109	contract_created	2024-12-24 20:46:40.579422	\N	2	21	t	900	9	Contract formed: 9 units of FIXED Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.900	\N
110	contract_created	2024-12-24 20:46:40.579422	\N	9	21	f	900	9	Contract formed: 9 units of UNFIXED Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.900	\N
111	contract_created	2024-12-24 20:46:50.961623	\N	2	21	t	900	10	Contract formed: 10 units of FIXED Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.900	\N
112	contract_created	2024-12-24 20:46:50.961623	\N	9	21	f	900	10	Contract formed: 10 units of UNFIXED Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.900	\N
113	contract_created	2024-12-24 20:46:54.708003	\N	2	21	t	900	10	Contract formed: 10 units of FIXED Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.900	\N
114	contract_created	2024-12-24 20:46:54.708003	\N	9	21	f	900	10	Contract formed: 10 units of UNFIXED Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.900	\N
115	contract_created	2024-12-24 20:46:58.388679	\N	2	21	t	900	11	Contract formed: 11 units of FIXED Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.900	\N
116	contract_created	2024-12-24 20:46:58.388679	\N	9	21	f	900	11	Contract formed: 11 units of UNFIXED Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.900	\N
117	new_account	2024-12-24 20:47:19.960561	\N	1	\N	\N	\N	\N	New account 9 created: local 1001	\N
118	offer_created	2024-12-24 20:47:19.964704	\N	9	21	f	800	11	Offer made: 11 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.800	\N
119	contract_created	2024-12-24 20:47:02.969822	\N	2	21	t	800	11	Contract formed: 11 units of FIXED Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.800	\N
120	contract_created	2024-12-24 20:47:02.969822	\N	9	21	f	800	11	Contract formed: 11 units of UNFIXED Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.800	\N
121	system	2024-12-24 20:51:25.621221	\N	1	\N	\N	\N	\N	Database setup run.	\N
122	offer_cancelled	2024-12-25 00:08:33.232383	\N	2	16	\N	167	600	Offer cancelled: 600 units of UNFIXED on Fix webhook secrets handling (18) with maturity 75 at 28 Dec at a (fixed) price of 0.167	\N
123	new_account	2024-12-25 15:35:33.794426	\N	1	\N	\N	\N	\N	New account 9 created: local 1001	\N
124	offer_created	2024-12-25 15:35:33.798425	\N	9	21	f	800	11	Offer made: 11 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.800	\N
125	new_account	2024-12-25 15:36:06.305534	\N	1	\N	\N	\N	\N	New account 9 created: local 1001	\N
126	offer_created	2024-12-25 15:36:06.309666	\N	9	21	f	800	11	Offer made: 11 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.800	\N
127	new_account	2024-12-25 15:37:03.287169	\N	1	\N	\N	\N	\N	New account 9 created: local 1001	\N
128	system	2024-12-26 00:43:07.716538	\N	1	\N	\N	\N	\N	Issue updated: https://github.com/pinfactory/pinfactory/issues/18	\N
129	system	2024-12-26 16:00:33.805014	\N	1	\N	\N	\N	\N	Issue updated: https://github.com/pinfactory/pinfactory/issues/18	\N
130	system	2024-12-26 16:11:55.190331	\N	1	\N	\N	\N	\N	Database setup run.	\N
131	system	2024-12-26 16:12:21.591215	\N	1	\N	\N	\N	\N	Issue updated: https://github.com/pinfactory/pinfactory/issues/18	\N
132	contract_created	2024-12-26 16:32:41.823326	\N	2	21	t	800	11	Contract formed: 11 units of FIXED Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.800	\N
133	contract_created	2024-12-26 16:32:41.823326	\N	9	21	f	800	11	Contract formed: 11 units of UNFIXED Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.800	\N
134	contract_created	2024-12-26 16:32:52.318773	\N	2	21	t	800	11	Contract formed: 11 units of FIXED Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.800	\N
135	contract_created	2024-12-26 16:32:52.318773	\N	9	21	f	800	11	Contract formed: 11 units of UNFIXED Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.800	\N
138	offer_created	2024-12-27 16:16:14.533742	\N	2	38	f	100	100	Offer made: 100 units of UNFIXED on Security review. (11) with maturity 77 at 25 Jan 2025 at a (fixed) price of 0.100	\N
146	new_account	2024-12-28 16:17:23.567005	\N	1	\N	\N	\N	\N	New account 9 created: local 1001	\N
147	offer_created	2024-12-28 16:17:23.570886	\N	9	21	f	860	10	Offer made: 10 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan 2025 at a (fixed) price of 0.860	\N
148	system	2024-12-28 16:38:03.681693	\N	1	\N	\N	\N	\N	Database setup run.	\N
149	new_account	2025-01-05 01:54:19.151682	\N	1	\N	\N	\N	\N	New account 10 created: GitHub 10239434	\N
152	system	2025-01-13 05:17:05.924675	\N	1	\N	\N	\N	\N	Database setup run.	\N
153	new_account	2025-01-18 00:36:27.406384	\N	1	\N	\N	\N	\N	New account 11 created: GitHub 67113663	\N
163	contract_resolved	2025-02-08 13:31:22.451384	\N	11	43	t	0	150	Contract resolved: FAQ (26) with maturity 78 at 08 Feb for a payout of 0 tokens	\N
164	contract_resolved	2025-02-08 13:31:22.451384	\N	2	43	f	1000	145	Contract resolved: FAQ (26) with maturity 78 at 08 Feb for a payout of 145 tokens	\N
173	system	2025-10-02 14:05:55.495157	\N	1	\N	\N	\N	\N	Database setup run.	\N
175	new_account	2025-10-06 00:51:15.021609	\N	1	\N	\N	\N	\N	New account 13 created: local 1000	\N
176	new_account	2025-10-06 13:06:22.352374	\N	1	\N	\N	\N	\N	New account 13 created: local 1000	\N
139	system	2024-12-28 14:42:40.774474	\N	1	\N	\N	\N	\N	Issue created: https://github.com/pinfactory/pinfactory/issues/26	\N
143	contract_created	2024-12-28 14:44:47.753624	\N	2	40	t	100	100	Contract formed: 100 units of FIXED FAQ (26) with maturity 77 at 25 Jan 2025 at a (fixed) price of 0.100	\N
144	contract_created	2024-12-28 14:44:47.753624	\N	9	40	f	100	100	Contract formed: 100 units of UNFIXED FAQ (26) with maturity 77 at 25 Jan 2025 at a (fixed) price of 0.100	\N
150	offer_cancelled	2025-01-11 06:25:01.641058	\N	9	21	f	860	10	Offer cancelled: 10 units of UNFIXED on Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan at a (fixed) price of 0.860	\N
151	info	2025-01-11 06:25:01.641058	\N	9	\N	\N	\N	\N	An offer from you has been cancelled because the maturity date is in the past.	\N
154	offer_cancelled	2025-01-25 06:25:01.695547	\N	2	38	f	100	100	Offer cancelled: 100 units of UNFIXED on Security review. (11) with maturity 77 at 25 Jan at a (fixed) price of 0.100	\N
155	info	2025-01-25 06:25:01.695547	\N	2	\N	\N	\N	\N	An offer from you has been cancelled because the maturity date is in the past.	\N
165	new_account	2025-03-03 00:11:50.753795	\N	1	\N	\N	\N	\N	New account 12 created: GitHub 121135798	\N
140	new_account	2024-12-28 14:47:01.686154	\N	1	\N	\N	\N	\N	New account 9 created: local 1001	\N
156	offer_created	2025-01-27 01:25:11.390231	\N	11	43	t	333	150	Offer made: 150 units of FIXED on FAQ (26) with maturity 78 at 08 Feb at a (fixed) price of 0.333	\N
157	contract_created	2025-01-27 21:06:17.167075	\N	11	43	t	333	150	Contract formed: 150 units of FIXED FAQ (26) with maturity 78 at 08 Feb at a (fixed) price of 0.333	\N
158	contract_created	2025-01-27 21:06:17.167075	\N	2	43	f	333	150	Contract formed: 150 units of UNFIXED FAQ (26) with maturity 78 at 08 Feb at a (fixed) price of 0.333	\N
159	contract_resolved	2025-01-27 21:33:45.872762	\N	2	40	t	0	100	Contract resolved: FAQ (26) with maturity 77 at 25 Jan for a payout of 0 tokens	\N
160	contract_resolved	2025-01-27 21:33:45.872762	\N	9	40	f	1000	99	Contract resolved: FAQ (26) with maturity 77 at 25 Jan for a payout of 99 tokens	\N
161	contract_resolved	2025-01-27 21:33:55.670056	\N	2	21	t	0	84	Contract resolved: Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan for a payout of 0 tokens	\N
162	contract_resolved	2025-01-27 21:33:55.670056	\N	9	21	f	1000	77	Contract resolved: Add CSS to keep "Estimated fee" elements on the same line (15) with maturity 76 at 11 Jan for a payout of 77 tokens	\N
166	offer_created	2025-07-22 22:32:03.812422	\N	2	48	t	100	100	Offer made: 100 units of FIXED on Microsoft Windows and VS Code instructions in README.md (28) with maturity 91 at 09 Aug at a (fixed) price of 0.100	\N
167	offer_created	2025-07-22 22:34:08.995982	\N	2	49	t	100	100	Offer made: 100 units of FIXED on Security review. (11) with maturity 91 at 09 Aug at a (fixed) price of 0.100	\N
141	new_account	2024-12-28 14:47:10.528309	\N	1	\N	\N	\N	\N	New account 9 created: local 1001	\N
142	offer_created	2024-12-28 14:47:10.531829	\N	9	40	f	100	100	Offer made: 100 units of UNFIXED on FAQ (26) with maturity 77 at 25 Jan 2025 at a (fixed) price of 0.100	\N
168	offer_cancelled	2025-08-09 06:25:01.87165	\N	2	48	t	100	100	Offer cancelled: 100 units of FIXED on Microsoft Windows and VS Code instructions in README.md (28) with maturity 91 at 09 Aug at a (fixed) price of 0.100	\N
169	info	2025-08-09 06:25:01.87165	\N	2	\N	\N	\N	\N	An offer from you has been cancelled because the maturity date is in the past.	\N
170	offer_cancelled	2025-08-09 06:25:01.876385	\N	2	49	t	100	100	Offer cancelled: 100 units of FIXED on Security review. (11) with maturity 91 at 09 Aug at a (fixed) price of 0.100	\N
171	info	2025-08-09 06:25:01.876385	\N	2	\N	\N	\N	\N	An offer from you has been cancelled because the maturity date is in the past.	\N
136	system	2024-12-26 19:15:03.595954	\N	1	\N	\N	\N	\N	Database setup run.	\N
174	system	2025-10-04 17:52:05.9669	\N	1	\N	\N	\N	\N	Database setup run.	\N
177	new_account	2025-10-06 15:20:04.998926	\N	1	\N	\N	\N	\N	New account 15 created: local 31337	\N
178	new_account	2025-10-06 15:20:04.998926	\N	1	\N	\N	\N	\N	New account 16 created: local 31337	\N
179	new_account	2025-10-06 15:20:04.998926	\N	1	\N	\N	\N	\N	New account 17 created: local 31337	\N
180	new_account	2025-10-06 15:20:04.998926	\N	1	\N	\N	\N	\N	New account 18 created: local 31337	\N
181	new_account	2025-10-06 15:20:05.018464	\N	1	\N	\N	\N	\N	New account 19 created: local 5100601	\N
\.


--
-- Data for Name: offer; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.offer (id, account, created, contract_type, side, price, quantity, all_or_nothing, expires) FROM stdin;
\.


--
-- Data for Name: position; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."position" (id, account, created, modified, contract_type, basis, quantity) FROM stdin;
\.


--
-- Data for Name: project; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.project (id, url, owner, webhook_secret) FROM stdin;
1	https://github.com/pinfactory/pinfactory	1	\N
\.


--
-- Data for Name: userid; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.userid (id, account, host, sub, username, profile) FROM stdin;
1	2	GitHub	48007	dmarti	https://github.com/dmarti
2	3	GitHub	63842643	Adegbite1999	https://github.com/Adegbite1999
3	4	GitHub	68496788	Ephraim-nonso	https://github.com/Ephraim-nonso
4	5	GitHub	41296318	nahmii-john	https://github.com/nahmii-john
5	6	GitHub	9271195	HDauven	https://github.com/HDauven
6	7	GitHub	7009200	MariusTH	https://github.com/MariusTH
7	8	GitHub	124433287	f198200100	https://github.com/f198200100
28	18	local	31337	agent_31337	http://localhost/agent/31337
29	19	local	5100601	agent_5100601	http://localhost/agent/5100601
8	9	local	1001	trading bot	https://market.pinfactory.org/bots
21	10	GitHub	10239434	mickbransfield	https://github.com/mickbransfield
22	11	GitHub	67113663	jimmyceroneii	https://github.com/jimmyceroneii
23	12	GitHub	121135798	ODO15	https://github.com/ODO15
24	13	local	1000	agent_1000	http://localhost/agent/1000
\.


--
-- Name: account_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.account_id_seq', 19, true);


--
-- Name: contract_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.contract_type_id_seq', 49, true);


--
-- Name: issue_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.issue_id_seq', 35, true);


--
-- Name: maturity_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.maturity_id_seq', 98, true);


--
-- Name: message_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.message_id_seq', 181, true);


--
-- Name: offer_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.offer_id_seq', 29, true);


--
-- Name: position_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.position_id_seq', 8, true);


--
-- Name: project_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.project_id_seq', 24, true);


--
-- Name: userid_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.userid_id_seq', 29, true);


--
-- Name: account account_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.account
    ADD CONSTRAINT account_pkey PRIMARY KEY (id);


--
-- Name: contract_type contract_type_issue_matures_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contract_type
    ADD CONSTRAINT contract_type_issue_matures_key UNIQUE (issue, matures);


--
-- Name: contract_type contract_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contract_type
    ADD CONSTRAINT contract_type_pkey PRIMARY KEY (id);


--
-- Name: issue issue_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issue
    ADD CONSTRAINT issue_pkey PRIMARY KEY (id);


--
-- Name: issue issue_url_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issue
    ADD CONSTRAINT issue_url_key UNIQUE (url);


--
-- Name: maturity maturity_matures_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.maturity
    ADD CONSTRAINT maturity_matures_key UNIQUE (matures);


--
-- Name: maturity maturity_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.maturity
    ADD CONSTRAINT maturity_pkey PRIMARY KEY (id);


--
-- Name: message message_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.message
    ADD CONSTRAINT message_pkey PRIMARY KEY (id);


--
-- Name: offer offer_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.offer
    ADD CONSTRAINT offer_pkey PRIMARY KEY (id);


--
-- Name: position position_account_contract_type_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."position"
    ADD CONSTRAINT position_account_contract_type_key UNIQUE (account, contract_type);


--
-- Name: position position_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."position"
    ADD CONSTRAINT position_pkey PRIMARY KEY (id);


--
-- Name: project project_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project
    ADD CONSTRAINT project_pkey PRIMARY KEY (id);


--
-- Name: project project_url_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project
    ADD CONSTRAINT project_url_key UNIQUE (url);


--
-- Name: userid userid_host_profile_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userid
    ADD CONSTRAINT userid_host_profile_key UNIQUE (host, profile);


--
-- Name: userid userid_host_sub_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userid
    ADD CONSTRAINT userid_host_sub_key UNIQUE (host, sub);


--
-- Name: userid userid_host_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userid
    ADD CONSTRAINT userid_host_username_key UNIQUE (host, username);


--
-- Name: userid userid_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userid
    ADD CONSTRAINT userid_pkey PRIMARY KEY (id);


--
-- Name: offer check_offer_date; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER check_offer_date BEFORE INSERT ON public.offer FOR EACH ROW EXECUTE FUNCTION public.check_contract_type_maturity();


--
-- Name: position check_position_date; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER check_position_date BEFORE INSERT ON public."position" FOR EACH ROW EXECUTE FUNCTION public.check_contract_type_maturity();


--
-- Name: issue update_issue_modified; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_issue_modified BEFORE UPDATE ON public.issue FOR EACH ROW EXECUTE FUNCTION public.update_modified_column();


--
-- Name: position update_position_modified; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_position_modified BEFORE UPDATE ON public."position" FOR EACH ROW EXECUTE FUNCTION public.update_modified_column();


--
-- Name: contract_type contract_type_issue_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contract_type
    ADD CONSTRAINT contract_type_issue_fkey FOREIGN KEY (issue) REFERENCES public.issue(id);


--
-- Name: contract_type contract_type_matures_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.contract_type
    ADD CONSTRAINT contract_type_matures_fkey FOREIGN KEY (matures) REFERENCES public.maturity(id);


--
-- Name: issue issue_project_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issue
    ADD CONSTRAINT issue_project_fkey FOREIGN KEY (project) REFERENCES public.project(id);


--
-- Name: message message_contract_type_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.message
    ADD CONSTRAINT message_contract_type_fkey FOREIGN KEY (contract_type) REFERENCES public.contract_type(id);


--
-- Name: message message_recipient_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.message
    ADD CONSTRAINT message_recipient_fkey FOREIGN KEY (recipient) REFERENCES public.account(id);


--
-- Name: offer offer_account_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.offer
    ADD CONSTRAINT offer_account_fkey FOREIGN KEY (account) REFERENCES public.account(id);


--
-- Name: offer offer_contract_type_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.offer
    ADD CONSTRAINT offer_contract_type_fkey FOREIGN KEY (contract_type) REFERENCES public.contract_type(id);


--
-- Name: position position_account_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."position"
    ADD CONSTRAINT position_account_fkey FOREIGN KEY (account) REFERENCES public.account(id);


--
-- Name: position position_contract_type_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."position"
    ADD CONSTRAINT position_contract_type_fkey FOREIGN KEY (contract_type) REFERENCES public.contract_type(id);


--
-- Name: project project_owner_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.project
    ADD CONSTRAINT project_owner_fkey FOREIGN KEY (owner) REFERENCES public.account(id);


--
-- Name: userid userid_account_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.userid
    ADD CONSTRAINT userid_account_fkey FOREIGN KEY (account) REFERENCES public.account(id);


--
-- PostgreSQL database dump complete
--

