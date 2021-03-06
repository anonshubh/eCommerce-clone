import math
from django.db import models
from cart.models import Cart
from django.db.models.signals import pre_save,post_save
from django.utils.encoding import smart_str
from ecommerce_src.utils import unique_order_id_generator
from billing.models import BillingProfile
from addresses.models import Address
from django.urls import reverse
from products.models import Product
from django.conf import settings

User = settings.AUTH_USER_MODEL

ORDER_STATUS_CHOICES=[
    ('created','Created'),
    ('paid','Paid'),
    ('shipped','Shipped'),
    ('refunded','Refunded'),
    ('cancelled','Cancelled'),
]

class OrderManagerQuerySet(models.query.QuerySet):
    def by_request(self,request):
        my_profile,created = BillingProfile.objects.get_or_new(request)
        return self.filter(billing_profile=my_profile)
    
    def not_created(self):
        return self.exclude(status = 'created')

class OrderManager(models.Manager):
    
    def get_queryset(self):
        return OrderManagerQuerySet(self.model,using=self._db)
    
    def by_request(self,request):
        return self.get_queryset().by_request(request)

    def get_or_new(self,billing_profile,cart_obj):
        created = False
        qs = self.get_queryset().filter(billing_profile=billing_profile,cart=cart_obj,active=True,status='created')
        if qs.count()==1:
            created = False
            obj = qs.first()
        else:
            obj = self.model.objects.create(cart=cart_obj,billing_profile=billing_profile)
            created = True
        return obj,created

class Order(models.Model):
    billing_profile = models.ForeignKey(BillingProfile,null=True,blank=True,on_delete=models.CASCADE)
    order_id        = models.CharField(max_length=120,editable=False)
    cart            = models.ForeignKey(Cart,on_delete=models.CASCADE)
    shipping_address = models.ForeignKey(Address,related_name='shipping_address',null=True,blank=True,on_delete=models.CASCADE)
    billing_address  = models.ForeignKey(Address,related_name='billing_address',null=True,blank=True,on_delete=models.CASCADE)
    shipping_address_final  = models.TextField(blank=True, null=True)
    billing_address_final   = models.TextField(blank=True, null=True)
    status          = models.CharField(max_length=100,default='created',choices=ORDER_STATUS_CHOICES)
    shipping_total  = models.DecimalField(default=50,max_digits=100,decimal_places=2)
    total           = models.DecimalField(default=0.00,max_digits=100,decimal_places=2)
    active          = models.BooleanField(default=True)
    timestamp       = models.DateTimeField(auto_now_add=True)
    updated         = models.DateTimeField(auto_now=True)

    objects = OrderManager()

    class Meta():
        ordering = ['-timestamp','-updated']

    def __str__(self):
        return smart_str(self.order_id)

    def get_absolute_url(self):
        return reverse("orders:detail",kwargs={'order_id':self.order_id})
    
    def update_total(self):
        self.total = format(math.fsum([self.cart.total + self.shipping_total]),'.2f')
        self.save()
        return self.total
    
    def get_shipping_status(self):
        if self.status == 'refunded':
            return "Refunded Order"
        if self.status == 'shipped':
            return "Shipped"
        if self.status == 'cancelled':
            return "Cancelled"
        else:
            return "Shipping Soon"

    def cancellation(self):
        self.status = 'cancelled'
        self.save()

    def check_done(self):
        shipping_address_required = not self.cart.is_digital
        shipping_done = False
        if shipping_address_required and self.shipping_address:
            shipping_done = True
        elif shipping_address_required and not self.shipping_address:
            shipping_done = False
        else:
            shipping_done = True
        billing_profile = self.billing_profile
        billing_address = self.billing_address
        shipping_address = self.shipping_address
        total = self.total
        if billing_profile and shipping_done and billing_address and total>0:
            return True
        return False

    def update_purchases(self):
        for p in self.cart.products.all():
            obj,created = ProductPurchase.objects.get_or_create(
                order_id = self.order_id,
                product = p,
                billing_profile=self.billing_profile
            )
        return ProductPurchase.objects.filter(order_id=self.order_id).count()
    
    def mark_paid(self):
        if self.status != 'paid':
            if self.check_done:
                self.status = "paid"
                self.save()
                self.update_purchases()
        return self.status

def pre_save_create_order_id(sender,instance,*args,**kwargs):
    if not instance.order_id:
        instance.order_id = unique_order_id_generator(instance)
    qs = Order.objects.filter(cart=instance.cart).exclude(billing_profile=instance.billing_profile)
    if qs.exists():
        qs.update(active=False)
    
    if instance.shipping_address and not instance.shipping_address_final:
        instance.shipping_address_final = instance.shipping_address.get_address()

    if instance.billing_address and not instance.billing_address_final:
        instance.billing_address_final = instance.billing_address.get_address()

pre_save.connect(pre_save_create_order_id,sender=Order)

def post_save_cart_total(sender,instance,created,*args,**kwargs):
    if not created:
        cart_obj = instance
        qs = Order.objects.filter(cart__id=cart_obj.id)
        if qs.count()==1:
            order_obj = qs.first()
            order_obj.update_total()

post_save.connect(post_save_cart_total,sender=Cart)

def post_save_order(sender,instance,created,*args,**kwargs):
    if created:
        instance.update_total()

post_save.connect(post_save_order,sender=Order)


class ProductPurchaseQuerySet(models.query.QuerySet):
    def active(self):
        return self.filter(refunded=False)
    
    def digital(self):
        return self.filter(product__is_digital=True)
    
    def by_request(self,request):
        my_profile,created = BillingProfile.objects.get_or_new(request)
        return self.filter(billing_profile=my_profile)

class ProductPurchaseManager(models.Manager):
    def get_queryset(self):
        return ProductPurchaseQuerySet(self.model,using=self._db)

    def all(self):
        return self.get_queryset().active()
    
    def digital(self):
        return self.get_queryset().active().digital()
    
    def by_request(self,request):
        return self.get_queryset().by_request(request)
    
    def products_by_request(self,request):
        qs = self.by_request(request).digital()
        ids = [x.product.id for x in qs]
        products_qs = Product.objects.filter(id__in=ids).distinct()
        return products_qs

class ProductPurchase(models.Model):
    order_id  = models.CharField(max_length=120,editable=False)
    billing_profile = models.ForeignKey(BillingProfile,on_delete=models.CASCADE)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    refunded = models.BooleanField(default = False)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    objects = ProductPurchaseManager()
    
    def __str__(self):
        return smart_str(self.product.title)