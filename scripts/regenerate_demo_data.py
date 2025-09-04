#!/usr/bin/env python3
"""
DocuScan Demo Data Regeneration Script - Production Ready

This script populates Elasticsearch with realistic legal documents for testing
and demonstration purposes. It creates 1000+ documents with proper classification,
client information, and metadata.
"""

import sys
import json
import random
import requests
from datetime import datetime, timedelta
from faker import Faker
from faker.providers import BaseProvider

# Initialize Faker
fake = Faker()

# Custom legal provider for Faker
class LegalProvider(BaseProvider):
    legal_case_types = [
        'civil', 'criminal', 'corporate', 'family', 'immigration',
        'employment', 'real_estate', 'tax', 'bankruptcy'
    ]
    
    urgency_levels = ['low', 'medium', 'high', 'critical']
    
    legal_terms = [
        'contract', 'agreement', 'lawsuit', 'litigation', 'settlement',
        'deposition', 'motion', 'brief', 'affidavit', 'subpoena',
        'injunction', 'damages', 'liability', 'negligence', 'breach',
        'compliance', 'regulation', 'statute', 'precedent', 'jurisdiction'
    ]
    
    legal_entities = [
        'LLC', 'Corp', 'Inc', 'LP', 'LLP', 'PLLC', 'PC'
    ]
    
    def legal_case_type(self):
        return self.random_element(self.legal_case_types)
    
    def urgency_level(self):
        # Weight towards higher priorities for demo
        weights = [0.1, 0.2, 0.5, 0.2]  # low, medium, high, critical
        return random.choices(self.urgency_levels, weights=weights)[0]
    
    def legal_term(self):
        return self.random_element(self.legal_terms)
    
    def legal_entity(self):
        return self.random_element(self.legal_entities)

fake.add_provider(LegalProvider)

# Elasticsearch configuration
ES_HOST = "http://localhost:9200"
INDEX_NAME = "docuscan_documents"

def check_elasticsearch():
    """Check if Elasticsearch is running and accessible."""
    try:
        response = requests.get(f"{ES_HOST}/_cluster/health", timeout=5)
        if response.status_code == 200:
            health = response.json()
            print(f"✅ Elasticsearch is running - Status: {health['status']}")
            return True
        else:
            print(f"❌ Elasticsearch health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Cannot connect to Elasticsearch: {e}")
        return False

def create_index():
    """Create or recreate the documents index with proper mappings."""
    print(f"🔄 Creating index: {INDEX_NAME}")
    
    # Delete existing index if it exists
    try:
        response = requests.delete(f"{ES_HOST}/{INDEX_NAME}")
        if response.status_code in [200, 404]:
            print("🗑️ Existing index removed")
    except Exception as e:
        print(f"⚠️ Could not delete existing index: {e}")
    
    # Create new index with mappings
    mapping = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 0
        },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "filename": {"type": "text", "analyzer": "standard"},
                "client_name": {
                    "type": "text",
                    "analyzer": "standard",
                    "fields": {
                        "keyword": {"type": "keyword"}
                    }
                },
                "case_type": {"type": "keyword"},
                "urgency_level": {"type": "keyword"},
                "status": {"type": "keyword"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "file_size_bytes": {"type": "integer"},
                "content": {"type": "text", "analyzer": "standard"},
                "extracted_entities": {"type": "text"},
                "tags": {"type": "keyword"},
                "deadline": {"type": "date"},
                "priority_score": {"type": "float"},
                "processing_time_ms": {"type": "integer"},
                "ocr_confidence": {"type": "float"},
                "nlp_confidence": {"type": "float"}
            }
        }
    }
    
    try:
        response = requests.put(f"{ES_HOST}/{INDEX_NAME}", json=mapping, headers={"Content-Type": "application/json"})
        if response.status_code == 200:
            print("✅ Index created successfully")
            return True
        else:
            print(f"❌ Failed to create index: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Error creating index: {e}")
        return False

def generate_legal_content(case_type, client_name):
    """Generate realistic legal document content based on case type."""
    content_templates = {
        'civil': [
            f"COMPLAINT FOR DAMAGES\n\nPlaintiff {client_name} hereby files this complaint against defendant for damages resulting from breach of contract dated {fake.date_between(start_date='-2y', end_date='today')}. The plaintiff seeks monetary damages in the amount of ${random.randint(10000, 500000):,} plus attorney fees and costs.",
            f"MOTION FOR SUMMARY JUDGMENT\n\nTO THE HONORABLE COURT: {client_name} respectfully moves this Court for summary judgment on the grounds that there are no genuine issues of material fact and that movant is entitled to judgment as a matter of law."
        ],
        'criminal': [
            f"CRIMINAL COMPLAINT\n\nThe People of the State hereby charge {fake.name()} with violation of Penal Code Section {random.randint(100, 999)}. The defendant is accused of committing said offense on or about {fake.date_between(start_date='-1y', end_date='today')}.",
            f"PLEA AGREEMENT\n\nDefendant {fake.name()}, represented by {client_name}, hereby enters into the following plea agreement with the prosecution. Defendant agrees to plead guilty to the reduced charge in exchange for a recommended sentence."
        ],
        'corporate': [
            f"ARTICLES OF INCORPORATION\n\n{client_name} hereby files these Articles of Incorporation for {fake.company()} {fake.legal_entity()}. The corporation is organized for the purpose of conducting lawful business activities.",
            f"MERGER AGREEMENT\n\nThis Merger Agreement is entered into between {fake.company()} and {fake.company()} with legal counsel provided by {client_name}. The effective date of this merger shall be {fake.date_between(start_date='today', end_date='+1y')}."
        ],
        'family': [
            f"PETITION FOR DISSOLUTION OF MARRIAGE\n\nPetitioner, represented by {client_name}, respectfully requests this Court grant a dissolution of marriage from Respondent {fake.name()}. The parties were married on {fake.date_between(start_date='-20y', end_date='-1y')}.",
            f"CHILD CUSTODY AGREEMENT\n\nThe parties, through their counsel {client_name}, agree to the following custody arrangement for the minor child(ren). This agreement is in the best interests of the child(ren) involved."
        ],
        'immigration': [
            f"PETITION FOR NATURALIZATION\n\nPetitioner {fake.name()}, represented by {client_name}, respectfully requests this Court grant citizenship. Petitioner has been a lawful permanent resident since {fake.date_between(start_date='-10y', end_date='-5y')}.",
            f"APPLICATION FOR ASYLUM\n\nApplicant seeks asylum in the United States due to persecution in their home country. Represented by {client_name}, applicant demonstrates eligibility under Immigration and Nationality Act."
        ],
        'employment': [
            f"EMPLOYMENT DISCRIMINATION COMPLAINT\n\nPlaintiff {fake.name()}, represented by {client_name}, files this complaint alleging workplace discrimination. The discriminatory acts occurred between {fake.date_between(start_date='-2y', end_date='-6m')} and {fake.date_between(start_date='-6m', end_date='today')}.",
            f"WRONGFUL TERMINATION LAWSUIT\n\nPlaintiff seeks damages for wrongful termination from {fake.company()}. Legal representation provided by {client_name}. Plaintiff was employed from {fake.date_between(start_date='-5y', end_date='-1y')} until termination."
        ],
        'real_estate': [
            f"PURCHASE AND SALE AGREEMENT\n\nBuyer and Seller, with legal counsel from {client_name}, agree to the sale of real property located at {fake.address()}. Purchase price: ${random.randint(200000, 2000000):,}. Closing date: {fake.date_between(start_date='today', end_date='+3m')}.",
            f"LANDLORD-TENANT DISPUTE\n\nLandlord, represented by {client_name}, seeks eviction of tenant for non-payment of rent. Tenant owes ${random.randint(1000, 10000):,} in back rent as of {fake.date_between(start_date='-6m', end_date='today')}."
        ],
        'tax': [
            f"TAX COURT PETITION\n\nPetitioner {fake.name()}, represented by {client_name}, contests the IRS determination of tax liability for tax year {random.randint(2018, 2023)}. The disputed amount is ${random.randint(5000, 100000):,}.",
            f"TAX SETTLEMENT AGREEMENT\n\nTaxpayer and IRS reach settlement regarding disputed tax liability. Legal counsel provided by {client_name}. Settlement amount: ${random.randint(10000, 50000):,}."
        ],
        'bankruptcy': [
            f"CHAPTER 7 BANKRUPTCY PETITION\n\nDebtor {fake.name()}, represented by {client_name}, files for Chapter 7 bankruptcy relief. Total debts: ${random.randint(50000, 500000):,}. Assets: ${random.randint(10000, 100000):,}.",
            f"CHAPTER 11 REORGANIZATION PLAN\n\nDebtor corporation, through counsel {client_name}, proposes the following reorganization plan. The plan provides for payment of creditors over a {random.randint(3, 7)}-year period."
        ]
    }
    
    templates = content_templates.get(case_type, [f"Legal document for {case_type} case handled by {client_name}."])
    base_content = random.choice(templates)
    
    # Add some legal boilerplate
    additional_content = f"\n\nFILED: {fake.date_between(start_date='-1y', end_date='today')}\nCOURT: {fake.city()} Superior Court\nCASE NO: {random.randint(100000, 999999)}\nATTORNEY: {client_name}\n\nThis document contains confidential attorney-client privileged information."
    
    return base_content + additional_content

def generate_document():
    """Generate a single realistic legal document."""
    case_type = fake.legal_case_type()
    urgency = fake.urgency_level()
    
    # Generate client name (law firm or attorney)
    client_types = [
        f"{fake.last_name()} & Associates",
        f"{fake.last_name()}, {fake.last_name()} & {fake.last_name()} LLP",
        f"{fake.last_name()} Law Firm",
        f"{fake.first_name()} {fake.last_name()}, Esq.",
        f"{fake.company()} Legal Services",
        f"{fake.last_name()} & Partners"
    ]
    client_name = random.choice(client_types)
    
    # Generate filename based on case type and date
    file_extensions = ['.pdf', '.docx', '.doc']
    date_str = fake.date_between(start_date='-1y', end_date='today').strftime('%Y%m%d')
    case_num = random.randint(1000, 9999)
    
    filename_patterns = [
        f"{case_type}_{case_num}_{date_str}{random.choice(file_extensions)}",
        f"{fake.legal_term()}_{case_num}{random.choice(file_extensions)}",
        f"case_{case_num}_{case_type}_{date_str}{random.choice(file_extensions)}",
        f"{client_name.split()[0].lower()}_filing_{case_num}{random.choice(file_extensions)}"
    ]
    filename = random.choice(filename_patterns)
    
    # Generate document content
    content = generate_legal_content(case_type, client_name)
    
    # Calculate priority score based on urgency and case type
    urgency_scores = {'low': 0.25, 'medium': 0.5, 'high': 0.75, 'critical': 1.0}
    case_type_multipliers = {
        'criminal': 1.2, 'family': 1.1, 'immigration': 1.1,
        'employment': 1.0, 'civil': 0.9, 'corporate': 0.8,
        'real_estate': 0.7, 'tax': 0.8, 'bankruptcy': 0.9
    }
    
    priority_score = urgency_scores[urgency] * case_type_multipliers.get(case_type, 1.0)
    
    # Generate creation date
    created_at = fake.date_time_between(start_date='-1y', end_date='now')
    
    # Generate deadline (if high or critical priority)
    deadline = None
    if urgency in ['high', 'critical']:
        deadline = fake.date_time_between(start_date='now', end_date='+6m')
    
    document = {
        "id": f"doc_{fake.uuid4()}",
        "filename": filename,
        "client_name": client_name,
        "case_type": case_type,
        "urgency_level": urgency,
        "status": random.choice(['complete', 'processing', 'pending_review']),
        "created_at": created_at.isoformat(),
        "updated_at": fake.date_time_between(start_date=created_at, end_date='now').isoformat(),
        "file_size_bytes": random.randint(50000, 5000000),  # 50KB to 5MB
        "content": content,
        "extracted_entities": f"{fake.name()}, {client_name}, {fake.company()}, {fake.address()}",
        "tags": [case_type, urgency, fake.legal_term()],
        "deadline": deadline.isoformat() if deadline else None,
        "priority_score": round(priority_score, 2),
        "processing_time_ms": random.randint(500, 15000),
        "ocr_confidence": round(random.uniform(0.85, 0.99), 3),
        "nlp_confidence": round(random.uniform(0.80, 0.95), 3)
    }
    
    return document

def bulk_index_documents(documents, batch_size=100):
    """Index documents in bulk to Elasticsearch."""
    print(f"📤 Indexing {len(documents)} documents in batches of {batch_size}")
    
    for i in range(0, len(documents), batch_size):
        batch = documents[i:i + batch_size]
        bulk_body = []
        
        for doc in batch:
            # Index action
            bulk_body.append(json.dumps({"index": {"_index": INDEX_NAME, "_id": doc["id"]}}))
            # Document source
            bulk_body.append(json.dumps(doc))
        
        bulk_data = "\n".join(bulk_body) + "\n"
        
        try:
            response = requests.post(
                f"{ES_HOST}/_bulk",
                data=bulk_data,
                headers={"Content-Type": "application/x-ndjson"}
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("errors"):
                    print(f"⚠️ Some documents in batch {i//batch_size + 1} had errors")
                else:
                    print(f"✅ Batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size} indexed successfully")
            else:
                print(f"❌ Batch {i//batch_size + 1} failed: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error indexing batch {i//batch_size + 1}: {e}")

def verify_documents():
    """Verify that documents were indexed correctly."""
    try:
        response = requests.get(f"{ES_HOST}/{INDEX_NAME}/_count")
        if response.status_code == 200:
            count = response.json()["count"]
            print(f"✅ Verification: {count} documents indexed")
            
            # Get some sample statistics
            agg_query = {
                "size": 0,
                "aggs": {
                    "case_types": {"terms": {"field": "case_type", "size": 20}},
                    "urgency_levels": {"terms": {"field": "urgency_level", "size": 10}}
                }
            }
            
            response = requests.post(f"{ES_HOST}/{INDEX_NAME}/_search", json=agg_query)
            if response.status_code == 200:
                aggs = response.json()["aggregations"]
                
                print("\n📊 Case Type Distribution:")
                for bucket in aggs["case_types"]["buckets"]:
                    print(f"   {bucket['key']}: {bucket['doc_count']}")
                
                print("\n🚨 Urgency Distribution:")
                for bucket in aggs["urgency_levels"]["buckets"]:
                    print(f"   {bucket['key']}: {bucket['doc_count']}")
                    
            return count
        else:
            print(f"❌ Verification failed: {response.status_code}")
            return 0
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return 0

def main():
    """Main function to regenerate demo data."""
    print("🏛️ DocuScan Demo Data Regeneration Script")
    print("=" * 50)
    
    # Check Elasticsearch connection
    if not check_elasticsearch():
        print("❌ Cannot proceed without Elasticsearch connection")
        sys.exit(1)
    
    # Create index
    if not create_index():
        print("❌ Cannot proceed without creating index")
        sys.exit(1)
    
    # Generate documents
    num_documents = 1000
    print(f"🏗️ Generating {num_documents} legal documents...")
    
    documents = []
    for i in range(num_documents):
        if (i + 1) % 100 == 0:
            print(f"   Generated {i + 1}/{num_documents} documents...")
        documents.append(generate_document())
    
    print(f"✅ Generated {len(documents)} documents")
    
    # Index documents
    bulk_index_documents(documents)
    
    # Verify indexing
    print("\n🔍 Verifying indexed documents...")
    count = verify_documents()
    
    if count > 0:
        print(f"\n🎉 SUCCESS! {count} legal documents have been indexed in Elasticsearch")
        print("🔗 You can now access the DocuScan dashboard to view the data")
        print("📊 API Statistics: http://localhost:8000/api/dashboard/statistics")
        print("🔍 Document Search: http://localhost:8000/api/documents")
        print("🌐 Frontend Dashboard: http://localhost:3000")
    else:
        print("\n❌ FAILED! No documents were successfully indexed")
        sys.exit(1)

if __name__ == "__main__":
    main() 