
# Scripts to query OpenAlex and DOAJ APIs for publication information 

Gets works published by year for LUC and LUMC, APC data for returned journals, and first affiliated Loyola author.

## works-query.py

From OpenAlex: Gets all works for a given institution (LUC and LUMC) and year.
Work attributes returned: primary topic, subfield, field, domain, open access status, primary location, source, APC paid, APC list, funders, authors, author institutions, year, DOI, type, ISSN, publisher, etc.

From DOAJ: for gold OA journals only, query ISSN 
to return APC data: if has APC, waiver amount, APC max value, APC currency, DOAJ license.

## author-position.py
Extracts position of "Loyola University Chicago" or "Loyola University Chicago" from institutions column (output from works-query.py). Find matching position in authorships column and outputs both (and position number) into their own columns.
