# Deploy Dart

Dart is deployed through a script that uses AWS Cloudformation to bring up the necessary resources.
A Dart environment depends on two Cloudformation stacks: a core stack of AWS resources that are shared between
environments and stack of resources specific to the environment. To create an entire Dart environment you can run:

```
python deploy.py /path/to/config/file/dart-config.yaml --create-core
```

# Update Dart

# Dart Config

Dart uses a YAML config file to set variables