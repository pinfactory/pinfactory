--SQL database functions. These are only run when we deploy first time to populate
--the database. Triggers are the exception -- they run whenever a change happens.
--It is run when db_setup.sh is called (from restart.sh).

--Database trigger: Keeps column called modified set to time and date at the
--current time of calling this function.
--NEW is a database record holding the info we are updating.
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.modified = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Do not allow an offer to be made after the contract matures.
-- Declaring not_after as a variable of type TIMESTAMP
CREATE OR REPLACE FUNCTION check_contract_type_maturity()
RETURNS TRIGGER AS $$
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
$$ language 'plpgsql';

-- Accounts
CREATE TABLE IF NOT EXISTS account (
	id SERIAL PRIMARY KEY,
	enabled BOOLEAN NOT NULL DEFAULT true,
	system BOOLEAN NOT NULL DEFAULT false, -- system account
	banker BOOLEAN NOT NULL DEFAULT false, -- create tokens
	oracle BOOLEAN NOT NULL DEFAULT false, -- resolve contracts
	balance BIGINT NOT NULL CHECK (balance >= 0), /* millitokens */
	min_balance BIGINT NOT NULL DEFAULT 0 -- Can't bring balance below this amount by transfers.
					      -- Handle "free" tokens allocated to users for investing.
);

-- User identifiers.  The "sub" column is the unique
-- identifer from the OAuth host.
-- Contains the info to get you logged in. And a pointer to your account.
-- Multiple user ids (say you log in with different ids) can reference the same
-- account.
DO $$ BEGIN
	CREATE TYPE host_class AS ENUM ('GitHub', 'local');
EXCEPTION
	WHEN duplicate_object THEN null;
END $$;
CREATE TABLE IF NOT EXISTS userid (
	id SERIAL PRIMARY KEY,
	account INT REFERENCES account(id),
	host host_class NOT NULL,
	sub TEXT NOT NULL,
	username TEXT NOT NULL,
	profile TEXT NOT NULL,
	UNIQUE (host, sub),
	UNIQUE (host, username),
	UNIQUE (host, profile)
);

-- issues (on which trades can be made)
CREATE TABLE IF NOT EXISTS issue (
	id SERIAL PRIMARY KEY,
	url TEXT UNIQUE NOT NULL,
	title TEXT, /* NULL if no title sent by the webhook */
	created TIMESTAMP NOT NULL DEFAULT NOW(),
	modified TIMESTAMP NOT NULL DEFAULT NOW(),
	updated TIMESTAMP,
	tracker_status TEXT,                 /* raw status as obtained from the BTS. NULL = not fetched yet. */
	open BOOLEAN NOT NULL DEFAULT true,
	fixed BOOLEAN NOT NULL DEFAULT false /* used to resolve contracts */
);

-- A trigger is a procedure that runs inside the database when a certain query
-- happens. Here update modified.
DROP TRIGGER IF EXISTS update_issue_modified ON issue;
CREATE TRIGGER update_issue_modified BEFORE UPDATE ON issue FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

-- possible expiration dates for a contract
-- enforces maturity dates that are already in the database
CREATE TABLE IF NOT EXISTS maturity (
	id SERIAL PRIMARY KEY,
	matures TIMESTAMP NOT NULL UNIQUE
);

-- a contract type has an issue and an expiration date (maturity id). Can only
-- point to issues and maturity ids that exist. Table is created but not yet populated.
CREATE TABLE IF NOT EXISTS contract_type (
	id SERIAL PRIMARY KEY,
	issue INT REFERENCES issue(id),
	matures INT REFERENCES maturity(id),
        UNIQUE (issue, matures)
);

-- Open unmatched offers. We only track the quantity that is
-- unmatched, not part of a contract
CREATE TABLE IF NOT EXISTS offer (
	id SERIAL PRIMARY KEY,
	account INT REFERENCES account(id),
	created TIMESTAMP NOT NULL DEFAULT NOW(),
	contract_type INT REFERENCES contract_type(id),
	side BOOLEAN NOT NULL, /* true fixed false unfixed */
	price BIGINT NOT NULL CHECK (price >= 0 AND price <= 1000), /* price of the "fixed" side in millitokens */
	quantity BIGINT NOT NULL CHECK (quantity > 0), /* units, worth 1000 millitokens to the winner */
	all_or_nothing BOOL NOT NULL DEFAULT false
);
DROP TRIGGER IF EXISTS check_offer_date ON offer;
CREATE TRIGGER check_offer_date BEFORE INSERT ON offer FOR EACH ROW EXECUTE PROCEDURE check_contract_type_maturity();

-- view on offers. Used in several related queries. Lets us select from this
-- view at the application level since this is a view used often.
-- maturity and issue objects exist in their own tables. Here in this view we join
-- that info with contract. Note that contract_type table just references the
-- ids but here we need more info from the maturity and issue objects.
DROP VIEW IF EXISTS offer_overview;
CREATE VIEW offer_overview AS
	SELECT maturity.id AS maturity, maturity.matures,
	contract_type.id AS contract_type,
	issue.id AS issue, issue.url, issue.title,
	offer.id, offer.account AS account, offer.side, offer.price, offer.quantity, offer.created, offer.all_or_nothing
	FROM maturity JOIN contract_type ON maturity.id = contract_type.matures
	INNER JOIN issue ON issue.id = contract_type.issue
	INNER JOIN offer ON contract_type.id = offer.contract_type;

-- positions held.  Cannot be cancelled, but can be
-- offset by taking the other side.
-- modified refers to selling out or offsetting part of your position, thus it
-- relates to the number of units modified.
-- basis refers to the original price of this position (need to store this to
-- calculate the oracle fee)
--An account can only have one position given a contract type. However a contract_type
--can have multiple different accounts, for a given position. In the UI these
--are displayed as different offers/contracts (equivalent to piling on). 
CREATE TABLE IF NOT EXISTS position (
	id SERIAL PRIMARY KEY,
	account INT REFERENCES account(id),
	created TIMESTAMP NOT NULL DEFAULT NOW(),
	modified TIMESTAMP NOT NULL DEFAULT NOW(),
	contract_type INT REFERENCES contract_type(id),
	basis BIGINT NOT NULL CHECK (basis >= 0),       /* cost basis for this position in millitokens */
	quantity BIGINT NOT NULL CHECK (quantity != 0), /* units, worth 1000 millitokens to the winner *
							 * positive: FIXED.                            *
							 * negative: UNFIXED.                          */
	UNIQUE (account, contract_type)
);
DROP TRIGGER IF EXISTS check_position_date ON position;
CREATE TRIGGER check_position_date BEFORE INSERT ON position FOR EACH ROW EXECUTE PROCEDURE check_contract_type_maturity();
DROP TRIGGER IF EXISTS update_position_modified ON position;
CREATE TRIGGER update_position_modified BEFORE UPDATE ON position FOR EACH ROW EXECUTE PROCEDURE update_modified_column();

-- messages
-- message class enumerates the different kinds of messages.
DO $$ BEGIN
	CREATE TYPE message_class AS ENUM('system', 'info', 'offer_created', 'offer_cancelled',
				          'contract_created', 'position_covered', 'contract_resolved',
				          'new_account');
EXCEPTION
	WHEN duplicate_object THEN null;
END $$;
CREATE TABLE IF NOT EXISTS message (
	id SERIAL PRIMARY KEY,
	class message_class NOT NULL,
	created TIMESTAMP NOT NULL DEFAULT NOW(),
	delivered TIMESTAMP, /* NULL: not delivered */
	recipient INT REFERENCES account(id),
	contract_type INT REFERENCES contract_type(id),
	side BOOLEAN,
	price BIGINT,
	quantity BIGINT,
	message TEXT NOT NULL
);

-- For populating messages
-- Note: table is actually persisted to the database. Tables are concepts that
-- have integrity with correctness checks, normalized, etc. A view is a convenient
-- query of the database that brings together a bunch of info that is typically
-- needed together.
DROP VIEW IF EXISTS message_overview;
CREATE VIEW message_overview AS
	SELECT maturity.id AS maturity, maturity.matures,
	issue.id AS issue, issue.url, issue.title,
	message.id, message.class, message.created, message.delivered, message.recipient, message.contract_type,
	message.side, message.price, message.quantity, message.message
	FROM message LEFT OUTER JOIN contract_type ON contract_type.id = message.contract_type
	LEFT OUTER JOIN maturity ON maturity.id = contract_type.matures
	LEFT OUTER JOIN issue ON issue.id = contract_type.issue;

-- For summary stats
DROP VIEW IF EXISTS ticker;
CREATE VIEW ticker AS
	SELECT DISTINCT maturity.id AS maturity, maturity.matures,
	contract_type.id AS contract_type,
	issue.id AS issue, issue.url, issue.title,
	message.id, message.class, message.side, message.price, message.quantity, message.created
	FROM maturity JOIN contract_type ON maturity.id = contract_type.matures
	INNER JOIN issue ON issue.id = contract_type.issue
	INNER JOIN message ON contract_type.id = message.contract_type
	WHERE side IS NOT NULL AND price > 0;

-- create the system account if it does not exist
INSERT INTO account (system, balance) SELECT true, 0
	WHERE NOT EXISTS ( SELECT id FROM account WHERE system = true);

-- all done
INSERT INTO message (class, recipient, message)
	VALUES ('system', (SELECT id FROM account WHERE system = true),
	'Database setup run.');

SELECT * FROM message;
