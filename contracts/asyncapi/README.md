# Event contract

**Status:** empty starter — this application neither publishes nor consumes any messages, so
there is no boundary today for this contract to describe.

The directory exists although it is empty, and that is a choice between two ways of being
silent. A missing directory says "nobody thought about this"; a directory with the sentence
above says "this was checked, there is nothing to describe". The two states look identical in
a file tree and completely different to somebody who is adding the first queue.

This is not the same thing as a **non-goal**. Non-goals — the things this product knowingly
does not do — live in `spec/invariants.md` and bind every change. Having no events is not a
product decision but a statement of fact: the first feature that needs them fills this
directory and does not have to overturn anything.

## What goes in here when something does

A `.yaml` file in AsyncAPI 3.x, one per area, with the **compatibility mode in a header
comment** — before the first key, because an AsyncAPI document has no field of its own for it.

Delivery semantics are part of the contract rather than a deployment detail, and they require
three questions answered before the first message goes out:

- **How many times it arrives.** *At-least-once* by default; "exactly once" is a property the
  network does not have, and pretending it does ends in a double write at the receiver.
- **How a repeat is recognised.** An idempotency key **derived from the content**, never
  random: a key issued at send time is different on a retry, so it cannot tell a repeat from
  a new event.
- **Where what failed ends up.** A dead-letter queue after a fixed number of attempts. A
  message retried forever is a message that has stopped the stream.

The version then stands in two places and both carry weight: the document's `info.version`
and a `schema-version` header required on every message — the receiver reads the second one,
because it never sees the first.

Rules common to every boundary: [`contracts/README.md`](../README.md).
