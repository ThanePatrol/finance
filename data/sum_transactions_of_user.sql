SELECT t.name, SUM(r.amount), t.discord_id FROM rent_payments as r
LEFT JOIN renter as t
ON r.discord_id = t.discord_id
GROUP BY r.discord_id;
