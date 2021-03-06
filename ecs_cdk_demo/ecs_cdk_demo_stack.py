from constructs import Construct
from aws_cdk import (
    CfnOutput,
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecs_patterns as ecs_patterns,
    aws_route53 as route53,
    aws_certificatemanager as certificatemanager,
)


class EcsCdkDemoStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        self.vpc = ec2.Vpc(
            self,
            "ecs_cdk_demo_vpc",
            cidr="10.0.0.0/24",
            max_azs=2,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public-Subnet",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=26,
                ),
                ec2.SubnetConfiguration(
                    name="Private-Subnet",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=26,
                ),
            ],
        )

        self.vpc_public_subnets = ec2.SubnetSelection(
            subnets=self.vpc.select_subnets(
                subnet_group_name="Public-Subnet"
            ).subnets
        )

        # Given how often I delete this stack
        # The SOA is in a different account
        self.zone = route53.HostedZone.from_lookup(
            self, "cdkdemo_hosted_zone", domain_name="cdkdemo.techmonkey.pro"
        )

        self.cert = certificatemanager.Certificate(
            self,
            "demo_cert",
            domain_name="cdkdemo.techmonkey.pro",
            subject_alternative_names=["*.cdkdemo.techmonkey.pro"],
            validation=(
                certificatemanager.CertificateValidation.from_dns(self.zone)
            ),
        )

        self.ecs_cluster = ecs.Cluster(
            self,
            "demo_cluster",
            vpc=self.vpc,
            cluster_name="ecs_cdk_cluster",
            container_insights=True,
        )

        self.ecs_cluster.add_default_cloud_map_namespace(name="service.local")

        self.ecs_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "demo_fargate_service",
            cluster=self.ecs_cluster,
            memory_limit_mib=1024,
            task_subnets=self.vpc_public_subnets,
            desired_count=1,
            cpu=512,
            redirect_http=True,
            certificate=self.cert,
            domain_name="cdkdemo.techmonkey.pro",
            domain_zone=self.zone,
            assign_public_ip=True,  # needed to pull container
            task_image_options=(
                ecs_patterns.ApplicationLoadBalancedTaskImageOptions(
                    image=ecs.ContainerImage.from_registry(
                        "public.ecr.aws/nginx/nginx:latest"
                    )
                )
            ),
        )

        self.scalable_target = self.ecs_service.service.auto_scale_task_count(
            min_capacity=1, max_capacity=20
        )

        self.scalable_target.scale_on_cpu_utilization(
            "CpuScaling", target_utilization_percent=50
        )

        self.scalable_target.scale_on_memory_utilization(
            "MemoryScaling", target_utilization_percent=50
        )

        # Cloudformation Outputs

        self.namespace_outputs = {
            "ARN": self.ecs_cluster.default_cloud_map_namespace.namespace_arn,
            "NAME": self.ecs_cluster.default_cloud_map_namespace.namespace_name,
            "ID": self.ecs_cluster.default_cloud_map_namespace.namespace_id,
        }

        self.cluster_outputs = {
            "NAME": self.ecs_cluster.cluster_name,
            "SECGRPS": (str(self.ecs_cluster.connections.security_groups)),
        }

        if self.ecs_cluster.connections.security_groups:
            self.cluster_outputs["SECGRPS"] = str(
                [
                    x.security_group_id
                    for x in self.ecs_cluster.connections.security_groups
                ][0]
            )

        # All Outputs required for other stacks to build
        CfnOutput(
            self,
            "NSArn",
            value=self.namespace_outputs["ARN"],
            export_name="NSARN",
        )
        CfnOutput(
            self,
            "NSName",
            value=self.namespace_outputs["NAME"],
            export_name="NSNAME",
        )
        CfnOutput(
            self,
            "NSId",
            value=self.namespace_outputs["ID"],
            export_name="NSID",
        )
        CfnOutput(
            self,
            "ECSClusterName",
            value=self.cluster_outputs["NAME"],
            export_name="ECSClusterName",
        )
        CfnOutput(
            self,
            "ECSClusterSecGrp",
            value=self.cluster_outputs["SECGRPS"],
            export_name="ECSSecGrpList",
        )
