import subprocess
from pathlib import PosixPath
import json
import uuid
from langchain_core.tools import tool


@tool
def sync_workspace_to_object_store(workspace_dir: PosixPath ) -> dict:
    """Sync all files of the current workspace to an S3 bucket.

    Creates a new S3 bucket named after the current workspace (directory name)
    if it doesn't already exist, then uploads all files recursively.

    AWS credentials are read from ~/.aws/ directory (using default AWS CLI
    credential resolution: environment variables, ~/.aws/credentials,
    ~/.aws/config, IAM roles, etc.).

    Returns
    -------
    dict
        A dict with the bucket name and sync status.

    Examples
    --------
    >>> sync_workspace_to_object_store()
    {'bucket': 'sra_chem', 'status': 'synced', 'message': 'Successfully synced 42 files to s3://sra_chem'}
    """

    bucket_name = workspace_dir.name

    # create the bucket
    _ = create_bucket(bucket_name)

    # Sync all files to the bucket
    sync_msg = sync_bucket(workspace_dir, bucket_name)

    return{
        "bucket": bucket_name,
        "status": "Bucket created and synced",
        "message": sync_msg["message"] 
    }


def create_bucket(bucketname: str):
    """Creates a bucket in the Object Store using the AWS CLI.

    Executes ``aws s3api create-bucket`` with the connector's
    endpoint URL, access key, and secret key.

    Raises
    ------
    RuntimeError
        If the AWS CLI command returns a non-zero exit code.
    """
    
    print(f"Creates bucket {bucketname} in Object Store")

    cmd = [
        "aws",
        "s3api",
        "create-bucket",
        "--bucket",
        bucketname,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to create bucket via CLI: {result.stderr.strip()}"
        )
    
    apply_expiration_lifecycle_policy(bucketname)
    
    return result.stdout

def apply_expiration_lifecycle_policy(bucket, retention_days=31):
    """Applies a lifecycle rule to expire all objects in the bucket after a given number of days.

    Parameters
    ----------
    bucket : str
        The name of the bucket to configure

    Raises
    ------
    RuntimeError
        If the AWS CLI command returns a non-zero exit code.
    """
    print(
        f"Applies {retention_days}-day expiration lifecycle policy to bucket {bucket}"
    )

    lifecycle_config = {
        "Rules": [
            {
                "ID": f"DeleteObjectsAfter{retention_days}Days_{uuid.uuid4()}",
                "Status": "Enabled",
                "Filter": {"Prefix": ""},
                "Expiration": {"Days": retention_days},
            }
        ]
    }

    cmd = [
        "aws",
        "s3api",
        "put-bucket-lifecycle-configuration",
        "--bucket",
        bucket,
        "--lifecycle-configuration",
        json.dumps(lifecycle_config),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to set lifecycle policy via CLI: {result.stderr.strip()}"
        )
    
def sync_bucket(workspace_dir, bucket_name):
    """Sync all files from a local workspace directory to an S3 bucket.

    Executes ``aws s3 sync`` to recursively upload all files from the
    workspace directory to the specified S3 bucket.

    Parameters
    ----------
    workspace_dir : PosixPath
        The local directory containing files to sync.
    bucket_name : str
        The name of the S3 bucket to sync to.

    Returns
    -------
    dict
        A dict with the bucket name, sync status, and a message
        indicating how many files were uploaded.

    Raises
    ------
    RuntimeError
        If the AWS CLI command returns a non-zero exit code.
    """

    # Sync all files to the bucket
    sync_cmd = [
        "aws", "s3", "sync",
        str(workspace_dir),
        f"s3://{bucket_name}",
    ]
    result = subprocess.run(
        sync_cmd,
        capture_output=True,
        text=True,
        check=True
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Failed to sync bucket via CLI: {result.stderr.strip()}"
        )
    
    # Count uploaded files from the output
    lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
    uploaded_count = sum(
        1 for line in lines
        if line.startswith("upload:")
    )

    return {
        "bucket": bucket_name,
        "status": "synced",
        "message": f"Successfully synced {uploaded_count} files to s3://{bucket_name}",
    }
