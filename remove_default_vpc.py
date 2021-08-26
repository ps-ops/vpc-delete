"""

Remove those pesky AWS default VPCs.

Python Version: 3.7.0
Boto3 Version: 1.7.50

"""

import boto3
from botocore.exceptions import ClientError
import logging
import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--dryrun", help="do not modify, show what would be done", action='store_true')
parser.add_argument(
    '-d', '--debug',
    help="Print lots of debugging statements",
    action="store_const", dest="loglevel", const=logging.DEBUG,
    default=logging.WARNING,
)
parser.add_argument(
    '-v', '--verbose',
    help="Be verbose",
    action="store_const", dest="loglevel", const=logging.INFO,
)

global_args = parser.parse_args()
logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s', level=global_args.loglevel, datefmt='%Y-%m-%d %H:%M:%S')


def delete_igw(ec2, vpc_id):
  """
  Detach and delete the internet gateway
  """

  args = {
    'Filters' : [
      {
        'Name' : 'attachment.vpc-id',
        'Values' : [ vpc_id ]
      }
    ]
  }

  try:
    igw = ec2.describe_internet_gateways(**args)['InternetGateways']
  except ClientError as e:
    logging.error(e.response['Error']['Message'])

  if igw:
    igw_id = igw[0]['InternetGatewayId']
    
    if global_args.dryrun:
      logging.warning("DRYRUN, would have deleted:"+ str(igw_id) +' IN VPC: '+ str(vpc_id))
    else:
      try:
        logging.info("Detaching IGW:"+ str(igw_id) +' in VPC: '+ str(vpc_id))
        result = ec2.detach_internet_gateway(InternetGatewayId=igw_id, VpcId=vpc_id)
      except ClientError as e:
        logging.error(e.response['Error']['Message'])

      try:
        logging.warning("Deleting IGW:"+ str(igw_id) +' in VPC: '+ str(vpc_id))
        result = ec2.delete_internet_gateway(InternetGatewayId=igw_id)
      except ClientError as e:
        logging.error(e.response['Error']['Message'])
  else:
    logging.debug('No IGW found in '+ str(vpc_id))

  return


def delete_subnets(ec2, args, vpc_id):
  """
  Delete the subnets
  """

  try:
    subs = ec2.describe_subnets(**args)['Subnets']
  except ClientError as e:
    logging.error(e.response['Error']['Message'])
  
  if subs:
    for sub in subs:
      sub_id = sub['SubnetId']
      if global_args.dryrun:
        logging.warning("DRYRUN, would have deleted subnet:"+ str(sub['SubnetId']) +' ('+ str(sub['CidrBlock']) +') IN VPC: '+ str(vpc_id))
      else:
        try:
          logging.warning("Deleting subnet:"+ str(sub['SubnetId']) +' ('+ str(sub['CidrBlock']) +') IN VPC: '+ str(vpc_id))
          result = ec2.delete_subnet(SubnetId=sub_id)
        except ClientError as e:
          logging.error(e.response['Error']['Message'])
  else:
    logging.warning('No Subnets found in '+ str(vpc_id))

  return


def check_for_non_default_rtbs(ec2, args, vpc_id):
  """
  Delete the route tables
  """

  try:
    rtbs = ec2.describe_route_tables(**args)['RouteTables']
  except ClientError as e:
    logging.error(e.response['Error']['Message'])

  if rtbs:
    for rtb in rtbs:
      for assoc in rtb['Associations']:
        if not assoc['Main']:
          logging.warning('Found non default route tables associated with VPC; this requires manual investigation. rtb id: ' + str(rtb['RouteTableId']) + 'vpc id: ' + str(vpc_id))
          return True
 
  return False


def check_for_non_default_acls(ec2, args, vpc_id):
  """
  Delete the network access lists (NACLs)
  """

  try:
    acls = ec2.describe_network_acls(**args)['NetworkAcls']
  except ClientError as e:
    logging.error(e.response['Error']['Message'])

  if acls:
    for acl in acls:
      if not acl['IsDefault']: 
        logging.warning('Found non default network ACL associated with VPC; this requires manual investigation. ACL id: ' + str(acl['NetworkAclId']) + 'vpc id: ' + str(vpc_id))
        return True

  return False


def check_for_non_default_sgs(ec2, args, vpc_id):
  """
  Delete any security groups
  """

  try:
    sgps = ec2.describe_security_groups(**args)['SecurityGroups']
  except ClientError as e:
    logging.error(e.response['Error']['Message'])

  if sgps:
    for sgp in sgps:
      if not (sgp['GroupName'] == 'default'):
        logging.warning('Found non default security group associated with VPC; this requires manual investigation. ACL id: ' + str(sgp['GroupId']) + ' vpc id: ' + str(vpc_id))
        return True

  return False


def delete_vpc(ec2, vpc_id, region):
  """
  Delete the VPC
  """
  if global_args.dryrun:
    logging.warning('Dryrun mode. Would have deleted VPC: ' + str(vpc_id)+' in region ' + str(region))
  else:
    try:
      logging.warning('Deleting VPC: ' + str(vpc_id) + ' in region ' + str(region))
      result = ec2.delete_vpc(VpcId=vpc_id)
    except ClientError as e:
      logging.error(e.response['Error']['Message'])

  return


def get_regions(ec2):
  """
  Return all AWS regions
  """

  regions = []

  try:
    aws_regions = ec2.describe_regions()['Regions']
  except ClientError as e:
    logging.error(e.response['Error']['Message'])

  else:
    for region in aws_regions:
      regions.append(region['RegionName'])

  return regions


def main(profile):
  """
  Do the work..

  Order of operation:

  1.) Delete the internet gateway
  2.) Delete subnets
  3.) Check for non-default route tables (default cannot be deleted, others require manual investigation)
  4.) Check for non-default network access lists
  5.) Check for non-default security groups
  6.) Delete the VPC 
  """

  # AWS Credentials
  # https://boto3.amazonaws.com/v1/documentation/api/latest/guide/configuration.html
  try:
    session = boto3.Session(profile_name=profile)
    sts = session.client('sts', region_name='us-east-1')
    response = sts.get_caller_identity()
    logging.info('Logged in as: ' + response['Arn'])
    ec2 = session.client('ec2', region_name='us-east-1')
  except:
    logging.error("UNABLE TO CONNECT!")

  regions = get_regions(ec2)
  logging.info('Fetched Regions: '+ str(regions))

  for region in regions:
    logging.info('Processing region '+ str(region))
    ec2 = session.client('ec2', region_name=region)

    try:
      attribs = ec2.describe_account_attributes(AttributeNames=[ 'default-vpc' ])['AccountAttributes']
      logging.debug('Found account attributes:'+ str(attribs))
    except ClientError as e:
      logging.error(e.response['Error']['Message'])
      return


    vpc_id = attribs[0]['AttributeValues'][0]['AttributeValue']
    logging.info('FOUND A VPC: '+ str(vpc_id))
    if vpc_id == 'none':
      logging.info('VPC (default) was not found in the {} region.'.format(region))
      continue

    # Are there any existing resources?  Since most resources attach an ENI, let's check..

    args = {
      'Filters' : [
        {
          'Name' : 'vpc-id',
          'Values' : [ vpc_id ]
        }
      ]
    }

    try:
      eni = ec2.describe_network_interfaces(**args)['NetworkInterfaces']
    except ClientError as e:
      logging.error(e.response['Error']['Message'])
      return

    if eni:
      logging.warning('VPC {} has existing network interfaces in the {} region and will be skipped.'.format(vpc_id, region))
      continue

    delete_igw(ec2, vpc_id)
    delete_subnets(ec2, args, vpc_id)
    non_default_rtb_exists = check_for_non_default_rtbs(ec2, args, vpc_id)
    non_default_acl_exists = check_for_non_default_acls(ec2, args, vpc_id)
    non_default_sg_exists = check_for_non_default_sgs(ec2, args, vpc_id)

    if not (non_default_rtb_exists or non_default_acl_exists or non_default_sg_exists):
      delete_vpc(ec2, vpc_id, region)
    else:
      logging.warning('Not deleting vpc because non-default resources are associated: ' + str(vpc_id))

  return


if __name__ == "__main__":
  logging.info('Running default loop')
  main(profile = 'orgmaster002-alignbi')

