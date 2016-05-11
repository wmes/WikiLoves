#!/usr/bin/python
# -*- coding: latin-1 -*-

import pywikibot as pb
from pywikibot import pagegenerators
import mwparserfromhell as mwh
from optparse import OptionParser
from datetime import datetime
import pandas as pd
from urllib import urlencode, urlopen
import json
from random import sample
import copy

aut_com_colors = ['Ivory', 'Beige', 'Wheat', 'Tan', 'DarkKhaki', 'Silver', 'Gray', 'DarkMagenta', 'Navy',
                  'RoyalBlue', 'LightSteelBlue', 'Purple', 'Teal', 'ForestGreen', 'Olive', 'Chartreuse', 'Lime',
                  'GoldenRod', 'PaleGoldenRod', 'LightCoral', 'Salmon', 'DeepPink', 'Fuchsia', 'Lavender',
                  'Plum', 'Indigo', 'Maroon', 'Crimson']

WLF_CATEGORY = u"Category:Images from Wiki Loves Folk 2016 in Spain"

API_BASE_URL = u'https://commons.wikimedia.org/w/api.php'
API_QUERY_STRING = {"action": "query",
                    "format": "json",
                    "gulimit": "10",
                    "prop": "globalusage",
                    "guprop": "url|namespace",
                    "titles": None
                    }

NO_ID_CATEGORY_NAME = u"Images from WLF 2016 in Spain with no ID"
NO_ID_VERIFIED_CATEGORY_NAME = u"%s (verified)" % (NO_ID_CATEGORY_NAME)
NO_ID_CATEGORY_STRING = u"\n[[Category:%s]]" % (NO_ID_CATEGORY_NAME)

BASE_WLF2016_NAME           = u"Commons:Wiki Loves Folk/2016"
STATISTICS_PAGE             = BASE_WLF2016_NAME + u"/Stats"
LOG_PAGE                    = BASE_WLF2016_NAME + u"/Log"
FESTIVAL_DB_PAGE            = BASE_WLF2016_NAME + u"/Festival DB"
GALLERY_PAGE_AUTHORS        = BASE_WLF2016_NAME + u"/Contributors"
GALLERY_PAGE_FESTIVALS      = BASE_WLF2016_NAME + u"/Festivals"
GALLERY_FEATURED_ARTICLES   = BASE_WLF2016_NAME + u'/QI'

START_TIME = 1459461600000  # 2016 April 01, 00:00:00 CEST (miliseconds)
END_TIME = 1462053600000    # 2016 April 30, 23:59:59 CEST (miliseconds)
DAY_LENGTH = 86400000
OLD_TIME = START_TIME -(90*86400000)
NEW_USER_TIME = START_TIME - (86400000*14)

FRACTION_BUG_HEAD = u"* '''Commons category''': [[:Category:Sanfermines|Sanfermines]]\n" \
                    u"* {{gl|[[:gl:Sanfermines|Sanfermines]]}}\n" \
                    u"* {{pt|[[:pt:Festas de São Firmino|Festas de São Firmino]]}}\n" \
                    u"* {{es|[[:es:Sanfermines|Sanfermines]]}}\n" \
                    u"* {{en|[[:en:San Fermín|San Fermín]]}}\n" \
                    u"* {{fr|[[:fr:Fêtes de San Fermín|Fêtes de San Fermín]]}}\n" \
                    u"* {{eu|[[:eu:Iruñeko Sanferminak|Iruñeko Sanferminak]]}}\n" \
                    u"* {{it|[[:it:Festa di san Firmino|Festa di san Firmino]]}}\n" \
                    u"* {{ca|[[:ca:Sanfermines|Sanfermines]]}}\n\n"

FRACTION_BUG_CAT = u'Sanfermines'

annexes = [
            [u'Anexo:Fiestas de interés turístico de Andalucía', None, u'Andalusia'],
            [u'Anexo:Fiestas de interés turístico de Aragón', None, u'Aragon'],
            [u'Anexo:Fiestas de interés turístico de Asturias', None, u'Asturias'],
            [u'Anexo:Fiestas de interés turístico de Cantabria', None, u'Cantabria'],
            [u'Anexo:Fiestas de interés turístico de Castilla-La Mancha', None, u'Castile-La Mancha'],
            [u'Anexo:Fiestas de interés turístico de Castilla y León', None, u'Castile and León'],
            [u'Anexo:Fiestas de interés turístico de Cataluña', None, u'Catalonia'],
            [u'Anexo:Fiestas de interés turístico de la Comunidad de Madrid', None, u'Community of Madrid'],
            [u'Anexo:Fiestas de interés turístico de la Comunidad Valenciana', None, u'Valencian Community'],
            [u'Anexo:Fiestas de interés turístico de Extremadura', None, u'Extremadura'],
            [u'Anexo:Fiestas de interés turístico de las Islas Baleares', None, u'Balearic Islands'],
            [u'Anexo:Fiestas de interés turístico de las Islas Canarias', None, u'Canary Islands'],
            [u'Anexo:Fiestas de interés turístico de Galicia', u'Lista de festas de Interese Turístico de Galicia', u'Galicia'],
            [u'Anexo:Fiestas de interés turístico de La Rioja', None, u'La Rioja'],
            [u'Anexo:Fiestas de interés turístico de Navarra', None, u'Navarre'],
            [u'Anexo:Fiestas de interés turístico de la Región de Murcia', None, u'Region of Murcia'],
            [u'Anexo:Fiestas y tradiciones del País Vasco', None, u'Basque Country']
        ]

def unix_time(zulu_time_string):
    dt = datetime.strptime(zulu_time_string, "%Y-%m-%dT%H:%M:%SZ")
    epoch = datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return int(delta.total_seconds() * 1000)

def return_day (epoch_time) :
    return ((int(epoch_time) - START_TIME) / DAY_LENGTH) + 1

def get_color (grade) :
    if grade < 10.0 :
        percentage_color = 'ff6666'
    elif grade < 30.0 :
        percentage_color = 'ffb366'
    elif grade < 50.0 :
        percentage_color = 'ffff66'
    elif grade < 70.0 :
        percentage_color = 'd9ff66'
    elif grade < 90.0 :
        percentage_color = '66ff66'
    else :
        percentage_color = '668cff '
    return percentage_color


def create_pie_chart (input_dict, input_colors, suffix) :
    output_text = u'{{#invoke:Chart|pie chart\n' \
                  u'| radius = 150\n' \
                  u'| slices = \n'
    for key, value in input_dict.iteritems() :
        output_text += u'    ( %d: %s : %s)\n' %(value, key, input_colors[key])

    output_text += u'| units suffix = _%s\n' \
                   u'| percent = true\n' \
                   u'}}\n' %(suffix)
    return output_text

def main():
    parser = OptionParser()
    parser.add_option('-c', '--cached', action="store_true", default=False, dest='cached', help="works on cached list in commons")
    parser.add_option('-u', '--updatefest', action="store_true", default=False, dest='update_festival', help="updates the festival list (otherwise uses cached copy)")
    (options, args) = parser.parse_args()

    wikipedia_site = pb.Site("es", "wikipedia")

    wikidata_site = pb.Site("wikidata", "wikidata")
    repo = wikidata_site.data_repository()

    commons_site = pb.Site("commons", "commons")
    list_page = pb.Page(commons_site, LOG_PAGE)
    festival_counter = dict()
    festival_counter["not_found"] = 0

    if options.update_festival == True :
        # We create the festival dataframe
        pb.output('Retrieving -->  WLF 2016-1 Festivals from annexes to build new list')
        festivals_df = pd.DataFrame(columns=['name', 'aut_com', 'wikidata_id', 'wikidata_timestamp', 'category', 'cat_timestamp', 'image'])
        counter = 0
        for annex in annexes :
            page = pb.Page(wikipedia_site, annex[0])
            text = page.text
            wikicode = mwh.parse(text)
            templates = wikicode.filter_templates()

            for template in templates :
                if template.name.lower().strip() == u"fila wlf" :
                    counter += 1
                    df_row = dict()
                    df_row["name"] = u''
                    df_row["aut_com"] = annex[2]
                    df_row["wikidata_id"] = u''
                    df_row["wikidata_timestamp"] = None
                    df_row["category"] = None
                    df_row["cat_timestamp"] = None
                    df_row["image"] = None

                    if template.get(u"nombre_enlace").value and len(template.get(u"nombre_enlace").value) > 2:
                        df_row["name"] = template.get(u"nombre_enlace").value.strip()
                    if template.get(u"wikidata").value and len(template.get(u"wikidata").value) > 2:
                        df_row["wikidata_id"] = template.get(u"wikidata").value.strip()
                        item_page = pb.Page(wikidata_site, title=template.get(u"wikidata").value)
                        creation = item_page.oldest_revision
                        df_row["wikidata_timestamp"] = str(unix_time(str(creation.timestamp)))
                    if template.get(u"imagen").value and len(template.get(u"imagen").value) > 2:
                        df_row["image"] = template.get(u"imagen").value.strip()
                    if template.get(u"categoría-Commons").value and len(template.get(u"categoría-Commons").value) > 3:
                        df_row["category"] = template.get(u"categoría-Commons").value.strip()
                        cat_page = pb.Page(commons_site, title=template.get(u"categoría-Commons").value, ns=14)
                        creation = cat_page.oldest_revision
                        df_row["cat_timestamp"] = str(unix_time(str(creation.timestamp)))

                    festivals_df = festivals_df.append(df_row, ignore_index=True)

        pb.output('Retrieved -->  WLF 2016-1 Festivals from annexes to build new list')
        pb.output('Publishing --> WLF 2016-1 list of festivals')
        register_text = u'<pre>\n'
        for index, data in festivals_df.iterrows() :
            for key, value in data.iteritems() :
                if value == None :
                    data[key] = u''
            row_text = u'%s;%s;%s;%s;%s;%s;%s;\n' %(data["name"],
                                                  data["aut_com"],
                                                  data["wikidata_id"],
                                                  data["wikidata_timestamp"],
                                                  data["category"],
                                                  data["cat_timestamp"],
                                                  data["image"])
            register_text += row_text
            #print int(data["wikidata_timestamp"])
        register_text += u'</pre>\n'

        fest_db_page = pb.Page(commons_site, FESTIVAL_DB_PAGE)
        fest_db_page.text = register_text
        fest_db_page.save("WLF Spain 2016-1: Update")
    else :
        pb.output('Retrieving --> WLF 2016-1 Festivals list from cache')
        image_repository = list()
        festival_list_page = pb.Page(commons_site, FESTIVAL_DB_PAGE)
        csv_text = festival_list_page.text
        for line in csv_text.splitlines(True) :
            tokens = line[:-1].split(';')
            if len(tokens) > 1 :
                tokens.pop()
                tokens[3] = float(tokens[3])
                if tokens[5] : tokens[5] = float(tokens[5])
                image_repository.append(tokens)
        pb.output('Retrieved --> WLF 2016-1 Festivals list from cache')
        festivals_df = pd.DataFrame(image_repository, columns=['name', 'aut_com', 'wikidata_id', 'wikidata_timestamp', 'category', 'cat_timestamp', 'image'])

    QI_list = list()

    api_call_counter = 0
    image_usage_counter = 0
    image_perwiki_counter = dict()
    article_perwiki_counter = dict()
    raw_api_query_string = u''
    query_string_items = list()
    if options.cached == False :
        # Retrieving images from the WLF category
        pb.output('Retrieving --> WLF 2016-1 images from category')
        cat = pb.Category(commons_site, WLF_CATEGORY)
        gen = pagegenerators.CategorizedPageGenerator(cat)
        image_repository = list()
        #row_text = u'%s;%s;%s;%s;\n' % (title, WLF_identifier, uploader, creation.timestamp)

        list_text = u'<pre>\n'
        image_counter = 0
        for page in gen:
            if page.isImage():
                if (image_counter != 0) and (image_counter % 50 == 0) :
                    pb.output ('Retrieving --> '+str(image_counter)+" image descriptions downloaded")
                image_counter += 1
                image_item = [None] * 4
                title = page.title(withNamespace=False)
                creation = page.oldest_revision
                image_item[0] = title
                image_item[3] = str(creation.timestamp)
                image_item[2] = creation["user"]

                api_call_counter += 1
                title = 'File:' + page.title(withNamespace=False)
                query_string_items.append(title)
                if api_call_counter % 5 == 0:
                    raw_api_query_string = unicode(u'|'.join(query_string_items)).encode('utf-8')
                    API_QUERY_STRING["titles"] = raw_api_query_string
                    f = urlopen(API_BASE_URL, urlencode(API_QUERY_STRING))
                    response = f.read()
                    # print response
                    response_dict = json.loads(response)
                    for key, value in response_dict["query"]["pages"].iteritems():
                        if len(value[u'globalusage']) > 0:
                            found_dict = dict()
                            image_usage_counter += 1
                            for item in value[u'globalusage']:
                                if (item[u'ns'] == u'0') or (item[u'ns'] == u'104'):
                                    if item[u'wiki'] in article_perwiki_counter:
                                        article_perwiki_counter[item[u'wiki']] += 1
                                    else:
                                        article_perwiki_counter[item[u'wiki']] = 1
                                    found_dict[item[u'wiki']] = True
                                    # print item
                            # print found_dict
                            for key, value in found_dict.iteritems():
                                if key in image_perwiki_counter:
                                    image_perwiki_counter[key] += 1
                                else:
                                    image_perwiki_counter[key] = 1
                    query_string_items = list()

                text = page.text
                wikicode = mwh.parse(text)
                templates = wikicode.filter_templates()
                WLF_template_found = False
                QI_template_found = False
                WLF_identifier = ''
                for template in templates :
                    if template.name.lower().strip() == u"wlf" :
                        WLF_template_found = True
                        WLF_identifier = str(template.get(1).value)
                        if QI_template_found : break
                    elif template.name.lower().strip() == u"qualityimage" :
                        QI_template_found = True
                        QI_list.append(image_item[0])
                        if WLF_template_found: break

                if WLF_template_found == False :
                    catset = page.categories()
                    valid_category_found = False
                    for cat in catset :
                        if cat.titleWithoutNamespace() == NO_ID_CATEGORY_NAME or \
                                      cat.titleWithoutNamespace() == NO_ID_VERIFIED_CATEGORY_NAME :
                            valid_category_found = True
                            break
                    if valid_category_found == False:
                        page.text = text + NO_ID_CATEGORY_STRING
                        page.save("WLF Spain 2016-1: No WLF identifier found")

                image_item[1] = WLF_identifier
                image_repository.append(image_item)
                row_text = u'%s;\n' % (';'.join(image_item))
                list_text += row_text
        pb.output ('Retrieving --> '+str(image_counter)+" images downloaded")
        pb.output('Retrieved --> WLF 2016-1 image list')

        list_text += u'</pre>'
        list_page.text = list_text
        pb.output('Publishing --> WLF 2016-1 image log')
        list_page.save(u"WLF Spain 2016-1 log")

    else :
        # Taking from a previously uploaded list of images
        # Data frame creation
        image_repository = list()
        csv_text = list_page.text
        pb.output('Retrieving --> WLF 2016-1 images list from cache')
        for line in csv_text.splitlines(True) :
            tokens = line[:-1].split(';')
            if len(tokens) > 1 :
                tokens.pop()
                image_repository.append(tokens)

                page = pb.Page(commons_site, tokens[0], ns=6)
                text = page.text
                wikicode = mwh.parse(text)
                templates = wikicode.filter_templates()

                for template in templates:
                    if template.name.lower().strip() == u"qualityimage":
                        QI_list.append(page.title(withNamespace=False))
                        break

                api_call_counter += 1
                title = 'File:' + tokens[0]
                query_string_items.append(title)
                if api_call_counter % 5 == 0:
                    raw_api_query_string = unicode(u'|'.join(query_string_items)).encode('utf-8')
                    API_QUERY_STRING["titles"] = raw_api_query_string
                    f = urlopen(API_BASE_URL, urlencode(API_QUERY_STRING))
                    response = f.read()
                    response_dict = json.loads(response)
                    for key, value in response_dict["query"]["pages"].iteritems():
                        if len(value[u'globalusage']) > 0:
                            found_dict = dict()
                            image_usage_counter += 1
                            for item in value[u'globalusage']:
                                if (item[u'ns'] == u'0') or (item[u'ns'] == u'104'):
                                    if item[u'wiki'] in article_perwiki_counter:
                                        article_perwiki_counter[item[u'wiki']] += 1
                                    else:
                                        article_perwiki_counter[item[u'wiki']] = 1
                                    found_dict[item[u'wiki']] = True
                            for key, value in found_dict.iteritems():
                                if key in image_perwiki_counter:
                                    image_perwiki_counter[key] += 1
                                else:
                                    image_perwiki_counter[key] = 1
                    query_string_items = list()

        pb.output('Retrieved --> WLF 2016-1 image list from cache')

    # Panda management
    images_df = pd.DataFrame(image_repository, columns=['image_title', 'wikidata_id', 'uploader', 'timestamp'])
    images_df["timestamp"] = images_df["timestamp"].apply(unix_time)
    images_df["month_day"] = images_df["timestamp"].apply(return_day)

    festival_contribs_df = pd.DataFrame(columns=['aut_com', 'es_annex', 'wikidata_id', 'category', 'image', 'WLF_image'])
    for annex in annexes :
        #print "Processing annex", annex[0]
        page = pb.Page(wikipedia_site, annex[0])
        text = page.text
        wikicode = mwh.parse(text)
        templates = wikicode.filter_templates()

        for template in templates :
            if template.name.lower().strip() == u"fila wlf" :
                df_row = dict()
                df_row["aut_com"] = annex[2]
                df_row["gl_annex"] = annex[1]
                df_row["es_annex"] = annex[0]
                df_row["wikidata_id"] = u''
                df_row["category"] = None
                df_row["image"] = None
                df_row["WLF_image"] = None

                if template.get(u"wikidata").value and len(template.get(u"wikidata").value) > 3:
                    df_row["wikidata_id"] = template.get(u"wikidata").value
                if template.get(u"imagen").value and len(template.get(u"imagen").value) > 3:
                    df_row["image"] = template.get(u"imagen").value
                    if template.get(u"imagen").value.strip() in list(images_df["image_title"]):
                        df_row["WLF_image"] = True
                if template.get(u"categoría-Commons").value and len(template.get(u"categoría-Commons").value) > 3:
                    df_row["category"] = template.get(u"categoría-Commons").value

                festival_contribs_df = festival_contribs_df.append(df_row, ignore_index=True)
    pb.output('Retrieving --> WLF 2016-1 festival list')

    # 'queries' for further creation of wikitext
    authors             = images_df["uploader"].value_counts()
    authors_with_code   = images_df[images_df["wikidata_id"] != u'']["uploader"].value_counts()
    festivals           = images_df["wikidata_id"].value_counts()
    authors_with_festivals  = images_df.groupby(['uploader'])
    festivals_with_pictures = images_df.groupby(['wikidata_id'])
    month_days          = images_df["month_day"].value_counts()
    autonomous_communities = festivals_df[festivals_df['wikidata_id'].isin(images_df['wikidata_id'].unique())]["aut_com"]
    images_total_df     = pd.merge(images_df, festivals_df, on='wikidata_id')
    images_per_autcom   = images_total_df["aut_com"].value_counts()
    #print (pd.Series([images_df.count()['image_title']-images_total_df["aut_com"].value_counts().sum()], index=['From no festival']))
    images_per_autcom   = images_per_autcom.append(pd.Series([images_df.count()['image_title']-images_total_df["aut_com"].value_counts().sum()], index=['From no festival']))
    #print images_per_autcom
    #raw_input('>')
    #print autonomous_communities.value_counts()
    #raw_input('>')

    day_counter = [0] * 34
    for day, counter in month_days.iteritems() :
        if day > 30 :
            day_counter[33] += counter
        elif day > 0 :
            day_counter[day+1] = counter
        else :
            day_counter[0] += counter

    # Quality images gallery
    qi_gallery_text = u'This page lists the %d [[Commons:Quality Images|quality images]] uploaded as part of ' \
                      u'the first period of the [[Commons:Wiki Loves Folk|Wiki Loves Folk]] contest in ' \
                      u'2016.\n\n' % (len(QI_list))
    qi_gallery_text += u"'''Statistics generation date''': {{subst:CURRENTTIME}} UTC, {{subst:CURRENTMONTHNAME}} {{subst:CURRENTDAY}}, {{subst:CURRENTYEAR}}\n"
    qi_gallery_text += u'<gallery>\n'
    qi_gallery_text += u'\n'.join (QI_list)
    qi_gallery_text += u'\n</gallery>\n\n'
    qi_gallery_text += u'[[Category:Wiki Loves Folk in Spain| Quality]]'
    qi_gallery_page = pb.Page(commons_site, GALLERY_FEATURED_ARTICLES)
    qi_gallery_page.text = qi_gallery_text
    pb.output('Publishing --> WLF 2016-1 quality images gallery')
    qi_gallery_page.save(u"WLF 2016-1 quality images gallery")

    # Statistics page and authors gallery
    author_gallery_text = u''
    statisticts_text =  u'[[File:Wiki Loves Folk Logo.svg|thumb]]\n'
    statisticts_text += u"Welcome to the '''WLF Spain 2016''' statistics. Below you will find information about the " \
                        u"number of uploaded images, the contributors and the WLF festivals the pictures belong to. " \
                        u"Enjoy!!!\n\n"
    statisticts_text += u"==Images==\n"
    statisticts_text += u"* '''Main category''': " \
                        u"[[:Category:Images from Wiki Loves Folk 2016 in Spain|Images from Wiki Loves Folk 2016 in Spain]]\n"
    statisticts_text += u"* '''Total''': %d pictures\n" % (images_df.count()['image_title'])
    statisticts_text += u"** '''Quality Images''': %d pictures ([[%s|see]])\n" % (len(QI_list), GALLERY_FEATURED_ARTICLES)
    statisticts_text += u"* '''Statistics generation date''': {{subst:CURRENTTIME}} UTC, {{subst:CURRENTMONTHNAME}} {{subst:CURRENTDAY}}, {{subst:CURRENTYEAR}}\n"
    statisticts_text += u'==Participants==\n' \
                        u'<br clear="all"/>\n' \
                        u'{| class="wikitable sortable" style="width:50%; font-size:89%; margin-top:0.5em;"\n' \
                        u'|- valign="middle"\n' \
                        u'! Author<br/><small>(registration time)</small>\n' \
                        u'! Uploaded images (total)\n' \
                        u'! Uploaded images<br/>(from a WLF festival)\n' \
                        u'! Contributed to festivals\n'
    new_authors = list()
    for author, count in authors.iteritems():
        author_gallery_text += u'== %s ==\n\n' % (author)
        author_gallery_text += u'<gallery>\n'
        user = pb.User(commons_site, title=author)
        if unix_time(str(user.registration())) > NEW_USER_TIME : new_authors.append(author)
        author_with_festivals = list(authors_with_festivals.get_group(author)["wikidata_id"].unique())
        author_with_pictures = list(authors_with_festivals.get_group(author)["image_title"].unique())
        for index, value in enumerate(author_with_pictures) :
            author_gallery_text += u'%s\n' %(value)
        if u'' in author_with_festivals : author_with_festivals.remove(u'')
        for index, value in enumerate(author_with_festivals) :
            author_with_festivals[index] = u'[[:d:%s|%s]]' % (value, value)
        if author not in authors_with_code :
            authors_with_code[author] = 0
        statisticts_text += u'|-\n' \
                            u'| {{u|%s}} ([[%s#%s|contribs]])<br/><small>(registered on %d-%s-%s)</small>\n' \
                            u'| align="center" | %s\n' \
                            u'| align="center" | %s\n' \
                            u'| align="center" | %s<br/>(\'\'\'%d\'\'\')\n' % (author,
                                                          GALLERY_PAGE_AUTHORS,
                                                          author,
                                                          user.registration().year,
                                                          str(user.registration().month).zfill(2),
                                                          str(user.registration().day).zfill(2),
                                                          str(count),
                                                          authors_with_code[author],
                                                          ',<br/>'.join(author_with_festivals),
                                                          len(author_with_festivals))
        author_gallery_text += u'</gallery>\n\n'
    author_gallery_text += u'[[Category:Wiki Loves Folk in Spain| Contributors]]'
    pb.output('Generating --> WLF 2016-1 contributors gallery')

    statisticts_text += u'|-\n' \
                        u'! Total: %d contributors\n' \
                        u'! align="center" | %d\n' \
                        u'! align="center" | %d\n' \
                        u'! align="center" | %d\n' \
                        u'|}\n' % (authors.size, images_df.count()['image_title'], authors_with_code.sum(), (len(festivals)-1))

    statisticts_text += u"\n'''Number of contributors registered during (or just before) the contest''':" \
                        u" '''%d''' ({{u|%s}})\n\n" % (len(new_authors), '}}, {{'.join(new_authors))
    pb.output('Generating --> WLF 2016-1 contributor statistics')

    statisticts_text += u'=== Per-day contributions chart ===\n' \
                        u'<br clear="all"/>\n'

    chart_text = u'{{ #invoke:Chart | bar chart\n' \
                 u'| height = 450\n' \
                 u'| width = 800\n' \
                 u'| group 1 = %s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s\n' \
                 u'| x legends = <1::1::::5:::::10:::::15:::::20:::::25:::::30::>30\n' \
                 u'| group names = Pictures\n' \
                 u'| colors = orange\n' \
                 u'}}\n' % tuple(day_counter)
    statisticts_text += chart_text
    pb.output('Generating --> WLF 2016-1 per-day contribution statistics')

    statisticts_text += u'==Festivals==\n' \
                        u'<br clear="all"/>\n'

    statisticts_text += u'{| class="wikitable sortable" style="width:45%; font-size:89%; margin-top:0.5em;"\n' \
                        u'|- valign="middle"\n' \
                        u'! WLF Festival<br/>(Commons category)\n' \
                        u'! Autonomous community\n' \
                        u'! Uploaded images\n'

    not_found_counter=0
    for festival, count in festivals.iteritems():
        #print festival, festival_counter[festival]
        if len(festival) == 0 :
            not_found_counter = str(count)
        else :
            item = pb.ItemPage(repo, title=festival)
            commons_cat_link = u''
            try :
                item.get()
                if 'P373' in item.claims:
                    commons_cat = item.claims['P373'][0].getTarget()
                    commons_cat_link = u'<br/>([[:Category:%s|%s]])' % (commons_cat, commons_cat)
            except :
                if festival == "Q829919" :
                    commons_cat = FRACTION_BUG_CAT  # float quantities bug
                    commons_cat_link = u'<br/>([[:Category:%s|%s]])' % (commons_cat, commons_cat)
            try:
                aut_com = festivals_df[festivals_df["wikidata_id"] == festival]["aut_com"].iloc[0]
            except :
                aut_com = u''
            statisticts_text += u'|-\n' \
                                u'| [[:d:%s|%s]]%s\n' \
                                u'| align="center" | %s \n' \
                                u'| align="center" | %d ([[%s#%s|see]])\n' % (festival,
                                                                           festival,
                                                                           commons_cat_link,
                                                                           aut_com,
                                                                           count,
                                                                           GALLERY_PAGE_FESTIVALS,
                                                                           festival)
    statisticts_text += u'|-\n' \
                        u'| Images from no valid festival\n' \
                        u'| align="center" | N/A\n' \
                        u'| align="center" | %s ([[%s#No_valid_festival|see]])\n' %(not_found_counter, GALLERY_PAGE_FESTIVALS)

    statisticts_text += u'|-\n' \
                        u"! '''Total''': %d/%d festivals (%.2f%%)\n" \
                        u'! %d aut. communities\n' \
                        u'! %s\n' \
                        u'|}\n' % ((len(festivals)-1),
                                   festival_contribs_df.count()['aut_com'],
                                   float((len(festivals)-1)*100)/float(festival_contribs_df.count()['aut_com']),
                                   autonomous_communities.unique().size,
                                   images_df.count()['image_title']
                                   )
    pb.output('Generating --> WLF 2016-1 Festival Statistics')

    statisticts_text += u'=== Per-autonomous community contributions chart ===\n' \
                        u'{| border="0" width="90%"\n' \
                        u'|-\n' \
                        u'|\n'
    festivals_per_autcom = autonomous_communities.value_counts().to_dict()
    selected_colors = sample(aut_com_colors, len(festivals_per_autcom)+1)
    reduced_selected_colors = copy.deepcopy(selected_colors)
    reduced_selected_colors.pop()
    expanded_festival_per_autcom_keys = copy.deepcopy(festivals_per_autcom.keys())
    expanded_festival_per_autcom_keys.append('From no festival')

    statisticts_text += create_pie_chart(images_per_autcom, dict(zip(expanded_festival_per_autcom_keys, selected_colors)), 'pictures')
    statisticts_text += u'|\n'
    statisticts_text += create_pie_chart(festivals_per_autcom, dict(zip(festivals_per_autcom.keys(), reduced_selected_colors)), 'festivals')
    statisticts_text += u'|}\n'
    coverage_statisticts_text = u'==Coverage==\n' \
                        u'Coverage statistics measure the number of festival wikidata items and commons categories ' \
                        u'listed in the annexes in the Spanish Wikipedia. Direct access to said annexes is provided ' \
                        u'through the <nowiki>[es]</nowiki> wikilink in the \'Autonomous Community\' column within ' \
                        u'the table (other links to lists in other Wikipedias may be provided for the sake of ' \
                        u'completeness; however, only the ones in the Spanish Wikipedia are used to create ' \
                        u'this set of statistics).\n\n' \
                        u'{| class="wikitable sortable" style="width:55%; font-size:89%; margin-top:0.5em;"\n' \
                        u'|- valign="middle"\n' \
                        u'! Autonomous Community\n' \
                        u'! Festivals (total)\n' \
                        u'! Festivals (in lists)<br/> with category\n' \
                        u'! Festivals (in lists)<br/> with image\n' \
                        u'! Festivals (in lists)<br/> with image (from WLF 2016)\n'

    grouped = festival_contribs_df.groupby(['aut_com'])
    for name, group in grouped:
        percentage_festivals_with_cat = float (group.count()['category']*100.0/float(group.count()['aut_com']))
        percentage_festivals_with_image = float (group.count()['image']*100.0/float(group.count()['aut_com']))
        wikisites_string = u'[[:es:%s|[es]]]' % group["es_annex"].unique()[0]
        if group["gl_annex"].unique()[0] != None and group["gl_annex"].unique()[0] > 3 :
            glsite_string = u' [[:gl:%s|[gl]]]' % group["gl_annex"].unique()[0]
            wikisites_string += glsite_string
        coverage_statisticts_text += u'|-\n' \
                            u'| %s %s\n' \
                            u'| align="center" | %d\n' \
                            u'| align="center" bgcolor="#%s" | %d (%.2f%%)\n' \
                            u'| align="center" bgcolor="#%s" | %d (%.2f%%)\n' \
                            u'| align="center" | %d\n' % (group["aut_com"].unique()[0],
                                                          wikisites_string,
                                                          group.count()['aut_com'],
                                                          get_color(percentage_festivals_with_cat),
                                                          group.count()['category'],
                                                          percentage_festivals_with_cat,
                                                          get_color(percentage_festivals_with_image),
                                                          group.count()['image'],
                                                          percentage_festivals_with_image,
                                                          group.count()['WLF_image'])
    coverage_statisticts_text += u'|-\n' \
                        u'| Total\n' \
                        u'| align="center" | %d\n' \
                        u'| align="center" bgcolor="#%s" | %d (%.2f%%)\n' \
                        u'| align="center" bgcolor="#%s" | %d (%.2f%%)\n' \
                        u'| align="center" | %d\n' \
                        u'|}\n\n' % (festival_contribs_df.count()['aut_com'],
                                        get_color(float (festival_contribs_df.count()['category']*100.0/float(festival_contribs_df.count()['aut_com']))),
                                        festival_contribs_df.count()['category'],
                                        float (festival_contribs_df.count()['category']*100.0/float(festival_contribs_df.count()['aut_com'])),
                                        get_color(float (festival_contribs_df.count()['image']*100.0/float(festival_contribs_df.count()['aut_com']))),
                                        festival_contribs_df.count()['image'],
                                        float (festival_contribs_df.count()['image']*100.0/float(festival_contribs_df.count()['aut_com'])),
                                        festival_contribs_df.count()['WLF_image'])

    pb.output('Generating --> WLF 2016-1 Coverage Statistics')
    statisticts_text += coverage_statisticts_text

    image_usage_text = u'==Image usage==\n\n' \
                       u'{| class="wikitable sortable" style="width:30%; font-size:89%; margin-top:0.5em;"\n' \
                       u'|- valign="middle"\n' \
                       u'! Item\n' \
                       u'! Counter\n'
    for key, value in image_perwiki_counter.iteritems():
        image_usage_text += u'|-\n' \
                            u'| width="80%%" | WLF 2016 images used in %s\n' \
                            u'| align="center" | %d\n' % (key, value)
    image_usage_text += u'|-\n' \
                        u'| width="80%%" | Distinct WLF 2016 images used in any Wikipedia\n' \
                        u'| align="center" | \'\'\'%d\'\'\' (%.2f%%)\n' % (
                                                            image_usage_counter,
                                                            float(image_usage_counter)*100/float(images_df.count()['image_title'])
                                                            )
    for key, value in article_perwiki_counter.iteritems():
        image_usage_text += u'|-\n' \
                            u'| width="80%%" | Articles with WLF 2016 images in %s\n' \
                            u'| align="center" | %d\n' % (key, value)
    image_usage_text += u'|-\n' \
                        u'| width="80%%" | Articles with WLF 2016 images in any Wikipedia\n' \
                        u'| align="center" | \'\'\'%d\'\'\'\n' % (sum(article_perwiki_counter.values()))
    image_usage_text += u'|}\n\n'
    pb.output('Generating --> WLF 2016-1 Image Usage Statistics')
    statisticts_text += image_usage_text

    supporting_task_text = u'==Supporting tasks==\n' \
                    u'As part of the contest organization, creation of wikidata items and commons categories has been carried out. ' \
                    u'Below you can find when they were created.\n' \
                    u'<br clear="all"/>\n' \
                    u'{| class="wikitable sortable" style="width:60%; font-size:89%; margin-top:0.5em;"\n' \
                    u'|- valign="middle"\n' \
                    u'! \n' \
                    u'! Pre-exiting<br/>(created before<br/>2016-01-01)\n' \
                    u'! Created during<br/>contest organization<br/>(between 2016-01-01<br/>and 2016-03-31)\n' \
                    u'! Created during<br/>the contest\n' \
                    u'! Created after<br/>the contest\n' \
                    u'! &nbsp;&nbsp;&nbsp;Total&nbsp;&nbsp;&nbsp;\n'
    supporting_task_text_1 = u'|-\n' \
                        u'| Wikidata items\n' \
                        u'| align="center" | %d\n' \
                        u'| align="center" | %d\n' \
                        u'| align="center" | %d\n' \
                        u'| align="center" | %d\n' \
                        u'| align="center" bgcolor="#%s" | %d (100%%)\n' % (len(festivals_df[festivals_df["wikidata_timestamp"]<OLD_TIME].index),
                                                      len(festivals_df[(festivals_df["wikidata_timestamp"]>OLD_TIME) & (festivals_df["wikidata_timestamp"]<START_TIME)].index),
                                                      len(festivals_df[(festivals_df["wikidata_timestamp"]>START_TIME) & (festivals_df["wikidata_timestamp"]<END_TIME)].index),
                                                      len(festivals_df[(festivals_df["wikidata_timestamp"]>END_TIME)].index),
                                                      get_color(100.0),
                                                      len(festivals_df.index)
                                                      )
    supporting_task_text += supporting_task_text_1
    supporting_task_text_2 = u'|-\n' \
                        u'| Commons categories\n' \
                        u'| align="center" | %d\n' \
                        u'| align="center" | %d\n' \
                        u'| align="center" | %d\n' \
                        u'| align="center" | %d\n' \
                        u'| align="center" bgcolor="#%s" | %d (%.2f%%)\n' \
                        u'|}\n\n' % (len(festivals_df[(festivals_df["cat_timestamp"] != u'') & (festivals_df["cat_timestamp"]<OLD_TIME)].index),
                                     len(festivals_df[(festivals_df["cat_timestamp"] != u'') & (festivals_df["cat_timestamp"]>OLD_TIME) & (festivals_df["cat_timestamp"]<START_TIME)].index),
                                     len(festivals_df[(festivals_df["cat_timestamp"] != u'') & (festivals_df["cat_timestamp"]>START_TIME) & (festivals_df["cat_timestamp"]<END_TIME)].index),
                                     len(festivals_df[(festivals_df["cat_timestamp"] != u'') & (festivals_df["cat_timestamp"]>END_TIME)].index),
                                     get_color(float(len(festivals_df[(festivals_df["cat_timestamp"] != u'')])*100.0)/float(len(festivals_df.index))),
                                     len(festivals_df[(festivals_df["cat_timestamp"] != u'')]),
                                     float(len(festivals_df[(festivals_df["cat_timestamp"] != u'')])*100.0)/float(len(festivals_df.index))
                                    )
    supporting_task_text += supporting_task_text_2
    statisticts_text += supporting_task_text
    pb.output('Generating --> WLF 2016-1 Supporting Tasks Statistics')

    statisticts_text += u'\n[[Category:Wiki Loves Folk in Spain| Stats]]'

    # festivals gallery
    festival_gallery_text = u''
    for index, item in festivals_with_pictures:
        sitelinks_string = u''
        if len(index) > 0 :
            festival_gallery_text += '== %s ==\n' % (index)
            festival_gallery_text += u"* '''Wikidata''': [[d:%s|%s]]\n" % (index, index)
            wikidata_item = pb.ItemPage(repo, title=index)
            try:
                wikidata_item.get()
                if 'P373' in wikidata_item.claims:
                    commons_cat = wikidata_item.claims['P373'][0].getTarget()
                    commons_cat_link = u"* '''Commons category''': [[:Category:%s|%s]]\n" % (commons_cat, commons_cat)
                    festival_gallery_text += commons_cat_link

                for key, value in wikidata_item.sitelinks.iteritems():
                    if key == u'astwiki' :
                        sitelinks_string += u'* {{ast|[[:ast:%s|%s]]}}\n' % (value, value)
                    elif key == u'cawiki' :
                        sitelinks_string += u'* {{ca|[[:ca:%s|%s]]}}\n' % (value, value)
                    elif key == u'enwiki' :
                        sitelinks_string += u'* {{en|[[:en:%s|%s]]}}\n' % (value, value)
                    elif key == u'eswiki' :
                        sitelinks_string += u'* {{es|[[:es:%s|%s]]}}\n' % (value, value)
                    elif key == u'euwiki' :
                        sitelinks_string += u'* {{eu|[[:eu:%s|%s]]}}\n' % (value, value)
                    elif key == u'extwiki' :
                        sitelinks_string += u'* {{ext|[[:ext:%s|%s]]}}\n' % (value, value)
                    elif key == u'frwiki' :
                        sitelinks_string += u'* {{fr|[[:fr:%s|%s]]}}\n' % (value, value)
                    elif key == u'glwiki' :
                        sitelinks_string += u'* {{gl|[[:gl:%s|%s]]}}\n' % (value, value)
                    elif key == u'itwiki' :
                        sitelinks_string += u'* {{it|[[:it:%s|%s]]}}\n' % (value, value)
                    elif key == u'ptwiki' :
                        sitelinks_string += u'* {{pt|[[:pt:%s|%s]]}}\n' % (value, value)
                festival_gallery_text += sitelinks_string
            except :
                if index == "Q829919" :
                    festival_gallery_text += FRACTION_BUG_HEAD

        else :
            festival_gallery_text += '== No valid festival ==\n\n'
        festival_gallery_text += '<gallery>\n'
        for i, value in item["image_title"].iteritems() :
            festival_gallery_text += u'%s\n' % (value)
        festival_gallery_text += '</gallery>\n\n'
    pb.output('Generating --> WLF 2016-1 Festival gallery')
    festival_gallery_text += u'[[Category:Wiki Loves Folk in Spain| Festivals]]'

    stats_page = pb.Page(commons_site, STATISTICS_PAGE)
    stats_page.text = statisticts_text
    pb.output('Publishing --> WLF 2016-1 Statistics')
    stats_page.save(u"WLF Spain 2016-1 statistics")

    authors_page = pb.Page(commons_site, GALLERY_PAGE_AUTHORS)
    authors_page.text = author_gallery_text
    pb.output('Publishing --> WLF 2016-1 Authors gallery')
    authors_page.save(u"WLF Spain 2016-1 gallery (per author)")

    festivals_page = pb.Page(commons_site, GALLERY_PAGE_FESTIVALS)
    festivals_page.text = festival_gallery_text
    pb.output('Publishing --> WLF 2016-1 Festivals gallery')
    festivals_page.save(u"WLF Spain 2016-1 gallery (per festival)")

if __name__ == "__main__":
    main()