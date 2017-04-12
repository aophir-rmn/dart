#!/bin/bash -ex
# ----------------------------------------------------------------------------------------------------------
#         ^^^^^ ...because we'd like to (e)xit on errors, and print commands as they are e(x)ecuted
#
#         vvvvv ...allows viewing console output from the ec2 console ("Instance Settings > Get System Log")
# ----------------------------------------------------------------------------------------------------------
exec > >(tee /var/log/user-data.log | logger -t user-data -s 2>/dev/console) 2>&1

# increase the rsyslog line length from the default 2k to 32k
echo -e "\$MaxMessageSize 32k\n$(cat /etc/rsyslog.conf)" > /etc/rsyslog.conf
service rsyslog restart

n=0
until [ $n -ge 5 ]
do
  # install the aws cli
  yum install -y aws-cli && break
  n=$[$n+1]
  sleep 15
done

# discover instance metadata
INSTANCE_ID="$(curl -s 'http://169.254.169.254/latest/meta-data/instance-id')"
REGION="$(curl -s 'http://169.254.169.254/latest/meta-data/placement/availability-zone' | rev | cut -c 2- | rev)"
export AWS_DEFAULT_REGION=${REGION}

# create TAGS associative array
aws ec2 describe-tags --filters "Name=resource-id,Values=${INSTANCE_ID}" --region ${REGION} --output=text | cut -f 2,5 > /root/ec2-tags
declare -A TAGS
while read line; do k=$(cut -d ' ' -f 1 <<< ${line}); v=$(cut -d ' ' -f 2 <<< ${line}); TAGS["${k}"]="${v}"; done < /root/ec2-tags

ECS_CLUSTER=${TAGS["dart:ecs-cluster"]}
echo -e "ECS_CLUSTER=${ECS_CLUSTER}\nECS_AVAILABLE_LOGGING_DRIVERS=[\"json-file\",\"syslog\"]" >> /etc/ecs/ecs.config

# update the docker daemon config so that it uses syslog (allowing the cloudwatchlogs container to pick it up)
echo "OPTIONS=\"\${OPTIONS} --log-driver=syslog\"" >> /etc/sysconfig/docker

# restart docker (this will also kill the ecs agent/container)
service docker restart

# start ecs
start ecs

# update ECS services based on tags if needed
if [ -n "${TAGS["dart:ecs-service-and-increment-1"]}" ]; then
    ASG_NAME=$(aws autoscaling describe-auto-scaling-instances --instance-ids ${INSTANCE_ID} --query 'AutoScalingInstances[0].AutoScalingGroupName' --output text)
    ASG_DESIRED_COUNT=$(aws autoscaling describe-auto-scaling-groups --auto-scaling-group-name ${ASG_NAME} --query 'AutoScalingGroups[0].DesiredCapacity' --output text)
fi
i=0
while true; do
    i=$((i+1))
    if [ -z "${TAGS["dart:ecs-service-and-increment-${i}"]}" ]; then
        break
    fi
    ECS_SERVICE_PARAMS=${TAGS["dart:ecs-service-and-increment-${i}"]}
    NAME=$(cut -d '|' -f 1 <<< ${ECS_SERVICE_PARAMS} | cut -d '/' -f 2)
    INCREMENT=$(cut -d '|' -f 2 <<< ${ECS_SERVICE_PARAMS})
    COUNT=$((INCREMENT * ASG_DESIRED_COUNT))

    aws ecs update-service --cluster ${ECS_CLUSTER} --service ${NAME} --desired-count ${COUNT}
done
