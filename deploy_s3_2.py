import boto3
import time

# Define the CloudFormation template
cloudformation_template = """
AWSTemplateFormatVersion: '2010-09-09'
Description: S3 to Lambda event-based trigger to copy object to another bucket

Resources:

  SourceBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "${AWS::StackName}-source"

  DestinationBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "${AWS::StackName}-destination"

  LambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: "2012-10-17"
        Statement:
          - Effect: Allow
            Principal:
              Service: 
                - lambda.amazonaws.com
            Action: 
              - 'sts:AssumeRole'
      Policies:
        - PolicyName: LambdaS3Policy
          PolicyDocument:
            Version: "2012-10-17"
            Statement:
              - Effect: Allow
                Action:
                  - 's3:GetObject'
                  - 's3:PutObject'
                Resource:
                  - !Sub 'arn:aws:s3:::${AWS::StackName}-source/*'
                  - !Sub 'arn:aws:s3:::${AWS::StackName}-destination/*'

  S3CopyLambda:
    Type: AWS::Lambda::Function
    Properties:
      Handler: index.lambda_handler
      Role: !GetAtt LambdaExecutionRole.Arn
      Runtime: python3.9
      Timeout: 60
      Code:
        ZipFile: |
          import boto3

          s3 = boto3.client('s3')

          def lambda_handler(event, context):
              source_bucket = event['Records'][0]['s3']['bucket']['name']
              object_key = event['Records'][0]['s3']['object']['key']
              destination_bucket = source_bucket.replace("source", "destination")

              copy_source = {'Bucket': source_bucket, 'Key': object_key}
              s3.copy_object(Bucket=destination_bucket, CopySource=copy_source, Key=object_key)

              return {'status': 'success'}

  S3CopyLambdaPermission:
    Type: AWS::Lambda::Permission
    Properties:
      FunctionName: !Ref S3CopyLambda
      Action: lambda:InvokeFunction
      Principal: s3.amazonaws.com
      SourceArn: !GetAtt SourceBucket.Arn
"""

# Initialize the boto3 client for CloudFormation
cf_client = boto3.client('cloudformation', region_name='us-east-1')

# Create the CloudFormation stack
stack_name = "demos3"
cf_client.create_stack(
    StackName=stack_name,
    TemplateBody=cloudformation_template,
    Capabilities=['CAPABILITY_NAMED_IAM']
)

# Wait for the stack creation to complete
while True:
    response = cf_client.describe_stacks(StackName=stack_name)
    stack_status = response['Stacks'][0]['StackStatus']
    print(f"Stack status: {stack_status}")
    if stack_status == 'CREATE_COMPLETE':
        break
    elif stack_status == 'CREATE_FAILED':
        raise Exception("Stack creation failed")
    time.sleep(10)

print("CloudFormation stack created successfully.")
