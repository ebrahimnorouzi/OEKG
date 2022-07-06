
# import useful libraries
from rdflib import Graph
from rdflib import URIRef, BNode, Literal
from rdflib import Namespace
from rdflib.namespace import OWL, RDF, RDFS, FOAF, XSD
import pandas as pd

df = pd.read_excel('MSE_ontologies.xlsx')

class xlsx2RDF(object):

    def __init__(self):
            
        # initialize an empty graph
        self.g = Graph()
        
        # load the Ontology Metadata Vocabulary (OMV) 
        # OMV_url = 'https://raw.githubusercontent.com/vemonet/ontology-metadata-vocabulary/main/OMV.owl'
        # self.g.parse(OMV_url, format='application/rdf+xml')

        # namespace example for the PMD knowledge graph          
        self.pmd_kg = Namespace("http://www.materialdigital.de/ontology/")
        self.g.bind("pmd_kg", self.pmd_kg)
        
        # load excel file to dataframe
        self.data = pd.read_excel('MSE_ontologies.xlsx')
    
        
    def create_triples(self):

        # bind the OMV namspaces
        omv = Namespace("http://omv.ontoware.org/2005/05/ontology#")
        self.g.bind("omv", omv) 
      
        # iterate over excel file and create triples
        for row in self.data.itertuples(index=False):
            
            #We check if entity in our small local dictionary 
            ontology_short_name = URIRef(self.pmd_kg + row[1].lower().replace(" ", "_"))
            
            # define literals
            ontology_last_update = Literal(row[3], datatype=XSD.string) #XSD.dateTime)

            ontology_name = Literal(row[0], datatype=XSD.string)
            ontology_domain = Literal(row[2], datatype=XSD.string)
            ontology_url = Literal(row[6], datatype=XSD.string)

            ontology_n_classes = Literal(row[4], datatype=XSD.integer)
            ontology_n_properties = Literal(row[5], datatype=XSD.integer)
            
            # create triples
            self.g.add((ontology_short_name, RDF.type, omv.Ontology))

            self.g.add((ontology_short_name, omv.name, ontology_name))
            self.g.add((ontology_short_name, omv.modificationDate, ontology_last_update))
            self.g.add((ontology_short_name, omv.description, ontology_domain))
            self.g.add((ontology_short_name, omv.resourceLocator, ontology_url))
            self.g.add((ontology_short_name, omv.numClasses, ontology_n_classes))
            self.g.add((ontology_short_name, omv.numProperties, ontology_n_properties))
            
            
        self.g.serialize(destination='mse_ontologies.ttl', format='ttl')



if __name__ == '__main__':
    
    pmd_kg = xlsx2RDF()
    pmd_kg.create_triples()