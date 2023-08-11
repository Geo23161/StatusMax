from django.shortcuts import render, redirect
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .permissions import *
from rest_framework.response import Response
import requests
import json
from .models import *
import random
from .ip2location import get_quart
from .algo import set_audiences,  get_new_point
from .core import Kkiapay
import time

pays_codes_indicatifs = {
    "BJ": "+229",
    "US": "+1",
    "FR": "+33",
    "GB": "+44",
    "CI": "+225",
    "TG": "+228"
}


def val(key):
    return GeoxDetails.objects.get(key=key).value


def get_unique_code(): return random.randint(10000000, 99999999)


@api_view(['GET', 'HEAD'])
@permission_classes([IsAuthenticated])
def ping(request):
    return Response({'done': True})


@api_view(["GET"])
def search_place(rqt, name):
    req = requests.get(
        f'https://maps.googleapis.com/maps/api/place/textsearch/json?key=AIzaSyDNoBJJXRj_p5miy5gSPGazRa4Mr-95D18&query={name}')
    results = json.loads(req.content)['results']
    return Response({
        'done': True,
        'result': results
    })


@api_view(["POST"])
def register_view(request):
    name = request.POST.get('name')
    email = request.POST.get('email')
    password = request.POST.get('password')
    quart = request.POST.get('quart')
    exist = User.objects.filter(email=email).exists()
    if exist:
        return Response({
            'done': False
        })
    user = User.objects.create_user(
        name=name, email=email, quart=quart, password=password)
    commerce = request.POST.get('commerce')
    description = request.POST.get('description')
    if commerce and description:
        company = Company.objects.create(
            creator=user, name=commerce, description=description)
        company.users.add(user)
    
    return Response({
        'done': True
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def whatsapp_auth(request):
    number = request.data.get('number')
    
    country = request.data.get('country')
    if country:
        request.user.country = country
        request.user.save()
    if GeoxDetails.objects.filter(key = 'is:prod').exists() :
        if User.objects.filter(whatsapp = pays_codes_indicatifs[country] + number).exists() :
            return Response({
                'done' : False,
                'reason' : 'Ce numero whatsapp a déja été utilisé.'
            })
    number = pays_codes_indicatifs[country] + number
    gd = GeoxDetails.objects.create(
        key="code:user:" + str(request.user.pk), value=get_unique_code())
    try:
        send_messages(get_auth_data(number, gd.value), 'auth', can_log=False)
    except Exception as e:
        print(e)
        return Response({
            'done': False,
            'reason': "Le numero whatsapp " + number + " est invalide."
        })
    request.user.uwhatsapp = number
    request.user.save()
    return Response({
        'done': True,
        'result': number

    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_code(request):
    code = request.data.get('code')
    number = request.data.get('number')
    gd = GeoxDetails.objects.filter(
        key="code:user:" + str(request.user.pk), value=code)
    request.user.whatsapp = number
    request.user.save()
    if gd.exists():
        gd.delete()
        return Response({
            'done': True
        })
    return Response({
        'done': False
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_register_stp(request):
    stp = 0
    if request.user.uwhatsapp:
        stp += 1
    if request.user.whatsapp and request.user.uwhatsapp:
        stp += 1
    story = UserStories.objects.filter(user=request.user)
    if story.exists() and request.user.whatsapp and request.user.uwhatsapp:
        if story.first().taille:
            stp += 1
    return Response({
        'done': True,
        'result': stp
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_interests(request):
    boxl = Interest.objects.filter(box = None)
    restd = {}
    for box in boxl :
        restd['inter:' + str(box.pk)] = InterestSerializers(box.subs.all(), many = True).data

    return Response({
        'done': True,
        'result': InterestSerializers(Interest.objects.all(), many=True).data,
        'boxl' : InterestSerializers(boxl, many = True).data,
        'restd' : restd
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_professions(request):
    return Response({
        'done': True,
        'result': ProfessionSerializers(Profession.objects.all(), many=True).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_stories(request):
    taille = request.data.get('taille')
    ages = json.loads(request.data.get('ages'))
    girls_num = request.data.get('girls_num')
    my_interests = [p['id'] for p in json.loads(request.data.get('interests'))]
    my_profs = [p['id'] for p in json.loads(request.data.get('professions'))]
    story = UserStories.objects.get_or_create(user=request.user)[0]
    story.taille = int(taille)
    story.min_age = int(ages['lower'])
    story.max_age = int(ages['upper'])
    """
    stories = UserStories.objects.filter(pk__in=[story.pk])
    stories = stories.update(taille=int(taille), men_per=int(taille) - int(girls_num),
                             wmen_per=int(girls_num), min_age=int(ages['lower']), max_age=int(ages['upper']))
    """
    for interest in story.d_interest.all():
        story.d_interest.remove(interest)
    for prof in story.professions.all():
        story.professions.remove(prof)
    for interest in my_interests:
        story.d_interest.add(interest)
    for prof in my_profs:
        story.professions.add(prof)
    media_id = request.data.get('media_id')
    if int(media_id) :
        media = MediaPost.objects.get(pk = int(media_id))
        story.picture = media.image.url
    story.save()
    def find_audiences():
        story = UserStories.objects.get_or_create(user=request.user)[0]
        for campaign in Campaign.objects.all():
            st = get_new_point(story, campaign)
            if st['point']:
                Audiences.objects.create(
                    campaign=campaign, story=st['story'], point=st['point'])
                for post in campaign.posts.all() : post.save()
                    
    send_by_thread(find_audiences)
    return Response({
        'done': True,
        'result' : story.pk,
        'quiz' : get_value('quiz:link') + f'{story.pk}/',
        'quizObj' : {
            'title' : "Aide-moi à mieux te connaître",
            'text' : "Je suis maintenant membre de StatusMax, et pour plus de statuts interessant, prends quelques secondes pour repondre à ce quiz afin de me permettre de mieux te connaître.",
            'url': get_value('quiz:link') + f'{story.pk}/',
            'dialogTitle' : "Invitez votre audience"
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_details(request):
    my_story = UserStories.objects.get(user=request.user)

    return Response({
        'done': True,
        'result': {
            'taille': my_story.taille,
            'ages': {
                'lower': my_story.min_age,
                'upper': my_story.max_age
            },
            'girls_num': my_story.taille - my_story.men_per,
            'interests': InterestSerializers(my_story.d_interest.all(), many=True).data,
            'professions': ProfessionSerializers(my_story.professions.all(), many=True).data,
            'picture' : my_story.get_my_picture()
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_home(request):
    my_story = UserStories.objects.get(user=request.user)
    accepts = [p.id for p in my_story.get_en_cours() + my_story.get_payed()]
    homeObj = sorted([
        {
            'slug': "en_cours",
            "name": "En cours",
            "desc": "Les posts que vous avez acceptés récemment",
            "medias": MediaSerializer([p.media for p in my_story.get_en_cours()[:7]], many=True).data,
            "value": my_story.en_cours_val()
        },
        {
            'slug': "proposed",
            "name": "Proposés",
            "desc": "Les posts que nous vous proposons pour la semaine",
            "medias": MediaSerializer([p.media for p in my_story.proposed_posts.all().exclude(id__in=accepts)[:7]], many=True).data,
            "value": my_story.get_values(my_story.proposed_posts.all().exclude(id__in=accepts))
        },
        {
            'slug': "payed",
            "name": "Payés",
            "desc": "Les posts qui vous ont déjà été payés.",
            "medias": MediaSerializer([p.media for p in my_story.get_payed()[:7]], many=True).data,
            "value": my_story.payed_val()
        }
    ], key=lambda e: len(e['medias']), reverse=True)
    return Response({
        'done': True,
        'result': homeObj,
        'story' : my_story.pk
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_home_from_slug(request, slug):
    my_story = UserStories.objects.get(user=request.user)
    pks = json.loads(request.data.get('pks'))
    accepts = [p.id for p in my_story.get_en_cours() + my_story.get_payed()]
    homeObj = {
        'en_cours': {
            'slug': "en_cours",
            "name": "En cours",
            "desc": "Les posts que vous avez acceptés récemment",
            "medias": PostSerializer([p for p in my_story.get_en_cours() if not p.pk in pks], many=True).data,
            "value": my_story.en_cours_val()
        },
        "proposed": {
            'slug': "proposed",
            "name": "Proposés",
            "desc": "Les posts que nous vous proposons pour la semaine",
            "medias": PostSerializer([p for p in my_story.proposed_posts.all().exclude(id__in=accepts) if not p.pk in pks], many=True).data,
            "value": my_story.get_values(my_story.proposed_posts.all().exclude(id__in=accepts))
        },
        "payed": {
            'slug': "payed",
            "name": "Payés",
            "desc": "Les posts qui vous ont déjà été payés.",
            "medias": PostSerializer([p for p in my_story.get_payed() if not p.pk in pks], many=True).data,
            "value": my_story.payed_val()
        }
    }
    return Response({
        'done': True,
        'result': homeObj[slug],
        'price': my_story.price()
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_post(request):
    post = Post.objects.get(pk=int(request.data.get('post')))
    
    goal = int(request.data.get('goal'))
    my_story = UserStories.objects.get(user=request.user)
    if int(int(GeoxDetails.objects.get(key ='price:10:' + post.get_media_typ()).value) * goal / 10) > (post.total_invest - post.already_used) :
        return Response({
            'done' : False,
            'reason' : "La somme restante pour ce post ne peut que vous payez pour un nombre de vue inférieure à " + str(int((post.total_invest - post.already_used)/my_story.price() * 10)) + "."
        })
    accepted = AcceptedPost.objects.create(
        post=post, story=my_story, goals=goal, payc=int(int(GeoxDetails.objects.get(key ='price:10:' + post.get_media_typ() + ':real').value) * goal / 10))
    my_story.proposed_posts.remove(post)
    my_story.save()
    return Response({
        'done': True,
        'result': accepted.pk
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_preuve(request):
    post = Post.objects.get(pk=int(request.data.get('post')))
    my_story = UserStories.objects.get(user=request.user)
    accepted = AcceptedPost.objects.filter(
        post__pk=post.pk, story__pk=my_story.pk)
    if not accepted.exists():
        return Response({
            'done': True,
            'result': "",
            'status': "",
            "errors": "",
            "vue_nb": 0
        })
    else:
        return Response({
            'done': True,
            'result': accepted.first().get_preuve(),
            'status': accepted.first().get_status(),
            "errors": accepted.first().get_errors(),
            'vue_nb': accepted.first().result
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_preuve(request):
    post = Post.objects.get(pk=int(request.POST.get('post')))
    my_story = UserStories.objects.get(user=request.user)
    accepted = AcceptedPost.objects.filter(
        post__pk=post.pk, story__pk=my_story.pk).first()
    file = request.FILES.get('preuve')
    accepted.preuve = file
    accepted.save()
    return Response({
        'done': True,
        'result': accepted.get_preuve()
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_checked(request):
    nb_vues = int(request.data.get('nb_vues'))
    post = Post.objects.get(pk=int(request.data.get('post')))
    my_story = UserStories.objects.get(user=request.user)
    accepted = AcceptedPost.objects.filter(
        post__pk=post.pk, story__pk=my_story.pk).first()
    accepted.result = nb_vues
    accepted.status = "En cours de traitement"
    accepted.error = None
    accepted.save()
    return Response({
        'done': True,
        'result': 0
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_payments(request):
    my_story = UserStories.objects.get(user=request.user)
    has_retr = Payment.objects.filter(story=my_story).exclude(
        name="Versement").exclude(status="Effectué").exists()
    return Response({
        'done': True,
        'result': {
            'total': my_story.get_total(),
            'dispo': my_story.get_rest(),
            'price_image': get_value('price:10:image:real'),
            'price_video': get_value('price:10:video:real'),
            "payments": PaymentSerializer(my_story.payments.all().order_by("-created_at"), many=True).data,
            "momo": MomoSerializer(my_story.momo).data if my_story.momo else 0,
            
        },
        'has_retr': has_retr
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def retire_all(request):
    my_story = UserStories.objects.get(user=request.user)
    payment = Payment.objects.create(
        name="Retrait", status="En cours", montant=my_story.get_rest(), story=my_story)

    return Response({
        'done': True,
        'result': PaymentSerializer(payment).data,
        'has_retr': Payment.objects.filter(story=my_story).exclude(name="Versement").exclude(status="Effectué").exists()
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_momo(request):
    country = request.data.get('country')
    number = request.data.get('number')
    name = request.data.get('name')
    momo = MoMoCompte.objects.create(
        name=name, number=pays_codes_indicatifs[country] + number)
    my_story = UserStories.objects.get(user=request.user)
    my_story.momo = momo
    my_story.save()
    return Response({
        'done': True,
        'result': MomoSerializer(momo).data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_params(request):
    my_story = UserStories.objects.get(user=request.user)

    return Response({
        'done': True,
        'result': {
            'actif': my_story.is_actif,
            'whatsapp': my_story.user.whatsapp,
            'momo': MomoSerializer(my_story.momo).data,
            'admin': GeoxDetails.objects.get(key='admin:whatsapp').value,
            'privacy': GeoxDetails.objects.get(key='privacy_policy').value,
            'story' : my_story.pk
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_company(request):
    company = request.user.company_in.all().first()
    return Response({
        'done': True,
        'result': CompanySerializers(company).data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_posts(request):
    company = request.user.company_in.all().first()
    def check_or_create_notif():
        notifs = Notifications.objects.filter(
            text__icontains="Bienvenu sur StatusMax Buisness", typ='buis', company=company)
        if not notifs.exists():
            notif = Notifications.objects.create(company=company, text="Bienvenu sur StatusMax Buisness! Etes-vous prêt a atteindre plus de clients? Créez une campagne maintenant.",
                                                 image=GeoxDetails.objects.get(key='notif:image:welcome').value, typ='buis', action_url="/create")
            notif.send_now()
    send_by_thread(check_or_create_notif)
    pks = json.loads(request.data.get('pks'))
    return Response({
        'done': True,
        'result': PostBuisSerializer(company.posts.all().exclude(pk__in=pks).order_by('-created_at'), many=True).data,
        'has_next': len(pks) < company.posts.all().count(),
        'state': company.status == 'on'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_update(request):
    company = request.user.company_in.all().first()
    posts = company.posts.all()
    pks = json.loads(request.data.get('pks'))
    return Response({
        'done': True,
        'result': PostBuisSerializer(posts.filter(pk__in = pks).order_by('-created_at'), many=True).data,
        'state': company.status == 'on'
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsPostOwner])
def get_my_post(request):
    return Response({
        'done': True,
        'result': PostDetailSerializer(Post.objects.get(pk=int(request.data.get('post')))).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsPostOwner])
def set_budget(request):
    new_b = request.data.get('new_b')
    post = Post.objects.get(pk=int(request.data.get('post')))
    post.total_invest = int(new_b)
    post.save()
    return Response({
        'done': True,
        'result': PostDetailSerializer(Post.objects.get(pk=int(request.data.get('post')))).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_media(request):
    typ= request.POST.get('typ')
    image = request.FILES.get('image')
    if typ == 'profil' :
        media = MediaPost.objects.create(
            image=image, name='profil:' + str(request.user.pk))
        return Response({
            'done' : True,
            'result' : {
                'url' : media.get_url(),
                'pk' : media.pk
            }
        })
    video = request.FILES.get('video')
    id = int(request.POST.get('id'))
    if not id:
        media = MediaPost.objects.create(
            image=image, name='user:' + str(request.user.pk))
    else:
        media = MediaPost.objects.get(pk=id)
        media.image = image
        media.save()
    if video:
        media.video = video
        media.save()
    else:
        media.video = None
        media.save()
    return Response({
        'done': True,
        'result': {
            'image': media.get_url(),
            'video': media.video.url if media.video else "",
            'id': media.pk,
            'typ': 'vid' if media.video else 'img'
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_campaigns(request):
    company = request.user.company_in.all().first()
    campagns = company.campaignes.all().order_by('-created_at')
    return Response({
        'done': True,
        'result': CampaignSerializer(campagns, many=True).data,
        'price:image': GeoxDetails.objects.get(key='price:10:image').value,
        'price:video' : GeoxDetails.objects.get(key = 'price:10:video').value
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_campaign(request):
    ages = json.loads(request.data.get('ages'))
    name = request.data.get('name')
    lieux = json.loads(request.data.get('lieux'))
    interests = Interest.objects.all() if request.data.get('interests') == 'all' else Interest.objects.filter(
        pk__in=[interest['id'] for interest in json.loads(request.data.get('interests'))])
    professions = Profession.objects.all() if request.data.get('professions') == 'all' else Profession.objects.filter(
        pk__in=[interest['id'] for interest in json.loads(request.data.get('professions'))])
    campaign = Campaign.objects.create(quart=json.dumps(
        lieux), min_age=ages['lower'], max_age=ages['upper'], name=name)
    for inter in interests:
        campaign.interests.add(inter)
    for prof in professions:
        campaign.professions.add(prof)
    taille = set_audiences(campaign)
    return Response({
        'done': True,
        'result': {
            'id': campaign.pk,
            "name": campaign.name,
            'taille': taille
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def set_campaign(request):
    campaign = Campaign.objects.get(pk=request.data.get('id'))
    company = request.user.company_in.all().first()
    campaign.company = company
    campaign.save()
    return Response({
        'done': True,
        'result': CampaignSerializer(campaign).data
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_post(request):
    company = request.user.company_in.all().first()
    if company.status == 'off':
        return Response({
            'done': False,
            'code': 350
        })
    media = MediaPost.objects.get(pk=int(request.data.get('media')))
    name = request.data.get('name')
    text = request.data.get('text')
    link = request.data.get('link')
    campaign = Campaign.objects.get(pk=int(request.data.get('campaign')))
    budget = int(request.data.get('budget'))
    post = Post.objects.create(
        media=media, name=name, campaign=campaign, text=text, real_url=link, total_invest=budget, company = company)
    post.url = GeoxDetails.objects.get(key = 'url:debut').value + str(post.pk) + '/'
    post.save()
    return Response({
        'done': True,
        'result': 0
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_min_pay(request):
    company = request.user.company_in.all().first()
    posts = company.posts.all()
    min_pay = 0
    proposed = 0
    for post in posts:
        if post.get_status()[0] != "Terminé":
            price_25 = int(GeoxDetails.objects.get(key = 'price:20:' + post.get_media_typ()).value)
            min_pay += (post.already_used - post.already_payed)
            proposed += (post.total_invest - post.already_payed) if post.already_used > price_25 * 2.9 else 0
    min_pay -= company.get_amount()
    proposed -= company.get_amount()
    return Response({
        'done': True,
        'result': min_pay if min_pay > 0 else 0,
        'key': GeoxDetails.objects.get(key = "kkiapay0" + (":sand" if IS_DEV else "")).value,
        'proposed' : proposed if proposed > 0 else 0
    })

def getKkiapay():
    return Kkiapay(val('kkiapay0'+ (":sand" if IS_DEV else "")), val('kkiapay1'+ (":sand" if IS_DEV else "")), val('kkiapay2'+ (":sand" if IS_DEV else "")), sandbox= IS_DEV)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def make_payment(request):
    transactionId = request.data.get('transactionId')
    company = request.user.company_in.all().first()
    kkia = getKkiapay()
    if kkia.verify_transaction(transaction_id=transactionId).status == "SUCCESS":
        CompanyPay.objects.create(amount=int(
            request.data.get('amount')), company=company)
        company.status = 'on'
        company.save()
        for post in company.posts.all() : 
            if post.get_status()[1] != 'red' :
                post.save()
        return Response({
            'done': True,
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def duplicate_data(request):
    post = Post.objects.get(pk=int(request.data.get('id')))
    return Response({
        'done': True,
        'result': {
            'media': {
                    'image': post.media.get_url(),
                    'video': post.media.video.url if post.media.video else "",
                    'id': post.media.pk,
                    'typ': 'vid' if post.media.video else 'img'
                    },
            'name': post.name,
            'text': post.name,
            'link': post.real_url,
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_notifs(request):
    company = request.user.company_in.all().first()
    notifs = company.notifs.all().order_by('-created_at')[:20]
    return Response({
        'done': True,
        'result': {
            'can_notif': FCMDevice.objects.filter(user=request.user).exists(),
            'notifs': NotifSerializer(notifs, many=True).data
        }
    })


def handle_click(request, id):
    post = Post.objects.get(pk=id)
    ip = request.META['REMOTE_ADDR']
    already_ips = list(json.loads(post.click_ips))
    if not (ip in already_ips):
        already_ips.append(ip)
        Post.objects.filter(pk=post.pk).update(
            clicks=post.clicks + 1, click_ips=json.dumps(already_ips))
    return redirect(post.real_url)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_stats(request):
    company = request.user.company_in.all().first()
    posts = company.posts.all()
    depense = 0
    views = 0
    clicks = 0
    post_start = 0
    post_ended = 0
    posts_p = 0
    for post in posts:
        depense += post.already_payed
        views += post.get_seen()
        clicks += post.clicks
        post_start += 1
        if post.get_status()[0] == "Terminé":
            post_ended += 1
        posts_p += len(post.already_posts())
    return Response({
        'done': True,
        'result': {
            'depense': depense,
            'views': views,
            'clicks': clicks,
            'post_start': post_start,
            'post_ended': post_ended,
            'posts': posts_p
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cpays(request):
    company = request.user.company_in.all().first()
    return Response({
        'done': True,
        'result': CPaySerialiser(company.pays.all().order_by('-created_at'), many=True).data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_cparams(request):
    company = request.user.company_in.all().first()
    min_pay = 0
    for post in company.posts.all():
        if post.get_status()[0] != "Terminé":
            min_pay += (post.already_used - post.already_payed) 
    min_pay -= company.get_amount()
    params = {
        'name': company.name,
        "status": ['Actif' if company.status == 'on' else 'Bloqué', 'green' if company.status == 'on' else 'red'],
        'dispo': company.get_amount(),
        'debt': min_pay if min_pay > 0 else 0,
        'admin': GeoxDetails.objects.get(key='admin:whatsapp').value,
        'privacy': GeoxDetails.objects.get(key='privacy_policy').value
    }
    return Response({
        'done' : True,
        'result' : params
    })


def index(request) :
    status = UserStories.objects.all()
    views = 0
    for st in status : views += st.taille
    return render(request, 'app/index.html', {
        'buis_site' : GeoxDetails.objects.get(key = "buis:site").value,
        'status' : status.count(),
        'views' : views
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def delete_post(request, id) :
    company = request.user.company_in.all().first()
    post = Post.objects.filter(company = company, pk = id)
    if post.exists() :
        post.delete()
        return Response({
            'done' : True,
        })

def privacy(request) :
    return render(request, 'app/privacy.html', {})

def delete_view(request) :
    has_done = False
    if request.method == "POST" :
        email = request.POST.get('email') 
        password = request.POST.get('password')
        us = User.objects.filter(email = email) 
        if us.exists() :
            if us.first().check_password(password) :
                us.delete()
                has_done = True
    return render(request, "app/suppr.html", {
        'has_done' : has_done
    })

def gamify_interest(request, pk) :
    story : UserStories = UserStories.objects.get(pk = pk)
    """
    ip = request.META['REMOTE_ADDR']
    try :
        already_ips = list(json.loads(GeoxDetails.objects.get_or_create(key = "already_reg:" + story.pk)[0]))
    except :
        already_ips = []
    if not (ip in already_ips):
        already_ips.append(ip)
    rest_dic = {}
    box_interests = Interest.objects.all()
    box_list = [ b.name for b in box_interests if not b.box ]
    for box in box_list :
        rest_dic[box] = [i.name for i in Interest.objects.filter(box__name = box)]
    """
    api_get = GeoxDetails.objects.get(key = 'api:url').value + "game_list/"
    api_post = GeoxDetails.objects.get(key = 'api:url').value + "set_games/"
    return render(request, "app/gamify.html", {
        'story' : story,
        'app_link' : GeoxDetails.objects.get(key= 'app:link').value,
        'api_get' : api_get,
        'api_post' : api_post,
        'url': get_value('quiz:link') + f'{story.pk}/',
    })

@api_view(['GET'])
def game_list(request) :
    rest_dic = {}
    box_interests = Interest.objects.all()
    box_list = [ b.name for b in box_interests if not b.box ]
    for box in box_list :
        rest_dic[box] = [i.name for i in Interest.objects.filter(box__name = box)]

    return Response({
        'done' : True,
        'result' : {
            'box_list' : box_list,
            'rest_dic' : rest_dic
        }
    })

@api_view(['POST'])
def set_games(request) :

    story = UserStories.objects.get(pk = int(request.data.get('story')))
    boxs = json.loads(request.data.get('boxs'))
    rests = json.loads(request.data.get('rests'))
    tots = boxs + rests
    ip = request.META['REMOTE_ADDR']
    ciblef = CibleF.objects.get_or_create(ip_address = ip, story = story)[0]
    reply = request.data.get('reply')
    if reply :
        cib = CibleF.objects.get(pk = int(reply))
        tots = [inter.name for inter in cib.interests.all()]
    for inter in tots :
        if not ciblef.interests.all().filter(name = inter).exists() :
            interObj = Interest.objects.get(name = inter)
            ciblef.interests.add(interObj)
            story.d_interest.add(interObj)
    def set_quart() :
        ciblef.quart = json.dumps(get_quart(ip))
        ciblef.save()
    if not ciblef.quart : send_by_thread(set_quart)
    return Response({
        'done' : True,
        'result' : ciblef.pk
    })

@api_view(['GET'])
def cible_stats(request, pk) :
    story = UserStories.objects.get(pk = pk)
    total_c = CibleF.objects.filter(story = story).count()
    cible_per = float(GeoxDetails.objects.get(key = 'cible:per').value)

    return Response({
        'done' : True,
        'result' : {
            'total_c' : total_c,
            'cible_per' : cible_per,
            'good' : True if (total_c / story.taille) > cible_per else False,
            'cibleObj' : {
                    'title' : "Aide-moi à mieux te connaître",
                    'text' : "Je suis maintenant membre de StatusMax, et pour plus de statuts interessant, prends quelques secondes pour repondre à ce quiz afin de me permettre de mieux te connaître.",
                    'url': get_value('quiz:link') + f'{story.pk}/',
                    'dialogTitle' : "Invitez votre audience"
                },
            'must' : int(story.taille * cible_per)
        }
    })

def download_page(request, pk) :
    post = Post.objects.get(pk = pk)
    return render(request,"app/download.html", {
        'post' : post,
        'app_link' : GeoxDetails.objects.get(key= 'app:link').value,
    })
