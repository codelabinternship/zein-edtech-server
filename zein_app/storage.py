from storages.backends.s3boto3 import S3Boto3Storage
import os
import time

class CustomS3Storage(S3Boto3Storage):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_acl = None  # Remove ACL
        
    def _clean_name(self, name):
        return name.lstrip('/')
        
    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            dir_name, file_name = os.path.split(name)
            base, extension = os.path.splitext(file_name)
            name = os.path.join(dir_name, f"{base}_{int(time.time())}{extension}")
        return super().get_available_name(name, max_length)