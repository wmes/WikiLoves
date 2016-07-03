#!/usr/bin/python
# -*- coding: utf-8  -*-
# NPM_wikidata_updater.py   Takes NPM lists from the Spanish Wikipedia and creates all necessary stuff in Wikidata
# author:                   Discasto (WM-ES)
# date:                     2016-07-03
#
# Distributed under the terms of the MIT license.
########################################################################################################################
#
import pywikibot as pb
import mwparserfromhell as mwh
import pandas as pd

ANNEXES = [u'Wikiproyecto:Ningún municipio español sin fotografía/Álava',
           u'Wikiproyecto:Ningún municipio español sin fotografía/AB-CR-TO',
           u'Wikiproyecto:Ningún municipio español sin fotografía/Asturias',
           u'Wikiproyecto:Ningún municipio español sin fotografía/Extremadura',
           u'Wikiproyecto:Ningún municipio español sin fotografía/Castilla y León Norte',
           u'Wikiproyecto:Ningún municipio español sin fotografía/C-N-R',
           u'Wikiproyecto:Ningún municipio español sin fotografía/Comunitat Valenciana',
           u'Wikiproyecto:Ningún municipio español sin fotografía/Andalucía',
           u'Wikiproyecto:Ningún municipio español sin fotografía/CU-GU',
           u'Wikiproyecto:Ningún municipio español sin fotografía/Guipúzcoa',
           u'Wikiproyecto:Ningún municipio español sin fotografía/Aragón y Catalunya',
           u'Wikiproyecto:Ningún municipio español sin fotografía/Salamanca',
           u'Wikiproyecto:Ningún municipio español sin fotografía/Santa Cruz de Tenerife',
           u'Wikiproyecto:Ningún municipio español sin fotografía/AV-SG',
           u'Wikiproyecto:Ningún municipio español sin fotografía/Vizcaya',
           u'Wikiproyecto:Ningún municipio español sin fotografía/Zamora']

CATEGORY = u'Category:Images from Spanish municipalities with no previous picture uploaded in 2016'

IMAGE_PROPERTY          = u'P18'
COMMONS_CAT_PROPERTY    = u'P373'
IMPORTED_FROM_PROPERTY  = u'P143'
INSTANCE_OF_PROPERTY    = u'P31'

MUNICIPALITY_VALUE      = 'Q2074737'      # Municipality of Spain
SPANISH_WIKIPEDIA_VALUE = 'Q8449'

def main () :
    commons_site = pb.Site("commons", "commons")
    wikipedia_site = pb.Site("es", "wikipedia")
    wikidata_site = pb.Site("wikidata", "wikidata")
    wikidata_site.login()
    repo = wikidata_site.data_repository()

    municipalities_df = pd.DataFrame(columns=['mun', 'code', 'category'])
    municipalities_cat = list()
    errors = list()

    for annex in ANNEXES:
        page = pb.Page(wikipedia_site, annex)
        text = page.text
        wikicode = mwh.parse(text)
        templates = wikicode.filter_templates()

        for template in templates:
            if template.name.lower().strip() == u"fila nmsf":
                df_row = dict()
                df_row["mun"] = None
                df_row["code"] = None
                df_row["category"] = None

                try:
                    if len(template.get(u"wikidata").value.strip()) > 3:
                        df_row["code"] = template.get(u"wikidata").value.strip()
                except:
                    pass
                try:
                    if len(template.get(u"municipio").value.strip()) > 3:
                        df_row["mun"] = template.get(u"municipio").value.strip()
                except:
                    pass
                try:
                    cat_name = template.get(u"categoría-Commons").value.strip()
                    if (len(cat_name) > 3) and cat_name != u"No hay":
                        df_row["category"] = cat_name
                        municipalities_cat.append(cat_name)
                except:
                except:
                    pass

                municipalities_df = municipalities_df.append(df_row, ignore_index=True)
        pb.output('Retrieving --> %s' %(annex))

    # Creating generic 'imported_from' source
    importedfrom = pb.Claim(repo,IMPORTED_FROM_PROPERTY)
    importedfrom.setTarget(pb.ItemPage(repo,SPANISH_WIKIPEDIA_VALUE))

    counter = 0
    for index, row in municipalities_df.iterrows():
        counter += 1
        if row["code"] != None :
            item = pb.ItemPage(repo, title=row["code"])
            try:
                item.get()
            except:
                errors.append (
                    {"id": row["code"],
                    "name": row["mun"],
                    "error": u"item information not retrievable"}
                    )
                continue
            if INSTANCE_OF_PROPERTY not in item.claims:
                instance_of_claim = pb.Claim(repo, INSTANCE_OF_PROPERTY)
                target = pb.ItemPage(repo, MUNICIPALITY_VALUE)
                try :
                    instance_of_claim.setTarget(target)
                    pb.output('Adding %s --> %s' % (instance_of_claim.getID(), instance_of_claim.getTarget()))
                    item.addClaim(instance_of_claim)
                    instance_of_claim.addSource(importedfrom)
                except:
                    errors.append(
                        {"id": row["code"],
                         "name": row["mun"],
                         "error": u"'instance of' insertion failed"}
                    )
            else:
                right_instance_of_already_present = False
                for i, claim in enumerate(item.claims[INSTANCE_OF_PROPERTY]):
                    if claim.target_equals(MUNICIPALITY_VALUE) and len(claim.sources) == 0:
                        pb.output('Adding %s --> %s' % (claim.getID(), claim.getTarget()))
                        claim.addSource(importedfrom)
                        right_instance_of_already_present = True
                    elif claim.target_equals(MUNICIPALITY_VALUE) and right_instance_of_already_present == True:
                        item.removeClaims(claim)
                    elif claim.target_equals(MUNICIPALITY_VALUE):
                        right_instance_of_already_present = True
                if right_instance_of_already_present == False:
                    instance_of_claim = pb.Claim(repo, INSTANCE_OF_PROPERTY)
                    target = pb.ItemPage(repo, MUNICIPALITY_VALUE)
                    try:
                        instance_of_claim.setTarget(target)
                        pb.output('Adding %s --> %s' % (instance_of_claim.getID(), instance_of_claim.getTarget()))
                        item.addClaim(instance_of_claim)
                        instance_of_claim.addSource(importedfrom)
                    except:
                        errors.append(
                            {"id": row["code"],
                            "name": row["mun"],
                            "error": u"'instance of' insertion failed"}
                            )
            # Handling commons cat
            if row["category"] != None:
                commons_cat = pb.Page(commons_site, title=row["category"], ns=14)
                if not commons_cat.exists() or commons_cat.isRedirectPage() or commons_cat.isDisambig():
                    errors.append (
                        {"id": row["code"],
                         "name": row["mun"],
                         "error": u"commons category not valid"}
                        )
                if commons_cat.exists() and \
                        not commons_cat.isRedirectPage() and \
                        not commons_cat.isDisambig() and \
                        COMMONS_CAT_PROPERTY in item.claims:
                    commons_cat_already_found = False
                    for claim in item.claims[COMMONS_CAT_PROPERTY]:
                        if claim.getTarget().title().lower().strip() == commons_cat.title(withNamespace=False).lower().strip() :
                            commons_cat_already_found = True
                            if len(claim.sources) == 0:
                                pb.output('Adding %s --> %s' % (claim.getID(), claim.getTarget()))
                                claim.addSource(importedfrom)
                        else :
                            errors.append(
                                {"id": row["code"],
                                 "name": row["mun"],
                                 "error": u"category in annex and in wikidata does not match"}
                            )
                    if COMMONS_CAT_PROPERTY not in item.claims:
                        try:
                            pb.output(
                                'Processing --> Commons cat claim not available. Claim will inserted')
                            claim = pb.Claim(repo, COMMONS_CAT_PROPERTY)
                            claim.setTarget(row["category"])
                            pb.output('Adding %s --> %s' % (claim.getID(), claim.getTarget()))
                            item.addClaim(claim)
                            claim.addSource(importedfrom)
                        except:
                            errors.append(
                                {"id": row["code"],
                                 "name": row["mun"],
                                "error": u"commons cat insertion failed"}
                            )
                    if u"commonswiki" not in item.sitelinks:
                        try:
                            pb.output('Adding commonswiki --> %s' % (item.getID()))
                            item.setSitelink(
                                sitelink={'site': 'commonswiki', 'title': commons_cat.title()},
                                summary=u'Set commons sitelink'
                            )
                        except:
                            errors.append(
                                {"id": row["code"],
                                 "name": row["mun"],
                                "error": u"commonswikilink insertion not possible"}
                            )
                    else:
                        if item.getSitelink(u"commonswiki") != commons_cat.title():
                            errors.append(
                                {"id": row["code"],
                                 "name": row["mun"],
                                "error": u"different commonswikilink already present"}
                            )
    # error publication
    my_error = u"<pre>\n"
    for error in errors:
        raw_text = u"%s;%s;%s;\n" % (error["id"], error["name"], error["error"])
        my_error = my_error + raw_text
    my_error = my_error + u'\n</pre>'
    list_page = pb.Page(wikidata_site, u"User:Discasto/tests 3")
    list_page.text = my_error
    list_page.save(u"NPM summary")

if __name__ == "__main__":
    main()
