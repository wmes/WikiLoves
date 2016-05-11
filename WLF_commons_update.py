#!/usr/bin/python
# -*- coding: latin-1 -*-

# WLF_commons_updater.py        Takes WLF lists from the Spanish Wikipedia and updates all necessary stuff in Commons
# author:                       Discasto (WM-ES)
# date:                         2016-04-04
#
# Distributed under the terms of the MIT license.
########################################################################################################################
#
import mwparserfromhell as mwh
import pywikibot as pb
import sys
import getopt
import re

COMMONS_CAT_PROPERTY    = u'P373'

annexes = [ u'Anexo:Fiestas de interés turístico de Andalucía',
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

categories = [ u"Festivals of Andalusia",
               u"Festivals of Aragón",
               u"Festivals of Asturias",
               u"Festivals of Cantabria",
               u"Festivals of Castile-La Mancha",
               u"Festivals of Castile and León",
               u"Festivals of Catalonia",
               u"Festivals of the Community of Madrid",
               u"Festivals of the Land of Valencia",
               u"Festivals of Extremadura",
               u"Festivals of the Balearic Islands",
               u"Festivals of the Canary Islands",
               u"Festivals of Galicia (Spain)",
               u"Festivals of La Rioja",
               u"Festivals of Navarre",
               u"Festivals of the Region of Murcia",
               u"Festivals of the Basque Autonomous Community"]

def clean_page (page_wikitext, wikidata_id) :
    out = re.sub("(\[\[\s*[a-zA-Z]{2,3}\s*:.*?\]\]\s*\n)", '', page_wikitext)
    out = re.sub("(\[\[\s*[a-zA-Z]{2,3}\s*:.*?\]\]\s*)", '', out)
    out = re.sub("(\n{3,})", '\n\n', out)
    #out = out.replace('\n\n\n\n', '\n\n')
    #out = out.replace('\n\n\n', '\n\n')

    interwikis = u''

    wikidata_site = pb.Site("wikidata", "wikidata")
    repo = wikidata_site.data_repository()
    item = pb.ItemPage(repo, title=wikidata_id)
    try :
        item.get()
    except :
        pb.output('Processing --> Information from item not retrieved: ' + wikidata_id)
        return out

    commons_cat = list()
    if COMMONS_CAT_PROPERTY in item.claims :
        for claim in item.claims[COMMONS_CAT_PROPERTY]:
            commons_cat.append(claim.getTarget().title().lower().strip())
    if u"commonswiki" in item.sitelinks and len(item.sitelinks[u"commonswiki"]) > 0 :
        commonswiki_cat = item.sitelinks[u"commonswiki"].replace(u'Category:', '').lower().strip()
    else :
        commonswiki_cat = None

    if commonswiki_cat in commons_cat :
        pass
    elif len(item.sitelinks) > 0 :
        for sitelink in item.sitelinks :
            if sitelink != u'commonswiki' :
                interwikis += u'[[%s:%s]]\n' %(sitelink[:-4], item.sitelinks[sitelink])
        out += u'\n'+interwikis

    return out

def main(argv) :
    festivals = list()
    set_categories = False
    try:
        opts, args = getopt.getopt(argv, "hc", ["help", "category"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-c", "--category"):
            set_categories = True

    wikipedia_site = pb.Site("es", "wikipedia")
    commons_site = pb.Site("commons", "commons")

    for i, annex in enumerate(annexes) :
        pb.output('Retrieving --> Annex with index '+str(i))
        page = pb.Page(wikipedia_site, annex)
        text = page.text
        wikicode = mwh.parse(text)
        templates = wikicode.filter_templates()

        for template in templates :
            if template.name.lower().strip() == u"fila wlf" :
                festival = dict()
                if template.get(u"wikidata").value :
                    festival["wikidata"] = template.get(u"wikidata").value.strip()
                else :
                    festival["wikidata"] = u''
                if template.get(u"categoría-Commons").value :
                    festival["cat_commons"] = template.get(u"categoría-Commons").value.strip()
                else :
                    festival["cat_commons"] = u''
                if len(festival["wikidata"]) > 0 and len(festival["cat_commons"]) > 0 :
                    festival["meta_cat"] = categories[i]
                    festivals.append(festival)

    for festival in festivals :
        pb.output('Processing --> Festival with identifier ' + festival["wikidata"])
        if "cat_commons" in festival and len(festival["cat_commons"]) > 0 :
            try:
                category_page = pb.Category(commons_site, title=festival["cat_commons"])
            except :
                pb.output('Processing --> Category not accessible: ' + festival["wikidata"])
                continue

            if not category_page.exists() or category_page.isRedirectPage() or category_page.isDisambig() :
                pb.output('Processing --> Wrong category: ' + festival["wikidata"])
                continue

            valid_category_found = False
            catset = category_page.categories()
            for cat in catset :
                if cat.titleWithoutNamespace() == festival["meta_cat"] :
                    valid_category_found = True
                    break
                supercatset = pb.Category(commons_site, title=cat.titleWithoutNamespace()).categories()
                for super_cat in supercatset :
                    if super_cat.titleWithoutNamespace() == festival["meta_cat"] :
                        valid_category_found = True
                        break
                    supersupercatset = pb.Category(commons_site, title=super_cat.titleWithoutNamespace()).categories()
                    for super_super_cat in supersupercatset :
                        if super_super_cat.titleWithoutNamespace() == festival["meta_cat"] :
                            valid_category_found = True
                            break
                        supersupersupercatset = pb.Category(commons_site, title=super_super_cat.titleWithoutNamespace()).categories()
                        for super_super_super_cat in supersupersupercatset :
                            if super_super_super_cat.titleWithoutNamespace() == festival["meta_cat"] :
                                valid_category_found = True
                                break

            if valid_category_found :
                pass
            else :
                pb.output('Processing --> No right category found: ' + festival["wikidata"])

        category_page_text = category_page.text
        category_wikicode = mwh.parse(category_page_text)

        right_WLF_template_found = False
        right_WLF_identifier_found = False
        wikitemplates = category_wikicode.filter_templates()
        for template in wikitemplates :
            if template.name.lower().strip() == u"wlf" :
                found_id = template.get(1).value
                if found_id == festival["wikidata"] :
                    right_WLF_identifier_found = True
                right_WLF_template_found = True
        if right_WLF_template_found == False : print festival["wikidata"]

        if set_categories :
            if valid_category_found and right_WLF_template_found :
                output_wikitex = category_page_text
                if right_WLF_identifier_found == False :
                    category_page.text = clean_page (output_wikitex.replace(
                                                                            found_id.encode("utf-8"),
                                                                            festival["wikidata"].encode("utf-8")),
                                                                            festival["wikidata"])
                    category_page.save("WLF identifier fixed")
                    pb.output('Doing --> No proper identifier: fixed (%s)' % (festival["wikidata"]))
                else :
                    category_page.text = clean_page (output_wikitex, festival["wikidata"])
                    category_page.save("Language interwikis fixed")
                    pb.output('Doing --> Cleaning language interwikis (%s)' % (festival["wikidata"]))
                pb.output('Doing --> Nothing: Already with good category and template')
            elif not valid_category_found and right_WLF_template_found :
                output_wikitex = category_page_text+u'\n[[Category:'+festival["meta_cat"]+u']]'
                if right_WLF_identifier_found == False :
                    category_page.text = output_wikitex.replace(found_id.encode("utf-8"), festival["wikidata"].encode("utf-8"))
                category_page.save("Category updated")
                pb.output('Doing --> No proper category: category updated (%s)' % (festival["wikidata"]))
            elif valid_category_found and not right_WLF_template_found :
                output_wikitex = u"{{WLF|"+ festival["wikidata"]+u"}}\n"+category_page_text
                category_page.text = output_wikitex
                category_page.save("Template updated")
                pb.output('Doing --> No proper WLF template: template updated (%s)' % (festival["wikidata"]))
            else :
                output_wikitex = u"{{WLF|"+ festival["wikidata"]+u"}}\n\n"+category_page_text+u'\n[[Category:'+festival["meta_cat"]+u']]'
                category_page.text = output_wikitex
                category_page.save("Category and template updated")
                pb.output('Doing --> No proper category: category and template updated (%s)' % (festival["wikidata"]))
        else :
            if right_WLF_template_found == False:
                output_wikitex = u"{{WLF|"+ festival["wikidata"]+u"}}\n"+category_page_text
                category_page.text = output_wikitex
                pb.output('Doing --> No proper WLF template: template updated (%s)' % (festival["wikidata"]))
            '''else :
                pb.output('Doing --> Nothing: already with good template')'''

if __name__ == "__main__":
    main(sys.argv[1:])