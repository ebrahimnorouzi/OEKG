
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
SELECT ?q1 (COUNT(?q1) AS ?count)
WHERE {
    pmd_kg:pmd_projects omv:contributesToOntology ?s .
    ?s a omv:Ontology .
    ?s omv:useImports ?q1 .
} GROUP BY ?q1
ORDER BY DESC(?count)
"""
qres = g.query(query2)

for row in qres:
    print(row)
    #print(row['q1'], "frequency", row['count'])