# Ledger — acceptance criteria

A single account tracks a balance in integer cents. `charge` decreases the
balance; `refund` increases it, and can never give back more than was
originally charged. Every charge and every refund carries an idempotency
key (a unique tag per request) so a retried request never gets applied
twice.

## Charge

WHEN a charge is submitted with an idempotency key that has not been used
before, THE SYSTEM SHALL apply the charge — deduct the charge amount from
the account balance and record it under that key.

WHEN a charge is submitted with an idempotency key that has already been
used, THE SYSTEM SHALL NOT apply the charge again — the account balance
and the original charge record are unaffected.

## Refund

WHEN a refund is submitted for a given charge ID, with a refund idempotency
key that has not been used before, and the refund amount (combined with
any refunds already applied to that charge) does not exceed the original
charge amount, THE SYSTEM SHALL apply the refund — credit the account
balance and reduce that charge's remaining refundable amount.

WHEN a refund would cause the total refunded against a charge to exceed the
original charge amount, THE SYSTEM SHALL reject it.

WHEN a refund is submitted with an idempotency key that has already been
used, THE SYSTEM SHALL NOT apply the refund again — the account balance
and the original refund record are unaffected.

## Balance

WHEN the account balance is queried, THE SYSTEM SHALL reflect the sum of
all applied charges (each counted once, regardless of duplicate
submissions) minus all applied refunds (each counted once, regardless of
duplicate submissions).
