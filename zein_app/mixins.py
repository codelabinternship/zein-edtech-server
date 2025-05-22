from django.core.files.storage import default_storage

class ImageDeleteMixin:
    def delete_old_image(self, instance, field_name):
        """
        Delete the old image file when a new one is uploaded or when the field is cleared
        """
        old_image = getattr(instance, field_name)
        if old_image:
            try:
                default_storage.delete(old_image.path)
            except Exception:
                print(f"Error deleting old image: {old_image.path}")
                pass  # If file doesn't exist or other error, just continue
