### Remove AWS Default VPCs

This Python script attempts to delete the AWS default VPC in each region.

**Requirements:**

* Tested with:
   * Python version: 3.8.1
   * Boto3 version: 1.18.29
   * Botocore version: 1.21.29
* Valid AWS API keys/profile

**Setup:**

Update with your AWS profile / credentials.

```
main(profile = '<YOUR_PROFILE>')
```

**Usage:**

```
python remove_default_vpc.py

You are logged in as arn:aws:sts::<ACCOUNT_ID>:assumed-role/<ROLE_NAME>/<SESSION_NAME>

If the above user/account are correct, enter 'yes' to attempt to delete resources: yes
```

**Output:**

```
2021-08-26 15:58:14 WARNING  VPC vpc-ddacdca0 has existing network interfaces in the us-east-1 region and will be skipped.
2021-08-26 15:58:15 WARNING  No Subnets found in vpc-f2880199
2021-08-26 15:58:15 WARNING  Deleting launch wizard security group: launch-wizard-3 sg-066cfefce69c82a6c in VPC: vpc-f2880199
2021-08-26 15:58:16 WARNING  Deleting launch wizard security group: launch-wizard-1 sg-0727d511a2783f71d in VPC: vpc-f2880199
2021-08-26 15:58:16 WARNING  Deleting launch wizard security group: launch-wizard-2 sg-08fb56da0b1f15361 in VPC: vpc-f2880199
2021-08-26 15:58:16 WARNING  Deleting VPC: vpc-f2880199 in region us-east-2
```

**References:**

* https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html

