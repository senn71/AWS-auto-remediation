## Build Log
# Build Log

**Region:** us-east-2 (US East, Ohio)

---

## Phase 1: Safety & Logging Setup — Nov 12, 2026

### 1. Zero-Spend Budget
- Created a Zero-Spend budget in AWS Budgets that emails me if spending exceeds $0.01.
- Meant to cost guardrail so any resource that leaves the Free Tier is caught immediately.
  
![Zero-spend budget](../screenshots/01-budget.png)

### 2. CloudTrail Trail
- Created a multi-region trail `security-audit-trail` that logs management events to an S3 bucket.
- CloudTrail records every API call in the account. It's the event source the detection pipeline listens to.
- Trail status shows Logging.

![CloudTrail trail](../screenshots/02-cloudtrail.png)

### 3. GuardDuty (skipped)
- Attempted to enable Amazon GuardDuty for threat detection.
- Blocked due to the service not being supported for my account tier level. 
- Proceeded without it. Detection is handled by CloudTrail + EventBridge pattern matching.


### 4. SNS Topic and Email Subscription
- Created a Standard SNS topic `SecurityAlerts` and subscribed my email.
- Lambda will publish a message to this topic after each remediation, and SNS delivers it to every subscriber.
  
![SNS subscription confirmed](../screenshots/04-sns-confirmed.png)


### 5. IAM Role for Lambda
- Created role `ssh-remediation-lambda-role` with a trust policy allowing only Lambda to assume it.
- **Permissions:** `AWSLambdaBasicExecutionRole` (CloudWatch logging) plus an inline policy allowing `ec2:DescribeSecurityGroups`, `ec2:RevokeSecurityGroupIngress`, and `sns:Publish` scoped to the `SecurityAlerts` topic.
- Least privilege. The function can only do the exact actions remediation needs.

![IAM role](../screenshots/05-iam-role.png)


### 6. Lambda Function
- Created `ssh-auto-remediation` (.py file) using the `ssh-remediation-lambda-role` execution role.
- **Config:** Added environment variable `SNS_TOPIC_ARN` (topic ARN, not subscription ARN). Raised timeout from 3s to 15s to avoid cold-start cutoffs.
  
![Lambda function](../screenshots/06-lambda.png)


### 7. EventBridge Rule
- Created rule `detect-sg-ingress-change` on the default event bus, targeting the `ssh-auto-remediation` Lambda.
- It matches CloudTrail-recorded EC2 API calls where `eventName` is `AuthorizeSecurityGroupIngress`.
- This API call adds an inbound rule to a security group, the moment a port gets opened.
- Initially opened "Scheduled rules (legacy)," which is for timer-based rules. Switched to an event-pattern rule via Event buses → default. Used the Advanced builder to paste the JSON pattern.

![EventBridge rule](../screenshots/07-eventbridge-rule.png)


---

## Repo Setup
- Created folder structure: `lambda/`, `eventbridge/`, `iam/`, `docs/`, `screenshots/`.
- Used `.gitkeep` to keep the empty `screenshots/` folder, since Git doesn't track empty folders.
