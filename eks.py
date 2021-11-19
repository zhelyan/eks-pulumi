import json

import pulumi
from pulumi.resource import ResourceOptions
from pulumi_kubernetes.helm.v3 import Chart, ChartOpts
from pulumi_kubernetes.core.v1.Namespace import Namespace
import pulumi_aws as aws
import pulumi_eks as eks


class ExistingEksClusterConfigurator:
    def __init__(self, k8s_provider: object, cluster: object, managed_nodegroup_config: dict, managed_addons: list,
                 chart_config: dict, namespaces: list) -> None:
        self.k8s_provider = k8s_provider
        self.cluster = cluster
        self.cluster_name = cluster.name
        self.managed_addons = managed_addons
        self.managed_nodegroup_config = managed_nodegroup_config
        self.chart_config = chart_config
        self.namespaces = namespaces

    def create_managed_addons(self):
        for addon in self.managed_addons:
            aws.eks.Addon(addon, addon_name=addon, cluster_name=self.cluster_name)

    def create_worker_role(self, id: str):
        return aws.iam.Role(id,
                            assume_role_policy=json.dumps({
                                "Version":
                                "2012-10-17",
                                "Statement": [{
                                    "Action": "sts:AssumeRole",
                                    "Effect": "Allow",
                                    "Sid": "",
                                    "Principal": {
                                        "Service": "ec2.amazonaws.com",
                                    },
                                }],
                            }),
                            managed_policy_arns=[
                                "arn:aws:iam::aws:policy/AmazonEKSWorkerNodePolicy",
                                "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly",
                                "arn:aws:iam::aws:policy/AmazonEKS_CNI_Policy",
                                "arn:aws:iam::aws:policy/AmazonElasticContainerRegistryPublicReadOnly"
                            ])

    def create_managed_nodegroup(self, id: str, group_options: dict):

        for az, subnet_ids in group_options.get("subnet_ids").items():
            node_group_id = f"{id}-{az}"
            node_group_iam_role = self.create_worker_role(f"{node_group_id}-instance-role")

            required_config = {
                "cluster_name": self.cluster_name,
                "cluster": {
                    "cluster": self.cluster_name
                },
                "subnet_ids": subnet_ids,
                "instance_types": ["t3.medium"],
                "node_role": node_group_iam_role
            }

            nodegroup_config = group_options.get("options") | required_config

            ng = eks.ManagedNodeGroup(node_group_id, **nodegroup_config)

            pulumi.export(f"{node_group_id}-role", node_group_iam_role.id)
            pulumi.export("{node_group_id}-id", ng.id)

    def create_namespace(self, name: str):
        Namespace(name, metadata={"name": name}, opts=ResourceOptions(provider=self.k8s_provider))

    def deploy_chart(self, chart_options: dict):
        Chart(chart_options["name"],
              config=ChartOpts(namespace=chart_options.get("namespace"),
                               repo=chart_options.get("repo"),
                               chart=chart_options.get("name"),
                               version=chart_options.get("version"),
                               fetch_opts={"repo": chart_options.get("repo_url")}),
              opts=ResourceOptions(provider=self.k8s_provider))

    def configure(self):

        self.create_managed_addons()

        for ns in self.namespaces:
            self.create_namespace(ns)

        for node_group_name, group_options in self.managed_nodegroup_config.items():
            self.create_managed_nodegroup(id=node_group_name, group_options=group_options)

        for chart_options in self.chart_config:
            if not chart_options["namespace"] in self.namespaces:
                self.create_namespace(chart_options["namespace"])

            self.deploy_chart(chart_options=chart_options)