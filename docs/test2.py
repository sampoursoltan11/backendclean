#!/usr/bin/env python3
"""
Check if your AWS profile/role has DynamoDB write permissions
Usage: python check_dynamodb_permissions.py [--profile PROFILE_NAME] [--table TABLE_NAME]
"""

import boto3
import argparse
from botocore.exceptions import ClientError, NoCredentialsError
import json

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

def test_dynamodb_permissions(session, table_name=None):
    """Test DynamoDB permissions by trying various operations"""
    dynamodb = session.client('dynamodb')

    print("\n🔍 Testing DynamoDB Permissions...")
    print("-" * 80)

    results = {
        'list_tables': False,
        'describe_table': False,
        'put_item': False,
        'get_item': False,
        'update_item': False,
        'delete_item': False,
        'scan': False,
        'query': False
    }

    # Test 1: List Tables
    print("\n1️⃣  Testing ListTables permission...")
    try:
        response = dynamodb.list_tables()
        results['list_tables'] = True
        print(f"   ✅ SUCCESS - Can list tables")
        print(f"   Found {len(response.get('TableNames', []))} table(s)")

        if response.get('TableNames'):
            print(f"   Tables: {', '.join(response['TableNames'][:5])}")
            if not table_name and response['TableNames']:
                table_name = response['TableNames'][0]
                print(f"   Using '{table_name}' for further tests")
    except ClientError as e:
        print(f"   ❌ DENIED - {e.response['Error']['Code']}: {e.response['Error']['Message']}")
        results['list_tables'] = False

    if not table_name:
        print("\n⚠️  No table specified and couldn't find any tables. Skipping table-specific tests.")
        return results

    # Test 2: Describe Table
    print(f"\n2️⃣  Testing DescribeTable permission on '{table_name}'...")
    try:
        response = dynamodb.describe_table(TableName=table_name)
        results['describe_table'] = True
        print(f"   ✅ SUCCESS - Can describe table")

        # Get key schema
        key_schema = response['Table']['KeySchema']
        print(f"   Key Schema: {key_schema}")
    except ClientError as e:
        print(f"   ❌ DENIED - {e.response['Error']['Code']}: {e.response['Error']['Message']}")
        results['describe_table'] = False
        return results  # Can't continue without table info

    # Get the primary key info
    hash_key = next((k['AttributeName'] for k in key_schema if k['KeyType'] == 'HASH'), None)
    range_key = next((k['AttributeName'] for k in key_schema if k['KeyType'] == 'RANGE'), None)

    if not hash_key:
        print(f"   ⚠️  Could not determine hash key. Skipping write tests.")
        return results

    # Test 3: Scan (Read)
    print(f"\n3️⃣  Testing Scan permission on '{table_name}'...")
    try:
        response = dynamodb.scan(TableName=table_name, Limit=1)
        results['scan'] = True
        print(f"   ✅ SUCCESS - Can scan table")
        print(f"   Items scanned: {response.get('ScannedCount', 0)}")
    except ClientError as e:
        print(f"   ❌ DENIED - {e.response['Error']['Code']}: {e.response['Error']['Message']}")
        results['scan'] = False

    # Test 4: PutItem (Write) - Dry run using conditional check
    print(f"\n4️⃣  Testing PutItem permission on '{table_name}'...")
    test_item = {
        hash_key: {'S': 'TEST-PERMISSION-CHECK-DO-NOT-USE'}
    }
    if range_key:
        test_item[range_key] = {'S': 'TEST-SORT-KEY'}

    try:
        # Try to put with a condition that will fail (to avoid actually writing)
        dynamodb.put_item(
            TableName=table_name,
            Item=test_item,
            ConditionExpression=f"attribute_not_exists({hash_key}) AND attribute_exists(NonExistentAttribute)"
        )
        results['put_item'] = True
        print(f"   ✅ SUCCESS - Has PutItem permission")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            # Condition failed, but we have permission!
            results['put_item'] = True
            print(f"   ✅ SUCCESS - Has PutItem permission (verified via conditional check)")
        elif e.response['Error']['Code'] == 'AccessDeniedException':
            print(f"   ❌ DENIED - No PutItem permission")
            results['put_item'] = False
        else:
            print(f"   ⚠️  UNKNOWN - {e.response['Error']['Code']}: {e.response['Error']['Message']}")
            results['put_item'] = False

    # Test 5: GetItem (Read)
    print(f"\n5️⃣  Testing GetItem permission on '{table_name}'...")
    key = {hash_key: {'S': 'NONEXISTENT-KEY'}}
    if range_key:
        key[range_key] = {'S': 'NONEXISTENT-SORT'}

    try:
        dynamodb.get_item(TableName=table_name, Key=key)
        results['get_item'] = True
        print(f"   ✅ SUCCESS - Can get items")
    except ClientError as e:
        print(f"   ❌ DENIED - {e.response['Error']['Code']}: {e.response['Error']['Message']}")
        results['get_item'] = False

    # Test 6: UpdateItem (Write)
    print(f"\n6️⃣  Testing UpdateItem permission on '{table_name}'...")
    try:
        dynamodb.update_item(
            TableName=table_name,
            Key=key,
            UpdateExpression='SET #attr = :val',
            ExpressionAttributeNames={'#attr': 'test_attribute'},
            ExpressionAttributeValues={':val': {'S': 'test'}},
            ConditionExpression='attribute_not_exists(#pk)',
            ExpressionAttributeNames={'#pk': hash_key}
        )
        results['update_item'] = True
        print(f"   ✅ SUCCESS - Has UpdateItem permission")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            results['update_item'] = True
            print(f"   ✅ SUCCESS - Has UpdateItem permission (verified via conditional check)")
        elif e.response['Error']['Code'] == 'AccessDeniedException':
            print(f"   ❌ DENIED - No UpdateItem permission")
            results['update_item'] = False
        else:
            print(f"   ⚠️  UNKNOWN - {e.response['Error']['Code']}: {e.response['Error']['Message']}")
            results['update_item'] = False

    # Test 7: DeleteItem (Write)
    print(f"\n7️⃣  Testing DeleteItem permission on '{table_name}'...")
    try:
        dynamodb.delete_item(
            TableName=table_name,
            Key=key,
            ConditionExpression='attribute_not_exists(#pk)',
            ExpressionAttributeNames={'#pk': hash_key}
        )
        results['delete_item'] = True
        print(f"   ✅ SUCCESS - Has DeleteItem permission")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            results['delete_item'] = True
            print(f"   ✅ SUCCESS - Has DeleteItem permission (verified via conditional check)")
        elif e.response['Error']['Code'] == 'AccessDeniedException':
            print(f"   ❌ DENIED - No DeleteItem permission")
            results['delete_item'] = False
        else:
            print(f"   ⚠️  UNKNOWN - {e.response['Error']['Code']}: {e.response['Error']['Message']}")
            results['delete_item'] = False

    # Test 8: Query (Read)
    print(f"\n8️⃣  Testing Query permission on '{table_name}'...")
    try:
        dynamodb.query(
            TableName=table_name,
            KeyConditionExpression=f"{hash_key} = :pk",
            ExpressionAttributeValues={':pk': {'S': 'NONEXISTENT'}},
            Limit=1
        )
        results['query'] = True
        print(f"   ✅ SUCCESS - Can query table")
    except ClientError as e:
        print(f"   ❌ DENIED - {e.response['Error']['Code']}: {e.response['Error']['Message']}")
        results['query'] = False

    return results

def print_summary(results):
    """Print a summary of permission test results"""
    print_section("Permission Test Summary")

    # Categorize permissions
    read_ops = ['list_tables', 'describe_table', 'get_item', 'scan', 'query']
    write_ops = ['put_item', 'update_item', 'delete_item']

    print("\n📖 READ Permissions:")
    for op in read_ops:
        status = "✅ ALLOWED" if results.get(op) else "❌ DENIED"
        print(f"   {op:<20} {status}")

    print("\n✍️  WRITE Permissions:")
    for op in write_ops:
        status = "✅ ALLOWED" if results.get(op) else "❌ DENIED"
        print(f"   {op:<20} {status}")

    # Overall assessment
    print("\n" + "=" * 80)
    can_read = any(results.get(op) for op in read_ops)
    can_write = any(results.get(op) for op in write_ops)

    if can_read and can_write:
        print("✅ You have BOTH read and write access to DynamoDB")
    elif can_write:
        print("✅ You have WRITE access to DynamoDB (but limited read)")
    elif can_read:
        print("⚠️  You have READ-ONLY access to DynamoDB")
    else:
        print("❌ You have NO access to DynamoDB")

    print("=" * 80)

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Check DynamoDB permissions for your AWS profile/role')
    parser.add_argument('--profile', '-p', help='AWS profile name to use', default=None)
    parser.add_argument('--table', '-t', help='DynamoDB table name to test', default=None)
    args = parser.parse_args()

    print_section("DynamoDB Permission Checker")

    if args.profile:
        print(f"\n🔑 Using AWS Profile: {args.profile}")

    try:
        # Get current identity
        identity, session = get_current_identity(args.profile)

        if not identity:
            print("❌ Could not determine AWS identity. Check your credentials.")
            return

        print(f"\n🔑 Current AWS Identity:")
        print(f"  User ID: {identity['UserId']}")
        print(f"  Account: {identity['Account']}")
        print(f"  ARN: {identity['Arn']}")

        # Test DynamoDB permissions
        results = test_dynamodb_permissions(session, args.table)

        # Print summary
        print_summary(results)

        # Additional recommendations
        if not results.get('put_item') and not results.get('update_item'):
            print("\n💡 RECOMMENDATION:")
            print("   Your role lacks DynamoDB write permissions.")
            print("   You need policies that allow:")
            print("   - dynamodb:PutItem")
            print("   - dynamodb:UpdateItem")
            print("   - dynamodb:DeleteItem (optional)")
            print("\n   Example policy:")
            print('   {')
            print('       "Effect": "Allow",')
            print('       "Action": [')
            print('           "dynamodb:PutItem",')
            print('           "dynamodb:UpdateItem",')
            print('           "dynamodb:GetItem",')
            print('           "dynamodb:Scan",')
            print('           "dynamodb:Query"')
            print('       ],')
            print('       "Resource": "arn:aws:dynamodb:*:*:table/YOUR_TABLE_NAME"')
            print('   }')

    except NoCredentialsError:
        print("❌ No AWS credentials found!")
        print("   Please configure your AWS credentials:")
        print("   - Run: aws configure")
        print(f"   - Or for a specific profile: aws configure --profile {args.profile or 'YOUR_PROFILE'}")

    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
