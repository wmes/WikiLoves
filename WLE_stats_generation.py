#!/usr/bin/python
# -*- coding: utf-8 -*-

# WLE_stats_generation.py  Creates the statistics for WLE 2016 in Spain. It takes as inputs the category where the images
#                          are ('WLE_CATEGORY') and a CVS-like page with information about sites of community importance
#                          in Spain ('SCI_DB_PAGE'). It has to be created beforehand
# author:                  Discasto (WM-ES)
# date:                    2016-05-11
#
# Distributed under the terms of the MIT license.
########################################################################################################################
#
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
import re
from collections import OrderedDict
from operator import itemgetter

# Information about the SCI sources
annexes = [
            ['ES-AN', u'Andalusia', u'Anexo:Lugares de importancia comunitaria de Andalucía', '', ''],
            ['ES-AR', u'Aragon', u'Anexo:Lugares de importancia comunitaria de Aragón', '', ''],
            ['ES-AS', u'Asturias', u'Anexo:Lugares de importancia comunitaria de Asturias', '', ''],
            ['ES-CB', u'Cantabria', u'Anexo:Lugares de importancia comunitaria de Cantabria', '', ''],
            ['ES-CE', u'Ceuta and Melilla', u'Anexo:Lugares de importancia comunitaria de Ceuta y Melilla', '', ''],
            ['ES-CL', u'Castile and León', u'Anexo:Lugares de importancia comunitaria de Castilla y León', '', ''],
            ['ES-CM', u'Castile-La Mancha', u'Anexo:Lugares de importancia comunitaria de Castilla-La Mancha', '', ''],
            ['ES-CN', u'Canary Islands', u'Anexo:Lugares de importancia comunitaria de las Islas Canarias', '', ''],
            ['ES-CT', u'Catalonia', u'Anexo:Lugares de importancia comunitaria de Cataluña', '', u'Viquiprojecte:Patrimoni natural/Llista de llocs d\'importància comunitària de Catalunya'],
            ['ES-EX', u'Extremadura', u'Anexo:Lugares de importancia comunitaria de Extremadura', '', ''],
            ['ES-GA', u'Galicia', u'Anexo:Lugares de importancia comunitaria de Galicia', u'Lugares de importancia comunitaria en Galicia', ''],
            ['ES-IB', u'Balearic Islands', u'Anexo:Lugares de importancia comunitaria de las Islas Baleares', '', u'Llista de Llocs d\'Importància Comunitària de les Illes Balears'],
            ['ES-MC', u'Region of Murcia', u'Anexo:Lugares de importancia comunitaria de la Región de Murcia', '', ''],
            ['ES-MD', u'Community of Madrid', u'Anexo:Lugares de importancia comunitaria de la Comunidad de Madrid', '', ''],
            ['ES-ML', u'Melilla', u'Anexo:Lugares de importancia comunitaria de Ceuta y Melilla', '', ''],
            ['ES-NC', u'Navarre', u'Anexo:Lugares de importancia comunitaria de Navarra', '', ''],
            ['ES-PV', u'Basque Country', u'Anexo:Lugares de importancia comunitaria del País Vasco', '', ''],
            ['ES-RI', u'La Rioja', u'Anexo:Lugares de importancia comunitaria de La Rioja', '', ''],
            ['ES-VC', u'Valencian Community', u'Anexo:Lugares de importancia comunitaria de la Comunidad Valenciana', '', u'Llista de llocs d\'importància comunitària del País Valencià'],
            ['ES-MAGRAMA', u'Ministry of Agriculture, Food and Enviroment', u'Anexo:Lugares de importancia comunitaria del MAGRAMA', '', '']
        ]
annexes_df = pd.DataFrame(annexes, columns=['aut_com', 'aut_com_name', 'aut_com_es_annex', 'aut_com_gl_annex', 'aut_com_ca_annex'])

# Colors needed to draw pie charts
aut_com_colors = ['Ivory', 'Beige', 'Wheat', 'Tan', 'DarkKhaki', 'Silver', 'Gray', 'DarkMagenta', 'Navy',
                  'RoyalBlue', 'LightSteelBlue', 'Purple', 'Teal', 'ForestGreen', 'Olive', 'Chartreuse', 'Lime',
                  'GoldenRod', 'PaleGoldenRod', 'LightCoral', 'Salmon', 'DeepPink', 'Fuchsia', 'Lavender',
                  'Plum', 'Indigo', 'Maroon', 'Crimson']

# Mediawiki API calls to get image global usage
API_BASE_URL = u'https://commons.wikimedia.org/w/api.php'
API_QUERY_STRING = {"action": "query",
                    "format": "json",
                    "gulimit": "10",
                    "prop": "globalusage",
                    "guprop": "url|namespace",
                    "titles": None
                    }

# Source category
WLE_CATEGORY = u"Category:Images from Wiki Loves Earth 2016 in Spain"

# Outputs
BASE_WLE2016_NAME           = u"Commons:Wiki Loves Earth 2016 in Spain"
STATISTICS_PAGE             = BASE_WLE2016_NAME + u"/Stats"
IMAGE_LOG_PAGE              = BASE_WLE2016_NAME + u"/Log"
GALLERY_PAGE_AUTHORS        = BASE_WLE2016_NAME + u"/Contributors"
GALLERY_PAGE_SCIS           = BASE_WLE2016_NAME + u"/SCIs"
GALLERY_FEATURED_ARTICLES   = BASE_WLE2016_NAME + u'/QI'

# Other inputs
SCI_DB_PAGE                 = BASE_WLE2016_NAME + u"/SCI DB"

# Time variables for finding out who is a new editor
DAY_LENGTH = 86400000
START_TIME = 1462053600000              # 2016 May 01, 00:00:00 CEST (miliseconds)
END_TIME = START_TIME + (31*86400000)   # 2016 May 30, 23:59:59 CEST (miliseconds)
OLD_TIME = START_TIME - (90*86400000)
NEW_USER_TIME = START_TIME - (86400000*14)

def unix_time(zulu_time_string):
    dt = datetime.strptime(zulu_time_string, "%Y-%m-%dT%H:%M:%SZ")
    epoch = datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return int(delta.total_seconds() * 1000)

def return_day (epoch_time) :
    return ((int(epoch_time) - START_TIME) / DAY_LENGTH) + 1

def get_quality_color (grade) :
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

def create_pie_chart (input_dict, input_colors, suffix, special_item_key=None) :
    if special_item_key != None :
        special_item = dict()
        special_item[special_item_key] = 0

    output_text = u'{{#invoke:Chart|pie chart\n' \
                  u'| radius = 180\n' \
                  u'| slices = \n'
    input_dict = dict(input_dict)
    sorted_dict = OrderedDict(sorted(input_dict.items(), key=itemgetter(1), reverse=True))
    for key, value in sorted_dict.iteritems() :
        if special_item_key == None or key != special_item_key :
            output_text += u'    ( %d: %s : %s)\n' %(value, key, input_colors[key])
        else :
            special_item[special_item_key] = value

    if special_item_key != None :
        output_text += u'    ( %d: %s : %s)\n' % (special_item[special_item_key], special_item_key, input_colors[special_item_key])

    output_text += u'| units suffix = _%s\n' \
                   u'| percent = true\n' \
                   u'}}\n' %(suffix)
    return output_text

def split_range (input_range, n) :
    modulus = input_range % n
    quotient = input_range / n
    boundaries = list()
    last_value = 0
    for i in range(1, n+1):
        if modulus > 0:
            boundaries.append(last_value+quotient+1)
            last_value += quotient+1
            modulus-=1
        else :
            boundaries.append(last_value+quotient)
            last_value += quotient
    return boundaries

def main():
    parser = OptionParser()
    parser.add_option('-c', '--cached', action="store_true", default=False, dest='cached', help="works on cached image list in commons")
    (options, args) = parser.parse_args()

    wikipedia_site = pb.Site("es", "wikipedia")
    commons_site = pb.Site("commons", "commons")

    image_list_page = pb.Page(commons_site, IMAGE_LOG_PAGE)
    sci_list_page   = pb.Page(commons_site, SCI_DB_PAGE)
    qi_gallery_page = pb.Page(commons_site, GALLERY_FEATURED_ARTICLES)
    stats_page      = pb.Page(commons_site, STATISTICS_PAGE)
    authors_page    = pb.Page(commons_site, GALLERY_PAGE_AUTHORS)
    scis_page       = pb.Page(commons_site, GALLERY_PAGE_SCIS)

    # SCI dataframe creation
    pb.output('Retrieving --> WLE 2016 SCI list from cache')
    sci_repository = list()
    sci_csv_text = sci_list_page.text

    # useful indices from ['name', 'code', 'magrama_record', 'aut_com', 'bio_region', 'continent', 'alt_max', 'alt_min', 'alt_med',
    #'lon', 'lat', 'area', 'sea_area_percentage', 'sea_area', 'image', 'cat-commons', 'wikidata_id']
    sci_csv_indices = [0, 1, 3, 14, 15, 16]
    for line in sci_csv_text.splitlines(True) :
        tokens = line[:-1].split(';')
        if len(tokens) > 1 :
            valid_tokens = [tokens[i] for i in sci_csv_indices]
            sci_repository.append(valid_tokens)
    pb.output('Retrieved --> WLE 2016 SCI list from cache')
    scis_df = pd.DataFrame(sci_repository, columns=['name', 'code', 'aut_com', 'image', 'category', 'wikidata_id'])
    scis_df = pd.merge(scis_df, annexes_df[['aut_com', 'aut_com_name', 'aut_com_es_annex']], on='aut_com')
    sci_list = list(scis_df["code"])

    api_call_counter = 0
    image_usage_counter = 0
    image_perwiki_counter = dict()
    article_perwiki_counter = dict()
    raw_api_query_string = u''
    query_string_items = list()

    QI_list = list()

    if options.cached == False :
       # Retrieving images from the actual WLE category
        image_repository = list()

        pb.output('Retrieving --> WLE 2016 images from category')
        cat = pb.Category(commons_site, WLE_CATEGORY)
        gen = pagegenerators.CategorizedPageGenerator(cat)

        list_text = u'<pre>\n'
        image_counter = 0
        for page in gen:
            if page.isImage():
                if (image_counter != 0) and (image_counter % 50 == 0) :
                    pb.output ('Retrieving --> '+str(image_counter)+" image descriptions downloaded")
                image_counter += 1
                print '.'

                image_item = [None] * 4
                title = page.title(withNamespace=False)
                creation = page.oldest_revision
                image_item[0] = title
                image_item[2] = creation["user"]
                image_item[3] = str(creation.timestamp)

                text = page.text
                wikicode = mwh.parse(text)
                templates = wikicode.filter_templates()
                WLE_template_found = False
                QI_template_found = False
                WLE_identifier = ''
                for template in templates :
                    if template.name.lower().strip() == u"lic" :
                        WLE_template_found = True
                        match = re.search(r'ES[0-9]{5,6}', template.get(1).value.strip())
                        if match and template.get(1).value.strip() in sci_list:
                            WLE_identifier = template.get(1).value.strip()
                        if QI_template_found : break
                    elif template.name.lower().strip() == u"qualityimage" :
                        QI_template_found = True
                        QI_list.append(image_item[0])
                        if WLE_template_found: break
                image_item[1] = WLE_identifier
                image_repository.append(image_item)
                row_text = u'%s;\n' % (';'.join(image_item))
                list_text += row_text

                title = 'File:' + page.title(withNamespace=False)
                api_call_counter += 1
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

        pb.output ('Retrieving --> '+str(image_counter)+" images downloaded")
        pb.output('Retrieved --> WLE 2016 image list')

        list_text += u'</pre>'
        image_list_page.text = list_text
        image_list_page.save(u"WLE Spain 2016 image log")
        pb.output('Publishing --> WLE 2016 image log')
    else :
        # Taking from a previously uploaded list of images
        image_repository = list()

        csv_text = image_list_page.text
        pb.output('Retrieving --> WLE 2016 images list from cache')

        image_counter = 0
        for line in csv_text.splitlines(True) :
            tokens = line[:-1].split(';')
            if len(tokens) > 1 :
                if (image_counter != 0) and (image_counter % 50 == 0) :
                    pb.output ('Retrieving --> '+str(image_counter)+" image descriptions retrieved from log")
                image_counter += 1
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

                title = 'File:' + tokens[0]
                api_call_counter += 1
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

        pb.output('Retrieved --> WLE 2016 image list from cache')

    # Panda management
    images_df = pd.DataFrame(image_repository, columns=['image_title', 'code', 'uploader', 'timestamp'])
    images_df["timestamp"] = images_df["timestamp"].apply(unix_time)
    images_df["month_day"] = images_df["timestamp"].apply(return_day)

    sci_coverage_df = pd.DataFrame(columns=['aut_com', 'es_annex', 'gl_annex', 'ca_annex', 'code', 'category', 'image'])
    for annex in annexes :
        if annex[0] == u'ES-ML' : continue
        page = pb.Page(wikipedia_site, annex[2])
        text = page.text
        wikicode = mwh.parse(text)
        templates = wikicode.filter_templates()

        for template in templates :
            if template.name.lower().strip() == u"fila lic" :
                df_row = dict()
                df_row["aut_com"] = annex[1]
                df_row["es_annex"] = annex[2]
                df_row["gl_annex"] = annex[3]
                df_row["ca_annex"] = annex[4]
                df_row["code"] = None
                df_row["image"] = None
                df_row["category"] = None

                try :
                    if len(template.get(u"código").value.strip()) > 3 :
                        df_row["code"] = template.get(u"código").value.strip()
                except :
                    pass
                try :
                    if len(template.get(u"imagen").value.strip()) > 3 :
                        df_row["image"] = template.get(u"imagen").value.strip()
                except :
                    pass
                try :
                    if len(template.get(u"categoría-Commons").value.strip()) > 3 :
                        df_row["category"] = template.get(u"categoría-Commons").value.strip()
                except :
                    pass

                sci_coverage_df = sci_coverage_df.append(df_row, ignore_index=True)
    pb.output('Retrieving --> WLE 2016 SCI list')

    # 'queries' for further creation of wikitext
    images_total_df     = pd.merge(images_df, scis_df, on='code', how='left') # This dataframe add SCI information to image information
    authors             = images_total_df["uploader"].value_counts()          # This query shows the number of images per uploader
    authors_with_code   = images_total_df[images_total_df["code"] != u'']["uploader"].value_counts()
                                                                              # This query shows the number of valid images per uploader
    SCIs                = images_total_df["code"].value_counts()              # This query shows the number of images per SCI
    month_days          = images_total_df["month_day"].value_counts()         # This query shows the number of uploaded images in every day
    images_per_autcom   = images_total_df["aut_com_name"].value_counts()      # This query shows the number of uploaded images per autonomous community
    images_per_autcom   = images_per_autcom.append(pd.Series([images_total_df.count()['image_title']-images_total_df["aut_com"].value_counts().sum()], index=['From no valid site']))

    authors_with_SCIs   = images_total_df.groupby(['uploader'])     # This query groups images per uploader
    scis_with_pictures  = images_total_df.groupby(['code'])         # This query groups images per SCI

    aut_com_with_SCI    = scis_df[scis_df['code'].isin(images_total_df['code'].unique())]["aut_com_name"]

    # Month day uploads computation
    day_counter = [0] * 35
    for day, counter in month_days.iteritems() :
        if day > 31 :
            day_counter[34] += counter
        elif day > 0 :
            day_counter[day+1] = counter
        else :
            day_counter[0] += counter

    # Creation and publication of quality images gallery
    qi_gallery_text = u'This page lists the %d [[Commons:Quality Images|quality images]] uploaded as part of ' \
                      u'the first period of the [[Commons:Wiki Loves Earth 2016 in Spain|Wiki Loves Earth]] contest ' \
                      u'in Spain in 2016.\n\n' % (len(QI_list))
    qi_gallery_text += u"'''Statistics generation date''': {{subst:CURRENTTIME}} UTC, {{subst:CURRENTMONTHNAME}} " \
                       u"{{subst:CURRENTDAY}}, {{subst:CURRENTYEAR}}\n"
    qi_gallery_text += u'<gallery>\n'
    qi_gallery_text += u'\n'.join (QI_list)
    qi_gallery_text += u'\n</gallery>\n\n'
    qi_gallery_text += u'[[Category:Wiki Loves Earth 2016 in Spain| Quality]]'
    qi_gallery_page.text = qi_gallery_text
    pb.output('Publishing --> WLE 2016 quality images gallery')
    qi_gallery_page.save(u"WLE 2016 quality images gallery")

    # Creation and publication of sites of community importance gallery
    sci_gallery_text = u''
    for code, item in scis_with_pictures:
        sitelinks_string = u''
        if len(code) > 0 :
            sci_gallery_text += '== %s (%s) ==\n' % (scis_df[scis_df["code"] == code]["name"].iloc[0], code)
            sci_gallery_text += u"\'\'\'Local name\'\'\': %s\n" % (scis_df[scis_df["code"] == code]["name"].iloc[0])
            sci_gallery_text += u"\'\'\'Uploaded images\'\'\': [[:Category:Images of site of community importance " \
                                u"with code %s from Wiki Loves Earth 2016 in Spain|category]]" % (code)
        else :
            sci_gallery_text += '== No valid site of community importance ==\n\n'
        sci_gallery_text += '<gallery>\n'
        for i, value in item["image_title"].iteritems() :
            sci_gallery_text += u'%s\n' % (value)
        sci_gallery_text += '</gallery>\n\n'
    pb.output('Generating --> WLE 2016 SCI gallery')
    sci_gallery_text += u'[[Category:Wiki Loves Earth 2016 in Spain| Site]]'
    scis_page.text = sci_gallery_text
    pb.output('Publishing --> WLE 2016 SCI gallery')
    scis_page.save(u"WLE Spain 2016 gallery (per SCI)")

    # Statistics page and authors gallery
    author_gallery_text = u''
    statisticts_text =  u'{| align=right\n' \
                        u'|[[File:WLE Austria Logo (transparent).svg|200px|link=]]\n' \
                        u'|-\n' \
                        u'| style="text-align:center; font-family:arial black; font-size:200%; color:grey" ' \
                        u'| {{LangSwitch| es=España|ca=Espanya|en=Spain}}&nbsp;&nbsp;&nbsp;\n' \
                        u'|}\n'
    statisticts_text += u"Welcome to the '''WLE Spain 2016''' statistics. Below you will find information about the " \
                        u"number of uploaded images, the contributors and the WLE sites the pictures belong to. " \
                        u"Enjoy!!!\n\n"
    statisticts_text += u"==Images==\n"
    statisticts_text += u"* '''Main category''': " \
                        u"[[:Category:Images from Wiki Loves Earth 2016 in Spain|Images from Wiki Loves Earth 2016 in Spain]]\n"
    statisticts_text += u"* '''Total''': %d pictures\n" % (images_df.count()['image_title'])
    statisticts_text += u"** '''Quality Images''': %d pictures ([[%s|see]])\n" % (len(QI_list), GALLERY_FEATURED_ARTICLES)
    statisticts_text += u"* '''Statistics generation date''': {{subst:CURRENTTIME}} UTC, {{subst:CURRENTMONTHNAME}} " \
                        u"{{subst:CURRENTDAY}}, {{subst:CURRENTYEAR}}\n"
    statisticts_text += u'==Participants==\n' \
                        u'<br clear="all"/>\n' \
                        u'{| class="wikitable sortable" style="width:65%; font-size:89%; margin-top:0.5em;"\n' \
                        u'|- valign="middle"\n' \
                        u'! Author<br/><small>(registration time)</small>\n' \
                        u'! Uploaded images (total)\n' \
                        u'! Uploaded images<br/>(from a site of community importance)\n' \
                        u'! Contributed to SCIs\n'
    new_authors = list()
    for author, count in authors.iteritems():
        author_gallery_text += u'== %s ==\n\n' % (author)
        author_gallery_text += u'<gallery>\n'
        user = pb.User(commons_site, title=author)
        if unix_time(str(user.registration())) > NEW_USER_TIME : new_authors.append(author)
        author_with_SCIs = list(authors_with_SCIs.get_group(author)["code"].unique())
        author_with_pictures = list(authors_with_SCIs.get_group(author)["image_title"].unique())
        for index, value in enumerate(author_with_pictures) :
            author_gallery_text += u'%s\n' %(value)
        if u'' in author_with_SCIs :
            author_with_SCIs.remove(u'')
        for index, value in enumerate(author_with_SCIs) :
            author_with_SCIs[index] = u'[http://natura2000.eea.europa.eu/Natura2000/SDF.aspx?site=%s %s] (%s)' \
                                      % (value,
                                       value,
                                       scis_df[scis_df["code"] == value]["name"].iloc[0]
                                       )
        if author not in authors_with_code :
            authors_with_code[author] = 0
        if len(author_with_SCIs) == 0 :
            trailing_break = u''
        else :
            trailing_break = u'<br/>'
        statisticts_text += u'|-\n' \
                            u'| {{u|%s}} ([[%s#%s|contribs]])<br/><small>(registered on %d-%s-%s)</small>\n' \
                            u'| align="center" | %s\n' \
                            u'| align="center" | %s\n' \
                            u'| align="center" | %s%s(\'\'\'%d\'\'\')\n' % (author,
                                                          GALLERY_PAGE_AUTHORS,
                                                          author,
                                                          user.registration().year,
                                                          str(user.registration().month).zfill(2),
                                                          str(user.registration().day).zfill(2),
                                                          str(count),
                                                          authors_with_code[author],
                                                          '<br/>'.join(author_with_SCIs),
                                                          trailing_break,
                                                          len(author_with_SCIs))
        author_gallery_text += u'</gallery>\n\n'
    author_gallery_text += u'[[Category:Wiki Loves Earth 2016 in Spain| Contributors]]'
    pb.output('Generating --> WLE 2016 contributors gallery')

    statisticts_text += u'|-\n' \
                        u'! Total: %d contributors\n' \
                        u'! align="center" | %d pictures\n' \
                        u'! align="center" | %d pictures from<br/>a site of community importance\n' \
                        u'! align="center" | %d sites of<br/>community importance\n' \
                        u'|}\n' % (authors.size, images_df.count()['image_title'], authors_with_code.sum(), (len(SCIs)-1))

    statisticts_text += u"\n===New contributors===\n" \
                        u"'''Number of contributors registered during (or just before) the contest''':" \
                        u" '''%d'''\n\n" % (len(new_authors))
    statisticts_text += u"{| border = 0\n" \
                        u"| -\n" \
                        u"|\n"
    boundaries = split_range(len(new_authors), 3)
    statisticts_text += u"*{{u|%s}}\n" % ('}}\n* {{u|'.join(new_authors[:boundaries[0]]))
    statisticts_text += u"|\n"
    statisticts_text += u"*{{u|%s}}\n" % ('}}\n* {{u|'.join(new_authors[boundaries[0]:boundaries[1]]))
    statisticts_text += u"|\n"
    statisticts_text += u"*{{u|%s}}\n" % ('}}\n* {{u|'.join(new_authors[boundaries[1]:]))
    statisticts_text += u"|}\n\n"
    pb.output('Generating --> WLE 2016 contributor statistics')

    statisticts_text += u'=== Per-day contributions chart ===\n' \
                        u'<br clear="all"/>\n'

    chart_text = u'{{ #invoke:Chart | bar chart\n' \
                 u'| height = 450\n' \
                 u'| width = 800\n' \
                 u'| group 1 = %s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s\n' \
                 u'| x legends = <1::1::::5:::::10:::::15:::::20:::::25::::::31::>31\n' \
                 u'| group names = Pictures\n' \
                 u'| colors = orange\n' \
                 u'}}\n' % tuple(day_counter)
    statisticts_text += chart_text
    pb.output('Generating --> WLE 2016 per-day contribution statistics')

    statisticts_text += u'==Sites of Community Importance==\n' \
                        u'<br clear="all"/>\n'

    statisticts_text += u'{| class="wikitable sortable" style="width:55%; font-size:89%; margin-top:0.5em;"\n' \
                        u'|- valign="middle"\n' \
                        u'! Site of Community Importance<br/>(Commons category)\n' \
                        u'! Autonomous community\n' \
                        u'! Uploaded images\n'

    not_found_counter=0
    for site_code, count in SCIs.iteritems():
        if len(site_code) == 0 :
            not_found_counter = str(count)
        else :
            commons_cat_link = u''
            commons_cat = scis_df[scis_df["code"] == site_code]["category"].iloc[0]
            if len(commons_cat) > 0 :
                commons_cat_link = u'<br/>\'\'\'Commons category\'\'\': [[:Category:%s|%s]]' % (commons_cat, commons_cat)
            try:
                aut_com = scis_df[scis_df["code"] == site_code]["aut_com_name"].iloc[0]
            except :
                aut_com_name = u''
            site_name = scis_df[scis_df["code"] == site_code]["name"].iloc[0]
            statisticts_text += u'|-\n' \
                                u'| %s ([http://natura2000.eea.europa.eu/Natura2000/SDF.aspx?site=%s %s])%s\n' \
                                u'| align="center" | %s \n' \
                                u'| align="center" | %d<br/>(see [[%s#%s (%s)|gallery]], ' \
                                u'[[:Category:Images of site of community importance with code %s ' \
                                u'from Wiki Loves Earth 2016 in Spain|category]])\n' % (site_name,
                                                                              site_code,
                                                                              site_code,
                                                                              commons_cat_link,
                                                                              aut_com,
                                                                              count,
                                                                              GALLERY_PAGE_SCIS,
                                                                              site_name,
                                                                              site_code,
                                                                              site_code)
    statisticts_text += u'|-\n' \
                        u'| Images from no valid site of community importance\n' \
                        u'| align="center" | N/A\n' \
                        u'| align="center" | %s ([[%s#No_valid_site|see]])\n' %(not_found_counter, GALLERY_PAGE_SCIS)

    statisticts_text += u'|-\n' \
                        u"! '''Total''': %d/%d sites of community importance (%.2f%%)\n" \
                        u'! %d aut. communities\n' \
                        u'! %s\n' \
                        u'|}\n' % ((len(SCIs)-1),
                                   scis_df.count()['aut_com'],
                                   float((len(SCIs)-1)*100)/float(scis_df.count()['aut_com']),
                                   aut_com_with_SCI.unique().size,
                                   images_df.count()['image_title']
                                   )

    statisticts_text += u'=== Per-autonomous community contributions chart ===\n' \
                        u'{| border="0" width="90%"\n' \
                        u'|-\n' \
                        u'| valign="top" | \n'
    scis_per_autcom = aut_com_with_SCI.value_counts().to_dict()
    selected_colors = sample(aut_com_colors, len(scis_per_autcom)+1)
    reduced_selected_colors = copy.deepcopy(selected_colors)
    reduced_selected_colors.pop()
    expanded_sci_per_autcom_keys = copy.deepcopy(scis_per_autcom.keys())
    expanded_sci_per_autcom_keys.append('From no valid site')

    statisticts_text += create_pie_chart(images_per_autcom, dict(zip(expanded_sci_per_autcom_keys, selected_colors)), 'pictures', 'From no valid site')
    statisticts_text += u'| valign="top" |\n'
    statisticts_text += create_pie_chart(scis_per_autcom, dict(zip(scis_per_autcom.keys(), reduced_selected_colors)), 'SCIs')
    statisticts_text += u'|}\n'

    coverage_statisticts_text = u'==Coverage==\n' \
                        u'Coverage statistics measure the number of sites of community importance ' \
                        u'listed in the annexes in the Spanish Wikipedia. Direct access to said annexes is provided ' \
                        u'through the <nowiki>[es]</nowiki> wikilink in the \'Autonomous Community\' column within ' \
                        u'the table (other links to lists in other Wikipedias may be provided for the sake of ' \
                        u'completeness; however, only the ones in the Spanish Wikipedia are used to create ' \
                        u'this set of statistics).\n\n' \
                        u'{| class="wikitable sortable" style="width:55%; font-size:89%; margin-top:0.5em;"\n' \
                        u'|- valign="middle"\n' \
                        u'! Autonomous Community\n' \
                        u'! Sites (total)\n' \
                        u'! Sites (in lists)<br/> with category\n' \
                        u'! Sites (in lists)<br/> with image\n'

    grouped = sci_coverage_df.groupby(['aut_com'])
    for name, group in grouped:
        percentage_scis_with_cat = float (group.count()['category']*100.0/float(group.count()['aut_com']))
        percentage_scis_with_image = float (group.count()['image']*100.0/float(group.count()['aut_com']))
        wikisites_string = u'[[:es:%s|[es]]]' % group["es_annex"].unique()[0]
        if group["ca_annex"].unique()[0] != None and group["ca_annex"].unique()[0] > 3 :
            casite_string = u' [[:ca:%s|[ca]]]' % group["ca_annex"].unique()[0]
            wikisites_string += casite_string
        if group["gl_annex"].unique()[0] != None and group["gl_annex"].unique()[0] > 3 :
            glsite_string = u' [[:gl:%s|[gl]]]' % group["gl_annex"].unique()[0]
            wikisites_string += glsite_string
        coverage_statisticts_text += u'|-\n' \
                            u'| %s %s\n' \
                            u'| align="center" | %d\n' \
                            u'| align="center" bgcolor="#%s" | %d (%.2f%%)\n' \
                            u'| align="center" bgcolor="#%s" | %d (%.2f%%)\n' % \
                                                           (group["aut_com"].unique()[0],
                                                            wikisites_string,
                                                            group.count()['aut_com'],
                                                            get_quality_color(percentage_scis_with_cat),
                                                            group.count()['category'],
                                                            percentage_scis_with_cat,
                                                            get_quality_color(percentage_scis_with_image),
                                                            group.count()['image'],
                                                            percentage_scis_with_image)
    coverage_statisticts_text += u'|-\n' \
                        u'| Total\n' \
                        u'| align="center" | %d\n' \
                        u'| align="center" bgcolor="#%s" | %d (%.2f%%)\n' \
                        u'| align="center" bgcolor="#%s" | %d (%.2f%%)\n' \
                        u'|}\n\n' % (sci_coverage_df.count()['aut_com'],
                                        get_quality_color(float (sci_coverage_df.count()['category']*100.0/float(sci_coverage_df.count()['aut_com']))),
                                        sci_coverage_df.count()['category'],
                                        float (sci_coverage_df.count()['category']*100.0/float(sci_coverage_df.count()['aut_com'])),
                                        get_quality_color(float (sci_coverage_df.count()['image']*100.0/float(sci_coverage_df.count()['aut_com']))),
                                        sci_coverage_df.count()['image'],
                                        float (sci_coverage_df.count()['image']*100.0/float(sci_coverage_df.count()['aut_com'])))

    pb.output('Generating --> WLE 2016 Coverage Statistics')
    statisticts_text += coverage_statisticts_text

    image_usage_text = u'==Image usage==\n\n' \
                       u'{| class="wikitable sortable" style="width:50%; font-size:89%; margin-top:0.5em;"\n' \
                       u'|- valign="middle"\n' \
                       u'! Item\n' \
                       u'! Counter\n'
    for key, value in image_perwiki_counter.iteritems():
        image_usage_text += u'|-\n' \
                            u'| width="80%%" | WLE 2016 images used in %s\n' \
                            u'| align="center" | %d\n' % (key, value)
    image_usage_text += u'|-\n' \
                        u'| width="80%%" | Distinct WLE 2016 images used in any Wikipedia\n' \
                        u'| align="center" | \'\'\'%d\'\'\' (%.2f%%)\n' % (
                                                            image_usage_counter,
                                                            float(image_usage_counter)*100/float(images_df.count()['image_title'])
                                                            )
    for key, value in article_perwiki_counter.iteritems():
        image_usage_text += u'|-\n' \
                            u'| width="80%%" | Articles with WLE 2016 images in %s\n' \
                            u'| align="center" | %d\n' % (key, value)
    image_usage_text += u'|-\n' \
                        u'| width="80%%" | Articles with WLE 2016 images in any Wikipedia\n' \
                        u'| align="center" | \'\'\'%d\'\'\'\n' % (sum(article_perwiki_counter.values()))
    image_usage_text += u'|}\n\n'
    pb.output('Generating --> WLE 2016 Image Usage Statistics')
    statisticts_text += image_usage_text

    statisticts_text += u'\n[[Category:Wiki Loves Earth 2016 in Spain| Stats]]'
    stats_page.text = statisticts_text
    pb.output('Publishing --> WLE 2016 Statistics')
    stats_page.save(u"WLE Spain 2016 statistics")

    authors_page.text = author_gallery_text
    pb.output('Publishing --> WLE 2016 Authors gallery')
    authors_page.save(u"WLE Spain 2016 gallery (per author)")

if __name__ == "__main__":
    main()
