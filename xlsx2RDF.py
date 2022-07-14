
# import useful libraries
from rdflib import Graph
from rdflib import URIRef, BNode, Literal
from rdflib import Namespace
from rdflib.namespace import OWL, RDF, RDFS, FOAF, XSD
import pandas as pd
import zipfile
from io import StringIO, BytesIO
from urllib.request import urlopen
from rdflib.plugin import register, Serializer, Parser
register('text/rdf+n3', Parser, 'rdflib.plugins.parsers.notation3', 'N3Parser')

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
        self.data = pd.read_excel('MSE_ontologies.xlsx').fillna('')
    
        
    def create_triples(self):

        # bind the OMV namspaces
        omv = Namespace("http://omv.ontoware.org/2005/05/ontology#")
        self.g.bind("omv", omv)

        pmd_projects = URIRef(self.pmd_kg + 'pmd_projects')
        self.g.add((pmd_projects, RDF.type, omv.Organisation))

        # iterate over excel file and create triples
        for row in self.data.itertuples(index=False):
            
            #We check if entity in our small local dictionary 
            ontology_short_name = URIRef(self.pmd_kg + row[1].lower().replace(" ", "_"))
            
            # define literals
            ontology_last_update = Literal(row[3], datatype=XSD.string) #XSD.dateTime)

            ontology_name = Literal(row[0], datatype=XSD.string)
            ontology_domain = Literal(row[2], datatype=XSD.string)
            ontology_url = Literal(row[6], datatype=XSD.string)

            # create triples
            self.g.add((ontology_short_name, RDF.type, omv.Ontology))
            self.g.add((pmd_projects, omv.contributesToOntology, ontology_short_name))

            if row[4] != '':
                ontology_n_classes = Literal(row[4], datatype=XSD.integer)
                self.g.add((ontology_short_name, omv.numClasses, ontology_n_classes))
            if row[5] != '':
                ontology_n_properties = Literal(row[5], datatype=XSD.integer)
                self.g.add((ontology_short_name, omv.numProperties, ontology_n_properties))

            self.g.add((ontology_short_name, omv.name, ontology_name))
            self.g.add((ontology_short_name, omv.modificationDate, ontology_last_update))
            self.g.add((ontology_short_name, omv.description, ontology_domain))
            self.g.add((ontology_short_name, omv.resourceLocator, ontology_url))
            
            # add all the used ontologies in an Ontology
            if row[7] != '' and isinstance(row[7], str):
                ontology_file = row[7].strip()
                
                if ontology_file[-3:] == "zip":
                    myzipfile = zipfile.ZipFile(BytesIO(urlopen(ontology_file).read()))                    
                    ontology_file = myzipfile.read('metal-alloy.owl')
                    Ontology_format = 'xml'
                
                else:
                    Ontology_format = 'xml' if ontology_file[-3:]=='owl' else ontology_file[-3:]

                try:
                    g = Graph().parse(ontology_file, format=Ontology_format)
                    for prefix, namespace in g.namespaces():
                        prefix = URIRef(self.pmd_kg + prefix)
                        self.g.add((prefix, RDF.type, omv.Ontology))
                        self.g.add((ontology_short_name, omv.useImports, prefix))
                except:
                    pass

            
        self.g.serialize(destination='mse_ontologies.ttl', format='ttl')




if __name__ == '__main__':
    
    pmd_kg = xlsx2RDF()
    pmd_kg.create_triples()