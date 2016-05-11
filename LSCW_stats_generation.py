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

LSCW_CATEGORY = u"Category:Images from the Spanish Civil War contest"

BASE_LSCW2016_NAME          = u"Commons:Locations from the Spanish Civil War/2016"
STATISTICS_PAGE             = BASE_LSCW2016_NAME + u"/Stats"
LOG_PAGE                    = BASE_LSCW2016_NAME + u"/Log"
GALLERY_PAGE_AUTHORS        = BASE_LSCW2016_NAME + u"/Contributors"
GALLERY_FEATURED_ARTICLES   = BASE_LSCW2016_NAME + u'/QI'

START_TIME = 1459461600000 # 2016 April 01, 00:00:00 CEST (miliseconds)
DAY_LENGTH = 86400000
NEW_USER_TIME = 1459461600000 - (86400000*14)

API_BASE_URL = u'https://commons.wikimedia.org/w/api.php'
API_QUERY_STRING = {"action": "query",
                    "format": "json",
                    "gulimit": "10",
                    "prop": "globalusage",
                    "guprop": "url|namespace",
                    "titles": None
                    }

def unix_time(zulu_time_string):
    dt = datetime.strptime(zulu_time_string, "%Y-%m-%dT%H:%M:%SZ")
    epoch = datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return int(delta.total_seconds() * 1000)

def return_day (epoch_time) :
    return ((int(epoch_time) - START_TIME) / DAY_LENGTH) + 1

def main():
    parser = OptionParser()
    parser.add_option('-c', '--cached', action="store_true", default=False, dest='cached', help="work on cached list in commons")
    (options, args) = parser.parse_args()

    commons_site = pb.Site("commons", "commons")
    list_page = pb.Page(commons_site, LOG_PAGE)
    QI_list = list()

    api_call_counter = 0
    image_usage_counter = 0
    image_perwiki_counter = dict()
    article_perwiki_counter = dict()
    raw_api_query_string = u''
    query_string_items = list()

    if options.cached == False :
        # Retrieving images from the LSCW category
        pb.output('Retrieving --> LSCW 2016 images from category')
        cat = pb.Category(commons_site, LSCW_CATEGORY)
        gen = pagegenerators.CategorizedPageGenerator(cat)
        images = list()
        #list_row_text = u'%s;%s;%s;%s;\n' % (title, LSCW_identifier, uploader, creation.timestamp)

        image_counter = 0
        list_text = u'<pre>\n'
        for page in gen:
            if page.isImage():
                if (image_counter != 0) and (image_counter % 50 == 0) :
                    pb.output ('Retrieving --> '+str(image_counter)+" image descriptions downloaded")
                image_counter += 1
                image_item = [None] * 3
                title = page.title(withNamespace=False)
                creation = page.oldest_revision
                image_item[0] = title
                image_item[2] = str(creation.timestamp)
                image_item[1] = creation["user"]
                images.append(image_item)

                text = page.text
                wikicode = mwh.parse(text)
                templates = wikicode.filter_templates()

                for template in templates:
                    if template.name.lower().strip() == u"qualityimage":
                        QI_list.append(title)
                        break

                list_row_text = u'%s;\n' % (';'.join(image_item))
                list_text += list_row_text

                api_call_counter += 1
                title = 'File:' + page.title(withNamespace=False)
                query_string_items.append(title)
                if api_call_counter % 5 == 0:
                    pb.output('Retrieving --> LSCW 2016 image usage information')
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

        pb.output ('Retrieving --> '+str(image_counter)+" images downloaded")
        pb.output('Retrieved --> LSCW 2016 image list')

        list_text += u'</pre>'
        list_page.text = list_text
        pb.output('Publishing --> LSCW 2016 image log')
        list_page.save(u"LSCW Spain 2016 log")

    else :
        # Taking from a previously uploaded list of images
        # Data frame creation
        images = list()
        csv_text = list_page.text
        pb.output('Retrieving --> LSCW 2016 images list from cache')
        for line in csv_text.splitlines(True) :
            tokens = line[:-1].split(';')
            if len(tokens) > 1 :
                tokens.pop()
                images.append(tokens)

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
                    pb.output('Retrieving --> LSCW 2016 image usage information')
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
        pb.output('Retrieved --> LSCW 2016 image list from cache')

    # Panda management
    images_df = pd.DataFrame(images, columns=['image_title', 'uploader', 'timestamp'])
    images_df["timestamp"] = images_df["timestamp"].apply(unix_time)
    images_df["month_day"] = images_df["timestamp"].apply(return_day)

    author_counts   = images_df["uploader"].value_counts()
    author_groups   = images_df.groupby(['uploader'])
    month_days      = images_df["month_day"].value_counts()
    day_counter = [0] * 34
    for day, counter in month_days.iteritems() :
        if day > 30 :
            day_counter[33] += counter
        elif day > 0 :
            day_counter[day+1] = counter
        else :
            day_counter[0] += counter

    # Quality images gallery
    qi_gallery_text = u'This page lists the %d [[Commons:Quality Images|quality images]] uploaded as part of the ' \
                      u'[[:es:Wikiproyecto:Historia militar/Guerra Civil Española/Localizaciones|Locations of the Spanish Civil War]] ' \
                      u'contest in 2016.\n\n' % (len(QI_list))
    qi_gallery_text += u"'''Statistics generation date''': {{subst:CURRENTTIME}} UTC, {{subst:CURRENTMONTHNAME}} {{subst:CURRENTDAY}}, {{subst:CURRENTYEAR}}\n"
    qi_gallery_text += u'<gallery>\n'
    for qi in QI_list :
        qi_gallery_text += u'%s\n' % (qi)
    qi_gallery_text += u'</gallery>\n\n'
    qi_gallery_text += u'[[Category:Spanish Civil War contest]]'
    qi_gallery_page = pb.Page(commons_site, GALLERY_FEATURED_ARTICLES)
    qi_gallery_page.text = qi_gallery_text
    pb.output('Publishing --> LSCW 2016 quality images gallery')
    qi_gallery_page.save(u"LSCW 2016 quality images gallery")

    # Statistics page and authors gallery
    author_gallery_text = u''
    statisticts_text =  u"Welcome to the '''Locations from the Spanish Civil War (LSCW) 2016 contest''' statistics. " \
                        u"Below you will find information about the number of uploaded images, their usage, and the " \
                        u"contributors. Enjoy!!!\n\n"
    statisticts_text += u"==Images==\n"
    statisticts_text += u"* '''Main category''': " \
                        u"[[:Category:Images from the Spanish Civil War contest|Images from the Spanish Civil War contest]]\n\n"
    statisticts_text += u"* '''Total''': %d pictures\n" % (images_df.count()['image_title'])
    statisticts_text += u"** '''Quality Images''': %d pictures ([[Commons:Locations from the Spanish Civil War/2016/QI|see]])\n" % (len(QI_list))
    statisticts_text += u"* '''Statistics generation date''': {{subst:CURRENTTIME}} UTC, {{subst:CURRENTMONTHNAME}} {{subst:CURRENTDAY}}, {{subst:CURRENTYEAR}}\n"
    statisticts_text += u'==Participants==\n' \
                        u'<br clear="all"/>\n' \
                        u'{| class="wikitable sortable" style="width:40%; font-size:89%; margin-top:0.5em;"\n' \
                        u'|- valign="middle"\n' \
                        u'! Author<br/><small>(registration time)</small>\n' \
                        u'! Uploaded images (total)\n'
    new_authors = list()
    for author, count in author_counts.iteritems():
        author_gallery_text += u'== %s ==\n\n' % (author)
        author_gallery_text += u'<gallery>\n'
        user = pb.User(commons_site, title=author)
        #print author
        #print str(user.registration())
        if (user.registration()) != None and (unix_time(str(user.registration())) > NEW_USER_TIME) :
            new_authors.append(author)
        author_with_pictures = list(author_groups.get_group(author)["image_title"].unique())
        for index, value in enumerate(author_with_pictures) :
            author_gallery_text += u'%s\n' %(value)
        if (user.registration()) != None :
            statisticts_text += u'|-\n' \
                            u'| {{u|%s}} ([[%s#%s|contribs]])<br/><small>(registered on %d-%s-%s)</small>\n' \
                            u'| align="center" | %s\n' % (author,
                                                          GALLERY_PAGE_AUTHORS,
                                                          author,
                                                          user.registration().year,
                                                          str(user.registration().month).zfill(2),
                                                          str(user.registration().day).zfill(2),
                                                          str(count))
        else :
            statisticts_text += u'|-\n' \
                                u'| {{u|%s}} ([[%s#%s|contribs]])<br/><small>(registered very, very long ago)</small>\n' \
                                u'| align="center" | %s\n' % (author,
                                                              GALLERY_PAGE_AUTHORS,
                                                              author,
                                                              str(count))
        author_gallery_text += u'</gallery>\n\n'
    author_gallery_text += u'[[Category:Spanish Civil War contest]]'

    statisticts_text += u'|-\n' \
                        u'! Total: %d contributors\n' \
                        u'! align="center" | %d\n' \
                        u'|}\n' % (author_counts.size, images_df.count()['image_title'])

    statisticts_text += u"\n'''Number of contributors registered during (or just before) the contest''':" \
                        u" '''%d''' ({{u|%s}})\n\n" % (len(new_authors), '}}, {{u|'.join(new_authors))

    statisticts_text += u'== Per-day contributions ==\n' \
                        u'<br clear="all"/>\n'

    chart_text = u'{{ #invoke:Chart | bar chart\n' \
                 u'| height = 450\n' \
                 u'| width = 800\n' \
                 u'| group 1 = %s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s:%s\n' \
                 u'| x legends = <1::1::::5:::::10:::::15:::::20:::::25:::::30::>30\n' \
                 u'| group names = Pictures\n' \
                 u'| colors = green\n' \
                 u'}}\n' % tuple(day_counter)
    statisticts_text += chart_text

    image_usage_text = u'==Image usage==\n\n' \
                       u'{| class="wikitable sortable" style="width:30%; font-size:89%; margin-top:0.5em;"\n' \
                       u'|- valign="middle"\n' \
                       u'! Item\n' \
                       u'! Counter\n'


    for key, value in image_perwiki_counter.iteritems():
        image_usage_text += u'|-\n' \
                            u'| width="80%%" | LSCW 2016 images used in %s\n' \
                            u'| align="center" | %d\n' % (key, value)
    image_usage_text += u'|-\n' \
                        u'| width="80%%" | Distinct LSCW 2016 images used in any Wikipedia\n' \
                        u'| align="center" | \'\'\'%d\'\'\' (%.2f%%)\n' % (
                            image_usage_counter,
                            float(image_usage_counter) * 100 / float(images_df.count()['image_title'])
                        )
    for key, value in article_perwiki_counter.iteritems():
        image_usage_text += u'|-\n' \
                            u'| width="80%%" | Articles with LSCW 2016 images in %s\n' \
                            u'| align="center" | %d\n' % (key, value)
    image_usage_text += u'|-\n' \
                        u'| width="80%%" | Articles with LSCW 2016 images in any Wikipedia\n' \
                        u'| align="center" | \'\'\'%d\'\'\'\n' % (sum(article_perwiki_counter.values()))
    image_usage_text += u'|}\n\n'
    pb.output('Generating --> LSCW 2016 Image Usage Statistics')
    statisticts_text += image_usage_text

    statisticts_text += u'\n[[Category:Spanish Civil War contest]]'

    stats_page = pb.Page(commons_site, STATISTICS_PAGE)
    stats_page.text = statisticts_text
    pb.output('Publishing --> LSCW 2016 Statistics')
    stats_page.save(u"LSCW Spain 2016 statistics")

    authors_page = pb.Page(commons_site, GALLERY_PAGE_AUTHORS)
    authors_page.text = author_gallery_text
    pb.output('Publishing --> LSCW 2016 Authors gallery')
    authors_page.save(u"LSCW Spain 2016 gallery (per author)")

if __name__ == "__main__":
    main()