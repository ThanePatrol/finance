-- human readable balance
alter table transactions
add column balance text;

alter table transactions
add column user text;

-- original data for more context
alter table transactions
add column original_record text;
