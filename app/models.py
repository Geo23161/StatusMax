from django.db import models
from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
import json
import requests
from rest_framework import serializers
from cloudinary.models import CloudinaryField
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
import threading
from fcm_django.models import FCMDevice
from firebase_admin.messaging import Message, Notification, AndroidNotification, WebpushConfig, WebpushFCMOptions, AndroidConfig, APNSConfig, APNSPayload, Aps
from datetime import datetime, timedelta

# Create your models here.

def send_by_thread(func):
    proc = threading.Thread(target=func)
    proc.start()

def get_value(key) -> str:
    return GeoxDetails.objects.get(key=key).value

IS_DEV = False


class CustomUserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(('The Email must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError(('Superuser must have is_staff'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(('superuser must have is_superuser set to True'))
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=150, blank=True)
    email = models.EmailField(unique=True)
    sex = models.CharField(null=True, blank=True, max_length=10)
    quart = models.TextField(null=True, blank=True)
    country = models.CharField(max_length=15, null=True, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    whatsapp = models.CharField(max_length=15, null=True, blank=True)
    uwhatsapp = models.CharField(max_length=15, null=True, blank=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def get_quart(self):
        return json.loads(self.quart)

class Company(models.Model):
    users = models.ManyToManyField(
        User, null=True, blank=True, related_name="company_in")
    creator = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=150, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=150, default="on")
    def get_amount(self) :
        amount = 0
        for pay in self.pays.all() : amount += pay.amount
        return amount

class CompanyPay(models.Model) :
    created_at = models.DateTimeField(auto_now_add=True)
    amount = models.IntegerField(default=0)
    company = models.ForeignKey(Company, related_name="pays", null=True, blank=True, on_delete=models.CASCADE)
    post = models.ForeignKey('Post', related_name="pays", on_delete=models.CASCADE, null=True, blank=True)

class MediaPost(models.Model):
    image = models.ImageField(upload_to="images/")
    video = CloudinaryField(resource_type='video', null=True, blank=True)
    name = models.CharField(max_length=150, null=True, blank=True)

    def get_url(self):
        return self.image.url

    def is_vid(self):
        return True if self.video else False

    def vid_url(self):
        return "" if not self.video else self.video.url


class GeoxDetails(models.Model):
    key = models.CharField(max_length=150, null=True, blank=True)
    value = models.TextField(null=True, blank=True, default="")

    def __str__(self) -> str:
        return self.key


class Interest(models.Model):
    name = models.CharField(max_length=150, null=True, blank=True)
    box = models.ForeignKey("Interest", related_name="subs",
                            on_delete=models.CASCADE, null=True, blank=True)

    def __str__(self) :
        return self.name

class ProductCat(models.Model):
    name = models.CharField(max_length=150, null=True, blank=True)
    box = models.ForeignKey("ProductCat", related_name="subs",
                            on_delete=models.CASCADE, null=True, blank=True)


class Profession(models.Model):
    name = models.CharField(max_length=150, null=True, blank=True)
    box = models.ForeignKey("Profession", related_name="subs",
                            on_delete=models.CASCADE, null=True, blank=True)
    

class Campaign(models.Model):
    quart = models.TextField(null=True, blank=True)
    min_age = models.IntegerField(default=18)
    max_age = models.IntegerField(default=50)
    sex = models.CharField(max_length=10, default="all")
    interests = models.ManyToManyField(Interest, related_name="in_campaigns")
    professions = models.ManyToManyField(
        Profession, related_name="in_campaigns")
    currency = models.CharField(max_length=10, default="XOF")
    days = models.IntegerField(default=1)
    enchere = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now=True)
    company = models.ForeignKey(
        Company, related_name="campaignes", on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=150, null=True, blank=True)

    def get_quarts(self) :
        return json.loads(self.quart)
    
    def default_name(self) :
        na = ""
        try : 
            for quart in self.get_quarts()[:3] : na += quart['name']
        except :
            pass
        return na

    def get_audiences(self) :
        return [audience.story for audience in self.audiences.all()]
    
    
    def get_audiences_pk(self) :
        return [story.pk for story in self.get_audiences_pk()]
    
    
    
    
class Audiences(models.Model) :
    campaign = models.ForeignKey(Campaign, on_delete=models.CASCADE, related_name="audiences", null=True, blank=True)
    story = models.ForeignKey("UserStories", related_name="audiences_in", on_delete=models.CASCADE, null=True, blank=True)
    point = models.IntegerField(default=0)
    


class Post(models.Model):
    name = models.CharField(max_length=150, null=True, blank=True)
    campaign = models.ForeignKey(
        Campaign, related_name="posts", on_delete=models.CASCADE)
    company = models.ForeignKey(Company, related_name="posts", null=True, blank=True, on_delete=models.CASCADE)
    media = models.ForeignKey(
        MediaPost, related_name="in_posts", on_delete=models.CASCADE)
    text = models.TextField(null=True, blank=True)
    url = models.TextField(null=True, blank=True)
    real_url = models.TextField(null=True, blank=True)
    clicks = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    total_invest = models.IntegerField(default=0)
    already_used = models.IntegerField(default=0)
    already_payed = models.IntegerField(default=0)
    click_ips = models.TextField(null=True, blank=True, default="[]")
    def get_bonus(self) :
        return 0
    
    def get_media_typ(self) :
        return 'video' if self.media.is_vid() else 'image'

    def price_10(self) :
        return int(get_value('price:10:' + self.get_media_typ() + ':real'))
    
    def get_vid_url(self) :
        return self.media.vid_url() if self.get_media_typ() == 'video' else ''

    def get_image(self) :
        return self.media.get_url()  
    
    def get_title(self) :
        return self.campaign.company.name
    
    def get_desc(self) :
        return self.text if self.text else ""
    
    def get_url(self) :
        return self.url if self.url else ""
    
    def get_media(self) :
        return self.media.video if self.media.video else self.media.image

    def get_complete(self) :
        return self.get_desc() + '\n' + self.get_url()
    
    def already_posts(self) :
        return [accepted.story.pk for accepted in self.accepted_stories.all()]
    
    def get_status(self) :
        if self.company.status == "off" :
            return ['Bloqué', 'red']
        posted = self.already_posts()
        if not len(posted) :
            return ['En attente', 'gray']
        if (self.total_invest - self.already_used) < int(GeoxDetails.objects.get(key = 'price:10:' + self.get_media_typ()).value) : 
            return ["Terminé", "blue"]
        return ["En cours (posté par " + str(len(posted)) + ")", "green"]
    
    def get_seen(self) :
        seen_num = 0
        for accepted in self.accepted_stories.all() :
            seen_num += accepted.result
        return seen_num
    
    def get_preuve(self) :
        preuves = []
        for accepted in self.accepted_stories.all().exclude(preuve = None) :
            if(accepted.preuve) : preuves.append(accepted.preuve.url)
        return preuves
    
    def status_number(self) :
        return self.accepted_stories.all().count()
    
    def get_predicted(self) :
        predicted = 0
        for accepted in self.accepted_stories.all() :
            predicted += accepted.goals
        return predicted

    
    
class MoMoCompte(models.Model) :
    name = models.CharField(max_length=150, null=True, blank=True)
    number = models.CharField(max_length=150, null=True, blank=True)
    def get_name(self) :
        return f"Compte Momo: {self.name}"
    
    def __str__(self) -> str:
        return self.name + ' -> ' + self.number

class UserStories(models.Model):
    user = models.ForeignKey(User, null=True, blank=True,
                             related_name="stories", on_delete=models.CASCADE)
    platform = models.CharField(max_length=150, default="whatsapp")
    taille = models.IntegerField(null=True, blank=True)
    men_per = models.IntegerField(null=True, blank=True)
    wmen_per = models.IntegerField(null=True, blank=True)
    min_age = models.IntegerField(null=True, blank=True)
    max_age = models.IntegerField(null=True, blank=True)
    d_interest = models.ManyToManyField(Interest, related_name="in_stories")
    wanted_p = models.ManyToManyField(ProductCat, related_name="in_stories")
    professions = models.ManyToManyField(Profession, related_name="in_stories")
    proposed_posts = models.ManyToManyField(Post, related_name="in_stories")
    is_actif = models.BooleanField(default=True)
    momo = models.OneToOneField(MoMoCompte, null=True, blank=True, related_name="story", on_delete=models.PROTECT)
    picture = models.TextField(null=True, blank=True)

    def get_my_picture(self) :
        return self.picture

    def price(self) :
        return int(GeoxDetails.objects.get(key = 'price:10').value)
    def __str__(self) -> str :
        return self.user.email

    def get_values(self, posts):
        val = 0
        for post in posts:
            val += (self.taille / 10) * (self.price() + post.campaign.enchere)
        return int(val)

    def proposed_val(self):
        val = 0
        for post in self.proposed_posts:
            val += (self.taille / 10) * (self.price() + post.campaign.enchere)
        return val

    def get_en_cours(self):
        return [a.post for a in self.accepted_posts.all() if not a.payed]

    def en_cours_val(self) :
        val = 0
        accepteds = self.accepted_posts.all().exclude(payed= True)
        for post in accepteds :
            val += (post.goals /10) * self.price()
        return int(val)

    def get_payed(self):
        return [a.post for a in self.accepted_posts.all() if a.payed]
    
    def payed_val(self) :
        val = 0
        for a in self.accepted_posts.filter(payed = True) :
            val += (a.result / 10) * self.price() 
        return int(val)
    
    def get_total(self) :
        montant = 0
        for pay in self.payments.filter(name = "Versement") : montant += pay.montant
        return montant
    
    def get_rest(self) :
        montant = self.get_total()
        for pay in self.payments.filter(post = None, status = "Effectué") : montant -= pay.montant
        return montant


class AcceptedPost(models.Model):
    post = models.ForeignKey(Post, null=True, blank=True,
                             related_name="accepted_stories", on_delete=models.PROTECT)
    story = models.ForeignKey(UserStories, null=True, blank=True,
                              related_name="accepted_posts", on_delete=models.CASCADE)
    goals = models.IntegerField(default=10)
    preuve = models.ImageField(upload_to="preuves/", null=True, blank=True)
    payed = models.BooleanField(default=False)
    status = models.CharField(null=True, blank=True, max_length=150)
    error = models.TextField(null=True, blank=True)
    result = models.IntegerField(default=0)
    payc = models.IntegerField(default=0)
    def get_preuve(self) :
        return self.preuve.url if self.preuve else ""
    def get_status(self) :
        return self.status if self.status else ""
    def get_errors(self) :
        return self.error if self.error else ""
    def get_value(self) :
        return self.post.get_bonus() + self.story.price()
    
    def post_media(self) :
        return self.post
    
class Payment(models.Model) :
    name = models.CharField(max_length=150, null=True, blank=True)
    status = models.CharField(max_length=150, null= True, blank=True)
    montant = models.IntegerField(default=0)
    story = models.ForeignKey(UserStories, related_name="payments", on_delete=models.CASCADE, null=True, blank=True)
    post = models.ForeignKey(AcceptedPost, null=True, blank=True, on_delete=models.CASCADE )
    created_at = models.DateTimeField(auto_now_add=True)
    def get_color(self) :
        return 'green' if self.status == "Effectué" else 'gray'
    def get_momo(self) :
        return self.story.momo if self.story else 0
    

class CibleF(models.Model) :
    ip_address = models.CharField(max_length=150, null=True, blank=True)
    story = models.ForeignKey(UserStories, related_name="cibles", on_delete=models.CASCADE)
    interests = models.ManyToManyField(Interest, related_name="cibles", null=True, blank=True)
    quart = models.TextField(null=True, blank=True)
    created = models.DateTimeField(auto_now=True)
    
    def get_quart(self) :
        return json.loads(self.quart)

class Notifications(models.Model) :
    company = models.ForeignKey(Company, related_name="notifs", on_delete=models.CASCADE, null=True, blank=True)
    story = models.ForeignKey(UserStories, related_name="notifs", on_delete=models.CASCADE, null=True, blank=True)
    image = models.TextField(null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    typ = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    action_url = models.CharField(max_length=150, null=True, blank=True)
    def send_now(self) :
        users = self.company.users.all() if self.typ == 'buis' else User.objects.filter(pk = self.story.user.pk)
        for user in users :
            device = FCMDevice.objects.filter(user = user)
            if device.exists() :
                device = device.first()
                device.send_message(
                    notification = Message(notification=Notification(title="StatusMax " + ('Buisness' if self.typ == 'buis' else ''), body=self.text)),
                    android = AndroidConfig(notification = AndroidNotification(click_action="FCM_PLUGIN_ACTION")),
                    webpush = WebpushConfig(options = WebpushFCMOptions(link=GeoxDetails.objects.get(key="site:link" + (':buis' if self.typ == 'buis' else ':story')))),
                    apns = APNSConfig(payload = APNSPayload(aps = Aps(category = "GENERAL"))),
                )


# Serializers-------------------------------|||||||||||||||||||*--------------------------||||||||||||||||||||||||||||||||||||||||

class CPaySerialiser(serializers.ModelSerializer) :
    class Meta :
        model = CompanyPay
        fields = ('id', 'amount', 'created_at', 'amount')

class NotifSerializer(serializers.ModelSerializer) :
    class Meta :

        model = Notifications
        fields = ('id', 'image', 'text', 'typ', 'action_url')

class CampaignSerializer(serializers.ModelSerializer) :
    class Meta :
        model = Campaign
        fields = ('id', 'name', 'default_name', 'get_quarts')

class PostDetailSerializer(serializers.ModelSerializer) :
    campaign = CampaignSerializer()
    class Meta :
        model = Post
        fields = ('id', 'get_status', 'name', 'get_image', 'get_seen', 'get_predicted', 'clicks', 'get_media_typ', 'text', 'real_url', 'already_used', 'status_number', 'total_invest', 'campaign', 'get_preuve', 'get_vid_url' )

class PostBuisSerializer(serializers.ModelSerializer) :
    class Meta :
        model = Post
        fields = ('id', 'get_status', 'name', 'get_image', 'get_seen', 'get_predicted', 'clicks', 'get_media_typ' )

class UserCompany(serializers.ModelSerializer) :
    class Meta :
        model = User
        fields = ('id', 'name', 'email')

class CompanySerializers(serializers.ModelSerializer) :
    users = UserCompany(many = True)
    creator = UserCompany()
    class Meta :
        model = Company
        fields = ('id', 'users', 'creator', 'name', 'description')

class MomoSerializer(serializers.ModelSerializer) :
    class Meta :
        model = MoMoCompte
        fields = ("id", 'name', 'number')

class PaymentSerializer(serializers.ModelSerializer) :
    class Meta :
        model = Payment
        fields = ('id', "name", "status", "montant", "get_color")

class MediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaPost
        fields = ('id', "get_url", "is_vid", "vid_url")

class PostSerializer(serializers.ModelSerializer) :
    media = MediaSerializer()
    class Meta :
        model = Post
        fields = ('id', 'media', 'get_bonus', 'get_title', 'get_desc', 'get_url', 'get_complete', "price_10")

class InterestSerializers(serializers.ModelSerializer):
    class Meta:
        model = Interest
        fields = ('id', 'name')


class ProfessionSerializers(serializers.ModelSerializer):
    class Meta:
        model = Profession
        fields = ('id', 'name')


# Whatsap Code for messages
def getENDPOINT():
    return f'https://graph.facebook.com/v15.0/{get_value("WHATSAPP_PHONE_NUMBER_ID")}/messages'


def getHeaders(access):
    return {
        'Authorization': f'Bearer {access}',
        'Content-Type': 'application/json'
    }

"""
def get_notif_data(user : User) :
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": f"{user.whatsapp}",
        "type": "template",
        "template": {
            "name": "post_ready",
            "language": {
                "code": "fr"
            }
        }
    }
    return json.dumps(data)

"""
def get_notif_data(user : User):
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": f"{user.whatsapp}",
        "type": "template",
        "template": {
            "name": "demand_alert",
            "language": {
                "code": "fr"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": "promotion"
                        }
                    ]
                }
            ]
        }
    }
    return json.dumps(data)

def get_auth_data(number, code):
    data = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": f"{number}",
        "type": "template",
        "template": {
            "name": "geox_auth",
            "language": {
                "code": "fr"
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "text": code,
                        }
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "url",
                    "index": "0",
                    "parameters": [
                        {
                            "type": "text",
                            "text": code,
                        }
                    ]
                },
            ]
        }
    }
    return json.dumps(data)


def send_messages(data, slug, can_log=True):
    """
    resp = requests.post(url=getENDPOINT(), headers=getHeaders(
        get_value("WHATSAPP_ACCESS_TOKEN")), data=data)

    if can_log:
        logs = GeoxDetails.objects.get_or_create(key='whatsapp_logs')[0]
        print(resp.status_code, resp.content)
        logs.value += f"$${slug}:<!0{str(resp.content)}0!>"
        logs.save()
    else:
        print(f"\t {resp.content}")
    return resp
    """

#Signals ----------------------||||||||||-------
# 
# 
# -------|||||||||||------------------------------------------

@receiver(post_save, sender=Post)
def update_audiences(sender, instance : Post, **kwargs):
    def update() :
        stories = instance.in_stories.all()
        for story in stories :
            story.proposed_posts.remove(instance)
        al_posts = instance.already_posts()
        price_25 = int(GeoxDetails.objects.get(key = 'price:20:' + instance.get_media_typ()).value)
        audiences = [ aud.story.pk for aud in  instance.campaign.audiences.all().order_by('-point') if not aud.story.pk in al_posts]
        stories_r = UserStories.objects.filter(pk__in= audiences)
        if ((instance.already_used - instance.already_payed ) >= price_25 and ( instance.already_payed != 0) ) or ((instance.already_payed == 0) and (instance.already_used - instance.already_payed) >= price_25 * 3 ) :
            amount= instance.already_used - instance.already_payed
            
            if amount > instance.company.get_amount() :
                instance.company.status = "off"
                instance.company.save()

            else :
                CompanyPay.objects.create(amount = -(instance.already_used - instance.already_payed), company = instance.company, post = instance)
                Post.objects.filter(pk = instance.pk).update(already_payed = instance.already_used)
        if((instance.total_invest - instance.already_used) > int(GeoxDetails.objects.get(key ='price:10:' + instance.get_media_typ()).value) ) :
            for story in stories_r :
                story.proposed_posts.add(instance)
                last_notif : Notifications = story.notifs.all().order_by('-created_at').first()
                if last_notif :
                    if timezone.now() - last_notif.created_at > timedelta(days=1) :
                        send_messages(get_notif_data(story.user), 'user:notif:' + str(story.user.pk))
                else :
                    send_messages(get_notif_data(story.user), 'user:notif:' + str(story.user.pk)) 
        if kwargs['created'] :
            Notifications.objects.create(company = instance.company, text= f"Votre contenu <<{instance.name}>> a été envoyé a plus de {stories_r.count()} personnes pouvant poster. Veuillez suivre ses résultats pour en voir plus.", image = instance.get_image(), typ = 'buis', action_url = "/post/" + str(instance.pk)).send_now()
    send_by_thread(update)

@receiver(post_save, sender=AcceptedPost)
def update_p(sender, instance, **kwargs):
    if kwargs['created'] :
        instance.post.already_used += instance.payc
        instance.post.save()
        
        if len(instance.post.already_posts()) == 1 :
            Notifications.objects.create(company = instance.post.post.company, text= f"Votre contenu <<{instance.post.name}>> a commencé a être posté.", image = instance.get_image(), typ = 'buis', action_url = "/post/" + str(instance.post.pk)).send_now()


@receiver(post_save, sender=CompanyPay)
def send_notif(sender, instance : CompanyPay, **kwargs):
    if instance.amount > 0 :
        Notifications.objects.create(company = instance.post.company if instance.post else instance.company, text= f"Vous avez rechargez votre compte de {instance.amount} FCFA.", image = GeoxDetails.objects.get(key = 'notif:image:payment').value, typ = 'buis', action_url = "/tabs/tab3").send_now()
