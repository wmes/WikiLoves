 #!/usr/bin/python
# -*- coding: latin-1 -*-

# generic_wikidata_updater.py   Takes WLF lists from the Spanish Wikipedia and creates all necessary stuff in Wikidata
# author:                       Discasto (WM-ES)
# date:                         2016-04-04
#
# Distributed under the terms of the MIT license.
########################################################################################################################
#
import mwparserfromhell as mwh
import pywikibot as pb
import pandas as pd
import urllib2
import urllib
import json
import sys
import getopt

COUNTRY_PROPERTY        = u'P17'
IMAGE_PROPERTY          = u'P18'
INSTANCE_OF_PROPERTY    = u'P31'
IMPORTED_FROM_PROPERTY  = u'P143'
LOCATION_PROPERTY       = u'P276'
COMMONS_CAT_PROPERTY    = u'P373'

COUNTRY_VALUE           = 'Q29'      # Spain
FESTIVAL_VALUE          = 'Q132241'
EVENT_VALUE             = 'Q1656682'
SPANISH_WIKIPEDIA_VALUE = 'Q8449'

INT_TOURIST_FESTIVAL_VALUE          = 'Q3323691'
NAT_TOURIST_FESTIVAL_VALUE          = 'Q64161'
ANDALUSIA_TOURIST_FESTIVAL_VALUE    = 'Q23681146'
ARAGON_TOURIST_FESTIVAL_VALUE       = 'Q23657059'
ASTURIAS_TOURIST_FESTIVAL_VALUE     = 'Q23657241'
CANTABRIA_TOURIST_FESTIVAL_VALUE    = 'Q23657135'
CM_TOURIST_FESTIVAL_VALUE           = 'Q23681152'
MADRID_TOURIST_FESTIVAL_VALUE       = 'Q23726521'
EXTR_TOURIST_FESTIVAL_VALUE         = 'Q23661987'
RIOJA_TOURIST_FESTIVAL_VALUE        = 'Q23727520'
GALICIA_TOURIST_FESTIVAL_VALUE      = 'Q23660968'
NAVARRE_TOURIST_FESTIVAL_VALUE      = 'Q23727539'
MURCIA_TOURIST_FESTIVAL_VALUE       = 'Q23660852'

festival_sources = [
            [u'Anexo:Fiestas de Interés Turístico Internacional (España)', INT_TOURIST_FESTIVAL_VALUE],
            [u'Anexo:Fiestas de Interés Turístico Nacional (España)', NAT_TOURIST_FESTIVAL_VALUE],
            [u'Anexo:Fiestas de interés turístico de Andalucía', ANDALUSIA_TOURIST_FESTIVAL_VALUE],
            [u'Anexo:Fiestas de interés turístico de Aragón', ARAGON_TOURIST_FESTIVAL_VALUE],
            [u'Anexo:Fiestas de interés turístico de Asturias', ASTURIAS_TOURIST_FESTIVAL_VALUE],
            [u'Anexo:Fiestas de interés turístico de Cantabria', CANTABRIA_TOURIST_FESTIVAL_VALUE],
            [u'Anexo:Fiestas de interés turístico de Castilla-La Mancha', CM_TOURIST_FESTIVAL_VALUE],
            [u'Anexo:Fiestas de interés turístico de Castilla y León', FESTIVAL_VALUE],
            [u'Anexo:Fiestas de interés turístico de Cataluña', FESTIVAL_VALUE],
            [u'Anexo:Fiestas de interés turístico de la Comunidad de Madrid', MADRID_TOURIST_FESTIVAL_VALUE],
            [u'Anexo:Fiestas de interés turístico de la Comunidad Valenciana', FESTIVAL_VALUE],
            [u'Anexo:Fiestas de interés turístico de Extremadura', EXTR_TOURIST_FESTIVAL_VALUE],
            [u'Anexo:Fiestas de interés turístico de las Islas Baleares', FESTIVAL_VALUE],
            [u'Anexo:Fiestas de interés turístico de las Islas Canarias', FESTIVAL_VALUE],
            [u'Anexo:Fiestas de interés turístico de Galicia', GALICIA_TOURIST_FESTIVAL_VALUE],
            [u'Anexo:Fiestas de interés turístico de La Rioja', RIOJA_TOURIST_FESTIVAL_VALUE],
            [u'Anexo:Fiestas de interés turístico de Navarra', NAVARRE_TOURIST_FESTIVAL_VALUE],
            [u'Anexo:Fiestas de interés turístico de la Región de Murcia', MURCIA_TOURIST_FESTIVAL_VALUE],
            [u'Anexo:Fiestas y tradiciones del País Vasco', FESTIVAL_VALUE]
            ]

annexes = [u'Anexo:Fiestas de Interés Turístico Internacional (España)',
            u'Anexo:Fiestas de Interés Turístico Nacional (España)',
            u'Anexo:Fiestas de interés turístico de Andalucía',
            u'Anexo:Fiestas de interés turístico de Aragón',
            u'Anexo:Fiestas de interés turístico de Asturias',
            u'Anexo:Fiestas de interés turístico de Cantabria',
            u'Anexo:Fiestas de interés turístico de Castilla-La Mancha',
            u'Anexo:Fiestas de interés turístico de Castilla y León',
            u'Anexo:Fiestas de interés turístico de Cataluña',
            u'Anexo:Fiestas de interés turístico de la Comunidad de Madrid',
            u'Anexo:Fiestas de interés turístico de la Comunidad Valenciana',
            u'Anexo:Fiestas de interés turístico de Extremadura',
            u'Anexo:Fiestas de interés turístico de las Islas Baleares',
            u'Anexo:Fiestas de interés turístico de las Islas Canarias',
            u'Anexo:Fiestas de interés turístico de Galicia',
            u'Anexo:Fiestas de interés turístico de La Rioja',
            u'Anexo:Fiestas de interés turístico de Navarra',
            u'Anexo:Fiestas de interés turístico de la Región de Murcia',
            u'Anexo:Fiestas y tradiciones del País Vasco'
            ]

festival_categories = [INT_TOURIST_FESTIVAL_VALUE,
                       NAT_TOURIST_FESTIVAL_VALUE,
                       ANDALUSIA_TOURIST_FESTIVAL_VALUE,
                       ARAGON_TOURIST_FESTIVAL_VALUE,
                       ASTURIAS_TOURIST_FESTIVAL_VALUE,
                       CANTABRIA_TOURIST_FESTIVAL_VALUE,
                       CM_TOURIST_FESTIVAL_VALUE,
                       FESTIVAL_VALUE,
                       FESTIVAL_VALUE,
                       MADRID_TOURIST_FESTIVAL_VALUE,
                       FESTIVAL_VALUE,
                       EXTR_TOURIST_FESTIVAL_VALUE,
                       FESTIVAL_VALUE,
                       FESTIVAL_VALUE,
                       GALICIA_TOURIST_FESTIVAL_VALUE,
                       RIOJA_TOURIST_FESTIVAL_VALUE,
                       NAVARRE_TOURIST_FESTIVAL_VALUE,
                       MURCIA_TOURIST_FESTIVAL_VALUE,
                       FESTIVAL_VALUE
                       ]
'''annexes = [
            u'Anexo:Fiestas de Interés Turístico Internacional (España)',
            u'Anexo:Fiestas de Interés Turístico Nacional (España)',
            u'Anexo:Fiestas de interés turístico de Cataluña'
            ]'''

festival_categories = [
                        INT_TOURIST_FESTIVAL_VALUE,
                        NAT_TOURIST_FESTIVAL_VALUE,
                        FESTIVAL_VALUE
                       ]
def setClaim (item, claim_id, claim_target, source_id, source_target, prompt=False) :
    claim = pb.Claim(repo, claim_id)
    target = pb.ItemPage(repo, claim_target)
    claim.setTarget(target)
    pb.output('Adding %s --> %s' % (claim.getID(), claim.getTarget()))
    try :
        item.addClaim(claim)
    except Exception as e:
        raise e

    if source_id is not None and source_target is not None :
        source_claim = pb.Claim(repo, source)
        source_claim.setTarget(pb.ItemPage(repo, source_target))
        try :
            claim.addSource(source_claim)
        except Exception as e:
            raise e
    if prompt :
        prompt = '>'
        raw_input(prompt)

    return True

def main(argv) :
    publish_to_wikidata = False
    location_retrieval = False
    try:
        opts, args = getopt.getopt(argv, "hpl", ["help", "publish", "location"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-p", "--publish"):
            publish_to_wikidata = True
        elif opt in ("-l", "--location"):
            location_retrieval = True

    festivals = list()
    festivals_df = pd.DataFrame(columns=['nombre',
                                     'nombre_enlace',
                                     'wikidata',
                                     'cat_commons',
                                     'lugar',
                                     'lugar_nombre',
                                     'location',
                                     'annex',
                                     'order']
                            )
    errors = list()

    pb.output('Processing --> WLF 2016-1 Wikidata')
    if location_retrieval :
        pb.output('Retrieving --> WLF 2016-1 Festival locations')
    media_site = pb.Site("commons", "commons")
    wikipedia_site = pb.Site("es", "wikipedia")
    wikidata_site = pb.Site("wikidata", "wikidata")
    wikidata_site.login()
    repo = wikidata_site.data_repository()

    wikidata_ids = list()   # to enhance with pandas
    for i, annex in enumerate(festival_sources) :
        pb.output('Processing --> WLF 2016-1 annex ' + str(i) + ': ' + annex[0])
        page = pb.Page(wikipedia_site, annex[0])
        text = page.text
        wikicode = mwh.parse(text)
        templates = wikicode.filter_templates()

        counter = 0
        for template in templates :
            counter += 1
            #print counter
            if template.name.lower().strip() == u"fila wlf" :
                festival = dict()

                if template.get(u"wikidata").value :
                    festival["wikidata"] = template.get(u"wikidata").value.strip()
                else :
                    festival["wikidata"] = u''

                if template.get(u"nombre").value :
                    festival["nombre"] = template.get(u"nombre").value.strip()
                else :
                    festival["nombre"] = u''

                try :
                    festival["nombre_enlace"] = template.get(u"nombre_enlace").value.strip()
                except :
                    errors.append(
                                {"id": festival["wikidata"],
                                 "name": festival["nombre"],
                                 "error": u"nombre_enlace not found"}
                    )
                    festival["nombre_enlace"] = festival["nombre"]

                try :
                    festival["fecha_c"] = template.get(u"fecha_celebración").value.strip()
                except :
                    errors.append(
                        {"id": festival["wikidata"],
                         "name": festival["nombre"],
                         "error": u"fecha_celebración not found"}
                    )
                    festival["fecha_c"] = u''
                # declaration date extraction
                try :
                    festival["fecha_d"] = template.get(u"fecha_declaración").value.strip()
                except :
                    errors.append(
                        {"id": festival["wikidata"],
                         "name": festival["nombre"],
                         "error": u"fecha_declaración not found"}
                    )
                    festival["fecha_d"] = u''
                # default commons category extraction
                try :
                    festival["cat_commons_defecto"] = template.get(u"categoría-Commons-defecto").value.strip()
                except :
                    festival["cat_commons_defecto"] = u''
                # coordinates extraction
                if template.get(u"coord").value :
                    festival["coord"] = template.get(u"coord").value.strip()
                else :
                    festival["coord"] = u''
                # image extraction
                if template.get(u"imagen").value :
                    festival["image"] = template.get(u"imagen").value.strip()
                else :
                    festival["image"] = u''
                # commons category extraction
                if template.get(u"categoría-Commons").value :
                    festival["cat_commons"] = template.get(u"categoría-Commons").value.strip().replace(' ', '_')
                else :
                    festival["cat_commons"] = u''

                if template.get(u"lugar").value :
                    festival["lugar"] = template.get(u"lugar").value.strip()
                    locations_wikitext = mwh.parse(festival["lugar"])
                    locations = locations_wikitext.filter_wikilinks()
                    if location_retrieval :
                        try:
                            festival["lugar_nombre"] = locations[0][2:-2].split('|')[0].split('(')[0].replace('_', ' ').strip()
                            url = "https://es.wikipedia.org/w/api.php"
                            values = {'action': 'query',
                                    'prop': 'pageprops',
                                    'ppprop': 'wikibase_item',
                                    'titles': locations[0][2:-2].split('|')[0],
                                    'formatversion': '2',
                                    'format': 'json',
                                    'redirects': ''}
                            encoded_values = {}
                            for k, v in values.iteritems () :
                                encoded_values[k] = unicode(v).encode('utf-8')
                            data = urllib.urlencode(encoded_values)
                            req = urllib2.Request(url, data)
                            response = urllib2.urlopen(req)
                            json_text = response.read()
                            json_object = json.loads(json_text)
                            festival["location"] = json_object["query"]["pages"][0]["pageprops"]["wikibase_item"]
                        except :
                            festival["location"] = u''
                            errors.append(
                                {"id" : festival["wikidata"],
                                 "name" : festival["nombre"],
                                 "error" : u"error when downloading item location information"}
                            )
                else :
                    festival["lugar"] = u''
                    festival["lugar_nombre"] = u''
                    festival["location"] = u''

                festival["annex"] = festival_sources[i][0]
                festival["order"] = i
                if festival["wikidata"] not in wikidata_ids :
                    festival["repeated"] = False
                    if festival["wikidata"] != u'' :
                        wikidata_ids.append(festival["wikidata"])
                else :
                    festival["repeated"] = True

                intermediate_df = pd.DataFrame(festival, index=[0])
                festivals_df = pd.concat ([festivals_df, intermediate_df])
                festivals.append(festival)
    pb.output('Retrieved --> WLF 2016-1 Festival information')
    #raw_input('>')
    # Creating generic 'imported_from' source
    importedfrom = pb.Claim(repo,IMPORTED_FROM_PROPERTY)
    importedfrom.setTarget(pb.ItemPage(repo,SPANISH_WIKIPEDIA_VALUE))

    counter = 0
    for festival in festivals :
        counter += 1
        #print counter, len(festival["wikidata"])
        #if festival["wikidata"] == u'Q23891297' : continue
        if ("wikidata" not in festival or len(festival["wikidata"]) == 0) and not festival["repeated"] :
            pb.output('Processing --> Item without wikidata identifier')
            '''try :
                print festival["nombre"]
            except :
                print "can't print name"
            raw_input('*****')'''
            # We assume that no Wikidata item is available for this festival and therefore create a new wikidata item
            # wikidata item creation
            data =  { u'labels':
                        {
                            u'es': {u'language': u'es', u'value': festival["nombre"] }
                        }
                    }
            identification = {}
            summary = u'Creating new item with data from WLF in the Spanish Wikipedia'
            pb.output('Processing --> Starting to create item in wikidata')
            wikidata_item_created = True
            try :
                result = repo.editEntity(identification, data, summary=summary)
                festival["wikidata"] = result.get(u'entity').get('id')
                pb.output('Processing --> Created item: %s' % (result.get(u'entity').get('id')))
            except :
                festival["wikidata"] = u''
                wikidata_item_created = False

            if wikidata_item_created :
                item = pb.ItemPage(repo, title=festival["wikidata"])
                item.get()

                # Adding description
                try :
                    pb.output('Processing --> Adding descriptions (%s)' %(festival["wikidata"]))
                    item.editDescriptions({u'es': u'fiesta en '+festival["lugar_nombre"]})
                except Exception as e:
                    print str(e)
                    errors.append(
                        {"id": festival["wikidata"],
                         "name": festival["nombre"],
                         "error":u"description insertion failed"}
                    )

                # Adding country
                try:
                    #setClaim (item, COUNTRY_PROPERTY, COUNTRY_VALUE, IMPORTED_FROM_PROPERTY, SPANISH_WIKIPEDIA_VALUE, False)
                    claim = pb.Claim(repo, COUNTRY_PROPERTY)
                    target = pb.ItemPage(repo, COUNTRY_VALUE)
                    claim.setTarget(target)
                    pb.output('Processing --> Adding claim %s to target %s' % (claim.getID(), claim.getTarget()))
                    item.addClaim(claim)
                    claim.addSource(importedfrom)
                except :
                    errors.append(
                        {"id":festival["wikidata"],
                         "name": festival["nombre"],
                         "error": u"country insertion failed"}
                    )

                # Adding location (if available)
                if "location" in festival and len(festival["location"]) > 0 :
                    try :
                        claim = pb.Claim(repo, LOCATION_PROPERTY)
                        target = pb.ItemPage(repo, festival["location"])
                        claim.setTarget(target)
                        pb.output('Processing --> Adding claim %s to target %s' % (claim.getID(), claim.getTarget()))
                        item.addClaim(claim)
                        claim.addSource(importedfrom)
                    except :
                        errors.append(
                            {"id":festival["wikidata"],
                             "name": festival["nombre"],
                             "error":u"location insertion failed"}
                        )

                # Adding instance of
                try :
                    claim = pb.Claim(repo, INSTANCE_OF_PROPERTY)
                    target = pb.ItemPage(repo, festival_sources[festival["order"]][1])
                    claim.setTarget(target)
                    pb.output('Processing --> Adding claim %s to target %s' % (claim.getID(), claim.getTarget()))
                    item.addClaim(claim)
                    claim.addSource(importedfrom)
                except :
                    errors.append(
                        {"id": festival["wikidata"],
                         "name": festival["nombre"],
                         "error": u"instance_of insertion failed"}
                    )

                # Adding image (if available)
                if "image" in festival and len(festival["image"]) > 0 :
                    image_claim = pb.Claim(repo, IMAGE_PROPERTY)
                    imagelink = pb.Link(festival["image"], source=media_site, defaultNamespace=6)
                    image = pb.FilePage(imagelink)
                    if not image.exists() or image.isRedirectPage() :
                        errors.append(
                            {"id": festival["wikidata"],
                             "name": festival["nombre"],
                             "error":u"image not valid"}
                        )
                        continue

                    try :
                        image_claim.setTarget(image)
                        pb.output('Processing --> Adding claim %s to target %s' % (claim.getID(), claim.getTarget()))
                        item.addClaim(image_claim)
                        image_claim.addSource(importedfrom)
                    except :
                        errors.append(
                            {"id": festival["wikidata"],
                             "name": festival["nombre"],
                             "error": u"image insertion failed"}
                        )

        elif not festival["repeated"] :
            # The item exists and will be enhanced, if necessary
            pb.output('Processing --> Item with wikidata identifier (%s)' % (festival["wikidata"]))
            item = pb.ItemPage(repo, title=festival["wikidata"])
            try :
                item.get()
            except :
                errors.append(
                    {"id": festival["wikidata"],
                     "name": festival["nombre"],
                     "error":u"item information not retrievable"}
                )
                continue

            # Handling country
            if COUNTRY_PROPERTY not in item.claims:
                country_claim = pb.Claim(repo, COUNTRY_PROPERTY)
                target = pb.ItemPage(repo, COUNTRY_VALUE)
                try :
                    country_claim.setTarget(target)
                    pb.output('Processing --> Adding claim %s to target %s' % (claim.getID(), claim.getTarget()))
                    item.addClaim(country_claim)
                    country_claim.addSource(importedfrom)
                except :
                    errors.append(
                        {"id": festival["wikidata"],
                         "name": festival["nombre"],
                         "error":u"country insertion failed"}
                    )
            elif len(item.claims[COUNTRY_PROPERTY]) == 1 :
                if not item.claims[COUNTRY_PROPERTY][0].target_equals(COUNTRY_VALUE) :
                    item.removeClaims(item.claims[COUNTRY_PROPERTY][0])
                    country_claim = pb.Claim(repo, COUNTRY_PROPERTY)
                    target = pb.ItemPage(repo, COUNTRY_VALUE)
                    try :
                        country_claim.setTarget(target)
                        pb.output('Processing --> Adding claim %s to target %s' % (claim.getID(), claim.getTarget()))
                        item.addClaim(country_claim)
                        country_claim.addSource(importedfrom)
                    except :
                        errors.append(
                            {"id":festival["wikidata"],
                             "name": festival["nombre"],
                             "error":u"country insertion failed"}
                        )
                elif len(item.claims[COUNTRY_PROPERTY][0].sources) == 0 :
                    pb.output('Processing --> Adding source to claim %s with target %s' % (
                                                                item.claims[COUNTRY_PROPERTY][0].getID(),
                                                                item.claims[COUNTRY_PROPERTY][0].getTarget()
                                                                )
                              )
                    item.claims[COUNTRY_PROPERTY][0].addSource(importedfrom)
            elif len(item.claims[COUNTRY_PROPERTY]) > 1 :
                right_country_found = False
                for i, claim in enumerate(item.claims[COUNTRY_PROPERTY]) :
                    if i == 0 :
                        if not claim.target_equals(COUNTRY_VALUE) :
                            item.removeClaims(claim)
                            country_claim = pb.Claim(repo, COUNTRY_PROPERTY)
                            target = pb.ItemPage(repo, COUNTRY_VALUE)
                            try :
                                country_claim.setTarget(target)
                                pb.output('Processing --> Adding claim %s to target %s' % (claim.getID(), claim.getTarget()))
                                item.addClaim(country_claim)
                                country_claim.addSource(importedfrom)
                            except :
                                errors.append(
                                    {"id": festival["wikidata"],
                                     "name": festival["nombre"],
                                     "error":u"country insertion failed"}
                                )
                        else :
                            pb.output('Processing --> Adding source to claim %s with target %s' % (
                                                                item.claims[COUNTRY_PROPERTY][0].getID(),
                                                                item.claims[COUNTRY_PROPERTY][0].getTarget()
                                                                )
                                     )
                            item.claims[COUNTRY_PROPERTY][0].addSource(importedfrom)
                    else :
                        item.removeClaims(claim)

            # Handling image
            if IMAGE_PROPERTY not in item.claims and "image" in festival and len(festival["image"]) > 0:
                image_claim = pb.Claim(repo, IMAGE_PROPERTY)
                imagelink = pb.Link(festival["image"], source=media_site, defaultNamespace=6)
                image = pb.FilePage(imagelink)
                if not image.exists() or image.isRedirectPage() :
                    errors.append(
                        {"id": festival["wikidata"],
                         "name": festival["nombre"],
                         "error": u"image not valid"}
                    )
                    continue

                try :
                    image_claim.setTarget(image)
                    pb.output('Adding %s --> %s' % (image_claim.getID(), image_claim.getTarget()))
                    item.addClaim(image_claim)
                    image_claim.addSource(importedfrom)
                except :
                    errors.append(
                        {"id": festival["wikidata"],
                         "name": festival["nombre"],
                         "error": u"image insertion failed"}
                    )
            elif IMAGE_PROPERTY in item.claims and "image" in festival and len(festival["image"]) > 0 :
                for i, claim in enumerate(item.claims[IMAGE_PROPERTY]) :
                    image = pb.FilePage(pb.Link(festival["image"], source=media_site, defaultNamespace=6))
                    if claim.target_equals(image) and len(claim.sources) == 0:
                        pb.output('Adding source to %s --> %s' % (claim.getID(), claim.getTarget()))
                        claim.addSource(importedfrom)

            # Handling type of festival
            if INSTANCE_OF_PROPERTY not in item.claims:
                instance_of_claim = pb.Claim(repo, INSTANCE_OF_PROPERTY)
                target = pb.ItemPage(repo, festival_sources[festival["order"]][1])
                try :
                    instance_of_claim.setTarget(target)
                    pb.output('Adding %s --> %s' % (instance_of_claim.getID(), instance_of_claim.getTarget()))
                    item.addClaim(instance_of_claim)
                    instance_of_claim.addSource(importedfrom)
                except:
                    errors.append(
                        {"id": festival["wikidata"],
                         "name": festival["nombre"],
                         "error": u"type of festival insertion failed"}
                    )
            else :
                right_instance_of_already_present = False
                for i, claim in enumerate(item.claims[INSTANCE_OF_PROPERTY]) :
                    festival_value = festival_sources[festival["order"]][1]
                    #print festival_value, claim.getTarget()
                    #raw_input('>')
                    if claim.target_equals(FESTIVAL_VALUE) and festival_sources[festival["order"]][1] != FESTIVAL_VALUE:
                        item.removeClaims(claim)
                    elif claim.target_equals(festival_sources[festival["order"]][1]) and len(claim.sources) == 0 :
                        pb.output('Adding %s --> %s' % (claim.getID(), claim.getTarget()))
                        claim.addSource(importedfrom)
                        right_instance_of_already_present = True
                    elif claim.target_equals(festival_sources[festival["order"]][1]) and right_instance_of_already_present == True :
                        item.removeClaims(claim)
                    elif claim.target_equals(EVENT_VALUE) :
                        item.removeClaims(claim)
                    elif claim.target_equals(festival_sources[festival["order"]][1]) :
                        right_instance_of_already_present = True
                if right_instance_of_already_present == False :
                    instance_of_claim = pb.Claim(repo, INSTANCE_OF_PROPERTY)
                    target = pb.ItemPage(repo, festival_sources[festival["order"]][1])
                    try :
                        instance_of_claim.setTarget(target)
                        pb.output('Adding %s --> %s' % (instance_of_claim.getID(), instance_of_claim.getTarget()))
                        item.addClaim(instance_of_claim)
                        instance_of_claim.addSource(importedfrom)
                    except:
                        errors.append(
                            {"id": festival["wikidata"],
                             "name": festival["nombre"],
                             "error": u"type of festival insertion failed"}
                        )

            # Handling location
            if location_retrieval :
                if LOCATION_PROPERTY not in item.claims and "location" in festival and len(festival["location"]) > 0 :
                    location_claim = pb.Claim(repo, LOCATION_PROPERTY)
                    target = pb.ItemPage(repo, festival["location"])
                    try :
                        location_claim.setTarget(target)
                        pb.output('Adding %s --> %s' % (location_claim.getID(), location_claim.getTarget()))
                        item.addClaim(location_claim)
                        location_claim.addSource(importedfrom)
                    except :
                        errors.append(
                            {"id": festival["wikidata"],
                             "name": festival["nombre"],
                             "error": u"location insertion failed"}
                        )
                elif LOCATION_PROPERTY in item.claims :
                    duplicated_location_claim = False
                    for claim in item.claims[LOCATION_PROPERTY] :
                        if claim.target_equals(festival["location"]) :
                            duplicated_location_claim = True
                            if len(claim.sources) == 0:
                                pb.output('Adding %s --> %s' % (claim.getID(), claim.getTarget()))
                                claim.addSource(importedfrom)
                    if duplicated_location_claim == False :
                        location_claim = pb.Claim(repo, LOCATION_PROPERTY)
                        try :
                            target = pb.ItemPage(repo, festival["location"])
                            location_claim.setTarget(target)
                            pb.output('Adding %s --> %s' % (location_claim.getID(), location_claim.getTarget()))
                            item.addClaim(location_claim)
                            location_claim.addSource(importedfrom)
                        except :
                            errors.append(
                                {"id": festival["wikidata"],
                                 "name": festival["nombre"],
                                 "error": u"location insertion failed"}
                            )

            # Handling commons cat
            if "cat_commons" in festival and len(festival["cat_commons"]) > 0 :
                commons_cat = pb.Page(media_site, title=festival["cat_commons"], ns=14)
                if not commons_cat.exists() or commons_cat.isRedirectPage() or commons_cat.isDisambig() :
                    errors.append(
                        {"id": festival["wikidata"],
                         "name": festival["nombre"],
                         "error": u"commons category not valid"}
                    )

                if commons_cat.exists() and \
                        not commons_cat.isRedirectPage() and \
                        not commons_cat.isDisambig() and \
                        COMMONS_CAT_PROPERTY in item.claims :
                    commons_cat_already_found = False
                    for claim in item.claims[COMMONS_CAT_PROPERTY]:
                        #### There seems to be a bug as claim.getTarget().title() seems to capitalize all the words
                        if u"category:"+claim.getTarget().title().lower().strip() == commons_cat.title().lower().strip() :
                            commons_cat_already_found = True
                            if len(claim.sources) == 0:
                                pb.output('Adding %s --> %s' % (claim.getID(), claim.getTarget()))
                                claim.addSource(importedfrom)
                        else :
                            item.removeClaims(claim)
                    if commons_cat_already_found == False :
                        try :
                            claim = pb.Claim(repo, COMMONS_CAT_PROPERTY)
                            claim.setTarget(festival["cat_commons"].replace('_', ' '))
                            pb.output('Adding %s --> %s' % (claim.getID(), claim.getTarget()))
                            item.addClaim(claim)
                            claim.addSource(importedfrom)
                        except:
                            errors.append(
                                {"id": festival["wikidata"],
                                 "name": festival["nombre"],
                                 "error": u"commons cat insertion failed"}
                            )

                if COMMONS_CAT_PROPERTY not in item.claims :
                    try :
                        pb.output('Processing --> Commons cat claim not available. Claim will inserted in %s' %(festival["wikidata"]))
                        claim = pb.Claim(repo, COMMONS_CAT_PROPERTY)
                        claim.setTarget(festival["cat_commons"].replace('_', ' '))
                        pb.output('Adding %s --> %s' % (claim.getID(), claim.getTarget()))
                        item.addClaim(claim)
                        claim.addSource(importedfrom)
                    except:
                        errors.append(
                            {"id": festival["wikidata"],
                             "name": festival["nombre"],
                             "error": u"commons cat insertion failed"}
                        )
                if u"commonswiki" not in item.sitelinks :
                    try:
                        pb.output('Adding commonswiki --> %s' % (item.getID()))
                        item.setSitelink(
                            sitelink={'site': 'commonswiki', 'title': commons_cat.title()},
                            summary=u'Set commons sitelink'
                        )
                    except:
                        errors.append(
                            {"id": festival["wikidata"],
                             "name": festival["nombre"],
                             "error": u"commonswikilink insertion not possible"}
                        )
                else :
                    if item.getSitelink(u"commonswiki") != commons_cat.title() :
                        errors.append(
                            {"id": festival["wikidata"],
                             "name": festival["nombre"],
                             "error": u"different commonswikilink already present"}
                        )
            else :
                if COMMONS_CAT_PROPERTY in item.claims or u"commonswiki" in item.sitelinks :
                    errors.append(
                        {"id": festival["wikidata"],
                         "name": festival["nombre"],
                         "error" :u"commons cat available in item"}
                    )
    # error publication
    my_error = u"<pre>\n"
    for error in errors:
        raw_text = u"%s;%s;%s;\n" %(error["id"], error["name"], error["error"])
        my_error = my_error + raw_text
    my_error = my_error + u'\n</pre>'
    list_page = pb.Page(wikidata_site, u"User:WikiLovesESBot/Wiki Loves Folk (error)")
    list_page.text = my_error
    list_page.save(u"WLF summary")

    if publish_to_wikidata == True :
        # Creation of wikitext to be subsequently cut-and-pasted in the Spanish Wikipedia
        festival_class = None
        for i, festival in enumerate(festivals) :
            if festival_class != festival["annex"] :
                if festival_class != None :
                    my_text = my_text + u'\n</pre>'
                    # Publication of wikitext in a user page in wikidata
                    list_page = pb.Page(wikidata_site, u"User:WikiLovesESBot/"+festival_class[6:])
                    list_page.text = my_text
                    list_page.save(u"Wikitext saved")
                my_text = u"<pre>\n"
            template_text = u"{{fila WLF\n| nombre_enlace     = %s\n" \
                            u"| nombre            = %s\n| lugar             = %s\n" \
                            u"| fecha_celebración = %s\n| fecha_declaración = %s\n" \
                            u"| categoría-Commons-defecto = %s\n| categoría-Commons = %s\n" \
                            u"| wikidata          = %s\n| coord             = %s\n" \
                            u"| imagen            = %s\n}}\n" % (
                festival["nombre_enlace"], festival["nombre"], festival["lugar"], festival["fecha_c"],
                festival["fecha_d"], festival["cat_commons_defecto"], festival["cat_commons"].replace('_', ' '),
                festival["wikidata"], festival["coord"], festival["image"])
            my_text = my_text + template_text
            festival_class = festival["annex"]

        # Creation of CSV-like log
        wlf_text = u'<pre>\n'
        wlf_text = wlf_text + u'nombre_es;nombre enlace_es;identificador wikidata;categoría commons;imagen;lugar;origen;estatus;\n'
        for festival in festivals :
            if festival["repeated"] == True :
                template_text = u"%s;%s;%s;%s;%s;%s;%s;duplicado;\n" % (
                    festival["nombre"], festival["nombre_enlace"],
                    festival["wikidata"], festival["cat_commons"].replace('_', ' '),
                    festival["image"], festival["lugar"],  festival["annex"][6:]
                )
            else :
                template_text = u"%s;%s;%s;%s;%s;%s;%s;;\n" % (
                    festival["nombre"], festival["nombre_enlace"],
                    festival["wikidata"], festival["cat_commons"].replace('_', ' '),
                    festival["image"], festival["lugar"],  festival["annex"][6:]
                )
            wlf_text = wlf_text + template_text
        wlf_text = wlf_text + u'\n</pre>'
        list_page = pb.Page(wikidata_site, u"User:WikiLovesESBot/Wiki Loves Folk")
        list_page.text = wlf_text
        list_page.save(u"WLF summary")

if __name__ == "__main__":
    main(sys.argv[1:])