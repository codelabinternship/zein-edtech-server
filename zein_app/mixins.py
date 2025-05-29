from django.core.files.storage import default_storage

class ImageDeleteMixin:
    def delete_old_image(self, instance, field_name):
        """
        Delete the old image file when a new one is uploaded or when the field is cleared
        """
        old_image = getattr(instance, field_name)
        if old_image and old_image.name:
            try:
                # Check if file exists in storage before attempting to delete
                if default_storage.exists(old_image.name):
                    default_storage.delete(old_image.name)
                else:
                    print(f"Old image {old_image.name} not found in storage, skipping deletion")
            except Exception as e:
                print(f"Error deleting old image: {str(e)}")
                pass  # If file doesn't exist or other error, just continue
