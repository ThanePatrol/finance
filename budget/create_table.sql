CREATE TABLE rent_payments (
	discord_id INTEGER,
	to_pay INTEGER, -- in cents
	paid INTEGER, -- in cents
	time_of_notice INTEGER -- time we initially sent a notification
);
