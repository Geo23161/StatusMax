from django.contrib import admin
from django.apps import apps
from .models import *

models = apps.get_models()

for model in models :
    if model != AcceptedPost and model != Payment :
        if str(model) != "<class 'fcm_django.models.FCMDevice'>" :
            try :
                admin.site.register(model) 
            except :
                pass

@admin.display(empty_value="???")
def post_media(self, obj) :
    return obj.post.get_media()

@admin.action(description="Valider les preuves sélectionnées")
def validate_preuve(modeladmin, request, queryset) :
    for query in queryset :
        query.status = "Resultat validé"
        Payment.objects.get_or_create(name = "Versement", status = "Effectué", montant = query.payc if query.result >= query.goals else (query.result/10 * int(GeoxDetails.objects.get(key = 'price:10').value)), story = query.story, post = query)
        query.payed = True
        query.save()
    
@admin.action(description="Rejeter les preuves en raison des vues")
def reject_preuve_vue(modeladmin, request, queryset) :
    for query in queryset :
        query.status = "Resultat rejeté"
        query.preuve = None
        query.error = "Le nombres de vues sur votre capture d'ecran est illisible ou ne correspond pas au resultat que vous avez saisi. Veuillez resoumettre une capture puis renvoyer."
        query.save()

@admin.action(description="Rejeter les preuves")
def reject_preuve(modeladmin, request, queryset) :
    for query in queryset :
        query.status = "Resultat rejeté"
        query.preuve = None
        query.error = "L'image sur votre capture ne correspond pas au post. Veuillez resoumettre une capture puis renvoyer."
        query.save()

@admin.action(description="Marque comme effectué")
def set_done(modeladmin, request, queryset) :
    queryset.update(status = "Effectué")

class AcceptedPostAdmin(admin.ModelAdmin) :
    list_display = ["story" ,'post', 'result', 'preuve', 'status']
    actions = [validate_preuve, reject_preuve, reject_preuve_vue ]

class PaymentAdmin(admin.ModelAdmin) :
    list_display = ['name', 'status', 'montant', 'get_momo']
    
admin.site.register(AcceptedPost, AcceptedPostAdmin)
admin.site.register(Payment, PaymentAdmin)










