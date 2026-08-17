import enum


class JobStatus(str, enum.Enum):
    """
    Lifecycle states for a job.

    queued      → just created, waiting for a worker to pick it up
    processing  → a worker has claimed it and is working on it
    completed   → worker finished successfully; result is populated
    failed      → worker encountered an error; error_message is populated
    cancelled   → user cancelled the job before a worker claimed it
    """

    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
