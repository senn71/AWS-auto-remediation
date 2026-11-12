## Build Log
# Build Log

**Region:** us-east-1 <!-- replace with yours -->

---

## Phase 1: Safety & Logging Setup — Nov 12, 2026

### 1. Zero-Spend Budget
- **What:** Created a Zero-Spend budget in AWS Budgets that emails me if spending exceeds $0.01.
- **Why:** Cost guardrail so any resource that leaves the Free Tier is caught immediately.
- **Result:** Budget `ZeroSpendBudget` shows status OK at $0.00 spent.
- **Issue:** AWS now requires new email recipients to verify their address before alerts are delivered. Verified via the email link.

![Zero-spend budget](../screenshots/01-budget.png)

### 2. CloudTrail Trail
- **What:** Created a multi-region trail `security-audit-trail` that logs management events to an S3 bucket.
- **Why:** CloudTrail records every API call in the account. It's the event source the detection pipeline listens to.
- **Result:** Trail status shows Logging.

![CloudTrail trail](../screenshots/02-cloudtrail.png)

---

## Repo Setup
- Created folder structure: `lambda/`, `eventbridge/`, `iam/`, `docs/`, `screenshots/`.
- Used `.gitkeep` to keep the empty `screenshots/` folder, since Git doesn't track empty folders.
