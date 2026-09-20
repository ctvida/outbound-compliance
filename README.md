# outbound-compliance

The CAN-SPAM footer, the opt-out rule, the suppression rule and the daily send
cap, in one place, so that every engine that sends email states them the same way.

No engine owns this package and it imports no engine. That is the whole point:
marketing-engine and sales-engine each depend on it, neither depends on the
other, and a client who licenses one engine installs one small library rather
than the other product.

```
outbound-compliance @ git+https://github.com/ctvida/outbound-compliance@v0.1.0
```

Pin the same tag in every engine. Two engines on two tags send two different
footers, which is the failure this package exists to remove, so bump them
together or not at all. For local work on the package itself, install it
editable over the pinned copy (`make dev` in either engine).

```python
from outbound_compliance import compose, is_opt_out, is_suppressed, DAILY_SEND_CAP

body = compose(draft, {"name": ..., "title": ..., "company": ..., "postal_address": ...})
```

Pure functions only: no I/O, no clock, no database. Each engine keeps its own
store and passes rows in. Changing `FOOTER_TEMPLATE` changes what every engine
sends, which is why the wording lives here and not in either engine.

Email only. SMS is out of scope on purpose, see the module docstring.

    python -m pytest -q
