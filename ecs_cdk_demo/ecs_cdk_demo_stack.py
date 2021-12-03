from constructs import Construct
from aws_cdk import (
    App, Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_elasticloadbalancingv2 as alb
)

class EcsCdkDemoStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        self.vpc = ec2.Vpc(self, 'ecs_cdk_demo_vpc',
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

        self.vpc_public_subnets = ec2.SubnetSelection(
            subnets=self.vpc.select_subnets(subnet_group_name="Public-Subnet").subnets
        )

        self.alb = alb.ApplicationLoadBalancer(self, "demo_alb",
            vpc= self.vpc,
            vpc_subnets= self.vpc_public_subnets,
            internet_facing= True
        )

        self.cluster = ecs.Cluster(self, "demo_cluster", vpc=self.vpc)

        self.fargate_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self, "demo_fargate_service",
            cluster=self.cluster,
            memory_limit_mib=1024,
            task_subnets= self.vpc_public_subnets,
            desired_count=1,
            load_balancer= self.alb,
            cpu=512, 
            task_image_options=ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                image=ecs.ContainerImage.from_registry("amazon/amazon-ecs-sample")
            )                      
        )

        self.scalable_target = self.fargate_service.service.auto_scale_task_count(
            min_capacity=1,
            max_capacity=20
        )

        self.scalable_target.scale_on_cpu_utilization("CpuScaling",
            target_utilization_percent=50
        )

        self.scalable_target.scale_on_memory_utilization("MemoryScaling",
            target_utilization_percent=50
        )
        