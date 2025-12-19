from django.db import models, transaction
from django.conf import settings


# Create your models here.
class BroadcastMessage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='messages')
    message = models.TextField()
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.active:
            # Use atomic transaction with row locking to prevent race conditions
            with transaction.atomic():
                # Lock and deactivate all user's active messages
                BroadcastMessage.objects.select_for_update().filter(
                    user=self.user, active=True
                ).update(active=False)
                # Save this message as active
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.username}: {self.message[:20]}'