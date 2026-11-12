import boto3
import json
import os
from datetime import datetime, timezone

ec2 = boto3.client('ec2')
sns = boto3.client('sns')
SNS_TOPIC_ARN = os.environ['SNS_TOPIC_ARN']


def exposes_ssh(perm):
    """True if this rule's protocol/port range includes port 22."""
    protocol = perm.get('ipProtocol')
    if protocol == '-1':                      # -1 = "All traffic"
        return True
    if protocol not in ('tcp', '6'):          # SSH is TCP only
        return False
    from_port, to_port = perm.get('fromPort'), perm.get('toPort')
    if from_port is None or to_port is None:
        return False
    return from_port <= 22 <= to_port


def lambda_handler(event, context):
    print(json.dumps(event))                  # full event goes to CloudWatch Logs

    detail = event['detail']
    if detail.get('errorCode'):               # the API call failed, nothing to fix
        return {'statusCode': 200, 'body': 'Call failed, skipping'}

    params = detail['requestParameters']
    group_id = params.get('groupId')
    actor = detail.get('userIdentity', {}).get('arn', 'unknown')
    event_time = datetime.strptime(detail['eventTime'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)

    revoked = []
    for perm in params.get('ipPermissions', {}).get('items', []):
        if not exposes_ssh(perm):
            continue

        open_v4 = [r['cidrIp'] for r in perm.get('ipRanges', {}).get('items', [])
                   if r.get('cidrIp') == '0.0.0.0/0']
        open_v6 = [r['cidrIpv6'] for r in perm.get('ipv6Ranges', {}).get('items', [])
                   if r.get('cidrIpv6') == '::/0']
        if not open_v4 and not open_v6:
            continue

        rule = {'IpProtocol': perm['ipProtocol']}
        if perm['ipProtocol'] != '-1':
            rule['FromPort'] = perm['fromPort']
            rule['ToPort'] = perm['toPort']
        if open_v4:
            rule['IpRanges'] = [{'CidrIp': c} for c in open_v4]
        if open_v6:
            rule['Ipv6Ranges'] = [{'CidrIpv6': c} for c in open_v6]

        ec2.revoke_security_group_ingress(GroupId=group_id, IpPermissions=[rule])
        revoked.append(rule)

    if not revoked:
        return {'statusCode': 200, 'body': 'No public SSH exposure found'}

    seconds = (datetime.now(timezone.utc) - event_time).total_seconds()
    message = (
        "AUTO-REMEDIATION TRIGGERED\n\n"
        f"Security Group: {group_id}\n"
        f"Changed by: {actor}\n"
        f"Change time (UTC): {detail['eventTime']}\n"
        f"Revoked rule(s): {json.dumps(revoked)}\n"
        f"Time from exposure to fix: {seconds:.1f} seconds\n\n"
        "Public SSH access (port 22 open to the internet) was removed automatically."
    )
    print(message)
    sns.publish(TopicArn=SNS_TOPIC_ARN, Subject="AWS Auto-Remediation: Public SSH Revoked", Message=message)
    return {'statusCode': 200, 'body': 'Remediated'}
