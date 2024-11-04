from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, XSD
import pandas as pd
import zipfile
import os
from io import BytesIO
from urllib.request import urlopen
from rdflib.plugin import register, Parser
import requests
from urllib.parse import urlparse

# Register the parser for N3 notation
register('text/rdf+n3', Parser, 'rdflib.plugins.parsers.notation3', 'N3Parser')

# Set GitHub token
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
headers = {"Authorization": f"token {GITHUB_TOKEN}"}

class CSVtoRDF:
    def __init__(self):
        """Initialize an RDF graph and define namespaces and ontology bindings."""

        # Initialize an empty RDF graph
        self.g = Graph()
        
        # Define custom namespaces
        self.oekg = Namespace("http://example/oekg/")
        self.omv = Namespace("http://omv.ontoware.org/2005/05/ontology#")
        
        # Bind namespaces for readability
        self.g.bind("omv", self.omv)
        self.g.bind("oekg", self.oekg)
        
        # Manually specify the column names for the CSV
        column_names = [
            "Ontology_Name", "Short_Name", "Domain", "Used_in_Projects", "Purpose",
            "Competency_Questions", "License", "Last_update", "Homepage", "Ontology_category",
            "Ontology_file", "Reference_Paper", "Citations", "use_cases", "overlaps",
            "what_makes_it_common", "structural_differences", "special_problem"
        ]

        # Load CSV file into a DataFrame with specified column names
        self.data = pd.read_csv('MSE_ontologies.csv', sep=',', names=column_names, header=0, encoding_errors='ignore').fillna('')

    def fetch_github_metadata(self, url):
        """Fetch comprehensive metadata from a GitHub repository if URL is a GitHub link."""
        github_api_base = "https://api.github.com/repos"
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.strip('/').split('/')
        
        if parsed_url.netloc != "github.com" or len(path_parts) < 2:
            return None

        owner, repo = path_parts[:2]
        api_url = f"{github_api_base}/{owner}/{repo}"

        try:
            # Fetch main repository data
            repo_response = requests.get(api_url, headers=headers)
            if repo_response.status_code != 200:
                print(f"Error fetching main repo data for {owner}/{repo}: {repo_response.json().get('message')}")
                return None
            repo_data = repo_response.json()

            # Fetch additional metadata
            languages_data = requests.get(f"{api_url}/languages", headers=headers).json()
            topics_data = requests.get(f"{api_url}/topics", headers={**headers, "Accept": "application/vnd.github.mercy-preview+json"}).json()
            contributors_data = requests.get(f"{api_url}/contributors", headers=headers).json()
            releases_data = requests.get(f"{api_url}/releases", headers=headers).json()
            tags_data = requests.get(f"{api_url}/tags", headers=headers).json()
            issues_data = requests.get(f"{api_url}/issues?state=all", headers=headers).json()
            commit_activity_data = requests.get(f"{api_url}/stats/commit_activity", headers=headers).json()
            community_data = requests.get(f"{api_url}/community/profile", headers=headers).json()

            # Compile metadata
            metadata = {
                "stars": repo_data.get("stargazers_count", 0),
                "forks": repo_data.get("forks_count", 0),
                "watchers_count": repo_data.get("watchers_count", 0),
                "size": repo_data.get("size", 0),
                "license": repo_data.get("license", {}).get("name"),
                "has_wiki": repo_data.get("has_wiki", False),
                "has_pages": repo_data.get("has_pages", False),
                "default_branch": repo_data.get("default_branch"),
                "topics": topics_data.get("names", []),
                "languages": list(languages_data.keys()),
                "last_update": repo_data.get("updated_at"),
                "owner": repo_data.get("owner", {}).get("login"),
                "description": repo_data.get("description"),
                "contributors": [{c.get("login"): c.get("contributions")} for c in contributors_data if "login" in c],
                "tags": [tag.get("name") for tag in tags_data],
                "releases": [{"tag_name": r.get("tag_name"), "published_at": r.get("published_at")} for r in releases_data],
                "pulls_count": len([issue for issue in issues_data if issue.get("pull_request")]),
                "open_issues": len([issue for issue in issues_data if issue.get("state") == 'open' and not issue.get("pull_request")]),
                "closed_issues": len([issue for issue in issues_data if issue.get("state") == 'closed' and not issue.get("pull_request")]),
                "commit_activity": commit_activity_data,
                "community": {
                    "health_percentage": community_data.get("health_percentage"),
                    "has_code_of_conduct": bool(community_data.get("files", {}).get("code_of_conduct")),
                    "has_contributing_guide": bool(community_data.get("files", {}).get("contributing")),
                    "has_issue_template": bool(community_data.get("files", {}).get("issue_template")),
                    "has_pull_request_template": bool(community_data.get("files", {}).get("pull_request_template"))
                }
            }

            return metadata

        except Exception as e:
            print(f"Error fetching GitHub metadata for {owner}/{repo}: {e}")
            return None   
              
    def create_triples(self):
        """Convert CSV data to RDF triples and add them to the RDF graph."""

        # Iterate over each row in the DataFrame to create triples
        for row in self.data.itertuples(index=False, name="OntologyRow"):
            # Define ontology short name as a URI reference
            ontology_short_name = URIRef(self.oekg + getattr(row, 'Short_Name').lower().replace(" ", "_"))
            
            # Define literals for various attributes
            ontology_name = Literal(getattr(row, 'Ontology_Name'), datatype=XSD.string)
            ontology_domain = Literal(getattr(row, 'Domain'), datatype=XSD.string)
            ontology_purpose = Literal(getattr(row, 'Purpose'), datatype=XSD.string)
            ontology_last_update = Literal(getattr(row, 'Last_update'), datatype=XSD.string)
            ontology_url = Literal(getattr(row, 'Homepage'), datatype=XSD.anyURI)
            ontology_license = Literal(getattr(row, 'License'), datatype=XSD.string)
            
            # Add basic ontology type triple
            self.g.add((ontology_short_name, RDF.type, self.omv.Ontology))
            
            # Add common properties to RDF graph
            self.g.add((ontology_short_name, self.omv.name, ontology_name))
            self.g.add((ontology_short_name, self.omv.domain, ontology_domain))
            self.g.add((ontology_short_name, self.omv.purpose, ontology_purpose))
            self.g.add((ontology_short_name, self.omv.modificationDate, ontology_last_update))
            self.g.add((ontology_short_name, self.omv.resourceLocator, ontology_url))
            self.g.add((ontology_short_name, self.omv.license, ontology_license))
            
            # Add optional properties if they exist
            if getattr(row, 'Competency_Questions'):
                competency_questions = Literal(getattr(row, 'Competency_Questions'), datatype=XSD.string)
                self.g.add((ontology_short_name, self.omv.competencyQuestion, competency_questions))
            if getattr(row, 'Used_in_Projects'):
                used_in_projects = Literal(getattr(row, 'Used_in_Projects'), datatype=XSD.string)
                self.g.add((ontology_short_name, self.omv.usedInProject, used_in_projects))
            if getattr(row, 'Ontology_category'):
                ontology_category = Literal(getattr(row, 'Ontology_category'), datatype=XSD.string)
                self.g.add((ontology_short_name, self.omv.ontologyCategory, ontology_category))
            if getattr(row, 'Reference_Paper'):
                reference_paper = Literal(getattr(row, 'Reference_Paper'), datatype=XSD.string)
                self.g.add((ontology_short_name, self.omv.reference, reference_paper))
            if getattr(row, 'Citations'):
                citations = Literal(getattr(row, 'Citations'), datatype=XSD.string)
                self.g.add((ontology_short_name, self.omv.citations, citations))
            if getattr(row, 'use_cases'):
                use_cases = Literal(getattr(row, 'use_cases'), datatype=XSD.string)
                self.g.add((ontology_short_name, self.omv.useCases, use_cases))
            if getattr(row, 'overlaps'):
                overlaps = Literal(getattr(row, 'overlaps'), datatype=XSD.string)
                self.g.add((ontology_short_name, self.omv.overlaps, overlaps))
            if getattr(row, 'what_makes_it_common'):
                common_factors = Literal(getattr(row, 'what_makes_it_common'), datatype=XSD.string)
                self.g.add((ontology_short_name, self.omv.commonFactors, common_factors))
            if getattr(row, 'structural_differences'):
                structural_differences = Literal(getattr(row, 'structural_differences'), datatype=XSD.string)
                self.g.add((ontology_short_name, self.omv.structuralDifferences, structural_differences))
            if getattr(row, 'special_problem'):
                special_problem = Literal(getattr(row, 'special_problem'), datatype=XSD.string)
                self.g.add((ontology_short_name, self.omv.specialProblem, special_problem))
            
            # If the homepage is a GitHub URL, fetch and add GitHub metadata
            homepage = getattr(row, 'Homepage', '').strip()
            if "github.com" in homepage:
                github_metadata = self.fetch_github_metadata(homepage)

                if github_metadata:
                    # Basic repository metadata
                    stars = Literal(github_metadata['stars'], datatype=XSD.integer)
                    forks = Literal(github_metadata['forks'], datatype=XSD.integer)
                    watchers_count = Literal(github_metadata['watchers_count'], datatype=XSD.integer)
                    size = Literal(github_metadata['size'], datatype=XSD.integer)
                    last_update = Literal(github_metadata['last_update'], datatype=XSD.dateTime)
                    open_issues = Literal(github_metadata['open_issues'], datatype=XSD.integer)
                    closed_issues = Literal(github_metadata['closed_issues'], datatype=XSD.integer)
                    owner = Literal(github_metadata['owner'], datatype=XSD.string)
                    description = Literal(github_metadata['description'], datatype=XSD.string)
                    license = Literal(github_metadata['license'], datatype=XSD.string)
                    has_wiki = Literal(github_metadata['has_wiki'], datatype=XSD.boolean)
                    has_pages = Literal(github_metadata['has_pages'], datatype=XSD.boolean)
                    default_branch = Literal(github_metadata['default_branch'], datatype=XSD.string)

                    # Add these triples to the RDF graph
                    self.g.add((ontology_short_name, self.oekg.stars, stars))
                    self.g.add((ontology_short_name, self.oekg.forks, forks))
                    self.g.add((ontology_short_name, self.oekg.watchersCount, watchers_count))
                    self.g.add((ontology_short_name, self.oekg.size, size))
                    self.g.add((ontology_short_name, self.oekg.lastUpdate, last_update))
                    self.g.add((ontology_short_name, self.oekg.openIssues, open_issues))
                    self.g.add((ontology_short_name, self.oekg.closedIssues, closed_issues))
                    self.g.add((ontology_short_name, self.oekg.owner, owner))
                    self.g.add((ontology_short_name, self.oekg.description, description))
                    self.g.add((ontology_short_name, self.oekg.license, license))
                    self.g.add((ontology_short_name, self.oekg.hasWiki, has_wiki))
                    self.g.add((ontology_short_name, self.oekg.hasPages, has_pages))
                    self.g.add((ontology_short_name, self.oekg.defaultBranch, default_branch))

                    # Topics
                    for topic in github_metadata['topics']:
                        topic_literal = Literal(topic, datatype=XSD.string)
                        self.g.add((ontology_short_name, self.oekg.topic, topic_literal))

                    # Languages
                    for language in github_metadata['languages']:
                        language_literal = Literal(language, datatype=XSD.string)
                        self.g.add((ontology_short_name, self.oekg.language, language_literal))

                    # Contributors
                    for contributor in github_metadata['contributors']:
                        for name, contributions in contributor.items():
                            contributor_name = Literal(name, datatype=XSD.string)
                            contributions_count = Literal(contributions, datatype=XSD.integer)
                            self.g.add((ontology_short_name, self.oekg.contributor, contributor_name))
                            self.g.add((ontology_short_name, self.oekg.contributions, contributions_count))

                    # Tags
                    for tag in github_metadata['tags']:
                        tag_name = Literal(tag, datatype=XSD.string)
                        self.g.add((ontology_short_name, self.oekg.tag, tag_name))

                    # Releases
                    for release in github_metadata['releases']:
                        tag_name = Literal(release['tag_name'], datatype=XSD.string)
                        published_at = Literal(release['published_at'], datatype=XSD.dateTime)
                        self.g.add((ontology_short_name, self.oekg.releaseTag, tag_name))
                        self.g.add((ontology_short_name, self.oekg.releaseDate, published_at))

                    # Commit Activity
                    for week_data in github_metadata['commit_activity']:
                        week_total = Literal(week_data['total'], datatype=XSD.integer)
                        self.g.add((ontology_short_name, self.oekg.weeklyCommits, week_total))

                    # Community Health Metrics
                    if github_metadata['community']:
                        health_percentage = Literal(github_metadata['community'].get("health_percentage", 0), datatype=XSD.integer)
                        self.g.add((ontology_short_name, self.oekg.healthPercentage, health_percentage))
                        
                        has_code_of_conduct = Literal(github_metadata['community'].get("has_code_of_conduct", False), datatype=XSD.boolean)
                        self.g.add((ontology_short_name, self.oekg.hasCodeOfConduct, has_code_of_conduct))
                        
                        has_contributing_guide = Literal(github_metadata['community'].get("has_contributing_guide", False), datatype=XSD.boolean)
                        self.g.add((ontology_short_name, self.oekg.hasContributingGuide, has_contributing_guide))
                        
                        has_issue_template = Literal(github_metadata['community'].get("has_issue_template", False), datatype=XSD.boolean)
                        self.g.add((ontology_short_name, self.oekg.hasIssueTemplate, has_issue_template))
                        
                        has_pull_request_template = Literal(github_metadata['community'].get("has_pull_request_template", False), datatype=XSD.boolean)
                        self.g.add((ontology_short_name, self.oekg.hasPullRequestTemplate, has_pull_request_template))

            '''
            # Process ontology file if provided

            ontology_file = getattr(row, 'Ontology_file', '').strip()
            if ontology_file:
                try:
                    # Handle zip files by extracting contents
                    if ontology_file.endswith("zip"):
                        with zipfile.ZipFile(BytesIO(urlopen(ontology_file).read())) as myzipfile:
                            ontology_file = myzipfile.read('metal-alloy.owl')
                            ontology_format = 'xml'
                    else:
                        ontology_format = 'xml' if ontology_file.endswith('owl') else ontology_file.split('.')[-1]

                    # Import additional namespaces or ontologies if specified
                    g = Graph().parse(ontology_file, format=ontology_format)
                    for prefix, namespace in g.namespaces():
                        prefix_uri = URIRef(self.oekg + prefix)
                        self.g.add((prefix_uri, RDF.type, self.omv.Ontology))
                        self.g.add((ontology_short_name, self.omv.useImports, prefix_uri))
                except Exception as e:
                    print(f"Error processing ontology file for {getattr(row, 'Short_Name')}: {e}")
            '''
            
        # Serialize the graph to a Turtle file
        self.g.serialize(destination='mse_ontologies.ttl', format='ttl')
        print("RDF graph created and saved to mse_ontologies.ttl")

# Execute the script
if __name__ == '__main__':
    oekg = CSVtoRDF()
    oekg.create_triples()
