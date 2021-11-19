"""A Kubernetes Python Pulumi program"""

import pulumi
import pulumi_aws as aws
import pulumi_kubernetes as k8s
import eks

config = pulumi.Config(name="kubernetes")

cluster = aws.eks.Cluster.get(config.get("context"), id=config.get("cluster"), arn=config.get("context"))

k8s_provider = k8s.Provider(config.get("cluster"), context=config.get("context"))

eks.ExistingEksClusterConfigurator(cluster=cluster,
                                   k8s_provider=k8s_provider,
                                   chart_config=config.require_object("charts"),
                                   managed_nodegroup_config=config.require_object("managed_nodegroups"),
                                   managed_addons=config.require_object("managed_addons"),
                                   namespaces=config.require_object("namespaces")
                                   ).configure()
