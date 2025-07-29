CREATE TABLE rent_payments (
	discord_id INTEGER,
	amount INTEGER, -- in cents. Negative for a rent notice. ie they owe money. Positive if they have paid money
	time INTEGER, -- time we sent a notification OR time we called the ubank API
	transaction_id TEXT -- empty string if it is our notice, else transaction ID of ubank
);

CREATE TABLE renter (
	name TEXT, -- legal name of renter
	discord_id INTEGER,
	channel_id INTEGER
);

-- Option 1:
-- storing all events as positive/negative and taking the sum
-- Pros:
-- Table is immutable, each insert event is independent of another
--
-- Cons:
-- Table always grows (not a big issue)
-- Need to scan the the entire table to get a result - eh
-- What happens if the amount does not equal exactly 0? - Just ignore if low else send notice
-- If we add to this daily we need to ensure we deduplicate the transactions, can't just keep adding ones that already exist in the table.

-- Option 2:
-- Store each notice as an individual occurrence. If paid, modify the amount to reflect what has paid
-- Pros:
-- Less rows
--
-- Cons:
-- Need to match the amount of to_pay and paid
-- Introduces more application logic, how to match ubank transaction to the right notice?
-- What if they pay less or more than what the amount they owe?
