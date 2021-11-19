# Configure an existing EKS cluster with Pulumi

Testing how can we do this with Pulumi.


- change the AWS account number,subnet ids, AZs, Cluster name in `Pulumi.test.yaml` then:

One-off:

```sh
# used by the test stack
export PULUMI_CONFIG_PASSPHRASE="foo"

pulumi login file://.

pulumi stack init test
```

Developing

```sh
export PULUMI_CONFIG_PASSPHRASE="foo"
pulumi preview
pulumi up
```
