"""Conservative correlation of already validated offline transport records."""


CORRELATION_EXPLICIT = "CORRELATION_EXPLICIT"
CORRELATION_AMBIGUOUS = "CORRELATION_AMBIGUOUS"
CORRELATION_UNAVAILABLE = "CORRELATION_UNAVAILABLE"


class Correlator:
    def __init__(self):
        self.pending = {}
        self.ambiguous = set()
        self.outcomes = []
        self.counts = {"matched_pairs": 0, "orphan_replies": 0,
                       "uncorrelated_records": 0, "ambiguous_correlations": 0,
                       "invalidated_requests": 0}

    @staticmethod
    def generation(record):
        return (record.get("capture_id"), record["capture_generation"],
                record.get("boot_generation"))

    def key(self, record):
        correlation = record.get("correlation")
        if not correlation or record.get("request_id") is None:
            return None
        if record.get("endpoint") is None or record.get("channel") is None:
            return None
        identity = record["request_id"]
        return (self.generation(record), record.get("lifetime_generation"),
                record["asc"], record["endpoint"], record["channel"],
                record["service"], correlation["scope"],
                type(identity).__name__, identity)

    def feed(self, record, gap=False):
        outcome = {"status": CORRELATION_UNAVAILABLE, "reason": "not an exchange",
                   "capture_generation": record["capture_generation"],
                   "sequence": record.get("sequence", record.get("record_index"))}
        self.outcomes.append(outcome)
        if gap or record["loss_state"]["status"] != "none":
            invalidated = [key for key in self.pending if key[0] == self.generation(record)]
            self.counts["invalidated_requests"] += len(invalidated)
            for key in invalidated:
                self.pending.pop(key)["outcome"].update(reason="capture loss before reply")
        if record["kind"] not in ("request", "reply"):
            return outcome
        key = self.key(record)
        if key is None or record["loss_state"]["status"] != "none":
            outcome["reason"] = "missing explicit scope/identity or incomplete record"
            self.counts["uncorrelated_records"] += 1
        elif key in self.ambiguous:
            outcome.update(status=CORRELATION_AMBIGUOUS, reason="ambiguous ID namespace")
            self.counts["uncorrelated_records"] += 1
        elif record["kind"] == "request":
            if key in self.pending:
                previous = self.pending.pop(key)
                previous["outcome"].update(status=CORRELATION_AMBIGUOUS, reason="duplicate in-flight ID")
                outcome.update(status=CORRELATION_AMBIGUOUS, reason="duplicate in-flight ID")
                self.ambiguous.add(key)
                self.counts["ambiguous_correlations"] += 1
            else:
                outcome["reason"] = "reply not observed"
                self.pending[key] = {"direction": record["direction"], "outcome": outcome,
                                     "evidence": record["correlation"]["evidence"]}
        elif key not in self.pending:
            outcome["reason"] = "request not observed"
            self.counts["orphan_replies"] += 1
        else:
            previous = self.pending.pop(key)
            if (previous["direction"] == record["direction"] or
                    previous["evidence"] != record["correlation"]["evidence"]):
                previous["outcome"].update(status=CORRELATION_AMBIGUOUS, reason="direction/contract mismatch")
                outcome.update(status=CORRELATION_AMBIGUOUS, reason="direction/contract mismatch")
                self.ambiguous.add(key)
                self.counts["ambiguous_correlations"] += 1
            else:
                previous["outcome"].update(status=CORRELATION_EXPLICIT, reason="explicit scoped pair",
                                           peer_sequence=outcome["sequence"])
                outcome.update(status=CORRELATION_EXPLICIT, reason="explicit scoped pair",
                               peer_sequence=previous["outcome"]["sequence"])
                self.counts["matched_pairs"] += 1
        return outcome

    def summary(self):
        return dict(self.counts, pending_requests=len(self.pending))