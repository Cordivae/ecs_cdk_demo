from constructs import Construct
from aws_cdk import App, Stack                    # core constructs
from aws_cdk import aws_ec2 as ec2                  # stable module

class EcsCdkDemoStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        self.vpc = ec2.Vpc(self, 'fargate_vpc',
            cidr= '10.0.0.0/24',
            max_azs= 2,
            enable_dns_hostnames= True,
            enable_dns_support= True,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public-Subnet",
                    subnet_type= ec2.SubnetType.PUBLIC,
                    cidr_mask=26
                ),
                ec2.SubnetConfiguration(
                    name="Private-Subnet",
                    subnet_type= ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=26
                )                
            ]
        )