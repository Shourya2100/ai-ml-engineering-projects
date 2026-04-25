import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.chunker import chunk_document


TWO_SECTION_DOC = """## Database Outage

When the primary database goes down, the on-call engineer should immediately check
the CloudWatch dashboard for error spikes. Look for connection timeout errors and
elevated latency in the database metrics panel. If the primary is unresponsive,
initiate a failover to the read replica by following the steps in the runbook.
Contact the database team lead if failover does not resolve within 15 minutes.
Monitor the recovery dashboard and verify all services reconnect automatically.
Document the timeline in the incident channel. After recovery, schedule a
post-incident review within 48 hours. Keep stakeholders informed with status
updates every 30 minutes during the outage. Preserve all logs for root cause analysis.
Ensure the monitoring alerts are re-enabled after the failover completes. Verify that
all application connection pools have reconnected and are healthy. Run the automated
integration test suite against the recovered database to confirm data integrity.
Check the replication lag between the new primary and remaining replicas. Update the
service status page to reflect the current operational state. Notify downstream teams
that depend on the database about the recovery timeline and any data implications.
Review the automated backup schedule to ensure the next backup captures the post-recovery
state. Schedule a blameless post-mortem meeting within one business day.

## Payment Service Failure

If Stripe webhooks stop arriving, first verify the webhook endpoint is reachable
from the Stripe dashboard. Check the webhook signing secret has not rotated.
Review the payment service logs for any deserialization errors. If the endpoint
is healthy but events are missing, check the Stripe event delivery dashboard for
failed attempts. Manually replay any failed events from the last 24 hours using
the Stripe CLI. Escalate to the payments team lead if the issue persists beyond
30 minutes. Ensure all refund operations are paused until webhook delivery is
confirmed restored. Run the reconciliation job to verify no payments were lost
during the outage window. Update the incident channel with resolution status.
Verify that subscription renewal events are processing correctly after recovery.
Check the payment idempotency keys to ensure no duplicate charges were created.
Review the dead letter queue for any events that failed processing during the outage.
Confirm that all pending refunds have been re-queued and are processing normally.
Update the finance team on any transactions that may need manual reconciliation.
Run the end-of-day settlement report to verify all payment totals are accurate.
Document all manual interventions performed during the incident for audit purposes.
""".strip()

SHORT_DOC = "This is a very short document that fits in one chunk."

EMPTY_DOC = "   "


def test_two_sections_produce_multiple_chunks():
    chunks = chunk_document(TWO_SECTION_DOC, "incident-response.md")
    assert len(chunks) >= 2
    assert all(c["filename"] == "incident-response.md" for c in chunks)


def test_overlap_appears_at_start_of_second_chunk():
    chunks = chunk_document(TWO_SECTION_DOC, "incident-response.md", chunk_size=100, overlap=20)
    assert len(chunks) >= 2
    first_tail = chunks[0]["text"].split()[-10:]
    second_head = chunks[1]["text"].split()[:20]
    overlap_words = set(first_tail) & set(second_head)
    assert len(overlap_words) > 0, "Expected overlapping words between chunk 0 and chunk 1"


def test_short_document_returns_single_chunk():
    chunks = chunk_document(SHORT_DOC, "short.md")
    assert len(chunks) == 1
    assert chunks[0]["text"] == SHORT_DOC
    assert chunks[0]["chunk_index"] == 0


def test_empty_document_returns_empty_list():
    chunks = chunk_document(EMPTY_DOC, "empty.md")
    assert chunks == []


def test_chunk_id_format():
    chunks = chunk_document(TWO_SECTION_DOC, "incident-response.md")
    for i, chunk in enumerate(chunks):
        assert chunk["chunk_id"] == f"incident-response.md__chunk_{i}"
