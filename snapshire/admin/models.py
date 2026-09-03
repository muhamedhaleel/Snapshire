from django.db import models

# Create your models here.


from django.db import models


class PlatformFee(models.Model):
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Platform Fee: ₹{self.amount}"
