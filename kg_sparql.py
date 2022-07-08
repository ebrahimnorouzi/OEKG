
from rdflib import Graph, Literal, URIRef, BNode
from rdflib.term import Identifier
from rdflib.collection import Collection
from rdflib.namespace import RDF, RDFS, SKOS, XSD, OWL
import rdflib.plugins.sparql.update
import owlrl.RDFSClosure

g = Graph()
g.parse('mse_ontologies.ttl')

query1 = """
SELECT ?s 
WHERE {
    pmd_kg:pmd_projects omv:contributesToOntology ?s .
    ?s a omv:Ontology .
    ?s omv:useImports pmd_kg:periodictable
}
"""
query2 = """
SELECT DISTINCT ?q1
WHERE {
    pmd_kg:pmd_projects omv:contributesToOntology ?s1 , ?s2 .
    ?s1 a omv:Ontology .
    ?s2 a omv:Ontology .
    ?s1 omv:useImports ?q1 .
    ?s2 omv:useImports ?q2 .
    FILTER((?q1=?q2) && !(?s1=?s2))# && ?q1 NOT IN (pmd_kg:dc, pmd_kg:skos, pmd_kg:dcat, pmd_kg:dcam, pmd_kg:foaf, pmd_kg:csvw, pmd_kg:xml, pmd_kg:xsd, pmd_kg:brick, pmd_kg:sosa, pmd_kg:schema, pmd_kg:rdf, pmd_kg:rdfs, pmd_kg:dcterms, pmd_kg:dcmitype))
}
"""
qres = g.query(query2)

for row in qres:
    #print(f"{row.s1} and {row.s2} similar {row.q1}")
    print(f"{row.q1}")