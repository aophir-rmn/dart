#!/usr/bin/ruby

# many thanks to the following resources:
#    https://github.com/rooneyp1976/docker-impala
#    https://github.com/awslabs/emr-bootstrap-actions/tree/master/impala

require 'net/http'
require 'json'
require 'optparse'




def run(cmd)
  if ! system(cmd) then
    raise "Command failed: #{cmd}"
  end
end


def sudo(cmd)
  run("sudo #{cmd}")
end


def parseOptions
	config_options = {
		:version => "2.3.0"
	}
	opt_parser = OptionParser.new do |opt|
    	opt.banner = "Usage: impala-install [OPTIONS]"
	    opt.on("-v",'--version [ Impala version to install ]',
	           "Ex : 2.3.0 )") do |version|
	      		config_options[:version] = version
	    end
	    opt.on("-d",'--docker-repo-base-url [ Docker Repo Base Url ]',
	           "Ex : 012345678901.dkr.ecr.us-east-1.amazonaws.com/myteam )") do |docker_repo_base_url|
	      		config_options[:docker_repo_base_url] = docker_repo_base_url
        end
    end
	opt_parser.parse!
	return config_options
end


def getClusterMetaData
	metaData = {}
	jobFlow = JSON.parse(File.read('/mnt/var/lib/info/job-flow.json'))
	userData = JSON.parse(Net::HTTP.get(URI('http://169.254.169.254/latest/user-data/')))

	#Determine if Instance Has IAM Roles
	req = Net::HTTP.get_response(URI('http://169.254.169.254/latest/meta-data/iam/security-credentials/'))
	metaData['roles'] = (req.code.to_i == 200) ? true : false

	metaData['instanceId'] = Net::HTTP.get(URI('http://169.254.169.254/latest/meta-data/instance-id/'))
	metaData['instanceType'] = Net::HTTP.get(URI('http://169.254.169.254/latest/meta-data/instance-type/'))
	metaData['masterPrivateDnsName'] = jobFlow['masterPrivateDnsName']
	metaData['isMaster'] = userData['isMaster']

	return metaData
end


def installDocker
    puts "Installing Docker"
    sudo "yum install -y docker"
    sudo 'sh -c \'echo -e "\nOPTIONS=\"\${OPTIONS} -g /mnt/docker/data\"" >> /etc/sysconfig/docker\''
    sudo "service docker start"
end


def configureImpala(isMaster, masterPrivateDnsName)
    puts "Updating config files"
    sudo "mkdir -p /mnt/impala/conf"
    sudo "mkdir -p /mnt/impala/log"
    sudo "useradd -u 999 impala" # the docker containers create the impala user with id 999
    sudo "usermod -aG hadoop impala"
    sudo "chown impala:impala /mnt/impala/log"
    sudo "ln -s /mnt/impala/log /var/log/impala"
    sudo "ln -s /var/run/hadoop-hdfs /mnt/impala/hadoop-hdfs"
    sudo "bash -c 'echo #{masterPrivateDnsName} > /mnt/impala/conf/masterPrivateDnsName.txt'"

    nodePattern = isMaster == true ? "HiveMetaStore" : "DataNode"
    user = isMaster == true ? "hive" : "hdfs"
    run "while [ $(ps -ef | grep #{nodePattern} | grep -e '^#{user}' | wc -l) -eq 0 ]; do sleep 2; done"

    sudo "cp /etc/hadoop/conf/core-site.xml /mnt/impala/conf/"
    sudo "cp /etc/hadoop/conf/hdfs-site.xml /mnt/impala/conf/"
    sudo "sed -i 's/\\/var\\/run\\/hadoop-hdfs\\/domain_socket\\._PORT/\\/mnt\\/impala\\/hadoop-hdfs\\/domain_socket._PORT/g' /mnt/impala/conf/hdfs-site.xml"
    if isMaster == true
        sudo "cp /etc/hive/conf/hive-site.xml /mnt/impala/conf/"
    end
end


def configureInstanceControllerLogs
	icConfig = JSON.parse(File.read('/etc/instance-controller/logs.json'))
	impalad = {
      	"delayPush" => "true",
      	"s3Path" => "node/$instance-id/apps/impala/$0",
      	"fileGlob" => "/var/log/impala/(.*)"
    }

    icConfig['logFileTypes'][1]['logFilePatterns'] << impalad
    conf = JSON.generate(icConfig)
    open("/tmp/ic-logs.json", 'w') do |f|
        f.puts(conf)
    end
    sudo "cp /tmp/ic-logs.json /etc/instance-controller/logs.json"
end


def runDockerContainers(isMaster, version, dockerRepoBaseUrl)
    sudo "$(aws ecr get-login)"
    if isMaster == true
        sudo "docker run --name impala-state-store --net=host -d --restart=always --privileged -v /mnt:/mnt -v /mnt1:/mnt1 -p 25010:25010 -p 24000:24000 #{dockerRepoBaseUrl}/impala-state-store:#{version}"
        sudo "docker run --name impala-catalog     --net=host -d --restart=always --privileged -v /mnt:/mnt -v /mnt1:/mnt1 -p 23020:23020 -p 25020:25020 -p 26000:26000  #{dockerRepoBaseUrl}/impala-catalog:#{version}"
        sudo "docker run --name impala-server      --net=host -d --restart=always --privileged -v /mnt:/mnt -v /mnt1:/mnt1 -p 21000:21000 -p 21050:21050 -p 22000:22000 -p 23000:23000 -p 25000:25000 #{dockerRepoBaseUrl}/impala-server:#{version}"
    else
        sudo "docker run --name impala-server      --net=host -d --restart=always --privileged -v /mnt:/mnt -v /mnt1:/mnt1 -p 21000:21000 -p 21050:21050 -p 22000:22000 -p 23000:23000 -p 25000:25000 #{dockerRepoBaseUrl}/impala-server:#{version}"
    end
end


def installImpalaShell
    sudo "rpm -ivh /mnt/impala/impala-shell.rpm"
end




@options = parseOptions
clusterMetaData = getClusterMetaData
isMaster = clusterMetaData['isMaster']
version = @options[:version]
dockerRepoBaseUrl = @options[:docker_repo_base_url]

puts "installing impala #{version}"
installDocker
configureImpala(isMaster, clusterMetaData['masterPrivateDnsName'])
configureInstanceControllerLogs
runDockerContainers(isMaster, version, dockerRepoBaseUrl)
installImpalaShell
puts "impala install finished"
exit 0
