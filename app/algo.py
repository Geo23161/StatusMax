import googlemaps
from datetime import datetime
from .models import Campaign, UserStories, Audiences, GeoxDetails
import haversine

gmaps = googlemaps.Client(key="AIzaSyDNoBJJXRj_p5miy5gSPGazRa4Mr-95D18")

def get_new_point(story, campaign) :
    my_dic = {
        'story' : story,
        'point' : 0
    }
    distances = []
    cibles = story.cibles.all()
    for cib in cibles :
        my_dic['point'] += (cib.interests.all() & campaign.interests.all()).count()
        dis = []
        mquart = cib.get_quart()
        for quart in campaign.get_quarts() :
            if quart['typ'] == 'country' :
                country = gmaps.reverse_geocode((mquart['lat'], mquart['lng']), result_type = 'country')[0]['formatted_address']
                if country == quart['formatted_address'] :
                    dis.append(1)
                else : dis.append(0)
            else :
                dist = haversine.haversine(point1=(quart['lat'], quart['lng']), point2=(mquart['lat'], mquart['lng']), unit=haversine.Unit.KILOMETERS)
                dis.append(1 if dist < 10 else (0.5 if dist < 20 else 0.1))
        distances.append(max(dis))
    if not my_dic['point'] and GeoxDetails.objects.filter(key = 'is:strict').exists()  :
        return my_dic
    cib_c = cibles.count() if cibles.count() else 1
    my_dic['point'] += int(sum(distances) / (cib_c))
    ages_intersec =len( set(range(story.min_age, story.max_age + 1)).intersection(range(campaign.min_age, campaign.max_age + 1)))
    my_dic['point'] += 1 if ages_intersec > 10 else (0.8 if ages_intersec > 5 else 0.5)
    my_dic['point'] += 1 if len(story.professions.all() & campaign.professions.all()) >= 1 else 0.5
    return my_dic
    
                


def get_point(story, campaign) :
    
    my_dic = {
        'story' : story,
        'point' : 0
    }
    distances = []
    for quart in campaign.get_quarts() :
        mquart = story.user.get_quart()
        if quart['typ'] == 'country' :
            country = gmaps.reverse_geocode((mquart['lat'], mquart['lng']), result_type = 'country')[0]['formatted_address']
            if country == quart['formatted_address'] :
                distances.append(10)
        else :
            dist = haversine.haversine(point1=(quart['lat'], quart['lng']), point2=(mquart['lat'], mquart['lng']), unit=haversine.Unit.KILOMETERS)
            distances.append((dist))
    if len(distances) :
        my_dic['point'] += (20 - (min(distances)))
    else : my_dic['point'] += 1
    ages_intersec = set(range(story.min_age, story.max_age + 1)).intersection(range(campaign.min_age, campaign.max_age + 1))
    my_dic['point'] += len(ages_intersec)
    sexes = ['h', 'f'] if campaign.sex == 'all' else (['h'] if campaign.sex == 'homme' else ['f'])
    if 'h' in sexes : my_dic['point'] *= (10 * story.men_per)
    if 'f' in sexes : my_dic['point'] *= (10 * story.wmen_per)
    my_dic['point'] += len(story.d_interest.all() & campaign.interests.all()) +1 + len(story.professions.all() & campaign.professions.all())
    return my_dic

def set_audiences(campaign) :
    stories = []
    for story in UserStories.objects.all() :
        stories.append(get_new_point(story, campaign))
    stories = [st for st in stories if st['point']]
    for st in stories :
        Audiences.objects.create(campaign = campaign, story = st['story'], point = st['point'])
    taille = 0
    for aud in campaign.audiences.all(): taille += aud.story.taille
    return taille



