
import rdflib#from rdflib import Graph#, Literal, URIRef, BNode
#from rdflib.term import Identifier
#from rdflib.collection import Collection
#from rdflib.namespace import RDF, RDFS, SKOS, XSD, OWL
import rdflib.plugins.sparql.update
#import owlrl.RDFSClosure

g = rdflib.Graph()
g.parse('mse_ontologies_pmd.ttl', format="ttl")

query1 = """
SELECT distinct ?s1 ?s2 ?q1 #(COUNT(?q1) AS ?count)
WHERE {
    pmd_kg:pmd_projects omv:contributesToOntology ?s1 .
    ?s1 omv:useImports ?q1 .
    ?s2 omv:useImports ?q1 .
    FILTER(!(?s1=?s2) && ?q1 NOT IN (pmd_kg:))
}
"""

query2 = """
SELECT ?q1 (COUNT(?q1) AS ?count)
WHERE {
    pmd_kg:pmd_projects omv:contributesToOntology ?s .
    ?s a omv:Ontology .
    ?s omv:useImports ?q1 .
} GROUP BY ?q1
ORDER BY DESC(?count)
"""

query3 = """
SELECT ?s1 ?s2
WHERE {
    pmd_kg:pmd_projects omv:contributesToOntology ?s1 ,?s2 .
    ?s1 omv:useImports ?s2 .
} 
"""
qres = g.query(query3)

for row in qres:
    print(row)
    #print(row['q1'].replace('http://www.materialdigital.de/ontology/', ''))
    #print(row['count'])