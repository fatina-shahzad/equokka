import boto3

def get_s3_presigned_url(bucket_name: str, region: str, file_name: str, expiration: int = 3000) -> str:
    """
    Generate a presigned URL to share an S3 object.
    :param bucket_name: Name of s3 bucket.
    :param region: Name of the file in the S3 bucket.
    :param file_name: Name of the file in the S3 bucket.
    :param expiration: Time in seconds for the presigned URL to remain valid.
    :return: Presigned URL as string.
    """
    s3_client = boto3.client("s3", region_name=region)
    url = s3_client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket_name, "Key": file_name},
        ExpiresIn=expiration,
    )
    return url