# Cleaning request upload integration

The cleaning form now owns its submission flow; it no longer uses `submitDemo`.
It shows pending/success/error states, disables editing and repeat submission while
pending, and retains the form and photos after failure. Retry reuses the same
Idempotency-Key until the user changes the form. Success resets the form only
after a receipt is returned. No percentage is displayed because fetch does not
provide upload progress.

## Backend dependency

There is currently no cleaning-request endpoint in Backend/app/api/v1/router.py.
Without configuration the cleaning page uses a local UI demo.
A valid submission resets the form and opens the shared success modal with a
standard confirmation copy and a local CLEAN-YYYYMMDD-XXXXXXXX tracking code.
Repair demos use REPAIR-YYYYMMDD-XXXXXXXX. The shared modal shows the entered
email, home and tracking buttons. These demo receipts are stored only in the
current page memory for the local tracking UI; reloading clears them. No
network request or backend persistence happens for demo submissions.
The user requested that demo labels be omitted from the UI; this remains a
frontend simulation until the backend endpoint is configured.
The transport adapter itself still rejects missing configuration. Setting the
endpoint switches the page to real submission and confirmation behavior.

Once implemented, set `VITE_CLEANING_REQUEST_URL` to the full endpoint URL in the
frontend environment and restart/rebuild Vite. The proposed contract below must
be implemented or the frontend adapter updated to the agreed backend contract:

- POST multipart/form-data: `clean_floor`, `clean_room`, `problem`, `work_type`
  (current Thai option label), optional `description` (at most 2,000 Unicode code points), `recipient_email`, repeated
  optional `image` fields (at most 5, JPEG/PNG/WebP, at most 5 MiB each).
- Success: 2xx JSON with a non-empty string `request_code` receipt.
- Failure: non-2xx JSON with `detail` as a string or a list containing `msg`.
- Accept the `Idempotency-Key` header, allow it through CORS, and enforce it
  atomically for the whole request and attachments. Repeating the same key and
  payload must return the original receipt without inserting/uploading twice.
  A changed payload with the same key must be rejected. Backend validation and
  image content inspection remain necessary.
- Timeout/network failures can occur after saving. Button disabling alone does
  not guarantee deduplication; backend idempotency is required before enabling
  retries against a real endpoint.

Run frontend checks: `npm run build` and `node --test tests/cleaningSubmission.test.js`.
