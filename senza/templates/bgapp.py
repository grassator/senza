'''
Background app with single EC2 instance
'''

from clickclick import warning
import pystache
from ._helper import prompt, check_security_group, check_iam_role, get_mint_bucket_name

TEMPLATE = '''
# basic information for generating and executing this definition
SenzaInfo:
  StackName: {{application_id}}
  Parameters:
    - ImageVersion:
        Description: "Docker image version of {{ application_id }}."

# a list of senza components to apply to the definition
SenzaComponents:

  # this basic configuration is required for the other components
  - Configuration:
      Type: Senza::StupsAutoConfiguration # auto-detect network setup

  # will create a launch configuration and auto scaling group with scaling triggers
  - AppServer:
      Type: Senza::TaupageAutoScalingGroup
      InstanceType: {{ instance_type }}
      SecurityGroups:
        - app-{{application_id}}
      IamRoles:
        - app-{{application_id}}
      AssociatePublicIpAddress: false # change for standalone deployment in default VPC
      TaupageConfig:
        application_version: "{{=<% %>=}}{{Arguments.ImageVersion}}<%={{ }}=%>"
        runtime: Docker
        source: "{{ docker_image }}:{{=<% %>=}}{{Arguments.ImageVersion}}<%={{ }}=%>"
        mint_bucket: "{{ mint_bucket }}"
'''


def gather_user_variables(variables, region):
    prompt(variables, 'application_id', 'Application ID', default='hello-world')
    prompt(variables, 'docker_image', 'Docker image without tag/version (e.g. "pierone.example.org/myteam/myapp")',
           default='stups/hello-world')
    prompt(variables, 'instance_type', 'EC2 instance type', default='t2.micro')
    prompt(variables, 'mint_bucket', 'Mint S3 bucket name', default=lambda: get_mint_bucket_name(region))

    sg_name = 'app-{}'.format(variables['application_id'])
    rules_missing = check_security_group(sg_name, [('tcp', 22)], region, allow_from_self=True)

    if ('tcp', 22) in rules_missing:
        warning('Security group {} does not allow SSH access, you will not be able to ssh into your servers'.format(
            sg_name))

    check_iam_role(variables['application_id'], variables['mint_bucket'], region)

    return variables


def generate_definition(variables):
    definition_yaml = pystache.render(TEMPLATE, variables)
    return definition_yaml
