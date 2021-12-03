#!/usr/bin/env python3
import os

from constructs import Construct
from aws_cdk import App, Stack, Environment                    # core constructs
from aws_cdk import aws_s3 as s3                  # stable module

from ecs_cdk_demo.ecs_cdk_demo_stack import EcsCdkDemoStack


app = App()
env_dev = Environment(account="310181001400", region="us-west-2")
EcsCdkDemoStack(app, "EcsCdkDemoStack", env=env_dev)

app.synth()
