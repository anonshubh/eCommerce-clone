from django.db import models
from billing.models import BillingProfile
from django.utils.encoding import smart_str
from django.urls import reverse

ADDRESS_TYPE=[
    ('billing','Billing Address'),
    ('shipping','Shipping Address'),
]

class Address(models.Model):
    name = models.CharField(max_length=120, null=True, blank=True, help_text='Shipping to? Who is it for?')
    nickname = models.CharField(max_length=120, null=True, blank=True, help_text='Internal Reference Nickname')
    billing_profile = models.ForeignKey(BillingProfile,on_delete=models.CASCADE)
    address_type = models.CharField(max_length=128,choices=ADDRESS_TYPE)
    address_line_1 = models.CharField(max_length=128)
    address_line_2 = models.CharField(max_length=128,null=True,blank=True)
    city = models.CharField(max_length=128)
    state = models.CharField(max_length=128)
    country = models.CharField(max_length=50,default='India')
    postal_code = models.PositiveIntegerField()

    def __str__(self):
        if self.nickname:
            return str(self.nickname)
        return smart_str(self.address_line_1)
    
    def get_absolute_url(self):
        return reverse("address-update", kwargs={"pk": self.pk})

    def get_short_address(self):
        for_name = self.name 
        if self.nickname:
            for_name = "{} | {},".format( self.nickname, for_name)
        return "{for_name} {line1}, {city}".format(
                for_name = for_name or "",
                line1 = self.address_line_1,
                city = self.city
            )
    
    def get_address(self):
        return "{for_name}\n{line1}\n{line2}\n{city}\n{state}, {postal}\n{country}".format(
                for_name = self.name or "",
                line1 = self.address_line_1,
                line2 = self.address_line_2 or "",
                city = self.city,
                state = self.state,
                postal= self.postal_code,
                country = self.country
            )




