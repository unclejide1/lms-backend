from django.db import models
from shortuuid.django_fields import ShortUUIDField
from django.utils.html import mark_safe
from django.utils import timezone
from django.dispatch import receiver
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save
from django.dispatch import receiver
from django_ckeditor_5.fields import CKEditor5Field

from userauths.models import User, Profile

from moviepy.editor import VideoFileClip

from datetime import timedelta  # Import timedelta for duration conversion

STATUS = (
    ("Draft", "Draft"),
    ("Disabled", "Disabled"),
    ("Rejected", "Rejected"),
    ("In Review", "In Review"),
    ("Published", "Published"),
)

VENDOR_COURSE_STATUS = (
    ("Draft", "Draft"),
    ("Disabled", "Disabled"),
    ("Published", "Published"),
)

PAYMENT_STATUS = (
    ("Paid", "Paid"),
    ("Processing", "Processing"),
    ("Failed", 'failed'),
)

NOTIFICATION_TYPE = (
        ("New Order", "New Order"),
        ("New Review", "New Review"),
        ("New Course Question", "New Course Question"),
        ("Course Published", "Course Published"),
    )


RATINGS = (
    (1, "1"),
    (2, "2"),
    (3, "3"),
    (4, "4"),
    (5, "5"),
)

LEVEL = (
    ("Beginner", "Beginner"),
    ("Intermediate", "Intermediate"),
    ("Advanced", "Advanced"),
)


LANGUAGE = (
    ("English", "English"),
    ("Spanish", "Spanish"),
    ("French", "French"),
)


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    image = models.FileField(upload_to="course-file", blank=True, null=True, default="default.jpg")
    full_name = models.CharField(max_length=100)
    bio = models.CharField(max_length=100, null=True, blank=True)
    facebook = models.URLField(null=True, blank=True)
    twitter = models.URLField(null=True, blank=True)
    linkedin = models.URLField(null=True, blank=True)
    about = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=100)
    # my_students = models.ManyToManyField()

    def __str__(self):
        return self.full_name
    
    def students(self):
        return CartOrderItem.objects.filter(teacher=self)

    def average_rating(self):
        average_rating = Review.objects.filter(course__teacher=self).aggregate(avg_rating=models.Avg('rating'))
        return average_rating['avg_rating']

    def courses(self):
        return Course.objects.filter(teacher=self)
    
    def review(self):
        return Course.objects.filter(teacher=self).count()
    

class Category(models.Model):
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to="course-file", default="category.jpg", null=True, blank=True)
    active = models.BooleanField(default=True)
    slug = models.SlugField(unique=True, null=True, blank=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ('title',)

    def thumbnail(self):
        return mark_safe('<img src="%s" width="50" height="50" style="object-fit:cover; border-radius: 6px;" />' % (self.image.url))

    def __str__(self):
        return self.title
    
    def course_count(self):
        return Course.objects.filter(category=self).count()

    def save(self, *args, **kwargs):
        if self.slug == "" or self.slug is None:
            self.slug = slugify(self.title)
        super(Category, self).save(*args, **kwargs) 

class Course(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    file = models.FileField(upload_to="course-file", blank=True, null=True)
    image = models.FileField(upload_to="course-file", blank=True, null=True, default="course.jpg")
    title = models.CharField(max_length=100)
    description = CKEditor5Field('Text', config_name='extends')
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Sale Price")
    level = models.CharField(choices=LEVEL, max_length=50, default="Beginner")
    language = models.CharField(choices=LANGUAGE, max_length=50, default="English" )
    platform_status = models.CharField(choices=STATUS, max_length=50, default="published")
    teacher_course_status = models.CharField(choices=VENDOR_COURSE_STATUS, max_length=50, default="published")
    featured = models.BooleanField(default=False, verbose_name="Marketplace Featured")
    rating = models.IntegerField(default=0, null=True, blank=True)
    course_id = ShortUUIDField(unique=True, length=6, max_length=30, alphabet="1234567890")
    slug = models.SlugField(null=True, blank=True)
    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        self.slug = slugify(self.title) + "-" + str(self.id)
        super(Course, self).save(*args, **kwargs) 

    def students(self):
        return EnrolledCourse.objects.filter(course=self)
    
    def curriculum(self):
        return Variant.objects.filter(course=self)
    
    def variant(self):
        return Variant.objects.filter(course=self)


    def lectures(self):
        return VariantItem.objects.filter(variant__course=self)
            
    def thumbnail(self):
        return mark_safe('<img src="%s" width="50" height="50" style="object-fit:cover; border-radius: 6px;" />' % (self.image.url))
   

    def average_rating(self):
        average_rating = Review.objects.filter(course=self).aggregate(avg_rating=models.Avg('rating'))
        return average_rating['avg_rating']
    
    def rating_count(self):
        return Review.objects.filter(course=self).count()
    
    def reviews(self):
        return Review.objects.filter(course=self, active=True)
    

class Variant(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=1000, verbose_name="Variant Name", null=True, blank=True)
    variant_id = ShortUUIDField(length=10, max_length=25, alphabet="1234567890")
    date = models.DateTimeField(auto_now_add=True)

    def get_items(self):
        return VariantItem.objects.filter(variant=self)

    class Meta:
        ordering = ["date"]
        verbose_name_plural = "Variant"

    def __str__(self):
        return self.title
    
    def items(self):
        return VariantItem.objects.filter(variant=self)
    
    def get_items(self):
        return VariantItem.objects.filter(variant=self)

    def variant_items(self):
        return VariantItem.objects.filter(variant=self)

import math

class VariantItem(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='variant_items')
    title = models.CharField(max_length=1000, verbose_name="Lecture Title", null=True, blank=True)
    description = models.TextField(max_length=200, verbose_name="Lecture Description", null=True, blank=True)
    file = models.FileField(upload_to="course-file", verbose_name="Lecture File", null=True, blank=True)
    duration = models.DurationField(null=True, blank=True) 
    content_duration = models.CharField(null=True, blank=True, max_length=1000) 
    date = models.DateTimeField(auto_now_add=True)
    preview = models.BooleanField(default=False)
    variant_item_id = ShortUUIDField(length=10, max_length=25, alphabet="1234567890")

    class Meta:
        ordering = ["date"]
        verbose_name_plural = "Variant Item"

    def __str__(self):
        return f"{self.variant.title} - {self.title}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Call the original save() method first

        if self.file:
            clip = VideoFileClip(self.file.path)
            duration_seconds = clip.duration
            self.duration = timedelta(seconds=duration_seconds)

            # Convert duration to minutes and seconds
            minutes, remainder = divmod(duration_seconds, 60)

            # Round seconds to nearest integer using round or math.floor
            # seconds = round(remainder)  # Round to nearest integer

            # Alternatively, round down using math.floor
            minutes = math.floor(minutes)
            seconds = math.floor(remainder)

            # Construct the human-readable duration string
            duration_text = f"{minutes}m {seconds}s"

            # Optionally, you can store the duration_text in a separate field
            # self.duration_text = duration_text
            # super().save(update_fields=['duration_text'])

            self.content_duration = duration_text
            super().save(update_fields=['content_duration'])


class Question_Answer(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=1000, null=True, blank=True)
    qa_id = ShortUUIDField(length=10, prefix="QA", max_length=25, alphabet="1234567890")
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.course.title}'

    class Meta:
        ordering = ['-date']
    
    def messages(self):
        return Question_Answer_Message.objects.filter(question=self)

    def profile(self):
        return Profile.objects.get(user=self.user)
    

class Question_Answer_Message(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    question = models.ForeignKey(Question_Answer, on_delete=models.SET_NULL, null=True, blank=True)
    message = models.TextField(null=False, blank=False)
    qam_id = ShortUUIDField(length=10, prefix="QA", max_length=25, alphabet="1234567890")
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.course.title}'

    class Meta:
        ordering = ['date']

    def profile(self):
        return Profile.objects.get(user=self.user)
    

class Certificate(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    certificate_id = ShortUUIDField(length=10, prefix="CT", max_length=25, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890")
    date = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f'{self.user.username} - {self.course.title}'

    class Meta:
        ordering = ['-date']

class Cart(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    price = models.DecimalField(decimal_places=2, max_digits=12, default=0.00, null=True, blank=True)
    tax_fee = models.DecimalField(decimal_places=2, max_digits=12, default=0.00, null=True, blank=True)
    total = models.DecimalField(decimal_places=2, max_digits=12, default=0.00, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    cart_id = models.CharField(max_length=1000, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.cart_id} - {self.course.title}'

class CartOrder(models.Model):
    teachers = models.ManyToManyField(Teacher, blank=True)
    student = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="student", blank=True)
    sub_total = models.DecimalField(default=0.00, max_digits=12, decimal_places=2)
    tax_fee = models.DecimalField(default=0.00, max_digits=12, decimal_places=2)
    total = models.DecimalField(default=0.00, max_digits=12, decimal_places=2)
    payment_status = models.CharField(max_length=100, choices=PAYMENT_STATUS, default="initiated")
    initial_total = models.DecimalField(default=0.00, max_digits=12, decimal_places=2, help_text="The original total before discounts")
    saved = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True, help_text="Amount saved by customer")
    full_name = models.CharField(max_length=1000)
    email = models.CharField(max_length=1000)
    country = models.CharField(max_length=100, null=True, blank=True)
    coupons = models.ManyToManyField('api.Coupon', blank=True)
    stripe_session_id = models.CharField(max_length=200,null=True, blank=True)
    oid = ShortUUIDField(length=10, prefix="D", max_length=25, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890")
    date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "Cart Order"

    def __str__(self):
        return self.oid

    def order_items(self):
        return CartOrderItem.objects.filter(order=self)

class CartOrderItem(models.Model):
    order = models.ForeignKey(CartOrder, on_delete=models.CASCADE, related_name="orderitem")
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="order_item")
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    tax_fee = models.DecimalField(default=0.00, max_digits=12, decimal_places=2, help_text="Estimated Vat based on delivery country = tax_rate * (total + shipping)")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Grand Total of all amount listed above")
    initial_total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text="Grand Total of all amount listed above before discount")
    saved = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True, help_text="Amount saved by customer")
    coupon = models.ManyToManyField("api.Coupon", blank=True)
    applied_coupon = models.BooleanField(default=False)
    oid = ShortUUIDField(length=10, prefix="D", max_length=25, alphabet="ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890")
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        verbose_name_plural = "Cart Order Item"
        ordering = ["-date"]
        
    def thumbnail(self):
        return mark_safe('<img src="%s" width="50" height="50" style="object-fit:cover; border-radius: 6px;" />' % (self.course.image.url))
   
    def order_id(self):
        return f"Order ID #{self.order.oid}"
    
    def payment_status(self):
        return f"{self.order.payment_status}"
    
    def __str__(self):
        return self.oid
    
class CompletedLesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    variant_item = models.ForeignKey(VariantItem, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.course.title}'

    class Meta:
        ordering = ['-date']

class EnrolledCourse(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    order_item = models.ForeignKey(CartOrderItem, on_delete=models.SET_NULL, null=True)
    enrollment_id = ShortUUIDField(length=20, prefix="ENR", max_length=50, alphabet="1234567890")
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.user:
            return f'{self.user.username} - {self.course.title}'
        else:
            return f'{self.course.title}'

    class Meta:
        ordering = ['-date']

    def lectures(self):
        return VariantItem.objects.filter(variant__course=self.course)

    def completed_lesson(self):
        return CompletedLesson.objects.filter(course=self.course, user=self.user)
    
    def curriculum(self):
        return Variant.objects.filter(course=self.course)
    
    def note(self):
        return Note.objects.filter(course=self.course, user=self.user)

    def question_answer(self):
        return Question_Answer.objects.filter(course=self.course)

    def review(self):
        return Review.objects.filter(course=self.course, user=self.user).first()


class Note(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, blank=True, null=True)
    title = models.CharField(max_length=1000, null=True, blank=True)
    note = models.TextField()
    note_id = ShortUUIDField(length=20, prefix="NT", max_length=50, alphabet="1234567890")
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Note Pad"
        ordering = ["-date"]
        
    def __str__(self):
        return f"{self.course.title} - {self.user.username}"

  

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    course = models.ForeignKey(Course, on_delete=models.SET_NULL, blank=True, null=True, related_name="reviews")
    review = models.TextField()
    rating = models.IntegerField(choices=RATINGS, default=None)
    reply = models.CharField(null=True, blank=True, max_length=1000)
    active = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Reviews & Rating"
        ordering = ["-date"]
        
    def __str__(self):
        if self.course:
            return self.course.title
        else:
            return "Review"
        
    def get_rating(self):
        return self.rating
    
    def profile(self):
        return Profile.objects.get(user=self.user)
    
@receiver(post_save, sender=Review)
def update_course_rating(sender, instance, **kwargs):
    if instance.course:
        instance.course.save()

        
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    order = models.ForeignKey(CartOrder, on_delete=models.SET_NULL, null=True, blank=True)
    order_item = models.ForeignKey(CartOrderItem, on_delete=models.SET_NULL, null=True, blank=True)
    review = models.ForeignKey(Review, on_delete=models.CASCADE, null=True, blank=True)
    type = models.CharField(max_length=100, choices=NOTIFICATION_TYPE)
    seen = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Notification"
    
    def __str__(self):
        if self.order:
            return self.order.oid
        else:
            return "Notification"

class Coupon(models.Model):
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, related_name="coupon_teacher")
    used_by = models.ManyToManyField(User, blank=True)
    code = models.CharField(max_length=1000)
    discount = models.IntegerField(default=1)
    date = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
   
    def __str__(self):
        return self.code
    
    class Meta:
        ordering =['-date']

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="wishlist")
    
    def __str__(self):
        return self.course.title
        

  
class Country(models.Model):
    name = models.CharField(max_length=500)
    tax_rate = models.IntegerField(default=5, help_text="Numbers added here are in percentage (5 = 5%)")
    active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Country"

    def __str__(self):
        return f"{self.name}"