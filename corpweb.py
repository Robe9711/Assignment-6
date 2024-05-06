from aws_cdk import (
    aws_ec2 as ec2,
    aws_elasticloadbalancingv2 as elbv2,
    core
)

class CorpWeb(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        instance_type = core.CfnParameter(self, 'InstanceType',
                                          type='String',
                                          default='t2.micro',
                                          allowed_values=['t2.micro', 't2.small'])

        key_pair = core.CfnParameter(self, 'KeyPair',
                                     type='String')
                        

        your_ip = core.CfnParameter(self, 'YourIp',
                                    type='String')

        vpc = ec2.Vpc(self, 'EngineeringVpc',
                      cidr='10.0.0.0/18',
                      nat_gateways=0,  
                      subnet_configuration=[
                          ec2.SubnetConfiguration(name='PublicSubnet1', subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24),
                          ec2.SubnetConfiguration(name='PublicSubnet2', subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24)
                      ])


        security_group = ec2.SecurityGroup(self, 'WebserversSG',
                                            vpc=vpc,
                                            security_group_name='WebserversSG')
        security_group.add_ingress_rule(peer=ec2.Peer.ipv4(your_ip.value_as_string),
                                        connection=ec2.Port.tcp(22),
                                        )
        security_group.add_ingress_rule(peer=ec2.Peer.any_ipv4(),
                                        connection=ec2.Port.tcp(80),)

        user_data = ec2.UserData.for_linux()
        user_data.add_commands(
            'yum update -y',
            'yum install -y git httpd php',
            'service httpd start',
            'chkconfig httpd on',
            'aws s3 cp s3://seis665-public/index.php /var/www/html/'
        )

        instance1 = ec2.Instance(self, 'web1',
                                  instance_type=ec2.InstanceType(instance_type.value_as_string),
                                  machine_image=ec2.MachineImage.latest_amazon_linux(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
                                  key_name=key_pair.value_as_string,
                                  vpc=vpc,
                                  vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                                  security_group=security_group,
                                  user_data=user_data)

        instance2 = ec2.Instance(self, 'web2',
                                  instance_type=ec2.InstanceType(instance_type.value_as_string),
                                  machine_image=ec2.MachineImage.latest_amazon_linux(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
                                  key_name=key_pair.value_as_string,
                                  vpc=vpc,
                                  vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
                                  security_group=security_group,
                                  user_data=user_data)

        alb = elbv2.ApplicationLoadBalancer(self, 'EngineeringLB',
                                            vpc=vpc,
                                            internet_facing=True)

        target_group = elbv2.ApplicationTargetGroup(self, 'EngineeringWebservers',
                                                    port=80,
                                                    protocol=elbv2.ApplicationProtocol.HTTP,
                                                    target_type=elbv2.TargetType.INSTANCE,
                                                    targets=[instance1, instance2],
                                                    vpc=vpc)

        listener = alb.add_listener('Listener',
                                    port=80,
                                    open=True,
                                    default_action=elbv2.ListenerAction.forward([target_group]))

        core.CfnOutput(self, 'WebUrl',
                       value=alb.load_balancer_dns)
