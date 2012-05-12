[dbpedia lite](http://dbpedialite.org) takes some of the structured data in [Wikipedia](http://wikipedia.org/) and presents it as [Linked Data](http://linkeddata.org/). It contains a small subset of the data that [dbpedia](http://dbpedia.org/) contains; it does not attempt to extract data from the Wikipedia infoboxes. Data is fetched live from the [Wikipedia API](http://en.wikipedia.org/w/api.php).

Unlike dbpedia is it uses stable Wikipedia pageIds in its URIs to attempt to mitigate the problems of article titles changing over time. If the title of a Wikipedia page changes, the dbpedia lite URI will stay the same. This makes it safer to store dbpedia lite identifiers in your own database.
