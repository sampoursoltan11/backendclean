#!/usr/bin/env python3
"""
Simple script to check IAM policies attached to your user and roles
Usage: python check_iam_policies.py [--profile PROFILE_NAME]
"""

import boto3
import json
import argparse
from botocore.exceptions import ClientError, NoCredentialsError

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def get_current_identity(profile_name=None):
    """Get the current AWS identity"""
    try:
        session = boto3.Session(profile_name=profile_name) if profile_name else boto3.Session()
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        return identity, session
    except Exception as e:
        print(f"❌ Error getting identity: {e}")
        return None, None

def get_user_policies(iam, username):
    """Get all policies attached to a user"""
    print(f"\n🔍 Checking policies for user: {username}")
    print("-" * 80)

    try:
        # Get managed policies attached to user
        print("\n📎 Managed Policies (Attached Directly):")
        response = iam.list_attached_user_policies(UserName=username)

        if response['AttachedPolicies']:
            for policy in response['AttachedPolicies']:
                print(f"  ✅ {policy['PolicyName']}")
                print(f"     ARN: {policy['PolicyArn']}")
        else:
            print("  (None)")

        # Get inline policies
        print("\n📝 Inline Policies:")
        response = iam.list_user_policies(UserName=username)

        if response['PolicyNames']:
            for policy_name in response['PolicyNames']:
                print(f"  ✅ {policy_name}")
        else:
            print("  (None)")

        # Get groups and their policies
        print("\n👥 Group Memberships and Policies:")
        response = iam.list_groups_for_user(UserName=username)

        if response['Groups']:
            for group in response['Groups']:
                print(f"\n  Group: {group['GroupName']}")

                # Get group's managed policies
                group_policies = iam.list_attached_group_policies(GroupName=group['GroupName'])
                if group_policies['AttachedPolicies']:
                    print("    Managed Policies:")
                    for policy in group_policies['AttachedPolicies']:
                        print(f"      ✅ {policy['PolicyName']}")
                        print(f"         ARN: {policy['PolicyArn']}")

                # Get group's inline policies
                group_inline = iam.list_group_policies(GroupName=group['GroupName'])
                if group_inline['PolicyNames']:
                    print("    Inline Policies:")
                    for policy_name in group_inline['PolicyNames']:
                        print(f"      ✅ {policy_name}")
        else:
            print("  (No groups)")

    except ClientError as e:
        print(f"❌ Error: {e}")

def get_role_policies(iam, role_name):
    """Get all policies attached to a role"""
    print(f"\n🔍 Checking policies for role: {role_name}")
    print("-" * 80)

    try:
        # Get managed policies attached to role
        print("\n📎 Managed Policies (Attached Directly):")
        response = iam.list_attached_role_policies(RoleName=role_name)

        if response['AttachedPolicies']:
            for policy in response['AttachedPolicies']:
                print(f"  ✅ {policy['PolicyName']}")
                print(f"     ARN: {policy['PolicyArn']}")
        else:
            print("  (None)")

        # Get inline policies
        print("\n📝 Inline Policies:")
        response = iam.list_role_policies(RoleName=role_name)

        if response['PolicyNames']:
            for policy_name in response['PolicyNames']:
                print(f"  ✅ {policy_name}")
        else:
            print("  (None)")

        # Get trust policy (who can assume this role)
        print("\n🔐 Trust Policy (Who can assume this role):")
        response = iam.get_role(RoleName=role_name)
        trust_policy = response['Role']['AssumeRolePolicyDocument']

        # Pretty print the trust policy
        for statement in trust_policy.get('Statement', []):
            principal = statement.get('Principal', {})
            if 'Service' in principal:
                print(f"  ✅ Service: {principal['Service']}")
            if 'AWS' in principal:
                print(f"  ✅ AWS Account/User: {principal['AWS']}")
            if 'Federated' in principal:
                print(f"  ✅ Federated: {principal['Federated']}")

    except ClientError as e:
        print(f"❌ Error: {e}")

def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Check IAM policies for your AWS profile/role')
    parser.add_argument('--profile', '-p', help='AWS profile name to use (default: default profile)', default=None)
    args = parser.parse_args()

    print_section("AWS IAM Policy Checker")

    if args.profile:
        print(f"\n🔑 Using AWS Profile: {args.profile}")

    try:
        # Get current identity
        print("\n🔑 Current AWS Identity:")
        identity, session = get_current_identity(args.profile)

        if not identity:
            print("❌ Could not determine AWS identity. Check your credentials.")
            return

        print(f"  User ID: {identity['UserId']}")
        print(f"  Account: {identity['Account']}")
        print(f"  ARN: {identity['Arn']}")

        # Create IAM client with the session
        iam = session.client('iam')

        # Parse the ARN to determine if it's a user or assumed role
        arn = identity['Arn']

        if ':user/' in arn:
            # It's an IAM user
            username = arn.split(':user/')[-1]
            print(f"\n✅ You are logged in as IAM User")

            print_section(f"Policies for IAM User: {username}")
            get_user_policies(iam, username)

        elif ':assumed-role/' in arn:
            # It's an assumed role
            role_name = arn.split(':assumed-role/')[-1].split('/')[0]
            session_name = arn.split(':assumed-role/')[-1].split('/')[1]

            print(f"\n✅ You are using an Assumed Role")
            print(f"  Role Name: {role_name}")
            print(f"  Session Name: {session_name}")

            print_section(f"Policies for Assumed Role: {role_name}")
            get_role_policies(iam, role_name)

        elif ':federated-user/' in arn:
            print(f"\n✅ You are logged in as a Federated User")
            print("  Note: Federated users get temporary credentials with specific permissions.")

        else:
            print(f"\n⚠️  Unknown identity type")
            print(f"  ARN: {arn}")

        # Offer to show detailed policy contents
        print("\n" + "=" * 80)
        print("\n💡 TIP: To see detailed permissions for a specific policy, you can:")
        print("   1. Note the policy ARN from above")
        print("   2. Run: aws iam get-policy-version --policy-arn <ARN> --version-id v1")
        print("   Or use the AWS Console to view policy details")

    except NoCredentialsError:
        print("❌ No AWS credentials found!")
        print("   Please configure your AWS credentials:")
        print("   - Run: aws configure")
        print(f"   - Or for a specific profile: aws configure --profile {args.profile or 'YOUR_PROFILE'}")
        print("   - Or set environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
